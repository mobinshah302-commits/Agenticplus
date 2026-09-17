FROM python:3.11-slim

# ابزارهای پایه‌ی توسعه + Node.js + گیت + کامپایلرها
# (اجنت می‌تونه با pip/npm داخل هوم خودِ هر کاربر هرچی لازم داره نصب کنه)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ make git curl wget unzip \
    build-essential python3-dev \
    sudo procps \
    ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# دایرکتوری داده‌ی پایدار (دیتابیس + هوم هر کاربر)
RUN mkdir -p /data/sandboxes /data/db

ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/data

CMD ["python", "main.py"]
