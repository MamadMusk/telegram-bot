from flask import Flask, request
import telebot
import os
import re
import instaloader
import logging
import time
import http.cookiejar as cookielib

TOKEN = "8837695158:AAETrphGJh6wS1bmCXHOFB7-r4YPx0n8KR8"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

logging.basicConfig(level=logging.INFO)

def download_instagram_post(url):
    files = []
    caption = ""
    
    # استخراج shortcode
    shortcode_match = re.search(r'/(?:p|reel|tv|stories)/([^/?]+)', url)
    if not shortcode_match:
        return None, "لینک معتبر اینستاگرام نیست."
    shortcode = shortcode_match.group(1)
    logging.info(f"Shortcode: {shortcode}")
    
    try:
        # ایجاد شیء instaloader
        loader = instaloader.Instaloader(
            download_pictures=True,
            download_videos=True,
            download_video_thumbnails=False,
            compress_json=False,
            save_metadata=False,
            post_metadata_txt_pattern='',
            max_connection_attempts=3
        )
        
        # بارگذاری کوکی (با روش استاندارد)
        if os.path.exists("cookies.txt"):
            cookie_jar = cookielib.MozillaCookieJar()
            cookie_jar.load("cookies.txt", ignore_expires=True, ignore_discard=True)
            loader.context._session.cookies.update(cookie_jar)
            logging.info("✅ Cookies loaded successfully")
        else:
            logging.warning("⚠️ cookies.txt not found! Trying without...")
        
        # دریافت و دانلود پست
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        loader.download_post(post, target=shortcode)
        
        # پیدا کردن فایل‌های دانلود شده
        for file in os.listdir('.'):
            if file.startswith(shortcode) and (file.endswith('.jpg') or file.endswith('.png') or file.endswith('.mp4')):
                files.append(os.path.join('.', file))
        
        caption = post.caption if post.caption else ""
        
        if files:
            logging.info(f"✅ Downloaded {len(files)} files")
            return files, caption
        else:
            return None, "هیچ فایلی دانلود نشد."
            
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
                logging.info(f"Message from {chat_id}: {text}")
                
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
                                if f.endswith('.mp4'):
                                    with open(f, 'rb') as video:
                                        bot.send_video(chat_id, video, caption=caption if i == 0 else None)
                                else:
                                    with open(f, 'rb') as photo:
                                        bot.send_photo(chat_id, photo, caption=caption if i == 0 else None)
                                os.remove(f)
                        except Exception as e:
                            bot.send_message(chat_id, f"خطا در ارسال: {e}")
                    
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
