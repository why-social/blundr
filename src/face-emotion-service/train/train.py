# Training script: ResNet34 from scratch (no pretrained weights)
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
from torch.amp import autocast
from torch.utils.data import DataLoader, random_split, Dataset
from torchvision import datasets, models
from tqdm import tqdm
import os
import csv
from PIL import Image

VAL_FRACTION = 0.2
BATCH_SIZE = 16
WORKERS_NUM = 4
LEARNING_RATE = 1e-3
EPOCHS = 30
INPUT_SIZE = 128

MODEL_VERSION = os.getenv('MODEL_VERSION', 'default')

MANIFEST_PATH = f"/gce/{MODEL_VERSION}/manifest.csv"

# Dataset definition
class ManifestDataset(Dataset):
	def __init__(self, manifest_path, transform=None):
		self.samples = []
		self.transform = transform

		with open(manifest_path, newline="") as f:
			reader = csv.DictReader(f)
			for row in reader:
				self.samples.append({
					"path": row["path"],
					"label": row["label"]
				})

		# Build label mapping
		labels = sorted({s["label"] for s in self.samples})
		self.class_to_idx = {label: idx for idx, label in enumerate(labels)}
		self.idx_to_class = {idx: label for label, idx in self.class_to_idx.items()}

	def __len__(self):
		return len(self.samples)

	def __getitem__(self, idx):
		sample = self.samples[idx]
		base_path = os.getenv("IMAGE_BASE_PATH", "")
		img_path = os.path.join(base_path, sample["path"])
		if not os.path.exists(img_path):
			raise FileNotFoundError(f"Image not found: {img_path}")
		label = self.class_to_idx[sample["label"]]

		image = Image.open(img_path).convert("RGB")

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


# Define data transformations
train_transform = transforms.Compose([
	transforms.Grayscale(num_output_channels=3),
	transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
	transforms.RandomHorizontalFlip(),
	transforms.RandomRotation(8),
	transforms.ToTensor(),
	transforms.Normalize([0.5]*3, [0.5]*3),
	transforms.RandomErasing(p=0.3, scale=(0.02, 0.2), ratio=(0.3, 3.3)),
])

val_transform = transforms.Compose([
	transforms.Grayscale(num_output_channels=3),
	transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
	transforms.ToTensor(),
	transforms.Normalize([0.5]*3, [0.5]*3)
])

# Load dataset
dataset = ManifestDataset(manifest_path=MANIFEST_PATH, transform=None)
num_classes = len(dataset.class_to_idx)
print("Classes:", dataset.class_to_idx)

# Split dataset into training and validation sets
train_size = int((1 - VAL_FRACTION) * len(dataset))
val_size = len(dataset) - train_size

# Use random_split to create train and validation datasets
train_subset, val_subset = random_split(dataset, [train_size, val_size])

# Apply transforms to datasets
train_dataset = TransformSubset(train_subset, transform=train_transform)
val_dataset = TransformSubset(val_subset, transform=val_transform)
# Create data loaders
train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=WORKERS_NUM)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=WORKERS_NUM)

# Initialize model
model = models.resnet34(weights=None)  # Train from scratch
model.fc = nn.Sequential(
	nn.Linear(512, 256),
	nn.ReLU(),
	nn.Dropout(0.4),
	nn.Linear(256, num_classes)
)

# Select device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)

# Use DataParallel if multiple GPUs are available
if torch.cuda.device_count() > 1:
	print(f"Using {torch.cuda.device_count()} GPUs!")
	model = nn.DataParallel(model)

# Count samples per class
class_counts = [0] * num_classes
for sample in dataset.samples:
	label_idx = dataset.class_to_idx[sample["label"]]
	class_counts[label_idx] += 1

# Compute class weights: inverse frequency
total = sum(class_counts)
class_weights = [total / (num_classes * c) for c in class_counts]
class_weights = torch.tensor(class_weights, dtype=torch.float).to(device)

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
		torch.save(model.state_dict(), f'/gce/{MODEL_VERSION}/fer_model.pt')
		best_acc = val_acc
		print(f"Saved new best model with accuracy: {best_acc:.4f} to /gce/{MODEL_VERSION}/fer_model.pt")

print("Training complete. Best validation accuracy:", best_acc)
