from flask import Flask, request
import telebot
import os

TOKEN = "8837695158:AAETrphGJh6wS1bmCXHOFB7-r4YPx0n8KR8"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ========== هندلر دستور start ==========
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "سلام! ربات روشنه! 🎉")

# ========== هندلر همه پیام‌ها ==========
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    bot.send_message(message.chat.id, f"شما گفتید: {message.text}")

# ========== Webhook ==========
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

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    bot.remove_webhook()
    webhook_url = "https://telegram-bot-tkaz.onrender.com/"
    bot.set_webhook(url=webhook_url)
    return f"Webhook set to {webhook_url}", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
