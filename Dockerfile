FROM python:3.11-slim

# تعيين متغير لمنع مشاكل التفاعل
ENV PYTHONUNBUFFERED=1

# تثبيت ffmpeg ومكتبات النظام اللي تحتاجها pytube/moviepy/telegram
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    libffi-dev \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# تحديد مجلد العمل
WORKDIR /app

# نسخ كل الملفات
COPY . .

# تثبيت المتطلبات
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# تشغيل التطبيق
CMD ["python", "main.py"]
