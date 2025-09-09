from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import random

app = Flask(__name__)
DB_NAME = "flashcards.db"


# ---------- INIT DB ----------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS flashcards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    russian TEXT NOT NULL,
                    english TEXT NOT NULL
                )''')
    conn.commit()
    conn.close()


init_db()


# ---------- HOME ----------
@app.route("/")
def index():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM flashcards")
    flashcards = c.fetchall()
    conn.close()
    return render_template("index.html", flashcards=flashcards)


# ---------- ADD FLASHCARD ----------
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        russian = request.form["russian"]
        english = request.form["english"]

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO flashcards (russian, english) VALUES (?, ?)", (russian, english))
        conn.commit()
        conn.close()

        return redirect(url_for("index"))

    return render_template("add.html")


# ---------- QUIZ ----------
@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM flashcards")
    flashcards = c.fetchall()
    conn.close()

    if not flashcards:
        return render_template("quiz.html", question=None)

    flashcard = random.choice(flashcards)

    if request.method == "POST":
        answer = request.form["answer"]
        if answer.strip().lower() == flashcard[2].lower():
            result = "✅ Correct!"
        else:
            result = f"❌ Incorrect. The correct answer was: {flashcard[2]}"
        return render_template("quiz.html", question=flashcard, result=result)

    return render_template("quiz.html", question=flashcard)
    

if __name__ == "__main__":
    app.run(debug=True)
