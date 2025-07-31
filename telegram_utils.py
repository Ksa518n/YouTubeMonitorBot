from telegram import Bot

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_video_to_telegram(file_path, part_number):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    caption = f"Part {part_number}"
    with open(file_path, 'rb') as video:
        bot.send_video(chat_id=TELEGRAM_CHAT_ID, video=video, caption=caption)
