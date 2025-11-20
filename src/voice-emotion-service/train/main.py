from dataset.dataset import SpecDataset
from dataset.config import DatasetConfig
from dataset.download import download_all
from dataset.merge import merge_datasets

if __name__ == '__main__':
    raw_datasets = download_all()

    dataset = SpecDataset(DatasetConfig())
    merged_dataset = merge_datasets(raw_datasets, dataset)
    dataset.preprocess(num_workers=8)
    print(dataset[1])
