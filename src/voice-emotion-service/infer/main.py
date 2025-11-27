import argparse
from pathlib import Path

import pandas as pd
import torch

# --- IMPORTS FROM COMMON SHARED LIB ---
from common.config.dataset_config import DatasetConfig
from common.config.model_config import ModelConfig
from common.model.crnn_model import CRNNModel
from common.utils.audio_processing import AudioProcessor
from common.utils.transformations import standardize_length
from data.load import load_transcribed_segments
from tqdm import tqdm

SAVE_PATH = Path("out/emotion_predictions.csv")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("model_path", type=str)
    parser.add_argument("--audio_path", type=str, required=True)
    parser.add_argument("--trans_path", type=str, required=True)
    parser.add_argument("--out_path", type=str)
    args = parser.parse_args()

    if args.out_path is not None:
        SAVE_PATH = Path(args.out_path)

    model_config = ModelConfig()
    data_config = DatasetConfig()
    processor = AudioProcessor(data_config)

    model = CRNNModel(
        model_config,
        n_mels=data_config.n_mels,
        num_classes=data_config.n_classes,
    ).to(model_config.device)

    model.load_state_dict(torch.load(args.model_path, map_location=model_config.device))
    model.eval()

    segments = load_transcribed_segments(
        Path(args.trans_path), Path(args.audio_path), data_config
    )
    print(f"Split into {len(segments)} chunks for inference.")

    results = []
    with torch.no_grad():
        for seg in tqdm(segments, desc="Predicting"):
            spec = processor.segment_to_spec(seg)  # load chunk (<= target_len)
            spec = standardize_length(
                spec, data_config.target_frames, mode="end"
            )  # pad if needed

            # Predict
            spec = spec.unsqueeze(0).to(model_config.device)
            outputs = model(spec)
            confidence, pred_idx = torch.max(outputs, 1)

            emotion = data_config.label_map_reverse.get(pred_idx.item())
            if emotion is None:
                emotion = "unknown"

            results.append(
                {
                    "file": seg.audio_path.name,
                    "start": f"{seg.start_time:.2f}",
                    "end": f"{seg.end_time:.2f}",
                    "emotion": emotion,
                    "confidence": confidence,
                }
            )

    pd.DataFrame(results).to_csv(str(SAVE_PATH), index=False)
    print(f"Saved to {SAVE_PATH}")
