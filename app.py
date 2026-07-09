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
    دانلود با yt-dlp - هم عکس و هم فیلم و پست‌های چندتایی
    """
    try:
        logging.info(f"Downloading: {url}")
        
        # تنظیمات yt-dlp
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': False,
            'cookiefile': 'cookies.txt',  # اگر کوکی نداری، این خط رو پاک کن
            'format': 'best',  # بهترین کیفیت (چه عکس چه فیلم)
            'ignoreerrors': True,
            'extract_flat': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            files = []
            caption = ""
            
            if info:
                # پست چندتایی (entries)
                if 'entries' in info and info['entries']:
                    for entry in info['entries']:
                        if entry:
                            filename = ydl.prepare_filename(entry)
                            if os.path.exists(filename):
                                files.append(filename)
                    # برای carousel، کپشن رو از entry اول می‌گیریم
                    if info['entries'] and info['entries'][0]:
                        caption = info['entries'][0].get('description', '')
                else:
                    # پست تکی
                    filename = ydl.prepare_filename(info)
                    if os.path.exists(filename):
                        files.append(filename)
                    caption = info.get('description', '')
            
            # اگه هیچ فایلی دانلود نشد، پیام خطا
            if not files:
                return None, "هیچ محتوایی برای دانلود پیدا نشد (ممکنه پست خصوصی یا حذف شده باشه)."
            
            logging.info(f"✅ Downloaded {len(files)} files")
            return files, caption
            
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
                    
                    # ارسال فایل‌ها
                    for i, f in enumerate(files):
                        try:
                            if os.path.exists(f):
                                # تشخیص نوع فایل
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
