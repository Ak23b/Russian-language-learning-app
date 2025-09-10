import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from tts import text_to_speech  # import helper

app = Flask(__name__)
app.secret_key = "supersecretkey"

# -------------------------
# Database connection helper
# -------------------------
def get_db_connection():
    conn = sqlite3.connect("flashcards.db")
    conn.row_factory = sqlite3.Row
    return conn

# -------------------------
# Home → redirect to login
# -------------------------
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

# -------------------------
# Dashboard page
# -------------------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")

# -------------------------
# Flashcards page
# -------------------------
@app.route("/index")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cards = conn.execute(
        "SELECT * FROM flashcards WHERE user_id = ?",
        (session["user_id"],),
    ).fetchall()
    conn.close()
    return render_template("index.html", cards=cards)

# -------------------------
# Add flashcard
# -------------------------
@app.route("/add", methods=("GET", "POST"))
def add():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        front = request.form["front"]
        back = request.form["back"]

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO flashcards (front, back, user_id) VALUES (?, ?, ?)",
            (front, back, session["user_id"]),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    return render_template("add.html")

# -------------------------
# Quiz page
# -------------------------
@app.route("/quiz")
def quiz():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cards = conn.execute(
        "SELECT * FROM flashcards WHERE user_id = ?",
        (session["user_id"],),
    ).fetchall()
    conn.close()
    return render_template("quiz.html", cards=cards)

# -------------------------
# Speak (TTS)
# -------------------------
@app.route("/speak", methods=("GET", "POST"))
def speak():
    if "user_id" not in session:
        return redirect(url_for("login"))

    audio_file = None
    if request.method == "POST":
        text = request.form["text"]
        audio_file = text_to_speech(text)

    return render_template("speak.html", audio_file=audio_file)

# -------------------------
# Settings page
# -------------------------
@app.route("/settings")
def settings():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("settings.html")

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
