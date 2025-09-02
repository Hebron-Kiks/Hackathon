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
HF_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
HF_API_KEY = os.environ.get("HF_API_KEY")

if not HF_API_KEY:
    raise ValueError("HF_API_KEY is not set in environment variables")

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
        data = request.get_json(force=True)
        notes = data.get("notes", "")

        if not notes.strip():
            return jsonify({"error": "No notes provided"}), 400

        # Call Hugging Face API
        response = requests.post(HF_API_URL, headers=headers, json={"inputs": notes})

        if response.status_code != 200:
            return jsonify({
                "error": "Hugging Face API error",
                "details": response.text
            }), 500

        hf_output = response.json()

        # Ensure response is in expected format
        if isinstance(hf_output, list) and "summary_text" in hf_output[0]:
            summary = hf_output[0]["summary_text"]
        elif isinstance(hf_output, dict) and "summary_text" in hf_output:
            summary = hf_output["summary_text"]
        else:
            return jsonify({
                "error": "Unexpected Hugging Face API response",
                "details": hf_output
            }), 500

        # Flashcards from summary
        flashcards = [
            {"question": "Summarize the notes:", "answer": summary},
            {"question": "Main topic?", "answer": summary.split(".")[0]}
        ]

        # Save to PostgreSQL
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
            cur.execute(
                "INSERT INTO flashcards (question, answer) VALUES (%s, %s)",
                (card["question"], card["answer"])
            )
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"flashcards": flashcards})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
