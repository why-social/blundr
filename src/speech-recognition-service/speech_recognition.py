import time
import whisper as ws 
import os

MIN_PAUSE = 0.2
model = ws.load_model("base")


prev_end = None
sentence_buffer = []
sentence_start = None

def transcribe_audio():
    global prev_end, sentence_buffer, sentence_start
    create_log_files()

    all_files = []

    for file in os.listdir("logs"):
        start = time.time()
        
        file_removed_txt = file.split(".txt")[0]
        result = model.transcribe(f"audiofiles/{file_removed_txt}.wav", word_timestamps=True)
        log_file = open(f"logs/{file}", "a") 
        
        parts = file.split("Sesh_id:")[1].split("user_id:")
        session_id = parts[0]
        user_id = parts[1].split(".txt")[0]

        log_file.write(f"session_id,timestamp_start,timestamp_end,user_id,sentence\n")
        create_log(transcription_result=result, log_file=log_file, session_id=session_id, user_id=user_id)
        if sentence_buffer: 
            sentence_end = prev_end
            last_sentence = f'{session_id},{sentence_start:.2f},{sentence_end:.2f},{user_id},"{" ".join(sentence_buffer)}"\n'
            log_file.write(last_sentence)

        log_file.close()

        print(open(f"logs/{file}", "r").read())
        print(f"Time elapsed: {time.time() - start} seconds")
        with open(f"logs/{file}") as file:
            all_files.append(file.read())


    return "\n".join(all_files)
    
def create_log_files():
    for file in os.listdir("audiofiles"):
        try:
            file_removed_wav = file.split(".wav")[0]
            with open(f"logs/{file_removed_wav}.txt", "x"):
                pass
        except FileExistsError:
            print("File already exists")

def create_log(transcription_result: str, log_file: str, session_id, user_id):
    global prev_end, sentence_buffer, sentence_start

    for segment in transcription_result["segments"]:
            for word in segment["words"]:
                word_start = word["start"]
                word_end = word["end"]
                text = word["word"].strip()

                if sentence_start is None:
                    sentence_start = word_start

                if prev_end is not None and (word_start - prev_end) > MIN_PAUSE:
                    sentence_end = prev_end
                    
                    dialouge_text = f'{session_id},{sentence_start:.2f},{sentence_end:.2f},{user_id},"{" ".join(sentence_buffer)}"\n'
                    silence_text = f'{session_id},{prev_end:.2f},{word_start:.2f},{user_id},". . ."\n'
                    
                    log_file.write(dialouge_text)
                    log_file.write(silence_text)
                    
                    sentence_buffer = []
                    sentence_start = word_start
                
                sentence_buffer.append(text)
                prev_end = word_end
