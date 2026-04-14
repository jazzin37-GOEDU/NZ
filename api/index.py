import os
from flask import Flask, request, jsonify, render_template
import requests
import time
from flask_cors import CORS

# Vercel 환경을 위해 templates 폴더 위치를 명시적으로 지정합니다.
app = Flask(__name__, template_folder='../templates')
CORS(app)

# Vercel 프로젝트 설정의 Environment Variables에 DEEPL_API_KEY를 등록하세요.
# DeepL Free API 키는 보통 끝에 :fx가 붙습니다.
DEEPL_API_KEY = os.environ.get("DEEPL_API_KEY", "b8901e01-7342-4889-a4a2-f4915659778a:fx")

# DeepL API 엔드포인트 (무료 버전은 api-free.deepl.com, 유료 버전은 api.deepl.com 사용)
DEEPL_URL = "https://api-free.deepl.com/v2/translate"

def translate_with_deepl(text):
    if not DEEPL_API_KEY:
        return "Error: DeepL API Key is missing. Please set DEEPL_API_KEY in Vercel."

    # DeepL API 파라미터 설정
    # source_lang은 생략 시 자동 감지되지만, 명시적으로 지정할 수도 있습니다.
    # target_lang은 필수이며 'KO' 또는 'EN-US' 등을 사용합니다.
    
    # 텍스트가 한글이 포함되어 있는지 간단히 체크하여 목적 언어 결정
    import re
    is_korean = bool(re.search('[가-힣]', text))
    target_lang = 'EN-US' if is_korean else 'KO'

    data = {
        'auth_key': DEEPL_API_KEY,
        'text': text,
        'target_lang': target_lang
    }

    # 지수 백오프(Exponential Backoff) 적용
    for i in range(5):
        try:
            response = requests.post(DEEPL_URL, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                try:
                    # DeepL 응답은 translations 리스트 안에 담겨 옵니다.
                    return result['translations'][0]['text'].strip()
                except (KeyError, IndexError):
                    return "Error: DeepL returned an unexpected format."
            
            elif response.status_code == 403:
                return "Error 403: Invalid DeepL API Key. Check if it's the Free or Pro key."
            
            elif response.status_code == 429: # Too many requests
                time.sleep(2**i)
            
            elif response.status_code == 456: # Quota exceeded
                return "Error 456: DeepL API Quota exceeded."
            
            else:
                return f"DeepL API Error {response.status_code}: {response.text}"
                
        except Exception as e:
            if i == 4:
                return f"Connection Error: {str(e)}"
            time.sleep(2**i)
            
    return "DeepL service is currently busy. Please try again later."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def handle_translate():
    data = request.json
    if not data or 'text' not in data:
        return jsonify({"error": "No text provided"}), 400
        
    source_text = data.get('text', '')
    translated_text = translate_with_deepl(source_text)
    return jsonify({"translatedText": translated_text})

# Vercel은 이 app 객체를 자동으로 실행합니다.
