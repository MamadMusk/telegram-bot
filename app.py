from flask import Flask, request
import telebot
import os
import yt_dlp
import logging
import time
import re
import requests

from config import TOKEN, ADMIN_IDS, DOWNLOAD_DIR, is_admin, get_db_setting
from messages import (
    MESSAGES, get_admin_keyboard, get_user_keyboard,
    get_force_sub_keyboard, get_confirm_keyboard, COMMANDS
)
from database import (
    add_user, get_all_users, get_stats,
    increment_download, get_total_downloads,
    get_force_channels_list, add_force_channel, remove_force_channel,
    get_all_admins, add_admin, remove_admin, is_super_admin,
    get_all_users_count, set_setting, get_setting,
    init_db
)

# ===== راه‌اندازی دیتابیس =====
init_db()

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

logging.basicConfig(level=logging.INFO)

# ===== تنظیم کامندها =====
try:
    bot.set_my_commands(COMMANDS)
    logging.info("✅ کامندها تنظیم شد")
except Exception as e:
    logging.error(f"خطا در تنظیم کامندها: {e}")

# ===================================================
# 🔒 توابع بررسی عضویت
# ===================================================
def get_force_channels():
    return get_force_channels_list()

def check_user_subscription(user_id):
    channels = get_force_channels()
    if not channels:
        return True, []
    not_subscribed = []
    for channel in channels:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['creator', 'administrator', 'member']:
                not_subscribed.append(channel)
        except Exception:
            not_subscribed.append(channel)
    return len(not_subscribed) == 0, not_subscribed

# ===================================================
# 📥 توابع دانلود
# ===================================================
def download_image_direct(shortcode):
    try:
        embed_url = f"https://www.instagram.com/p/{shortcode}/embed/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(embed_url, headers=headers, timeout=15)
        if response.status_code == 200:
            match = re.search(r'<img[^>]+src="([^"]+)"', response.text)
            if match:
                img_url = match.group(1)
                if 'cdninstagram.com' in img_url:
                    img_response = requests.get(img_url, headers=headers, timeout=15)
                    if img_response.status_code == 200:
                        filename = os.path.join(DOWNLOAD_DIR, f"{shortcode}.jpg")
                        with open(filename, 'wb') as f:
                            f.write(img_response.content)
                        return filename
        return None
    except Exception as e:
        logging.error(f"Direct image error: {e}")
        return None

def download_instagram_post(url, user_id):
    try:
        shortcode_match = re.search(r'/(?:p|reel|tv)/([^/?]+)', url)
        if not shortcode_match:
            return None, "لینک معتبر نیست"
        shortcode = shortcode_match.group(1)

        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': False,
            'format': 'best[ext=mp4]/best',
            'ignoreerrors': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                files = []
                if info:
                    if 'entries' in info and info['entries']:
                        for entry in info['entries']:
                            if entry:
                                fname = ydl.prepare_filename(entry)
                                if os.path.exists(fname):
                                    files.append(fname)
                    else:
                        fname = ydl.prepare_filename(info)
                        if os.path.exists(fname):
                            files.append(fname)
                if files:
                    increment_download(user_id)
                    return files, None
        except Exception as e:
            logging.warning(f"yt-dlp failed: {e}")

        img_file = download_image_direct(shortcode)
        if img_file:
            increment_download(user_id)
            return [img_file], None

        return None, MESSAGES["download_failed"]
    except Exception as e:
        logging.error(f"Error: {e}")
        return None, str(e)

# ===================================================
# 📊 توابع ادمین
# ===================================================
def show_stats(chat_id):
    stats = get_stats()
    total_downloads = get_total_downloads()
    text = MESSAGES["stats_text"].format(
        total=stats.get('users', 0),
        today=stats.get('today_downloads', 0),
        week=stats.get('active_users_7d', 0),
        month=stats.get('month', 0),
        downloads=total_downloads
    )
    bot.send_message(chat_id, text, parse_mode='Markdown')

def start_broadcast(chat_id, message_obj):
    msg = bot.send_message(chat_id, MESSAGES["broadcast_prompt"])
    bot.register_next_step_handler(msg, process_broadcast_message)

def process_broadcast_message(message):
    chat_id = message.chat.id
    broadcast_text = message.text
    if not broadcast_text or len(broadcast_text.strip()) == 0:
        bot.send_message(chat_id, MESSAGES["broadcast_empty"])
        return
    users = get_all_users()
    count = len(users)
    preview_text = MESSAGES["broadcast_preview"].format(message=broadcast_text, count=count)
    keyboard = get_confirm_keyboard()
    msg = bot.send_message(chat_id, preview_text, reply_markup=keyboard, parse_mode='Markdown')
    bot.user_data = getattr(bot, 'user_data', {})
    bot.user_data[chat_id] = {'broadcast_message': broadcast_text, 'message_id': msg.message_id}

def show_force_sub_settings(chat_id):
    channels = get_force_channels()
    channels_text = "\n".join([f"• {ch}" for ch in channels]) if channels else "❌ هیچ کانالی تنظیم نشده است."
    bot.send_message(
        chat_id,
        MESSAGES["force_sub_prompt"].format(channels=channels_text),
        parse_mode='Markdown'
    )

# ===================================================
# 📞 پردازش Callback
# ===================================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        bot.answer_callback_query(call.id, "⛔ شما دسترسی ادمین ندارید!", show_alert=True)
        return
    
    data = call.data
    
    if data == "broadcast_confirm":
        bot.answer_callback_query(call.id, "📨 در حال ارسال...")
        bot.user_data = getattr(bot, 'user_data', {})
        data_obj = bot.user_data.get(user_id, {})
        broadcast_text = data_obj.get('broadcast_message', '')
        if not broadcast_text:
            bot.send_message(user_id, "❌ پیامی برای ارسال وجود ندارد.")
            return
        users = get_all_users()
        success_count = 0
        for user in users:
            try:
                bot.send_message(user['user_id'], broadcast_text)
                success_count += 1
                time.sleep(0.05)
            except Exception as e:
                logging.error(f"Failed to send to {user['user_id']}: {e}")
        try:
            bot.edit_message_reply_markup(user_id, data_obj.get('message_id'), reply_markup=None)
        except Exception:
            pass
        bot.send_message(user_id, MESSAGES["broadcast_success"].format(count=success_count))
        if user_id in bot.user_data:
            del bot.user_data[user_id]
        return
    
    elif data == "broadcast_cancel":
        bot.answer_callback_query(call.id, "❌ لغو شد")
        bot.user_data = getattr(bot, 'user_data', {})
        data_obj = bot.user_data.get(user_id, {})
        try:
            bot.edit_message_reply_markup(user_id, data_obj.get('message_id'), reply_markup=None)
        except Exception:
            pass
        bot.send_message(user_id, MESSAGES["broadcast_cancelled"])
        if user_id in bot.user_data:
            del bot.user_data[user_id]
        return
    
    elif data == "force_sub_verify":
        is_subscribed, not_subscribed = check_user_subscription(user_id)
        if is_subscribed:
            bot.answer_callback_query(call.id, "✅ عضویت شما تأیید شد!", show_alert=True)
            bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)
            if is_admin(user_id):
                keyboard = get_admin_keyboard()
            else:
                keyboard = get_user_keyboard()
            bot.send_message(user_id, MESSAGES["force_sub_verified"], reply_markup=keyboard)
        else:
            channels_text = "\n".join([f"• {ch}" for ch in not_subscribed])
            bot.answer_callback_query(call.id, "❌ هنوز در همه کانال‌ها عضو نشدی!", show_alert=True)
            bot.send_message(user_id, MESSAGES["force_sub_required"].format(channels=channels_text))
        return

# ===================================================
# 🌐 Webhook - پردازش دستی پیام‌ها
# ===================================================
@app.route('/', methods=['POST'])
def webhook():
    try:
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            logging.info(f"📩 Webhook received: {json_string[:200]}...")
            
            update = telebot.types.Update.de_json(json_string)
            
            if update.message:
                chat_id = update.message.chat.id
                user_id = update.message.from_user.id
                text = update.message.text
                username = update.message.from_user.username
                first_name = update.message.from_user.first_name
                last_name = update.message.from_user.last_name
                
                logging.info(f"📨 Message from {chat_id}: {text}")
                
                # ثبت کاربر در دیتابیس
                add_user(user_id, username, first_name, last_name)
                
                # ===== بررسی عضویت اجباری (به جز ادمین) =====
                if not is_admin(user_id):
                    is_subscribed, not_subscribed = check_user_subscription(user_id)
                    if not is_subscribed:
                        channels_text = "\n".join([f"• {ch}" for ch in not_subscribed])
                        keyboard = get_force_sub_keyboard(not_subscribed)
                        bot.send_message(
                            chat_id,
                            MESSAGES["force_sub_required"].format(channels=channels_text),
                            reply_markup=keyboard
                        )
                        return 'OK', 200
                
                # ===== پردازش /start =====
                if text and text.startswith('/start'):
                    if is_admin(user_id):
                        keyboard = get_admin_keyboard()
                    else:
                        keyboard = get_user_keyboard()
                    bot.send_message(chat_id, MESSAGES["start"], reply_markup=keyboard)
                    return 'OK', 200
                
                # ===== دکمه‌های ادمین =====
                if is_admin(user_id):
                    if text == "📊 آمار ربات":
                        show_stats(chat_id)
                        return 'OK', 200
                    elif text == "📨 ارسال همگانی":
                        start_broadcast(chat_id, update.message)
                        return 'OK', 200
                    elif text == "🔒 قفل اسپانسر":
                        show_force_sub_settings(chat_id)
                        return 'OK', 200
                    elif text == "🔙 بازگشت":
                        bot.send_message(chat_id, MESSAGES["start"], reply_markup=get_admin_keyboard())
                        return 'OK', 200
                
                # ===== پردازش لینک =====
                if text and 'instagram.com' in text:
                    msg = bot.send_message(chat_id, MESSAGES["downloading"])
                    files, error = download_instagram_post(text, user_id)
                    
                    if not files:
                        bot.edit_message_text(f"❌ {error}", chat_id, msg.message_id)
                        return 'OK', 200
                    
                    for f in files:
                        try:
                            with open(f, 'rb') as media:
                                if f.endswith('.mp4'):
                                    bot.send_video(chat_id, media, caption=MESSAGES["caption"])
                                else:
                                    bot.send_photo(chat_id, media, caption=MESSAGES["caption"])
                                os.remove(f)
                        except Exception as e:
                            logging.error(f"خطا در ارسال فایل: {e}")
                            bot.send_message(chat_id, MESSAGES["send_error"].format(error=str(e)))
                    
                    bot.delete_message(chat_id, msg.message_id)
                else:
                    if not is_admin(user_id):
                        bot.send_message(chat_id, MESSAGES["invalid_link"])
            
            return 'OK', 200
        else:
            return 'Unsupported content type', 400
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return 'Error', 500

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    webhook_url = 'https://telegram-bot-tkaz.onrender.com/'
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=webhook_url)
    return 'Webhook set!', 200

@app.route('/', methods=['GET'])
def home():
    return 'ربات در حال کار است!', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
