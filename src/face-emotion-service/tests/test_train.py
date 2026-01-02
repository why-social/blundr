import csv
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image
from train import EPOCHS as EPOCHS
from train import INPUT_SIZE as INPUT_SIZE
from train import TRAIN_TRANSFORM as TRAIN_TRANSFORM
from train import VAL_TRANSFORM as VAL_TRANSFORM
from train import ManifestDataset as ManifestDataset
from train import TransformSubset as TransformSubset
from train import compute_class_weights as compute_class_weights
from train import initialize_model as initialize_model
from train import setup_training as setup_training
from train import split_manifest_dataset as split_manifest_dataset
from train import torch as torch
from train import train_model as train_model


# For ci pipeline
@pytest.fixture
def mock_model():
    fake_model = MagicMock()
    with patch("torch.load", return_value=fake_model), \
         patch("torch.nn.Module.to", return_value=fake_model):
         yield fake_model

def make_manifest(tmp_path, rows):
    manifest_file = tmp_path / "manifest.csv"
    with open(manifest_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["path","label"])
        for row in rows:
            writer.writerow(row)
    file.close()
    return manifest_file

def test_manifest_dataset_length(tmp_path):
    manifest_file = make_manifest(tmp_path, [("img1.png","happy"), ("img2.png","sad")])

    with patch("torch.load"), patch("torch.save"), patch("PIL.Image.open"), \
         patch("torchvision.transforms.ToTensor", return_value=lambda x: "tensor"):

        dataset = ManifestDataset(str(manifest_file), transform=None, cache_dir=str(tmp_path))
        dataset.load_samples()
        assert len(dataset) == 2

def test_getitem_cache(tmp_path):
    manifest_file = make_manifest(tmp_path, [("img1.png","happy"), ("img2.png","sad")])
    
    dataset = ManifestDataset(str(manifest_file), transform=None, cache_dir=str(tmp_path))
    dataset.load_samples()

    fake_tensor = MagicMock()
    with patch("os.path.exists", return_value=True), \
         patch("torch.load", return_value=fake_tensor) as mock_load, \
         patch("PIL.Image.open"), \
         patch("torchvision.transforms.ToTensor", return_value=lambda x: "tensor"):
        
        img, label = dataset[0]
        mock_load.assert_called_once()
        assert img == fake_tensor
        assert label == 0

def test_getitem_second_index(tmp_path):
    manifest_file = make_manifest(tmp_path, [("img1.png","happy"), ("img2.png","sad")])
    
    dataset = ManifestDataset(str(manifest_file), transform=None, cache_dir=str(tmp_path))
    dataset.load_samples()

    fake_tensor = MagicMock()
    with patch("os.path.exists", return_value=True), \
         patch("torch.load", return_value=fake_tensor):
        img, label = dataset[1]
        assert img == fake_tensor
        assert label == 1

def test_getitem_no_cache(tmp_path):
    manifest_file = make_manifest(tmp_path, [("img1.png","happy")])
    
    dataset = ManifestDataset(str(manifest_file), transform=None, cache_dir=str(tmp_path))
    dataset.load_samples()

    fake_image = MagicMock()
    fake_image.convert.return_value = fake_image

    with patch("os.path.exists", return_value=False), \
        patch("PIL.Image.open", return_value=fake_image) as mock_open, \
        patch("torchvision.transforms.ToTensor", return_value=lambda x: "tensor"), \
        patch("torch.save") as mock_save:

        img, label = dataset[0]
        mock_open.assert_called_once()
        mock_save.assert_called_once()
        assert img == "tensor"
        assert label == 0

def test_empty_manifest(tmp_path):
    manifest_file = make_manifest(tmp_path, [])
    
    dataset = ManifestDataset(str(manifest_file), transform=None, cache_dir=str(tmp_path))
    dataset.load_samples()
    assert len(dataset) == 0
    assert dataset.class_to_idx == {}    

def test_duplicate_labels(tmp_path):
    manifest_file = make_manifest(tmp_path, [("img1.png","happy"), ("img2.png","happy")])
    
    dataset = ManifestDataset(str(manifest_file), transform=None, cache_dir=str(tmp_path))
    dataset.load_samples()

    assert dataset.class_to_idx ==  {"happy": 0}
    assert len(dataset) == 2

def test_getitem_file_not_found(tmp_path):
    manifest_file = make_manifest(tmp_path, [("missing.png","happy")])
    
    dataset = ManifestDataset(str(manifest_file), transform=None, cache_dir=str(tmp_path))
    dataset.load_samples()
    
    with patch("os.path.exists", return_value=False), \
         patch("PIL.Image.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            _ = dataset[0]

def test_transform_applied(tmp_path):
    manifest_file = make_manifest(tmp_path, [("img1.png","happy"), ("img2.png","sad")])
    
    dataset = ManifestDataset(str(manifest_file), transform=None, cache_dir=str(tmp_path))
    dataset.load_samples()
    
    fake_tensor = "tensor"
    mock_transform = MagicMock(return_value="transformed")

    with patch("os.path.exists", return_value=True), patch("torch.load", return_value=fake_tensor):
        dataset.transform = mock_transform
        img, label = dataset[0]
        mock_transform.assert_called_once_with(fake_tensor)
        assert img == "transformed"

def test_class_to_idx_correct(tmp_path):
    manifest_file = make_manifest(tmp_path, [("img1.png", "happy"), ("img2.png", "sad")])
    
    dataset = ManifestDataset(str(manifest_file))
    dataset.load_samples()
    
    assert dataset.class_to_idx == {"happy": 0, "sad": 1}

def test_transform_varies_per_index(tmp_path):
    manifest_file = make_manifest(tmp_path, [("img1.png","happy"), ("img2.png","sad")])
    
    dataset = ManifestDataset(str(manifest_file), transform=None, cache_dir=str(tmp_path))
    dataset.load_samples()

    transform_mock = MagicMock(side_effect=lambda x: f"transformed_{x}")
    dataset.transform = transform_mock

    with patch("os.path.exists", return_value=True), patch("torch.load", return_value="tensor"):
        img0, _ = dataset[0]
        img1, _ = dataset[1]

        assert img0 == "transformed_tensor"
        assert img1 == "transformed_tensor"
        assert transform_mock.call_count == 2

def test_transformsubset_length():
    subset = [(MagicMock(), 0), (MagicMock(), 1)]
    transformed_subset = TransformSubset(subset)
    assert len(transformed_subset) == 2

def test_getitem_with_transform():
    subset = [(1, "a"), (2, "b")]
    transformed_subset = TransformSubset(subset, transform=lambda x: x*10)
    img, label = transformed_subset[1]
    assert img == 20
    assert label == "b"

def test_getitem_with_no_transform():
    subset = [(1, "a"), (2, "b")]
    transformed_subset = TransformSubset(subset)
    img, label = transformed_subset[0]
    assert img == 1
    assert label == "a"

def test_initialize_model_single_device():
    fake_model = MagicMock()

    with patch("train.models.resnet34", return_value=fake_model), \
         patch("train.torch.cuda.device_count", return_value=1):

        device = MagicMock()
        fake_model.to.return_value = fake_model

        model = initialize_model(num_classes=3, device=device)

        fake_model.to.assert_called_once_with(device)
        assert model is fake_model

def test_initialize_model_uses_datapararell():
    fake_model = MagicMock()
    fake_parallel = MagicMock()

    with patch("train.models.resnet34", return_value=fake_model), \
         patch("train.torch.cuda.device_count", return_value=2), \
         patch("train.nn.DataParallel", return_value=fake_parallel):

        device = MagicMock()
        fake_model.to.return_value = fake_model

        model = initialize_model(num_classes=3, device=device)

        fake_model.to.assert_called_once_with(device)
        assert model is fake_parallel

#Split dataset section
def test_split_dataset_create_and_load():
    fake_dataset = MagicMock()

    with patch("train.ManifestDataset", return_value=fake_dataset):
        split_manifest_dataset("fake.csv", val_fraction=0.2)

        fake_dataset.load_samples.assert_called_once()

def test_split_dataset_correct_split_size():
    fake_dataset = MagicMock()
    fake_dataset.__len__.return_value = 10

    with patch("train.ManifestDataset", return_value=fake_dataset), \
         patch("train.random_split", return_value=(MagicMock(), MagicMock)) as mock_split:
        split_manifest_dataset("fake.csv", val_fraction=0.2)

        fake_dataset.load_samples.assert_called_once()

        mock_split.assert_called_once_with(fake_dataset, [8, 2])

def test_split_dataset_correct_transform_wrap():
    fake_dataset = MagicMock()
    fake_dataset.__len__.return_value = 10

    with patch("train.ManifestDataset", return_value=fake_dataset), \
         patch("train.random_split", return_value=(MagicMock(), MagicMock())):
        

        train_dataset, validation_dataset, _ =split_manifest_dataset("fake.csv", val_fraction=0.2)

        assert isinstance(train_dataset, TransformSubset)
        assert isinstance(validation_dataset, TransformSubset)
        assert train_dataset.transform is TRAIN_TRANSFORM
        assert validation_dataset.transform is VAL_TRANSFORM

#Compute class weights
def test_compute_class_weights():
    samples = [
        ("img1", 0, "c1"),
        ("img2", 0, "c2"),
        ("img3", 1, "c3")
    ]
    num_classes = 2
    device = MagicMock()

    fake_tensor = MagicMock()

    with patch("train.torch.tensor", return_value=fake_tensor) as mock_tensor:
        fake_tensor.to.return_value = fake_tensor

        weights = compute_class_weights(samples, num_classes, device)

        mock_tensor.assert_called_once_with([0.75, 1.5], dtype=torch.float)
        fake_tensor.to.assert_called_once_with(device)
        assert weights is fake_tensor
        
#Setup training test
def test_setup_training():
    fake_model = MagicMock()
    fake_optimizer = MagicMock()
    fake_scheduler = MagicMock()
    fake_class_weights = MagicMock()
    fake_train_loader = MagicMock()

    epochs = 30
    learning_rate = 1e-3

    fake_train_loader.__len__.return_value = 10

    with patch("train.nn.CrossEntropyLoss", return_value="loss_fn") as mock_loss, \
         patch("train.optim.Adam", return_value=fake_optimizer) as mock_optim, \
         patch("train.torch.optim.lr_scheduler.OneCycleLR", return_value=fake_scheduler) as mock_scheduler:
        
        criterion, optimizer, scheduler = setup_training(
            fake_model,
            fake_class_weights,
            learning_rate=learning_rate,
            epochs=epochs,
            train_loader=fake_train_loader
        )

        mock_loss.assert_called_once_with(weight=fake_class_weights, label_smoothing=0.05)
        mock_optim.assert_called_once_with(fake_model.parameters(), lr=learning_rate)
        mock_scheduler.assert_called_once_with(
            fake_optimizer,
            max_lr=learning_rate,
            steps_per_epoch=len(fake_train_loader),
            epochs=epochs
        )

        assert criterion == "loss_fn"
        assert optimizer == fake_optimizer
        assert scheduler == fake_scheduler

#Train model test
def test_train_model_train_and_eval():
    fake_model = MagicMock()
    fake_criterion = MagicMock()
    fake_optimizer = MagicMock()
    fake_scheduler = MagicMock()
    device = MagicMock()

    mock_labels = MagicMock()
    mock_images = MagicMock()

    mock_labels.to.return_value = mock_labels
    mock_images.to.return_value = mock_images


    fake_val_loader = [(mock_images, mock_labels)]
    fake_train_loader = [(mock_images, mock_labels)]
    
    fake_loss = MagicMock()
    fake_loss.item.return_value = 0.5
    fake_criterion.return_value = fake_loss
    
    mock_labels.__eq__.return_value.sum.return_value.item.return_value = 1
    mock_labels.size.return_value = 1

    with patch("train.torch.save"), patch("train.torch.max", return_value=(MagicMock(), MagicMock())), patch("builtins.print"):
        best_acc = train_model(
            fake_model, fake_train_loader, fake_val_loader,
            fake_criterion, fake_optimizer, fake_scheduler, device
        )

    assert fake_model.train.call_count == EPOCHS
    assert fake_model.eval.call_count == EPOCHS
    assert fake_optimizer.zero_grad.call_count == EPOCHS
    assert fake_optimizer.step.call_count == EPOCHS
    assert fake_scheduler.step.call_count == EPOCHS
    
    assert best_acc == 1.0

# Image transformation testing
def test_train_transform_output_shape():
    img = torch.rand(3, 100, 100)
    output = TRAIN_TRANSFORM(img)
    assert isinstance(output, torch.Tensor)
    assert output.shape == (3, INPUT_SIZE, INPUT_SIZE)

# Final test whole pipeline, no mock data
def test_pipeline_end_to_end(tmp_path):
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    labels = ["happy", "sad", "fear", "surprise"]
    image_paths = []

    for i, label in enumerate(labels):
        img_path = image_dir / f"{label}.png"
        img = Image.new("RGB", (50, 50), color=(i*100, i*100, i*100))
        img.save(img_path)
        image_paths.append((str(img_path), label))

    manifest_file = tmp_path / "manifest.csv"
    with open(manifest_file, "w") as file:
        file.write("path,label\n")
        for path, label in image_paths:
            file.write(f"{path},{label}\n")
    dataset = ManifestDataset(str(manifest_file), cache_dir=str(tmp_path / "cache"))
    dataset.load_samples()

    assert len(dataset) == 4
    assert set(dataset.class_to_idx.keys()) == set(labels)

    train_dataset, val_dataset, complete_dataset = split_manifest_dataset(str(manifest_file))

    assert isinstance(train_dataset, TransformSubset)
    assert isinstance(val_dataset, TransformSubset)

    img, label = train_dataset[0]
    assert isinstance(img, torch.Tensor)
    assert img.shape == (3, INPUT_SIZE, INPUT_SIZE)
    assert img.min() >= -1.0 and img.max() <= 1.0
    assert isinstance(label, int)

    device = torch.device("cpu")
    model = initialize_model(num_classes=len(dataset.class_to_idx), device=device)
    batch = torch.stack([train_dataset[0][0], train_dataset[1][0]])
    output = model(batch.to(device))
    assert output.shape == (2, len(dataset.class_to_idx))
    assert torch.all(torch.isfinite(output))