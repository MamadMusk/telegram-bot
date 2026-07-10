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
    "stats_text": """📊 **آمار ربات**

👥 **کل کاربران:** {total}
🆕 **امروز:** {today}
📈 **هفته گذشته:** {week}
📅 **ماه گذشته:** {month}
📥 **کل دانلودها:** {downloads}""",
    
    # ===== ارسال همگانی =====
    "broadcast_prompt": "📝 پیام مورد نظر برای ارسال به تمام کاربران را بنویسید:",
    "broadcast_preview": "📨 **پیش‌نمایش پیام همگانی**\n\n{message}\n\n👥 تعداد گیرندگان: {count} نفر\n\nآیا از ارسال مطمئن هستید؟",
    "broadcast_cancelled": "❌ ارسال همگانی لغو شد.",
    "broadcast_success": "✅ پیام همگانی با موفقیت به {count} نفر ارسال شد.",
    "broadcast_failed": "❌ خطا در ارسال همگانی: {error}",
    "broadcast_empty": "❌ پیام نمی‌تواند خالی باشد.",
    
    # ===== قفل اسپانسر =====
    "force_sub_prompt": """🔒 **تنظیمات قفل اسپانسر**

کانال‌های اجباری فعلی:
{channels}

📌 برای **افزودن** کانال جدید، روی دکمه زیر کلیک کنید.
📌 برای **حذف** کانال، روی دکمه مربوطه کلیک کنید.""",
    "force_sub_add_prompt": "📝 آیدی کانال جدید را با @ وارد کنید:\nمثال: @MyChannel",
    "force_sub_added": "✅ کانال {channel} با موفقیت اضافه شد.",
    "force_sub_removed": "❌ کانال {channel} با موفقیت حذف شد.",
    "force_sub_not_found": "❌ کانال {channel} در لیست پیدا نشد.",
    "force_sub_required": """🔒 **برای استفاده از ربات باید در کانال‌های زیر عضو شوید:**

{channels}

پس از عضویت، دکمه زیر را بزنید.""",
    "force_sub_verified": "✅ عضویت شما تأیید شد! حالا می‌توانید از ربات استفاده کنید.",
    
    # ===== مدیریت ادمین‌ها =====
    "admin_list": """📋 **لیست ادمین‌ها**

{admins}
_________________
🔹 **نقش‌ها:**
• super - دسترسی کامل
• moderator - مدیریت کاربران
• viewer - فقط مشاهده""",
    "admin_add_prompt": "👤 آیدی عددی کاربر جدید را برای افزودن به عنوان ادمین وارد کنید:",
    "admin_add_success": "✅ کاربر با موفقیت به عنوان ادمین اضافه شد.\nنقش: {role}",
    "admin_remove_success": "❌ کاربر از لیست ادمین‌ها حذف شد.",
    "admin_invalid_id": "❌ آیدی وارد شده معتبر نیست.",
    "admin_cant_remove_self": "❌ نمی‌توانید خودتان را حذف کنید!",
    
    # ===== تنظیمات =====
    "settings_list": """⚙️ **تنظیمات ربات**

📌 **کانال‌های اجباری:** {channels}
📌 **سقف دانلود روزانه:** {daily_quota} 
📌 **حداکثر حجم فایل:** {max_file_size} MB
📌 **وضعیت ربات:** {is_active}""",
    "settings_updated": "✅ تنظیمات با موفقیت به‌روزرسانی شد.",
    "settings_quota_prompt": "📊 سقف دانلود روزانه را به عدد وارد کنید (0 = نامحدود):",
    "settings_size_prompt": "📦 حداکثر حجم فایل را به مگابایت وارد کنید:",
}

# ===================================================
# ⌨️ دکمه‌های شیشه‌ای (Reply Keyboard - فقط برای ادمین)
# ===================================================
def get_admin_keyboard():
    """دکمه‌های پنل ادمین (دکمه‌های شیشه‌ای اصلی)"""
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
    """کاربر عادی هیچ دکمه‌ای نمی‌بینه"""
    return ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)

# ===================================================
# 🔐 دکمه‌های شیشه‌ای (Inline Keyboard)
# ===================================================
def get_stats_refresh_keyboard():
    """دکمه شیشه‌ای برای بروزرسانی آمار"""
    keyboard = InlineKeyboardMarkup()
    btn_refresh = InlineKeyboardButton("🔄 بروزرسانی", callback_data="refresh_stats")
    keyboard.add(btn_refresh)
    return keyboard

def get_force_sub_keyboard(channels):
    """دکمه‌های تأیید عضویت در کانال"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    for channel in channels:
        btn = InlineKeyboardButton(f"📢 عضویت در {channel}", url=f"https://t.me/{channel.replace('@', '')}")
        keyboard.add(btn)
    btn_verify = InlineKeyboardButton("✅ تأیید عضویت", callback_data="force_sub_verify")
    keyboard.add(btn_verify)
    return keyboard

def get_confirm_keyboard():
    """دکمه‌های تأیید یا لغو برای ارسال همگانی"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    btn_confirm = InlineKeyboardButton("✅ تأیید و ارسال", callback_data="broadcast_confirm")
    btn_cancel = InlineKeyboardButton("❌ لغو", callback_data="broadcast_cancel")
    keyboard.add(btn_confirm, btn_cancel)
    return keyboard

def get_admin_list_inline_keyboard(admins):
    """دکمه‌های مدیریت ادمین‌ها با لیست و گزینه‌های عملیات"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for admin in admins:
        user_id = admin['user_id']
        name = admin.get('first_name', 'Unknown')
        username = admin.get('username', '')
        label = f"👤 {name} (@{username}) - {admin['role']}"
        btn_remove = InlineKeyboardButton(f"❌ {label}", callback_data=f"admin_remove_{user_id}")
        keyboard.add(btn_remove)
    
    btn_add = InlineKeyboardButton("➕ افزودن ادمین", callback_data="admin_add")
    btn_back = InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")
    keyboard.add(btn_add)
    keyboard.add(btn_back)
    
    return keyboard

def get_force_sub_inline_keyboard(channels):
    """دکمه‌های مدیریت قفل اسپانسر"""
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
    """دکمه‌های تنظیمات ربات"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    btn_quota = InlineKeyboardButton("📊 سقف دانلود", callback_data="setting_quota")
    btn_size = InlineKeyboardButton("📦 حجم فایل", callback_data="setting_size")
    btn_active = InlineKeyboardButton("🔄 وضعیت ربات", callback_data="setting_active")
    btn_back = InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")
    keyboard.add(btn_quota, btn_size)
    keyboard.add(btn_active)
    keyboard.add(btn_back)
    return keyboard

def get_back_keyboard():
    """دکمه بازگشت ساده"""
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
