from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import os
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)
app.secret_key = "your_secret_key"

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

questions = [
    "What is your full name?",
    "What is your address?",
    "What is your contact number?",
    "What is your date of birth?",
    "What is your gender?",
    "What is your marital status?",
    "Do you have an extra income? (Yes or No)",
    "What is the profession of your extra income?",
    "What is your income tax group? (Box1, Box2, Box3)",
    "What is your gross income for the applying month?",
    "What are your Total Social Security Wages for the applying month?",
    "Do you have the payslip in hand? (Yes or No)"
]

@app.route("/")
def index():
    session['step'] = 0
    session['answers'] = []
    return render_template("chat.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.form["message"]
    step = session.get("step", 0)
    answers = session.get("answers", [])

    if step < len(questions):
        answers.append(user_input)
        session["answers"] = answers
        session["step"] = step + 1
        if session["step"] < len(questions):
            return jsonify({"reply": questions[session['step']]})

    return jsonify({"reply": "🎉 Form completed. Upload your payslip and click Submit."})

@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files['file']
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    session["payslip_file"] = file_path
    return jsonify({"reply": "📁 Payslip uploaded!"})

@app.route("/submit", methods=["GET"])
def submit():
    try:
        df = pd.read_excel(session["payslip_file"])
        declared_income = float(session["answers"][9])
        extracted_income = float(df.iloc[1, 1])

        if abs(declared_income - extracted_income) > 10:
            return jsonify({"result": "❌ Income mismatch. Please verify and resubmit."})
        return jsonify({"result": "✅ Validation successful."})
    except Exception as e:
        return jsonify({"result": f"❌ Error: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
