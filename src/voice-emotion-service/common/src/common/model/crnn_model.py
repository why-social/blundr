# Original Author: Maxine Orlen
# Source: https://git.chalmers.se/courses/dit826/2025/team2
# License: MIT

import torch
import torch.nn as nn
import torch.nn.functional as F
from common.config.model_config import ModelConfig


class CRNNModel(nn.Module):
    def __init__(self, config: ModelConfig, n_mels: int, num_classes: int):
        super(CRNNModel, self).__init__()

        config.out_path.parent.mkdir(parents=True, exist_ok=True)

        # CNN Block
        self.conv1 = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Dropout(0.1),
        )
        self.conv2 = nn.Sequential(
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Dropout(0.1),
        )
        self.conv3 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Dropout(0.1),
        )

        cnn_out_height = n_mels // 8
        self.cnn_flat_size = 128 * cnn_out_height

        self.projection = nn.Linear(self.cnn_flat_size, 64)

        # --- 3. LSTM Block ---
        self.lstm = nn.LSTM(
            input_size=64,
            hidden_size=config.hidden_size,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=0.4,
        )

        self.attention = nn.Sequential(
            nn.Linear(config.hidden_size * 2, 1),
            nn.Tanh(),
        )

        # --- 5. Classifier ---
        self.classifier = nn.Sequential(
            nn.Linear(config.hidden_size * 2, 64),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(64, num_classes),
        )

    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)

        # Reshape
        x = x.permute(0, 3, 1, 2)
        b, t, c, f = x.size()
        x = x.reshape(b, t, c * f)

        # Bottleneck Projection
        x = self.projection(x)

        # LSTM
        lstm_out, _ = self.lstm(x)

        # --- Attention Aggregation ---
        attn_weights = self.attention(lstm_out)
        attn_weights = F.softmax(attn_weights, dim=1)

        # Multiply weights by LSTM output and sum -> Weighted Average
        context = torch.sum(attn_weights * lstm_out, dim=1)

        return self.classifier(context)
