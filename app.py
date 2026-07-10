from flask import Flask, request
import telebot
import os
import yt_dlp
import logging
import time
import re

TOKEN = "8837695158:AAETrphGJh6wS1bmCXHOFB7-r4YPx0n8KR8"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

logging.basicConfig(level=logging.INFO)

def download_instagram(url):
    try:
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': False,
            'format': 'best',  # بهترین کیفیت (عکس یا فیلم)
            'ignoreerrors': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            files = []
            caption = ""
            if info:
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            fname = ydl.prepare_filename(entry)
                            if os.path.exists(fname):
                                files.append(fname)
                    if info['entries'] and info['entries'][0]:
                        caption = info['entries'][0].get('description', '')
                else:
                    fname = ydl.prepare_filename(info)
                    if os.path.exists(fname):
                        files.append(fname)
                    caption = info.get('description', '')
            return files, caption
    except Exception as e:
        logging.error(f"yt-dlp error: {e}")
        return None, str(e)

@app.route('/', methods=['POST'])
def webhook():
    try:
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            if update.message:
                chat_id = update.message.chat.id
                text = update.message.text
                if text.startswith('/start'):
                    bot.send_message(chat_id, "سلام! لینک اینستاگرام رو بفرست.")
                    return 'OK', 200
                if 'instagram.com' in text:
                    msg = bot.send_message(chat_id, "⏳ دانلود...")
                    files, caption = download_instagram(text)
                    if not files:
                        bot.edit_message_text(f"❌ خطا: {caption}", chat_id, msg.message_id)
                        return 'OK', 200
                    for i, f in enumerate(files):
                        with open(f, 'rb') as media:
                            if f.lower().endswith(('.mp4', '.mov')):
                                bot.send_video(chat_id, media, caption=caption if i == 0 else None)
                            else:
                                bot.send_photo(chat_id, media, caption=caption if i == 0 else None)
                        os.remove(f)
                    bot.edit_message_text("✅ دانلود کامل شد!", chat_id, msg.message_id)
                else:
                    bot.send_message(chat_id, "❌ لینک اینستاگرام بفرست.")
            return 'OK', 200
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return 'Error', 500

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url='https://telegram-bot-tkaz.onrender.com/')
    return 'Webhook set!', 200

@app.route('/', methods=['GET'])
def home():
    return 'Bot is running!', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
