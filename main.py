from flask import Flask
from pytube import YouTube
from moviepy.video.io.VideoFileClip import VideoFileClip
import os
import requests
import time
from telegram import Bot

app = Flask(__name__)

# إعداد التليجرام
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(token=TELEGRAM_TOKEN)

# إعداد القناة المستهدفة
CHANNEL_ID = "UCm6dEXyAMIy0njEOW-suLww"
LAST_VIDEO_ID_FILE = "last_video_id.txt"

@app.route('/')
def index():
    return 'YouTube Automation System is Running!'

def get_latest_video():
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    content = response.text
    start = content.find("<yt:videoId>") + len("<yt:videoId>")
    end = content.find("</yt:videoId>")
    video_id = content[start:end]
    return video_id

def download_and_split(video_id):
    yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
    stream = yt.streams.filter(progressive=True, file_extension="mp4").order_by('resolution').desc().first()
    video_path = stream.download(filename="full_video.mp4")

    clip = VideoFileClip(video_path)
    duration = clip.duration
    part = 1
    start = 0

    while start < duration:
        end = min(start + 90, duration)
        subclip = clip.subclip(start, end)
        part_filename = f"part_{part}.mp4"
        subclip.write_videofile(part_filename, codec="libx264", audio_codec="aac")
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"Part {part} جاهز ✅")
        start += 90
        part += 1

    clip.close()

def save_last_video(video_id):
    with open(LAST_VIDEO_ID_FILE, "w") as f:
        f.write(video_id)

def load_last_video():
    if not os.path.exists(LAST_VIDEO_ID_FILE):
        return None
    with open(LAST_VIDEO_ID_FILE, "r") as f:
        return f.read().strip()

def check_for_new_video():
    last_saved = load_last_video()
    current = get_latest_video()
    if current and current != last_saved:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="📥 تم العثور على فيديو جديد، جاري التحميل والتقسيم...")
        download_and_split(current)
        save_last_video(current)
    else:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="✅ لا يوجد فيديو جديد الآن.")

if __name__ == "__main__":
    from threading import Thread

    def run_checker():
        while True:
            try:
                check_for_new_video()
            except Exception as e:
                bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"❌ حصل خطأ: {str(e)}")
            time.sleep(600)  # كل 10 دقائق

    Thread(target=run_checker).start()
    app.run(host="0.0.0.0", port=8000)
