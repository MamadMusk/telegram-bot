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
    get_force_sub_keyboard, get_confirm_keyboard,
    get_stats_refresh_keyboard, get_admin_list_inline_keyboard,
    get_settings_inline_keyboard, get_force_sub_inline_keyboard,
    get_back_keyboard, COMMANDS
)
from database import (
    add_user, get_all_users, get_stats,
    increment_download, get_total_downloads,
    get_force_channels_list, add_force_channel, remove_force_channel,
    get_all_admins, add_admin, remove_admin,
    get_all_users_count, set_setting, get_setting,
    init_db
)

# ===== 1. اول دیتابیس =====
init_db()

# ===== 2. بعد Flask app =====
app = Flask(__name__)

# ===== 3. بعد بات =====
bot = telebot.TeleBot(TOKEN)
bot.user_data = {}

# ===== 4. تنظیمات اولیه =====
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

logging.basicConfig(level=logging.INFO)

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
        except Exception as e:
            logging.error(f"Error checking channel {channel}: {e}")
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
        logging.error(f"Error in download_instagram_post: {e}")
        return None, str(e)

# ===================================================
# 📊 توابع ادمین
# ===================================================
def show_stats(chat_id, message_id=None):
    try:
        logging.info(f"📊 show_stats called for {chat_id}")
        stats = get_stats()
        total_downloads = get_total_downloads()
        
        text = MESSAGES["stats_text"].format(
            total=stats.get('users', 0),
            today=stats.get('today_downloads', 0),
            week=stats.get('active_users_7d', 0),
            month=stats.get('month', 0),
            downloads=total_downloads
        )
        
        keyboard = get_stats_refresh_keyboard()
        
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, parse_mode='HTML', reply_markup=keyboard)
        else:
            bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard)
        logging.info("✅ show_stats completed successfully")
    except Exception as e:
        logging.error(f"❌ Error in show_stats: {e}")

def show_admin_list(chat_id, message_id=None):
    try:
        logging.info(f"📋 show_admin_list called for {chat_id}")
        admins = get_all_admins()
        if not admins:
            admins_text = "❌ هیچ ادمینی ثبت نشده است."
        else:
            admins_text = "\n".join([
                f"• <code>{a['user_id']}</code> - {a.get('first_name', 'Unknown')} (@{a.get('username', '')}) - نقش: {a['role']}"
                for a in admins
            ])
        text = MESSAGES["admin_list"].format(admins=admins_text)
        keyboard = get_admin_list_inline_keyboard(admins)
        
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, parse_mode='HTML', reply_markup=keyboard)
        else:
            bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard)
        logging.info("✅ show_admin_list completed successfully")
    except Exception as e:
        logging.error(f"❌ Error in show_admin_list: {e}")

def show_force_sub_settings(chat_id, message_id=None):
    try:
        logging.info(f"🔒 show_force_sub_settings called for {chat_id}")
        channels = get_force_channels()
        channels_text = "\n".join([f"• {ch}" for ch in channels]) if channels else "❌ هیچ کانالی تنظیم نشده است."
        text = MESSAGES["force_sub_prompt"].format(channels=channels_text)
        keyboard = get_force_sub_inline_keyboard(channels)
        
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, parse_mode='HTML', reply_markup=keyboard)
        else:
            bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard)
        logging.info("✅ show_force_sub_settings completed successfully")
    except Exception as e:
        logging.error(f"❌ Error in show_force_sub_settings: {e}")

def show_settings(chat_id, message_id=None):
    try:
        logging.info(f"⚙️ show_settings called for {chat_id}")
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
        keyboard = get_settings_inline_keyboard()
        
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, parse_mode='HTML', reply_markup=keyboard)
        else:
            bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard)
        logging.info("✅ show_settings completed successfully")
    except Exception as e:
        logging.error(f"❌ Error in show_settings: {e}")

def start_broadcast(chat_id):
    try:
        logging.info(f"📨 start_broadcast called for {chat_id}")
        msg = bot.send_message(chat_id, MESSAGES["broadcast_prompt"])
        bot.user_data[chat_id] = {'step': 'broadcast', 'message_id': msg.message_id}
        logging.info(f"✅ start_broadcast set step for {chat_id}")
    except Exception as e:
        logging.error(f"❌ Error in start_broadcast: {e}")

def process_broadcast_message(chat_id, broadcast_text):
    try:
        logging.info(f"📨 process_broadcast_message for {chat_id}: {broadcast_text[:50]}...")
        if not broadcast_text or len(broadcast_text.strip()) == 0:
            bot.send_message(chat_id, MESSAGES["broadcast_empty"])
            return
        users = get_all_users()
        count = len(users)
        preview_text = MESSAGES["broadcast_preview"].format(message=broadcast_text, count=count)
        keyboard = get_confirm_keyboard()
        msg = bot.send_message(chat_id, preview_text, reply_markup=keyboard, parse_mode='HTML')
        bot.user_data[chat_id] = {'broadcast_message': broadcast_text, 'message_id': msg.message_id}
        logging.info("✅ process_broadcast_message completed")
    except Exception as e:
        logging.error(f"❌ Error in process_broadcast_message: {e}")

def start_add_admin(chat_id):
    try:
        logging.info(f"➕ start_add_admin called for {chat_id}")
        msg = bot.send_message(chat_id, MESSAGES["admin_add_prompt"])
        bot.user_data[chat_id] = {'step': 'add_admin', 'message_id': msg.message_id}
    except Exception as e:
        logging.error(f"❌ Error in start_add_admin: {e}")

def process_add_admin(chat_id, text):
    try:
        logging.info(f"➕ process_add_admin for {chat_id}: {text}")
        new_admin_id = int(text.strip())
        if new_admin_id == chat_id:
            bot.send_message(chat_id, "❌ نمی‌توانید خودتان را دوباره اضافه کنید!")
            return
        add_admin(new_admin_id, "moderator")
        bot.send_message(chat_id, MESSAGES["admin_add_success"].format(role="moderator"))
        show_admin_list(chat_id)
    except ValueError:
        bot.send_message(chat_id, MESSAGES["admin_invalid_id"])
    except Exception as e:
        logging.error(f"❌ Error in process_add_admin: {e}")

def start_add_force_channel(chat_id):
    try:
        logging.info(f"➕ start_add_force_channel called for {chat_id}")
        msg = bot.send_message(chat_id, MESSAGES["force_sub_add_prompt"])
        bot.user_data[chat_id] = {'step': 'add_force_channel', 'message_id': msg.message_id}
    except Exception as e:
        logging.error(f"❌ Error in start_add_force_channel: {e}")

def process_add_force_channel(chat_id, channel):
    try:
        logging.info(f"➕ process_add_force_channel for {chat_id}: {channel}")
        if not channel.startswith('@'):
            channel = f"@{channel}"
        add_force_channel(channel)
        bot.send_message(chat_id, MESSAGES["force_sub_added"].format(channel=channel))
        show_force_sub_settings(chat_id)
    except Exception as e:
        logging.error(f"❌ Error in process_add_force_channel: {e}")

def process_setting_change(chat_id, value, key):
    try:
        logging.info(f"⚙️ process_setting_change for {chat_id}: {key} = {value}")
        if key in ["daily_quota", "max_file_size"]:
            int(value)
        set_setting(key, value)
        bot.send_message(chat_id, MESSAGES["settings_updated"])
        show_settings(chat_id)
    except ValueError:
        bot.send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید!")
        if key == "daily_quota":
            msg = bot.send_message(chat_id, MESSAGES["settings_quota_prompt"])
        else:
            msg = bot.send_message(chat_id, MESSAGES["settings_size_prompt"])
        bot.user_data[chat_id] = {'step': f'set_{key}', 'message_id': msg.message_id}
    except Exception as e:
        logging.error(f"❌ Error in process_setting_change: {e}")

# ===================================================
# 🌐 Webhook - پردازش دستی کامل
# ===================================================
@app.route('/', methods=['POST'])
def webhook():
    try:
        if request.headers.get('content-type') != 'application/json':
            return 'Unsupported content type', 400
        
        json_string = request.get_data().decode('utf-8')
        logging.info("📩 Webhook received")
        
        update = telebot.types.Update.de_json(json_string)
        
        # ===== پردازش Callback Query (دکمه‌های شیشه‌ای) =====
        if update.callback_query:
            call = update.callback_query
            user_id = call.from_user.id
            chat_id = call.message.chat.id
            message_id = call.message.message_id
            data = call.data
            
            logging.info(f"📞 Callback: {data} from {user_id}")
            
            if not is_admin(user_id):
                bot.answer_callback_query(call.id, "⛔ شما دسترسی ادمین ندارید!", show_alert=True)
                return 'OK', 200
            
            bot.answer_callback_query(call.id)
            
            # ===== بروزرسانی آمار =====
            if data == "refresh_stats":
                bot.answer_callback_query(call.id, "🔄 آمار بروزرسانی شد!", show_alert=False)
                show_stats(chat_id, message_id)
                return 'OK', 200
            
            # ===== مدیریت ادمین‌ها =====
            elif data == "admin_add":
                bot.answer_callback_query(call.id, "➕ لطفاً آیدی عددی را وارد کنید", show_alert=False)
                bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
                start_add_admin(chat_id)
                return 'OK', 200
            
            elif data.startswith("admin_remove_"):
                admin_id = int(data.replace("admin_remove_", ""))
                if admin_id == user_id:
                    bot.answer_callback_query(call.id, "❌ نمی‌توانید خودتان را حذف کنید!", show_alert=True)
                    return 'OK', 200
                remove_admin(admin_id)
                bot.answer_callback_query(call.id, f"✅ ادمین {admin_id} حذف شد!", show_alert=True)
                show_admin_list(chat_id, message_id)
                return 'OK', 200
            
            # ===== قفل اسپانسر =====
            elif data == "force_sub_add":
                bot.answer_callback_query(call.id, "➕ لطفاً آیدی کانال را با @ وارد کنید", show_alert=False)
                bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
                start_add_force_channel(chat_id)
                return 'OK', 200
            
            elif data.startswith("force_sub_remove_"):
                channel = data.replace("force_sub_remove_", "")
                if remove_force_channel(channel):
                    bot.answer_callback_query(call.id, f"✅ کانال {channel} حذف شد!", show_alert=True)
                else:
                    bot.answer_callback_query(call.id, f"❌ کانال {channel} پیدا نشد!", show_alert=True)
                show_force_sub_settings(chat_id, message_id)
                return 'OK', 200
            
            # ===== تنظیمات =====
            elif data == "setting_quota":
                bot.answer_callback_query(call.id, "📊 عدد مورد نظر را وارد کنید", show_alert=False)
                bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
                msg = bot.send_message(chat_id, MESSAGES["settings_quota_prompt"])
                bot.user_data[chat_id] = {'step': 'set_daily_quota', 'message_id': msg.message_id}
                return 'OK', 200
            
            elif data == "setting_size":
                bot.answer_callback_query(call.id, "📦 عدد مورد نظر را وارد کنید", show_alert=False)
                bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
                msg = bot.send_message(chat_id, MESSAGES["settings_size_prompt"])
                bot.user_data[chat_id] = {'step': 'set_max_file_size', 'message_id': msg.message_id}
                return 'OK', 200
            
            elif data == "setting_active":
                current = get_setting("is_active", "True")
                new_value = "False" if current == "True" else "True"
                set_setting("is_active", new_value)
                bot.answer_callback_query(call.id, f"✅ وضعیت تغییر کرد: {'فعال' if new_value == 'True' else 'غیرفعال'}", show_alert=True)
                show_settings(chat_id, message_id)
                return 'OK', 200
            
            # ===== ارسال همگانی =====
            elif data == "broadcast_confirm":
                bot.answer_callback_query(call.id, "📨 در حال ارسال...", show_alert=False)
                data_obj = bot.user_data.get(user_id, {})
                broadcast_text = data_obj.get('broadcast_message', '')
                if not broadcast_text:
                    bot.send_message(user_id, "❌ پیامی برای ارسال وجود ندارد.")
                    return 'OK', 200
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
                    bot.edit_message_reply_markup(chat_id, data_obj.get('message_id'), reply_markup=None)
                except:
                    pass
                bot.send_message(user_id, MESSAGES["broadcast_success"].format(count=success_count))
                if user_id in bot.user_data:
                    del bot.user_data[user_id]
                return 'OK', 200
            
            elif data == "broadcast_cancel":
                bot.answer_callback_query(call.id, "❌ لغو شد", show_alert=False)
                data_obj = bot.user_data.get(user_id, {})
                try:
                    bot.edit_message_reply_markup(chat_id, data_obj.get('message_id'), reply_markup=None)
                except:
                    pass
                bot.send_message(user_id, MESSAGES["broadcast_cancelled"])
                if user_id in bot.user_data:
                    del bot.user_data[user_id]
                return 'OK', 200
            
            # ===== تأیید عضویت =====
            elif data == "force_sub_verify":
                is_subscribed, not_subscribed = check_user_subscription(user_id)
                if is_subscribed:
                    bot.answer_callback_query(call.id, "✅ عضویت شما تأیید شد!", show_alert=True)
                    bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
                    if is_admin(user_id):
                        keyboard = get_admin_keyboard()
                    else:
                        keyboard = get_user_keyboard()
                    bot.send_message(user_id, MESSAGES["force_sub_verified"], reply_markup=keyboard)
                else:
                    channels_text = "\n".join([f"• {ch}" for ch in not_subscribed])
                    bot.answer_callback_query(call.id, "❌ هنوز در همه کانال‌ها عضو نشدی!", show_alert=True)
                    bot.send_message(user_id, MESSAGES["force_sub_required"].format(channels=channels_text), parse_mode='HTML')
                return 'OK', 200
            
            # ===== بازگشت =====
            elif data == "admin_back":
                bot.answer_callback_query(call.id, "🔙 بازگشت", show_alert=False)
                bot.edit_message_text("🛠 پنل مدیریت", chat_id, message_id, reply_markup=get_admin_keyboard())
                return 'OK', 200
            
            return 'OK', 200
        
        # ===== پردازش پیام =====
        elif update.message:
            chat_id = update.message.chat.id
            user_id = update.message.from_user.id
            text = update.message.text
            username = update.message.from_user.username
            first_name = update.message.from_user.first_name
            last_name = update.message.from_user.last_name
            
            logging.info(f"📨 Message from {chat_id}: {text}")
            
            add_user(user_id, username, first_name, last_name)
            
            # ===== بررسی عضویت اجباری =====
            if not is_admin(user_id):
                is_subscribed, not_subscribed = check_user_subscription(user_id)
                if not is_subscribed:
                    channels_text = "\n".join([f"• {ch}" for ch in not_subscribed])
                    keyboard = get_force_sub_keyboard(not_subscribed)
                    bot.send_message(
                        chat_id,
                        MESSAGES["force_sub_required"].format(channels=channels_text),
                        reply_markup=keyboard,
                        parse_mode='HTML'
                    )
                    return 'OK', 200
            
            # ===== پردازش مراحل (step) =====
            step_data = bot.user_data.get(chat_id, {})
            step = step_data.get('step')
            
            if step == 'add_admin':
                process_add_admin(chat_id, text)
                if chat_id in bot.user_data:
                    del bot.user_data[chat_id]
                return 'OK', 200
            
            elif step == 'add_force_channel':
                process_add_force_channel(chat_id, text)
                if chat_id in bot.user_data:
                    del bot.user_data[chat_id]
                return 'OK', 200
            
            elif step == 'set_daily_quota':
                process_setting_change(chat_id, text, 'daily_quota')
                if chat_id in bot.user_data:
                    del bot.user_data[chat_id]
                return 'OK', 200
            
            elif step == 'set_max_file_size':
                process_setting_change(chat_id, text, 'max_file_size')
                if chat_id in bot.user_data:
                    del bot.user_data[chat_id]
                return 'OK', 200
            
            elif step == 'broadcast':
                process_broadcast_message(chat_id, text)
                if chat_id in bot.user_data:
                    del bot.user_data[chat_id]
                return 'OK', 200
            
            # ===== /start =====
            if text and text.startswith('/start'):
                if is_admin(user_id):
                    keyboard = get_admin_keyboard()
                    bot.send_message(chat_id, MESSAGES["start"], reply_markup=keyboard)
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
                    start_broadcast(chat_id)
                    return 'OK', 200
                elif text == "🔒 قفل اسپانسر":
                    show_force_sub_settings(chat_id)
                    return 'OK', 200
                elif text == "📋 مدیریت ادمین‌ها":
                    show_admin_list(chat_id)
                    return 'OK', 200
                elif text == "⚙️ تنظیمات ربات":
                    show_settings(chat_id)
                    return 'OK', 200
            
            # ===== لینک اینستاگرام =====
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
    except Exception as e:
        logging.error(f"❌ Webhook error: {e}")
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
