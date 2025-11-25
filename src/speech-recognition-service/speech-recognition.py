import time
import whisper as ws 
import os

MIN_PAUSE = 0.2
model = ws.load_model("base")


prev_end = None
sentence_buffer = []
sentence_start = None

for file in os.listdir("audiofiles"):
    try:
        file_removed_wav = file.split(".wav")[0]
        with open(f"logs/{file_removed_wav}.txt", "x"):
            pass
    except FileExistsError:
        print("File already exists")

for file in os.listdir("logs"):
    start = time.time()
    
    file_removed_txt = file.split(".txt")[0]
    result = model.transcribe(f"audiofiles/{file_removed_txt}.wav", word_timestamps=True)
    log_file = open(f"logs/{file}", "a") 
    
    parts = file.split("Sesh_id:")[1].split("user_id:")
    session_id = parts[0]
    user_id = parts[1]

    log_file.write(f"Session_id: {session_id}\n")
    for segment in result["segments"]:
        for word in segment["words"]:
            word_start = word["start"]
            word_end = word["end"]
            text = word["word"].strip()

            if sentence_start is None:
                sentence_start = word_start

            if prev_end is not None and (word_start - prev_end) > MIN_PAUSE:
                sentence_end = prev_end
                
                dialouge_text = f"[{sentence_start:.2f}] --> [{sentence_end:.2f}][{user_id}]: {' '.join(sentence_buffer)}\n"
                silence_text = f"[{prev_end:.2f}] --> [{word_start:.2f}][{user_id}]: . . .\n"
                
                log_file.write(dialouge_text)
                log_file.write(silence_text)
                
                sentence_buffer = []
                sentence_start = word_start
            
            sentence_buffer.append(text)
            prev_end = word_end
    if sentence_buffer: 
        sentence_end = prev_end
        last_sentence = f"[{sentence_start:.2f}] --> [{sentence_end:.2f}][{user_id}]: {' '.join(sentence_buffer)}\n"
        log_file.write(last_sentence)

    log_file.close()

    print(open(f"logs/{file}", "r").read())
    print(f"Time elapsed: {time.time() - start} seconds")