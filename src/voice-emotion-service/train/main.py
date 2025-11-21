from config.model_config import ModelConfig
from dataset.spec_dataset import SpecDataset
from config.dataset_config import DatasetConfig
from dataset.download import download_all
from dataset.merge import merge_datasets


if __name__ == '__main__':
    raw_datasets = download_all()

    dataset = SpecDataset(DatasetConfig())
    merged_dataset = merge_datasets(raw_datasets, dataset)
    dataset.preprocess(num_workers=8)

    config = ModelConfig()
