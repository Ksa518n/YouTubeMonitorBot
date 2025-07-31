import os
import yt_dlp
import requests
from flask import Flask
from pytube import YouTube
from moviepy.video.io.VideoFileClip import VideoFileClip
from pydub import AudioSegment
from telegram import Bot

app = Flask(__name__)

YOUTUBE_CHANNEL_ID = "UCm6dEXyAMIy0njEOW-suLww"
MY_CHANNEL_UPLOAD_URL = "https://www.youtube.com/@Ksa518nn"
TELEGRAM_TOKEN = "7775785980:AAEqt9Xld1mVZKwTH3lUOab9OELokAmsirA"
TELEGRAM_CHAT_ID = "518518518"
DOWNLOAD_PATH = "./downloads"

os.makedirs(DOWNLOAD_PATH, exist_ok=True)

def download_latest_video():
    ydl_opts = {
        'quiet': True,
        'outtmpl': f'{DOWNLOAD_PATH}/%(id)s.%(ext)s',
        'format': 'best'
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # استخراج بيانات القناة
        channel_url = f"https://www.youtube.com/channel/{YOUTUBE_CHANNEL_ID}/videos"
        info = ydl.extract_info(channel_url, download=False)
        
        # أخذ أحدث فيديو
        if "entries" not in info or not info["entries"]:
            print("❌ لا توجد فيديوهات.")
            return None

        latest_video = info["entries"][0]
        video_id = latest_video["id"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        # نحاول نتأكد أن الفيديو متاح
        try:
            ydl.extract_info(video_url, download=False)
        except Exception as e:
            print(f"⚠️ الفيديو غير متاح: {video_url}")
            return None
        
        # إذا الفيديو متاح نحمله
        ydl.download([video_url])
        return os.path.join(DOWNLOAD_PATH, f"{video_id}.mp4")

def split_video(video_path):
    clip = VideoFileClip(video_path)
    duration = clip.duration
    parts = []

    i = 0
    start = 0
    while start < duration:
        end = min(start + 90, duration)
        part_path = f"{video_path}_part{i+1}.mp4"
        clip.subclip(start, end).write_videofile(part_path, codec="libx264")
        parts.append(part_path)
        start = end
        i += 1

    clip.close()
    return parts

def notify_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    requests.post(url, data=data)

@app.route("/")
def run_bot():
    video_path = download_latest_video()
    if not video_path:
        return "⛔ لم يتم تحميل أي فيديو."

    parts = split_video(video_path)

    for idx, part in enumerate(parts):
        print(f"✅ Part {idx+1} saved: {part}")

    notify_telegram("📢 تم رفع الفيديو المجزأ على القناة.")

    return "✅ اكتملت العملية."

if __name__ == "__main__":
    app.run(debug=True)
