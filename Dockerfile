FROM kalilinux/kali-rolling
RUN apt-get update && apt-get install -y python3 python3-pip
WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt --break-system-packages
COPY . .
CMD ["python3", "main.py"]
