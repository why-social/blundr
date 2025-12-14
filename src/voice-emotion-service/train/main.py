import torch
from torch import nn
from common.config.dataset_config import AugmentsConfig, DatasetConfig
from common.config.model_config import ModelConfig
from common.model.crnn_model import CRNNModel
from dataset.augment import augment_dataset
from dataset.dataloaders import create_dataloaders
from dataset.download import download_datasets
from dataset.merge import merge_datasets
from dataset.spec_dataset import SpecDataset

DATASET_CONFIG = DatasetConfig()
AUGMENTS_CONFIG = AugmentsConfig()
MODEL_CONFIG = ModelConfig()

if __name__ == "__main__":
    raw_datasets = download_datasets(DATASET_CONFIG.raw_data_dir)

    augment_dataset(raw_datasets, AUGMENTS_CONFIG)

    dataset = SpecDataset(DATASET_CONFIG, AUGMENTS_CONFIG, is_train=True)
    merged_dataset = merge_datasets(raw_datasets, dataset)
    dataset.preprocess(num_workers=10, batch_size=24)

    train_loader, val_loader, test_loader = create_dataloaders(
        dataset, MODEL_CONFIG, AUGMENTS_CONFIG
    )

    train_labels = [s.emotion for s in train_loader.dataset.samples]
    class_counts = [train_labels.count(k) for k in dataset.label_map.keys()]
    total_samples = sum(class_counts)
    weights = [
        total_samples / (len(class_counts) * c) if c > 0 else 0 for c in class_counts
    ]
    class_weights = torch.FloatTensor(weights).to(MODEL_CONFIG.device)
    print(f"Class Weights: {weights}")

    model = CRNNModel(
        MODEL_CONFIG, dataset.config.n_mels, len(dataset.label_map.keys())
    ).to(MODEL_CONFIG.device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=MODEL_CONFIG.learning_rate,
        weight_decay=MODEL_CONFIG.weight_decay,
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", factor=0.5, patience=3
    )

    best_val_acc = 0.0

    for epoch in range(MODEL_CONFIG.epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        print(f"\nEpoch {epoch + 1}/{MODEL_CONFIG.epochs}")

        for inputs, labels in train_loader:
            inputs, labels = (
                inputs.to(MODEL_CONFIG.device),
                labels.to(MODEL_CONFIG.device),
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
                    inputs.to(MODEL_CONFIG.device),
                    labels.to(MODEL_CONFIG.device),
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
            if val_acc >= MODEL_CONFIG.save_thresh:
                torch.save(model.state_dict(), MODEL_CONFIG.out_path)
                print("Saved.")

    model.load_state_dict(torch.load(MODEL_CONFIG.out_path))
    model.eval()
    test_loss = 0
    val_total = 0
    val_correct = 0
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = (
                inputs.to(MODEL_CONFIG.device),
                labels.to(MODEL_CONFIG.device),
            )
            outputs = model(inputs)
            _, predicted = torch.max(outputs.data, 1)
            val_correct += (predicted == labels).sum().item()
            val_total += labels.size(0)

    print(
        "\nTest set: Accuracy: {}/{} ({:.0f}%)\n".format(
            val_correct,
            len(test_loader.dataset),
            100.0 * val_correct / len(test_loader.dataset),
        )
    )

    print("Training Complete. Goodbye!")
