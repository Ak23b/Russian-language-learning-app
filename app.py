from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from tts import text_to_speech   # import helper

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

DB_FILE = "flashcards.db"

# ----------------------
# Database setup
# ----------------------
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        # Users table
        c.execute("""CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL
                    )""")
        # Flashcards table
        c.execute("""CREATE TABLE IF NOT EXISTS flashcards (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        russian TEXT NOT NULL,
                        english TEXT NOT NULL,
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )""")
        conn.commit()

init_db()

# ----------------------
# Helpers
# ----------------------
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ----------------------
# Routes
# ----------------------
@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    cards = conn.execute("SELECT * FROM flashcards WHERE user_id = ?", 
                         (session["user_id"],)).fetchall()
    conn.close()
    return render_template("index.html", cards=cards)

@app.route("/add", methods=["GET", "POST"])
def add():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        russian = request.form["russian"]
        english = request.form["english"]
        conn = get_db_connection()
        conn.execute("INSERT INTO flashcards (user_id, russian, english) VALUES (?, ?, ?)",
                     (session["user_id"], russian, english))
        conn.commit()
        conn.close()
        flash("Flashcard added successfully!")
        return redirect(url_for("index"))
    return render_template("add.html")

@app.route("/quiz")
def quiz():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cards = conn.execute("SELECT * FROM flashcards WHERE user_id = ?", 
                         (session["user_id"],)).fetchall()
    conn.close()
    return render_template("quiz.html", cards=cards)

@app.route("/speak/<word>")
def speak(word):
    # Save speech audio into static folder
    audio_path = os.path.join("static", f"{word}.mp3")
    text_to_speech(word, audio_path)
    return render_template("speak.html", word=word, audio_file=audio_path)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?",
                            (username, password)).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Login successful!")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                         (username, password))
            conn.commit()
            flash("Registration successful! Please log in.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already taken!")
        finally:
            conn.close()

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for("login"))

@app.route("/settings")
def settings():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("settings.html")

# ----------------------
# Run app
# ----------------------
if __name__ == "__main__":
    app.run(debug=True)
