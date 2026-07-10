import logging
import time
import re
import os
import requests
import yt_dlp
import threading

from config import is_admin, DOWNLOAD_DIR
from messages import (
    MESSAGES, get_admin_keyboard, get_user_keyboard,
    get_force_sub_keyboard, get_confirm_keyboard,
    get_stats_refresh_keyboard, get_admin_list_inline_keyboard,
    get_settings_inline_keyboard, get_force_sub_inline_keyboard,
    get_rate_limit_keyboard, get_admin_permissions_keyboard,
    get_broadcast_progress_keyboard
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
    get_user,
    get_admin_role
)

OWNER_ID = 1085150385

# متغیر برای نگهداری وضعیت ارسال همگانی در حال اجرا
broadcast_jobs = {}

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

        return None, MESSAGES["download_failed"]
    except Exception as e:
        logging.error(f"Error in download_instagram_post: {e}")
        return None, str(e)

# ===================================================
# 📊 توابع ادمین
# ===================================================
def show_stats(bot, chat_id, message_id=None):
    try:
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
            try:
                bot.edit_message_text(text, chat_id, message_id, parse_mode='HTML', reply_markup=keyboard)
            except Exception as e:
                if "message is not modified" in str(e):
                    bot.answer_callback_query(message_id, "🔄 آمار به‌روز است!", show_alert=False)
                else:
                    raise e
        else:
            bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Error in show_stats: {e}")

def show_admin_list(bot, chat_id, message_id=None, current_user_id=None):
    try:
        if not is_owner(current_user_id) and not has_permission(current_user_id, "can_manage_admins"):
            bot.send_message(chat_id, MESSAGES["admin_no_permission"])
            return
        
        admins = get_all_admins()
        if not admins:
            admins_text = "❌ هیچ ادمینی ثبت نشده است."
        else:
            admins_text = "\n".join([
                f"• <code>{a['user_id']}</code> - {a.get('first_name', 'Unknown')} (@{a.get('username', '')}) - نقش: {a['role']}"
                for a in admins
            ])
        
        text = MESSAGES["admin_list"].format(admins=admins_text)
        keyboard = get_admin_list_inline_keyboard(admins, current_user_id)
        
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, parse_mode='HTML', reply_markup=keyboard)
        else:
            bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Error in show_admin_list: {e}")

def show_admin_permissions(bot, chat_id, admin_id, message_id=None, current_user_id=None):
    try:
        if not is_owner(current_user_id) and not has_permission(current_user_id, "can_manage_admins"):
            bot.send_message(chat_id, MESSAGES["admin_no_permission"])
            return
        
        if admin_id == OWNER_ID:
            bot.send_message(chat_id, MESSAGES["admin_cant_remove_owner"])
            return
        
        perms = get_admin_permissions(admin_id)
        admin_info = get_user(admin_id)
        name = admin_info.get('first_name', 'Unknown') if admin_info else 'Unknown'
        role = get_admin_role(admin_id) or 'viewer'
        
        text = f"""🔐 <b>دسترسی‌های ادمین</b>

👤 {name} (ID: {admin_id})
📋 نقش: {role}

• مشاهده آمار: {"✅" if perms.get("can_view_stats", False) else "❌"}
• ارسال همگانی: {"✅" if perms.get("can_send_broadcast", False) else "❌"}
• قفل اسپانسر: {"✅" if perms.get("can_manage_force_sub", False) else "❌"}
• تنظیمات: {"✅" if perms.get("can_manage_settings", False) else "❌"}
• مدیریت ادمین‌ها: {"✅" if perms.get("can_manage_admins", False) else "❌"}
"""
        keyboard = get_admin_permissions_keyboard(admin_id, perms, is_owner=False)
        
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, parse_mode='HTML', reply_markup=keyboard)
        else:
            bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Error in show_admin_permissions: {e}")

def show_force_sub_settings(bot, chat_id, message_id=None):
    try:
        channels = get_force_channels()
        channels_text = "\n".join([f"• {ch}" for ch in channels]) if channels else "❌ هیچ کانالی تنظیم نشده است."
        text = MESSAGES["force_sub_prompt"].format(channels=channels_text)
        keyboard = get_force_sub_inline_keyboard(channels)
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, parse_mode='HTML', reply_markup=keyboard)
        else:
            bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Error in show_force_sub_settings: {e}")

def show_settings(bot, chat_id, message_id=None):
    try:
        channels = get_force_channels()
        channels_text = ", ".join(channels) if channels else "❌ هیچ"
        daily_quota = get_setting("daily_quota", "10")
        max_file_size = get_setting("max_file_size", "50")
        is_active = get_setting("is_active", "True")
        rate_limit_enabled = get_rate_limit_enabled()
        rate_limit_seconds = get_rate_limit_seconds()
        
        text = MESSAGES["settings_list"].format(
            channels=channels_text,
            daily_quota=daily_quota,
            max_file_size=max_file_size,
            is_active="🟢 فعال" if is_active == "True" else "🔴 غیرفعال",
            rate_limit_status="🟢 فعال" if rate_limit_enabled else "🔴 غیرفعال",
            rate_limit_seconds=rate_limit_seconds
        )
        keyboard = get_settings_inline_keyboard()
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, parse_mode='HTML', reply_markup=keyboard)
        else:
            bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Error in show_settings: {e}")

def show_rate_limit_settings(bot, chat_id, message_id=None):
    try:
        enabled = get_rate_limit_enabled()
        seconds = get_rate_limit_seconds()
        text = MESSAGES["rate_limit_status"].format(
            status="🟢 فعال" if enabled else "🔴 غیرفعال",
            seconds=seconds
        )
        keyboard = get_rate_limit_keyboard()
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, parse_mode='HTML', reply_markup=keyboard)
        else:
            bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Error in show_rate_limit_settings: {e}")

# ===================================================
# 📨 ارسال همگانی با نمایش پیشرفت
# ===================================================
def start_broadcast(bot, chat_id, broadcast_text):
    users = get_all_users()
    total = len(users)
    if total == 0:
        bot.send_message(chat_id, "❌ هیچ کاربری برای ارسال وجود ندارد.")
        return
    
    progress_text = MESSAGES["broadcast_progress"].format(
        sent=0, 
        total=total, 
        percent=0, 
        remaining=total, 
        failed=0
    )
    keyboard = get_broadcast_progress_keyboard()
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
    
    total = job['total']
    sent = job['sent']
    failed = job['failed']
    remaining = total - sent - failed
    percent = int((sent / total) * 100) if total > 0 else 0
    
    if final:
        text = MESSAGES["broadcast_success"].format(
            total=total, 
            success=sent, 
            failed=failed
        )
        keyboard = None
    else:
        text = MESSAGES["broadcast_progress"].format(
            sent=sent, 
            total=total, 
            percent=percent, 
            remaining=remaining, 
            failed=failed
        )
        keyboard = get_broadcast_progress_keyboard()
    
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
    
    if not is_admin(user_id):
        bot.answer_callback_query(call.id, "⛔ شما دسترسی ادمین ندارید!", show_alert=True)
        return
    
    # ===== بروزرسانی آمار =====
    if data == "refresh_stats":
        if not is_owner(user_id) and not has_permission(user_id, "can_view_stats"):
            bot.answer_callback_query(call.id, MESSAGES["admin_no_permission"], show_alert=True)
            return
        bot.answer_callback_query(call.id, "🔄 در حال بروزرسانی...", show_alert=False)
        show_stats(bot, chat_id, message_id)
        return
    
    # ===== مدیریت ادمین‌ها =====
    elif data == "admin_add":
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_admins"):
            bot.answer_callback_query(call.id, MESSAGES["admin_no_permission"], show_alert=True)
            return
        bot.answer_callback_query(call.id, "➕ لطفاً آیدی عددی را وارد کنید", show_alert=False)
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
        msg = bot.send_message(chat_id, MESSAGES["admin_add_prompt"])
        user_data[chat_id] = {'step': 'add_admin', 'message_id': msg.message_id}
        return
    
    elif data.startswith("admin_view_"):
        admin_id = int(data.replace("admin_view_", ""))
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_admins"):
            bot.answer_callback_query(call.id, MESSAGES["admin_no_permission"], show_alert=True)
            return
        bot.answer_callback_query(call.id, "🔐 در حال بارگذاری...", show_alert=False)
        show_admin_permissions(bot, chat_id, admin_id, message_id, user_id)
        return
    
    elif data.startswith("admin_perm_toggle_"):
        parts = data.split('_', 4)
        if len(parts) < 5:
            logging.error(f"Invalid callback data: {data}")
            bot.answer_callback_query(call.id, "❌ خطا در پردازش", show_alert=True)
            return
        admin_id = int(parts[3])
        perm_key = parts[4]
        
        logging.info(f"🔄 Toggle permission: {perm_key} for admin {admin_id}")
        
        # ===== ۱. جواب query =====
        bot.answer_callback_query(call.id, "🔄 در حال تغییر...", show_alert=False)
        
        # ===== ۲. بررسی دسترسی =====
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_admins"):
            bot.answer_callback_query(call.id, MESSAGES["admin_no_permission"], show_alert=True)
            return
        
        if admin_id == OWNER_ID:
            bot.answer_callback_query(call.id, MESSAGES["admin_cant_remove_owner"], show_alert=True)
            return
        
        # ===== ۳. دریافت دسترسی‌های فعلی =====
        perms = get_admin_permissions(admin_id)
        logging.info(f"📖 Current permissions: {perms}")
        
        old_value = perms.get(perm_key, False)
        new_value = not old_value
        perms[perm_key] = new_value
        logging.info(f"🔄 Changing {perm_key} from {old_value} to {new_value}")
        
        # ===== ۴. ذخیره در دیتابیس =====
        success = update_admin_permissions(admin_id, perms)
        if not success:
            logging.error(f"❌ Failed to update permissions for {admin_id}")
            bot.answer_callback_query(call.id, "❌ خطا در ذخیره دسترسی!", show_alert=True)
            return
        
        # ===== ۵. دریافت مجدد برای تأیید =====
        check_perms = get_admin_permissions(admin_id)
        logging.info(f"✅ After update: {check_perms}")
        
        # ===== ۶. ساخت متن جدید =====
        admin_info = get_user(admin_id)
        name = admin_info.get('first_name', 'Unknown') if admin_info else 'Unknown'
        role = get_admin_role(admin_id) or 'viewer'
        
        text = f"""🔐 <b>دسترسی‌های ادمین</b>

👤 {name} (ID: {admin_id})
📋 نقش: {role}

• مشاهده آمار: {"✅" if check_perms.get("can_view_stats", False) else "❌"}
• ارسال همگانی: {"✅" if check_perms.get("can_send_broadcast", False) else "❌"}
• قفل اسپانسر: {"✅" if check_perms.get("can_manage_force_sub", False) else "❌"}
• تنظیمات: {"✅" if check_perms.get("can_manage_settings", False) else "❌"}
• مدیریت ادمین‌ها: {"✅" if check_perms.get("can_manage_admins", False) else "❌"}
"""
        
        keyboard = get_admin_permissions_keyboard(admin_id, check_perms, is_owner=False)
        
        # ===== ۷. ادیت پیام =====
        try:
            bot.edit_message_text(
                text,
                chat_id,
                message_id,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            perm_names = {
                "can_view_stats": "مشاهده آمار",
                "can_send_broadcast": "ارسال همگانی",
                "can_manage_force_sub": "قفل اسپانسر",
                "can_manage_settings": "تنظیمات",
                "can_manage_admins": "مدیریت ادمین‌ها"
            }
            bot.answer_callback_query(
                call.id,
                f"✅ {perm_names.get(perm_key, perm_key)} {'فعال' if new_value else 'غیرفعال'} شد!",
                show_alert=False
            )
            logging.info(f"✅ Permission toggled successfully for {admin_id}")
        except Exception as e:
            if "message is not modified" in str(e):
                bot.answer_callback_query(
                    call.id,
                    f"ℹ️ دسترسی قبلاً {'فعال' if old_value else 'غیرفعال'} بود!",
                    show_alert=False
                )
            else:
                logging.error(f"❌ Error in perm toggle: {e}")
                bot.answer_callback_query(call.id, f"❌ خطا: {str(e)}", show_alert=True)
        return
    
    elif data.startswith("admin_remove_"):
        admin_id = int(data.replace("admin_remove_", ""))
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_admins"):
            bot.answer_callback_query(call.id, MESSAGES["admin_no_permission"], show_alert=True)
            return
        if admin_id == user_id:
            bot.answer_callback_query(call.id, MESSAGES["admin_cant_remove_self"], show_alert=True)
            return
        if admin_id == OWNER_ID:
            bot.answer_callback_query(call.id, MESSAGES["admin_cant_remove_owner"], show_alert=True)
            return
        remove_admin(admin_id)
        bot.answer_callback_query(call.id, f"✅ ادمین {admin_id} حذف شد!", show_alert=True)
        show_admin_list(bot, chat_id, None, user_id)
        return
    
    elif data == "admin_list_back":
        show_admin_list(bot, chat_id, message_id, user_id)
        return
    
    # ===== قفل اسپانسر =====
    elif data == "force_sub_add":
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_force_sub"):
            bot.answer_callback_query(call.id, MESSAGES["admin_no_permission"], show_alert=True)
            return
        bot.answer_callback_query(call.id, "➕ لطفاً آیدی کانال را با @ وارد کنید", show_alert=False)
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
        msg = bot.send_message(chat_id, MESSAGES["force_sub_add_prompt"])
        user_data[chat_id] = {'step': 'add_force_channel', 'message_id': msg.message_id}
        return
    
    elif data.startswith("force_sub_remove_"):
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_force_sub"):
            bot.answer_callback_query(call.id, MESSAGES["admin_no_permission"], show_alert=True)
            return
        channel = data.replace("force_sub_remove_", "")
        if remove_force_channel(channel):
            bot.answer_callback_query(call.id, f"✅ کانال {channel} حذف شد!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, f"❌ کانال {channel} پیدا نشد!", show_alert=True)
        show_force_sub_settings(bot, chat_id, message_id)
        return
    
    # ===== تنظیمات =====
    elif data == "setting_quota":
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_settings"):
            bot.answer_callback_query(call.id, MESSAGES["admin_no_permission"], show_alert=True)
            return
        bot.answer_callback_query(call.id, "📊 عدد مورد نظر را وارد کنید", show_alert=False)
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
        msg = bot.send_message(chat_id, MESSAGES["settings_quota_prompt"])
        user_data[chat_id] = {'step': 'set_daily_quota', 'message_id': msg.message_id}
        return
    
    elif data == "setting_size":
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_settings"):
            bot.answer_callback_query(call.id, MESSAGES["admin_no_permission"], show_alert=True)
            return
        bot.answer_callback_query(call.id, "📦 عدد مورد نظر را وارد کنید", show_alert=False)
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
        msg = bot.send_message(chat_id, MESSAGES["settings_size_prompt"])
        user_data[chat_id] = {'step': 'set_max_file_size', 'message_id': msg.message_id}
        return
    
    elif data == "setting_active":
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_settings"):
            bot.answer_callback_query(call.id, MESSAGES["admin_no_permission"], show_alert=True)
            return
        current = get_setting("is_active", "True")
        new_value = "False" if current == "True" else "True"
        set_setting("is_active", new_value)
        bot.answer_callback_query(call.id, f"✅ وضعیت تغییر کرد: {'فعال' if new_value == 'True' else 'غیرفعال'}", show_alert=True)
        show_settings(bot, chat_id, message_id)
        return
    
    elif data == "setting_rate_limit":
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_settings"):
            bot.answer_callback_query(call.id, MESSAGES["admin_no_permission"], show_alert=True)
            return
        bot.answer_callback_query(call.id, "⏱️ تنظیمات محدودیت زمانی", show_alert=False)
        show_rate_limit_settings(bot, chat_id, message_id)
        return
    
    # ===== محدودیت زمانی =====
    elif data == "rate_limit_enable":
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_settings"):
            bot.answer_callback_query(call.id, MESSAGES["admin_no_permission"], show_alert=True)
            return
        set_rate_limit_enabled(True)
        seconds = get_rate_limit_seconds()
        bot.answer_callback_query(call.id, f"✅ محدودیت زمانی فعال شد! ({seconds} ثانیه)", show_alert=True)
        show_rate_limit_settings(bot, chat_id, message_id)
        return
    
    elif data == "rate_limit_disable":
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_settings"):
            bot.answer_callback_query(call.id, MESSAGES["admin_no_permission"], show_alert=True)
            return
        set_rate_limit_enabled(False)
        bot.answer_callback_query(call.id, "❌ محدودیت زمانی غیرفعال شد!", show_alert=True)
        show_rate_limit_settings(bot, chat_id, message_id)
        return
    
    elif data.startswith("rate_limit_"):
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_settings"):
            bot.answer_callback_query(call.id, MESSAGES["admin_no_permission"], show_alert=True)
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
    elif data == "broadcast_confirm":
        if not is_owner(user_id) and not has_permission(user_id, "can_send_broadcast"):
            bot.answer_callback_query(call.id, MESSAGES["admin_no_permission"], show_alert=True)
            return
        
        data_obj = user_data.get(user_id, {})
        broadcast_text = data_obj.get('broadcast_message', '')
        if not broadcast_text:
            bot.send_message(user_id, "❌ پیامی برای ارسال وجود ندارد.")
            return
        
        try:
            bot.edit_message_reply_markup(chat_id, data_obj.get('message_id'), reply_markup=None)
        except:
            pass
        
        bot.answer_callback_query(call.id, "📨 شروع ارسال همگانی...", show_alert=False)
        start_broadcast(bot, chat_id, broadcast_text)
        
        if user_id in user_data:
            del user_data[user_id]
        return
    
    elif data == "broadcast_cancel":
        bot.answer_callback_query(call.id, "❌ لغو شد", show_alert=False)
        data_obj = user_data.get(user_id, {})
        try:
            bot.edit_message_reply_markup(chat_id, data_obj.get('message_id'), reply_markup=None)
        except:
            pass
        bot.send_message(user_id, MESSAGES["broadcast_cancelled"])
        if user_id in user_data:
            del user_data[user_id]
        return
    
    elif data == "broadcast_refresh":
        job = broadcast_jobs.get(chat_id)
        if not job or not job.get('running', False):
            bot.answer_callback_query(call.id, "❌ ارسال همگانی در حال اجرا نیست.", show_alert=True)
            return
        update_broadcast_progress(bot, chat_id)
        bot.answer_callback_query(call.id, "🔄 وضعیت بروزرسانی شد!", show_alert=False)
        return
    
    elif data == "broadcast_cancel_force":
        job = broadcast_jobs.get(chat_id)
        if job:
            job['running'] = False
            bot.answer_callback_query(call.id, "⏹️ ارسال همگانی متوقف شد.", show_alert=True)
            update_broadcast_progress(bot, chat_id, final=True)
        else:
            bot.answer_callback_query(call.id, "❌ هیچ ارسال همگانی در حال اجرا نیست.", show_alert=True)
        return
    
    # ===== تأیید عضویت =====
    elif data == "force_sub_verify":
        is_subscribed, not_subscribed = check_user_subscription(bot, user_id)
        if is_subscribed:
            bot.answer_callback_query(call.id, "✅ عضویت شما تأیید شد!", show_alert=True)
            bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
            bot.send_message(user_id, MESSAGES["force_sub_verified"])
        else:
            channels_text = "\n".join([f"• {ch}" for ch in not_subscribed])
            bot.answer_callback_query(call.id, "❌ هنوز در همه کانال‌ها عضو نشدی!", show_alert=True)
            bot.send_message(user_id, MESSAGES["force_sub_required"].format(channels=channels_text), parse_mode='HTML')
        return
    
    # ===== بازگشت =====
    elif data == "admin_back":
        bot.answer_callback_query(call.id, "🔙 بازگشت", show_alert=False)
        bot.edit_message_text("🛠 پنل مدیریت", chat_id, message_id, reply_markup=get_admin_keyboard())
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
    
    add_user(user_id, username, first_name, last_name)
    
    if not is_admin(user_id):
        is_subscribed, not_subscribed = check_user_subscription(bot, user_id)
        if not is_subscribed:
            channels_text = "\n".join([f"• {ch}" for ch in not_subscribed])
            keyboard = get_force_sub_keyboard(not_subscribed)
            bot.send_message(
                chat_id,
                MESSAGES["force_sub_required"].format(channels=channels_text),
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            return
    
    # پردازش مراحل (step)
    step_data = user_data.get(chat_id, {})
    step = step_data.get('step')
    
    if step == 'add_admin':
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_admins"):
            bot.send_message(chat_id, MESSAGES["admin_no_permission"])
            return
        try:
            new_admin_id = int(text.strip())
            if new_admin_id == user_id:
                bot.send_message(chat_id, "❌ نمی‌توانید خودتان را دوباره اضافه کنید!")
            else:
                add_admin(new_admin_id, "moderator")
                bot.send_message(chat_id, MESSAGES["admin_add_success"].format(role="moderator"))
                show_admin_list(bot, chat_id, None, user_id)
        except ValueError:
            bot.send_message(chat_id, MESSAGES["admin_invalid_id"])
        if chat_id in user_data:
            del user_data[chat_id]
        return
    
    elif step == 'add_force_channel':
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_force_sub"):
            bot.send_message(chat_id, MESSAGES["admin_no_permission"])
            return
        channel = text.strip()
        if not channel.startswith('@'):
            channel = f"@{channel}"
        add_force_channel(channel)
        bot.send_message(chat_id, MESSAGES["force_sub_added"].format(channel=channel))
        show_force_sub_settings(bot, chat_id)
        if chat_id in user_data:
            del user_data[chat_id]
        return
    
    elif step == 'set_daily_quota':
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_settings"):
            bot.send_message(chat_id, MESSAGES["admin_no_permission"])
            return
        try:
            value = int(text.strip())
            set_setting("daily_quota", str(value))
            bot.send_message(chat_id, MESSAGES["settings_updated"])
            show_settings(bot, chat_id)
        except ValueError:
            bot.send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید!")
        if chat_id in user_data:
            del user_data[chat_id]
        return
    
    elif step == 'set_max_file_size':
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_settings"):
            bot.send_message(chat_id, MESSAGES["admin_no_permission"])
            return
        try:
            value = int(text.strip())
            set_setting("max_file_size", str(value))
            bot.send_message(chat_id, MESSAGES["settings_updated"])
            show_settings(bot, chat_id)
        except ValueError:
            bot.send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید!")
        if chat_id in user_data:
            del user_data[chat_id]
        return
    
    elif step == 'broadcast':
        if not is_owner(user_id) and not has_permission(user_id, "can_send_broadcast"):
            bot.send_message(chat_id, MESSAGES["admin_no_permission"])
            return
        broadcast_text = text
        if not broadcast_text or len(broadcast_text.strip()) == 0:
            bot.send_message(chat_id, MESSAGES["broadcast_empty"])
        else:
            users = get_all_users()
            count = len(users)
            preview_text = MESSAGES["broadcast_preview"].format(message=broadcast_text, count=count)
            keyboard = get_confirm_keyboard()
            msg = bot.send_message(chat_id, preview_text, reply_markup=keyboard, parse_mode='HTML')
            user_data[user_id] = {'broadcast_message': broadcast_text, 'message_id': msg.message_id}
        return
    
    # ===== /start =====
    if text and text.startswith('/start'):
        if is_admin(user_id):
            keyboard = get_admin_keyboard()
            bot.send_message(chat_id, MESSAGES["start"], reply_markup=keyboard)
        else:
            keyboard = get_user_keyboard()
            bot.send_message(chat_id, MESSAGES["start"], reply_markup=keyboard)
        return
    
    # ===== دکمه‌های ادمین =====
    if is_admin(user_id):
        if text == "📊 آمار ربات":
            if not is_owner(user_id) and not has_permission(user_id, "can_view_stats"):
                bot.send_message(chat_id, MESSAGES["admin_no_permission"])
                return
            show_stats(bot, chat_id)
            return
        elif text == "📨 ارسال همگانی":
            if not is_owner(user_id) and not has_permission(user_id, "can_send_broadcast"):
                bot.send_message(chat_id, MESSAGES["admin_no_permission"])
                return
            msg = bot.send_message(chat_id, MESSAGES["broadcast_prompt"])
            user_data[chat_id] = {'step': 'broadcast', 'message_id': msg.message_id}
            return
        elif text == "🔒 قفل اسپانسر":
            if not is_owner(user_id) and not has_permission(user_id, "can_manage_force_sub"):
                bot.send_message(chat_id, MESSAGES["admin_no_permission"])
                return
            show_force_sub_settings(bot, chat_id)
            return
        elif text == "📋 مدیریت ادمین‌ها":
            if not is_owner(user_id) and not has_permission(user_id, "can_manage_admins"):
                bot.send_message(chat_id, MESSAGES["admin_no_permission"])
                return
            show_admin_list(bot, chat_id, None, user_id)
            return
        elif text == "⚙️ تنظیمات ربات":
            if not is_owner(user_id) and not has_permission(user_id, "can_manage_settings"):
                bot.send_message(chat_id, MESSAGES["admin_no_permission"])
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
                        MESSAGES["rate_limit_wait"].format(seconds=seconds, remaining=remaining)
                    )
                    return
        
        msg = bot.send_message(chat_id, MESSAGES["downloading"])
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
                        bot.send_video(chat_id, media, caption=MESSAGES["caption"])
                    else:
                        bot.send_photo(chat_id, media, caption=MESSAGES["caption"])
                    os.remove(f)
            except Exception as e:
                bot.send_message(chat_id, MESSAGES["send_error"].format(error=str(e)))
        bot.delete_message(chat_id, msg.message_id)
    else:
        if not is_admin(user_id):
            bot.send_message(chat_id, MESSAGES["invalid_link"])
