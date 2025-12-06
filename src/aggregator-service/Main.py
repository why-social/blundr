from fastapi import FastAPI, Form, UploadFile, File
import csv
import io
from aggregator import aggregate_files
app = FastAPI()

# Structure of the json: {session_id1: {user_id1: {faceFile, transcript}, user_id2: {faceFile, transcript}}}
session_id_tracker = {}

@app.post("/aggregator/")
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
        return_info = aggregate_files(
            user_1=user_list[0][1],
            user_1_id=user_list[0][0], 
            user_2=user_list[1][1], 
            user_2_id=user_list[1][0], 
            session_id=session_id
            )
        return {
            "status": 204,
            "data": return_info
        }
    
    return {"status": "waiting for other part(s)"}
    