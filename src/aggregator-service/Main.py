import asyncio
import json
import os

import httpx
from aggregator import User, aggregate_files, extract_section_llm
from fastapi import BackgroundTasks, FastAPI, Form, HTTPException

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
PREMADE_OUTPUT = {
  "session_id": "test",
  "requested_by": "test",
  "status": "completed",
  "analysis": {
    "highlights": [
      {
        "timestamp": "50.5",
        "main_user": "test",
        "main_message": "And then that minute will begin of him taking over Yuji and that minute is where he is not allowed to harm anyone.",
        "description": "Exhibits clear understanding of the situation's rules despite negative emotions.",
        "annotation": "great",
        "context_block": [
          {
            "timestamp": "50.0",
            "user": "test",
            "message": "And then that minute will begin of him taking over Yuji and that minute is where he is not allowed to harm anyone."
          },
          {
            "timestamp": "51.0",
            "user": "test1",
            "message": "And then that minute will begin of him taking over Yuji and that minute is where he is not allowed to harm anyone."
          }
        ]
      },
      {
        "timestamp": "47.0",
        "main_user": "test",
        "main_message": "Do I have a right?",
        "description": "Asks an important question, showing interest in understanding the situation.",
        "annotation": "great",
        "context_block": [
          {
            "timestamp": "46.5",
            "user": "test1",
            "message": "But what about this?"
          },
          {
            "timestamp": "47.0",
            "user": "test",
            "message": "Do I have a right?"
          }
        ]
      },
      {
        "timestamp": "32.5",
        "main_user": "test",
        "main_message": "He’s not allowed to harm anyone during that minute.",
        "description": "Clearly defines the constraints of the situation, showing understanding and focus on rules.",
        "annotation": "excellent",
        "context_block": [
          {
            "timestamp": "32.0",
            "user": "test1",
            "message": "What about this?"
          },
          {
            "timestamp": "32.5",
            "user": "test",
            "message": "He’s not allowed to harm anyone during that minute."
          }
        ]
      }
    ],
    "strengths": [],
    "improvements": [
      "Could provide more context to clarify difficult points for better comprehension from others.",
      "Try to maintain a calmer tone when explaining complex situations to avoid misunderstandings."
    ]
  }
}

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

    Do NOT output JSON except inside the context_block.
    Do NOT output anything outside the required sections.

    Annotation explanation:
    - blunder: Indicates a critically bad mistake
    - mistake: A normal mistake
    - brilliant: Outstanding move
    - textbook: Standard correct move
    - great: A very good move
    - excellent: A very strong move


    You MUST output exactly THREE sections using these delimiters:

    ======BEGIN_HIGHLIGHTS======
    For each highlight, output exactly this JSON object on a single line:
    {{
        "timestamp": "<timestamp>",
        "main_user": "<speaker>",
        "main_message": "<text>",
        "description": "<short description>",
        "annotation": "<blunder, brilliant, excellent, mistake, great, textbook>",
        "context_block": [
            {{"timestamp": "<timestamp>", "user": "<speaker>", "message": "<text>"}},
            ...
        ]
    }}
    Do NOT include extra brackets or nested arrays.


    Extra rules:
    - main_user must always be the speaker of main_message
    - description must always be present; if unknown, use "No description"
    - context_block must always be a JSON array of objects with keys: "timestamp", "user", "message"
    - context_block must include at least 1 previous and 1 following message (if available)
    - Keep each message in context under 180 characters
    - Do NOT escape quotes inside context_block JSON
    - The ENTIRE context_block must be valid JSON

    ======END_HIGHLIGHTS======

    ======BEGIN_STRENGTHS======
    - text
    - text
    ======END_STRENGTHS======

    ======BEGIN_IMPROVEMENTS======
    - text
    - text
    ======END_IMPROVEMENTS======

    Global Rules:
    - Use all delimiters EXACTLY as shown
    - Make reasonable assumptions if uncertain
    - Strengths and improvements must refer specifically to this user: {user_id}
    - You MUST provide AT LEAST 1 strength and 1 improvement
    """


    response = await client.post(
        OLLAMA_URL,
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
    
    parsed_output = {
        "highlights": parse_highlights(highlights),
        "strengths": [] if strengths is None else parse_bullet_points(strengths),
        "improvements": [] if improvements is None else parse_bullet_points(improvements)
    }
    return parsed_output


def parse_highlights(text_block):
    highlights = []
    try:
        json_array_str = "[" + text_block.replace("}\n{", "},{") + "]"
        highlights = json.loads(json_array_str)
    except json.JSONDecodeError:
        buffer = ""    
        for line in text_block.splitlines():
            line = line.strip()
            if not line:
                continue
            buffer += line
            if line.endswith('}'):
                try:
                    obj = json.loads(buffer)
                    highlights.append(obj)
                except Exception:
                    pass
                buffer = ""
    return highlights

def parse_bullet_points(section):
    lines = [line.strip() for line in section.split("\n")]
    return [line[2:] for line in lines if line.startswith("- ")]

@app.get("/analyze")
async def analyze_session(session_id: str, user_id: str):
    if session_id == "test" and user_id == "test":
        return PREMADE_OUTPUT
    if session_id not in session_aggregate_cache:
        raise HTTPException(404, "Session not found")
    if user_id not in session_aggregate_cache[session_id]:
        raise HTTPException(404, "User not found in session")



    llm_analysis = session_aggregate_cache[session_id].pop(user_id, None)
    if not session_aggregate_cache[session_id]:
        session_aggregate_cache.pop(session_id)

    if llm_analysis is None:
        return {
            "session_id": session_id,
            "requested_by": user_id,
            "status": "processing",
            "analysis": None
        }

    return {
        "session_id": session_id,
        "requested_by": user_id,
        "status": "completed",
        "analysis": llm_analysis
    }


@app.post("/aggregator")
async def get_files(
    background_tasks: BackgroundTasks,
    session_id: str = Form(...),
    uuid: str = Form(...),
    fe_text: str | None = Form(None),
    ve_text: str | None = Form(None)
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
        session_id_tracker[session_id][uuid]["voice"] = ve_text
    
    session_id_tracker[session_id][uuid]["userId"] = uuid
    session_users = session_id_tracker[session_id]

    if len(session_users) == 2 and all(user.get("face") and user.get("voice") for user in session_users.values()):
        print("Processing...")
        user_list = list(session_users.items())
        user_1 = User(user_list[0][0], user_list[0][1])
        user_2 = User(user_list[1][0], user_list[1][1])

        final_agg_output = aggregate_files(user_1=user_1, user_2=user_2, session_id=session_id)
        
        background_tasks.add_task(process_llm, final_agg_output, session_id, user_1, user_2)
        
        return {"status": "processing started", "data": final_agg_output}
    
    return {"status": "waiting for other part(s)"}
    
async def process_llm(final_agg_output, session_id, user_1, user_2):
    llm_output_user_1, llm_output_user_2 = await asyncio.gather(
        call_llm(final_agg_output, user_id=user_1.id),
        call_llm(final_agg_output, user_id=user_2.id)
    ) 

    session_aggregate_cache.setdefault(session_id, {})
    session_aggregate_cache[session_id][user_1.id] = llm_output_user_1
    session_aggregate_cache[session_id][user_2.id] = llm_output_user_2
