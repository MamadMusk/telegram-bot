from flask import Flask, request
import telebot
import os
import logging

from config import TOKEN
from handlers import handle_message, handle_callback_query
from database import init_db

# ===== ۱. اول دیتابیس =====
init_db()

# ===== ۲. بعد Flask app =====
app = Flask(__name__)

# ===== ۳. بعد بات =====
bot = telebot.TeleBot(TOKEN)

logging.basicConfig(level=logging.INFO)

user_data = {}
user_last_download = {}

@app.route('/', methods=['POST'])
def webhook():
    try:
        json_string = request.get_data().decode('utf-8')
        logging.info("📩 Webhook received")
        update = telebot.types.Update.de_json(json_string)
        if update.callback_query:
            handle_callback_query(bot, update.callback_query, user_data)
        elif update.message:
            handle_message(bot, update.message, user_data, user_last_download)
        return 'OK', 200
    except Exception as e:
        logging.error(f"❌ Webhook error: {e}")
        return 'Error', 500

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    webhook_url = 'https://telegram-bot-tkaz.onrender.com/'
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    return 'Webhook set!', 200

@app.route('/', methods=['GET'])
def home():
    return 'ربات در حال کار است!', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
