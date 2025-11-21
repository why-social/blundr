from dataclasses import dataclass

@dataclass
class ModelConfig:
    hidden_size: int = 128
    learning_rate: float = 0.001
    epochs: int = 20

    @property
    def device(self) -> str:
        from torch.cuda import is_available
        return "cuda" if is_available() else "cpu"
