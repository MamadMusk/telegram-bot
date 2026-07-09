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

# ========== تنظیم لاگ برای دیباگ ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== پوشه دانلود ==========
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# ========== تابع دانلود از اینستاگرام با instaloader (برای عکس و ویدیو) ==========
def download_instagram_post(url):
    """دانلود عکس و ویدیو از اینستاگرام با instaloader"""
    # پاک کردن فایل‌های قبلی
    for f in os.listdir(DOWNLOAD_DIR):
        os.remove(os.path.join(DOWNLOAD_DIR, f))

    # استخراج shortcode
    match = re.search(r"/(?:p|reel|tv)/([^/?]+)", url)
    if not match:
        return None, "❌ لینک اینستاگرام معتبر نیست."
    shortcode = match.group(1)

    try:
        loader = instaloader.Instaloader(
            download_pictures=True,
            download_videos=True,
            save_metadata=False,
            post_metadata_txt_pattern="",
            filename_pattern="{shortcode}",
            quiet=True,
        )

        # ========== بارگذاری کوکی (برای دسترسی به پست‌های عمومی) ==========
        cookies_path = os.path.join(os.getcwd(), "cookies.txt")
        if os.path.exists(cookies_path):
            try:
                loader.load_session_from_file(cookies_path)
                logger.info("✅ کوکی با موفقیت بارگذاری شد")
            except Exception as e:
                logger.warning(f"⚠️ بارگذاری کوکی ناموفق: {e}")
        else:
            logger.warning("⚠️ فایل cookies.txt پیدا نشد. فقط پست‌های عمومی قابل دانلود هستند.")

        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        caption = post.caption if post.caption else "بدون کپشن"

        loader.download_post(post, target=DOWNLOAD_DIR)
        time.sleep(1)

        files = os.listdir(DOWNLOAD_DIR)
        media_files = []
        for f in sorted(files):
            if f.endswith((".mp4", ".jpg", ".png", ".jpeg")):
                media_files.append(os.path.join(DOWNLOAD_DIR, f))

        if not media_files:
            return None, "❌ هیچ فایلی در این پست پیدا نشد."

        return media_files, caption

    except Exception as e:
        logger.error(f"خطا در دانلود: {e}")
        return None, f"❌ خطا: {str(e)}"

# ========== تابع جایگزین با yt-dlp (برای مواقعی که instaloader جواب نده) ==========
def download_instagram_with_ytdlp(url):
    """دانلود با yt-dlp (برای پست‌هایی که instaloader نمی‌تونه دانلود کنه)"""
    # پاک کردن فایل‌های قبلی
    for f in os.listdir(DOWNLOAD_DIR):
        os.remove(os.path.join(DOWNLOAD_DIR, f))

    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'format': 'best[ext=mp4]/best[ext=jpg]/best',
        'ignoreerrors': True,
        'cookiefile': os.path.join(os.getcwd(), "cookies.txt") if os.path.exists(os.path.join(os.getcwd(), "cookies.txt")) else None,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                return None, "❌ لینک معتبر نیست یا محتوایی یافت نشد."

            caption = info.get('description', 'بدون کپشن')
            if caption is None:
                caption = 'بدون کپشن'

            files = os.listdir(DOWNLOAD_DIR)
            media_files = []
            for f in sorted(files):
                if f.endswith((".mp4", ".jpg", ".png", ".jpeg")):
                    media_files.append(os.path.join(DOWNLOAD_DIR, f))

            if not media_files:
                return None, "❌ هیچ فایلی دانلود نشد."

            return media_files, caption

    except Exception as e:
        logger.error(f"خطا در yt-dlp: {e}")
        return None, f"❌ خطا: {str(e)}"

# ========== هندلر دستور start ==========
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "👋 سلام! به ربات دانلود اینستاگرام خوش آمدید.\n\n📌 لینک پست اینستاگرام را ارسال کنید تا عکس یا ویدیو را دانلود کنم.")

# ========== هندلر پیام‌ها (پردازش لینک) ==========
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    chat_id = message.chat.id

    if not url or "instagram.com" not in url:
        bot.send_message(chat_id, "❌ لطفاً یک لینک معتبر از اینستاگرام ارسال کنید.")
        return

    bot.send_message(chat_id, "⏳ در حال دانلود... لطفاً صبر کنید.")

    # ========== تلاش با instaloader ==========
    files, caption = download_instagram_post(url)

    # ========== اگر instaloader جواب نداد، با yt-dlp امتحان کن ==========
    if not files:
        logger.info("instaloader جواب نداد، تلاش با yt-dlp...")
        files, caption = download_instagram_with_ytdlp(url)

    # ========== ارسال فایل به کاربر ==========
    if files:
        for file_path in files:
            try:
                with open(file_path, 'rb') as f:
                    if file_path.endswith(".mp4"):
                        bot.send_video(chat_id, f, caption=caption[:1024])
                    else:
                        bot.send_photo(chat_id, f, caption=caption[:1024])
                os.remove(file_path)
            except Exception as e:
                logger.error(f"خطا در ارسال فایل: {e}")
                bot.send_message(chat_id, f"❌ خطا در ارسال فایل: {str(e)}")
    else:
        bot.send_message(chat_id, caption)

# ========== Webhook ==========
@app.route('/', methods=['POST'])
def webhook():
    try:
        json_str = request.stream.read().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return 'ok', 200
    except Exception as e:
        logger.error(f"خطا در Webhook: {e}")
        return 'error', 500

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    bot.remove_webhook()
    webhook_url = "https://telegram-bot-tkaz.onrender.com/"
    bot.set_webhook(url=webhook_url)
    return f"Webhook set to {webhook_url}", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
