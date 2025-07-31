import time
import requests
import json
import os

from config import YOUTUBE_CHANNEL_ID, YOUTUBE_API_KEY, CHECK_INTERVAL
from youtube_utils import download_video, split_video
from telegram_utils import send_video_to_telegram

def get_latest_video_id(channel_id, api_key):
    url = f"https://www.googleapis.com/youtube/v3/search?key={api_key}&channelId={channel_id}&part=snippet,id&order=date&maxResults=1"
    response = requests.get(url)
    data = response.json()
    items = data.get("items", [])
    if not items:
        return None
    video_id = items[0]["id"].get("videoId")
    return video_id

def load_last_video_id():
    if os.path.exists("last_video.txt"):
        with open("last_video.txt", "r") as f:
            return f.read().strip()
    return None

def save_last_video_id(video_id):
    with open("last_video.txt", "w") as f:
        f.write(video_id)

def process_new_video(video_id):
    print(f"🟢 New video found: {video_id}")
    url = f"https://www.youtube.com/watch?v={video_id}"
    file_path = download_video(url)
    parts = split_video(file_path)
    for i, part in enumerate(parts, start=1):
        send_video_to_telegram(part, i)

def main_loop():
    while True:
        try:
            latest_id = get_latest_video_id(YOUTUBE_CHANNEL_ID, YOUTUBE_API_KEY)
            last_saved = load_last_video_id()
            if latest_id and latest_id != last_saved:
                process_new_video(latest_id)
                save_last_video_id(latest_id)
            else:
                print("🔁 No new videos.")
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main_loop()
