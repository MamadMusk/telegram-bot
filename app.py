from flask import Flask, request
import telebot
import os
import re
import yt_dlp
import logging
import time

TOKEN = "8837695158:AAETrphGJh6wS1bmCXHOFB7-r4YPx0n8KR8"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

logging.basicConfig(level=logging.INFO)

def download_instagram_post(url):
    """
    دانلود با yt-dlp (هم عکس و هم فیلم)
    """
    try:
        logging.info(f"Downloading: {url}")
        
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'cookiefile': 'cookies.txt',  # حتماً کوکی معتبر باشه
            'format': 'best',  # بهترین کیفیت رو بگیر (چه عکس چه فیلم)
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
                            filename = ydl.prepare_filename(entry)
                            if os.path.exists(filename):
                                files.append(filename)
                    caption = info.get('description', '')
                else:
                    filename = ydl.prepare_filename(info)
                    if os.path.exists(filename):
                        files.append(filename)
                    caption = info.get('description', '')
            
            if files:
                logging.info(f"Downloaded {len(files)} files")
                return files, caption
            else:
                return None, "هیچ فایلی دانلود نشد."
                
    except Exception as e:
        logging.error(f"yt-dlp error: {e}")
        return None, f"خطا: {str(e)}"

@app.route('/', methods=['POST'])
def webhook():
    try:
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            
            if update.message:
                chat_id = update.message.chat.id
                text = update.message.text
                logging.info(f"Message: {text}")
                
                if text and text.startswith('/start'):
                    bot.send_message(chat_id, "سلام! لینک اینستاگرام رو بفرست.")
                    return 'OK', 200
                
                if text and 'instagram.com' in text:
                    msg = bot.send_message(chat_id, "⏳ در حال دانلود...")
                    
                    files, caption = download_instagram_post(text)
                    
                    if files is None:
                        bot.edit_message_text(f"❌ {caption}", chat_id=chat_id, message_id=msg.message_id)
                        return 'OK', 200
                    
                    for i, f in enumerate(files):
                        try:
                            if os.path.exists(f):
                                if f.endswith(('.mp4', '.MP4')):
                                    with open(f, 'rb') as video:
                                        bot.send_video(chat_id, video, caption=caption if i == 0 else None)
                                else:
                                    with open(f, 'rb') as photo:
                                        bot.send_photo(chat_id, photo, caption=caption if i == 0 else None)
                                os.remove(f)
                        except Exception as e:
                            bot.send_message(chat_id, f"خطا در ارسال: {e}")
                    
                    bot.edit_message_text("✅ دانلود و ارسال کامل شد!", chat_id=chat_id, message_id=msg.message_id)
                else:
                    bot.send_message(chat_id, "لطفاً لینک اینستاگرام بفرست.")
            
            return 'OK', 200
        else:
            return 'Unsupported', 400
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return 'Error', 500

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    webhook_url = 'https://telegram-bot-tkaz.onrender.com/'
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=webhook_url)
    return 'Webhook set!', 200

@app.route('/', methods=['GET'])
def home():
    return 'Bot is running!', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
