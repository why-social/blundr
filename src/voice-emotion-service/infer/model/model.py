from pathlib import Path
from typing import List

import pandas as pd
import torch
from common.config.dataset_config import DatasetConfig
from common.config.model_config import ModelConfig
from common.model.crnn_model import CRNNModel
from common.utils.audio_processing import AudioProcessor
from common.utils.transformations import standardize_length
from data import segment
from data.load import load_transcribed_segments
from torch.nn.functional import softmax
from tqdm import tqdm


class Model:
    def __init__(self, model_path: Path) -> None:
        self.model_config = ModelConfig()
        self.data_config = DatasetConfig()
        self.processor = AudioProcessor(self.data_config)

        self.model = CRNNModel(
            self.model_config,
            n_mels=self.data_config.n_mels,
            num_classes=self.data_config.n_classes,
        ).to(self.model_config.device)

        print("Loading model...")
        self.model.load_state_dict(
            torch.load(model_path, map_location=self.model_config.device)
        )
        self.model.eval()
        print("Loaded")

        self.label_map = {v: k for k, v in self.data_config.label_map.items()}
        self.sorted_indices = sorted(self.label_map.keys())
        self.label_names = [self.label_map[i] for i in self.sorted_indices]

    def infer(self, audio_path: Path, transcript: pd.DataFrame) -> pd.DataFrame:
        # === LOAD DATA ===
        segments = load_transcribed_segments(transcript, audio_path, self.data_config)
        print(f"Split into {len(segments)} chunks for inference.")

        # === RUN INFERRENCE ===
        results = []
        with torch.no_grad():
            for seg in tqdm(segments, desc="Predicting"):
                spec = self.processor.segment_to_spec(
                    audio_path, seg
                )  # load chunk (<= target_len)
                spec = standardize_length(
                    spec, self.data_config.target_frames, mode="end"
                )  # pad if needed

                # Predict
                spec = spec.unsqueeze(0).to(self.model_config.device)
                outputs = self.model(spec)

                confs = softmax(outputs, dim=1).squeeze(0).cpu().numpy()

                row = {"sentence_idx": seg.sentence_idx}
                for label_name, prob_val in zip(self.label_names, confs):
                    row[label_name] = prob_val

                results.append(row)

        # === TRANSFORM OUTPUT ===
        preds_df = pd.DataFrame(
            results
        )  # shape (n_chunks, n_labels) - confidences per label for each chunk
        mean_confs = preds_df.groupby(
            "sentence_idx"
        ).mean()  # shape (n_sentences, n_labels) - averaged confidences per sentence

        winners = mean_confs.idxmax(
            axis=1
        )  # shape (n_sentences,) - map sentence_idx to label with highest conf
        scores = mean_confs.max(
            axis=1
        )  # shape (n_sentences,) - map sentence_idx to highest conf value

        result_df = transcript.copy()
        result_df["label"] = result_df.index.map(winners)
        result_df["confidence"] = result_df.index.map(scores)

        result_df["label"] = result_df["label"].fillna("unknown")
        result_df["confidence"] = result_df["confidence"].fillna(0.0)

        return result_df
