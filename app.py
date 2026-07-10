from flask import Flask, request
import telebot
import os
import yt_dlp
import logging
import time
import re
import requests
from messages import MESSAGES, get_main_keyboard, COMMANDS

TOKEN = "8837695158:AAETrphGJh6wS1bmCXHOFB7-r4YPx0n8KR8"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

logging.basicConfig(level=logging.INFO)

# ===== تنظیم کامندها در منوی ربات =====
try:
    bot.set_my_commands(COMMANDS)
    logging.info("✅ کامندها تنظیم شد")
except Exception as e:
    logging.error(f"خطا در تنظیم کامندها: {e}")

def download_image_direct(shortcode):
    try:
        embed_url = f"https://www.instagram.com/p/{shortcode}/embed/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(embed_url, headers=headers, timeout=15)
        if response.status_code == 200:
            match = re.search(r'<img[^>]+src="([^"]+)"', response.text)
            if match:
                img_url = match.group(1)
                if 'cdninstagram.com' in img_url:
                    img_response = requests.get(img_url, headers=headers, timeout=15)
                    if img_response.status_code == 200:
                        filename = os.path.join(DOWNLOAD_DIR, f"{shortcode}.jpg")
                        with open(filename, 'wb') as f:
                            f.write(img_response.content)
                        return filename
        return None
    except Exception as e:
        logging.error(f"Direct image error: {e}")
        return None

def download_instagram_post(url):
    try:
        shortcode_match = re.search(r'/(?:p|reel|tv)/([^/?]+)', url)
        if not shortcode_match:
            return None, "لینک معتبر نیست"
        shortcode = shortcode_match.group(1)
        logging.info(f"Shortcode: {shortcode}")

        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': False,
            'format': 'best[ext=mp4]/best',
            'ignoreerrors': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                files = []
                
                if info:
                    if 'entries' in info and info['entries']:
                        for entry in info['entries']:
                            if entry:
                                fname = ydl.prepare_filename(entry)
                                if os.path.exists(fname):
                                    files.append(fname)
                    else:
                        fname = ydl.prepare_filename(info)
                        if os.path.exists(fname):
                            files.append(fname)
                
                if files:
                    logging.info(f"✅ yt-dlp: {len(files)} فایل دانلود شد")
                    return files, None
        except Exception as e:
            logging.warning(f"yt-dlp failed: {e}")

        logging.info("Trying direct image download...")
        img_file = download_image_direct(shortcode)
        if img_file:
            return [img_file], None

        return None, MESSAGES["download_failed"]

    except Exception as e:
        logging.error(f"Error: {e}")
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
                logging.info(f"Message: {text}")
                
                # ===== بررسی دستورات =====
                if text.startswith('/start'):
                    keyboard = get_main_keyboard(is_admin=False)  # آیدی ادمین رو چک کن
                    bot.send_message(chat_id, MESSAGES["start"], reply_markup=keyboard)
                    return 'OK', 200
                
                if text.startswith('/help'):
                    bot.send_message(chat_id, MESSAGES["help"])
                    return 'OK', 200
                
                if text.startswith('/status'):
                    bot.send_message(chat_id, MESSAGES["status"])
                    return 'OK', 200
                
                # ===== پردازش لینک =====
                if 'instagram.com' in text:
                    msg = bot.send_message(chat_id, MESSAGES["downloading"])
                    files, error = download_instagram_post(text)
                    
                    if not files:
                        bot.edit_message_text(f"❌ {error}", chat_id, msg.message_id)
                        return 'OK', 200
                    
                    for f in files:
                        try:
                            with open(f, 'rb') as media:
                                if f.endswith('.mp4'):
                                    bot.send_video(chat_id, media, caption=MESSAGES["caption"])
                                else:
                                    bot.send_photo(chat_id, media, caption=MESSAGES["caption"])
                            os.remove(f)
                        except Exception as e:
                            logging.error(f"خطا در ارسال: {e}")
                            bot.send_message(chat_id, MESSAGES["send_error"].format(error=str(e)))
                else:
                    # ===== دکمه‌های شیشه‌ای =====
                    if text == MESSAGES["help"]:
                        bot.send_message(chat_id, "ℹ️ راهنمای ربات:\nلینک اینستاگرام رو بفرست تا دانلود کنم.")
                    elif text == MESSAGES["status"]:
                        bot.send_message(chat_id, "📊 ربات فعال است!")
                    elif text == MESSAGES["admin_panel"]:
                        bot.send_message(chat_id, "🛠 پنل مدیریت")
                    else:
                        bot.send_message(chat_id, MESSAGES["invalid_link"])
            
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
    return 'ربات در حال کار است!', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
