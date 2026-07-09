from flask import Flask, request
import telebot
import os
import json
from downloader import download_instagram_post

TOKEN = "8837695158:AAETrphGJh6wS1bmCXHOFB7-r4YPx0n8KR8"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    try:
        json_str = request.stream.read().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return 'ok', 200
    except Exception as e:
        print(f"خطا: {e}")
        return 'error', 500

# ========== هندلر دستور start ==========
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(
        message.chat.id,
        "👋 سلام! به ربات دانلود اینستاگرام خوش آمدید!\n\n"
        "📌 لینک پست اینستاگرام را ارسال کنید تا عکس یا ویدیو را دانلود کنم.\n"
        "✅ پشتیبانی از: عکس، ویدیو، رییل، پست‌های چندتایی"
    )

# ========== هندلر لینک اینستاگرام ==========
@bot.message_handler(func=lambda message: "instagram.com" in message.text)
def handle_instagram_link(message):
    url = message.text.strip()
    
    # پیام در حال دانلود
    status_msg = bot.send_message(message.chat.id, "⏳ در حال دانلود... لطفاً صبر کنید.")
    
    try:
        files, caption = download_instagram_post(url)
        
        if files:
            bot.delete_message(message.chat.id, status_msg.message_id)
            
            # ارسال همه فایل‌ها
            for idx, file_path in enumerate(files):
                with open(file_path, 'rb') as f:
                    # کپشن فقط برای فایل اول
                    cap = caption if idx == 0 else None
                    if file_path.endswith(".mp4"):
                        bot.send_video(message.chat.id, f, caption=cap[:1024])
                    else:
                        bot.send_photo(message.chat.id, f, caption=cap[:1024])
                os.remove(file_path)
        else:
            bot.edit_message_text(
                caption or "❌ خطا در دانلود",
                message.chat.id,
                status_msg.message_id
            )
    except Exception as e:
        bot.edit_message_text(
            f"❌ خطا: {str(e)}",
            message.chat.id,
            status_msg.message_id
        )

# ========== هندلر پیام‌های دیگر ==========
@bot.message_handler(func=lambda message: True)
def handle_other(message):
    bot.send_message(
        message.chat.id,
        "❗ لطفاً یک لینک معتبر از اینستاگرام ارسال کنید.\n"
        "مثال: https://www.instagram.com/p/CxYz123AbC/"
    )

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    bot.remove_webhook()
    webhook_url = "https://telegram-bot-tkaz.onrender.com/"
    bot.set_webhook(url=webhook_url)
    return f"Webhook set to {webhook_url}", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
