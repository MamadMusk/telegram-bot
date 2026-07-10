from telebot.types import ReplyKeyboardMarkup, KeyboardButton, BotCommand, InlineKeyboardMarkup, InlineKeyboardButton

# ===================================================
# 📝 همه پیام‌های ربات
# ===================================================
MESSAGES = {
    "start": """🎬 به ربات دانلودر خوش اومدی!

لینک مدنظر خود را جهت دانلود بفرستید.

📸 Instagram | 🐦 X | 📱 TikTok | 📌 Pinterest
📷 Snapchat | 🌐 Facebook | 🎧 SoundCloud
💬 Threads | 🔗 Reddit | 🎥 Likee""",
    
    "downloading": "⏳ دانلود...",
    "invalid_link": "❌ لطفاً یه لینک معتبر اینستاگرام بفرست.",
    "download_failed": "❌ دانلود نشد. پست ممکنه خصوصی یا حذف شده باشه.",
    "send_error": "❌ خطا در ارسال فایل: {error}",
    "caption": "🤍Downloaded by @iBBDownloaderBot",
    
    # ===== پنل ادمین =====
    "admin_welcome": "🛠 به پنل مدیریت خوش آمدید.\nلطفاً یکی از گزینه‌ها را انتخاب کنید:",
    
    # ===== آمار =====
    "stats_text": """📊 <b>آمار ربات</b>

👥 <b>کل کاربران:</b> {total}
🆕 <b>امروز:</b> {today}
📈 <b>هفته گذشته:</b> {week}
📅 <b>ماه گذشته:</b> {month}
📥 <b>کل دانلودها:</b> {downloads}""",
    
    # ===== ارسال همگانی =====
    "broadcast_prompt": "📝 پیام مورد نظر برای ارسال به تمام کاربران را بنویسید:",
    "broadcast_preview": "📨 <b>پیش‌نمایش پیام همگانی</b>\n\n{message}\n\n👥 تعداد گیرندگان: {count} نفر\n\nآیا از ارسال مطمئن هستید؟",
    "broadcast_cancelled": "❌ ارسال همگانی لغو شد.",
    "broadcast_success": "✅ ارسال همگانی با موفقیت به پایان رسید!\n\n📊 <b>گزارش ارسال:</b>\n• کل کاربران: {total}\n• ارسال موفق: {success}\n• خطا: {failed}",
    "broadcast_progress": "📨 <b>در حال ارسال همگانی...</b>\n\n• ارسال شده: {sent} از {total} ({percent}%)\n• باقی‌مانده: {remaining}\n• خطا: {failed}\n\nبرای بروزرسانی، روی دکمه کلیک کنید.",
    "broadcast_failed": "❌ خطا در ارسال همگانی: {error}",
    "broadcast_empty": "❌ پیام نمی‌تواند خالی باشد.",
    
    # ===== قفل اسپانسر =====
    "force_sub_prompt": """🔒 <b>تنظیمات قفل اسپانسر</b>

کانال‌های اجباری فعلی:
{channels}

📌 برای <b>افزودن</b> کانال جدید، روی دکمه زیر کلیک کنید.
📌 برای <b>حذف</b> کانال، روی دکمه مربوطه کلیک کنید.""",
    "force_sub_add_prompt": "📝 آیدی کانال جدید را با @ وارد کنید:\nمثال: @MyChannel",
    "force_sub_added": "✅ کانال {channel} با موفقیت اضافه شد.",
    "force_sub_removed": "❌ کانال {channel} با موفقیت حذف شد.",
    "force_sub_not_found": "❌ کانال {channel} در لیست پیدا نشد.",
    "force_sub_required": """🔒 <b>برای استفاده از ربات باید در کانال‌های زیر عضو شوید:</b>

{channels}

پس از عضویت، دکمه زیر را بزنید.""",
    "force_sub_verified": "✅ عضویت شما تأیید شد! حالا می‌توانید از ربات استفاده کنید.",
    
    # ===== مدیریت ادمین‌ها =====
    "admin_management": "📋 مدیریت ادمین‌ها",
    "admin_list": """📋 <b>لیست ادمین‌ها</b>

{admins}
_________________
🔹 <b>نقش‌ها:</b>
• owner - مالک ربات (دسترسی کامل)
• super - دسترسی کامل به جز حذف owner
• moderator - مدیریت کاربران
• viewer - فقط مشاهده""",
    "admin_add_prompt": "👤 آیدی عددی کاربر جدید را برای افزودن به عنوان ادمین وارد کنید:",
    "admin_add_success": "✅ کاربر با موفقیت به عنوان ادمین اضافه شد.\nنقش: {role}",
    "admin_remove_success": "❌ کاربر از لیست ادمین‌ها حذف شد.",
    "admin_invalid_id": "❌ آیدی وارد شده معتبر نیست.",
    "admin_cant_remove_self": "❌ نمی‌توانید خودتان را حذف کنید!",
    "admin_cant_remove_owner": "❌ نمی‌توانید مالک ربات را حذف یا ویرایش کنید!",
    "admin_no_permission": "⛔ شما دسترسی لازم برای این کار را ندارید.",
    
    # ===== مدیریت دسترسی ادمین =====
    "admin_permissions_title": "🔐 مدیریت دسترسی‌های ادمین",
    "admin_permissions_header": """🔐 <b>مدیریت دسترسی‌های ادمین</b>

👤 <b>ادمین:</b> {name} (ID: {user_id})
📋 <b>نقش:</b> {role}

<b>دسترسی‌های فعلی:</b>
• مشاهده آمار: {stats}
• ارسال همگانی: {broadcast}
• مدیریت قفل اسپانسر: {force_sub}
• مدیریت تنظیمات: {settings}
• مدیریت ادمین‌ها: {admins}

برای تغییر هر دسترسی، روی دکمه مربوطه کلیک کنید.
""",
    "permission_toggle_success": "✅ دسترسی {perm} برای ادمین {user_id} تغییر کرد.",
    
    # ===== تنظیمات =====
    "settings_list": """⚙️ <b>تنظیمات ربات</b>

📌 <b>کانال‌های اجباری:</b> {channels}
📌 <b>سقف دانلود روزانه:</b> {daily_quota} 
📌 <b>حداکثر حجم فایل:</b> {max_file_size} MB
📌 <b>وضعیت ربات:</b> {is_active}
📌 <b>محدودیت زمانی:</b> {rate_limit_status} ({rate_limit_seconds} ثانیه)""",
    "settings_updated": "✅ تنظیمات با موفقیت به‌روزرسانی شد.",
    "settings_quota_prompt": "📊 سقف دانلود روزانه را به عدد وارد کنید (0 = نامحدود):",
    "settings_size_prompt": "📦 حداکثر حجم فایل را به مگابایت وارد کنید:",
    
    # ===== محدودیت زمانی =====
    "rate_limit_title": "⏱️ <b>تنظیمات محدودیت زمانی</b>",
    "rate_limit_status": """⏱️ <b>تنظیمات محدودیت زمانی بین دانلودها</b>

وضعیت: {status}
زمان انتظار: {seconds} ثانیه

کاربر بعد از هر دانلود باید {seconds} ثانیه صبر کند تا بتواند لینک بعدی را ارسال کند.

برای تغییر، روی دکمه‌های زیر کلیک کنید:""",
    "rate_limit_enabled": "✅ محدودیت زمانی فعال شد! زمان انتظار: {seconds} ثانیه",
    "rate_limit_disabled": "❌ محدودیت زمانی غیرفعال شد.",
    "rate_limit_changed": "⏱️ زمان انتظار به {seconds} ثانیه تغییر کرد.",
    "rate_limit_wait": "⏳ لطفاً {seconds} ثانیه صبر کنید تا بتوانید لینک بعدی را ارسال کنید.\nزمان باقی‌مانده: {remaining} ثانیه",
}

# ===================================================
# ⌨️ دکمه‌های شیشه‌ای (Reply Keyboard - فقط برای ادمین)
# ===================================================
def get_admin_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_stats = KeyboardButton("📊 آمار ربات")
    btn_broadcast = KeyboardButton("📨 ارسال همگانی")
    btn_force_sub = KeyboardButton("🔒 قفل اسپانسر")
    btn_admins = KeyboardButton("📋 مدیریت ادمین‌ها")
    btn_settings = KeyboardButton("⚙️ تنظیمات ربات")
    keyboard.add(btn_stats, btn_broadcast)
    keyboard.add(btn_force_sub, btn_admins)
    keyboard.add(btn_settings)
    return keyboard

def get_user_keyboard():
    return ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)

# ===================================================
# 🔐 دکمه‌های شیشه‌ای (Inline Keyboard)
# ===================================================
def get_stats_refresh_keyboard():
    keyboard = InlineKeyboardMarkup()
    btn_refresh = InlineKeyboardButton("🔄 بروزرسانی", callback_data="refresh_stats")
    keyboard.add(btn_refresh)
    return keyboard

def get_force_sub_keyboard(channels):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for channel in channels:
        btn = InlineKeyboardButton(f"📢 عضویت در {channel}", url=f"https://t.me/{channel.replace('@', '')}")
        keyboard.add(btn)
    btn_verify = InlineKeyboardButton("✅ تأیید عضویت", callback_data="force_sub_verify")
    keyboard.add(btn_verify)
    return keyboard

def get_confirm_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    btn_confirm = InlineKeyboardButton("✅ تأیید و ارسال", callback_data="broadcast_confirm")
    btn_cancel = InlineKeyboardButton("❌ لغو", callback_data="broadcast_cancel")
    keyboard.add(btn_confirm, btn_cancel)
    return keyboard

def get_broadcast_progress_keyboard():
    keyboard = InlineKeyboardMarkup()
    btn_refresh = InlineKeyboardButton("🔄 بروزرسانی وضعیت", callback_data="broadcast_refresh")
    btn_cancel = InlineKeyboardButton("❌ توقف ارسال", callback_data="broadcast_cancel_force")
    keyboard.add(btn_refresh, btn_cancel)
    return keyboard

def get_admin_list_inline_keyboard(admins, current_user_id):
    """لیست ادمین‌ها به صورت دکمه‌های شیشه‌ای"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    for admin in admins:
        uid = admin['user_id']
        name = admin.get('first_name', 'Unknown')
        username = admin.get('username', '')
        role = admin.get('role', 'viewer')
        # نمایش با آیکون نقش
        role_icon = "👑" if role == "owner" else "⭐" if role == "super" else "🔹"
        label = f"{role_icon} {name} (@{username})"
        btn = InlineKeyboardButton(label, callback_data=f"admin_view_{uid}")
        keyboard.add(btn)
    # دکمه افزودن ادمین (فقط برای کسانی که اجازه دارند)
    keyboard.add(InlineKeyboardButton("➕ افزودن ادمین", callback_data="admin_add"))
    keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back"))
    return keyboard

def get_admin_permissions_keyboard(admin_user_id, permissions, is_owner=False):
    """دکمه‌های مدیریت دسترسی‌های یک ادمین خاص"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    # نمایش وضعیت هر دسترسی با دکمه تغییر
    for perm_key, perm_label in [
        ("can_view_stats", "👁️ مشاهده آمار"),
        ("can_send_broadcast", "📨 ارسال همگانی"),
        ("can_manage_force_sub", "🔒 قفل اسپانسر"),
        ("can_manage_settings", "⚙️ تنظیمات"),
        ("can_manage_admins", "👥 مدیریت ادمین‌ها")
    ]:
        status = "✅" if permissions.get(perm_key, False) else "❌"
        btn = InlineKeyboardButton(
            f"{status} {perm_label}",
            callback_data=f"admin_perm_toggle_{admin_user_id}_{perm_key}"
        )
        keyboard.add(btn)
    # دکمه حذف ادمین (فقط اگر owner نباشد)
    if not is_owner:
        keyboard.add(InlineKeyboardButton("❌ حذف ادمین", callback_data=f"admin_remove_{admin_user_id}"))
    keyboard.add(InlineKeyboardButton("🔙 بازگشت به لیست", callback_data="admin_list_back"))
    return keyboard

def get_force_sub_inline_keyboard(channels):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for channel in channels:
        btn_remove = InlineKeyboardButton(f"❌ حذف {channel}", callback_data=f"force_sub_remove_{channel}")
        keyboard.add(btn_remove)
    btn_add = InlineKeyboardButton("➕ افزودن کانال", callback_data="force_sub_add")
    btn_back = InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")
    keyboard.add(btn_add)
    keyboard.add(btn_back)
    return keyboard

def get_settings_inline_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    btn_quota = InlineKeyboardButton("📊 سقف دانلود", callback_data="setting_quota")
    btn_size = InlineKeyboardButton("📦 حجم فایل", callback_data="setting_size")
    btn_active = InlineKeyboardButton("🔄 وضعیت ربات", callback_data="setting_active")
    btn_rate_limit = InlineKeyboardButton("⏱️ محدودیت زمانی", callback_data="setting_rate_limit")
    btn_back = InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")
    keyboard.add(btn_quota, btn_size)
    keyboard.add(btn_active, btn_rate_limit)
    keyboard.add(btn_back)
    return keyboard

def get_rate_limit_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    btn_enable = InlineKeyboardButton("✅ فعال", callback_data="rate_limit_enable")
    btn_disable = InlineKeyboardButton("❌ غیرفعال", callback_data="rate_limit_disable")
    btn_10s = InlineKeyboardButton("⏱️ ۱۰ ثانیه", callback_data="rate_limit_10")
    btn_30s = InlineKeyboardButton("⏱️ ۳۰ ثانیه", callback_data="rate_limit_30")
    btn_60s = InlineKeyboardButton("⏱️ ۶۰ ثانیه", callback_data="rate_limit_60")
    btn_120s = InlineKeyboardButton("⏱️ ۱۲۰ ثانیه", callback_data="rate_limit_120")
    btn_back = InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")
    keyboard.add(btn_enable, btn_disable)
    keyboard.add(btn_10s, btn_30s, btn_60s, btn_120s)
    keyboard.add(btn_back)
    return keyboard

def get_back_keyboard():
    keyboard = InlineKeyboardMarkup()
    btn_back = InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")
    keyboard.add(btn_back)
    return keyboard

# ===================================================
# 📋 کامندها
# ===================================================
COMMANDS = [
    BotCommand("start", "شروع و نمایش راهنما"),
]
