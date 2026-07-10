from telebot.types import ReplyKeyboardMarkup, KeyboardButton, BotCommand, InlineKeyboardMarkup, InlineKeyboardButton

# ===================================================
# 📝 همه پیام‌های ربات - اینجا رو ادیت کن!
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
    
    # ===== پیام‌های پنل ادمین =====
    "admin_panel": "🛠 پنل مدیریت",
    "admin_welcome": "🛠 به پنل مدیریت خوش آمدید.\nلطفاً یکی از گزینه‌ها را انتخاب کنید:",
    "stats_title": "📊 آمار ربات",
    "stats_text": """📊 **آمار ربات**

👥 **کل کاربران:** {total}
🆕 **امروز:** {today}
📈 **هفته گذشته:** {week}
📅 **ماه گذشته:** {month}
📥 **کل دانلودها:** {downloads}""",
    
    "broadcast_title": "📨 ارسال همگانی",
    "broadcast_prompt": "📝 پیام مورد نظر برای ارسال به تمام کاربران را بنویسید:",
    "broadcast_preview": "📨 **پیش‌نمایش پیام همگانی**\n\n{message}\n\n👥 تعداد گیرندگان: {count} نفر\n\nآیا از ارسال مطمئن هستید؟",
    "broadcast_cancelled": "❌ ارسال همگانی لغو شد.",
    "broadcast_success": "✅ پیام همگانی با موفقیت به {count} نفر ارسال شد.",
    "broadcast_failed": "❌ خطا در ارسال همگانی: {error}",
    "broadcast_empty": "❌ پیام نمی‌تواند خالی باشد.",
    
    "force_sub_title": "🔒 قفل اسپانسر",
    "force_sub_prompt": """🔒 **تنظیمات قفل اسپانسر**

کانال‌های اجباری فعلی:
{channels}

برای اضافه کردن کانال جدید، آیدی آن را با @ وارد کنید.
برای حذف کانال، دستور /remove_channel @channel را بفرستید.""",
    "force_sub_added": "✅ کانال {channel} با موفقیت اضافه شد.",
    "force_sub_removed": "❌ کانال {channel} با موفقیت حذف شد.",
    "force_sub_not_found": "❌ کانال {channel} در لیست پیدا نشد.",
    "force_sub_check": "🔍 در حال بررسی عضویت شما در کانال‌های اجباری...",
    "force_sub_required": """🔒 **برای استفاده از ربات باید در کانال‌های زیر عضو شوید:**

{channels}

پس از عضویت، دکمه زیر را بزنید.""",
    "force_sub_verified": "✅ عضویت شما تأیید شد! حالا می‌توانید از ربات استفاده کنید.",
}

# ===================================================
# ⌨️ دکمه‌های شیشه‌ای (فقط برای ادمین)
# ===================================================
def get_admin_keyboard():
    """دکمه‌های پنل ادمین (فقط برای ادمین‌ها)"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    btn_stats = KeyboardButton("📊 آمار ربات")
    btn_broadcast = KeyboardButton("📨 ارسال همگانی")
    btn_force_sub = KeyboardButton("🔒 قفل اسپانسر")
    btn_back = KeyboardButton("🔙 بازگشت")
    
    keyboard.add(btn_stats, btn_broadcast)
    keyboard.add(btn_force_sub)
    keyboard.add(btn_back)
    
    return keyboard

def get_user_keyboard():
    """دکمه‌های کاربر عادی (هیچ دکمه‌ای!)"""
    # کاربر عادی هیچ دکمه‌ای نمی‌بینه
    return ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)

# ===================================================
# 🔐 دکمه‌های اینلاین (Inline Keyboard)
# ===================================================
def get_admin_inline_keyboard():
    """دکمه‌های اینلاین پنل ادمین"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    btn_stats = InlineKeyboardButton("📊 آمار", callback_data="admin_stats")
    btn_broadcast = InlineKeyboardButton("📨 ارسال همگانی", callback_data="admin_broadcast")
    btn_force_sub = InlineKeyboardButton("🔒 قفل اسپانسر", callback_data="admin_force_sub")
    btn_close = InlineKeyboardButton("❌ بستن", callback_data="admin_close")
    
    keyboard.add(btn_stats, btn_broadcast)
    keyboard.add(btn_force_sub)
    keyboard.add(btn_close)
    
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

# ===================================================
# 📋 لیست کامندها (برای منوی ربات)
# ===================================================
COMMANDS = [
    BotCommand("start", "شروع و نمایش راهنما"),
]
