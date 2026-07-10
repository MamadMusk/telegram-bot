from flask import Flask, request
import telebot
import os
import yt_dlp
import logging
import time
import re
import requests

# ===== ایمپورت‌های جدید =====
from config import TOKEN, ADMIN_IDS, DOWNLOAD_DIR, is_admin
from messages import (
    MESSAGES, get_admin_keyboard, get_user_keyboard, 
    get_admin_inline_keyboard, get_force_sub_keyboard, 
    get_confirm_keyboard, get_admin_actions_keyboard, COMMANDS
)
from database import (
    add_user, get_all_users, get_user_count, get_stats, 
    increment_download, get_total_downloads, 
    get_setting, set_setting,
    get_force_channels_list, add_force_channel, remove_force_channel,
    get_all_admins, add_admin, remove_admin, is_super_admin,
    get_all_users_count
)

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
        except:
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

def download_instagram_post(url):
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
                    increment_download()
                    return files, None
        except Exception as e:
            logging.warning(f"yt-dlp failed: {e}")

        img_file = download_image_direct(shortcode)
        if img_file:
            increment_download()
            return [img_file], None

        return None, MESSAGES["download_failed"]
    except Exception as e:
        logging.error(f"Error: {e}")
        return None, str(e)

# ===================================================
# 🤖 هندلرهای پیام
# ===================================================
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    add_user(user_id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
    
    if not is_admin(user_id):
        is_subscribed, not_subscribed = check_user_subscription(user_id)
        if not is_subscribed:
            channels_text = "\n".join([f"• {ch}" for ch in not_subscribed])
            keyboard = get_force_sub_keyboard(not_subscribed)
            bot.send_message(
                user_id, 
                MESSAGES["force_sub_required"].format(channels=channels_text),
                reply_markup=keyboard
            )
            return
    
    if is_admin(user_id):
        keyboard = get_admin_keyboard()
    else:
        keyboard = get_user_keyboard()
    
    bot.send_message(user_id, MESSAGES["start"], reply_markup=keyboard)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text
    
    add_user(user_id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
    
    # ===== بررسی عضویت اجباری =====
    if not is_admin(user_id):
        is_subscribed, not_subscribed = check_user_subscription(user_id)
        if not is_subscribed:
            channels_text = "\n".join([f"• {ch}" for ch in not_subscribed])
            keyboard = get_force_sub_keyboard(not_subscribed)
            bot.send_message(
                user_id, 
                MESSAGES["force_sub_required"].format(channels=channels_text),
                reply_markup=keyboard
            )
            return
    
    # ===== دکمه‌های ادمین =====
    if is_admin(user_id):
        if text == "📊 آمار ربات":
            show_stats(message)
            return
        elif text == "📨 ارسال همگانی":
            start_broadcast(message)
            return
        elif text == "🔒 قفل اسپانسر":
            show_force_sub_settings(message)
            return
        elif text == "📋 مدیریت ادمین‌ها":
            show_admin_list(message)
            return
        elif text == "⚙️ تنظیمات ربات":
            show_settings(message)
            return
        elif text == "🔙 بازگشت":
            bot.send_message(user_id, MESSAGES["start"], reply_markup=get_admin_keyboard())
            return
    
    # ===== پردازش لینک =====
    if 'instagram.com' in text:
        msg = bot.send_message(user_id, MESSAGES["downloading"])
        files, error = download_instagram_post(text)
        if not files:
            bot.edit_message_text(f"❌ {error}", user_id, msg.message_id)
            return
        for f in files:
            try:
                with open(f, 'rb') as media:
                    if f.endswith('.mp4'):
                        bot.send_video(user_id, media, caption=MESSAGES["caption"])
                    else:
                        bot.send_photo(user_id, media, caption=MESSAGES["caption"])
                    os.remove(f)
            except Exception as e:
                bot.send_message(user_id, MESSAGES["send_error"].format(error=str(e)))
        bot.delete_message(user_id, msg.message_id)
    else:
        if not is_admin(user_id):
            bot.send_message(user_id, MESSAGES["invalid_link"])

# ===================================================
# 📊 توابع ادمین
# ===================================================
def show_stats(message):
    user_id = message.chat.id
    stats = get_stats()
    total_downloads = get_total_downloads()
    text = MESSAGES["stats_text"].format(
        total=stats['total'],
        today=stats['today'],
        week=stats['week'],
        month=stats['month'],
        downloads=total_downloads
    )
    bot.send_message(user_id, text, parse_mode='Markdown')

# ===== ارسال همگانی =====
def start_broadcast(message):
    user_id = message.chat.id
    msg = bot.send_message(user_id, MESSAGES["broadcast_prompt"])
    bot.register_next_step_handler(msg, process_broadcast_message)

def process_broadcast_message(message):
    user_id = message.chat.id
    broadcast_text = message.text
    if not broadcast_text or len(broadcast_text.strip()) == 0:
        bot.send_message(user_id, MESSAGES["broadcast_empty"])
        return
    users = get_all_users()
    count = len(users)
    preview_text = MESSAGES["broadcast_preview"].format(message=broadcast_text, count=count)
    keyboard = get_confirm_keyboard()
    msg = bot.send_message(user_id, preview_text, reply_markup=keyboard, parse_mode='Markdown')
    bot.user_data = getattr(bot, 'user_data', {})
    bot.user_data[user_id] = {'broadcast_message': broadcast_text, 'message_id': msg.message_id}

# ===== قفل اسپانسر =====
def show_force_sub_settings(message):
    user_id = message.chat.id
    channels = get_force_channels()
    channels_text = "\n".join([f"• {ch}" for ch in channels]) if channels else "❌ هیچ کانالی تنظیم نشده است."
    bot.send_message(
        user_id,
        MESSAGES["force_sub_prompt"].format(channels=channels_text),
        parse_mode='Markdown'
    )

# ===== مدیریت ادمین‌ها =====
def show_admin_list(message):
    user_id = message.chat.id
    admins = get_all_admins()
    if not admins:
        admins_text = "❌ هیچ ادمینی ثبت نشده است."
    else:
        admins_text = "\n".join([
            f"• `{a['user_id']}` - {a.get('first_name', 'Unknown')} (@{a.get('username', '')}) - نقش: {a['role']}"
            for a in admins
        ])
    text = MESSAGES["admin_list"].format(admins=admins_text)
    keyboard = InlineKeyboardMarkup(row_width=2)
    btn_add = InlineKeyboardButton("➕ افزودن ادمین", callback_data="admin_add")
    btn_back = InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")
    keyboard.add(btn_add, btn_back)
    bot.send_message(user_id, text, parse_mode='Markdown', reply_markup=keyboard)

def start_add_admin(message):
    user_id = message.chat.id
    msg = bot.send_message(user_id, MESSAGES["admin_add_prompt"])
    bot.register_next_step_handler(msg, process_add_admin)

def process_add_admin(message):
    user_id = message.chat.id
    try:
        new_admin_id = int(message.text.strip())
        if new_admin_id == user_id:
            bot.send_message(user_id, "❌ نمی‌توانید خودتان را دوباره اضافه کنید!")
            return
        add_admin(new_admin_id, "moderator")
        bot.send_message(user_id, MESSAGES["admin_add_success"].format(role="moderator"))
    except ValueError:
        bot.send_message(user_id, MESSAGES["admin_invalid_id"])

# ===== تنظیمات =====
def show_settings(message):
    user_id = message.chat.id
    channels = get_force_channels()
    channels_text = ", ".join(channels) if channels else "❌ هیچ"
    daily_quota = get_setting("daily_quota", "10")
    max_file_size = get_setting("max_file_size", "50")
    is_active = get_setting("is_active", "True")
    text = MESSAGES["settings_list"].format(
        channels=channels_text,
        daily_quota=daily_quota,
        max_file_size=max_file_size,
        is_active="🟢 فعال" if is_active == "True" else "🔴 غیرفعال"
    )
    keyboard = InlineKeyboardMarkup(row_width=2)
    btn_quota = InlineKeyboardButton("📊 سقف دانلود", callback_data="setting_quota")
    btn_size = InlineKeyboardButton("📦 حجم فایل", callback_data="setting_size")
    btn_active = InlineKeyboardButton("🔄 وضعیت ربات", callback_data="setting_active")
    btn_back = InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")
    keyboard.add(btn_quota, btn_size, btn_active, btn_back)
    bot.send_message(user_id, text, parse_mode='Markdown', reply_markup=keyboard)

# ===================================================
# 📞 هندلرهای Callback
# ===================================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        bot.answer_callback_query(call.id, "⛔ شما دسترسی ادمین ندارید!", show_alert=True)
        return
    
    data = call.data
    
    # ===== ارسال همگانی =====
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
        except:
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
        except:
            pass
        bot.send_message(user_id, MESSAGES["broadcast_cancelled"])
        if user_id in bot.user_data:
            del bot.user_data[user_id]
        return
    
    # ===== عضویت اجباری =====
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
    
    # ===== مدیریت ادمین‌ها =====
    elif data == "admin_add":
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)
        except:
            pass
        start_add_admin(call.message)
        return
    
    elif data.startswith("admin_remove_"):
        admin_id = int(data.replace("admin_remove_", ""))
        if admin_id == user_id:
            bot.answer_callback_query(call.id, "❌ نمی‌توانید خودتان را حذف کنید!", show_alert=True)
            return
        remove_admin(admin_id)
        bot.answer_callback_query(call.id, "✅ ادمین حذف شد!", show_alert=True)
        show_admin_list(call.message)
        return
    
    elif data == "admin_admins":
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)
        except:
            pass
        show_admin_list(call.message)
        return
    
    # ===== تنظیمات =====
    elif data.startswith("setting_"):
        key = data.replace("setting_", "")
        if key == "quota":
            bot.answer_callback_query(call.id)
            msg = bot.send_message(user_id, "📊 سقف دانلود روزانه را به عدد وارد کنید (0 = نامحدود):")
            bot.register_next_step_handler(msg, lambda m: update_setting_handler(m, "daily_quota"))
        elif key == "size":
            bot.answer_callback_query(call.id)
            msg = bot.send_message(user_id, "📦 حداکثر حجم فایل را به مگابایت وارد کنید:")
            bot.register_next_step_handler(msg, lambda m: update_setting_handler(m, "max_file_size"))
        elif key == "active":
            current = get_setting("is_active", "True")
            new_value = "False" if current == "True" else "True"
            set_setting("is_active", new_value)
            bot.answer_callback_query(call.id, f"✅ وضعیت تغییر کرد: {'فعال' if new_value == 'True' else 'غیرفعال'}")
            show_settings(call.message)
        return
    
    # ===== بازگشت =====
    elif data == "admin_back":
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)
        except:
            pass
        bot.send_message(user_id, MESSAGES["admin_welcome"], reply_markup=get_admin_keyboard())
        return
    
    elif data == "admin_close":
        bot.answer_callback_query(call.id)
        try:
            bot.delete_message(user_id, call.message.message_id)
        except:
            pass
        return

def update_setting_handler(message, key):
    user_id = message.chat.id
    try:
        value = message.text.strip()
        if key in ["daily_quota", "max_file_size"]:
            int(value)  # validate
        set_setting(key, value)
        bot.send_message(user_id, MESSAGES["settings_updated"])
        show_settings(message)
    except ValueError:
        bot.send_message(user_id, "❌ لطفاً یک عدد معتبر وارد کنید!")
        msg = bot.send_message(user_id, "دوباره وارد کنید:")
        bot.register_next_step_handler(msg, lambda m: update_setting_handler(m, key))

# ===================================================
# 🌐 Webhook
# ===================================================
@app.route('/', methods=['POST'])
def webhook():
    try:
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return 'OK', 200
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
