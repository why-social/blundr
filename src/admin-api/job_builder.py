# Original Author: Maxine Orlen
# Source: https://git.chalmers.se/courses/dit826/2025/team2
# License: MIT

import uuid
from typing import List

from consts import (
    FER_DEPLOYMENT,
    FER_TRAIN_IMAGE,
    GCS_DATA_BUCKET_NAME,
    GCS_MODEL_BUCKET_NAME,
    GCS_MOUNTS,
)
from kubernetes import client


def _build_volumes() -> List[client.V1Volume]:
    # Bucket mounts
    volumes = [
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
        for bucket in GCS_MOUNTS.keys()
    ]

    # shared memory
    volumes.append(client.V1Volume(
        name="dshm",
        empty_dir=client.V1EmptyDirVolumeSource(medium="Memory")
    ))

    return volumes


def _build_container(model_version: str) -> client.V1Container:
    volume_mounts = [
        client.V1VolumeMount(
            name=name,
            mount_path=str(path),
        )
        for name, path in GCS_MOUNTS.items()
    ]

    volume_mounts.append(client.V1VolumeMount(
        name="dshm",
        mount_path="/dev/shm"
    ))

    return client.V1Container(
        name="fer-train",
        image=FER_TRAIN_IMAGE,
        image_pull_policy="Always",
        env=[
            client.V1EnvVar(
                name="MODEL_VERSION",
                value=model_version,
            ),
            client.V1EnvVar(
                name="IMAGE_BASE_PATH",
                value=str(GCS_MOUNTS[GCS_DATA_BUCKET_NAME]),
            ),
            client.V1EnvVar(
                name="MODEL_BASE_PATH",
                value=str(GCS_MOUNTS[GCS_MODEL_BUCKET_NAME]),
            ),
        ],
        volume_mounts=volume_mounts,
        resources=client.V1ResourceRequirements(
            requests={"cpu": "10", "memory": "18Gi"}, # slightly less than node max
            limits={"cpu": "12", "memory": "20Gi"} # node maximum
        ),
    )


def build_fer_training_job(model_version: str) -> client.V1Job:
    """
    Constructs a V1Job object for the training worker.
    """
    job_name = f"fer-training-job-{str(uuid.uuid4())[:6]}"
    volumes = _build_volumes()

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
                "cloud.google.com/gke-nodepool": FER_DEPLOYMENT['NODEPOOL_NAME'],
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
            containers=[_build_container(model_version)],
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
