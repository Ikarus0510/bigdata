# AI 自動產生分析報告系統

使用 Google Gemini API 進行輿情分析，輸入關鍵字即可自動產生完整分析報告。

## 安裝步驟

1. 安裝依賴套件

pip install -r requirements.txt


2. 設定 Google Gemini API 金鑰

前往 https://makersuite.google.com/app/apikey 建立 API 金鑰

複製 .env.example 為 .env

編輯 .env 檔案並填入你的金鑰

像是 GEMINI_API_KEY=AIzaSy...


3. 啟動伺服器

python manage.py runserver

然後開啟瀏覽器：http://127.0.0.1:8000/userkeyword_report/