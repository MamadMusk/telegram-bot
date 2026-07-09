from flask import Flask, request
import telebot
import os
import re
import logging
import time
from parth_dl import InstagramDownloader

TOKEN = "8837695158:AAETrphGJh6wS1bmCXHOFB7-r4YPx0n8KR8"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

logging.basicConfig(level=logging.INFO)

def download_instagram_post(url):
    """
    دانلود هر نوع پست اینستاگرام با parth-dl
    برمی‌گرداند: (list_of_files, caption) یا (None, error_message)
    """
    try:
        logging.info(f"Starting download with parth-dl for: {url}")
        
        # ایجاد شیء دانلودر
        dl = InstagramDownloader(verbose=False)
        
        # دانلود مستقیم
        result = dl.download(url, output_dir=DOWNLOAD_DIR)
        
        if not result:
            return None, "هیچ محتوایی برای دانلود پیدا نشد."
        
        # result می‌تونه یک فایل یا لیستی از فایل‌ها باشه
        files = []
        caption = ""
        
        if isinstance(result, list):
            files = result
        else:
            files = [result]
        
        # فقط فایل‌های موجود رو نگه دار
        existing_files = [f for f in files if os.path.exists(f)]
        
        if not existing_files:
            return None, "فایلی دانلود نشد."
        
        logging.info(f"Successfully downloaded {len(existing_files)} files")
        return existing_files, caption
        
    except Exception as e:
        logging.error(f"parth-dl failed: {e}")
        return None, f"خطا در دانلود: {str(e)}"

@app.route('/', methods=['POST'])
def webhook():
    try:
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            logging.info("Webhook received")
            update = telebot.types.Update.de_json(json_string)
            
            if update.message:
                chat_id = update.message.chat.id
                text = update.message.text
                logging.info(f"Message from {chat_id}: {text}")
                
                if text and text.startswith('/start'):
                    bot.send_message(chat_id, "سلام! به ربات دانلود اینستاگرام خوش آمدید.\nلینک پست رو بفرست.")
                    return 'OK', 200
                
                if text and ('instagram.com' in text or 'instagr.am' in text):
                    msg = bot.send_message(chat_id, "⏳ در حال دانلود...")
                    
                    files, caption = download_instagram_post(text)
                    
                    if files is None:
                        bot.edit_message_text(f"❌ خطا: {caption}", chat_id=chat_id, message_id=msg.message_id)
                        return 'OK', 200
                    
                    for i, f in enumerate(files):
                        try:
                            if os.path.exists(f):
                                if f.endswith('.mp4') or f.endswith('.MP4'):
                                    with open(f, 'rb') as video:
                                        bot.send_video(chat_id, video, caption=caption if i == 0 else None)
                                else:
                                    with open(f, 'rb') as photo:
                                        bot.send_photo(chat_id, photo, caption=caption if i == 0 else None)
                                os.remove(f)
                                logging.info(f"Sent and removed: {f}")
                        except Exception as e:
                            logging.error(f"Error sending file {f}: {e}")
                            bot.send_message(chat_id, f"خطا در ارسال فایل: {e}")
                    
                    bot.edit_message_text("✅ دانلود و ارسال کامل شد!", chat_id=chat_id, message_id=msg.message_id)
                else:
                    bot.send_message(chat_id, "❌ لطفاً یک لینک معتبر اینستاگرام بفرست.")
            
            return 'OK', 200
        else:
            return 'Unsupported content type', 400
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return 'Error', 500

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    try:
        webhook_url = 'https://telegram-bot-tkaz.onrender.com/'
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=webhook_url)
        return 'Webhook set successfully!', 200
    except Exception as e:
        return f'Error setting webhook: {e}', 500

@app.route('/', methods=['GET'])
def home():
    return 'Bot is running!', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
