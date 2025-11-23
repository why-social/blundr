import time
import whisper as ws 

MIN_PAUSE = 0.2
model = ws.load_model("base")

start = time.time()
result = model.transcribe("jacksepticeyeTest.wav", word_timestamps=True)

prev_end = None
sentence_buffer = []
sentence_start = None
with open("log.txt", "x"):
    pass
log_file = open("log.txt", "a")

for segment in result["segments"]:
    for word in segment["words"]:
        word_start = word["start"]
        word_end = word["end"]
        text = word["word"].strip()

        if sentence_start is None:
            sentence_start = word_start

        if prev_end is not None and (word_start - prev_end) > MIN_PAUSE:
            sentence_end = prev_end
            
            dialouge_text = f"[{sentence_start:.2f}] --> [{sentence_end:.2f}]: {' '.join(sentence_buffer)}\n"
            silence_text = f"[{prev_end:.2f}] --> [{word_start:.2f}]: . . .\n"
            
            log_file.write(dialouge_text)
            log_file.write(silence_text)
            
            sentence_buffer = []
            sentence_start = word_start
        
        sentence_buffer.append(text)
        prev_end = word_end
if sentence_buffer: 
    sentence_end = prev_end
    last_sentence = f"[{sentence_start:.2f}] --> [{sentence_end:.2f}]: {' '.join(sentence_buffer)}\n"
    log_file.write(last_sentence)

log_file.close()

print(open("log.txt", "r").read())
print(f"Time elapsed: {time.time() - start} seconds")