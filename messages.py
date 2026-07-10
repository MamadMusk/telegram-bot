from telebot.types import ReplyKeyboardMarkup, KeyboardButton, BotCommand

# ===================================================
# 📝 همه پیام‌های ربات
# ===================================================
MESSAGES = {
    "start": """موزیک، ویدئو، پست، ریلز، شورت و استوری های مدنظر خود را از تمام پلتفرم های زیر دانلود کنید.

📸 Instagram
🐦 X (Twitter)
📱 TikTok
📌 Pinterest
📷 Snapchat
🌐 Facebook
🎧 SoundCloud
💬 Threads
🔗 Reddit
🎥 Likee

لینک مدنظر خود را جهت دانلود بفرستید.""",
    "downloading": "⏳ دانلود...",
    "invalid_link": "❌ لطفاً یه لینک معتبر اینستاگرام بفرست.",
    "download_failed": "دانلود نشد. پست ممکنه خصوصی یا حذف شده باشه.",
    "send_error": "خطا در ارسال فایل: {error}",
    "caption": "🤍Downloaded by @iBBDownloaderBot",
    "admin_panel": "🛠 پنل مدیریت",
    "help": "ℹ️ راهنما",
    "status": "📊 وضعیت",
}

# ===================================================
# ⌨️ دکمه‌های شیشه‌ای (Reply Keyboard)
# ===================================================
def get_main_keyboard(is_admin=False):
    """دکمه‌های صفحه اصلی"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # دکمه‌های عمومی
    btn_download = KeyboardButton("📥 ارسال لینک اینستاگرام")
    btn_help = KeyboardButton(MESSAGES["help"])
    btn_status = KeyboardButton(MESSAGES["status"])
    
    if is_admin:
        btn_admin = KeyboardButton(MESSAGES["admin_panel"])
        keyboard.add(btn_download, btn_help, btn_status, btn_admin)
    else:
        keyboard.add(btn_download, btn_help, btn_status)
    
    return keyboard

# ===================================================
# 📋 لیست کامندها (برای منوی ربات)
# ===================================================
COMMANDS = [
    BotCommand("start", "شروع و نمایش راهنما"),
    BotCommand("help", "راهنمای ربات"),
    BotCommand("status", "وضعیت ربات"),
]

# ===================================================
# 🔐 دکمه‌های پنل ادمین (Inline Keyboard)
# ===================================================
def get_admin_inline_keyboard():
    """دکمه‌های پنل مدیریت"""
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    btn_users = InlineKeyboardButton("👥 کاربران", callback_data="admin_users")
    btn_stats = InlineKeyboardButton("📊 آمار", callback_data="admin_stats")
    btn_broadcast = InlineKeyboardButton("📨 پیام همگانی", callback_data="admin_broadcast")
    btn_settings = InlineKeyboardButton("⚙️ تنظیمات", callback_data="admin_settings")
    btn_back = InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")
    
    keyboard.add(btn_users, btn_stats)
    keyboard.add(btn_broadcast, btn_settings)
    keyboard.add(btn_back)
    
    return keyboard

def get_back_button():
    """دکمه بازگشت"""
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back"))
    return keyboard
