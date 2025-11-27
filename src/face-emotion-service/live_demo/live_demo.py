import cv2
import torch
import torchvision.transforms as transforms
from torchvision import models
import torch.nn as nn
from PIL import Image
import numpy as np
import time


# Settings
MODEL_PATH = "emotion_model.pt"
PREDICTION_INTERVAL = 0.5  # seconds

# DNN face detector model files
FACE_PROTO = "deploy.prototxt"
FACE_MODEL = "res10_300x300_ssd_iter_140000.caffemodel"

# Face detection confidence threshold
CONF_THRESHOLD = 0.6

# Classes in the order used during training
emotion_classes = [
	"angry", "disgust", "fear", "happy", "neutral", "sad", "surprise",
]

# Device selection
if torch.cuda.is_available():
	device = torch.device("cuda")
elif torch.backends.mps.is_available():
	device = torch.device("mps")
else:
	device = torch.device("cpu")
print("Using device:", device)

# Load emotion model
model = models.resnet50(weights=None)

# Apply the same head architecture as in training
model.fc = nn.Sequential(
    nn.Linear(2048, 512),
    nn.ReLU(),
    nn.Dropout(0.4),
    nn.Linear(512, len(emotion_classes))
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
	transforms.Resize((224, 224)),
	transforms.ToTensor(),
	transforms.Normalize([0.5, 0.5, 0.5],
                     [0.5, 0.5, 0.5])
])

# Dnn face detector (ResNet-SSD, Caffe)
face_net = cv2.dnn.readNetFromCaffe(FACE_PROTO, FACE_MODEL)

# To run on cuda
# face_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
# face_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

print("DNN face detector loaded.")

# Camera
cap = cv2.VideoCapture(0)
if not cap.isOpened():
	raise RuntimeError("Could not open camera.")
print("Camera is running. Press 'q' to quit.")

# Main loop
last_prediction_time = 0
last_emotion = "" # Last predicted emotion label to display between frames

while True:
	# Capture frame from camera
	ret, frame = cap.read()
	if not ret:
		continue

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

	current_time = time.time()

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

		# Predict emotion at defined intervals
		if current_time - last_prediction_time >= PREDICTION_INTERVAL:
			img_tensor = transform(face_pil).unsqueeze(0).to(device)
			with torch.no_grad():
				output = model(img_tensor)
				_, pred = torch.max(output, 1)
				emotion = emotion_classes[pred.item()]
			last_prediction_time = current_time
			last_emotion = emotion

		# Draw bounding box + label
		cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
		cv2.putText(
			frame,
			last_emotion,
			(x1, y1 - 10 if y1 - 10 > 10 else y1 + 20),
			cv2.FONT_HERSHEY_SIMPLEX,
			0.7,
			(0, 255, 0),
			2
		)

	cv2.imshow("Emotion Recognition (q to exit)", frame)
	if cv2.waitKey(1) & 0xFF == ord("q"):
		break


# Cleanup
cap.release()
cv2.destroyAllWindows()
print("Program ended.")
