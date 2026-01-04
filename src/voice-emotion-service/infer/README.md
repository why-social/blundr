# ve-infer

This module is the runtime for the VE model. It serves an endpoint to run 
emotion predictions on a single audio file, given the audio file and it's 
transcript.

## Under the hood

Currently, we use a CNN, which has an important implication of fixed input sizes
that are enforced at training time.

First, a transcript of the audio is created.
The audio file is split into *sentences* using timestamps from the transcript.
If a *sentence* is longer than the input size, it is split into *chunks* padded 
with equal amounts of silence (to avoid mostly silent chunks at ends of sentences).

## Building and running

**!!From the parent directory `voice-emotion-service`!!**

1. `docker build -t ve-infer .`
2. `docker compose up`

## API

`POST /voice-emotion/infer`

### Request

`session_id`: self-explanatory

`user_id`: self-explanatory

`audio`: the audio file to analyse


### Response

The endpoint creates a background job and immediately returns it's status:
```
200 OK
{
    "status": "accepted" | "error",
    "message": null or <str>,
}
```

The 'actual' response is sent to downstream (to the aggregator) when the job 
is finished.
The response is the transcript with added columns `label` and `confidence`:

`session_id`: the id of the chat

`uuid`: the id of the user

`ve_text`: the response object as a CSV string

_where the response object contains:_
```
[
    {
        "timestamp_start": <str (float)>,
        "timestamp_end": <str (float)>,
        "sentence": <str>,
        "label": <str (one of the emotions)>,
        "confidence": <float>,
    },
    ..., for each sentence or silence
]
```

