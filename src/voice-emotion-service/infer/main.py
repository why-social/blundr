import argparse
import sys
import time
import torch
import numpy as np
import sounddevice as sd
from datetime import timedelta

# --- IMPORTS FROM COMMON SHARED LIB ---
from common.config.dataset_config import DatasetConfig
from common.config.model_config import ModelConfig
from common.model.crnn_model import CRNNModel
from common.utils.audio_processing import AudioProcessor
from common.utils.transformations import standardize_length

# Threshold: Below this RMS value, we assume silence.
SILENCE_THRESHOLD = 0.002 

def list_devices():
    print("\nAvailable Audio Input Devices:")
    print(sd.query_devices())

def calculate_volume(audio_chunk):
    """Calculates Root Mean Square (RMS) amplitude."""
    return np.sqrt(np.mean(audio_chunk**2))

def print_vu_meter(volume, max_len=20):
    """Prints a simple ASCII bar based on volume."""
    # Logarithmic scaling looks better for audio
    if volume == 0:
        bar = ""
    else:
        # Simple scaling for visualization
        scaled = min(1.0, volume * 10) 
        bar_len = int(scaled * max_len)
        bar = "|" * bar_len
    return f"[{bar:<{max_len}}]"

# ... [load_model and predict_chunk remain the same] ...
def load_model(model_path: str, device: str, n_mels: int, num_classes: int):
    """Loads the trained CRNN model."""
    print(f"⏳ Loading model from {model_path}...")
    config = ModelConfig() 
    model = CRNNModel(config, n_mels=n_mels, num_classes=num_classes)
    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint)
    model.to(device)
    model.eval()
    print("✅ Model loaded successfully.")
    return model

def predict_chunk(model, processor, audio_chunk, config, device):
    # ... (Keep your existing prediction logic) ...
    spec = processor.mic_data_to_spec(audio_chunk) 
    spec = standardize_length(spec, config.target_frames, mode='end')
    spec = spec.unsqueeze(0).to(device)
    with torch.no_grad():
        outputs = model(spec)
        probs = torch.nn.functional.softmax(outputs, dim=1)
        conf, predicted = torch.max(probs, 1)
    
    idx = predicted.item()
    label = config.label_map_reverse.get(idx)
    assert label is not None
    return label, conf.item() * 100

def run_file_mode(args, model, processor, config):
    import torchaudio
    
    print(f"Processing file: {args.file_path}")
    
    # Load the full file
    full_waveform, sr = torchaudio.load(args.file_path)
    
    # Resample immediately to avoid math headaches later
    if sr != config.sample_rate:
        resampler = torchaudio.transforms.Resample(sr, config.sample_rate)
        full_waveform = resampler(full_waveform)
        
    # Convert to mono
    if full_waveform.shape[0] > 1:
        full_waveform = torch.mean(full_waveform, dim=0, keepdim=True)
        
    full_waveform = full_waveform.squeeze().numpy() # Flatten to 1D numpy
    
    # Sliding Window Logic
    # We want 3-second chunks (target_length)
    chunk_samples = int(config.target_length * config.sample_rate)
    stride = chunk_samples  # No overlap for now
    
    print("-" * 50)
    print(f"{'TIMESTAMP':<15} | {'EMOTION':<10} | {'CONFIDENCE'}")
    print("-" * 50)

    for i in range(0, len(full_waveform), stride):
        chunk = full_waveform[i : i + chunk_samples]
        
        # Skip chunks that are too short (less than 0.5s)
        if len(chunk) < config.sample_rate * 0.5:
            continue
            
        label, conf = predict_chunk(model, processor, chunk, config, args.device)
        
        # Timestamp
        seconds = i / config.sample_rate
        ts = str(timedelta(seconds=int(seconds)))
        
        print(f"{ts:<15} | {label:<10} | {conf:.1f}%")

def run_mic_mode(args, model, processor, config):
    print("\n🎤 Microphone Mode Activated")
    
    # Check device availability
    try:
        device_info = sd.query_devices(args.input_device, 'input')
        print(f"   Using Device: {device_info['name']}")
    except Exception as e:
        print(f"   Error finding device: {e}")
        list_devices()
        return

    print(f"   Sample Rate:  {config.sample_rate}")
    print("   Press Ctrl+C to stop.\n")

    block_size = int(config.sample_rate * config.target_length)
    
    print("-" * 70)
    print(f"{'STATUS':<15} | {'VOL':<5} | {'METER':<22} | {'EMOTION':<10} | {'CONF'}")
    print("-" * 70)

    try:
        with sd.InputStream(
            device=args.input_device,
            channels=1, 
            samplerate=config.sample_rate, 
            blocksize=block_size
        ) as stream:
            
            while True:
                data, overflowed = stream.read(block_size)
                if overflowed: print("   Overflow")
                
                audio_chunk = data.flatten()
                
                # --- CHECK 1: DEAD SILENCE ---
                if np.all(audio_chunk == 0):
                    print(f"{'No Input':<15} | 0.000 | {'[DEAD SIGNAL]':<22} | ---        | 0%")
                    continue

                # --- CHECK 2: VOLUME THRESHOLD ---
                volume = calculate_volume(audio_chunk)
                vu_meter = print_vu_meter(volume)
                
                if volume < SILENCE_THRESHOLD:
                    # Skip inference if too quiet
                    print(f"{'Silence':<15} | {volume:.3f} | {vu_meter:<22} | ---        | 0%")
                    continue

                # --- RUN INFERENCE ---
                label, conf = predict_chunk(model, processor, audio_chunk, config, args.device)
                
                print(f"{'Listening...':<15} | {volume:.3f} | {vu_meter:<22} | {label:<10} | {conf:.0f}%")

    except KeyboardInterrupt:
        print("\n   Stopping...")
    except Exception as e:
        print(f"\n   Error: {e}")

# ... [run_file_mode remains the same] ...

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("model_path", type=str)
    parser.add_argument("--mode", choices=["file", "mic"], required=True)
    parser.add_argument("--file_path", type=str)
    parser.add_argument("--device", type=str, default="cpu")
    
    # NEW: Allow selecting a specific mic ID
    parser.add_argument("--input_device", type=int, default=None, help="Device ID for microphone")
    # NEW: Helper to list devices
    parser.add_argument("--list_devices", action="store_true", help="Show available audio devices and exit")
    
    args = parser.parse_args()

    if args.list_devices:
        list_devices()
        sys.exit(0)

    # ... [Rest of initialization] ...
    dataset_config = DatasetConfig()
    audio_processor = AudioProcessor(dataset_config)
    model = load_model(args.model_path, args.device, dataset_config.n_mels, len(dataset_config.label_map))

    if args.mode == "file":
        if not args.file_path:
            print("   Error: --file_path is required for file mode.")
            sys.exit(1)
        run_file_mode(args, model, audio_processor, dataset_config)
    else:
        run_mic_mode(args, model, audio_processor, dataset_config)
