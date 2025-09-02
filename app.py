from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import requests
import os

app = Flask(__name__)
CORS(app)  # Allow frontend requests

# PostgreSQL connection (Render provides DATABASE_URL)
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    return conn

# Hugging Face API setup
HF_API_URL = "https://api-inference.huggingface.co/models/deepset/roberta-base-squad2"
HF_HEADERS = {"Authorization": "Bearer hf_your_real_token_here"}  # replace with real token

@app.route("/")
def home():
    return "✅ Flask + PostgreSQL + Render is working!"

@app.route("/generate", methods=["POST"])
def generate_flashcards():
    data = request.json
    notes = data.get("notes", "")

    if not notes:
        return jsonify({"error": "No notes provided"}), 400

    sentences = notes.split(".")
    flashcards = []

    # Ensure the flashcards table exists
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS flashcards (
            id SERIAL PRIMARY KEY,
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        )
    """)
    conn.commit()

    for sentence in sentences:
        if len(sentence.strip()) > 10:
            question = f"What is the meaning of: {sentence.strip()}?"

            response = requests.post(
                HF_API_URL,
                headers=HF_HEADERS,
                json={"context": notes, "question": question}
            )
            answer = response.json()

            try:
                answer_text = answer["answer"]
            except Exception:
                answer_text = "Not sure"

            # Insert into PostgreSQL
            cur.execute(
                "INSERT INTO flashcards (question, answer) VALUES (%s, %s)",
                (question, answer_text)
            )
            conn.commit()

            flashcards.append({"question": question, "answer": answer_text})

    cur.close()
    conn.close()

    return jsonify({"flashcards": flashcards})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
