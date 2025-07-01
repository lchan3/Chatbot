from flask import Flask, request, render_template_string
from docx import Document
from difflib import get_close_matches
import os

app = Flask(__name__)

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

html_template = """
<!doctype html>
<html>
<head>
    <title>FAQ Chatbot</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f4f4f4;
            margin: 0;
            padding: 20px;
        }
        .chat-container {
            max-width: 700px;
            margin: auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .chat-header {
            font-size: 24px;
            margin-bottom: 20px;
            text-align: center;
        }
        .chat-bubble {
            background: #e0e0e0;
            padding: 10px 15px;
            border-radius: 15px;
            margin-bottom: 10px;
            max-width: 80%;
        }
        .bot {
            background: #d1e7dd;
            align-self: flex-start;
        }
        .user {
            background: #cfe2ff;
            align-self: flex-end;
            text-align: right;
        }
        form {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        input[type="text"] {
            padding: 10px;
            font-size: 16px;
            border-radius: 5px;
            border: 1px solid #ccc;
        }
        input[type="submit"] {
            padding: 10px;
            font-size: 16px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        input[type="submit"]:hover {
            background: #0056b3;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">FAQ Chatbot</div>
        <form method="post">
            <input type="text" id="question" name="question" placeholder="Ask a question..." required>
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

def find_best_match(user_question, questions):
    matches = get_close_matches(user_question, questions, n=1, cutoff=0.6)
    return matches[0] if matches else None

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
            with open("unanswered_questions.txt", "a") as f:
                f.write(user_question + "\n")
    return render_template_string(html_template, response=response)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
