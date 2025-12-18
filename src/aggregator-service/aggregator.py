import io
import re
from collections import namedtuple

import pandas as pd

User = namedtuple("User", ["id", "data"])

def extract_section_llm(text: str, name: str):
    pattern = rf"=+BEGIN_{name}=+\s*(.*?)\s*=+END_{name}=+"
    match = re.search(pattern, text, flags=re.DOTALL) 
    return match.group(1).strip() if match else None   
            

def aggregate_files(user_1: User, user_2: User, session_id: str):
    merged_users_data = []
    users = [user_1, user_2]

    for user in users:
        print(f"Beginning aggregation process for User:{user.id}...\n")
        print(f"The face emotion csv contents: {user.data['face']}")
        print(f"The voice emotion csv contents: {user.data['voice']}")
        
        merged_users_data.append(ve_fe_aggregation(user=user, session_id=session_id))
    
    return combine_transcriptions(merged_users_data=merged_users_data, user_1=user_1, user_2=user_2)

def combine_transcriptions(merged_users_data: list, user_1: User, user_2: User):
    face_user_1 = pd.read_csv(io.StringIO(user_1.data["face"]))
    face_user_2 = pd.read_csv(io.StringIO(user_2.data["face"]))

    combined_data = pd.concat(merged_users_data, ignore_index=True)
    combined_data = combined_data.sort_values(by="time").reset_index(drop=True)

    final_rows = []

    for _, row in combined_data.iterrows():
        time = row["time"]
        speaker = row["speaking_user"]
        sentence = row["sentence"]
        speaker_voice = row["speaker_voice_emotion"]
        speaker_face = row["speaker_face_emotion"]

        listener = user_2.id if speaker == user_1.id else user_1.id
        face_df = face_user_2 if listener == user_2.id else face_user_1
        match = face_df.iloc[(face_df["time"] - time).abs().argsort().iloc[0]]

        if sentence.strip() == ". . .":
            speaker_voice = "silent"

        final_rows.append({
            "session_id": row["session_id"],
            "time": time,
            "speaking_user": speaker,
            "sentence": sentence,
            "speaker_voice_emotion": speaker_voice,
            "speaker_face_emotion": speaker_face,
            "listener_user": listener,
            "listener_face_emotion": match["emotion"]
        })
    
    final_df = pd.DataFrame(final_rows)
    print(f"This is the final df-json conversion output: {final_df.to_json(orient='records')}")
    return final_df.to_json(orient="records") 

def ve_fe_aggregation(user: User, session_id: str):
        face_emotion_df = pd.read_csv(io.StringIO(user.data["face"]))
        voice_emotion_df = pd.read_csv(io.StringIO(user.data["voice"]))

        merged_rows = []

        for _, row in face_emotion_df.iterrows():
            time = row["time"]
            
            interval = voice_emotion_df[(voice_emotion_df["timestamp_start"] <= time) & (voice_emotion_df["timestamp_end"] >= time)]
            if not interval.empty:
                voice_emotion_row = interval.iloc[0]
                merged_rows.append({
                    "session_id": session_id,
                    "time": time,
                    "speaking_user": user.id,
                    "sentence": voice_emotion_row['sentence'],
                    "speaker_voice_emotion": voice_emotion_row['label'],
                    "speaker_face_emotion": row['emotion']
                })
        merged_dataframe = pd.DataFrame(merged_rows)
        print(f"Merged information from User:{user.id}:\n{merged_dataframe}")
        return merged_dataframe