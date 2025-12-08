import cv2
import torch
import torchvision.transforms as transforms
from torchvision import models
import torch.nn as nn
from PIL import Image
import numpy as np
import os

MODE = "prod"

PREDICTION_INTERVAL = 0.5  # seconds

MODEL_PATH = "models/emotion_model.pt"
FACE_PROTO = "models/deploy.prototxt"
FACE_MODEL = "models/res10_300x300_ssd_iter_140000.caffemodel"
CONF_THRESHOLD = 0.6

emotion_classes = [
	"angry", "disgust", "fear", "happy", "neutral", "sad", "surprise",
]

if torch.cuda.is_available():
	device = torch.device("cuda")
elif torch.backends.mps.is_available():
	device = torch.device("mps")
else:
	device = torch.device("cpu")

print("Using device:", device)

model = models.resnet34(weights=None)

# Apply the same head architecture as in training
model.fc = nn.Sequential(
	nn.Linear(512, 256),
	nn.ReLU(),
	nn.Dropout(0.4),
	nn.Linear(256, len(emotion_classes))
)

# Load state dict (handle DataParallel if needed)
state_dict = torch.load(MODEL_PATH, map_location=device)
new_state_dict = {}
for k, v in state_dict.items():
	name = k.replace("module.", "")  # remove "module." prefix
	new_state_dict[name] = v

model.load_state_dict(new_state_dict)
model.to(device)
model.eval()

print("Emotion model loaded.")

# Preprocessing, same as during training
transform = transforms.Compose([
	transforms.Grayscale(num_output_channels=3),
	transforms.Resize((128, 128)),
	transforms.ToTensor(),
	transforms.Normalize([0.5, 0.5, 0.5],
					[0.5, 0.5, 0.5])
])

# Dnn face detector (ResNet-SSD, Caffe)
face_net = cv2.dnn.readNetFromCaffe(FACE_PROTO, FACE_MODEL)

print("DNN face detector loaded.")

def process_video(file_path):
	vidcap = cv2.VideoCapture(file_path, cv2.CAP_FFMPEG)
	fps = vidcap.get(cv2.CAP_PROP_FPS)
	frame_step = int(fps * PREDICTION_INTERVAL)
	success, frame = vidcap.read()
	frame_count = 0
	next_time = 0.0
	log = ""
	log += "time,emotion,confidence\n"
	if not success:
		vidcap.release()
		return {"status": "error", "message": "Could not read video file."}
	while success:
		current_time = frame_count / fps
		if current_time >= next_time:
			emotion, emotion_confidence = get_emotion(frame)
			log += f"{round(current_time * 2) / 2:.2f},{emotion},{emotion_confidence:.4f}\n"
			if MODE == "dev":
				print(f"{current_time:.2f},{emotion},{emotion_confidence:.4f}")
			next_time += PREDICTION_INTERVAL
		frame_count += 1
		success, frame = vidcap.read()
	
	vidcap.release()
	return log


def get_emotion(frame):
	(h, w) = frame.shape[:2]

	# Prepare blob for DNN face detector (expects BGR, 300x300)
	blob = cv2.dnn.blobFromImage(
		image=cv2.resize(frame, (300, 300)),
		scalefactor=1.0,
		size=(300, 300),
		mean=(104.0, 177.0, 123.0),
		swapRB=False,
		crop=False
	)

	# Detect faces
	face_net.setInput(blob)
	detections = face_net.forward()

	# Loop over detections
	for i in range(0, detections.shape[2]):
		confidence = detections[0, 0, i, 2]

		if confidence < CONF_THRESHOLD:
			continue

		# Get box in normalized coords and scale to frame size
		box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
		(x1, y1, x2, y2) = box.astype("int")

		# Clip to frame
		x1 = max(0, x1)
		y1 = max(0, y1)
		x2 = min(w - 1, x2)
		y2 = min(h - 1, y2)

		# Extract face ROI (BGR)
		face_rgb = frame[y1:y2, x1:x2]
		if face_rgb.size == 0:
			continue

		face_pil = Image.fromarray(cv2.cvtColor(face_rgb, cv2.COLOR_BGR2RGB))

		img_tensor = transform(face_pil).unsqueeze(0).to(device)
		with torch.no_grad():
			output = model(img_tensor)
			_, pred = torch.max(output, 1)
			emotion = emotion_classes[pred.item()]
			emotion_confidence = torch.softmax(output, dim=1)[0][pred.item()].item()
		
		return emotion, emotion_confidence
	return "undefined", 0.0