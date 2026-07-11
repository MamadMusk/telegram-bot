# ==========================================
# app.py - نقطه‌ی ورود ربات با Webhook
# ==========================================

import os
import logging
import traceback
from flask import Flask, request, jsonify
import telebot
from telebot.types import Update

from config import TOKEN
from handlers import handle_message, handle_callback_query
from database import init_db
from messages import COMMANDS

# ==========================================
# راه‌اندازی
# ==========================================

# تنظیم لاگینگ با فرمت مناسب
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# مقداردهی دیتابیس
init_db()

# ایجاد نمونه‌ی ربات
bot = telebot.TeleBot(TOKEN)

# ایجاد اپ Flask
app = Flask(__name__)

# دیکشنری برای داده‌های موقت کاربران (مراحل چندمرحله‌ای)
user_data = {}

# دیکشنری برای زمان آخرین دانلود (محدودیت زمانی)
user_last_download = {}

# ==========================================
# تنظیم کامندهای منوی ربات
# ==========================================
try:
    bot.set_my_commands(COMMANDS)
    logger.info("✅ کامندهای منو با موفقیت تنظیم شدند")
except Exception as e:
    logger.error(f"❌ خطا در تنظیم کامندهای منو: {e}")

# ==========================================
# مسیرهای Flask
# ==========================================

@app.route('/', methods=['POST'])
def webhook():
    """
    دریافت و پردازش تمام آپدیت‌های تلگرام (پیام‌ها و کلیک‌ها)
    """
    try:
        # دریافت داده‌های JSON
        json_string = request.get_data().decode('utf-8')
        logger.info("📩 Webhook received")
        
        # تبدیل به آبجکت Update
        update = Update.de_json(json_string)
        
        if update is None:
            logger.warning("⚠️ آپدیت خالی دریافت شد")
            return 'OK', 200
        
        # ===== پردازش Callback Query (کلیک روی دکمه) =====
        if update.callback_query:
            logger.info(f"📞 Callback from {update.callback_query.from_user.id}: {update.callback_query.data}")
            handle_callback_query(bot, update.callback_query, user_data)
        
        # ===== پردازش پیام =====
        elif update.message:
            logger.info(f"📨 Message from {update.message.from_user.id}: {update.message.text or '[non-text]'}")
            handle_message(bot, update.message, user_data, user_last_download)
        
        # ===== سایر انواع آپدیت (اختیاری) =====
        else:
            logger.info(f"ℹ️ نوع آپدیت دیگر: {update}")
        
        return 'OK', 200
    
    except Exception as e:
        # ثبت خطای کامل با traceback
        logger.error(f"❌ خطا در Webhook:\n{traceback.format_exc()}")
        return 'Error', 500

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    """
    تنظیم Webhook روی آدرس سرویس (فقط برای تست)
    """
    try:
        # آدرس Webhook - می‌توانید از متغیر محیطی استفاده کنید
        webhook_url = os.environ.get('WEBHOOK_URL', 'https://telegram-bot-tkaz.onrender.com/')
        
        # حذف Webhook قبلی
        bot.remove_webhook()
        
        # تنظیم Webhook جدید
        result = bot.set_webhook(url=webhook_url)
        
        if result:
            logger.info(f"✅ Webhook با موفقیت روی {webhook_url} تنظیم شد")
            return f'✅ Webhook set to {webhook_url}', 200
        else:
            logger.error("❌ تنظیم Webhook ناموفق بود")
            return '❌ تنظیم Webhook ناموفق بود', 500
    
    except Exception as e:
        logger.error(f"❌ خطا در set_webhook:\n{traceback.format_exc()}")
        return f'Error: {e}', 500

@app.route('/deletewebhook', methods=['GET'])
def delete_webhook():
    """
    حذف Webhook (برای برگشت به حالت Polling)
    """
    try:
        bot.remove_webhook()
        logger.info("✅ Webhook حذف شد")
        return '✅ Webhook removed', 200
    except Exception as e:
        logger.error(f"❌ خطا در حذف Webhook: {e}")
        return f'Error: {e}', 500

@app.route('/', methods=['GET'])
def home():
    """
    صفحه‌ی اصلی برای بررسی وضعیت سرویس
    """
    return '🤖 ربات دانلودر فعال است!', 200

@app.route('/health', methods=['GET'])
def health():
    """
    بررسی سلامت (برای Render)
    """
    return jsonify({"status": "healthy", "webhook": "active"}), 200

# ==========================================
# اجرا (برای Polling محلی یا اجرای مستقیم)
# ==========================================
if __name__ == '__main__':
    # اگر روی Render اجرا می‌شود، از پورت محیط استفاده کن
    port = int(os.environ.get('PORT', 10000))
    
    # اگر Webhook تنظیم شده، نیازی به Polling نیست
    logger.info(f"🚀 Starting Flask app on port {port}...")
    app.run(host='0.0.0.0', port=port)
