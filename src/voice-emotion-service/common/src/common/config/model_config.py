from dataclasses import dataclass
from pathlib import Path


@dataclass
class ModelConfig:
    hidden_size: int = 96
    learning_rate: float = 0.001
    epochs: int = 50
    batch_size: int = 32
    weight_decay: float = 1e-4
    save_thresh: float = 0.6
    out_path: Path = Path("./out/model.pth")

    @property
    def device(self) -> str:
        from torch.cuda import is_available

        return "cuda" if is_available() else "cpu"
