import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from tts import text_to_speech, translate_en_to_ru  # helper functions

app = Flask(__name__)
app.secret_key = "supersecretkey"

# -------------------------
# Paths & Folders
# -------------------------
DATABASE = "flashcards.db"
AUDIO_FOLDER = os.path.join("static", "audio")
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# -------------------------
# Database helpers
# -------------------------
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Audio cards table
    c.execute("""
        CREATE TABLE IF NOT EXISTS audio_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            original_text TEXT NOT NULL,
            translated_text TEXT NOT NULL,
            audio_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Settings table
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            tts TEXT DEFAULT 'enabled',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()

# Initialize DB
init_db()

# -------------------------
# Index (My Saved Audios shortcut)
# -------------------------
@app.route("/index")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("library"))

# -------------------------
# Home → redirect to login
# -------------------------
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

# -------------------------
# Dashboard
# -------------------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")

# -------------------------
# Speak (English → Russian → TTS, preview only)
# -------------------------
@app.route("/speak", methods=("GET", "POST"))
def speak():
    if "user_id" not in session:
        return redirect(url_for("login"))

    audio_file = None
    audio_filename = None
    original_text = None
    translated_text = None

    if request.method == "POST":
        original_text = request.form["text"]

        # Translate EN → RU
        translated_text = translate_en_to_ru(original_text)

        # Generate Russian TTS file (preview only)
        audio_filename, audio_file = text_to_speech(
            original_text, input_lang="en", output_folder=AUDIO_FOLDER
        )

    return render_template(
        "speak.html",
        audio_file=audio_file,
        audio_filename=audio_filename,
        original_text=original_text,
        translated_text=translated_text,
    )

# -------------------------
# Save Audio (manual save to DB)
# -------------------------
@app.route("/save_audio", methods=("POST",))
def save_audio():
    if "user_id" not in session:
        return redirect(url_for("login"))

    original_text = request.form["original_text"]
    translated_text = request.form["translated_text"]
    audio_filename = request.form["filename"]

    # Build path for DB storage
    audio_path = os.path.join("static", "audio", audio_filename)

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO audio_cards (user_id, original_text, translated_text, audio_path) VALUES (?, ?, ?, ?)",
        (session["user_id"], original_text, translated_text, audio_path),
    )
    conn.commit()
    conn.close()

    return redirect(url_for("library"))

# -------------------------
# Library (list saved audios)
# -------------------------
@app.route("/library")
def library():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cards = conn.execute(
        "SELECT * FROM audio_cards WHERE user_id = ? ORDER BY created_at DESC",
        (session["user_id"],),
    ).fetchall()
    conn.close()

    return render_template("library.html", cards=cards)

# -------------------------
# Delete Audio
# -------------------------
@app.route("/delete_audio/<int:audio_id>", methods=("POST",))
def delete_audio(audio_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    card = conn.execute(
        "SELECT * FROM audio_cards WHERE id = ? AND user_id = ?",
        (audio_id, session["user_id"]),
    ).fetchone()

    if card:
        # Remove file from disk if it exists
        if os.path.exists(card["audio_path"]):
            try:
                os.remove(card["audio_path"])
            except Exception as e:
                print(f"⚠ Could not delete file: {e}")

        # Delete record from DB
        conn.execute("DELETE FROM audio_cards WHERE id = ? AND user_id = ?", 
                     (audio_id, session["user_id"]))
        conn.commit()

    conn.close()
    return redirect(url_for("library"))

# -------------------------
# Settings
# -------------------------
@app.route("/settings", methods=("GET", "POST"))
def settings():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    # Get settings
    user_settings = conn.execute(
        "SELECT * FROM settings WHERE user_id = ?", (session["user_id"],)
    ).fetchone()

    # If no settings yet, insert defaults
    if not user_settings:
        conn.execute(
            "INSERT INTO settings (user_id, tts) VALUES (?, ?)",
            (session["user_id"], "enabled"),
        )
        conn.commit()
        user_settings = {"tts": "enabled"}

    conn.close()
    return render_template("settings.html", user_settings=user_settings)

# Update settings
@app.route("/update_settings", methods=("POST",))
def update_settings():
    if "user_id" not in session:
        return redirect(url_for("login"))

    tts_setting = request.form.get("tts", "enabled")

    conn = get_db_connection()
    conn.execute(
        "UPDATE settings SET tts = ? WHERE user_id = ?",
        (tts_setting, session["user_id"]),
    )
    conn.commit()
    conn.close()

    return redirect(url_for("settings"))


# -------------------------
# Register
# -------------------------
@app.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        existing_user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if existing_user:
            conn.close()
            return "User already exists!"

        hashed_pw = generate_password_hash(password)
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed_pw),
        )
        conn.commit()

        # Initialize settings for this user
        user_id = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()["id"]
        conn.execute(
            "INSERT INTO settings (user_id, tts) VALUES (?, ?)", (user_id, "enabled")
        )
        conn.commit()
        conn.close()
        return redirect(url_for("login"))

    return render_template("register.html")

# -------------------------
# Login
# -------------------------
@app.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        else:
            return "Invalid credentials!"

    return render_template("login.html")

# -------------------------
# Logout
# -------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
