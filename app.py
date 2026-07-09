from flask import Flask, request
import telebot
import os
import re
import instaloader
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
    دانلود هر نوع پست اینستاگرام (عکس، فیلم، ریل، پست چندتایی)
    برمی‌گرداند: (list_of_files, caption) یا (None, error_message)
    """
    files = []
    caption = ""
    
    # استخراج shortcode
    shortcode_match = re.search(r'/(?:p|reel|tv|stories)/([^/?]+)', url)
    if not shortcode_match:
        return None, "لینک معتبر اینستاگرام نیست."
    shortcode = shortcode_match.group(1)
    logging.info(f"Shortcode: {shortcode}")
    
    # ===== روش اول: instaloader (برای همه نوع پست) =====
    try:
        logging.info("Trying instaloader...")
        loader = instaloader.Instaloader(
            download_pictures=True,
            download_videos=True,
            download_video_thumbnails=False,
            compress_json=False,
            save_metadata=False,
            post_metadata_txt_pattern='',
            max_connection_attempts=3
        )
        
        # بارگذاری کوکی
        if os.path.exists("cookies.txt"):
            loader.load_cookies_from_txt("cookies.txt")
            logging.info("Cookies loaded successfully")
        else:
            logging.warning("cookies.txt not found!")
        
        # دریافت پست
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        logging.info(f"Post type: {post.typename}")
        
        # دانلود پست
        loader.download_post(post, target=shortcode)
        
        # پیدا کردن فایل‌های دانلود شده
        for file in os.listdir('.'):
            if file.startswith(shortcode) and (file.endswith('.jpg') or file.endswith('.png') or file.endswith('.mp4') or file.endswith('.jpeg')):
                files.append(os.path.join('.', file))
        
        caption = post.caption if post.caption else ""
        logging.info(f"Downloaded {len(files)} files with instaloader")
        
        if files:
            return files, caption
        else:
            logging.warning("No files found from instaloader")
            
    except Exception as e:
        logging.error(f"instaloader failed: {e}")
    
    # ===== روش دوم: yt-dlp (روش جایگزین برای فیلم‌ها) =====
    try:
        logging.info("Trying yt-dlp as fallback...")
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'cookiefile': 'cookies.txt' if os.path.exists("cookies.txt") else None,
            'format': 'best[ext=mp4]/best',
            'ignoreerrors': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
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
            logging.info(f"Downloaded {len(files)} files with yt-dlp")
            return files, caption
        else:
            return None, "با هیچ روشی محتوا دانلود نشد."
            
    except Exception as e:
        logging.error(f"yt-dlp failed: {e}")
        return None, f"دانلود با مشکل مواجه شد: {str(e)}"

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
                
                # پردازش لینک
                if text and ('instagram.com' in text or 'instagr.am' in text):
                    msg = bot.send_message(chat_id, "⏳ در حال دانلود...")
                    
                    files, caption = download_instagram_post(text)
                    
                    if files is None:
                        bot.edit_message_text(f"❌ خطا: {caption}", chat_id=chat_id, message_id=msg.message_id)
                        return 'OK', 200
                    
                    # ارسال فایل‌ها
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
