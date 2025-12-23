import json
import re
import shutil
import uuid
from pprint import pprint
from typing import Any, List, Optional

import aiofiles
import pandas as pd
from consts import (
    BATCH_ROOT,
    CAS_ROOT,
    ENDPOINT_PREFIX,
    FER_DEPLOYMENT,
    MODEL_FILENAME,
    MODELS_MOUNT_ROOT,
)
from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.concurrency import run_in_threadpool
from job_builder import build_fer_training_job
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
from kubernetes.client.models import V1Deployment, V1DeploymentStatus, V1Job
from utils.gcs import check_model_exists, get_latest_model_version, save_to_cas
from utils.handle_csv import clean_nones, from_csv_or_str, process_batch_manifest

# k8s clients
_batch_client = None


def get_k8s_batch_client() -> Optional[client.BatchV1Api]:
    global _batch_client
    if _batch_client:
        return _batch_client

    try:
        config.load_incluster_config()
    except config.ConfigException:
        try:
            config.load_kube_config()
        except config.ConfigException:
            return None

    _batch_client = client.BatchV1Api()
    return _batch_client


_apps_client = None


def get_k8s_apps_client() -> Optional[client.AppsV1Api]:
    global _apps_client
    if _apps_client:
        return _apps_client

    try:
        config.load_incluster_config()
    except config.ConfigException:
        try:
            config.load_kube_config()
        except config.ConfigException:
            return None

    _apps_client = client.AppsV1Api()
    return _apps_client


app = FastAPI()


@app.post(ENDPOINT_PREFIX + "/fer/data/upload", status_code=201)
async def upload_batch(
    files: List[UploadFile] = File(...),
    manifest_file: Optional[UploadFile] = File(None),
    manifest_str: Optional[str] = Form(None),
):
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Expected at least 1 file."
        )

    # read manifest into dataframe
    try:
        manifest_df = await from_csv_or_str(manifest_file, manifest_str)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not parse manifest: {str(e)}.",
        )

    # verify manifest content
    if "filename" not in manifest_df.columns or "label" not in manifest_df.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Manifest CSV must contain a 'filename' and a 'label' column.",
        )

    # create directory for the batch
    try:
        batch_uuid = str(uuid.uuid4())[:6]
        batch_dir = BATCH_ROOT / f"batch-{batch_uuid}"
        batch_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create directories on mount: {str(e)}",
        )

    # upload files listed in manifest (manifest == source of truth)
    upload_map = {f.filename: f for f in files}
    saved_files = []
    failed_files = []
    indices_to_drop = []

    manifest_df["hash"] = None
    manifest_df["path"] = None

    for idx, row in manifest_df.iterrows():
        target_filename: Any = row["filename"]
        if pd.isna(target_filename) or (
            isinstance(target_filename, str) and not target_filename.strip()
        ):
            failed_files.append(
                {
                    "filename": "undefined",
                    "reason": "Empty name",
                }
            )
            indices_to_drop.append(idx)
            continue

        if target_filename not in upload_map:
            failed_files.append(
                {
                    "filename": target_filename,
                    "reason": "Listed in manifest but missing in upload.",
                }
            )
            indices_to_drop.append(idx)
            continue

        file_obj = upload_map[target_filename]

        # write the file
        try:
            content = await file_obj.read()
            result = await save_to_cas(CAS_ROOT, content, str(target_filename))

            if result["exists"]:
                print(f"{target_filename} already exists in CAS")
                failed_files.append(
                    {
                        "filename": target_filename,
                        "reason": "Duplicate. File already exists in a previous batch.",
                    }
                )
                indices_to_drop.append(idx)
                continue

            manifest_df.at[idx, "hash"] = result["hash"]
            manifest_df.at[idx, "path"] = result["path"]
            saved_files.append(target_filename)
        except Exception as e:
            failed_files.append(
                {"filename": target_filename, "reason": f"IO Error: {str(e)}"}
            )
            indices_to_drop.append(idx)

    if not saved_files:
        shutil.rmtree(batch_dir, ignore_errors=True)
        print(f"Failing with manifest {manifest_df}")
        print(failed_files)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "All files failed or were duplicates.",
                "failures": failed_files,
            },
        )

    if indices_to_drop:
        # clean invalid manifest entries before saving
        manifest_df.drop(indices_to_drop, inplace=True)

    for uploaded_filename in upload_map.keys():
        if uploaded_filename not in saved_files:
            failed_files.append(
                {
                    "filename": uploaded_filename,
                    "reason": "Uploaded but not listed in manifest",
                }
            )

    # save CSV non-blocking-ly
    try:
        manifest_path = batch_dir / "manifest.csv"
        metadata_path = batch_dir / "metadata.json"

        await run_in_threadpool(manifest_df.to_csv, manifest_path, index=False)

        metadata = {
            "batch_id": batch_uuid,
            "count": len(saved_files),
            "label_distribution": manifest_df["label"].value_counts().to_dict(),
        }
        async with aiofiles.open(metadata_path, mode="w") as f:
            await f.write(json.dumps(metadata, indent=2))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save manifest CSV: {str(e)}",
        )

    return {
        "status": "success" if not failed_files else "partial",
        "batch_id": batch_uuid,
        "saved_files": {
            "count": len(saved_files),
        },
        "failed_files": {
            "count": len(failed_files),
            "detail": failed_files,
        },
    }


@app.post(ENDPOINT_PREFIX + "/fer/models/train")
async def start_training_job():
    """
    Aggregates all batch manifests, creates a master manifest,
    and submits the training job.
    """
    print("Creating model directory...")
    try:
        model_ver = f"v{get_latest_model_version() + 1}"
        model_root = MODELS_MOUNT_ROOT / model_ver
        model_root.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create directories on mount: {str(e)}",
        )

    # --- AGGREGATE BATCH MANIFESTS ---
    try:
        print("Scanning for batch data...")
        # Find all batch directories
        batch_dirs = [d for d in BATCH_ROOT.glob("batch-*") if d.is_dir()]

        if not batch_dirs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No training data found (no batch directories).",
            )

        dfs = []
        for b_dir in batch_dirs:
            df = await run_in_threadpool(process_batch_manifest, b_dir)
            if df is not None and not df.empty:
                dfs.append(df)

        if not dfs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Found batch directories but no valid manifests.",
            )

        # Concatenate all dataframes
        master_df = pd.concat(dfs, ignore_index=True)

        # Save master manifest to the new model directory
        master_manifest_path = model_root / "manifest.csv"
        print(
            f"Writing master manifest ({len(master_df)} items) to {master_manifest_path}..."
        )
        await run_in_threadpool(master_df.to_csv, master_manifest_path, index=False)

    except Exception as e:
        shutil.rmtree(model_root, ignore_errors=True)

        if isinstance(e, HTTPException):
            raise e

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to aggregate manifests: {str(e)}",
        )

    # --- BUILD AND RUN k8s JOB ---
    try:
        print("Building job object...")
        job_object = build_fer_training_job(model_ver)

        if job_object is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to build Job object",
            )

        batch_api = get_k8s_batch_client()
        if not batch_api:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="K8s config missing",
            )

        response = await run_in_threadpool(
            batch_api.create_namespaced_job,
            namespace="default",
            body=job_object,
            pretty=True,
            async_req=False,
        )
        assert isinstance(response, V1Job)
        print("Job started")
        pprint(clean_nones(response))

        return {
            "job_status": clean_nones(response.status),
            "metadata": clean_nones(response.metadata),
            "model_version": model_ver,
            "training_set_size": len(master_df),
        }

    except Exception as e:
        # clean up the directory
        if model_root.exists():
            try:
                shutil.rmtree(model_root)
            except OSError as cleanup_error:
                print(f"Failed to cleanup {model_root}: {cleanup_error}")

        # re-raise custom httpexceptions
        if isinstance(e, HTTPException):
            raise e

        # catch-all
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit job: {str(e)}",
        )


@app.post(ENDPOINT_PREFIX + "/fer/models/select")
async def select_model(model_version: str):
    latest_ver = get_latest_model_version()
    if model_version.lower() == "latest":
        selected_version = latest_ver
    else:
        version_pattern = re.compile(r"^v(\d+)$")
        match = version_pattern.match(model_version)

        if match:
            selected_version = int(match.group(1))
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=r"Version must match the pattern /^v(\d+)$/",
            )

        if selected_version <= 0 or selected_version > latest_ver:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid version number. Latest: {latest_ver}",
            )

    if not check_model_exists(model_version):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model not available (directory exists but model file not found)."
        )

    apps_api = get_k8s_apps_client()
    if not apps_api:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="K8s config missing",
        )

    try:
        # run blocking API call wrapped in FastAPI managed threadpool
        deployment = await run_in_threadpool(
            apps_api.read_namespaced_deployment,
            name=FER_DEPLOYMENT["DEPLOYMENT_NAME"],
            namespace=FER_DEPLOYMENT["NAMESPACE"],
            async_req=False,
        )

        # the type system needs to chill
        assert isinstance(deployment, V1Deployment)
        if (
            not deployment.spec
            or not deployment.spec.template
            or not deployment.spec.template.spec
        ):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="K8s API returned malformed deplyment manifest (missing spec/template field(s))",
            )

        containers = deployment.spec.template.spec.containers
        fer_container = next(
            (c for c in containers if c.name == FER_DEPLOYMENT["CONTAINER_NAME"]), None
        )
        if not fer_container:
            raise HTTPException(
                status_code=500,
                detail=f"Container '{FER_DEPLOYMENT['CONTAINER_NAME']}' not found.",
            )

        # get mount root name from definition
        mount_path = None
        if fer_container.volume_mounts:
            for mount in fer_container.volume_mounts:
                if mount.name == FER_DEPLOYMENT["VOLUME_NAME_KEY"]:
                    mount_path = mount.mount_path
                    break

        if not mount_path:
            raise HTTPException(
                status_code=500,
                detail=f"Could not find volume mount '{FER_DEPLOYMENT['VOLUME_NAME_KEY']}' in container definition.",
            )

        # "/models" + "/v1/emotion_model.pt"
        target_model_path = (
            f"{mount_path.rstrip('/')}/v{selected_version}/{MODEL_FILENAME}"
        )

        current_env_val = None
        if fer_container.env:
            for env_var in fer_container.env:
                if env_var.name == FER_DEPLOYMENT["ENV_VAR_NAME"]:
                    current_env_val = env_var.value
                    break

        if current_env_val == target_model_path:
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail=f"Selected version '{selected_version}' already active."
            )

        patch_body = {
            "spec": {
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "name": FER_DEPLOYMENT["CONTAINER_NAME"],
                                "env": [
                                    {
                                        "name": FER_DEPLOYMENT["ENV_VAR_NAME"],
                                        "value": target_model_path,
                                    }
                                ],
                            }
                        ]
                    }
                }
            }
        }

        response = await run_in_threadpool(
            apps_api.patch_namespaced_deployment,
            name=FER_DEPLOYMENT["DEPLOYMENT_NAME"],
            namespace=FER_DEPLOYMENT["NAMESPACE"],
            body=patch_body,
            async_req=False,
        )
        assert isinstance(response, V1Deployment)
        assert isinstance(response.status, V1DeploymentStatus)

        return {
            "status": clean_nones(response.status),
            "new_model": {
                "version": model_version,
                "path": target_model_path,
            },
        }

    except ApiException as e:
        raise HTTPException(status_code=500, detail=f"K8s API Error: {e.reason}")


@app.get(ENDPOINT_PREFIX + '/fer/models')
async def get_models():
    pattern = re.compile(r'^v\d+$')
    model_dirs = [
        d for d in MODELS_MOUNT_ROOT.iterdir()
        if d.is_dir() and pattern.match(d.name) and check_model_exists(d.name)
    ]

    metadatas = []
    versions = []

    for d in model_dirs:
        versions.append(d.name)
        metadata_path = d / "metadata.json"
        metadata = None

        if metadata_path.exists():
            try:
                async with aiofiles.open(metadata_path, mode='r') as f:
                    content = await f.read()
                    metadata = json.loads(content)
            except Exception as e:
                print(f"WARN: could not read metadata for {d.name}: {str(e)}")

        metadatas.append({
            "version": d.name,
            "metadata": metadata,
        })

    return {
        "count": len(metadatas),
        "versions": versions,
        "models": metadatas,
    }

