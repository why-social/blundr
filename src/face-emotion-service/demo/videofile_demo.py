import cv2
import numpy as np
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
from torchvision import models

PREDICTION_INTERVAL = 0.5  # seconds
VIDEO_FILE_PATH = "video.webm"
OUTPUT_VIDEO_PATH = "video_processed.mp4"
	
MODEL_PATH = "../models/emotion_model.pt"
FACE_PROTO = "../models/deploy.prototxt"
FACE_MODEL = "../models/res10_300x300_ssd_iter_140000.caffemodel"
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

# To run on cuda
# face_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
# face_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
print("DNN face detector loaded.")

def get_emotion(frame):
    (h, w) = frame.shape[:2]
    lastEmotion = None
    lastBox = None

    blob = cv2.dnn.blobFromImage(
        image=cv2.resize(frame, (300, 300)),
        scalefactor=1.0,
        size=(300, 300),
        mean=(104.0, 177.0, 123.0),
        swapRB=False,
        crop=False
    )

    face_net.setInput(blob)
    detections = face_net.forward()

    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence < CONF_THRESHOLD:
            continue

        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
        (x1, y1, x2, y2) = box.astype("int")

        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w - 1, x2)
        y2 = min(h - 1, y2)

        face_rgb = frame[y1:y2, x1:x2]
        if face_rgb.size == 0:
            continue

        face_pil = Image.fromarray(cv2.cvtColor(face_rgb, cv2.COLOR_BGR2RGB))
        img_tensor = transform(face_pil).unsqueeze(0).to(device)

        with torch.no_grad():
            output = model(img_tensor)
            _, pred = torch.max(output, 1)
            emotion = emotion_classes[pred.item()]

        lastEmotion = emotion
        lastBox = (x1, y1, x2, y2)
        break  # only use first face

    return lastBox, lastEmotion



# ---- MAIN VIDEO PROCESSING ----

vidcap = cv2.VideoCapture(VIDEO_FILE_PATH, cv2.CAP_FFMPEG)
fps = vidcap.get(cv2.CAP_PROP_FPS)
width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
writer = cv2.VideoWriter(OUTPUT_VIDEO_PATH, fourcc, fps, (width, height))

frame_step = int(fps * PREDICTION_INTERVAL)
success, frame = vidcap.read()
frame_count = 0
next_time = 0.0

log = "time,emotion\n"

prev_box = None
prev_emotion = ""

while success:
    current_time = frame_count / fps

    # Update prediction at intervals
    if current_time >= next_time:
        box, emotion = get_emotion(frame)
        if box is not None:
            prev_box = box
        if emotion is not None:
            prev_emotion = emotion

        log += f"{round(current_time * 2) / 2:.2f},{prev_emotion}\n"
        print(f"{current_time:.2f},{prev_emotion}")
        next_time += PREDICTION_INTERVAL

    # Always draw on the frame using last known values
    annotated_frame = frame.copy()

    if prev_box is not None:
        (x1, y1, x2, y2) = prev_box
        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            annotated_frame,
            prev_emotion,
            (x1, y1 - 10 if y1 - 10 > 10 else y1 + 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

    writer.write(annotated_frame)

    frame_count += 1
    success, frame = vidcap.read()


vidcap.release()
writer.release()

print("Processing complete.")
print("Saved video:", OUTPUT_VIDEO_PATH)
print(log)