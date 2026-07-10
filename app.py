from flask import Flask, request
import telebot
import os
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

# ===== راه‌اندازی دانلودر =====
# verbose=True یعنی اگر خطایی بود، بهت تو لاگ نشون بده
downloader = InstagramDownloader(verbose=True)

def download_instagram_post(url):
    """
    دانلود هر نوع محتوایی از اینستاگرام با parth-dl
    """
    try:
        logging.info(f"شروع دانلود: {url}")
        
        # متد download لیستی از مسیر فایل‌های دانلود شده رو برمی‌گردونه
        downloaded_files = downloader.download(url, output_dir=DOWNLOAD_DIR)
        
        if not downloaded_files:
            return None, "هیچ چیزی دانلود نشد. مطمئن شو لینک درسته و پست عمومی هست."
        
        # اگه فقط یه فایل باشه، تبدیلش به لیست می‌کنیم
        if isinstance(downloaded_files, str):
            downloaded_files = [downloaded_files]
            
        logging.info(f"{len(downloaded_files)} فایل با موفقیت دانلود شد.")
        
        # متاسفانه parth-dl کپشن رو برنمی‌گردونه، پس خالی می‌فرستیم
        return downloaded_files, ""
        
    except Exception as e:
        logging.error(f"خطا در دانلود: {e}")
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
                logging.info(f"پیام جدید: {text}")
                
                if text.startswith('/start'):
                    bot.send_message(chat_id, "سلام! لینک پست، ریل یا پروفایل اینستاگرام رو بفرست.")
                    return 'OK', 200
                
                if 'instagram.com' in text:
                    msg = bot.send_message(chat_id, "⏳ دارم دانلود میکنم...")
                    
                    files, caption = download_instagram_post(text)
                    
                    if files is None:
                        bot.edit_message_text(f"❌ {caption}", chat_id, msg.message_id)
                        return 'OK', 200
                    
                    # ارسال فایل‌ها به کاربر
                    for i, f in enumerate(files):
                        try:
                            if os.path.exists(f):
                                with open(f, 'rb') as media:
                                    if f.lower().endswith(('.mp4', '.mov', '.avi')):
                                        bot.send_video(chat_id, media, caption=caption if i == 0 else None)
                                    else:
                                        bot.send_photo(chat_id, media, caption=caption if i == 0 else None)
                                os.remove(f)  # پاک کردن فایل بعد از ارسال
                                logging.info(f"فایل ارسال و پاک شد: {f}")
                        except Exception as e:
                            logging.error(f"خطا در ارسال فایل {f}: {e}")
                            bot.send_message(chat_id, f"خطا در ارسال یکی از فایل‌ها: {e}")
                    
                    bot.edit_message_text("✅ دانلود و ارسال با موفقیت انجام شد!", chat_id, msg.message_id)
                else:
                    bot.send_message(chat_id, "❌ لطفاً یه لینک معتبر اینستاگرام بفرست.")
            
            return 'OK', 200
    except Exception as e:
        logging.error(f"خطا در Webhook: {e}")
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
    return 'ربات در حال کار است!', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
