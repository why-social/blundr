from fastapi import FastAPI, Form, UploadFile, File
from aggregator import aggregate_files
import requests
import httpx
import io

app = FastAPI()

# Structure of the json: {session_id1: {user_id1: {faceFile, transcript}, user_id2: {faceFile, transcript}}}
session_id_tracker = {}
final_agg_output = None

session_aggregate_cache = {}

async def call_llm(transcription: dict, user_id: str):
    prompt = f"""
    Context: The below JSON contains full information about a date between two users.
    You must:
    - analyze spoken words
    - evaluate emotional reactions
    - interpret facial emotion data
    - summarize performance of both users
    - highlight key moments
    - separate sections clearly

    If a user_id is provided, tailor part of the analysis to speak *directly to them*.

    USER requesting analysis: {user_id}

    Transcription data:
    {transcription}
    """
    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3", "prompt": prompt},
            timeout=None
        )
        return {"output": response.text}


@app.get("/analyse")
async def analyze_session(session_id: str, user_id: str):
    if session_id not in session_id_tracker:
        raise HTTPException(404, "Session not found")

    aggregated_json = session_aggregate_cache[session_id]

    llm_output = await call_llm(aggregated_json, user_id=user_id)

    return {
        "status": 200,
        "session_id": session_id,
        "requested_by": user_id,
        "analysis": llm_output
    }

    



@app.post("/aggregator")
async def get_files(
    session_id: str = Form(...),
    uuid: str = Form(...),
    fe_text: str | None = Form(None),
    ve_text: UploadFile | None = File(None)
    ):
    
    print(f"Session: {session_id}")
    print(f"User: {uuid}")
    
    if session_id not in session_id_tracker:
        session_id_tracker[session_id] = {}
    if uuid not in session_id_tracker[session_id]:
        session_id_tracker[session_id][uuid] = {}

    if fe_text is not None and fe_text != "":
        session_id_tracker[session_id][uuid]["face"] = fe_text
    if ve_text is not None:
        raw_file = await ve_text.read()
        content = raw_file.decode("utf-8")

        session_id_tracker[session_id][uuid]["voice"] = content
    
    session_id_tracker[session_id][uuid]["userId"] = uuid
    session_users = session_id_tracker[session_id]
    print(f"Session users: {session_users}")

    if len(session_users) == 2 and all(user.get("face") and user.get("voice") for user in session_users.values()):
        print("Processing...")
        user_list = list(session_users.items())
        final_agg_output = aggregate_files(
            user_1=user_list[0][1],
            user_1_id=user_list[0][0], 
            user_2=user_list[1][1], 
            user_2_id=user_list[1][0], 
            session_id=session_id
            )
        session_aggregate_cache[session_id] = final_agg_output
        return {
            "status": 204,
            "data": final_agg_output
        }
    
    return {"status": "waiting for other part(s)"}
    