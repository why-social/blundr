import whisper as ws 

model = ws.load_model("base")

result = model.transcribe("/data/voice/anger/03-01-04-01-01-01-01_aug0.wav")

print(result["text"])