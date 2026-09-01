FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3001
EXPOSE 3002

# 🔥 Waitress com 8 threads
CMD ["python", "-c", "from waitress import serve; frpython:3.12om app import app; serve(app, host='0.0.0.0', port=3001, threads=8)"]