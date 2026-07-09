from flask import Flask, request
import telebot
import os
import re
import instaloader
import yt_dlp
import time
import logging

TOKEN = "8837695158:AAETrphGJh6wS1bmCXHOFB7-r4YPx0n8KR8"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def download_instagram_post(url):
    files = []
    caption = ""
    
    shortcode_match = re.search(r'/(?:p|reel|tv|stories)/([^/?]+)', url)
    if not shortcode_match:
        return None, "لینک معتبر اینستاگرام نیست."
    shortcode = shortcode_match.group(1)
    
    # yt-dlp
    try:
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'cookiefile': 'cookies.txt',
            'format': 'best',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info and 'entries' in info:
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
            return files, caption
    except Exception as e:
        logging.error(f"yt-dlp failed: {e}")
    
    # instaloader
    try:
        loader = instaloader.Instaloader(
            download_pictures=True,
            download_videos=True,
            download_video_thumbnails=False,
            compress_json=False,
            save_metadata=False,
            post_metadata_txt_pattern='',
            max_connection_attempts=3
        )
        loader.load_cookies_from_txt("cookies.txt")
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        loader.download_post(post, target=shortcode)
        
        for file in os.listdir('.'):
            if file.startswith(shortcode) and (file.endswith('.jpg') or file.endswith('.png') or file.endswith('.mp4')):
                files.append(os.path.join('.', file))
        caption = post.caption if post.caption else ""
        
        if files:
            return files, caption
        else:
            return None, "هیچ فایلی دانلود نشد."
    except Exception as e:
        logging.error(f"instaloader failed: {e}")
        return None, f"دانلود با مشکل مواجه شد: {str(e)}"

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "سلام! به ربات دانلود اینستاگرام خوش آمدید.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    if not url.startswith('https://www.instagram.com/') and not url.startswith('https://instagram.com/'):
        bot.reply_to(message, "لطفاً یک لینک معتبر اینستاگرام بفرست.")
        return
    
    msg = bot.reply_to(message, "⏳ در حال دانلود...")
    
    files, caption = download_instagram_post(url)
    if files is None:
        bot.edit_message_text(f"❌ خطا: {caption}", chat_id=message.chat.id, message_id=msg.message_id)
        return
    
    for f in files:
        try:
            if f.endswith('.mp4'):
                with open(f, 'rb') as video:
                    bot.send_video(message.chat.id, video, caption=caption if len(files) == 1 else None)
            else:
                with open(f, 'rb') as photo:
                    bot.send_photo(message.chat.id, photo, caption=caption if len(files) == 1 else None)
            os.remove(f)
        except Exception as e:
            bot.send_message(message.chat.id, f"خطا در ارسال فایل: {e}")
    
    bot.edit_message_text("✅ دانلود و ارسال کامل شد!", chat_id=message.chat.id, message_id=msg.message_id)

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    else:
        return 'Unsupported content type', 400

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    webhook_url = 'https://telegram-bot-tkaz.onrender.com/'
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    return 'Webhook set!', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
