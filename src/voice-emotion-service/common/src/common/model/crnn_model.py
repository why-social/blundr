from common.config.dataset_config import DatasetConfig
import torch
import torch.nn as nn
import torch.nn.functional as F
from common.config.model_config import ModelConfig
from torch.utils.data import DataLoader


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


def train_crnn(model: CRNNModel, model_config: ModelConfig, data_config: DatasetConfig, train_loader: DataLoader, val_loader: DataLoader):
    train_labels = [s.emotion for s in train_loader.dataset.samples]
    class_counts = [train_labels.count(k) for k in data_config.label_map.keys()]
    total_samples = sum(class_counts)
    weights = [
        total_samples / (len(class_counts) * c) if c > 0 else 0 for c in class_counts
    ]

    class_weights = torch.FloatTensor(weights).to(model_config.device)
    print(f"Class Weights: {weights}")
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=model_config.learning_rate,
        weight_decay=model_config.weight_decay,
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", factor=0.5, patience=3
    )

    best_val_acc = 0.0

    for epoch in range(model_config.epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        print(f"\nEpoch {epoch + 1}/{model_config.epochs}")

        for inputs, labels in train_loader:
            inputs, labels = (
                inputs.to(model_config.device),
                labels.to(model_config.device),
            )

            optimizer.zero_grad()

            outputs = model(inputs)
            loss = criterion(outputs, labels)

            loss.backward()
            optimizer.step()

            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

        epoch_acc = 100 * correct / total
        print(
            f"Train Loss: {running_loss / len(train_loader):.4f} | Acc: {epoch_acc:.2f}%"
        )

        # VALIDATION
        model.eval()
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = (
                    inputs.to(model_config.device),
                    labels.to(model_config.device),
                )
                outputs = model(inputs)
                _, predicted = torch.max(outputs.data, 1)
                val_total += labels.size(0)
                val_correct += (predicted == labels).sum().item()

        val_acc = 100 * val_correct / val_total
        print(f"Validation Acc: {val_acc:.2f}%")

        scheduler.step(val_acc)

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            print("New Best.")
            if val_acc >= model_config.save_thresh:
                torch.save(model.state_dict(), model_config.out_path)
                print("Saved.")
