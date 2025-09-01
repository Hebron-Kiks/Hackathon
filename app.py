from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import requests
import os

app = Flask(__name__)
CORS(app)  # Allow frontend requests

# MySQL database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",        # change to your MySQL username
    password="1234",    # change to your MySQL password
    database="flashcards_db"
)
cursor = db.cursor()

# Hugging Face API setup
HF_API_URL = "https://api-inference.huggingface.co/models/deepset/roberta-base-squad2"
HF_HEADERS = {"Authorization": "Bearer hf_your_real_token_here"}  # ✅ FIXED

@app.route("/generate", methods=["POST"])
def generate_flashcards():
    data = request.json
    notes = data.get("notes", "")

    if not notes:
        return jsonify({"error": "No notes provided"}), 400

    sentences = notes.split(".")
    flashcards = []

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

            sql = "INSERT INTO flashcards (question, answer) VALUES (%s, %s)"
            cursor.execute(sql, (question, answer_text))
            db.commit()

            flashcards.append({"question": question, "answer": answer_text})

    return jsonify({"flashcards": flashcards})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
