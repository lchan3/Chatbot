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
<head><title>FAQ Chatbot</title></head>
<body>
    <h2>FAQ Chatbot</h2>
    <form method="post">
        <label for="question">Ask a question:</label><br>
        <input type="text" id="question" name="question" size="80" required><br><br>
        <input type="submit" value="Ask">
    </form>
    {% if response %}
        <p><strong>Bot:</strong> {{ response }}</p>
    {% endif %}
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
