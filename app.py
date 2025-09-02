from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import psycopg2
import os

app = Flask(__name__)
CORS(app)

# -----------------------------
# Database Connection
# -----------------------------
def get_db_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])

# -----------------------------
# Hugging Face API Setup
# -----------------------------
HF_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"  # Example model
HF_API_KEY = os.environ.get("HF_API_KEY")  # Store in Render environment variables

headers = {"Authorization": f"Bearer {HF_API_KEY}"}

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate_flashcards():
    try:
        data = request.get_json()
        notes = data.get("notes", "")

        if not notes.strip():
            return jsonify({"error": "No notes provided"}), 400

        # Call Hugging Face API
        response = requests.post(HF_API_URL, headers=headers, json={"inputs": notes})
        
        if response.status_code != 200:
            return jsonify({"error": "Hugging Face API error", "details": response.text}), 500

        # Simplify response into mock flashcards (you can refine logic here)
        summary = response.json()[0]["summary_text"]
        flashcards = [
            {"question": "Summarize the notes:", "answer": summary},
            {"question": "Main topic?", "answer": summary.split(".")[0]}
        ]

        # Save flashcards into PostgreSQL
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS flashcards (
                id SERIAL PRIMARY KEY,
                question TEXT,
                answer TEXT
            )
        """)
        for card in flashcards:
            cur.execute("INSERT INTO flashcards (question, answer) VALUES (%s, %s)", 
                        (card["question"], card["answer"]))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"flashcards": flashcards})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
