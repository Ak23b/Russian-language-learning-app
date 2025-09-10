from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from tts import text_to_speech   # Import our manual TTS helper

app = Flask(__name__)
app.secret_key = "supersecretkey"

DB_NAME = "flashcards.db"

# -------------------------
# Database helper
# -------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            english TEXT,
            russian TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -------------------------
# Routes
# -------------------------
@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM flashcards")
    cards = cursor.fetchall()
    conn.close()

    return render_template("index.html", cards=cards)


@app.route("/add", methods=["POST"])
def add():
    if "user" not in session:
        return redirect(url_for("login"))

    english = request.form["english"]
    russian = request.form["russian"]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO flashcards (english, russian) VALUES (?, ?)", (english, russian))
    conn.commit()
    conn.close()

    return redirect(url_for("index"))


@app.route("/speak/<int:card_id>")
def speak(card_id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT russian FROM flashcards WHERE id = ?", (card_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        russian_text = row[0]
        text_to_speech(russian_text)  # Manual TTS call
    return redirect(url_for("index"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return render_template("register.html", error="Username already exists")
        finally:
            conn.close()

        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
