from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import sqlite3, os, random
from tts import text_to_speech   # import helper

app = Flask(__name__)
DB_NAME = "flashcards.db"

# Ensure audio folder exists
os.makedirs("static/audio", exist_ok=True)

# ---------- PLAY AUDIO ----------
@app.route("/speak/<int:card_id>")
def speak(card_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT english FROM flashcards WHERE id=?", (card_id,))
    card = c.fetchone()
    conn.close()

    if not card:
        return "Card not found", 404

    english_word = card[0]
    filename, russian_text = text_to_speech(english_word, f"{card_id}.wav")

    return render_template("speak.html", english=english_word, russian=russian_text, filename=filename)
