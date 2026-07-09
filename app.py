from flask import Flask, request
import telebot
import os
import json

TOKEN = "8837695158:AAETrphGJh6wS1bmCXHOFB7-r4YPx0n8KR8"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    try:
        # دریافت داده‌های JSON از تلگرام
        json_str = request.stream.read().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        
        # پردازش دستی پیام (بدون هندلر!)
        if update.message:
            chat_id = update.message.chat.id
            text = update.message.text or ""
            
            # پاسخ به دستور /start
            if text == "/start":
                bot.send_message(chat_id, "سلام! ربات روشنه! 🎉")
            else:
                bot.send_message(chat_id, f"شما گفتید: {text}")
        
        return 'ok', 200
    except Exception as e:
        print(f"خطا: {e}")
        return 'error', 500

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    bot.remove_webhook()
    webhook_url = "https://telegram-bot-tkaz.onrender.com/"
    bot.set_webhook(url=webhook_url)
    return f"Webhook set to {webhook_url}", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
