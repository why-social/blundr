# This training script is configured to run in kaggle.com notebook

import torch
import torch.nn as nn
import torchvision.transforms as transforms
from torchvision import datasets, models
from torch.utils.data import DataLoader, random_split
import torch.optim as optim
from torch.optim.lr_scheduler import StepLR
from tqdm import tqdm

VAL_FRACTION = 0.2
BATCH_SIZE = 128
WORKERS_NUM = 4
LEARNING_RATE_HEAD = 1e-3
LEARNING_RATE_FULL = 1e-4
EPOCHS_HEAD = 5
EPOCHS_FULL = 15

# Define data transformations
train_transform = transforms.Compose([
	transforms.Grayscale(num_output_channels=3),
	transforms.Resize((224, 224)),
	transforms.RandomHorizontalFlip(),
	transforms.RandomRotation(8),
	transforms.ToTensor(),
	transforms.Normalize([0.5, 0.5, 0.5],
					 [0.5, 0.5, 0.5])
])

val_transform = transforms.Compose([
	transforms.Grayscale(num_output_channels=3),
	transforms.Resize((224, 224)),
	transforms.ToTensor(),
	transforms.Normalize([0.5, 0.5, 0.5],
					 [0.5, 0.5, 0.5])
])

# Load dataset
dataset = datasets.ImageFolder("/kaggle/input/facial-emotion-recognition-dataset/processed_data")

# Split dataset into training and validation sets
train_size = int((1 - VAL_FRACTION) * len(dataset))
val_size = len(dataset) - train_size

# Use random_split to create train and validation datasets
train_dataset, val_dataset = random_split(dataset, [train_size, val_size])

# Apply transforms to datasets
train_dataset.dataset.transform = train_transform
val_dataset.dataset.transform = val_transform

# Create data loaders
train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, pin_memory=True, num_workers=WORKERS_NUM)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, pin_memory=True, num_workers=WORKERS_NUM)

# Initialize model
num_classes = len(dataset.classes)
print(dataset.classes)

model = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)

# Freeze all layers except the final classification layer
for param in model.parameters():
	param.requires_grad = False

# Add custom classification head
model.fc = nn.Sequential(
	nn.Linear(2048, 512),
	nn.ReLU(),
	nn.Dropout(0.4),
	nn.Linear(512, num_classes)
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

# Define loss function and optimizer
criterion = nn.CrossEntropyLoss()

# Stage 1: Train classifier head (only head layers)
fc_params = model.module.fc.parameters() if isinstance(model, nn.DataParallel) else model.fc.parameters()
optimizer = optim.Adam(fc_params, lr=LEARNING_RATE_HEAD)
scheduler = StepLR(optimizer, step_size=7, gamma=0.1)
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
		train_loss += loss.item()
		_, preds = torch.max(outputs, 1)
		train_correct += (preds == labels).sum().item()
		total_train += labels.size(0)
	scheduler.step()
	train_accuracy = train_correct / total_train
	print(f"Head Epoch [{epoch+1}/{EPOCHS_HEAD}], Loss: {train_loss/len(train_loader):.4f}, Accuracy: {train_accuracy:.4f}")

# Stage 2: Unfreeze and fine-tune entire model
for param in model.parameters():
	param.requires_grad = True

# Redefine optimizer for all parameters
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE_FULL)
scheduler = StepLR(optimizer, step_size=7, gamma=0.1)
epochs_full = EPOCHS_FULL

# Use autocast for mixed precision training
from torch.amp import autocast

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
		train_loss += loss.item()
		_, preds = torch.max(outputs, 1)
		train_correct += (preds == labels).sum().item()
		total_train += labels.size(0)
	scheduler.step()
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
