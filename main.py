import os
import threading
import time
from flask import Flask
from googleapiclient.discovery import build
from pytube import YouTube
from moviepy.video.io.VideoFileClip import VideoFileClip
from telegram import Bot, Update
from telegram.ext import CommandHandler, ApplicationBuilder, ContextTypes

# المتغيرات البيئية
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ADMIN_ID = os.getenv("ADMIN_ID")

# Flask App
app = Flask(__name__)

@app.route("/")
def home():
    return "YouTube Monitor is running"

# YouTube API setup
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
last_video_id = None
monitoring_active = False

# تابع مراقبة اليوتيوب
def check_new_video():
    global last_video_id, monitoring_active
    while monitoring_active:
        try:
            req = youtube.search().list(part="snippet", channelId=YOUTUBE_CHANNEL_ID, order="date", maxResults=1)
            res = req.execute()
            video = res["items"][0]
            video_id = video["id"]["videoId"]
            if video_id != last_video_id:
                last_video_id = video_id
                url = f"https://www.youtube.com/watch?v={video_id}"
                download_and_send_video(url)
        except Exception as e:
            print(f"Error checking video: {e}")
        time.sleep(60)

# تحميل الفيديو وإرساله بتجزئة 1:30
def download_and_send_video(url):
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        filename = "video.mp4"
        stream.download(filename=filename)

        clips = split_video(filename)
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        for i, clip_path in enumerate(clips, 1):
            with open(clip_path, 'rb') as video_file:
                bot.send_video(chat_id=TELEGRAM_CHAT_ID, video=video_file, caption=f"Part {i}")
    except Exception as e:
        print(f"Error downloading/sending video: {e}")

# تقسيم الفيديو إلى مقاطع 90 ثانية
def split_video(file_path):
    clip = VideoFileClip(file_path)
    clips = []
    part = 1
    for i in range(0, int(clip.duration), 90):
        part_path = f"part{part}.mp4"
        clip.subclip(i, min(i + 90, clip.duration)).write_videofile(part_path, codec="libx264", logger=None)
        clips.append(part_path)
        part += 1
    return clips

# أوامر البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 بوت مراقبة اليوتيوب جاهز.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_ID:
        return
    if last_video_id:
        await update.message.reply_text(f"آخر فيديو: https://youtu.be/{last_video_id}")
    else:
        await update.message.reply_text("لم يتم العثور على فيديو بعد.")

async def start_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global monitoring_active
    if str(update.effective_user.id) != ADMIN_ID:
        return
    if not monitoring_active:
        monitoring_active = True
        threading.Thread(target=check_new_video, daemon=True).start()
        await update.message.reply_text("🚀 بدأ المراقبة.")
    else:
        await update.message.reply_text("المراقبة تعمل بالفعل.")

async def stop_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global monitoring_active
    if str(update.effective_user.id) != ADMIN_ID:
        return
    if monitoring_active:
        monitoring_active = False
        await update.message.reply_text("🛑 تم إيقاف المراقبة.")
    else:
        await update.message.reply_text("المراقبة متوقفة بالفعل.")

# بدء التليجرام بوت و Flask
def run_bot():
    app_bot = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("status", status))
    app_bot.add_handler(CommandHandler("start_monitoring", start_monitoring))
    app_bot.add_handler(CommandHandler("stop_monitoring", stop_monitoring))
    app_bot.run_polling()

# تشغيل الاثنين معاً
if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
