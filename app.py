from flask import Flask, request
import telebot
import os
import requests

TOKEN = "8837695158:AAETrphGJh6wS1bmCXHOFB7-r4YPx0n8KR8"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ========== آدرس صحیح رندر ==========
BASE_URL = "https://telegram-bot-tkaz.onrender.com"

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
    # حذف Webhook قدیمی
    bot.remove_webhook()
    
    # تنظیم Webhook با آدرس درست
    webhook_url = BASE_URL + "/"
    bot.set_webhook(url=webhook_url)
    
    # تایید نهایی با فراخوانی مستقیم API
    api_url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
    response = requests.get(api_url)
    current_webhook = response.json()
    
    return f"Webhook set successfully to {webhook_url}\n\nCurrent webhook info: {current_webhook}", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
