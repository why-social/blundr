from dataset.spec_dataset import SpecDataset, AudioSample
from pathlib import Path

import os
import re


def parse_crema(path, dataset: SpecDataset):
    """
    Parses the CREMA dataset into a `Dataset` object.
    """

    map = {
        'neu': 'neutral',
        'hap': 'happy',
        'sad': 'sad',
        'ang': 'angry',
        'fea': 'fear',
        'dis': 'disgust',
    }

    # Format: 001_DFA_SAD_XX.wav
    for root_dir, _, files in os.walk(path):
        for file in files:
            if not file.endswith('.wav'): continue

            base_name = file.lower().replace('.wav', '')
            parts = base_name.split('_')
            assert len(parts) == 4

            emotion_raw = parts[2]
            assert emotion_raw in map

            dataset.add(AudioSample(
                path=Path(root_dir)/file,
                filename=base_name,
                source_dataset="CREMA",
                emotion=map[emotion_raw],
                actor=parts[0],
            ))


def parse_ravdess(path, dataset):
    """
    Parses the RAVDESS dataset into a `Dataset` object.
    """

    map = {
        '01': 'neutral',
        # '02': 'calm',
        '03': 'happy',
        '04': 'sad',
        '05': 'angry',
        '06': 'fear',
        '07': 'disgust',
        '08': 'surprise',
    }

    # Format: 03-01-06-01-02-01-01.wav (Video-Audio-Emotion-Intensity-Statement-Repetition-Actor)
    for root_dir, _, files in os.walk(path):
        for file in files:
            if not file.endswith('.wav'): continue

            base_name = file.lower().replace('.wav', '')
            parts = base_name.split('-')
            assert len(parts) == 7

            emotion_code = parts[2]
            if emotion_code == '02': continue # explicitly drop 'calm'
            assert emotion_code in map

            dataset.add(AudioSample(
                path=Path(root_dir)/file,
                filename=base_name,
                source_dataset="RAVDESS",
                emotion=map[emotion_code],
                actor=parts[-1],
            ))


def parse_tess(path, dataset):
    """
    Parses the TESS dataset into a `Dataset` object.
    """

    map = {
        'neutral': 'neutral',
        'happy':   'happy',
        'sad':     'sad',
        'angry':   'angry',
        'fear':    'fear',
        'disgust': 'disgust',
        'ps':      'surprise',
    }

    for root_dir, _, files in os.walk(path):
        for file in files:
            if not file.endswith('.wav'): continue

            base_name = file.lower().replace('.wav', '')

            parts = base_name.split('_')
            assert len(parts) == 3

            raw_emotion = parts[-1]

            # Assert it exists to satisfy type checker
            assert raw_emotion in map

            dataset.add(AudioSample(
                path=Path(root_dir)/file,
                filename=base_name,
                source_dataset="TESS",
                emotion=map[raw_emotion],
                actor=parts[0],
            ))


def parse_savee(path, dataset):
    """
    Parses the SAVEE dataset into a `Dataset` object.
    """

    map = {
        'n':  'neutral',
        'h':  'happy',
        'sa': 'sad',
        'a':  'angry',
        'f':  'fear',
        'd':  'disgust',
        'su': 'surprise',
    }

    # Format: [LetterCode][Digits].wav
    for root_dir, _, files in os.walk(path):
        for file in files:
            if not file.endswith('.wav'): continue

            # 'sa01.wav' -> match group 1 is 'sa'
            match = re.match(r"([a-zA-Z]+)\d+", file)
            actor_code = os.path.basename(root_dir)

            if not match: continue

            emotion_code = match.group(1)
            assert emotion_code in map

            dataset.add(AudioSample(
                path=Path(root_dir)/file,
                filename=f"{actor_code}_{file.replace('.wav', '')}",
                source_dataset="SAVEE",
                emotion=map[emotion_code],
                actor=actor_code,
            ))

def merge_datasets(raw_datasets, dataset: SpecDataset, augment=True):
    parse_tess(raw_datasets['TESS'], dataset)
    parse_ravdess(raw_datasets['RAVDESS'], dataset)
    parse_crema(raw_datasets['CREMA'], dataset)
    parse_savee(raw_datasets['SAVEE'], dataset)

    return dataset

