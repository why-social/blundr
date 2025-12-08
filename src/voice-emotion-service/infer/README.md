# ve-infer

This module is the runtime for the VE model. It serves an endpoint to run 
emotion predictions on a single audio file, given the audio file and it's 
transcript.

## Under the hood

Currently, we use a CNN, which has an important implication of fixed input sizes
that are enforced at training time.
The audio file is split into *sentences* using timestamps from the transcript.
If a *sentence* is longer than the input size, it is split into *chunks* padded 
with equal amounts of silence (to avoid mostly silent chunks at ends of sentences).

## Building and running

**!!From the parent directory `voice-emotion-service`!!**

1. `docker build -t ve-infer .`
2. `docker compose up`

## API

`POST /infer`

### Request

`session_id`: self-explanatory

`user_id`: self-explanatory

`audio`: the audio file to analyse

`transcript`: the transcript from the transcription service, as a stringified csv

- expected format: `timestamp_start,timestamp_end\n...`
    - *the transcription service output contains more columnts, but these are the only ones used*
- the input is expected to have no empty entries (no empty sentences/silences)

### Request

The endpoint returns the following response:

`session_id`: self-explanatory

`user_id`: self-explanatory

`predictions`: labels for each *chunk*, as a stringified csv

- format: `start_time,end_time,label,confidence\n...`

