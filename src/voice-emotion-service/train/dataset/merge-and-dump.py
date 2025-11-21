from config.dataset_config import DatasetConfig
from download import download_datasets
from dataset import Dataset
from merge import merge_datasets

if __name__ == '__main__':
    raw_datasets = download_datasets()

    dataset = Dataset(DatasetConfig)
    merged_dataset = merge_datasets(raw_datasets, Dataset)
    merged_dataset.dump('./data')
