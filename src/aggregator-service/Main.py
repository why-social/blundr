from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from aggregator import aggregate_files, extract_section_llm, User
import httpx

app = FastAPI()
client = httpx.AsyncClient(timeout=None)
# Structure of the json: {session_id1: {user_id1: {faceFile, transcript}, user_id2: {faceFile, transcript}}}
session_id_tracker = {}
final_agg_output = None

session_aggregate_cache = {}

async def call_llm(transcription: dict, user_id: str):
    global client

    prompt = f"""
    You are an expert dating coach.

    You will receive JSON containing:
    - transcription
    - facial emotions
    - voice emotions
    - timestamps

    JSON data:
    {transcription}

    Do NOT output JSON.

    Annotation explanation:
    - ??: Indicates a blunder, a critically bad mistake
    - ?: A normal mistake
    - ?!: Quoestionable move, but may have some merit or is difficult to refute
    - !?: Could be a risky, an interesting but not the best move to be made
    - !: Indicates a good move, especially one that is suprising or requires particular skill
    - !!: Used for outstaning or particularly strong moves

    You MUST output exactly THREE sections using these delimiters:

    ======BEGIN_HIGHLIGHTS======
    For each highlight, output exactly this format:
    timestamp|||sentence_snippet|||description|||annotation
    Annotations can be one of: !!, !, !?, ?!, ?, ??
    timestamp|||sentence_snippet|||description|||annotation
    ======END_HIGHLIGHTS======

    ======BEGIN_STRENGTHS======
    - text
    - text
    ======END_STRENGTHS======

    ======BEGIN_IMPROVEMENTS======
    - text
    - text
    ======END_IMPROVEMENTS======

    Rules:
    - Always include timestamp, sentence snippet, and description for each highlight
    - The strengths and improvements are for this user: {user_id}
    - No commentary or explanations
    - Use the delimiters EXACTLY as shown
    - If unsure, make a reasonable assumption
    """

    response = await client.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5:7b", 
            "prompt": prompt, 
            "stream": False,
            "temperature": 0.0,
            }
        )

    model_output = response.text.strip()
    
    decoded_output = model_output.replace("\\n", "\n").replace('\\"', '"')

    highlights = extract_section_llm(decoded_output, "HIGHLIGHTS") 
    strengths = extract_section_llm(decoded_output, "STRENGTHS") 
    improvements = extract_section_llm(decoded_output, "IMPROVEMENTS") 
    
    return f"""=====BEGIN_HIGHLIGHTS=====\ntimestamp|||sentence_snippet|||description|||annotation
    \n{highlights}\n=====END_HIGHLIGHTS======
    \n=====BEGIN_STRENGTHS======\n{strengths}\n=====END_STRENGTHS=====\n
    =====BEGIN_IMPROVEMENTS=====\n{improvements}\n=====END_IMRPOVEMENTS====="""


@app.get("/analyze")
async def analyze_session(session_id: str, user_id: str):
    if session_id not in session_id_tracker:
        raise HTTPException(404, "Session not found")

    aggregated_json = session_aggregate_cache[session_id]

    llm_output = await call_llm(aggregated_json, user_id=user_id)

    session_aggregate_cache.pop(session_id)

    return {
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

    if len(session_users) == 2 and all(user.get("face") and user.get("voice") for user in session_users.values()):
        print("Processing...")
        user_list = list(session_users.items())
        user_1 = User(user_list[0][0], user_list[0][1])
        user_2 = User(user_list[1][0], user_list[1][1])

        final_agg_output = aggregate_files(user_1=user_1, user_2=user_2, session_id=session_id)
        
        session_aggregate_cache[session_id] = final_agg_output
        return {"data": final_agg_output}
    
    return {"status": "waiting for other part(s)"}
    