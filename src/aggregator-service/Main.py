from fastapi import FastAPI, Body
import json
from aggregator import aggregate_files
app = FastAPI()

# Structure -> {session_id1: {user_id1: {faceFile, transcript}, user_id2: {faceFile, transcript}}}
session_id_tracker = {}

@app.post("/aggregator/")
async def get_files(
    session_id: str = Body(...),
    uuid: str = Body(...),
    content: str = Body(...)
    ):

    parsed_info = json.loads(content)

    if session_id not in session_id_tracker:
        session_id_tracker[session_id] = {}
    if uuid not in session_id_tracker[session_id]:
        session_id_tracker[session_id][uuid] = {}
    
    for key, value in parsed_info.items():
        session_id_tracker[session_id][uuid][key] = value

    session_users = session_id_tracker[session_id]

    if len(session_users) == 2 and all(user.get("face") and user.get("voice") for user in session_users.values()):
        print("Processing...")
        user_list = list(session_users.values())
        return_info = aggregate_files(user_1=user_list[0], user_2=user_list[1])
        return {
            "status": "done",
            "data": return_info
        }
    
    return {"status": "waiting for other part(s)"}
    