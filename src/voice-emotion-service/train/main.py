from dataset.dataset import Dataset
from dataset.config import DatasetConfig
from dataset.download import download_all
from dataset.merge import merge_datasets

if __name__ == '__main__':
    raw_datasets = download_all()

    dataset = Dataset(DatasetConfig())
    merged_dataset = merge_datasets(raw_datasets, dataset)
    print(merged_dataset[0])
