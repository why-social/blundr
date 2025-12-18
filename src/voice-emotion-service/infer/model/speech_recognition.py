import time
from pathlib import Path
from typing import Dict

import whisper as ws
from consts import MIN_PAUSE, SILENCE_TOKEN
from pandas import DataFrame

model = ws.load_model("base", device="cpu")


def transcribe_audio(audio_path: Path) -> DataFrame:
    prev_end = None
    sentence_buffer = []
    sentence_start = None
    start = time.time()

    result = model.transcribe(str(audio_path), word_timestamps=True)
    transcription_data = []

    for segment in result["segments"]:
        for word in segment["words"]:
            word_start = word["start"]
            word_end = word["end"]
            text = word["word"].strip()

            if sentence_start is None:
                sentence_start = word_start

            if prev_end is not None and (word_start - prev_end) > MIN_PAUSE:
                sentence_end = prev_end

                transcription_data.append(
                    _make_entry(sentence_start, sentence_end, " ".join(sentence_buffer))
                )
                transcription_data.append(
                    _make_entry(prev_end, sentence_end, SILENCE_TOKEN)
                )

                sentence_buffer = []
                sentence_start = word_start

            sentence_buffer.append(text)
            prev_end = word_end

    if sentence_buffer:
        sentence_end = prev_end
        if sentence_start is not None and sentence_end is not None:
            transcription_data.append(
                _make_entry(sentence_start, sentence_end, " ".join(sentence_buffer))
            )

    print(f"Time elapsed: {time.time() - start} seconds")
    return DataFrame(transcription_data)


def _make_entry(start: float, end: float, sentence: str) -> Dict[str, str]:
    return {
        "timestamp_start": f"{start:.2f}",
        "timestamp_end": f"{end:.2f}",
        "sentence": sentence,
    }
