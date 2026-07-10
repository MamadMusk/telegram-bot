from flask import Flask, request
import telebot
import os
import logging

TOKEN = "8837695158:AAHmNAVxZU98wDXpIFC7_0CjOYh0B4nbbjk"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

@app.route('/', methods=['POST'])
def webhook():
    try:
        json_string = request.get_data().decode('utf-8')
        logging.info("📩 Webhook received")
        
        update = telebot.types.Update.de_json(json_string)
        
        # ===== پردازش دستی پیام =====
        if update.message:
            chat_id = update.message.chat.id
            text = update.message.text
            logging.info(f"📨 Message from {chat_id}: {text}")
            
            # پاسخ به پیام
            bot.send_message(chat_id, f"سلام! پیامت رو دریافت کردم: {text}")
        
        return 'OK', 200
    except Exception as e:
        logging.error(f"❌ Webhook error: {e}")
        return 'Error', 500

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    try:
        webhook_url = 'https://telegram-bot-tkaz.onrender.com/'
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        return 'Webhook set!', 200
    except Exception as e:
        logging.error(f"❌ Setwebhook error: {e}")
        return f'Error: {e}', 500

@app.route('/', methods=['GET'])
def home():
    return 'Bot is running!', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
