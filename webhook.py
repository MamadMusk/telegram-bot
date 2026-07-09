from flask import Flask, request
import telebot
import os
import re
import requests

TOKEN = "8837695158:AAETrphGJh6wS1bmCXHOFB7-r4YPx0n8KR8"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ========== تابع دانلود عکس از اینستاگرام ==========
def download_instagram_photo(shortcode):
    download_dir = "downloads"
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    url = f"https://www.instagram.com/p/{shortcode}/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        html = response.text
        caption = "بدون کپشن"
        caption_match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
        if caption_match:
            caption = caption_match.group(1)
        image_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
        if not image_match:
            return None, "عکس پیدا نشد"
        image_url = image_match.group(1)
        image_url = re.sub(r'\?.*$', '', image_url)
        img_response = requests.get(image_url, headers=headers, stream=True, timeout=15)
        filename = f"{shortcode}.jpg"
        filepath = os.path.join(download_dir, filename)
        with open(filepath, 'wb') as f:
            for chunk in img_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return [filepath], caption
    except Exception as e:
        return None, f"خطا: {str(e)}"

# ========== هندلرهای ربات ==========
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! لینک اینستاگرام را ارسال کنید.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    if not url or "instagram.com" not in url:
        bot.reply_to(message, "لطفاً لینک اینستاگرام ارسال کنید.")
        return
    match = re.search(r"/(?:p|reel|tv)/([^/?]+)", url)
    if not match:
        bot.reply_to(message, "لینک نامعتبر.")
        return
    shortcode = match.group(1)
    bot.reply_to(message, "در حال دانلود...")
    files, caption = download_instagram_photo(shortcode)
    if files:
        for file_path in files:
            with open(file_path, 'rb') as f:
                bot.send_photo(message.chat.id, f, caption=caption[:1024])
            os.remove(file_path)
    else:
        bot.reply_to(message, caption)

# ========== Webhook ==========
@app.route('/', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return 'ok', 200

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url="https://telegram-bot.onrender.com/")
    return "Webhook set successfully!", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
