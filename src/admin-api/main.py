import os
import shutil
import uuid
import aiofiles
from pprint import pprint
from typing import List, Optional
from pathlib import Path

from fastapi import (
    FastAPI, 
    UploadFile,
    File, 
    Form,
    HTTPException, 
    status,
)
from fastapi.concurrency import run_in_threadpool
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from job_builder import build_fer_training_job
from utils.gcs import get_latest_model_version
from utils.handle_csv import from_csv_or_str

ENDPOINT_PREFIX = "/admin"

# GCS mounts
DATA_MOUNT_ROOT = Path(os.getenv("DATA_ROOT", "/data"))
MODELS_MOUNT_ROOT = Path(os.getenv("MODELS_ROOT", "/models"))

# config.load_incluster_config()
# batch_api = client.BatchV1Api()

app = FastAPI()


@app.post(ENDPOINT_PREFIX + "/upload")
async def upload_batch(
    files: List[UploadFile] = File(...),
    manifest_file: Optional[UploadFile] = File(None),
    manifest_str: Optional[str] = Form(None),
):
    # TODO: hashing to avoid duplicates?
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expected at least 1 file.")

    # read manifest into dataframe
    try:
        manifest_df = await from_csv_or_str(manifest_file, manifest_str)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not parse manifest: {str(e)}.",
        )

    # verify manifest content
    if 'filename' not in manifest_df.columns or 'label' not in manifest_df.columns:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Manifest CSV must contain a 'filename' and a 'label' column.",
        )


    # create directory for the batch
    try:
        batch_uuid = str(uuid.uuid4())[:6]
        batch_root = DATA_MOUNT_ROOT / f"batch-{batch_uuid}"
        batch_data = batch_root/"data"

        batch_data.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create directories on mount: {str(e)}"
        )

    # upload files listed in manifest (manifest == source of truth)
    upload_map = {f.filename: f for f in files}
    saved_files = []
    failed_files = []

    for _, row in manifest_df.iterrows():
        target_filename = row['filename']
        if not target_filename:
            failed_files.append({
                "filename": target_filename,
                "reason": "Empty name",
            })
            continue

        if target_filename not in upload_map:
            failed_files.append({
                "filename": target_filename,
                "reason": "Listed in manifest but missing in upload.",
            })
            continue

        file_obj = upload_map[target_filename]
        dest_path = batch_data/str(target_filename)

        # write the file
        try:
            content = await file_obj.read()
            async with aiofiles.open(dest_path, 'wb') as out_file:
                await out_file.write(content)

            saved_files.append(target_filename)
        except Exception as e:
            failed_files.append({
                "filename": target_filename,
                "reason": f"IO Error: {str(e)}"
            })

    if not saved_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files in the upload matched the filenames in the manifest."
        )
    else:
        for uploaded_filename in upload_map.keys():
            if uploaded_filename not in saved_files:
                failed_files.append({
                    "filename": uploaded_filename,
                    "reason": "Uploaded but not listed in manifest",
                })

    # save CSV non-blocking-ly
    try:
        manifest_csv_path_data = batch_root/"manifest.csv"
        await run_in_threadpool(manifest_df.to_csv, manifest_csv_path_data, index=False)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save manifest CSVs: {str(e)}",
        )

    if not saved_files:
        print("Batch upload failed. Cleaning up directories.")
        for d in [batch_data, batch_root]:
            if d.exists():
                try:
                    shutil.rmtree(d)
                except OSError as cleanup_error:
                    print(f"Failed to cleanup {d}: {cleanup_error}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch processing failed, no files uploaded.",
        )

    return {
        "status": "success" if not failed_files else "partial",
        "batch_id": batch_uuid,
        "saved_files": {
            "count": len(saved_files),
        },
        "files_failed": {
            "count": len(failed_files),
            "detail": failed_files,
        }
    }


@app.post(ENDPOINT_PREFIX + "/train")
async def start_training_job():
    """
    Creates and submits the training job.
    """
    print("Creating model directory and manifest...")
    model_ver = f"v{get_latest_model_version(MODELS_MOUNT_ROOT) + 1}"
    try:
        model_root = MODELS_MOUNT_ROOT/model_ver
        model_root.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create directories on mount: {str(e)}"
        )


    print("Building job object...")
    job_object = build_fer_training_job(
        mounts={
            "blundr-fer-models": MODELS_MOUNT_ROOT,
            "blundr-fer-data": DATA_MOUNT_ROOT,
        },
        model_version=model_ver,
    )
    if job_object is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to build Job object",
        )

    print(f"Submitting {getattr(job_object.metadata, 'name', 'unknown')}...")
    try:
        response = batch_api.create_namespaced_job(
            namespace="default",
            body=job_object,
            pretty="true",
        )

        print("Job started:")
        pprint(response)

        return {
            "status": "success",
            "job_name": response.metadata.name,
            "uid": response.metadata.uid,
        }

    except ApiException as e:
        print(f"Failed to submit job: {e}")
        raise e

@app.post(ENDPOINT_PREFIX + "/select")
def select_model(model_version: str):
    pass
