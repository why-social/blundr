# admin-api
API for Blundr model administration.

NOTE: running locally is possible, but correct interaction with the cluster 
is not guaranteed. The service attempts to load a local k8s config, but it may 
be unsuitable or lack permissions.

## API

- `POST admin-api/fer/data/upload`

Uploads a batch of images labeled via a manifest to the data store.

### Request

`files`: 1 or more image files to be uploaded as a batch.

`manifest_file`: Manifest as CSV where columns are: filename, label

OR

`manifest_str`: Manifest CSV as a string

### Response

On success:
```
201 CREATED
{
    "status": "success" | "partial",
    "batch_id": <str>,
    "saved_files": {
        "count": <int>,
    },
    "failed_files": null | {
        "count": <int>,
        "detail": [
            {
                "filename": <str>,
                "reason": <str>,
            },
            ...
        ],
    },
}
```


- `POST admin-api/fer/models/train`

Starts a training job in the cluster using all available data.

This endpoint will not work locally unless a valid k8s configuration is present, 
granting access to the cluster.

### Request

No Body

### Response

On success:
```
200 OK
{
    "job_status": <str> (see kubernetes.client.models.V1Job),
    "metadata": <str> (see kubernetes.client.models.V1Job),
    "model_version": <str>,
    "training_set_size": <int>,
}
```


- `POST admin-api/fer/models/select`

Applies a selected model to the current instances of FER. On success, 
triggers a service restart in the cluster.

This endpoint will not work locally unless a valid k8s configuration is present, 
granting access to the cluster.

### Request

`model_version`: version matching /^v\d+$/, or "latest"

### Response

On success:
```
200 OK
{
    "status": <str> (see kubernetes.client.models.V1Deployment),
    "new_model": {
        "version": <str matching /^v\d+$/>,
        "path": <str>, -- path to the model in the GCS store
    }
}
```


- `GET admin-api/fer/models`

Returns all models present on the GCS store.

### Request

No Body.

### Response

On success:
```
200 OK
{
    "count": <int>,
    "versions": [<str matching /^v\d+$/>],
    "models": [
        {
            "version": <str matching /^v\d+$/>,
            "metadata": null OR {...} (matching metadata.json on the GCS store, as saved by the training service)
        }
    ]
}
```

## Build & run

### Requirements

- Docker
- Docker Compose

### Build

_from `admin-api/`_:

```bash
docker build -t admin-api .
```

### Run

```bash
docker compose up
```

## Deploy

This service can be deployed to k8s using the script in `<REPO_ROOT>/k8s`:
```bash
./build-push.sh admin
```

