import re
import torch
import soundfile as sf
from transformers import AutoProcessor, VitsModel
import argostranslate.translate

# Load Translator (English → Russian)
installed_languages = argostranslate.translate.get_installed_languages()
from_lang = next((lang for lang in installed_languages if lang.code == "en"), None)
to_lang = next((lang for lang in installed_languages if lang.code == "ru"), None)
translation = from_lang.get_translation(to_lang)

# Load TTS model
print("🔄 Loading Russian TTS...")
processor = AutoProcessor.from_pretrained("facebook/mms-tts-rus")
model = VitsModel.from_pretrained("facebook/mms-tts-rus")

def text_to_speech(english_text, filename):
    """Translate English to Russian and generate TTS audio file."""
    russian_text = translation.translate(english_text)

    # Sanitize filename
    safe_filename = re.sub(r"[^\w\s-]", "", english_text).strip().replace(" ", "_")
    filename = f"static/audio/{safe_filename}.wav"

    # Generate TTS
    inputs = processor(text=russian_text, return_tensors="pt")
    with torch.no_grad():
        speech = model(**inputs).waveform

    # Save audio
    sf.write(filename, speech.squeeze().numpy(), samplerate=16000)
    return filename, russian_text
