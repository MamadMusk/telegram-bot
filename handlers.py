import logging
import time
import re
import os
import requests
import yt_dlp
import threading
from telebot.types import MenuButtonCommands, InlineKeyboardMarkup, InlineKeyboardButton

from config import is_admin, DOWNLOAD_DIR
from messages import (
    MESSAGES, MESSAGES_FA, MESSAGES_EN, get_message,
    get_admin_keyboard, get_user_keyboard,
    get_force_sub_keyboard, get_confirm_keyboard,
    get_stats_refresh_keyboard, get_admin_list_inline_keyboard,
    get_settings_inline_keyboard, get_force_sub_inline_keyboard,
    get_rate_limit_keyboard, get_admin_permissions_keyboard,
    get_broadcast_progress_keyboard, get_broadcast_cancel_keyboard,
    get_admin_inline_keyboard, get_language_keyboard,
    get_settings_new_keyboard,
    COMMANDS_FA, COMMANDS_EN
)
from database import (
    add_user, get_all_users, get_stats,
    increment_download, get_total_downloads,
    get_force_channels_list, add_force_channel, remove_force_channel,
    get_all_admins, add_admin, remove_admin,
    set_setting, get_setting,
    get_rate_limit_enabled, set_rate_limit_enabled,
    get_rate_limit_seconds, set_rate_limit_seconds,
    get_admin_permissions, update_admin_permissions,
    get_user, get_user_language, set_user_language,
    get_admin_role
)

OWNER_ID = 1085150385

# متغیر برای نگهداری وضعیت ارسال همگانی در حال اجرا
broadcast_jobs = {}

# ===================================================
# 📩 تابع ارسال پیام خوش‌آمدگویی
# ===================================================
def send_welcome_message(bot, chat_id, user_id, lang=None):
    if lang is None:
        lang = get_user_language(user_id) or "fa"
    
    if is_admin(user_id):
        keyboard = get_admin_keyboard(lang)
    else:
        keyboard = get_user_keyboard()
    
    bot.send_message(chat_id, get_message("start", lang), reply_markup=keyboard)

# ===================================================
# 🔒 توابع بررسی عضویت و مجوزها
# ===================================================
def get_force_channels():
    return get_force_channels_list()

def check_user_subscription(bot, user_id):
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
            logging.error(f"Error checking subscription for {channel}: {e}")
            not_subscribed.append(channel)
    return len(not_subscribed) == 0, not_subscribed

def has_permission(user_id, permission):
    perms = get_admin_permissions(user_id)
    result = perms.get(permission, False)
    logging.info(f"🔍 Permission check: {permission} for {user_id} = {result}")
    return result

def is_owner(user_id):
    return user_id == OWNER_ID

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

        return None, "دانلود نشد."
    except Exception as e:
        logging.error(f"Error in download_instagram_post: {e}")
        return None, str(e)

# ===================================================
# 📊 توابع ادمین (با پشتیبانی از زبان)
# ===================================================
def show_stats(bot, chat_id, message_id=None):
    try:
        lang = get_user_language(chat_id) or "fa"
        stats = get_stats()
        total_downloads = get_total_downloads()
        text = get_message("stats_text", lang).format(
            total=stats.get('users', 0),
            today=stats.get('today_downloads', 0),
            week=stats.get('active_users_7d', 0),
            month=stats.get('month', 0),
            downloads=total_downloads
        )
        keyboard = get_stats_refresh_keyboard()
        if message_id:
            try:
                bot.edit_message_text(text, chat_id, message_id, parse_mode='HTML', reply_markup=keyboard)
            except Exception as e:
                if "message is not modified" in str(e):
                    pass
                else:
                    raise e
        else:
            bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Error in show_stats: {e}")

def show_admin_list(bot, chat_id, message_id=None, current_user_id=None):
    try:
        lang = get_user_language(current_user_id) or "fa"
        if not is_owner(current_user_id) and not has_permission(current_user_id, "can_manage_admins"):
            bot.send_message(chat_id, get_message("admin_no_permission", lang))
            return
        
        admins = get_all_admins()
        if not admins:
            admins_text = "❌ هیچ ادمینی ثبت نشده است."
        else:
            admins_text = "\n".join([
                f"• <code>{a['user_id']}</code> - {a.get('first_name', 'Unknown')} (@{a.get('username', '')}) - نقش: {a['role']}"
                for a in admins
            ])
        
        text = get_message("admin_list", lang).format(admins=admins_text)
        keyboard = get_admin_list_inline_keyboard(admins, current_user_id, lang)
        
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, parse_mode='HTML', reply_markup=keyboard)
        else:
            bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Error in show_admin_list: {e}")

def show_admin_permissions(bot, chat_id, admin_id, message_id=None, current_user_id=None):
    try:
        lang = get_user_language(current_user_id) or "fa"
        if not is_owner(current_user_id) and not has_permission(current_user_id, "can_manage_admins"):
            bot.send_message(chat_id, get_message("admin_no_permission", lang))
            return
        
        if admin_id == OWNER_ID:
            bot.send_message(chat_id, get_message("admin_cant_remove_owner", lang))
            return
        
        perms = get_admin_permissions(admin_id)
        admin_info = get_user(admin_id)
        name = admin_info.get('first_name', 'Unknown') if admin_info else 'Unknown'
        role = get_admin_role(admin_id) or 'viewer'
        
        # ===== نمایش جدید با دکمه‌های دو بخشی =====
        text = get_message("admin_permissions_header", lang).format(
            name=name,
            user_id=admin_id,
            role=role,
            stats="✅" if perms.get("can_view_stats", False) else "❌",
            broadcast="✅" if perms.get("can_send_broadcast", False) else "❌",
            force_sub="✅" if perms.get("can_manage_force_sub", False) else "❌",
            settings="✅" if perms.get("can_manage_settings", False) else "❌",
            admins="✅" if perms.get("can_manage_admins", False) else "❌"
        )
        keyboard = get_admin_permissions_keyboard(admin_id, perms, is_owner=False, lang=lang)
        
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, parse_mode='HTML', reply_markup=keyboard)
        else:
            bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Error in show_admin_permissions: {e}")

def show_force_sub_settings(bot, chat_id, message_id=None):
    try:
        lang = get_user_language(chat_id) or "fa"
        channels = get_force_channels()
        channels_text = "\n".join([f"• {ch}" for ch in channels]) if channels else "❌ هیچ کانالی تنظیم نشده است."
        text = get_message("force_sub_prompt", lang).format(channels=channels_text)
        keyboard = get_force_sub_inline_keyboard(channels, lang)
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, parse_mode='HTML', reply_markup=keyboard)
        else:
            bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Error in show_force_sub_settings: {e}")

# ===================================================
# 📊 تنظیمات جدید
# ===================================================
def show_settings(bot, chat_id, message_id=None):
    try:
        lang = get_user_language(chat_id) or "fa"
        
        # دریافت مقادیر فعلی
        daily_quota = get_setting("daily_quota", "10")
        max_file_size = get_setting("max_file_size", "50")
        is_active = get_setting("is_active", "True") == "True"
        rate_limit_enabled = get_rate_limit_enabled()
        rate_limit_seconds = get_rate_limit_seconds()
        
        # دریافت متن تنظیمات از messages.py
        text = get_message("settings_text", lang)
        
        keyboard = get_settings_new_keyboard(
            lang=lang,
            daily_quota=daily_quota,
            max_file_size=max_file_size,
            is_active=is_active,
            rate_limit_enabled=rate_limit_enabled,
            rate_limit_seconds=rate_limit_seconds
        )
        
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, parse_mode='HTML', reply_markup=keyboard)
        else:
            bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Error in show_settings: {e}")

def show_rate_limit_settings(bot, chat_id, message_id=None):
    try:
        lang = get_user_language(chat_id) or "fa"
        enabled = get_rate_limit_enabled()
        seconds = get_rate_limit_seconds()
        text = get_message("rate_limit_status", lang).format(
            status="🟢 فعال" if enabled else "🔴 غیرفعال",
            seconds=seconds
        )
        keyboard = get_rate_limit_keyboard(lang)
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, parse_mode='HTML', reply_markup=keyboard)
        else:
            bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Error in show_rate_limit_settings: {e}")

# ===================================================
# 📨 ارسال همگانی با نمایش پیشرفت و دکمه لغو
# ===================================================
def start_broadcast(bot, chat_id, user_data=None):
    try:
        logging.info(f"📨 start_broadcast called for {chat_id}")
        lang = get_user_language(chat_id) or "fa"
        keyboard = get_broadcast_cancel_keyboard(lang)
        msg = bot.send_message(
            chat_id,
            get_message("broadcast_prompt", lang),
            reply_markup=keyboard
        )
        if user_data is not None:
            user_data[chat_id] = {'step': 'broadcast', 'message_id': msg.message_id}
        if not hasattr(bot, 'user_data'):
            bot.user_data = {}
        bot.user_data[chat_id] = {'step': 'broadcast', 'message_id': msg.message_id}
        logging.info(f"✅ start_broadcast set step for {chat_id}")
    except Exception as e:
        logging.error(f"❌ Error in start_broadcast: {e}")

def process_broadcast_message(bot, message, user_data):
    chat_id = message.chat.id
    broadcast_text = message.text
    lang = get_user_language(chat_id) or "fa"
    
    try:
        if chat_id in user_data and 'message_id' in user_data[chat_id]:
            bot.delete_message(chat_id, user_data[chat_id]['message_id'])
        elif hasattr(bot, 'user_data') and chat_id in bot.user_data and 'message_id' in bot.user_data[chat_id]:
            bot.delete_message(chat_id, bot.user_data[chat_id]['message_id'])
    except:
        pass
    
    if not broadcast_text or len(broadcast_text.strip()) == 0:
        bot.send_message(chat_id, get_message("broadcast_empty", lang))
        if chat_id in user_data:
            del user_data[chat_id]
        if hasattr(bot, 'user_data') and chat_id in bot.user_data:
            del bot.user_data[chat_id]
        return
    
    users = get_all_users()
    count = len(users)
    preview_text = get_message("broadcast_preview", lang).format(message=broadcast_text, count=count)
    keyboard = get_confirm_keyboard(lang)
    msg = bot.send_message(chat_id, preview_text, reply_markup=keyboard, parse_mode='HTML')
    user_data[chat_id] = {'broadcast_message': broadcast_text, 'message_id': msg.message_id}
    if hasattr(bot, 'user_data'):
        bot.user_data[chat_id] = {'broadcast_message': broadcast_text, 'message_id': msg.message_id}

def start_broadcast_send(bot, chat_id, broadcast_text):
    users = get_all_users()
    total = len(users)
    if total == 0:
        lang = get_user_language(chat_id) or "fa"
        bot.send_message(chat_id, get_message("broadcast_failed", lang).format(error="هیچ کاربری وجود ندارد."))
        return
    
    lang = get_user_language(chat_id) or "fa"
    progress_text = get_message("broadcast_progress", lang).format(
        sent=0,
        total=total,
        percent=0,
        remaining=total,
        failed=0
    )
    keyboard = get_broadcast_progress_keyboard(lang)
    msg = bot.send_message(chat_id, progress_text, parse_mode='HTML', reply_markup=keyboard)
    
    broadcast_jobs[chat_id] = {
        'total': total,
        'sent': 0,
        'failed': 0,
        'users': users,
        'message': broadcast_text,
        'message_id': msg.message_id,
        'running': True
    }
    
    def send_async():
        job = broadcast_jobs.get(chat_id)
        if not job:
            return
        
        for user in job['users']:
            if not job['running']:
                break
            try:
                bot.send_message(user['id'], broadcast_text)
                job['sent'] += 1
                logging.info(f"✅ Broadcast sent to {user['id']}")
            except Exception as e:
                job['failed'] += 1
                logging.error(f"❌ Broadcast failed to {user['id']}: {e}")
            
            if (job['sent'] + job['failed']) % 5 == 0 or (job['sent'] + job['failed']) == job['total']:
                update_broadcast_progress(bot, chat_id)
            
            time.sleep(0.05)
        
        job['running'] = False
        update_broadcast_progress(bot, chat_id, final=True)
    
    threading.Thread(target=send_async, daemon=True).start()

def update_broadcast_progress(bot, chat_id, final=False):
    job = broadcast_jobs.get(chat_id)
    if not job:
        return
    
    lang = get_user_language(chat_id) or "fa"
    total = job['total']
    sent = job['sent']
    failed = job['failed']
    remaining = total - sent - failed
    percent = int((sent / total) * 100) if total > 0 else 0
    
    if final:
        text = get_message("broadcast_success", lang).format(
            total=total,
            success=sent,
            failed=failed
        )
        keyboard = None
    else:
        text = get_message("broadcast_progress", lang).format(
            sent=sent,
            total=total,
            percent=percent,
            remaining=remaining,
            failed=failed
        )
        keyboard = get_broadcast_progress_keyboard(lang)
    
    try:
        bot.edit_message_text(
            text,
            chat_id,
            job['message_id'],
            parse_mode='HTML',
            reply_markup=keyboard
        )
    except Exception as e:
        logging.error(f"Error updating broadcast progress: {e}")

# ===================================================
# 📞 پردازش Callback (دکمه‌های شیشه‌ای)
# ===================================================
def handle_callback_query(bot, call, user_data):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    data = call.data
    
    logging.info(f"📞 Callback: {data} from {user_id}")
    
    # ===== انتخاب زبان =====
    if data == "lang_fa":
        set_user_language(user_id, "fa")
        bot.answer_callback_query(call.id, MESSAGES_FA.get("lang_changed", "زبان تغییر کرد."), show_alert=True)
        try:
            bot.set_my_commands(COMMANDS_FA)
            bot.set_chat_menu_button(chat_id, menu_button=MenuButtonCommands())
            logging.info("✅ کامندها به فارسی تغییر کرد و دکمه‌ی منو تنظیم شد")
        except Exception as e:
            logging.error(f"❌ خطا در تغییر کامندها: {e}")
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
        send_welcome_message(bot, chat_id, user_id, "fa")
        return
    elif data == "lang_en":
        set_user_language(user_id, "en")
        bot.answer_callback_query(call.id, MESSAGES_EN.get("lang_changed_en", "Language changed."), show_alert=True)
        try:
            bot.set_my_commands(COMMANDS_EN)
            bot.set_chat_menu_button(chat_id, menu_button=MenuButtonCommands())
            logging.info("✅ Commands changed to English and menu button set")
        except Exception as e:
            logging.error(f"❌ Error changing commands: {e}")
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
        send_welcome_message(bot, chat_id, user_id, "en")
        return
    
    # ===== بقیه عملیات فقط برای ادمین‌ها =====
    if not is_admin(user_id):
        bot.answer_callback_query(call.id, "⛔ شما دسترسی ادمین ندارید!", show_alert=True)
        return
    
    # ===== بروزرسانی آمار =====
    if data == "refresh_stats":
        bot.answer_callback_query(call.id, "🔄 در حال بروزرسانی...", show_alert=False)
        show_stats(bot, chat_id, message_id)
        return
    
    # ===== منوی اصلی مدیریت =====
    if data == "admin_stats":
        bot.answer_callback_query(call.id, "📊 آماده...", show_alert=False)
        show_stats(bot, chat_id, message_id)
        return
    elif data == "admin_broadcast":
        bot.answer_callback_query(call.id, "📨 شروع ارسال همگانی...", show_alert=False)
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
        start_broadcast(bot, chat_id, user_data)
        return
    elif data == "admin_force_sub":
        bot.answer_callback_query(call.id, "🔒 قفل اسپانسر", show_alert=False)
        show_force_sub_settings(bot, chat_id, message_id)
        return
    elif data == "admin_admins":
        bot.answer_callback_query(call.id, "📋 مدیریت ادمین‌ها", show_alert=False)
        show_admin_list(bot, chat_id, message_id, user_id)
        return
    elif data == "admin_settings":
        bot.answer_callback_query(call.id, "⚙️ تنظیمات", show_alert=False)
        show_settings(bot, chat_id, message_id)
        return
    elif data == "admin_close":
        bot.answer_callback_query(call.id, "❌ بسته شد", show_alert=False)
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        return
    
    # ===== مدیریت ادمین‌ها =====
    elif data == "admin_add":
        lang = get_user_language(user_id) or "fa"
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_admins"):
            bot.answer_callback_query(call.id, get_message("admin_no_permission", lang), show_alert=True)
            return
        bot.answer_callback_query(call.id, "➕ لطفاً آیدی عددی را وارد کنید", show_alert=False)
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
        msg = bot.send_message(chat_id, get_message("admin_add_prompt", lang))
        user_data[chat_id] = {'step': 'add_admin', 'message_id': msg.message_id}
        return
    
    elif data.startswith("admin_view_"):
        admin_id = int(data.replace("admin_view_", ""))
        lang = get_user_language(user_id) or "fa"
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_admins"):
            bot.answer_callback_query(call.id, get_message("admin_no_permission", lang), show_alert=True)
            return
        bot.answer_callback_query(call.id, "🔐 در حال بارگذاری...", show_alert=False)
        show_admin_permissions(bot, chat_id, admin_id, message_id, user_id)
        return
    
    elif data.startswith("admin_perm_toggle_"):
        parts = data.split('_', 4)
        if len(parts) < 5:
            logging.error(f"Invalid callback data: {data}")
            return
        admin_id = int(parts[3])
        perm_key = parts[4]
        lang = get_user_language(user_id) or "fa"
        
        logging.info(f"🔄 Toggle permission: {perm_key} for admin {admin_id}")
        
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_admins"):
            bot.answer_callback_query(call.id, get_message("admin_no_permission", lang), show_alert=True)
            return
        if admin_id == OWNER_ID:
            bot.answer_callback_query(call.id, get_message("admin_cant_remove_owner", lang), show_alert=True)
            return
        
        perms = get_admin_permissions(admin_id)
        old_value = perms.get(perm_key, False)
        new_value = not old_value
        perms[perm_key] = new_value
        success = update_admin_permissions(admin_id, perms)
        if not success:
            bot.answer_callback_query(call.id, "❌ خطا در ذخیره دسترسی!", show_alert=True)
            return
        
        # ===== به‌روزرسانی صفحه =====
        show_admin_permissions(bot, chat_id, admin_id, message_id, user_id)
        return
    
    elif data.startswith("admin_remove_"):
        admin_id = int(data.replace("admin_remove_", ""))
        lang = get_user_language(user_id) or "fa"
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_admins"):
            bot.answer_callback_query(call.id, get_message("admin_no_permission", lang), show_alert=True)
            return
        if admin_id == user_id:
            bot.answer_callback_query(call.id, get_message("admin_cant_remove_self", lang), show_alert=True)
            return
        if admin_id == OWNER_ID:
            bot.answer_callback_query(call.id, get_message("admin_cant_remove_owner", lang), show_alert=True)
            return
        remove_admin(admin_id)
        bot.answer_callback_query(call.id, f"✅ ادمین {admin_id} حذف شد!", show_alert=True)
        show_admin_list(bot, chat_id, None, user_id)
        return
    
    elif data == "admin_list_back":
        bot.answer_callback_query(call.id, "🔙 بازگشت", show_alert=False)
        show_admin_list(bot, chat_id, message_id, user_id)
        return
    
    # ===== قفل اسپانسر =====
    elif data == "force_sub_add":
        lang = get_user_language(user_id) or "fa"
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_force_sub"):
            bot.answer_callback_query(call.id, get_message("admin_no_permission", lang), show_alert=True)
            return
        bot.answer_callback_query(call.id, "➕ لطفاً آیدی کانال را با @ وارد کنید", show_alert=False)
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
        msg = bot.send_message(chat_id, get_message("force_sub_add_prompt", lang))
        user_data[chat_id] = {'step': 'add_force_channel', 'message_id': msg.message_id}
        return
    
    elif data.startswith("force_sub_remove_"):
        lang = get_user_language(user_id) or "fa"
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_force_sub"):
            bot.answer_callback_query(call.id, get_message("admin_no_permission", lang), show_alert=True)
            return
        channel = data.replace("force_sub_remove_", "")
        if remove_force_channel(channel):
            bot.answer_callback_query(call.id, f"✅ کانال {channel} حذف شد!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, f"❌ کانال {channel} پیدا نشد!", show_alert=True)
        show_force_sub_settings(bot, chat_id, message_id)
        return
    
    # ===== تنظیمات جدید =====
    elif data == "setting_quota":
        lang = get_user_language(user_id) or "fa"
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_settings"):
            bot.answer_callback_query(call.id, get_message("admin_no_permission", lang), show_alert=True)
            return
        bot.answer_callback_query(call.id, "📊 عدد مورد نظر را وارد کنید", show_alert=False)
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
        msg = bot.send_message(chat_id, get_message("settings_quota_prompt", lang))
        user_data[chat_id] = {'step': 'set_daily_quota', 'message_id': msg.message_id}
        return
    
    elif data == "setting_size":
        lang = get_user_language(user_id) or "fa"
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_settings"):
            bot.answer_callback_query(call.id, get_message("admin_no_permission", lang), show_alert=True)
            return
        bot.answer_callback_query(call.id, "📦 عدد مورد نظر را وارد کنید", show_alert=False)
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
        msg = bot.send_message(chat_id, get_message("settings_size_prompt", lang))
        user_data[chat_id] = {'step': 'set_max_file_size', 'message_id': msg.message_id}
        return
    
    elif data == "setting_rate_limit":
        lang = get_user_language(user_id) or "fa"
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_settings"):
            bot.answer_callback_query(call.id, get_message("admin_no_permission", lang), show_alert=True)
            return
        bot.answer_callback_query(call.id, "⏱️ تنظیمات محدودیت زمانی", show_alert=False)
        show_rate_limit_settings(bot, chat_id, message_id)
        return
    
    elif data == "setting_toggle_active":
        lang = get_user_language(user_id) or "fa"
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_settings"):
            bot.answer_callback_query(call.id, get_message("admin_no_permission", lang), show_alert=True)
            return
        current = get_setting("is_active", "True")
        new_value = "False" if current == "True" else "True"
        set_setting("is_active", new_value)
        if lang == "en":
            status_text = "Active" if new_value == "True" else "Inactive"
            bot.answer_callback_query(call.id, f"✅ Bot status changed to {status_text}!", show_alert=True)
        else:
            status_text = "فعال" if new_value == "True" else "غیرفعال"
            bot.answer_callback_query(call.id, f"✅ وضعیت ربات به {status_text} تغییر کرد!", show_alert=True)
        show_settings(bot, chat_id, message_id)
        return
    
    # ===== محدودیت زمانی (دکمه‌های تغییر سریع) =====
    elif data == "rate_limit_enable":
        lang = get_user_language(user_id) or "fa"
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_settings"):
            bot.answer_callback_query(call.id, get_message("admin_no_permission", lang), show_alert=True)
            return
        set_rate_limit_enabled(True)
        seconds = get_rate_limit_seconds()
        bot.answer_callback_query(call.id, f"✅ محدودیت زمانی فعال شد! ({seconds} ثانیه)", show_alert=True)
        show_rate_limit_settings(bot, chat_id, message_id)
        return
    
    elif data == "rate_limit_disable":
        lang = get_user_language(user_id) or "fa"
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_settings"):
            bot.answer_callback_query(call.id, get_message("admin_no_permission", lang), show_alert=True)
            return
        set_rate_limit_enabled(False)
        bot.answer_callback_query(call.id, "❌ محدودیت زمانی غیرفعال شد!", show_alert=True)
        show_rate_limit_settings(bot, chat_id, message_id)
        return
    
    elif data.startswith("rate_limit_"):
        lang = get_user_language(user_id) or "fa"
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_settings"):
            bot.answer_callback_query(call.id, get_message("admin_no_permission", lang), show_alert=True)
            return
        seconds = int(data.replace("rate_limit_", ""))
        set_rate_limit_seconds(seconds)
        if get_rate_limit_enabled():
            bot.answer_callback_query(call.id, f"⏱️ زمان انتظار به {seconds} ثانیه تغییر کرد!", show_alert=True)
        else:
            set_rate_limit_enabled(True)
            bot.answer_callback_query(call.id, f"✅ محدودیت زمانی فعال شد! زمان انتظار: {seconds} ثانیه", show_alert=True)
        show_rate_limit_settings(bot, chat_id, message_id)
        return
    
    # ===== ارسال همگانی =====
    elif data == "broadcast_cancel_start":
        lang = get_user_language(user_id) or "fa"
        bot.answer_callback_query(call.id, "❌ ارسال لغو شد!", show_alert=True)
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        if chat_id in user_data:
            del user_data[chat_id]
        if hasattr(bot, 'user_data') and chat_id in bot.user_data:
            del bot.user_data[chat_id]
        bot.send_message(chat_id, get_message("broadcast_cancelled", lang))
        return
    
    elif data == "broadcast_confirm":
        lang = get_user_language(user_id) or "fa"
        if not is_owner(user_id) and not has_permission(user_id, "can_send_broadcast"):
            bot.answer_callback_query(call.id, get_message("admin_no_permission", lang), show_alert=True)
            return
        
        data_obj = user_data.get(user_id, {})
        if not data_obj:
            data_obj = bot.user_data.get(user_id, {})
        broadcast_text = data_obj.get('broadcast_message', '')
        if not broadcast_text:
            bot.send_message(user_id, get_message("broadcast_failed", lang).format(error="پیامی برای ارسال وجود ندارد."))
            return
        
        try:
            bot.edit_message_reply_markup(chat_id, data_obj.get('message_id'), reply_markup=None)
        except:
            pass
        
        bot.answer_callback_query(call.id, "📨 شروع ارسال همگانی...", show_alert=False)
        start_broadcast_send(bot, chat_id, broadcast_text)
        
        if user_id in user_data:
            del user_data[user_id]
        if hasattr(bot, 'user_data') and user_id in bot.user_data:
            del bot.user_data[user_id]
        return
    
    elif data == "broadcast_cancel":
        lang = get_user_language(user_id) or "fa"
        bot.answer_callback_query(call.id, "❌ لغو شد", show_alert=False)
        data_obj = user_data.get(user_id, {})
        if not data_obj:
            data_obj = bot.user_data.get(user_id, {})
        try:
            bot.edit_message_reply_markup(chat_id, data_obj.get('message_id'), reply_markup=None)
        except:
            pass
        bot.send_message(user_id, get_message("broadcast_cancelled", lang))
        if user_id in user_data:
            del user_data[user_id]
        if hasattr(bot, 'user_data') and user_id in bot.user_data:
            del bot.user_data[user_id]
        return
    
    elif data == "broadcast_refresh":
        lang = get_user_language(user_id) or "fa"
        job = broadcast_jobs.get(chat_id)
        if not job or not job.get('running', False):
            bot.answer_callback_query(call.id, get_message("broadcast_failed", lang).format(error="ارسال همگانی در حال اجرا نیست."), show_alert=True)
            return
        update_broadcast_progress(bot, chat_id)
        bot.answer_callback_query(call.id, "🔄 وضعیت بروزرسانی شد!", show_alert=False)
        return
    
    elif data == "broadcast_cancel_force":
        lang = get_user_language(user_id) or "fa"
        job = broadcast_jobs.get(chat_id)
        if job:
            job['running'] = False
            bot.answer_callback_query(call.id, "⏹️ ارسال همگانی متوقف شد.", show_alert=True)
            update_broadcast_progress(bot, chat_id, final=True)
        else:
            bot.answer_callback_query(call.id, get_message("broadcast_failed", lang).format(error="هیچ ارسال همگانی در حال اجرا نیست."), show_alert=True)
        return
    
    # ===== تأیید عضویت =====
    elif data == "force_sub_verify":
        lang = get_user_language(user_id) or "fa"
        is_subscribed, not_subscribed = check_user_subscription(bot, user_id)
        if is_subscribed:
            bot.answer_callback_query(call.id, "✅ عضویت شما تأیید شد!", show_alert=True)
            bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
            bot.send_message(user_id, get_message("force_sub_verified", lang))
        else:
            channels_text = "\n".join([f"• {ch}" for ch in not_subscribed])
            bot.answer_callback_query(call.id, "❌ هنوز در همه کانال‌ها عضو نشدی!", show_alert=True)
            bot.send_message(user_id, get_message("force_sub_required", lang).format(channels=channels_text), parse_mode='HTML')
        return
    
    # ===== بازگشت به پنل مدیریت =====
    elif data == "admin_back":
        lang = get_user_language(user_id) or "fa"
        bot.answer_callback_query(call.id, "🔙 بازگشت", show_alert=False)
        try:
            keyboard = get_admin_inline_keyboard(lang)
            bot.edit_message_text(
                get_message("admin_welcome", lang),
                chat_id,
                message_id,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        except Exception as e:
            logging.warning(f"Editing message failed, sending new one: {e}")
            try:
                bot.delete_message(chat_id, message_id)
            except:
                pass
            keyboard = get_admin_inline_keyboard(lang)
            bot.send_message(
                chat_id,
                get_message("admin_welcome", lang),
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        return

# ===================================================
# 📨 پردازش پیام
# ===================================================
def handle_message(bot, message, user_data, user_last_download=None):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    logging.info(f"📨 Message from {chat_id}: {text}")
    
    # زبان کاربر را دریافت کن (پیش‌فرض فارسی)
    lang = get_user_language(user_id) or "fa"
    add_user(user_id, username, first_name, last_name, lang)
    
    if not is_admin(user_id):
        is_subscribed, not_subscribed = check_user_subscription(bot, user_id)
        if not is_subscribed:
            channels_text = "\n".join([f"• {ch}" for ch in not_subscribed])
            keyboard = get_force_sub_keyboard(not_subscribed)
            bot.send_message(
                chat_id,
                get_message("force_sub_required", lang).format(channels=channels_text),
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            return
    
    # پردازش مراحل (step) - از user_data استفاده کن
    step_data = user_data.get(chat_id, {})
    step = step_data.get('step')
    
    # اگر در user_data نبود، از bot.user_data چک کن
    if not step and hasattr(bot, 'user_data'):
        step_data = bot.user_data.get(chat_id, {})
        step = step_data.get('step')
    
    if step == 'add_admin':
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_admins"):
            bot.send_message(chat_id, get_message("admin_no_permission", lang))
            return
        try:
            new_admin_id = int(text.strip())
            if new_admin_id == user_id:
                bot.send_message(chat_id, "❌ نمی‌توانید خودتان را دوباره اضافه کنید!")
            else:
                add_admin(new_admin_id, "moderator")
                bot.send_message(chat_id, get_message("admin_add_success", lang).format(role="moderator"))
                show_admin_list(bot, chat_id, None, user_id)
        except ValueError:
            bot.send_message(chat_id, get_message("admin_invalid_id", lang))
        if chat_id in user_data:
            del user_data[chat_id]
        if hasattr(bot, 'user_data') and chat_id in bot.user_data:
            del bot.user_data[chat_id]
        return
    
    elif step == 'add_force_channel':
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_force_sub"):
            bot.send_message(chat_id, get_message("admin_no_permission", lang))
            return
        channel = text.strip()
        if not channel.startswith('@'):
            channel = f"@{channel}"
        add_force_channel(channel)
        bot.send_message(chat_id, get_message("force_sub_added", lang).format(channel=channel))
        show_force_sub_settings(bot, chat_id)
        if chat_id in user_data:
            del user_data[chat_id]
        if hasattr(bot, 'user_data') and chat_id in bot.user_data:
            del bot.user_data[chat_id]
        return
    
    elif step == 'set_daily_quota':
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_settings"):
            bot.send_message(chat_id, get_message("admin_no_permission", lang))
            return
        try:
            value = int(text.strip())
            set_setting("daily_quota", str(value))
            bot.send_message(chat_id, get_message("settings_updated", lang))
            show_settings(bot, chat_id)
        except ValueError:
            bot.send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید!")
        if chat_id in user_data:
            del user_data[chat_id]
        if hasattr(bot, 'user_data') and chat_id in bot.user_data:
            del bot.user_data[chat_id]
        return
    
    elif step == 'set_max_file_size':
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_settings"):
            bot.send_message(chat_id, get_message("admin_no_permission", lang))
            return
        try:
            value = int(text.strip())
            set_setting("max_file_size", str(value))
            bot.send_message(chat_id, get_message("settings_updated", lang))
            show_settings(bot, chat_id)
        except ValueError:
            bot.send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید!")
        if chat_id in user_data:
            del user_data[chat_id]
        if hasattr(bot, 'user_data') and chat_id in bot.user_data:
            del bot.user_data[chat_id]
        return
    
    elif step == 'broadcast':
        if not is_owner(user_id) and not has_permission(user_id, "can_send_broadcast"):
            bot.send_message(chat_id, get_message("admin_no_permission", lang))
            return
        process_broadcast_message(bot, message, user_data)
        return
    
    # ===== /start =====
    if text and text.startswith('/start'):
        keyboard = get_language_keyboard()
        bot.send_message(chat_id, get_message("lang_selection", "fa"), reply_markup=keyboard)
        return
    
    # ===== /language =====
    if text and text.startswith('/language'):
        keyboard = get_language_keyboard()
        bot.send_message(chat_id, get_message("lang_prompt", lang), reply_markup=keyboard)
        return
    
    # ===== دکمه‌های ادمین (از طریق Reply Keyboard) =====
    if is_admin(user_id):
        if text == "📊 آمار ربات" or text == "📊 Statistics":
            if not is_owner(user_id) and not has_permission(user_id, "can_view_stats"):
                bot.send_message(chat_id, get_message("admin_no_permission", lang))
                return
            show_stats(bot, chat_id)
            return
        elif text == "📨 ارسال همگانی" or text == "📨 Broadcast":
            if not is_owner(user_id) and not has_permission(user_id, "can_send_broadcast"):
                bot.send_message(chat_id, get_message("admin_no_permission", lang))
                return
            start_broadcast(bot, chat_id, user_data)
            return
        elif text == "🔒 قفل اسپانسر" or text == "🔒 Force Subscribe":
            if not is_owner(user_id) and not has_permission(user_id, "can_manage_force_sub"):
                bot.send_message(chat_id, get_message("admin_no_permission", lang))
                return
            show_force_sub_settings(bot, chat_id)
            return
        elif text == "📋 مدیریت ادمین‌ها" or text == "📋 Manage Admins":
            if not is_owner(user_id) and not has_permission(user_id, "can_manage_admins"):
                bot.send_message(chat_id, get_message("admin_no_permission", lang))
                return
            show_admin_list(bot, chat_id, None, user_id)
            return
        elif text == "⚙️ تنظیمات ربات" or text == "⚙️ Settings":
            if not is_owner(user_id) and not has_permission(user_id, "can_manage_settings"):
                bot.send_message(chat_id, get_message("admin_no_permission", lang))
                return
            show_settings(bot, chat_id)
            return
    
    # ===== لینک اینستاگرام =====
    if text and 'instagram.com' in text:
        if get_rate_limit_enabled():
            seconds = get_rate_limit_seconds()
            if user_last_download is not None:
                last_download = user_last_download.get(user_id, 0)
                elapsed = time.time() - last_download
                if elapsed < seconds:
                    remaining = int(seconds - elapsed)
                    bot.send_message(
                        chat_id,
                        get_message("rate_limit_wait", lang).format(seconds=seconds, remaining=remaining)
                    )
                    return
        
        msg = bot.send_message(chat_id, get_message("downloading", lang))
        files, error = download_instagram_post(text, user_id)
        
        if not files:
            bot.edit_message_text(f"❌ {error}", chat_id, msg.message_id)
            return
        
        if user_last_download is not None:
            user_last_download[user_id] = time.time()
        
        for f in files:
            try:
                with open(f, 'rb') as media:
                    if f.endswith('.mp4'):
                        bot.send_video(chat_id, media, caption=get_message("caption", lang))
                    else:
                        bot.send_photo(chat_id, media, caption=get_message("caption", lang))
                    os.remove(f)
            except Exception as e:
                bot.send_message(chat_id, get_message("send_error", lang).format(error=str(e)))
        bot.delete_message(chat_id, msg.message_id)
    else:
        if not is_admin(user_id):
            bot.send_message(chat_id, get_message("invalid_link", lang))
