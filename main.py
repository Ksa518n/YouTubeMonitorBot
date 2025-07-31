import os
import requests
import time
from pytube import YouTube
from flask import Flask
from telegram import Bot

# متغيرات البيئة من رندر
YOUTUBE_API_KEY = os.environ['YOUTUBE_API_KEY']
CHANNEL_ID = os.environ['CHANNEL_ID']
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

CHECK_INTERVAL = 60  # كل دقيقة
video_cache = set()

def get_latest_video_id():
    url = f'https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={CHANNEL_ID}&part=snippet,id&order=date&maxResults=1'
    response = requests.get(url)
    data = response.json()
    if 'items' in data and len(data['items']) > 0:
        return data['items'][0]['id']['videoId']
    return None

def download_and_send_parts(video_url, title):
    yt = YouTube(video_url)
    stream = yt.streams.get_highest_resolution()
    file_path = stream.download(filename='video.mp4')

    part_duration = 90  # ثانية
    output_template = "part_%03d.mp4"
    os.system(f"ffmpeg -i video.mp4 -c copy -map 0 -segment_time {part_duration} -f segment {output_template}")

    part_num = 1
    while os.path.exists(f"part_{part_num:03}.mp4"):
        part_file = f"part_{part_num:03}.mp4"
        with open(part_file, 'rb') as f:
            bot.send_video(chat_id=TELEGRAM_CHAT_ID, video=f, caption=f"{title} - Part {part_num}")
        os.remove(part_file)
        part_num += 1

    os.remove("video.mp4")

def check_for_new_video():
    video_id = get_latest_video_id()
    if video_id and video_id not in video_cache:
        video_cache.add(video_id)
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        yt = YouTube(video_url)
        download_and_send_parts(video_url, yt.title)

@app.route("/")
def home():
    return "YouTube Monitor Bot is running!"

if __name__ == "__main__":
    while True:
        try:
            check_for_new_video()
        except Exception as e:
            print("Error:", e)
        time.sleep(CHECK_INTERVAL)
