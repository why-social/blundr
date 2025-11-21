from dataset.augment import augment_dataset
import torch
import torch.nn as nn

from config.model_config import ModelConfig
from dataset.spec_dataset import SpecDataset
from dataset.augment import augment_dataset
from config.dataset_config import AugmentsConfig, DatasetConfig
from dataset.download import download_datasets
from dataset.merge import merge_datasets
from model.dataloaders import create_dataloaders
from model.crnn_model import CRNNModel


if __name__ == '__main__':
    dataset_config = DatasetConfig()
    raw_datasets = download_datasets(dataset_config.raw_data_dir)

    augment_dataset(raw_datasets, AugmentsConfig())

    dataset = SpecDataset(dataset_config)
    merged_dataset = merge_datasets(raw_datasets, dataset)
    dataset.preprocess(num_workers=8)

    config = ModelConfig()
    train_loader, val_loader, test_loader = create_dataloaders(dataset, config)

    train_labels = [s.emotion for s in train_loader.dataset.samples]
    class_counts = [train_labels.count(k) for k in dataset.label_map.keys()]
    total_samples = sum(class_counts)
    weights = [total_samples / (len(class_counts) * c) if c > 0 else 0 for c in class_counts]
    class_weights = torch.FloatTensor(weights).to(config.device)
    print(f"Class Weights: {weights}")

    model = CRNNModel(config, dataset.config.n_mels, len(dataset.label_map.keys())).to(config.device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)

    for epoch in range(config.epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        print(f"\nEpoch {epoch+1}/{config.epochs}")

        for inputs, labels in train_loader:
            inputs, labels = inputs.to(config.device), labels.to(config.device)

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
        print(f"Train Loss: {running_loss/len(train_loader):.4f} | Acc: {epoch_acc:.2f}%")

        # VALIDATION
        model.eval()
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(config.device), labels.to(config.device)
                outputs = model(inputs)
                _, predicted = torch.max(outputs.data, 1)
                val_total += labels.size(0)
                val_correct += (predicted == labels).sum().item()

        val_acc = 100 * val_correct / val_total
        print(f"Validation Acc: {val_acc:.2f}%")

    print("Training Complete. Goodbye!")
