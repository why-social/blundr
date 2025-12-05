from fastapi import FastAPI, Form, UploadFile, File
import json
from aggregator import aggregate_files
app = FastAPI()

# Structure -> {session_id1: {user_id1: {faceFile, transcript}, user_id2: {faceFile, transcript}}}
session_id_tracker = {}

@app.post("/aggregator/")
async def get_files(
    session_id: str = Form(...),
    uuid: str = Form(...),

    fe_text: str | None = Form(None),
    ve_text: UploadFile | None = File(None)
    ):

   
    if session_id not in session_id_tracker:
        session_id_tracker[session_id] = {}
    if uuid not in session_id_tracker[session_id]:
        session_id_tracker[session_id][uuid] = {}

    if fe_text:
        try:
            parsed_info = json.loads(fe_text)
        except json.JSONDecodeError:
            return {"status": 404, "message": "Invalid JSON"}

        session_id_tracker[session_id][uuid]["face"] = parsed_info
    elif ve_text:
        raw_file = await ve_text.read()
        content = raw.decode("utf-8")

        session_id_tracker[session_id][uuid]["voice"] = content
    else:
        return {"status": 404, "message": "No content provided"}

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
    