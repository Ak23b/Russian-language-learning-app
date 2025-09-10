from transformers import AutoProcessor, VitsModel
import torch
import soundfile as sf
import re
import os

# -------------------------
# Load TTS model once
# -------------------------
print("🔄 Loading Russian TTS...")
processor = AutoProcessor.from_pretrained("facebook/mms-tts-rus")
model = VitsModel.from_pretrained("facebook/mms-tts-rus")

def text_to_speech(text: str, filename: str = None):
    """
    Convert Russian text to speech and save as WAV file.
    If filename is None, generate a safe filename automatically.
    """
    # -------------------------
    # Sanitize filename
    # -------------------------
    if not filename:
        safe_filename = re.sub(r"[^\w\s-]", "", text).strip().replace(" ", "_")
        filename = f"{safe_filename}.wav"

    # -------------------------
    # Generate speech
    # -------------------------
    inputs = processor(text=text, return_tensors="pt")
    with torch.no_grad():
        speech = model(**inputs).waveform

    # -------------------------
    # Save as WAV
    # -------------------------
    sf.write(filename, speech.squeeze().numpy(), samplerate=16000)
    print(f"✅ Audio saved as: {filename}")

    # Optional: play automatically on Windows
    try:
        os.system(f"start {filename}")
    except Exception:
        pass

    return filename
