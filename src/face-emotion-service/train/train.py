# Original Author: Aliaksei Khval
# Co-authored by: Danis Music, Maxine Orlen
# Source: https://git.chalmers.se/courses/dit826/2025/team2
# License: MIT

# Training script: ResNet34 from scratch (no pretrained weights)
import csv
import hashlib
import json
import os

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
from PIL import Image
from torch.utils.data import DataLoader, Dataset, random_split
from torchvision import models
from tqdm import tqdm

VAL_FRACTION = 0.2
LEARNING_RATE = 1e-3
EPOCHS = 30
INPUT_SIZE = 128

TRAIN_TRANSFORM = transforms.Compose([
		transforms.Grayscale(num_output_channels=3),
		transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
		transforms.RandomHorizontalFlip(),
		transforms.RandomRotation(8),
		transforms.Normalize([0.5]*3, [0.5]*3),
		transforms.RandomErasing(p=0.3, scale=(0.02, 0.2), ratio=(0.3, 3.3)),
	])

VAL_TRANSFORM = transforms.Compose([
		transforms.Grayscale(num_output_channels=3),
		transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
		transforms.Normalize([0.5]*3, [0.5]*3)
	])

MODEL_VERSION = os.getenv('MODEL_VERSION')
assert MODEL_VERSION is not None, "Must define MODEL_VERSION"

MODEL_BASE_PATH = os.getenv('MODEL_BASE_PATH', '/models')
MANIFEST_PATH = f"{MODEL_BASE_PATH}/{MODEL_VERSION}/manifest.csv"


def _get_cores_num():
	try:
		num_cores = len(os.sched_getaffinity(0))
	except AttributeError:
		num_cores = os.cpu_count()

	if not num_cores:
		num_cores = 4
		print("WARN: Could not determine core count. Assuming 4.")
	
	return num_cores

def get_workers_num():
	num_cores = _get_cores_num()
	num_workers = num_cores - 2 if num_cores > 2 else 2
	print(f"Using {num_workers} workers.")
	return num_workers

def get_batch_size():
	num_cores = _get_cores_num()

	if num_cores >= 32:
		optimal_bs = 64
	elif num_cores >= 16:
		optimal_bs = 32
	else:
		optimal_bs = 16
		
	print(f"Selected CPU batch size: {optimal_bs} ({num_cores} cores)")
	return optimal_bs


BATCH_SIZE = get_batch_size()
WORKERS_NUM = get_workers_num()

# Dataset definition
class ManifestDataset(Dataset):
	def __init__(self, manifest_path, transform=None, cache_dir="/tmp/image_cache"):
		self.transform = transform
		self.cache_dir = cache_dir
		self.manifest_path = manifest_path
		self.samples = []
		self.class_to_idx = {}

	def load_samples(self):
		os.makedirs(self.cache_dir, exist_ok=True)

		with open(self.manifest_path) as f:
			rows = list(csv.DictReader(f))

		labels = sorted({r["label"] for r in rows})
		self.class_to_idx = {label: i for i, label in enumerate(labels)}

		self.samples = []
		base_path = os.getenv("IMAGE_BASE_PATH", "/data")

		for r in rows:
			img_path = os.path.join(base_path, r["path"])
			key = hashlib.md5(img_path.encode()).hexdigest()
			self.samples.append((
				img_path,
				self.class_to_idx[r["label"]],
				os.path.join(self.cache_dir, f"{key}.pt")
			))

	def __len__(self):
		return len(self.samples)

	def __getitem__(self, idx):
		img_path, label, cache_path = self.samples[idx]

		if os.path.exists(cache_path):
			image = torch.load(cache_path)
		else:
			image = Image.open(img_path).convert("RGB")
			image = transforms.ToTensor()(image)
			torch.save(image, cache_path)

		if self.transform:
			image = self.transform(image)

		return image, label

class TransformSubset(torch.utils.data.Dataset):
	def __init__(self, subset, transform=None):
		self.subset = subset
		self.transform = transform

	def __len__(self):
		return len(self.subset)

	def __getitem__(self, idx):
		image, label = self.subset[idx]
		if self.transform:
			image = self.transform(image)
		return image, label

def initialize_model(num_classes, device, use_pretrained=False):
	"""
	Initializes an untrained resnet model that either uses GPU or CPU
	"""
	model = models.resnet34(weights=None)
	model.fc = nn.Sequential(
		nn.Linear(512, 256),
		nn.ReLU(),
		nn.Dropout(0.4),
		nn.Linear(256, num_classes)
	)
	# Select device
	model = model.to(device)
	# Use DataParallel if multiple GPUs are available
	if torch.cuda.device_count() > 1:
		print(f"Using {torch.cuda.device_count()} GPUs!")
		model = nn.DataParallel(model)

	return model

def split_manifest_dataset(manifest_path, val_fraction=0.2):
	# Load dataset
	dataset = ManifestDataset(manifest_path, transform=None)
	dataset.load_samples()
	print("Classes:", dataset.class_to_idx)

	# Split dataset into training and validation sets
	train_size = int((1 - VAL_FRACTION) * len(dataset))
	val_size = len(dataset) - train_size

	# Use random_split to create train and validation datasets
	train_subset, val_subset = random_split(dataset, [train_size, val_size])

	# Apply transforms to datasets
	train_dataset = TransformSubset(train_subset, transform=TRAIN_TRANSFORM)
	val_dataset = TransformSubset(val_subset, transform=VAL_TRANSFORM)

	return train_dataset, val_dataset, dataset

def compute_class_weights(samples, num_classes, device):
	class_counts = [0] * num_classes
	for _, label_idx, _ in samples:
		class_counts[label_idx] += 1

	# Compute class weights: inverse frequency
	total = sum(class_counts)
	class_weights = [total / (num_classes * c) for c in class_counts]
	return torch.tensor(class_weights, dtype=torch.float).to(device)

def setup_training(model, class_weights, learning_rate=LEARNING_RATE, epochs=EPOCHS, train_loader=None):
	# Define loss function and optimizer
	criterion = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=0.05)

	# Optimizer and scheduler
	optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
	scheduler = torch.optim.lr_scheduler.OneCycleLR(
		optimizer,
		max_lr=LEARNING_RATE,
		steps_per_epoch=len(train_loader),
		epochs=EPOCHS
	)
	return criterion, optimizer, scheduler

def train_model(model, train_loader, val_loader, criterion, optimizer, scheduler, device):
	# Training loop
	best_acc = 0.0
	for epoch in range(EPOCHS):
		model.train()
		train_loss, train_correct, total_train = 0.0, 0, 0

		for images, labels in tqdm(train_loader):
			images, labels = images.to(device), labels.to(device)
			optimizer.zero_grad()
			outputs = model(images)
			loss = criterion(outputs, labels)
			loss.backward()
			optimizer.step()
			scheduler.step()

			train_loss += loss.item()
			_, preds = torch.max(outputs, 1)
			train_correct += (preds == labels).sum().item()
			total_train += labels.size(0)

		train_acc = train_correct / total_train

		# Validation
		model.eval()
		val_loss, val_correct, total_val = 0.0, 0, 0
		with torch.no_grad():
			for images, labels in val_loader:
				images, labels = images.to(device), labels.to(device)
				outputs = model(images)
				loss = criterion(outputs, labels)
				val_loss += loss.item()
				_, preds = torch.max(outputs, 1)
				val_correct += (preds == labels).sum().item()
				total_val += labels.size(0)

		val_acc = val_correct / total_val
		print(f"Epoch [{epoch+1}/{EPOCHS}] "
			f"Train Loss: {train_loss/len(train_loader):.4f}, Train Acc: {train_acc:.4f} | "
			f"Val Loss: {val_loss/len(val_loader):.4f}, Val Acc: {val_acc:.4f}")

		if val_acc > best_acc:
			torch.save(model.state_dict(), f'{MODEL_BASE_PATH}/{MODEL_VERSION}/fer_model.pt')
			best_acc = val_acc
			print(f"Saved new best model with accuracy: {best_acc:.4f} to {MODEL_BASE_PATH}/{MODEL_VERSION}/fer_model.pt")
	
	return best_acc

if __name__ == "__main__":
	# Split dataset into training and validation data
	train_dataset, val_dataset, dataset = split_manifest_dataset(MANIFEST_PATH)
	num_classes = len(dataset.class_to_idx)

	# Create data loaders
	print("creating dataloaders...")
	train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=WORKERS_NUM, persistent_workers=True)
	val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=WORKERS_NUM, persistent_workers=True)

	# Initialize model
	device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
	model = initialize_model(num_classes, device)

	# compile model to enable hardware optimizations
	if device.type == 'cpu':
		try:
			print("Compiling model (torch.compile)...")
			model = torch.compile(model)
		except Exception as e:
			print(f"Could not compile model. Running standard mode. Error: {e}")

	# Count samples per class
	print("computing class weights...")
	class_weights = compute_class_weights(dataset.samples, num_classes, device)
	print(f"  class weights: {class_weights}")

	print("setting up training...")
	criterion, optimizer, scheduler = setup_training(model, class_weights, learning_rate=LEARNING_RATE, epochs=EPOCHS, train_loader=train_loader)

	print("starting training...")
	best_acc = train_model(model, train_loader, val_loader, criterion, optimizer, scheduler, device)
	print(f"Training complete. Best validation accuracy: {best_acc:.4f}")

	metadata = {
		"val_accuracy": best_acc,
		"hyperparams": {
			"learning_rate": LEARNING_RATE,
			"epochs": EPOCHS,
		},
		"data": {
			"val_fraction": VAL_FRACTION,
			"batch_size": BATCH_SIZE,
		},
	}

	with open(f'{MODEL_BASE_PATH}/{MODEL_VERSION}/metadata.json', 'w') as f:
		f.write(json.dumps(metadata))
		
