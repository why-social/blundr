from unittest.mock import MagicMock, patch

import numpy as np
from process_video import chosen_device as chosen_device
from process_video import get_emotion as get_emotion
from process_video import process_video as process_video


def test_chosen_device_cuda():
    with patch("process_video.torch.cuda.is_available", return_value=True):
        device = chosen_device()
        assert device.type == "cuda"
        

def test_chosen_device_mps():
    with patch("process_video.torch.cuda.is_available", return_value=False), \
         patch("process_video.torch.backends.mps.is_available", return_value=True):
        device = chosen_device()
        assert device.type == "mps"
        

def test_chosen_device_cpu():
    with patch("process_video.torch.cuda.is_available", return_value=False), \
         patch("process_video.torch.backends.mps.is_available", return_value=False):
        device = chosen_device()
        assert device.type == "cpu"
        

def test_process_video_header(tmp_path):
    video = tmp_path / "test.mp4"
    video.touch()

    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    mock = MagicMock()
    mock.get.return_value = 30
    mock.read.side_effect = [
        (True, fake_frame),
        (False, None)
    ]

    with patch("process_video.cv2.VideoCapture", return_value=mock), \
         patch("process_video.get_emotion", return_value=("neutral", 0.5)):
        
        log = process_video(str(video))
    lines = log.strip().splitlines()
    assert lines[0] == "time,emotion,confidence"

def test_process_video_single_prediction(tmp_path):
    video = tmp_path / "test.mp4"
    video.touch()

    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    mock = MagicMock()
    mock.get.return_value = 30
    mock.read.side_effect = [(True, fake_frame), (False, None)]

    with patch("process_video.cv2.VideoCapture", return_value=mock), \
         patch("process_video.get_emotion", return_value=("neutral", 0.5)):
        log = process_video(str(video))

    lines = log.strip().splitlines()
    assert len(lines) == 2


def test_process_video_multiple_predictions(tmp_path):
    video = tmp_path / "test.mp4"
    video.touch()

    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    fps = 30
    prediciton_interval = 0.5
    num_frames = 30

    mock = MagicMock()
    mock.get.return_value = 30
    mock.read.side_effect = [(True, fake_frame)] * 30 + [(False, None)]

    with patch("process_video.cv2.VideoCapture", return_value=mock), \
         patch("process_video.get_emotion", return_value=("neutral", 0.5)):
        log = process_video(str(video))

    lines = log.strip().splitlines()
    expected_predictions = int(num_frames / fps / prediciton_interval)
    assert len(lines) == expected_predictions + 1

def test_process_video_not_readable_file(tmp_path):
    video = tmp_path / "test.mp4"
    video.touch()

    mock = MagicMock()
    mock.get.return_value = 30
    mock.read.return_value = (False, None)

    with patch("process_video.cv2.VideoCapture", return_value=mock):
        log = process_video(str(video))
    
    assert isinstance(log, dict)
    assert log["status"] == "error"
    assert "Could not read video file" in log["message"]

def test_process_video_fps_fallback(tmp_path):
    video = tmp_path / "test.mp4"
    video.touch()

    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    mock = MagicMock()
    mock.get.return_value = 0
    mock.read.side_effect = [(True, fake_frame), (False, None)]

    with patch("process_video.cv2.VideoCapture", return_value=mock), \
         patch("process_video.get_emotion", return_value=("neutral", 0.5)):
        log = process_video(str(video))

    lines = log.strip().splitlines()
    assert len(lines) == 2

def test_process_video_mode_dev(tmp_path):
    video = tmp_path / "test.mp4"
    video.touch()

    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    with patch("process_video.get_emotion", return_value=("happy", 0.95)),\
         patch("process_video.cv2.VideoCapture") as mock_video, \
         patch("process_video.MODE", "dev"), \
         patch("builtins.print") as mock_print:
        
        mock_video_instance = mock_video.return_value
        mock_video_instance.read.side_effect = [(True, fake_frame), (False, None)]
        mock_video_instance.get.return_value = 30
        
        log = process_video(str(video))
        mock_print.assert_called()
        assert "happy" in log

def test_get_emotion_low_conf_single_image():
    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    detections = np.zeros((1, 1, 1, 7))
    detections[0, 0, 0, 2] = 0.01 

    mock_face_net = MagicMock()
    mock_face_net.forward.return_value = detections
    
    mock_tensor = MagicMock()
    mock_tensor.unsqueeze.return_value.to.return_value = "tensor"

    with patch("process_video.face_net", new=mock_face_net), \
         patch("process_video.model", new_callable=MagicMock), \
         patch("process_video.transform", return_value=mock_tensor):

        emotion, conf = get_emotion(fake_frame)

    assert emotion == "undefined"
    assert conf == 0.0

def test_get_emotion_invalid_frame():
    for frame in [None, np.ndarray, "Not an array"]:
        emotion, conf = get_emotion(frame)
        assert emotion == "undefined"
        assert conf == 0.0

def test_get_emotion_no_faces():
    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    mock = MagicMock()
    mock.forward.return_value = np.zeros((1, 1, 0, 7), dtype=float)

    with patch("process_video.face_net", new=mock):
        emotion, conf = get_emotion(fake_frame)
    
    assert emotion == "undefined"
    assert conf == 0.0

def test_get_emotion_empty_face_roi():
    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    invalid_box = [-1, -1, -1, -1]
    
    detections = np.zeros((1, 1, 1, 7))
    detections[0, 0, 0, 2] = 1.0
    detections[0, 0, 0, 3:7] = invalid_box

    mock = MagicMock()
    mock.forward.return_value = detections
    
    with patch("process_video.face_net", new=mock):
        emotion, conf = get_emotion(fake_frame)
    
    assert emotion == "undefined"
    assert conf == 0.0

def test_get_emotion_single_face():
    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    roi = [0.1, 0.1, 0.2, 0.2]

    detections = np.zeros((1, 1, 1, 7))
    detections[0, 0, 0, 2] = 1.0
    detections[0, 0, 0, 3:7] = roi 

    mock = MagicMock()
    mock.forward.return_value = detections
    
    with patch("process_video.face_net", new=mock), \
         patch("process_video.model", new_callable=MagicMock) as mock_model, \
         patch("process_video.transform") as mock_transform, \
         patch("torch.max") as mock_max, \
         patch("torch.softmax") as mock_softmax:

        mock_transform.return_value.unsquezze.return_value.to.return_value = "tensor"

        mock_model.return_value = np.array([[0,0,0,10,0,0,0]])
        
        mock_max.return_value = (None, MagicMock(item=lambda: 3))
        mock_softmax.return_value = np.array([[0,0,0,1,0,0,0]])

        emotion, conf = get_emotion(fake_frame)

    assert emotion in ["angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"]
    assert 0.0 <= conf <= 1.0

def test_get_emotion_multiple_faces():
    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    rois = [
        [0.1, 0.1, 0.2, 0.2],
        [0.3, 0.3, 0.4, 0.4]    
    ]

    detections = np.zeros((1, 1, len(rois), 7))
    for i, roi in enumerate(rois):
        detections[0, 0, i, 2] = 1.0
        detections[0, 0, i, 3:7] = roi

    mock = MagicMock()
    mock.forward.return_value = detections

    with patch("process_video.face_net", new=mock), \
         patch("process_video.model", new_callable=MagicMock) as mock_model, \
         patch("process_video.transform") as mock_transform, \
         patch("torch.max") as mock_max, \
         patch("torch.softmax") as mock_softmax:
        
        mock_transform.return_value.unsqueeze.return_value.to.return_value = "tensor"

        #Unnormalized values for confidence
        mock_model.return_value = np.array([[0,0,0,10,0,0,0]])
        
        mock_max.return_value = (None, MagicMock(item=lambda: 3))
        mock_softmax.return_value = np.array([[0,0,0,1,0,0,0]])

        emotion, conf = get_emotion(fake_frame)

    assert emotion == "happy"
    assert 0.0 <= conf <= 1.0
