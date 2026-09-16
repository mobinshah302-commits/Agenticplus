FROM python:3.11-slim

# نصب پیش‌نیازهای لازم برای کامپایل پکیج‌های پایتونی (Rust و GCC)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    rustc \
    cargo \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "main.py"]
