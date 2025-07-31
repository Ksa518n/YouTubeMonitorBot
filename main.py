import os
import subprocess
from googleapiclient.discovery import build
import yt_dlp
from telegram import Bot

# قراءة بيانات API من متغيرات البيئة
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# قائمة القنوات اللي تبي تتابعها (حط فيها أكثر من قناة لو حاب)
CHANNEL_IDS = [
    "UCm6dEXyAMIy0njEOW-suLww",  # مثال قناة
]

# إعداد بوت التليجرام
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# إنشاء خدمة يوتيوب API
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def get_latest_video_id(channel_id):
    try:
        request = youtube.search().list(
            part="id",
            channelId=channel_id,
            maxResults=1,
            order="date",
            type="video"
        )
        response = request.execute()
        items = response.get('items')
        if items:
            return items[0]['id']['videoId']
        else:
            print(f"لا يوجد فيديوهات في القناة {channel_id}")
            return None
    except Exception as e:
        print(f"خطأ في جلب الفيديو الأخير: {e}")
        return None

def download_video(video_url, filename):
    ydl_opts = {
        'outtmpl': filename,
        'format': 'mp4',
        'quiet': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
    except Exception as e:
        print(f"فشل تحميل الفيديو {video_url}: {e}")
        return False
    return True

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
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"خطأ في تقطيع الفيديو: {e}")
        return False
    return True

def send_to_telegram(video_path):
    try:
        with open(video_path, 'rb') as video_file:
            bot.send_video(chat_id=TELEGRAM_CHAT_ID, video=video_file)
        print(f"تم إرسال الفيديو {video_path} بنجاح للتليجرام")
    except Exception as e:
        print(f"فشل إرسال الفيديو {video_path} إلى التليجرام: {e}")

def main():
    for channel_id in CHANNEL_IDS:
        print(f"جاري معالجة القناة: {channel_id}")
        video_id = get_latest_video_id(channel_id)
        if not video_id:
            continue

        video_url = f"https://www.youtube.com/watch?v={video_id}"
        filename = f"{video_id}.mp4"

        if not os.path.exists(filename):
            print(f"جاري تحميل الفيديو {video_url}")
            success = download_video(video_url, filename)
            if not success:
                print("تخطي الفيديو بسبب فشل التحميل")
                continue

            output_pattern = f"{video_id}_part%03d.mp4"
            print("جاري تقطيع الفيديو وكتابة الأجزاء ...")
            success = cut_and_mark_video(filename, output_pattern)
            if not success:
                print("تخطي إرسال الفيديوهات بسبب فشل التقطيع")
                continue

            parts = sorted([f for f in os.listdir('.') if f.startswith(video_id + '_part')])
            for part in parts:
                print(f"إرسال {part} إلى التليجرام ...")
                send_to_telegram(part)
        else:
            print(f"الفيديو {filename} موجود مسبقاً، سيتم تخطي التحميل")

if __name__ == "__main__":
    main()
