import os
import logging
from telegram import Bot
from telegram.error import TelegramError
from flask import Flask
from youtube_downloader import check_new_video_and_process

app = Flask(__name__)

TELEGRAM_TOKEN = "7775785980:AAEIifkXcI1nHMOlmbaUE140unjFiK_8MYY"
CHANNEL_ID = "UCm6dEXyAMIy0njEOW-suLww"
TELEGRAM_CHAT_ID = "1459633282"  # غيره لـ ID حسابك

bot = Bot(token=TELEGRAM_TOKEN)

@app.route('/')
def index():
    return 'YouTube Monitor Running!'

@app.route('/check')
def run_check():
    try:
        new_video = check_new_video_and_process(CHANNEL_ID)
        if new_video:
            message = f"📢 تم تحميل فيديو جديد وتقسيمه: {new_video['title']}"
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        return "Checked!"
    except TelegramError as e:
        logging.error(f"Telegram Error: {e}")
        return "Telegram Error"
    except Exception as e:
        logging.error(f"General Error: {e}")
        return "Error"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
