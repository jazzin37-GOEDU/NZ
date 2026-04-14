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

    # [로직 정밀 개선] 
    # 1. 텍스트에서 한글이 한 글자라도 있는지 확인
    has_korean = bool(re.search('[가-힣]', text))
    
    # 2. 번역 방향 결정
    # 한글이 포함되어 있다면 한국 사용자가 쓴 것이므로 영어(EN-US)로 번역
    # 한글이 전혀 없다면 뉴질랜드 사용자가 쓴 것이므로 한국어(KO)로 번역
    if has_korean:
        target_lang = 'EN-US'
    else:
        target_lang = 'KO'

    headers = {
        "Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}"
    }
    
    # DeepL API에 전달할 데이터
    # source_lang을 명시하지 않으면 DeepL이 자동으로 감지하여 정확도가 높아집니다.
    data = {
        'text': text,
        'target_lang': target_lang
    }

    # 무료/유료 서버 주소 리스트 (자동 전환 로직)
    primary_url = "https://api-free.deepl.com/v2/translate" if DEEPL_API_KEY.endswith(':fx') else "https://api.deepl.com/v2/translate"
    secondary_url = "https://api.deepl.com/v2/translate" if DEEPL_API_KEY.endswith(':fx') else "https://api-free.deepl.com/v2/translate"
    urls = [primary_url, secondary_url]

    for url in urls:
        for i in range(3):
            try:
                response = requests.post(url, headers=headers, data=data, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    return result['translations'][0]['text'].strip()
                
                elif response.status_code == 403:
                    break # API 키 타입 불일치 시 다음 URL 시도
                
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
    # 로컬 테스트용 포트 설정
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
