import os
from flask import Flask, request, jsonify, render_template
import requests
import time
from flask_cors import CORS

# Vercel 환경을 위해 templates 폴더 위치를 명시적으로 지정합니다.
app = Flask(__name__, template_folder='../templates')
CORS(app)

# Vercel 프로젝트 설정의 Environment Variables에 GEMINI_API_KEY를 반드시 등록해야 합니다.
API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyC-CgzFK8oJbFZnN8y62t3A0j7i4p5jac0") 

# [수정] 404 에러 해결을 위해 모델명을 최신 버전인 'gemini-1.5-flash-latest'로 변경합니다.
MODEL_NAME = "gemini-1.5-flash-latest"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"

def translate_with_gemini(text):
    if not API_KEY:
        return "Error: API Key is missing on the server side."

    # 신문 제작에 최적화된 프롬프트 구성
    prompt = f"""Translate the following text for a school exchange newspaper. 
    If the input is Korean, translate to English. If the input is English, translate to Korean.
    Maintain a friendly and educational tone. 
    Keep the output as plain text only.
    
    Text: {text}"""
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    # 지수 백오프(Exponential Backoff)를 사용하여 안정성 강화
    for i in range(5):
        try:
            response = requests.post(API_URL, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', "").strip()
            elif response.status_code == 429: # Rate limit reached
                time.sleep(2**i)
            elif response.status_code == 404: # 모델명을 찾을 수 없는 경우
                return f"API Error 404: Model '{MODEL_NAME}' not found. Please verify the model name and API version."
            else:
                return f"API Error: {response.status_code} - {response.text}"
        except Exception as e:
            if i == 4: # 마지막 시도에서도 실패하면 에러 메시지 반환
                return f"Connection Error: {str(e)}"
            time.sleep(2**i)
            
    return "Translation service is currently busy. Please try again later."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def handle_translate():
    data = request.json
    if not data or 'text' not in data:
        return jsonify({"error": "No text provided"}), 400
        
    source_text = data.get('text', '')
    translated_text = translate_with_gemini(source_text)
    return jsonify({"translatedText": translated_text})

# Vercel은 이 app 객체를 자동으로 실행합니다.
