import os
import subprocess
from googleapiclient.discovery import build
import yt_dlp
from telegram import Bot
from flask import Flask, request

app = Flask(__name__)

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def get_latest_video_id(channel_id):
    request_youtube = youtube.search().list(
        part="id",
        channelId=channel_id,
        maxResults=1,
        order="date",
        type="video"
    )
    response = request_youtube.execute()
    items = response.get('items')
    if items:
        return items[0]['id']['videoId']
    return None

def download_video(video_url, filename):
    ydl_opts = {
        'outtmpl': filename,
        'format': 'mp4',
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

def cut_and_mark_video(filename, output_pattern):
    command = [
        "ffmpeg", "-i", filename, "-vf",
        "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='pert\\: %{n}':x=10:y=10:fontsize=24:fontcolor=white:box=1:boxcolor=black@0.5",
        "-c:a", "copy",
        "-f", "segment",
        "-segment_time", "90",
        "-reset_timestamps", "1",
        output_pattern
    ]
    subprocess.run(command, check=True)

def send_to_telegram(video_path):
    with open(video_path, 'rb') as video_file:
        bot.send_video(chat_id=TELEGRAM_CHAT_ID, video=video_file)

@app.route('/')
def main():
    channel_id = request.args.get("channel_id", "UCm6dEXyAMIy0njEOW-suLww")

    video_id = get_latest_video_id(channel_id)
    if not video_id:
        return f"No videos found for channel {channel_id}", 404

    video_url = f"https://www.youtube.com/watch?v={video_id}"
    filename = f"{video_id}.mp4"

    if not os.path.exists(filename):
        download_video(video_url, filename)
        output_pattern = f"{video_id}_part%03d.mp4"
        cut_and_mark_video(filename, output_pattern)

        parts = sorted([f for f in os.listdir('.') if f.startswith(video_id + '_part')])
        for part in parts:
            send_to_telegram(part)
        return "Videos sent to Telegram"
    else:
        return "Video already downloaded"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
