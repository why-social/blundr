from config.model_config import ModelConfig
import torch.nn as nn

class CRNNModel(nn.Module):
    def __init__(self, config: ModelConfig, n_mels: int, num_classes: int):
        super(CRNNModel, self).__init__()
        
        # CNN Block
        self.conv1 = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2) # 128->64, 300->150
        )
        self.conv2 = nn.Sequential(
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2) # 64->32, 150->75
        )
        self.conv3 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2) # 32->16, 75->37
        )

        # LSTM Block
        # Input features = channels (128) * freq_height (16) = 2048
        self.lstm_input_size = 128 * (n_mels // 8)
        self.lstm = nn.LSTM(
            input_size=self.lstm_input_size, 
            hidden_size=config.hidden_size, 
            num_layers=2, 
            batch_first=True, 
            bidirectional=True
        )

        # Classifier
        self.classifier = nn.Sequential(
            nn.Linear(config.hidden_size*2, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, num_classes)
        )

    def forward(self, x):
        # x: (batch, 1, 128, 300)
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x) 
        # x: (batch, 128, 16, 37)

        # Reshape for LSTM: (batch, time, features)
        x = x.permute(0, 3, 1, 2) # (batch, 37, 128, 16)
        b, t, c, f = x.size()
        x = x.reshape(b, t, c*f)  # (batch, 37, 2048)
        
        # LSTM
        x, _ = self.lstm(x)
        # x: (batch, 37, 256) - (hidden*2 for bidirectional)
        
        # Take the last time step
        x = x[:, -1, :]
        
        return self.classifier(x)
