from flask import Flask, request
import telebot
import os
import re
import yt_dlp
import gallery_dl
import logging
import time
import json
from io import StringIO
import contextlib

TOKEN = "8837695158:AAETrphGJh6wS1bmCXHOFB7-r4YPx0n8KR8"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

logging.basicConfig(level=logging.INFO)

def download_with_gallery_dl(url, output_dir):
    """
    دانلود با gallery-dl و برگرداندن لیست فایل‌های دانلود شده
    """
    try:
        # تنظیمات gallery-dl برای خروجی
        config = {
            "extractor": {
                "instagram": {
                    "cookies": "cookies.txt" if os.path.exists("cookies.txt") else None,
                    "posts": "metadata",
                    "archive": None,
                }
            },
            "output": {
                "directory": [output_dir],
                "filename": "{shortcode}_{num}.{extension}"
            }
        }
        
        # اجرای gallery-dl و گرفتن خروجی
        f = StringIO()
        with contextlib.redirect_stderr(f), contextlib.redirect_stdout(f):
            gallery_dl.download([url], config, False)
        
        # پیدا کردن فایل‌های دانلود شده
        downloaded_files = []
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.endswith(('.jpg', '.jpeg', '.png', '.mp4', '.mov')):
                    downloaded_files.append(os.path.join(root, file))
        
        if downloaded_files:
            logging.info(f"✅ gallery-dl downloaded {len(downloaded_files)} files")
            return downloaded_files
        else:
            logging.warning("⚠️ gallery-dl didn't download any files")
            return None
            
    except Exception as e:
        logging.error(f"gallery-dl error: {e}")
        return None

def download_instagram_post(url):
    """
    دانلود با اولویت yt-dlp و fallback به gallery-dl
    """
    try:
        logging.info(f"Downloading: {url}")
        
        # ===== مرحله ۱: تلاش با yt-dlp =====
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': False,
            'cookiefile': 'cookies.txt' if os.path.exists("cookies.txt") else None,
            'format': 'best[ext=mp4]/best',  # اولویت با mp4
            'ignoreerrors': True,
            'extract_flat': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                files = []
                caption = ""
                
                if info:
                    if 'entries' in info and info['entries']:
                        for entry in info['entries']:
                            if entry:
                                filename = ydl.prepare_filename(entry)
                                if os.path.exists(filename):
                                    files.append(filename)
                        if info['entries'] and info['entries'][0]:
                            caption = info['entries'][0].get('description', '')
                    else:
                        filename = ydl.prepare_filename(info)
                        if os.path.exists(filename):
                            files.append(filename)
                        caption = info.get('description', '')
                
                if files:
                    logging.info(f"✅ yt-dlp downloaded {len(files)} files")
                    return files, caption
                    
        except Exception as e:
            logging.warning(f"yt-dlp failed: {e}")
        
        # ===== مرحله ۲: Fallback به gallery-dl =====
        logging.info("Trying gallery-dl as fallback...")
        files = download_with_gallery_dl(url, DOWNLOAD_DIR)
        
        if files:
            return files, ""
        else:
            return None, "هیچ محتوایی برای دانلود پیدا نشد (ممکنه پست خصوصی یا حذف شده باشه)."
            
    except Exception as e:
        logging.error(f"Download error: {e}")
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
                    
                    # ارسال فایل‌ها
                    for i, f in enumerate(files):
                        try:
                            if os.path.exists(f):
                                if f.lower().endswith(('.mp4', '.mov', '.avi')):
                                    with open(f, 'rb') as video:
                                        bot.send_video(chat_id, video, caption=caption if i == 0 else None)
                                else:
                                    with open(f, 'rb') as photo:
                                        bot.send_photo(chat_id, photo, caption=caption if i == 0 else None)
                                os.remove(f)
                                logging.info(f"Sent and removed: {f}")
                        except Exception as e:
                            logging.error(f"Error sending {f}: {e}")
                            bot.send_message(chat_id, f"خطا در ارسال فایل: {e}")
                    
                    bot.edit_message_text("✅ دانلود کامل شد!", chat_id=chat_id, message_id=msg.message_id)
                else:
                    bot.send_message(chat_id, "❌ لطفاً لینک اینستاگرام بفرست.")
            
            return 'OK', 200
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
