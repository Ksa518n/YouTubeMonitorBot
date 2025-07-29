# استخدم صورة Python الرسمية
FROM python:3.11-slim

# تعيين متغير بيئة لمنع مشاكل التفاعل
ENV PYTHONUNBUFFERED=1

# تثبيت ffmpeg + أدوات النظام الأساسية
RUN apt-get update && \
    apt-get install -y ffmpeg gcc libffi-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# تحديد مجلد العمل
WORKDIR /app

# نسخ كل ملفات المشروع
COPY . .

# تثبيت المتطلبات
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# تحديد أمر التشغيل
CMD ["python", "main.py"]
