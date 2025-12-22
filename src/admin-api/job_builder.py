import uuid
from pathlib import Path
from typing import Dict, List

from kubernetes import client

NODEPOOL_NAME = "kiddie-pool"


def _build_volumes(buckets) -> List[client.V1Volume]:
    return [
        client.V1Volume(
            name=bucket,
            csi=client.V1CSIVolumeSource(
                driver="gcsfuse.csi.storage.gke.io",
                volume_attributes={
                    "bucketName": bucket,
                    "mountOptions": "implicit-dirs",
                },
            ),
        )
        for bucket in buckets
    ]


def _build_container(model_version: str, mounts: Dict[str, Path]) -> client.V1Container:
    return client.V1Container(
        name="fer-trainer",
        # TODO: use actual training image
        image="alpine:latest",
        image_pull_policy="Always",
        command=["cat", f"/models/{model_version}/manifest.csv"],
        env=[
            client.V1EnvVar(
                name="MODEL_VERSION",
                value=model_version,
            ),
        ],
        volume_mounts=[
            client.V1VolumeMount(
                name=name,
                mount_path=str(path),
            )
            for name, path in mounts.items()
        ],
    )


def build_fer_training_job(mounts: Dict[str, Path], model_version: str) -> client.V1Job:
    """
    Constructs a V1Job object for the training worker.
    """
    job_name = f"fer-training-job-{str(uuid.uuid4())[:6]}"
    volumes = _build_volumes(mounts.keys())

    pod_template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(
            labels={"app": "blundr", "component": "trainer"},
            annotations={
                "gke-gcsfuse/volumes": "true",
            },
        ),
        spec=client.V1PodSpec(
            restart_policy="Never",
            service_account_name="admin-api-sa",
            node_selector={
                "cloud.google.com/gke-nodepool": NODEPOOL_NAME,
            },
            tolerations=[
                client.V1Toleration(
                    key="workload",
                    operator="Equal",
                    value="training",
                    effect="NoSchedule",
                )
            ],
            volumes=volumes,
            containers=[_build_container(model_version, mounts)],
        ),
    )

    return client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(name=job_name, namespace="default"),
        spec=client.V1JobSpec(
            template=pod_template,
            ttl_seconds_after_finished=60,
            backoff_limit=2,  # Retry up to 2 times on failure
        ),
    )
