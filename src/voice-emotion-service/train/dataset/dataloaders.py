from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader

from common.config.dataset_config import AugmentsConfig
from common.config.model_config import ModelConfig
from dataset.spec_dataset import SpecDataset


def create_dataloaders(dataset: SpecDataset, model_config: ModelConfig, aug_config: AugmentsConfig):
    # Split Actors, not Samples
    all_actors = list(set(s.actor for s in dataset.samples))
    train_actors, temp_actors = train_test_split(all_actors, test_size=0.2, random_state=42)
    val_actors, test_actors = train_test_split(temp_actors, test_size=0.5, random_state=42)

    print(f"Split Stats (Actors): Train={len(train_actors)}, Val={len(val_actors)}, Test={len(test_actors)}")

    # 3. Filter Samples based on Actor Split
    train_samples = [s for s in dataset.samples if s.actor in train_actors]
    val_samples   = [s for s in dataset.samples if s.actor in val_actors]
    test_samples  = [s for s in dataset.samples if s.actor in test_actors]

    print(f"Split Stats (Samples): Train={len(train_samples)}, Val={len(val_samples)}, Test={len(test_samples)}")

    # 4. Create Datasets
    train_ds = SpecDataset(dataset.config, aug_config, train_samples, is_train=True)
    val_ds = SpecDataset(dataset.config, aug_config, val_samples, is_train=False)
    test_ds = SpecDataset(dataset.config, aug_config, test_samples, is_train=False)

    # 5. Create DataLoaders
    # shuffle=True only for training
    train_loader = DataLoader(train_ds, batch_size=model_config.batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_ds, batch_size=model_config.batch_size, shuffle=False, num_workers=2)
    test_loader = DataLoader(test_ds, batch_size=model_config.batch_size, shuffle=False, num_workers=2)

    return train_loader, val_loader, test_loader
