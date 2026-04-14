import os
from flask import Flask, request, jsonify, render_template
import requests
import time
from flask_cors import CORS
import re

app = Flask(__name__, template_folder='../templates')
CORS(app)

# 환경변수 설정 확인
DEEPL_API_KEY = os.environ.get("DEEPL_API_KEY", "b8901e01-7342-4889-a4a2-f4915659778a:fx").strip()

def translate_with_deepl(text):
    if not DEEPL_API_KEY:
        return "Error: DeepL API Key is missing. Please set DEEPL_API_KEY in Vercel settings."

    # [로직 개선] 한국어 입력 -> 영어 번역 / 영어 입력 -> 한국어 번역
    # 1. 한글이 포함되어 있는지 확인
    has_korean = bool(re.search('[가-힣]', text))
    # 2. 영어 알파벳이 포함되어 있는지 확인
    has_english = bool(re.search('[a-zA-Z]', text))

    # 로직 결정:
    # 한글이 포함되어 있으면 한국어로 쓴 것으로 간주 -> 영어(EN-US)로 번역
    # 한글이 없고 영어가 포함되어 있으면 -> 한국어(KO)로 번역
    # 둘 다 없거나 모호하면 기본적으로 한국어(KO)로 번역을 시도
    if has_korean:
        target_lang = 'EN-US'
    elif has_english:
        target_lang = 'KO'
    else:
        # 기본값은 한국어 번역으로 설정 (뉴질랜드 학생 배려)
        target_lang = 'KO'

    headers = {
        "Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}"
    }
    
    data = {
        'text': text,
        'target_lang': target_lang
    }

    # 무료/유료 서버 주소 리스트
    primary_url = "https://api-free.deepl.com/v2/translate" if DEEPL_API_KEY.endswith(':fx') else "https://api.deepl.com/v2/translate"
    secondary_url = "https://api.deepl.com/v2/translate" if DEEPL_API_KEY.endswith(':fx') else "https://api-free.deepl.com/v2/translate"
    urls = [primary_url, secondary_url]

    for url in urls:
        for i in range(3):
            try:
                # 데이터를 보낼 때 명시적으로 timeout을 설정하여 무한 대기를 방지합니다.
                response = requests.post(url, headers=headers, data=data, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    return result['translations'][0]['text'].strip()
                
                elif response.status_code == 403:
                    break # 다음 주소로 시도
                
                elif response.status_code == 429:
                    time.sleep(1)
                    continue
                
                elif response.status_code == 456:
                    return "Error 456: DeepL API Quota exceeded."
                
                else:
                    continue
                    
            except Exception as e:
                time.sleep(1)
                
    return f"번역 응답 실패 (목적 언어: {target_lang}). 입력한 텍스트를 확인하거나 잠시 후 다시 시도해 주세요."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def handle_translate():
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({"error": "No text provided"}), 400
            
        source_text = data.get('text', '')
        if not source_text.strip():
            return jsonify({"translatedText": ""})

        translated_text = translate_with_deepl(source_text)
        return jsonify({"translatedText": translated_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
