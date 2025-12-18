# This training script is configured to run in kaggle.com notebook

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
from torch.amp import autocast
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, models
from tqdm import tqdm

VAL_FRACTION = 0.2
BATCH_SIZE = 192
WORKERS_NUM = 4
LEARNING_RATE_HEAD = 1e-3
LEARNING_RATE_FULL = 5e-5
EPOCHS_HEAD = 5
EPOCHS_FULL = 15

INPUT_DIR = "/kaggle/input/facial-emotion-recognition-dataset/processed_data"

# Define data transformations
train_transform = transforms.Compose([
	transforms.Grayscale(num_output_channels=3),
	transforms.Resize((128, 128)),
	transforms.RandomHorizontalFlip(),
	transforms.RandomRotation(8),
	transforms.ToTensor(),
	transforms.Normalize([0.5, 0.5, 0.5],
					 [0.5, 0.5, 0.5]),
	transforms.RandomErasing(p=0.3, scale=(0.02, 0.2), ratio=(0.3, 3.3)),
])

val_transform = transforms.Compose([
	transforms.Grayscale(num_output_channels=3),
	transforms.Resize((128, 128)),
	transforms.ToTensor(),
	transforms.Normalize([0.5, 0.5, 0.5],
					 [0.5, 0.5, 0.5])
])

# Load dataset
dataset = datasets.ImageFolder(INPUT_DIR)

# Split dataset into training and validation sets
train_size = int((1 - VAL_FRACTION) * len(dataset))
val_size = len(dataset) - train_size

# Use random_split to create train and validation datasets
train_indices, val_indices = random_split(dataset, [train_size, val_size])

# Apply transforms to datasets
train_dataset = torch.utils.data.Subset(
    datasets.ImageFolder(INPUT_DIR, transform=train_transform), train_indices.indices
)

val_dataset = torch.utils.data.Subset(
    datasets.ImageFolder(INPUT_DIR, transform=val_transform), val_indices.indices
)

# Create data loaders
train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, pin_memory=True, num_workers=WORKERS_NUM)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, pin_memory=True, num_workers=WORKERS_NUM)

# Initialize model
num_classes = len(dataset.classes)
print(dataset.classes)

model = models.resnet34(weights=models.ResNet34_Weights.DEFAULT)

# Freeze all layers except the final classification layer
for param in model.parameters():
	param.requires_grad = False

# Add custom classification head
model.fc = nn.Sequential(
	nn.Linear(512, 256),
	nn.ReLU(),
	nn.Dropout(0.4),
	nn.Linear(256, num_classes)
)

# Only train classification head at first
for param in model.fc.parameters():
	param.requires_grad = True

# Select device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)

# Use DataParallel if multiple GPUs are available
if torch.cuda.device_count() > 1:
	print(f"Using {torch.cuda.device_count()} GPUs!")
	model = nn.DataParallel(model)

# Count samples per class
class_counts = [0] * num_classes
for _, label in dataset.samples:
    class_counts[label] += 1

# Compute class weights: inverse frequency
total = sum(class_counts)
class_weights = [total / (num_classes * c) for c in class_counts]
class_weights = torch.tensor(class_weights, dtype=torch.float).to(device)

# Define loss function and optimizer
criterion = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=0.05)

# Stage 1: Train classifier head (only head layers)
fc_params = model.module.fc.parameters() if isinstance(model, nn.DataParallel) else model.fc.parameters()
optimizer = optim.Adam(fc_params, lr=LEARNING_RATE_HEAD)
scheduler = torch.optim.lr_scheduler.OneCycleLR(
    optimizer,
    max_lr=LEARNING_RATE_HEAD,
    steps_per_epoch=len(train_loader),
    epochs=EPOCHS_HEAD
)
for epoch in range(EPOCHS_HEAD):
	model.train()
	train_loss = 0.0
	train_correct = 0
	total_train = 0
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
	train_accuracy = train_correct / total_train
	print(f"Head Epoch [{epoch+1}/{EPOCHS_HEAD}], Loss: {train_loss/len(train_loader):.4f}, Accuracy: {train_accuracy:.4f}")

# Stage 2: Unfreeze and fine-tune entire model
for param in model.parameters():
	param.requires_grad = True

# Redefine optimizer for all parameters
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE_FULL)
scheduler = torch.optim.lr_scheduler.OneCycleLR(
    optimizer,
    max_lr=LEARNING_RATE_FULL,
    steps_per_epoch=len(train_loader),
    epochs=EPOCHS_FULL
)
epochs_full = EPOCHS_FULL


best_acc = 0.0
for epoch in range(EPOCHS_FULL):
	model.train()
	train_loss = 0.0
	train_correct = 0
	total_train = 0
	for images, labels in tqdm(train_loader):
		images, labels = images.to(device), labels.to(device)
		optimizer.zero_grad()
		with autocast(device_type="cuda"):
			outputs = model(images)
			loss = criterion(outputs, labels)
		loss.backward()
		optimizer.step()
		scheduler.step()
		train_loss += loss.item()
		_, preds = torch.max(outputs, 1)
		train_correct += (preds == labels).sum().item()
		total_train += labels.size(0)
	train_accuracy = train_correct / total_train

	# Validation loop
	model.eval()
	val_loss = 0.0
	val_correct = 0
	total_val = 0
	with torch.no_grad():
		for images, labels in val_loader:
			images, labels = images.to(device), labels.to(device)
			outputs = model(images)
			loss = criterion(outputs, labels)
			val_loss += loss.item()
			_, preds = torch.max(outputs, 1)
			val_correct += (preds == labels).sum().item()
			total_val += labels.size(0)
	val_accuracy = val_correct / total_val
	print(f"Finetune Epoch [{epoch+1}/{EPOCHS_FULL}], Train Loss: {train_loss/len(train_loader):.4f}, "
		  f"Val Loss: {val_loss/len(val_loader):.4f}, Val Accuracy: {val_accuracy:.4f}")
	if val_accuracy > best_acc:
		torch.save(model.state_dict(), 'emotion_model.pt')
		best_acc = val_accuracy
		print(f"Saved new best model with accuracy: {best_acc:.4f}")

print("Training complete. Best validation accuracy:", best_acc)
