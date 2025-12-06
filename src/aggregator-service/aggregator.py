import pandas as pd
import io

def aggregate_files(user_1: dict, user_1_id: str, user_2: dict, user_2_id: str, session_id: str):
    merged_users_data = []
    users = [
        {"data": user_1, "user_id": user_1_id},
        {"data": user_2, "user_id": user_2_id}
    ]
    for user in users:
        print(f"Beginning aggregation process for User:{user['user_id']}...\n")
        print(f"The face emotion csv contents: {user['data']['face']}")
        print(f"The voice emotion csv contents: {user['data']['voice']}")
        
        merged_users_data.append(ve_fe_aggregation(user["data"], user["user_id"], session_id))
    
    return combine_transcriptions(merged_users_data, user_1, user_1_id, user_2, user_2_id)

def combine_transcriptions(merged_users_data: list, user_1: str, user_1_id: str, user_2: str, user_2_id: str):
    face_user_1 = pd.read_csv(io.StringIO(user_1["face"]))
    face_user_2 = pd.read_csv(io.StringIO(user_2["face"]))

    combined_data = pd.concat(merged_users_data, ignore_index=True)
    combined_data = combined_data.sort_values(by="time").reset_index(drop=True)

    final_rows = []

    for _, row in combined_data.iterrows():
        time = row["time"]
        speaker = row["speaking_user"]
        sentence = row["sentence"]
        speaker_voice = row["speaker_voice_emotion"]
        speaker_face = row["speaker_face_emotion"]

        listener = user_2_id if speaker == user_1_id else user_1_id
        face_df = face_user_2 if listener == user_2_id else face_user_1
        match = face_df.iloc[(face_df["time"] - time).abs().argsort().iloc[0]]

        if sentence.strip() == ". . .":
            speaker_voice = "silence"

        final_rows.append({
            "session_id": row["session_id"],
            "time": time,
            "speaking_user": speaker,
            "speaker_voice_emotion": speaker_voice,
            "speaker_face_emotion": speaker_face,
            "listener_user": listener,
            "listener_face_emotion": match["emotion"]
        })
    
    final_df = pd.DataFrame(final_rows)
    
    return final_df.to_json(orient="records") 

def ve_fe_aggregation(user: dict, user_id: str, session_id: str):
        face_emotion_df = pd.read_csv(io.StringIO(user["face"]))
        voice_emotion_df = pd.read_csv(io.StringIO(user["voice"]))

        merged_rows = []

        for _, row in face_emotion_df.iterrows():
            time = row["time"]
            
            interval = voice_emotion_df[(voice_emotion_df["timestamp_start"] <= time) & (voice_emotion_df["timestamp_end"] >= time)]
            if not interval.empty:
                voice_emotion_row = interval.iloc[0]
                merged_rows.append({
                    "session_id": session_id,
                    "time": time,
                    "speaking_user": user_id,
                    "sentence": voice_emotion_row['sentence'],
                    "speaker_voice_emotion": voice_emotion_row['emotion'],
                    "speaker_face_emotion": row['emotion']
                })
        merged_dataframe = pd.DataFrame(merged_rows)
        print(f"Merged information from User:{user_id}:\n{merged_dataframe}")
        return merged_dataframe