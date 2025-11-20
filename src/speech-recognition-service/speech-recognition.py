from faster_whisper import WhisperModel
import sounddevice as sd 
import soundfile as sf 
import numpy as np
import time 

SAMPLERATE = 16000
CHUNK = 16000
CHUNK_PROCESSING_LEN = 5
CHUNK_OVERLAP_TIME = 1
CHANNELS = 1
FILENAME = "output.wav"

CHUNK_SAMPLES = int(CHUNK_PROCESSING_LEN * SAMPLERATE)
OVERLAP_SAMPLES = int(CHUNK_OVERLAP_TIME * SAMPLERATE)

model = WhisperModel("base", compute_type="int8")

buffer = np.zeros(0, dtype=np.float32)

def process_chunk(audio_chunk):
    if len(audio_chunk) == 0:
        return
    segments, info = model.transcribe(audio_chunk, beam_size=5)
    for segment in segments:
        print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}", flush=True)

  
def callback(indata, frames, time_info, status):
    global buffer
    audio_data = indata[:, 0].astype(np.float32).flatten()
    buffer = np.concatenate([buffer, audio_data])

    while len(buffer) >= CHUNK_SAMPLES:
        chunk_to_process = buffer[:CHUNK_SAMPLES]
        process_chunk(chunk_to_process)
        buffer = buffer[CHUNK_SAMPLES - OVERLAP_SAMPLES:]


with sd.InputStream(channels=1, samplerate=SAMPLERATE, blocksize=CHUNK, callback=callback):
    while True:
        sd.sleep(1000)
