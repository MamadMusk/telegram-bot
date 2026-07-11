import logging
import time
import re
import os
import requests
import yt_dlp
import threading
import inspect
from datetime import datetime, timezone
from telebot.types import MenuButtonCommands, InlineKeyboardMarkup, InlineKeyboardButton

from config import is_admin, DOWNLOAD_DIR
from messages import (
    MESSAGES, MESSAGES_FA, MESSAGES_EN, get_message,
    get_admin_keyboard, get_user_keyboard,
    get_force_sub_keyboard, get_force_sub_inline_keyboard,
    get_confirm_keyboard, get_broadcast_cancel_keyboard,
    get_broadcast_progress_keyboard,
    get_stats_refresh_keyboard, get_report_keyboard,
    get_admin_list_inline_keyboard,
    get_settings_inline_keyboard, get_settings_new_keyboard,
    get_rate_limit_keyboard, get_admin_permissions_keyboard,
    get_admin_inline_keyboard, get_language_keyboard,
    get_premium_list_inline_keyboard, get_premium_user_settings_keyboard,
    get_cancel_keyboard,
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
    get_admin_role, get_all_premium_users, get_premium_settings,
    set_premium_status, remove_premium_user, get_premium_user_details,
    is_premium_user, get_user_daily_quota, get_user_max_file_size,
    get_user_rate_limit, is_user_exempt_from_force_subscribe,
    set_admin_expire, is_admin_expired, check_quota,
    get_new_users_today, get_failed_downloads_today, get_conn
)

# ===== اضافه کردن تابع دانلود جدید از downloader.py =====
from downloader import download_media, detect_platform, get_platform_icon

OWNER_ID = 1085150385

# متغیر برای نگهداری وضعیت ارسال همگانی در حال اجرا
broadcast_jobs = {}

logger = logging.getLogger(__name__)

# ===================================================
# 📩 تابع ارسال پیام خوش‌آمدگویی
# ===================================================
def send_welcome_message(bot, chat_id, user_id, lang=None):
    if lang is None:
        try:
            lang = get_user_language(user_id) or "fa"
        except:
            lang = "fa"
    if is_admin(user_id):
        keyboard = get_admin_keyboard(lang)
    else:
        keyboard = get_user_keyboard()
    try:
        bot.send_message(chat_id, get_message("start", lang), reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in send_welcome_message: {e}")

# ===================================================
# 🔒 توابع بررسی عضویت و مجوزها
# ===================================================
def get_force_channels():
    return get_force_channels_list()

def check_user_subscription(bot, user_id):
    if is_user_exempt_from_force_subscribe(user_id):
        return True, []
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
            logger.error(f"Error checking subscription for {channel}: {e}")
            not_subscribed.append(channel)
    return len(not_subscribed) == 0, not_subscribed

def has_permission(user_id, permission):
    try:
        perms = get_admin_permissions(user_id)
        result = perms.get(permission, False)
        logger.info(f"🔍 Permission check: {permission} for {user_id} = {result}")
        return result
    except:
        return False

def is_owner(user_id):
    return user_id == OWNER_ID

# ===================================================
# 📋 تولید گزارش روزانه
# ===================================================
def generate_daily_report():
    try:
        stats = get_stats()
        total_downloads = get_total_downloads()
        premium_users = get_all_premium_users()
        admins = get_all_admins()
        new_users_today = get_new_users_today()
        failed_downloads = get_failed_downloads_today()
        
        report = f"""📊 <b>گزارش روزانه ربات</b>

📅 تاریخ: {datetime.now().strftime('%Y/%m/%d')}
⏰ زمان: {datetime.now().strftime('%H:%M')}

👥 <b>آمار کاربران:</b>
• کل کاربران: {stats['users']}
• کاربران جدید امروز: {new_users_today}
• کاربران ویژه: {len(premium_users)}
• ادمین‌ها: {len(admins)}

📥 <b>آمار دانلودها:</b>
• کل دانلودها: {total_downloads}
• دانلودهای امروز: {stats['today_downloads']}
• دانلودهای ناموفق امروز: {failed_downloads}

👑 <b>کاربران ویژه فعال:</b>
"""
        if premium_users:
            for user in premium_users[:10]:
                name = user.get('first_name', 'Unknown')
                username = user.get('username', '')
                days_left = user.get('days_left')
                days_text = f"({days_left} روز مانده)" if days_left is not None else "(همیشه)"
                report += f"• {name} (@{username}) {days_text}\n"
            if len(premium_users) > 10:
                report += f"... و {len(premium_users) - 10} کاربر دیگر\n"
        else:
            report += "• هیچ کاربر ویژه‌ای فعال نیست.\n"
        
        report += f"""
📊 <b>وضعیت ربات:</b>
• وضعیت: {'🟢 فعال' if get_setting('is_active', 'True') == 'True' else '🔴 غیرفعال'}
• سقف دانلود روزانه: {get_setting('daily_quota', '10')}
• محدودیت زمانی: {'فعال' if get_rate_limit_enabled() else 'غیرفعال'} ({get_rate_limit_seconds()} ثانیه)
"""
        return report
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return "❌ خطا در تولید گزارش"

def send_daily_report(bot, chat_id, lang="fa"):
    report = generate_daily_report()
    keyboard = get_report_keyboard(lang)
    bot.send_message(chat_id, report, parse_mode='HTML', reply_markup=keyboard)

# ===================================================
# 📊 توابع ادمین (با پشتیبانی از زبان و Premium)
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
            downloads=total_downloads,
            premium_users=stats.get('premium_users', 0)
        )
        keyboard = get_stats_refresh_keyboard(lang)
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
        logger.error(f"Error in show_stats: {e}")

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
        logger.error(f"Error in show_admin_list: {e}")

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
        text = get_message("admin_permissions_header", lang).format(
            name=name,
            user_id=admin_id,
            role=role,
            stats="✅" if perms.get("can_view_stats", False) else "❌",
            broadcast="✅" if perms.get("can_send_broadcast", False) else "❌",
            force_sub="✅" if perms.get("can_manage_force_sub", False) else "❌",
            settings="✅" if perms.get("can_manage_settings", False) else "❌",
            admins="✅" if perms.get("can_manage_admins", False) else "❌",
            premium="✅" if perms.get("can_manage_premium", False) else "❌"
        )
        keyboard = get_admin_permissions_keyboard(admin_id, perms, is_owner=False, lang=lang)
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, parse_mode='HTML', reply_markup=keyboard)
        else:
            bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in show_admin_permissions: {e}")

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
        logger.error(f"Error in show_force_sub_settings: {e}")

def show_premium_users(bot, chat_id, message_id=None, current_user_id=None):
    try:
        lang = get_user_language(current_user_id) or "fa"
        if not is_owner(current_user_id) and not has_permission(current_user_id, "can_manage_premium"):
            bot.send_message(chat_id, get_message("admin_no_permission", lang))
            return
        premium_users = get_all_premium_users()
        if not premium_users:
            users_text = "❌ هیچ کاربر ویژه‌ای ثبت نشده است."
        else:
            users_text = "\n".join([
                f"• <code>{u['id']}</code> - {u.get('first_name', 'Unknown')} (@{u.get('username', '')}) - {'🟢 فعال' if u.get('days_left') is None or u.get('days_left') > 0 else '⏳ منقضی'}"
                for u in premium_users
            ])
        text = get_message("premium_users_list", lang).format(users=users_text)
        keyboard = get_premium_list_inline_keyboard(premium_users, current_user_id, lang)
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, parse_mode='HTML', reply_markup=keyboard)
        else:
            bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in show_premium_users: {e}")

def show_premium_user_settings(bot, chat_id, premium_user_id, message_id=None, current_user_id=None):
    try:
        lang = get_user_language(current_user_id) or "fa"
        if not is_owner(current_user_id) and not has_permission(current_user_id, "can_manage_premium"):
            bot.send_message(chat_id, get_message("admin_no_permission", lang))
            return
        user_details = get_premium_user_details(premium_user_id)
        if not user_details:
            bot.send_message(chat_id, get_message("premium_not_found", lang))
            return
        settings = get_premium_settings(premium_user_id)
        name = user_details.get('first_name', 'Unknown')
        joined_date = user_details.get('joined_date', 'N/A')
        status = "🟢 فعال" if settings.get('is_premium') else "🔴 غیرفعال"
        expire_date = settings.get('premium_expire', 'نامحدود')
        daily_quota = settings.get('premium_daily_quota', 'پیش‌فرض')
        file_size = settings.get('premium_max_file_size', 'پیش‌فرض')
        rate_limit = settings.get('premium_rate_limit', 'پیش‌فرض')
        text = get_message("premium_user_settings", lang).format(
            name=name,
            user_id=premium_user_id,
            joined_date=joined_date,
            status=status,
            expire_date=expire_date,
            daily_quota=daily_quota,
            file_size=file_size,
            rate_limit=rate_limit
        )
        keyboard = get_premium_user_settings_keyboard(premium_user_id, settings, lang)
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, parse_mode='HTML', reply_markup=keyboard)
        else:
            bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in show_premium_user_settings: {e}")

# ===================================================
# 📊 تنظیمات جدید
# ===================================================
def show_settings(bot, chat_id, message_id=None):
    try:
        lang = get_user_language(chat_id) or "fa"
        daily_quota = get_setting("daily_quota", "10")
        max_file_size = get_setting("max_file_size", "50")
        is_active = get_setting("is_active", "True") == "True"
        rate_limit_enabled = get_rate_limit_enabled()
        rate_limit_seconds = get_rate_limit_seconds()
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
        logger.error(f"Error in show_settings: {e}")

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
        logger.error(f"Error in show_rate_limit_settings: {e}")

# ===================================================
# 📨 ارسال همگانی
# ===================================================
def start_broadcast(bot, chat_id, user_data=None):
    try:
        logger.info(f"📨 start_broadcast called for {chat_id}")
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
        logger.info(f"✅ start_broadcast set step for {chat_id}")
    except Exception as e:
        logger.error(f"❌ Error in start_broadcast: {e}")

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
                logger.info(f"✅ Broadcast sent to {user['id']}")
            except Exception as e:
                job['failed'] += 1
                logger.error(f"❌ Broadcast failed to {user['id']}: {e}")
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
        logger.error(f"Error updating broadcast progress: {e}")

# ===================================================
# 📞 پردازش Callback (دکمه‌های شیشه‌ای)
# ===================================================
def handle_callback_query(bot, call, user_data):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    data = call.data
    logger.info(f"📞 Callback: {data} from {user_id}")
    
    # ===== انتخاب زبان =====
    if data == "lang_fa":
        set_user_language(user_id, "fa")
        bot.answer_callback_query(call.id, MESSAGES_FA.get("lang_changed", "زبان تغییر کرد."), show_alert=True)
        try:
            bot.set_my_commands(COMMANDS_FA)
            bot.set_chat_menu_button(chat_id, menu_button=MenuButtonCommands())
            logger.info("✅ کامندها به فارسی تغییر کرد و دکمه‌ی منو تنظیم شد")
        except Exception as e:
            logger.error(f"❌ خطا در تغییر کامندها: {e}")
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
        send_welcome_message(bot, chat_id, user_id, "fa")
        return
    elif data == "lang_en":
        set_user_language(user_id, "en")
        bot.answer_callback_query(call.id, MESSAGES_EN.get("lang_changed_en", "Language changed."), show_alert=True)
        try:
            bot.set_my_commands(COMMANDS_EN)
            bot.set_chat_menu_button(chat_id, menu_button=MenuButtonCommands())
            logger.info("✅ Commands changed to English and menu button set")
        except Exception as e:
            logger.error(f"❌ Error changing commands: {e}")
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
        send_welcome_message(bot, chat_id, user_id, "en")
        return
    
    # ===== دکمه لغو =====
    elif data == "cancel_action":
        lang = get_user_language(user_id) or "fa"
        bot.answer_callback_query(call.id, "❌ عملیات لغو شد.", show_alert=True)
        if chat_id in user_data:
            msg_id = user_data[chat_id].get('message_id')
            if msg_id:
                try:
                    bot.delete_message(chat_id, msg_id)
                except:
                    pass
            del user_data[chat_id]
        if hasattr(bot, 'user_data') and chat_id in bot.user_data:
            del bot.user_data[chat_id]
        bot.send_message(chat_id, get_message("broadcast_cancelled", lang))
        return
    
    # ===== جابجایی بین لیست ادمین‌ها و ویژه =====
    elif data == "switch_to_premium":
        bot.answer_callback_query(call.id, "👑 کاربران ویژه", show_alert=False)
        show_premium_users(bot, chat_id, message_id, user_id)
        return
    elif data == "switch_to_admins":
        bot.answer_callback_query(call.id, "📋 ادمین‌ها", show_alert=False)
        show_admin_list(bot, chat_id, message_id, user_id)
        return
    
    # ===== بقیه عملیات فقط برای ادمین‌ها =====
    if not is_admin(user_id):
        bot.answer_callback_query(call.id, "⛔ شما دسترسی ادمین ندارید!", show_alert=True)
        return
    
    # ===== منوی اصلی مدیریت =====
    if data == "admin_stats":
        bot.answer_callback_query(call.id, "📊 آماده...", show_alert=False)
        show_stats(bot, chat_id, message_id)
        return
    elif data == "admin_report":
        bot.answer_callback_query(call.id, "📋 گزارش روزانه", show_alert=False)
        send_daily_report(bot, chat_id, get_user_language(user_id) or "fa")
        return
    elif data == "refresh_report":
        bot.answer_callback_query(call.id, "🔄 در حال بروزرسانی گزارش...", show_alert=False)
        send_daily_report(bot, chat_id, get_user_language(user_id) or "fa")
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
        bot.answer_callback_query(call.id, "📋 مدیریت کاربران", show_alert=False)
        show_admin_list(bot, chat_id, message_id, user_id)
        return
    elif data == "admin_premium":
        bot.answer_callback_query(call.id, "👑 کاربران ویژه", show_alert=False)
        show_premium_users(bot, chat_id, message_id, user_id)
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
    
    # ===== آمار و بروزرسانی =====
    elif data == "refresh_stats":
        bot.answer_callback_query(call.id, "🔄 در حال بروزرسانی...", show_alert=False)
        show_stats(bot, chat_id, message_id)
        return
    
    # ===== مدیریت ادمین‌ها =====
    elif data == "admin_add":
        lang = get_user_language(user_id) or "fa"
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_admins"):
            bot.answer_callback_query(call.id, get_message("admin_no_permission", lang), show_alert=True)
            return
        bot.answer_callback_query(call.id, "➕ لطفاً آیدی عددی را وارد کنید", show_alert=False)
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
        msg = bot.send_message(chat_id, get_message("admin_add_prompt", lang), reply_markup=get_cancel_keyboard(lang))
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
            logger.error(f"Invalid callback data: {data}")
            return
        admin_id = int(parts[3])
        perm_key = parts[4]
        lang = get_user_language(user_id) or "fa"
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
        show_admin_permissions(bot, chat_id, admin_id, message_id, user_id)
        return
    elif data.startswith("admin_expire_"):
        admin_id = int(data.replace("admin_expire_", ""))
        lang = get_user_language(user_id) or "fa"
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_admins"):
            bot.answer_callback_query(call.id, get_message("admin_no_permission", lang), show_alert=True)
            return
        if admin_id == OWNER_ID:
            bot.answer_callback_query(call.id, get_message("admin_cant_remove_owner", lang), show_alert=True)
            return
        bot.answer_callback_query(call.id, "📆 تعداد روزهای اعتبار را وارد کنید (0 برای همیشه):", show_alert=False)
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
        msg = bot.send_message(chat_id, get_message("premium_expire_prompt", lang))
        user_data[chat_id] = {'step': 'admin_expire', 'admin_id': admin_id, 'message_id': msg.message_id}
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
    
    # ===== مدیریت کاربران ویژه =====
    elif data == "premium_add":
        lang = get_user_language(user_id) or "fa"
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_premium"):
            bot.answer_callback_query(call.id, get_message("admin_no_permission", lang), show_alert=True)
            return
        bot.answer_callback_query(call.id, "➕ آیدی کاربر جدید را برای افزودن به ویژه وارد کنید:", show_alert=False)
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
        msg = bot.send_message(chat_id, get_message("premium_add_prompt", lang), reply_markup=get_cancel_keyboard(lang))
        user_data[chat_id] = {'step': 'add_premium', 'message_id': msg.message_id}
        return
    elif data.startswith("premium_view_"):
        premium_user_id = int(data.replace("premium_view_", ""))
        lang = get_user_language(user_id) or "fa"
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_premium"):
            bot.answer_callback_query(call.id, get_message("admin_no_permission", lang), show_alert=True)
            return
        bot.answer_callback_query(call.id, "👑 در حال بارگذاری...", show_alert=False)
        show_premium_user_settings(bot, chat_id, premium_user_id, message_id, user_id)
        return
    elif data.startswith("premium_toggle_"):
        premium_user_id = int(data.replace("premium_toggle_", ""))
        lang = get_user_language(user_id) or "fa"
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_premium"):
            bot.answer_callback_query(call.id, get_message("admin_no_permission", lang), show_alert=True)
            return
        settings = get_premium_settings(premium_user_id)
        new_status = not settings.get('is_premium', False)
        set_premium_status(premium_user_id, new_status)
        bot.answer_callback_query(call.id, get_message("premium_toggle_success", lang), show_alert=True)
        show_premium_user_settings(bot, chat_id, premium_user_id, message_id, user_id)
        return
    elif data.startswith("premium_expire_"):
        premium_user_id = int(data.replace("premium_expire_", ""))
        lang = get_user_language(user_id) or "fa"
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_premium"):
            bot.answer_callback_query(call.id, get_message("admin_no_permission", lang), show_alert=True)
            return
        bot.answer_callback_query(call.id, "📆 تعداد روزهای اعتبار را وارد کنید (0 برای همیشه):", show_alert=False)
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
        msg = bot.send_message(chat_id, get_message("premium_expire_prompt", lang))
        user_data[chat_id] = {'step': 'premium_expire', 'premium_user_id': premium_user_id, 'message_id': msg.message_id}
        return
    elif data.startswith("premium_quota_"):
        premium_user_id = int(data.replace("premium_quota_", ""))
        lang = get_user_language(user_id) or "fa"
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_premium"):
            bot.answer_callback_query(call.id, get_message("admin_no_permission", lang), show_alert=True)
            return
        bot.answer_callback_query(call.id, get_message("premium_quota_prompt", lang), show_alert=False)
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
        msg = bot.send_message(chat_id, get_message("premium_quota_prompt", lang))
        user_data[chat_id] = {'step': 'premium_quota', 'premium_user_id': premium_user_id, 'message_id': msg.message_id}
        return
    elif data.startswith("premium_size_"):
        premium_user_id = int(data.replace("premium_size_", ""))
        lang = get_user_language(user_id) or "fa"
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_premium"):
            bot.answer_callback_query(call.id, get_message("admin_no_permission", lang), show_alert=True)
            return
        bot.answer_callback_query(call.id, get_message("premium_size_prompt", lang), show_alert=False)
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
        msg = bot.send_message(chat_id, get_message("premium_size_prompt", lang))
        user_data[chat_id] = {'step': 'premium_size', 'premium_user_id': premium_user_id, 'message_id': msg.message_id}
        return
    elif data.startswith("premium_rate_"):
        premium_user_id = int(data.replace("premium_rate_", ""))
        lang = get_user_language(user_id) or "fa"
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_premium"):
            bot.answer_callback_query(call.id, get_message("admin_no_permission", lang), show_alert=True)
            return
        bot.answer_callback_query(call.id, get_message("premium_rate_prompt", lang), show_alert=False)
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
        msg = bot.send_message(chat_id, get_message("premium_rate_prompt", lang))
        user_data[chat_id] = {'step': 'premium_rate', 'premium_user_id': premium_user_id, 'message_id': msg.message_id}
        return
    elif data.startswith("premium_remove_"):
        premium_user_id = int(data.replace("premium_remove_", ""))
        lang = get_user_language(user_id) or "fa"
        if not is_owner(user_id) and not has_permission(user_id, "can_manage_premium"):
            bot.answer_callback_query(call.id, get_message("admin_no_permission", lang), show_alert=True)
            return
        remove_premium_user(premium_user_id)
        bot.answer_callback_query(call.id, get_message("premium_remove_success", lang), show_alert=True)
        show_premium_users(bot, chat_id, None, user_id)
        return
    elif data == "premium_list_back":
        bot.answer_callback_query(call.id, "🔙 بازگشت", show_alert=False)
        show_premium_users(bot, chat_id, message_id, user_id)
        return
    
    # ===== تنظیمات =====
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
    
    # ===== محدودیت زمانی =====
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
            logger.warning(f"Editing message failed, sending new one: {e}")
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
    
    # ===== dummy =====
    elif data == "dummy":
        bot.answer_callback_query(call.id, "ℹ️ این دکمه فقط برای نمایش است.", show_alert=False)
        return

# ===================================================
# 📨 پردازش پیام (نسخه نهایی با لاگ و مدیریت خطا)
# ===================================================
def handle_message(bot, message, user_data, user_last_download=None):
    try:
        # ===== لاگ ورود =====
        logger.info("🚀 Entering handle_message")
        chat_id = message.chat.id
        user_id = message.from_user.id
        text = message.text or ""
        username = message.from_user.username or ""
        first_name = message.from_user.first_name or ""
        last_name = message.from_user.last_name or ""
        logger.info(f"📨 Message from {user_id} in chat {chat_id}: {text[:50]}")
        
        # ===== دریافت زبان =====
        try:
            lang = get_user_language(user_id) or "fa"
        except Exception as e:
            logger.error(f"Error getting language: {e}")
            lang = "fa"
        logger.info(f"🌐 Language: {lang}")
        
        # ===== اضافه کردن کاربر =====
        try:
            sig = inspect.signature(add_user)
            params = list(sig.parameters.keys())
            if 'lang' in params:
                add_user(user_id, username, first_name, last_name, lang)
            else:
                add_user(user_id, username, first_name, last_name)
                try:
                    set_user_language(user_id, lang)
                except:
                    pass
            logger.info(f"✅ User {user_id} added/updated")
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            # ادامه بده حتی اگر کاربر اضافه نشد
        
        # ===== عضویت اجباری =====
        if not is_admin(user_id):
            try:
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
                    logger.info("🔒 Force subscription required")
                    return
            except Exception as e:
                logger.error(f"Error checking subscription: {e}")
                # اگر خطا در بررسی عضویت بود، اجازه بده ادامه بده
        
        # ===== پردازش مراحل =====
        step_data = user_data.get(chat_id, {})
        step = step_data.get('step')
        if not step and hasattr(bot, 'user_data'):
            step_data = bot.user_data.get(chat_id, {})
            step = step_data.get('step')
        logger.info(f"📌 Step: {step}")
        
        # ===== دکمه‌های ادمین (Reply Keyboard) =====
        if is_admin(user_id):
            admin_menu_handlers = {
                "📊 آمار ربات": lambda: show_stats(bot, chat_id),
                "📋 گزارش روزانه": lambda: send_daily_report(bot, chat_id, lang),
                "👥 مدیریت کاربران و ادمین‌ها": lambda: show_admin_list(bot, chat_id, None, user_id),
                "👑 کاربران ویژه": lambda: show_premium_users(bot, chat_id, None, user_id),
                "📨 ارسال همگانی": lambda: start_broadcast(bot, chat_id, user_data),
                "⚙️ تنظیمات ربات": lambda: show_settings(bot, chat_id),
                "🔒 قفل اسپانسر": lambda: show_force_sub_settings(bot, chat_id),
                "🔙 بازگشت به منوی اصلی": lambda: send_welcome_message(bot, chat_id, user_id, lang)
            }
            if text in admin_menu_handlers:
                logger.info(f"🔄 Admin menu button clicked: {text}")
                try:
                    admin_menu_handlers[text]()
                except Exception as e:
                    logger.error(f"Error in admin menu handler: {e}")
                    bot.send_message(chat_id, f"❌ خطا: {e}")
                return
        
        # ===== مراحل مدیریتی =====
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
                    if chat_id in user_data:
                        msg_id = user_data[chat_id].get('message_id')
                        if msg_id:
                            try:
                                bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=None)
                            except:
                                pass
                    show_admin_list(bot, chat_id, None, user_id)
            except ValueError:
                bot.send_message(chat_id, get_message("admin_invalid_id", lang))
            if chat_id in user_data:
                del user_data[chat_id]
            if hasattr(bot, 'user_data') and chat_id in bot.user_data:
                del bot.user_data[chat_id]
            return
        
        elif step == 'admin_expire':
            if not is_owner(user_id) and not has_permission(user_id, "can_manage_admins"):
                bot.send_message(chat_id, get_message("admin_no_permission", lang))
                return
            admin_id = step_data.get('admin_id')
            try:
                days = int(text.strip())
                set_admin_expire(admin_id, days if days > 0 else None)
                bot.send_message(chat_id, get_message("premium_expire_success", lang))
                if chat_id in user_data:
                    msg_id = user_data[chat_id].get('message_id')
                    if msg_id:
                        try:
                            bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=None)
                        except:
                            pass
                show_admin_permissions(bot, chat_id, admin_id, None, user_id)
            except ValueError:
                bot.send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید!")
            if chat_id in user_data:
                del user_data[chat_id]
            if hasattr(bot, 'user_data') and chat_id in bot.user_data:
                del bot.user_data[chat_id]
            return
        
        # ===== مراحل ویژه =====
        elif step == 'add_premium':
            if not is_owner(user_id) and not has_permission(user_id, "can_manage_premium"):
                bot.send_message(chat_id, get_message("admin_no_permission", lang))
                return
            try:
                premium_user_id = int(text.strip())
                user_info = get_user(premium_user_id)
                if not user_info:
                    bot.send_message(chat_id, "❌ کاربر پیدا نشد!")
                    return
                set_premium_status(premium_user_id, True)
                bot.send_message(chat_id, f"✅ کاربر {premium_user_id} به ویژه اضافه شد.")
                if chat_id in user_data:
                    msg_id = user_data[chat_id].get('message_id')
                    if msg_id:
                        try:
                            bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=None)
                        except:
                            pass
                show_premium_users(bot, chat_id, None, user_id)
            except ValueError:
                bot.send_message(chat_id, "❌ آیدی وارد شده معتبر نیست!")
            if chat_id in user_data:
                del user_data[chat_id]
            if hasattr(bot, 'user_data') and chat_id in bot.user_data:
                del bot.user_data[chat_id]
            return
        
        elif step == 'premium_expire':
            if not is_owner(user_id) and not has_permission(user_id, "can_manage_premium"):
                bot.send_message(chat_id, get_message("admin_no_permission", lang))
                return
            premium_user_id = step_data.get('premium_user_id')
            try:
                days = int(text.strip())
                set_premium_status(premium_user_id, True, expire_days=days if days > 0 else None)
                bot.send_message(chat_id, get_message("premium_expire_success", lang))
                if chat_id in user_data:
                    msg_id = user_data[chat_id].get('message_id')
                    if msg_id:
                        try:
                            bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=None)
                        except:
                            pass
                show_premium_user_settings(bot, chat_id, premium_user_id, None, user_id)
            except ValueError:
                bot.send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید!")
            if chat_id in user_data:
                del user_data[chat_id]
            if hasattr(bot, 'user_data') and chat_id in bot.user_data:
                del bot.user_data[chat_id]
            return
        
        elif step == 'premium_quota':
            if not is_owner(user_id) and not has_permission(user_id, "can_manage_premium"):
                bot.send_message(chat_id, get_message("admin_no_permission", lang))
                return
            premium_user_id = step_data.get('premium_user_id')
            try:
                quota = int(text.strip())
                set_premium_status(premium_user_id, True, daily_quota=quota)
                bot.send_message(chat_id, get_message("settings_updated", lang))
                if chat_id in user_data:
                    msg_id = user_data[chat_id].get('message_id')
                    if msg_id:
                        try:
                            bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=None)
                        except:
                            pass
                show_premium_user_settings(bot, chat_id, premium_user_id, None, user_id)
            except ValueError:
                bot.send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید!")
            if chat_id in user_data:
                del user_data[chat_id]
            if hasattr(bot, 'user_data') and chat_id in bot.user_data:
                del bot.user_data[chat_id]
            return
        
        elif step == 'premium_size':
            if not is_owner(user_id) and not has_permission(user_id, "can_manage_premium"):
                bot.send_message(chat_id, get_message("admin_no_permission", lang))
                return
            premium_user_id = step_data.get('premium_user_id')
            try:
                size = int(text.strip())
                set_premium_status(premium_user_id, True, max_file_size=size)
                bot.send_message(chat_id, get_message("settings_updated", lang))
                if chat_id in user_data:
                    msg_id = user_data[chat_id].get('message_id')
                    if msg_id:
                        try:
                            bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=None)
                        except:
                            pass
                show_premium_user_settings(bot, chat_id, premium_user_id, None, user_id)
            except ValueError:
                bot.send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید!")
            if chat_id in user_data:
                del user_data[chat_id]
            if hasattr(bot, 'user_data') and chat_id in bot.user_data:
                del bot.user_data[chat_id]
            return
        
        elif step == 'premium_rate':
            if not is_owner(user_id) and not has_permission(user_id, "can_manage_premium"):
                bot.send_message(chat_id, get_message("admin_no_permission", lang))
                return
            premium_user_id = step_data.get('premium_user_id')
            try:
                rate = int(text.strip())
                set_premium_status(premium_user_id, True, rate_limit=rate)
                bot.send_message(chat_id, get_message("settings_updated", lang))
                if chat_id in user_data:
                    msg_id = user_data[chat_id].get('message_id')
                    if msg_id:
                        try:
                            bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=None)
                        except:
                            pass
                show_premium_user_settings(bot, chat_id, premium_user_id, None, user_id)
            except ValueError:
                bot.send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید!")
            if chat_id in user_data:
                del user_data[chat_id]
            if hasattr(bot, 'user_data') and chat_id in bot.user_data:
                del bot.user_data[chat_id]
            return
        
        # ===== تنظیمات عمومی =====
        elif step == 'set_daily_quota':
            if not is_owner(user_id) and not has_permission(user_id, "can_manage_settings"):
                bot.send_message(chat_id, get_message("admin_no_permission", lang))
                return
            try:
                quota = int(text.strip())
                set_setting("daily_quota", str(quota))
                bot.send_message(chat_id, get_message("settings_updated", lang))
                if chat_id in user_data:
                    msg_id = user_data[chat_id].get('message_id')
                    if msg_id:
                        try:
                            bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=None)
                        except:
                            pass
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
                size = int(text.strip())
                set_setting("max_file_size", str(size))
                bot.send_message(chat_id, get_message("settings_updated", lang))
                if chat_id in user_data:
                    msg_id = user_data[chat_id].get('message_id')
                    if msg_id:
                        try:
                            bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=None)
                        except:
                            pass
                show_settings(bot, chat_id)
            except ValueError:
                bot.send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید!")
            if chat_id in user_data:
                del user_data[chat_id]
            if hasattr(bot, 'user_data') and chat_id in bot.user_data:
                del bot.user_data[chat_id]
            return
        
        # ===== اضافه کردن کانال اجباری =====
        elif step == 'add_force_channel':
            if not is_owner(user_id) and not has_permission(user_id, "can_manage_force_sub"):
                bot.send_message(chat_id, get_message("admin_no_permission", lang))
                return
            channel = text.strip()
            if not channel.startswith('@'):
                bot.send_message(chat_id, "❌ لطفاً آیدی کانال را با @ شروع کنید!")
                return
            add_force_channel(channel)
            bot.send_message(chat_id, f"✅ کانال {channel} به لیست اضافه شد.")
            if chat_id in user_data:
                msg_id = user_data[chat_id].get('message_id')
                if msg_id:
                    try:
                        bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=None)
                    except:
                        pass
            show_force_sub_settings(bot, chat_id)
            if chat_id in user_data:
                del user_data[chat_id]
            if hasattr(bot, 'user_data') and chat_id in bot.user_data:
                del bot.user_data[chat_id]
            return
        
        # ===== ارسال همگانی =====
        elif step == 'broadcast':
            process_broadcast_message(bot, message, user_data)
            return
        
        # ===================================================
        # ===== پردازش دستورات و لینک‌ها =====
        # ===================================================
        
        if text.startswith('/'):
            # دستورات معمولی
            if text == '/start':
                send_welcome_message(bot, chat_id, user_id, lang)
            elif text == '/help':
                bot.send_message(chat_id, get_message("help", lang))
            elif text == '/language':
                keyboard = get_language_keyboard()
                bot.send_message(chat_id, get_message("select_language", lang), reply_markup=keyboard)
            elif text == '/admin' and is_admin(user_id):
                keyboard = get_admin_inline_keyboard(lang)
                bot.send_message(chat_id, get_message("admin_welcome", lang), reply_markup=keyboard, parse_mode='HTML')
            else:
                bot.send_message(chat_id, get_message("unknown_command", lang))
        
        elif text.startswith('http://') or text.startswith('https://'):
            # ===== دانلود =====
            logger.info(f"📥 Download request: {text}")
            
            # بررسی فعال بودن ربات
            if get_setting("is_active", "True") != "True":
                bot.send_message(chat_id, get_message("bot_inactive", lang))
                return
            
            # بررسی سقف دانلود
            if not is_admin(user_id):
                try:
                    daily_quota = get_user_daily_quota(user_id)
                    if daily_quota is not None and daily_quota <= 0:
                        bot.send_message(chat_id, get_message("daily_quota_reached", lang))
                        return
                except:
                    pass
            
            # محدودیت زمانی
            if get_rate_limit_enabled() and not is_admin(user_id):
                if user_last_download is not None:
                    last_time = user_last_download.get(user_id, 0)
                    current_time = time.time()
                    wait_seconds = get_rate_limit_seconds()
                    if current_time - last_time < wait_seconds:
                        wait_time = int(wait_seconds - (current_time - last_time))
                        bot.send_message(chat_id, get_message("rate_limit_wait", lang).format(seconds=wait_time))
                        return
            
            # دانلود
            msg = bot.send_message(chat_id, get_message("downloading", lang))
            try:
                files, error = download_media(text, user_id)
                if files:
                    for f in files:
                        try:
                            if f.endswith(('.mp4', '.mkv', '.webm')):
                                with open(f, 'rb') as video:
                                    bot.send_video(chat_id, video, caption="✅ دانلود شد!")
                            elif f.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                                with open(f, 'rb') as img:
                                    bot.send_photo(chat_id, img, caption="✅ دانلود شد!")
                            elif f.endswith(('.mp3', '.m4a', '.aac')):
                                with open(f, 'rb') as audio:
                                    bot.send_audio(chat_id, audio, caption="✅ دانلود شد!")
                            else:
                                with open(f, 'rb') as doc:
                                    bot.send_document(chat_id, doc, caption="✅ دانلود شد!")
                            os.remove(f)
                        except Exception as e:
                            logger.error(f"Error sending file: {e}")
                            bot.send_message(chat_id, f"❌ خطا در ارسال فایل: {e}")
                    if user_last_download is not None:
                        user_last_download[user_id] = time.time()
                    bot.delete_message(chat_id, msg.message_id)
                else:
                    bot.edit_message_text(f"❌ خطا: {error}", chat_id, msg.message_id)
            except Exception as e:
                logger.error(f"Download error: {e}")
                bot.edit_message_text(f"❌ خطا: {e}", chat_id, msg.message_id)
        
        else:
            # ===== پیام معمولی =====
            logger.info(f"ℹ️ Normal message: {text[:50]}")
            if is_admin(user_id):
                keyboard = get_admin_keyboard(lang)
                bot.send_message(chat_id, get_message("admin_welcome", lang), reply_markup=keyboard)
            else:
                keyboard = get_user_keyboard()
                bot.send_message(chat_id, get_message("start", lang), reply_markup=keyboard)
        
        logger.info("✅ handle_message completed successfully")
    
    except Exception as e:
        # ===== خطای کلی =====
        logger.error(f"🔥 CRITICAL ERROR in handle_message: {e}", exc_info=True)
        try:
            bot.send_message(chat_id, "⚠️ خطای داخلی رخ داد. لطفاً دوباره تلاش کنید.")
        except:
            pass
