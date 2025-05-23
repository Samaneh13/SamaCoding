
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import pandas as pd
import os
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
    session['payslip_file'] = None
    session['retries'] = 0
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

    return jsonify({"reply": "🎉 Form completed. Please upload your payslip and then click 'Submit for Validation'."})

@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"reply": "No file uploaded."})
    file = request.files['file']
    if file.filename == '':
        return jsonify({"reply": "No selected file."})
    if file:
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        session['payslip_file'] = filename
        return jsonify({"reply": "📁 File uploaded successfully!"})

@app.route("/submit", methods=["GET"])
def submit():
    answers = session.get("answers", [])
    payslip_file = session.get("payslip_file", None)
    payslip_path = os.path.join(app.config['UPLOAD_FOLDER'], payslip_file) if payslip_file else None

    result = ""
    valid = True

    try:
        declared_income = int(answers[9])
        df = pd.read_excel(payslip_path)
        payslip_income = int(df.iloc[1, 1])

        retry_count = session.get("retries", 0)
        if declared_income != payslip_income:
            retry_count += 1
            session["retries"] = retry_count
            if retry_count >= 3:
                result = "❌ Validation failed 3 times. 📞 A staff member will contact you."
            else:
                result = f"❌ Income mismatch. Attempt {retry_count}/3. Please correct and resubmit."
        else:
            session["retries"] = 0
            result = "✅ Validation successful. Your data is ready for processing."
    except Exception as e:
        result = f"❌ Error reading payslip: {str(e)}"

    return jsonify({"result": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
