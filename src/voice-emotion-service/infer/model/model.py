from pathlib import Path
from typing import List

import torch
from common.config.dataset_config import DatasetConfig
from common.config.model_config import ModelConfig
from common.model.crnn_model import CRNNModel
from common.utils.audio_processing import AudioProcessor
from common.utils.transformations import standardize_length
from data.load import load_transcribed_segments
from data.prediction import Prediction
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

    def infer(self, audio_path: Path, transcript: str) -> List[Prediction]:
        segments = load_transcribed_segments(
            transcript, Path(audio_path), self.data_config
        )
        print(f"Split into {len(segments)} chunks for inference.")

        results = []
        with torch.no_grad():
            for seg in tqdm(segments, desc="Predicting"):
                spec = self.processor.segment_to_spec(seg)  # load chunk (<= target_len)
                spec = standardize_length(
                    spec, self.data_config.target_frames, mode="end"
                )  # pad if needed

                # Predict
                spec = spec.unsqueeze(0).to(self.model_config.device)
                outputs = self.model(spec)

                probs = softmax(outputs, dim=1)
                confidence, pred_idx = torch.max(probs, 1)

                emotion = self.label_map.get(pred_idx.item())
                if emotion is None:
                    emotion = "unknown"

                results.append(
                    Prediction(
                        start_time=seg.start_time,
                        end_time=seg.end_time,
                        label=emotion,
                        confidence=confidence.item(),
                    )
                )

        return results
