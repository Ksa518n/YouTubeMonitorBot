import os
import requests
import time
from pytube import YouTube
from moviepy.video.io.VideoFileClip import VideoFileClip
from telegram import Bot

# إعدادات
CHANNEL_ID = "UCm6dEXyAMIy0njEOW-suLww"
API_KEY = "AIzaSyD...your-youtube-api-key..."  # ضع مفتاح YouTube Data API v3
TELEGRAM_TOKEN = "7775785980:AAEqt9Xld1mVZKwTH3lUOab9OELokAmsirA"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"  # معرف الشات، يمكنك استخدام BotFather للحصول عليه

VIDEO_FOLDER = "videos"
os.makedirs(VIDEO_FOLDER, exist_ok=True)

bot = Bot(token=TELEGRAM_TOKEN)

# جلب أحدث فيديو
def get_latest_video():
    url = f"https://www.googleapis.com/youtube/v3/search?key={API_KEY}&channelId={CHANNEL_ID}&part=snippet,id&order=date&maxResults=1"
    r = requests.get(url)
    data = r.json()
    video_id = data["items"][0]["id"].get("videoId", None)
    return video_id

# تحميل فيديو
def download_video(video_id):
    yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
    stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
    file_path = os.path.join(VIDEO_FOLDER, f"{video_id}.mp4")
    stream.download(output_path=VIDEO_FOLDER, filename=f"{video_id}.mp4")
    return file_path

# تقسيم الفيديو إلى أجزاء كل جزء دقيقة ونص
def split_video(file_path):
    clips = []
    clip = VideoFileClip(file_path)
    duration = clip.duration
    count = 1
    for start in range(0, int(duration), 90):
        end = min(start + 90, duration)
        part_path = os.path.join(VIDEO_FOLDER, f"part{count}.mp4")
        clip.subclip(start, end).write_videofile(part_path, codec="libx264", audio_codec="aac")
        clips.append(part_path)
        count += 1
    clip.close()
    return clips

# إرسال الفيديوهات لتليجرام
def send_to_telegram(parts):
    for i, part in enumerate(parts):
        caption = f"Part {i + 1}"
        with open(part, 'rb') as video_file:
            bot.send_video(chat_id=TELEGRAM_CHAT_ID, video=video_file, caption=caption)

# التخزين المحلي للفيديو السابق
LAST_ID_FILE = "last_video_id.txt"

def get_last_video_id():
    if os.path.exists(LAST_ID_FILE):
        with open(LAST_ID_FILE, "r") as f:
            return f.read().strip()
    return ""

def save_last_video_id(video_id):
    with open(LAST_ID_FILE, "w") as f:
        f.write(video_id)

# المهمة الرئيسية
def main():
    while True:
        try:
            latest_video_id = get_latest_video()
            last_video_id = get_last_video_id()

            if latest_video_id and latest_video_id != last_video_id:
                print(f"[+] فيديو جديد: {latest_video_id}")
                file_path = download_video(latest_video_id)
                parts = split_video(file_path)
                send_to_telegram(parts)
                save_last_video_id(latest_video_id)
            else:
                print("[-] لا يوجد فيديو جديد")

        except Exception as e:
            print(f"[!] خطأ: {e}")

        time.sleep(300)  # انتظر 5 دقائق قبل التحقق مجددًا

if __name__ == "__main__":
    main()
