import os
import threading
from flask import Flask
from googleapiclient.discovery import build
from pytube import YouTube
from moviepy.video.io.VideoFileClip import VideoFileClip
from telegram import Bot

# إعداد المتغيرات من البيئة
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Flask app للتوافق مع Render
app = Flask(__name__)

@app.route("/")
def home():
    return "YouTube Monitor is running"

# إعدادات اليوتيوب
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
last_video_id = None

# تابع لمراقبة قناة اليوتيوب
def check_new_video():
    global last_video_id
    while True:
        req = youtube.search().list(part="snippet", channelId=YOUTUBE_CHANNEL_ID, order="date", maxResults=1)
        res = req.execute()
        video = res["items"][0]
        video_id = video["id"]["videoId"]
        if video_id != last_video_id:
            last_video_id = video_id
            url = f"https://www.youtube.com/watch?v={video_id}"
            download_and_send_video(url)
        time.sleep(60)

# تحميل الفيديو وتقسيمه ورفعه للتلقرام
def download_and_send_video(url):
    yt = YouTube(url)
    stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
    filename = "video.mp4"
    stream.download(filename=filename)

    clips = split_video(filename)
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    for i, clip_path in enumerate(clips, 1):
        bot.send_video(chat_id=TELEGRAM_CHAT_ID, video=open(clip_path, 'rb'), caption=f"Part {i}")

def split_video(file_path):
    clip = VideoFileClip(file_path)
    clips = []
    part = 1
    for i in range(0, int(clip.duration), 90):
        part_path = f"part{part}.mp4"
        clip.subclip(i, min(i + 90, clip.duration)).write_videofile(part_path, codec="libx264")
        clips.append(part_path)
        part += 1
    return clips

# بدء خيط المراقبة
threading.Thread(target=check_new_video, daemon=True).start()

# تشغيل السيرفر على البورت المناسب
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
