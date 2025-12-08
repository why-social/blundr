import torch
import torch.nn as nn
from common.config.dataset_config import AugmentsConfig, DatasetConfig
from common.config.model_config import ModelConfig
from common.model.crnn_model import CRNNModel, train_crnn
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


    model = CRNNModel(
        MODEL_CONFIG, DATASET_CONFIG.n_mels, DATASET_CONFIG.n_classes
    ).to(MODEL_CONFIG.device)

    train_crnn(model, MODEL_CONFIG, DATASET_CONFIG, train_loader, val_loader)

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
