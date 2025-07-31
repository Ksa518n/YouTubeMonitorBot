import os
import time
import threading
from flask import Flask
from googleapiclient.discovery import build
from pytube import YouTube
from moviepy.video.io.VideoFileClip import VideoFileClip
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

# المتغيرات البيئية
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# إعداد Flask
app = Flask(__name__)
@app.route("/")
def home():
    return "✅ YouTube Monitor Bot is Running!"

# إعداد YouTube API
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
last_video_id = None
monitoring_active = False

# دالة مراقبة قناة اليوتيوب
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
            print(f"[!] Error checking video: {e}")
        time.sleep(60)

# تحميل الفيديو وتقسيمه وإرساله
def download_and_send_video(url):
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        filename = "video.mp4"
        stream.download(filename=filename)

        clips = split_video(filename)
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        for i, part_path in enumerate(clips, 1):
            with open(part_path, 'rb') as f:
                bot.send_video(chat_id=TELEGRAM_CHAT_ID, video=f, caption=f"🎬 Part {i}")
    except Exception as e:
        print(f"[!] Error sending video: {e}")

# تقسيم الفيديو إلى مقاطع مدتها 90 ثانية
def split_video(file_path):
    clip = VideoFileClip(file_path)
    clips = []
    for i in range(0, int(clip.duration), 90):
        part_path = f"part_{i//90 + 1}.mp4"
        clip.subclip(i, min(i + 90, clip.duration)).write_videofile(part_path, codec="libx264", audio_codec="aac")
        clips.append(part_path)
    return clips

# أوامر البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أهلاً بك! استخدم /start_monitoring لبدء المراقبة أو /stop_monitoring للإيقاف.")

async def start_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global monitoring_active
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 غير مصرح لك باستخدام هذا الأمر.")
    if not monitoring_active:
        monitoring_active = True
        threading.Thread(target=check_new_video, daemon=True).start()
        await update.message.reply_text("✅ بدأت مراقبة قناة اليوتيوب.")
    else:
        await update.message.reply_text("ℹ️ المراقبة تعمل بالفعل.")

async def stop_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global monitoring_active
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 غير مصرح لك باستخدام هذا الأمر.")
    monitoring_active = False
    await update.message.reply_text("🛑 تم إيقاف مراقبة قناة اليوتيوب.")

# بدء البوت
def start_bot():
    app_bot = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("start_monitoring", start_monitoring))
    app_bot.add_handler(CommandHandler("stop_monitoring", stop_monitoring))
    app_bot.run_polling()

# تشغيل البوت في خيط منفصل
threading.Thread(target=start_bot, daemon=True).start()

# تشغيل السيرفر Flask
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
