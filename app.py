from flask import Flask, request
import telebot
import os

TOKEN = "8837695158:AAETrphGJh6wS1bmCXHOFB7-r4YPx0n8KR8"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! ربات روشنه! 🎉")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"شما گفتید: {message.text}")

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
