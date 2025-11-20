import dataset
from download import download_all
from dataset import Dataset
from merge import parse_crema, parse_ravdess, parse_savee, parse_tess

if __name__ == '__main__':
    raw_datasets = download_all()
    
    merged_dataset = Dataset()
    parse_tess(raw_datasets['TESS'], merged_dataset)
    parse_ravdess(raw_datasets['RAVDESS'], merged_dataset)
    parse_crema(raw_datasets['CREMA'], merged_dataset)
    parse_savee(raw_datasets['SAVEE'], merged_dataset)

    merged_dataset.dump('./data')
