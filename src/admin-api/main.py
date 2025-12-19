from pprint import pprint

from fastapi import FastAPI
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from job_builder import build_fer_training_job

PREFIX = "/admin"

config.load_incluster_config()
batch_api = client.BatchV1Api()

app = FastAPI()


@app.post(PREFIX + "/upload")
async def upload_batch():
    pass


@app.post(PREFIX + "/train")
async def start_training_job():
    """
    Creates and submits the training job.
    """
    print("Building job object...")
    job_object = build_fer_training_job("v1")
    assert job_object is not None, "PANIC: failed to build object"

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
