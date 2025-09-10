from transformers import AutoProcessor, VitsModel, MarianMTModel, MarianTokenizer
import torch
import soundfile as sf
import re
import os
import time
import hashlib

# -------------------------
# Setup device (GPU if available, else CPU)
# -------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# -------------------------
# Load translation (EN → RU)
# -------------------------
print("🔄 Loading English → Russian translator...")
TRANS_MODEL_NAME = "Helsinki-NLP/opus-mt-en-ru"
trans_tokenizer = MarianTokenizer.from_pretrained(TRANS_MODEL_NAME)
trans_model = MarianMTModel.from_pretrained(TRANS_MODEL_NAME).to(device)

# -------------------------
# Load Russian TTS
# -------------------------
print("🔄 Loading Russian TTS...")
processor = AutoProcessor.from_pretrained("facebook/mms-tts-rus")
tts_model = VitsModel.from_pretrained("facebook/mms-tts-rus").to(device)

# Ensure static/audio directory exists
AUDIO_DIR = os.path.join("static", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)


def translate_en_to_ru(text: str) -> str:
    """
    Translate English text into Russian.
    """
    if not text.strip():
        raise ValueError("❌ Input text is empty.")

    inputs = trans_tokenizer(text, return_tensors="pt", padding=True, truncation=True).to(device)
    with torch.no_grad():
        translated = trans_model.generate(**inputs)

    russian = trans_tokenizer.decode(translated[0], skip_special_tokens=True)
    return russian.strip()


def text_to_speech(text: str, filename: str = None, input_lang: str = "en") -> str:
    """
    Convert English → Russian → Speech (default).
    Or directly Russian → Speech if input_lang="ru".
    
    Returns the relative URL (e.g. '/static/audio/file.wav') for Flask templates.
    """

    # -------------------------
    # Step 1: Translate if needed
    # -------------------------
    if input_lang == "en":
        russian_text = translate_en_to_ru(text)
    elif input_lang == "ru":
        russian_text = text.strip()
    else:
        raise ValueError("❌ Unsupported input_lang. Use 'en' or 'ru'.")

    if not russian_text:
        raise ValueError("❌ No Russian text to synthesize.")

    # Normalize spaces
    russian_text = re.sub(r"\s+", " ", russian_text)
    print(f"🌍 Final Russian Text: {russian_text}")

    # -------------------------
    # Step 2: Generate unique filename
    # -------------------------
    # Use hash for uniqueness
    text_hash = hashlib.md5(russian_text.encode("utf-8")).hexdigest()[:8]
    timestamp = int(time.time())
    base_name = re.sub(r"[^\w\s-]", "", russian_text).strip().replace(" ", "_")
    if not base_name:
        base_name = "output"

    if not filename:
        filename = f"{base_name}_{text_hash}_{timestamp}.wav"

    filepath = os.path.join(AUDIO_DIR, filename)

    # -------------------------
    # Step 3: Generate speech
    # -------------------------
    inputs = processor(text=russian_text, return_tensors="pt")

    # Make sure input_ids are correct type & device
    if "input_ids" in inputs:
        inputs["input_ids"] = inputs["input_ids"].to(dtype=torch.long, device=device)

    with torch.no_grad():
        speech = tts_model(**inputs).waveform.cpu()

    # -------------------------
    # Step 4: Save as WAV
    # -------------------------
    sf.write(filepath, speech.squeeze().numpy(), samplerate=16000)
    print(f"✅ Audio saved as: {filepath}")

    # -------------------------
    # Step 5: Return relative URL for Flask
    # -------------------------
    return f"/static/audio/{filename}"


# -------------------------
# Example standalone run
# -------------------------
if __name__ == "__main__":
    test_text = "Hello, how are you?"
    url = text_to_speech(test_text, input_lang="en")
    print(f"🎧 Flask URL: {url}")
