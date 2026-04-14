import os
from flask import Flask, request, jsonify, render_template
import requests
import time
from flask_cors import CORS

# Vercel 환경을 위해 templates 폴더 위치를 명시적으로 지정합니다.
app = Flask(__name__, template_folder='../templates')
CORS(app)

API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyC-CgzFK8oJbFZnN8y62t3A0j7i4p5jac0") 
MODEL_NAME = "gemini-2.5-flash-preview-09-2025"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"

def translate_with_gemini(text):
    if not API_KEY:
        return "Error: API Key is missing."
    prompt = f"Translate to English if Korean, or to Korean if English: {text}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(API_URL, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', "").strip()
    except Exception:
        pass
    return "Translation error."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def handle_translate():
    data = request.json
    source_text = data.get('text', '')
    translated_text = translate_with_gemini(source_text)
    return jsonify({"translatedText": translated_text})

# Vercel은 이 app 객체를 자동으로 실행합니다.