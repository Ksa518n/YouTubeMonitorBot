# استخدم صورة Python الرسمية مع إصدار 3.11
FROM python:3.11-slim

# تثبيت ffmpeg وأدوات أساسية
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# إنشاء مجلد العمل
WORKDIR /app

# نسخ ملفات المشروع إلى مجلد العمل
COPY . /app

# تثبيت مكتبات Python المطلوبة
RUN pip install --no-cache-dir -r requirements.txt

# أمر تشغيل البرنامج عند بدء الحاوية
CMD ["python", "main.py"]
