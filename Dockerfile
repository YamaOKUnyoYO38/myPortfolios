FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# Streamlit はデフォルトで 8501
EXPOSE 8501

# ホスト全インターフェースで待受（コンテナ/Render 用）
CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
