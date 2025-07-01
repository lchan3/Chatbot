from flask import Flask, request, render_template_string
from docx import Document
from difflib import get_close_matches
import os
import sqlite3
import requests

app = Flask(__name__)

# === Teams Webhook Placeholder ===
TEAMS_WEBHOOK_URL = "https://outlook.office.com/webhook/your-webhook-url"

# === Initialize SQLite Database ===
def init_db():
    conn = sqlite3.connect("chatbot.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS unanswered (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# === Notify Teams via Webhook ===
def notify_teams(question):
    payload = {
        "text": f"❓ New unanswered question received:\n\n**{question}**"
    }
    try:
        requests.post(TEAMS_WEBHOOK_URL, json=payload)
    except Exception as e:
        print("Failed to send Teams notification:", e)

# === Load FAQs from .docx Files ===
def load_faqs(faq_folder='faqs'):
    qa_pairs = {}
    if not os.path.exists(faq_folder):
        return qa_pairs
    for filename in os.listdir(faq_folder):
        if filename.endswith(".docx"):
            doc = Document(os.path.join(faq_folder, filename))
            for para in doc.paragraphs:
                if ": " in para.text:
                    question, answer = para.text.split(": ", 1)
                    qa_pairs[question.strip()] = answer.strip()
    return qa_pairs

qa_pairs = load_faqs()

# === Chatbot HTML Template ===
html_template = """
<!doctype html>
<html>
<head>
    <title>FAQ Chatbot</title>
    <style>
        body { font-family: Arial; background: #f4f4f4; padding: 20px; }
        .chat-container { max-width: 700px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        .chat-header { font-size: 24px; margin-bottom: 20px; text-align: center; }
        .chat-bubble { padding: 10px 15px; border-radius: 15px; margin-bottom: 10px; max-width: 80%; }
        .bot { background: #d1e7dd; }
        .user { background: #cfe2ff; text-align: right; }
        form { display: flex; flex-direction: column; gap: 10px; }
        input[type="text"] { padding: 10px; font-size: 16px; border-radius: 5px; border: 1px solid #ccc; }
        input[type="submit"] { padding: 10px; font-size: 16px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        input[type="submit"]:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">FAQ Chatbot</div>
        <form method="post">
            <input type="text" name="question" placeholder="Ask a question..." required>
            <input type="submit" value="Ask">
        </form>
        {% if response %}
            <div class="chat-bubble user">{{ request.form['question'] }}</div>
            <div class="chat-bubble bot"><strong>Bot:</strong> {{ response }}</div>
        {% endif %}
    </div>
</body>
</html>
"""

# === Admin Dashboard Template ===
admin_template = """
<!doctype html>
<html>
<head>
    <title>Unanswered Questions</title>
    <style>
        body { font-family: Arial; background: #f4f4f4; padding: 20px; }
        .dashboard { max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; border: 1px solid #ccc; text-align: left; }
        th { background: #007bff; color: white; }
    </style>
</head>
<body>
    <div class="dashboard">
        <h2>Unanswered Questions</h2>
        <table>
            <tr><th>Question</th><th>Timestamp</th></tr>
            {% for q, t in questions %}
            <tr><td>{{ q }}</td><td>{{ t }}</td></tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

# === Match User Question ===
def find_best_match(user_question, questions):
    matches = get_close_matches(user_question, questions, n=1, cutoff=0.6)
    return matches[0] if matches else None

# === Chatbot Route ===
@app.route("/", methods=["GET", "POST"])
def chatbot():
    response = None
    if request.method == "POST":
        user_question = request.form["question"]
        match = find_best_match(user_question, qa_pairs.keys())
        if match:
            response = qa_pairs[match]
        else:
            response = "I'm sorry, I don't have an answer for that. I'll forward your question to someone who can help."
            conn = sqlite3.connect("chatbot.db")
            c = conn.cursor()
            c.execute("INSERT INTO unanswered (question) VALUES (?)", (user_question,))
            conn.commit()
            conn.close()
            notify_teams(user_question)
    return render_template_string(html_template, response=response)

# === Admin Dashboard Route ===
@app.route("/admin")
def admin_dashboard():
    conn = sqlite3.connect("chatbot.db")
    c = conn.cursor()
    c.execute("SELECT question, timestamp FROM unanswered ORDER BY timestamp DESC")
    questions = c.fetchall()
    conn.close()
    return render_template_string(admin_template, questions=questions)

# === Run App ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
