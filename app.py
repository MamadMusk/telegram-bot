from flask import Flask, request
import telebot
import os
import logging

TOKEN = "8837695158:AAHmNAVxZU98wDXpIFC7_0CjOYh0B4nbbjk"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# ===== هندلر ساده برای /start =====
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "✅ ربات فعال است! Webhook درست کار می‌کند.")

# ===== هندلر برای همه پیام‌ها =====
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    bot.reply_to(message, f"📩 پیام شما دریافت شد: {message.text}")

@app.route('/', methods=['POST'])
def webhook():
    try:
        json_string = request.get_data().decode('utf-8')
        logging.info(f"📩 Webhook received: {json_string[:100]}...")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return 'Error', 500

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    try:
        webhook_url = 'https://telegram-bot-tkaz.onrender.com/'
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        return 'Webhook set!', 200
    except Exception as e:
        return f'Error: {e}', 500

@app.route('/', methods=['GET'])
def home():
    return 'Bot is running!', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
