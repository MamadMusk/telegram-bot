from telebot.types import ReplyKeyboardMarkup, KeyboardButton, BotCommand, InlineKeyboardMarkup, InlineKeyboardButton

# ===================================================
# 📝 همه پیام‌های ربات (دو زبانه)
# ===================================================
MESSAGES_FA = {
    "start": """🎬 به ربات دانلودر خوش اومدی!

لینک مدنظر خود را جهت دانلود بفرستید.

📸 Instagram | 🐦 X | 📱 TikTok | 📌 Pinterest
📷 Snapchat | 🌐 Facebook | 🎧 SoundCloud
💬 Threads | 🔗 Reddit | 🎥 Likee""",
    "lang_selection": "🌍 لطفاً زبان مورد نظر خود را انتخاب کنید:\nPlease select your language:",
    "lang_changed": "✅ زبان با موفقیت به فارسی تغییر کرد.",
    "lang_changed_en": "✅ Language changed to English successfully.",
    "lang_prompt": "🌍 برای تغییر زبان، روی دکمه زیر کلیک کنید:",
    "downloading": "⏳ دانلود...",
    "invalid_link": "❌ لطفاً یه لینک معتبر اینستاگرام بفرست.",
    "download_failed": "❌ دانلود نشد. پست ممکنه خصوصی یا حذف شده باشه.",
    "send_error": "❌ خطا در ارسال فایل: {error}",
    "caption": "🤍Downloaded by @iBBDownloaderBot",
    "admin_welcome": "🛠 به پنل مدیریت خوش آمدید.\nلطفاً یکی از گزینه‌ها را انتخاب کنید:",
    "stats_text": """📊 <b>آمار ربات</b>

👥 <b>کل کاربران:</b> {total}
🆕 <b>امروز:</b> {today}
📈 <b>هفته گذشته:</b> {week}
📅 <b>ماه گذشته:</b> {month}
📥 <b>کل دانلودها:</b> {downloads}
👑 <b>کاربران ویژه:</b> {premium_users}""",
    "broadcast_prompt": "📝 پیام مورد نظر برای ارسال به تمام کاربران را بنویسید:",
    "broadcast_preview": "📨 <b>پیش‌نمایش پیام همگانی</b>\n\n{message}\n\n👥 تعداد گیرندگان: {count} نفر\n\nآیا از ارسال مطمئن هستید؟",
    "broadcast_cancelled": "❌ ارسال همگانی لغو شد.",
    "broadcast_success": "✅ ارسال همگانی با موفقیت به پایان رسید!\n\n📊 <b>گزارش ارسال:</b>\n• کل کاربران: {total}\n• ارسال موفق: {success}\n• خطا: {failed}",
    "broadcast_progress": "📨 <b>در حال ارسال همگانی...</b>\n\n• ارسال شده: {sent} از {total} ({percent}%)\n• باقی‌مانده: {remaining}\n• خطا: {failed}\n\nبرای بروزرسانی، روی دکمه کلیک کنید.",
    "broadcast_failed": "❌ خطا در ارسال همگانی: {error}",
    "broadcast_empty": "❌ پیام نمی‌تواند خالی باشد.",
    "force_sub_prompt": """🔒 <b>تنظیمات قفل اسپانسر</b>

کانال‌های اجباری فعلی:
{channels}

📌 برای <b>افزودن</b> کانال جدید، روی دکمه زیر کلیک کنید.
📌 برای <b>حذف</b> کانال، روی دکمه مربوطه کلیک کنید.""",
    "force_sub_required": """🔒 <b>برای دسترسی به ربات، ابتدا عضو کانال‌های زیر شوید 🔑</b>

{channels}

پس از عضویت، دکمه زیر را بزنید.""",
    "force_sub_add_prompt": "📝 آیدی کانال جدید را با @ وارد کنید:\nمثال: @MyChannel",
    "force_sub_added": "✅ کانال {channel} با موفقیت اضافه شد.",
    "force_sub_removed": "❌ کانال {channel} با موفقیت حذف شد.",
    "force_sub_not_found": "❌ کانال {channel} در لیست پیدا نشد.",
    "force_sub_verified": "✅ عضویت شما تأیید شد! حالا می‌توانید از ربات استفاده کنید.",
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
    "admin_expired": "⛔ دسترسی شما منقضی شده است. لطفاً با ادمین اصلی تماس بگیرید.",
    "admin_permissions_header": """🔐 <b>دسترسی‌های ادمین</b>

👤 {name} (ID: {user_id})
📋 نقش: {role}

• مشاهده آمار: {stats}
• ارسال همگانی: {broadcast}
• قفل اسپانسر: {force_sub}
• تنظیمات: {settings}
• مدیریت ادمین‌ها: {admins}
• مدیریت ویژه: {premium}
""",
    "permission_toggle_success": "✅ دسترسی {perm} برای ادمین {user_id} تغییر کرد.",
    "settings_text": """⚙️ <b>تنظیمات ربات</b>

⚠️ <b>توجه:</b> تغییر هر یک از تنظیمات زیر بر روی کل ربات اعمال می‌شود و برای همه کاربران تأثیر خواهد داشت. لطفاً با دقت اقدام کنید.

• <b>وضعیت ربات:</b> فعال یا غیرفعال کردن ربات
• <b>سقف دانلود روزانه:</b> حداکثر تعداد دانلود برای هر کاربر در روز
• <b>حداکثر حجم فایل:</b> حداکثر حجم مجاز برای دانلود
• <b>محدودیت زمانی:</b> فاصله زمانی بین دانلودهای هر کاربر
""",
    "settings_updated": "✅ تنظیمات با موفقیت به‌روزرسانی شد.",
    "settings_quota_prompt": "📊 سقف دانلود روزانه را به عدد وارد کنید (0 = نامحدود):",
    "settings_size_prompt": "📦 حداکثر حجم فایل را به مگابایت وارد کنید:",
    "rate_limit_status": """⏱️ <b>تنظیمات محدودیت زمانی بین دانلودها</b>

وضعیت: {status}
زمان انتظار: {seconds} ثانیه

کاربر بعد از هر دانلود باید {seconds} ثانیه صبر کند تا بتواند لینک بعدی را ارسال کند.

برای تغییر، روی دکمه‌های زیر کلیک کنید:""",
    "rate_limit_enabled": "✅ محدودیت زمانی فعال شد! زمان انتظار: {seconds} ثانیه",
    "rate_limit_disabled": "❌ محدودیت زمانی غیرفعال شد.",
    "rate_limit_changed": "⏱️ زمان انتظار به {seconds} ثانیه تغییر کرد.",
    "rate_limit_wait": "⏳ لطفاً {seconds} ثانیه صبر کنید تا بتوانید لینک بعدی را ارسال کنید.\nزمان باقی‌مانده: {remaining} ثانیه",
    "admin_report": """📊 <b>گزارش روزانه ربات</b>

📅 تاریخ: {date}
👥 کل کاربران: {users}
🆕 کاربران جدید امروز: {new_users}
📥 کل دانلودها: {downloads}
📥 دانلودهای امروز: {today_downloads}
❌ خطاهای امروز: {errors}
""",
    "premium_users_list": """👑 <b>کاربران ویژه</b>

{users}
_________________
🔹 برای مدیریت هر کاربر، روی دکمه مربوطه کلیک کنید.""",
    "premium_user_settings": """👑 <b>تنظیمات کاربر ویژه</b>

👤 {name} (ID: {user_id})
📅 تاریخ عضویت: {joined_date}
⏳ وضعیت: {status}
📆 تاریخ انقضا: {expire_date}
📊 سقف دانلود ویژه: {daily_quota}
📦 حجم فایل ویژه: {file_size} MB
⏱️ محدودیت زمانی ویژه: {rate_limit} ثانیه
""",
    "premium_toggle_success": "✅ وضعیت کاربر ویژه تغییر کرد.",
    "premium_expire_prompt": "📆 تعداد روزهای اعتبار را وارد کنید (0 برای نامحدود):",
    "premium_expire_success": "✅ تاریخ انقضای کاربر ویژه با موفقیت به‌روزرسانی شد.",
    "premium_quota_prompt": "📊 سقف دانلود ویژه را به عدد وارد کنید (0 = نامحدود):",
    "premium_size_prompt": "📦 حجم فایل ویژه را به مگابایت وارد کنید:",
    "premium_rate_prompt": "⏱️ محدودیت زمانی ویژه را به ثانیه وارد کنید:",
    "premium_not_found": "❌ کاربر ویژه پیدا نشد.",
    "premium_remove_success": "❌ کاربر از لیست ویژه حذف شد.",
    "premium_add_prompt": "👤 آیدی عددی کاربر را برای افزودن به ویژه وارد کنید:",
}

MESSAGES_EN = {
    "start": """🎬 Welcome to Downloader Bot!

Send your Instagram link to download.

📸 Instagram | 🐦 X | 📱 TikTok | 📌 Pinterest
📷 Snapchat | 🌐 Facebook | 🎧 SoundCloud
💬 Threads | 🔗 Reddit | 🎥 Likee""",
    "lang_selection": "🌍 Please select your language:\nلطفاً زبان مورد نظر خود را انتخاب کنید:",
    "lang_changed": "✅ Language changed to Persian successfully.",
    "lang_changed_en": "✅ Language changed to English successfully.",
    "lang_prompt": "🌍 To change language, click the button below:",
    "downloading": "⏳ Downloading...",
    "invalid_link": "❌ Please send a valid Instagram link.",
    "download_failed": "❌ Download failed. Post might be private or deleted.",
    "send_error": "❌ Error sending file: {error}",
    "caption": "🤍Downloaded by @iBBDownloaderBot",
    "admin_welcome": "🛠 Welcome to Admin Panel.\nPlease select an option:",
    "stats_text": """📊 <b>Bot Statistics</b>

👥 <b>Total Users:</b> {total}
🆕 <b>Today:</b> {today}
📈 <b>Last Week:</b> {week}
📅 <b>Last Month:</b> {month}
📥 <b>Total Downloads:</b> {downloads}
👑 <b>Premium Users:</b> {premium_users}""",
    "broadcast_prompt": "📝 Write the message to send to all users:",
    "broadcast_preview": "📨 <b>Broadcast Preview</b>\n\n{message}\n\n👥 Recipients: {count}\n\nAre you sure you want to send?",
    "broadcast_cancelled": "❌ Broadcast cancelled.",
    "broadcast_success": "✅ Broadcast completed successfully!\n\n📊 <b>Report:</b>\n• Total Users: {total}\n• Success: {success}\n• Failed: {failed}",
    "broadcast_progress": "📨 <b>Sending broadcast...</b>\n\n• Sent: {sent} / {total} ({percent}%)\n• Remaining: {remaining}\n• Failed: {failed}\n\nClick button to update.",
    "broadcast_failed": "❌ Broadcast error: {error}",
    "broadcast_empty": "❌ Message cannot be empty.",
    "force_sub_prompt": """🔒 <b>Force Subscribe Settings</b>

Current channels:
{channels}

📌 Click below to <b>add</b> a channel.
📌 Click on each channel to <b>remove</b> it.""",
    "force_sub_required": """🔒 <b>To access the bot, please join the following channels first 🔑</b>

{channels}

After joining, click the button below.""",
    "force_sub_add_prompt": "📝 Enter new channel ID with @:\nExample: @MyChannel",
    "force_sub_added": "✅ Channel {channel} added successfully.",
    "force_sub_removed": "❌ Channel {channel} removed successfully.",
    "force_sub_not_found": "❌ Channel {channel} not found.",
    "force_sub_verified": "✅ Your membership verified! You can now use the bot.",
    "admin_list": """📋 <b>Admins List</b>

{admins}
_________________
🔹 <b>Roles:</b>
• owner - Full access
• super - Full access except removing owner
• moderator - User management
• viewer - View only""",
    "admin_add_prompt": "👤 Enter user ID to add as admin:",
    "admin_add_success": "✅ User added as admin successfully.\nRole: {role}",
    "admin_remove_success": "❌ Admin removed successfully.",
    "admin_invalid_id": "❌ Invalid ID.",
    "admin_cant_remove_self": "❌ You cannot remove yourself!",
    "admin_cant_remove_owner": "❌ You cannot remove or edit the owner!",
    "admin_no_permission": "⛔ You don't have permission for this action.",
    "admin_expired": "⛔ Your access has expired. Please contact the main admin.",
    "admin_permissions_header": """🔐 <b>Admin Permissions</b>

👤 {name} (ID: {user_id})
📋 Role: {role}

• View Stats: {stats}
• Send Broadcast: {broadcast}
• Manage Force Subscribe: {force_sub}
• Manage Settings: {settings}
• Manage Admins: {admins}
• Manage Premium: {premium}
""",
    "permission_toggle_success": "✅ Permission {perm} for admin {user_id} changed.",
    "settings_text": """⚙️ <b>Settings</b>

⚠️ <b>Warning:</b> Changes to the settings below affect the entire bot and will impact all users. Please proceed with caution.

• <b>Bot Status:</b> Enable or disable the bot
• <b>Daily Quota:</b> Maximum downloads per user per day
• <b>Max File Size:</b> Maximum file size allowed for download
• <b>Rate Limit:</b> Time delay between downloads for each user
""",
    "settings_updated": "✅ Settings updated successfully.",
    "settings_quota_prompt": "📊 Enter daily quota number (0 = unlimited):",
    "settings_size_prompt": "📦 Enter max file size in MB:",
    "rate_limit_status": """⏱️ <b>Rate Limit Settings</b>

Status: {status}
Wait time: {seconds} seconds

Users must wait {seconds} seconds between downloads.

Click buttons below to change:""",
    "rate_limit_enabled": "✅ Rate limit enabled! Wait time: {seconds} seconds",
    "rate_limit_disabled": "❌ Rate limit disabled.",
    "rate_limit_changed": "⏱️ Wait time changed to {seconds} seconds.",
    "rate_limit_wait": "⏳ Please wait {seconds} seconds before sending another link.\nRemaining: {remaining} seconds",
    "admin_report": """📊 <b>Daily Bot Report</b>

📅 Date: {date}
👥 Total Users: {users}
🆕 New Users Today: {new_users}
📥 Total Downloads: {downloads}
📥 Downloads Today: {today_downloads}
❌ Errors Today: {errors}
""",
    "premium_users_list": """👑 <b>Premium Users</b>

{users}
_________________
🔹 Click on each user to manage.""",
    "premium_user_settings": """👑 <b>Premium User Settings</b>

👤 {name} (ID: {user_id})
📅 Joined: {joined_date}
⏳ Status: {status}
📆 Expire Date: {expire_date}
📊 Daily Quota: {daily_quota}
📦 Max File Size: {file_size} MB
⏱️ Rate Limit: {rate_limit} seconds
""",
    "premium_toggle_success": "✅ Premium status changed.",
    "premium_expire_prompt": "📆 Enter number of days (0 for unlimited):",
    "premium_expire_success": "✅ Premium expire date updated successfully.",
    "premium_quota_prompt": "📊 Enter premium daily quota (0 = unlimited):",
    "premium_size_prompt": "📦 Enter premium max file size in MB:",
    "premium_rate_prompt": "⏱️ Enter premium rate limit in seconds:",
    "premium_not_found": "❌ Premium user not found.",
    "premium_remove_success": "❌ User removed from premium list.",
    "premium_add_prompt": "👤 Enter user ID to add as premium:",
}

# ===================================================
# 🔧 توابع دریافت پیام بر اساس زبان
# ===================================================
def get_message(key: str, lang: str = "fa") -> str:
    if lang == "en":
        return MESSAGES_EN.get(key, MESSAGES_FA.get(key, key))
    return MESSAGES_FA.get(key, key)

MESSAGES = MESSAGES_FA

# ===================================================
# ⌨️ دکمه‌های شیشه‌ای (Reply Keyboard - فقط برای ادمین)
# ===================================================
def get_admin_keyboard(lang: str = "fa"):
    """دکمه‌های اصلی پنل ادمین (با دکمه ترکیبی مدیریت کاربران)"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    if lang == "en":
        btn_stats = KeyboardButton("📊 Statistics")
        btn_broadcast = KeyboardButton("📨 Broadcast")
        btn_force_sub = KeyboardButton("🔒 Force Subscribe")
        btn_users = KeyboardButton("👥 Users & Admins")  # ترکیبی
        btn_settings = KeyboardButton("⚙️ Settings")
    else:
        btn_stats = KeyboardButton("📊 آمار ربات")
        btn_broadcast = KeyboardButton("📨 ارسال همگانی")
        btn_force_sub = KeyboardButton("🔒 قفل اسپانسر")
        btn_users = KeyboardButton("👥 مدیریت کاربران و ادمین‌ها")  # ترکیبی
        btn_settings = KeyboardButton("⚙️ تنظیمات ربات")
    keyboard.add(btn_stats, btn_broadcast)
    keyboard.add(btn_force_sub, btn_users)
    keyboard.add(btn_settings)
    return keyboard

def get_user_keyboard():
    return ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)

# ===================================================
# 🔐 دکمه‌های شیشه‌ای (Inline Keyboard)
# ===================================================

def get_admin_inline_keyboard(lang: str = "fa"):
    keyboard = InlineKeyboardMarkup(row_width=2)
    if lang == "en":
        btn_stats = InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")
        btn_broadcast = InlineKeyboardButton("📨 Broadcast", callback_data="admin_broadcast")
        btn_force_sub = InlineKeyboardButton("🔒 Force Subscribe", callback_data="admin_force_sub")
        btn_users = InlineKeyboardButton("👥 Users & Admins", callback_data="admin_admins")
        btn_settings = InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")
        btn_close = InlineKeyboardButton("❌ Close", callback_data="admin_close")
    else:
        btn_stats = InlineKeyboardButton("📊 آمار", callback_data="admin_stats")
        btn_broadcast = InlineKeyboardButton("📨 ارسال همگانی", callback_data="admin_broadcast")
        btn_force_sub = InlineKeyboardButton("🔒 قفل اسپانسر", callback_data="admin_force_sub")
        btn_users = InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_admins")
        btn_settings = InlineKeyboardButton("⚙️ تنظیمات", callback_data="admin_settings")
        btn_close = InlineKeyboardButton("❌ بستن", callback_data="admin_close")
    keyboard.add(btn_stats, btn_broadcast)
    keyboard.add(btn_force_sub, btn_users)
    keyboard.add(btn_settings)
    keyboard.add(btn_close)
    return keyboard

def get_language_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    btn_fa = InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_fa")
    btn_en = InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
    keyboard.add(btn_fa, btn_en)
    return keyboard

def get_stats_refresh_keyboard(lang: str = "fa"):
    keyboard = InlineKeyboardMarkup()
    if lang == "en":
        btn_refresh = InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stats")
        btn_back = InlineKeyboardButton("🔙 Back", callback_data="admin_back")
    else:
        btn_refresh = InlineKeyboardButton("🔄 بروزرسانی", callback_data="refresh_stats")
        btn_back = InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")
    keyboard.add(btn_refresh)
    keyboard.add(btn_back)
    return keyboard

def get_force_sub_keyboard(channels):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for channel in channels:
        btn = InlineKeyboardButton(f"📢 {channel}", url=f"https://t.me/{channel.replace('@', '')}")
        keyboard.add(btn)
    btn_verify = InlineKeyboardButton("✅ Verify", callback_data="force_sub_verify")
    keyboard.add(btn_verify)
    return keyboard

def get_force_sub_inline_keyboard(channels, lang: str = "fa"):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for channel in channels:
        if lang == "en":
            btn_remove = InlineKeyboardButton(f"❌ Remove {channel}", callback_data=f"force_sub_remove_{channel}")
        else:
            btn_remove = InlineKeyboardButton(f"❌ حذف {channel}", callback_data=f"force_sub_remove_{channel}")
        keyboard.add(btn_remove)
    if lang == "en":
        btn_add = InlineKeyboardButton("➕ Add Channel", callback_data="force_sub_add")
        btn_back = InlineKeyboardButton("🔙 Back", callback_data="admin_back")
    else:
        btn_add = InlineKeyboardButton("➕ افزودن کانال", callback_data="force_sub_add")
        btn_back = InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")
    keyboard.add(btn_add)
    keyboard.add(btn_back)
    return keyboard

def get_confirm_keyboard(lang: str = "fa"):
    keyboard = InlineKeyboardMarkup(row_width=2)
    if lang == "en":
        btn_confirm = InlineKeyboardButton("✅ Confirm & Send", callback_data="broadcast_confirm")
        btn_cancel = InlineKeyboardButton("❌ Cancel", callback_data="broadcast_cancel")
    else:
        btn_confirm = InlineKeyboardButton("✅ تأیید و ارسال", callback_data="broadcast_confirm")
        btn_cancel = InlineKeyboardButton("❌ لغو", callback_data="broadcast_cancel")
    keyboard.add(btn_confirm, btn_cancel)
    return keyboard

def get_broadcast_cancel_keyboard(lang: str = "fa"):
    keyboard = InlineKeyboardMarkup()
    if lang == "en":
        btn_cancel = InlineKeyboardButton("❌ Cancel", callback_data="broadcast_cancel_start")
    else:
        btn_cancel = InlineKeyboardButton("❌ لغو ارسال", callback_data="broadcast_cancel_start")
    keyboard.add(btn_cancel)
    return keyboard

def get_broadcast_progress_keyboard(lang: str = "fa"):
    keyboard = InlineKeyboardMarkup(row_width=2)
    if lang == "en":
        btn_refresh = InlineKeyboardButton("🔄 Update", callback_data="broadcast_refresh")
        btn_cancel = InlineKeyboardButton("⏹️ Stop", callback_data="broadcast_cancel_force")
    else:
        btn_refresh = InlineKeyboardButton("🔄 بروزرسانی وضعیت", callback_data="broadcast_refresh")
        btn_cancel = InlineKeyboardButton("⏹️ توقف ارسال", callback_data="broadcast_cancel_force")
    keyboard.add(btn_refresh, btn_cancel)
    return keyboard

# ===================================================
# 🆕 دکمه‌های مدیریت ادمین‌ها و ویژه (با جابجایی)
# ===================================================
def get_admin_list_inline_keyboard(admins, current_user_id, lang: str = "fa"):
    """کیبورد لیست ادمین‌ها با دکمه جابجایی به ویژه"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    for admin in admins:
        uid = admin['user_id']
        name = admin.get('first_name', 'Unknown')
        username = admin.get('username', '')
        role = admin.get('role', 'viewer')
        role_icon = "👑" if role == "owner" else "⭐" if role == "super" else "🔹"
        label = f"{role_icon} {name} (@{username})"
        if admin.get('expire_date'):
            label += " ⏳"
        btn = InlineKeyboardButton(label, callback_data=f"admin_view_{uid}")
        keyboard.add(btn)
    if lang == "en":
        keyboard.add(InlineKeyboardButton("➕ Add Admin", callback_data="admin_add"))
        keyboard.add(InlineKeyboardButton("👑 Manage Premium", callback_data="switch_to_premium"))
        keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
    else:
        keyboard.add(InlineKeyboardButton("➕ افزودن ادمین", callback_data="admin_add"))
        keyboard.add(InlineKeyboardButton("👑 مدیریت ویژه", callback_data="switch_to_premium"))
        keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back"))
    return keyboard

def get_premium_list_inline_keyboard(premium_users, current_user_id, lang: str = "fa"):
    """کیبورد لیست کاربران ویژه با دکمه جابجایی به ادمین‌ها"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    for user in premium_users:
        uid = user['id']
        name = user.get('first_name', 'Unknown')
        username = user.get('username', '')
        days_left = user.get('days_left')
        status_icon = "👑" if days_left is None or days_left > 0 else "⏳"
        label = f"{status_icon} {name} (@{username})"
        if days_left is not None:
            label += f" - {days_left} روز"
        btn = InlineKeyboardButton(label, callback_data=f"premium_view_{uid}")
        keyboard.add(btn)
    if lang == "en":
        keyboard.add(InlineKeyboardButton("➕ Add Premium", callback_data="premium_add"))
        keyboard.add(InlineKeyboardButton("📋 Manage Admins", callback_data="switch_to_admins"))
        keyboard.add(InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
    else:
        keyboard.add(InlineKeyboardButton("➕ افزودن ویژه", callback_data="premium_add"))
        keyboard.add(InlineKeyboardButton("📋 مدیریت ادمین‌ها", callback_data="switch_to_admins"))
        keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back"))
    return keyboard

def get_cancel_keyboard(lang: str = "fa"):
    """کیبورد دکمه لغو برای عملیات‌های درخواست ورودی"""
    keyboard = InlineKeyboardMarkup()
    if lang == "en":
        btn_cancel = InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")
    else:
        btn_cancel = InlineKeyboardButton("❌ لغو", callback_data="cancel_action")
    keyboard.add(btn_cancel)
    return keyboard

# ===================================================
# 🆕 دکمه‌های مدیریت دسترسی ادمین (با مدیریت ویژه)
# ===================================================
def get_admin_permissions_keyboard(admin_user_id, permissions, is_owner=False, lang: str = "fa"):
    keyboard = InlineKeyboardMarkup(row_width=2)
    if lang == "en":
        perm_labels = {
            "can_view_stats": "👁️ View Stats",
            "can_send_broadcast": "📨 Broadcast",
            "can_manage_force_sub": "🔒 Force Subscribe",
            "can_manage_settings": "⚙️ Settings",
            "can_manage_admins": "👥 Manage Admins",
            "can_manage_premium": "👑 Manage Premium"
        }
        expire_label = "📆 Set Expire"
        remove_label = "❌ Remove Admin"
        back_label = "🔙 Back to List"
    else:
        perm_labels = {
            "can_view_stats": "👁️ مشاهده آمار",
            "can_send_broadcast": "📨 ارسال همگانی",
            "can_manage_force_sub": "🔒 قفل اسپانسر",
            "can_manage_settings": "⚙️ تنظیمات",
            "can_manage_admins": "👥 مدیریت ادمین‌ها",
            "can_manage_premium": "👑 مدیریت ویژه"
        }
        expire_label = "📆 تنظیم تاریخ انقضا"
        remove_label = "❌ حذف ادمین"
        back_label = "🔙 بازگشت به لیست"
    for perm_key, perm_label in perm_labels.items():
        status = "✅" if permissions.get(perm_key, False) else "❌"
        btn_status = InlineKeyboardButton(status, callback_data=f"admin_perm_toggle_{admin_user_id}_{perm_key}")
        btn_label = InlineKeyboardButton(perm_label, callback_data=f"perm_{perm_key}")
        keyboard.add(btn_status, btn_label)
    if not is_owner:
        keyboard.add(InlineKeyboardButton(expire_label, callback_data=f"admin_expire_{admin_user_id}"))
        keyboard.add(InlineKeyboardButton(remove_label, callback_data=f"admin_remove_{admin_user_id}"))
    keyboard.add(InlineKeyboardButton(back_label, callback_data="admin_list_back"))
    return keyboard

# ===================================================
# 🆕 دکمه‌های جدید تنظیمات ربات
# ===================================================
def get_settings_new_keyboard(lang: str = "fa", daily_quota: str = "10", max_file_size: str = "50", is_active: bool = True, rate_limit_enabled: bool = False, rate_limit_seconds: int = 30):
    keyboard = InlineKeyboardMarkup(row_width=2)
    # وضعیت ربات (کل عرض)
    if lang == "en":
        status_text = "🟢 Active" if is_active else "🔴 Inactive"
        btn_status = InlineKeyboardButton(f"Bot Status: {status_text}", callback_data="setting_toggle_active")
    else:
        status_text = "🟢 فعال" if is_active else "🔴 غیرفعال"
        btn_status = InlineKeyboardButton(f"وضعیت ربات: {status_text}", callback_data="setting_toggle_active")
    keyboard.add(btn_status)
    # سقف دانلود: مقدار در چپ (قابل کلیک)، برچسب در راست
    if lang == "en":
        btn_quota_value = InlineKeyboardButton(daily_quota, callback_data="setting_quota")
        btn_quota_label = InlineKeyboardButton("📊 Daily Quota", callback_data="dummy")
    else:
        btn_quota_value = InlineKeyboardButton(daily_quota, callback_data="setting_quota")
        btn_quota_label = InlineKeyboardButton("📊 سقف دانلود", callback_data="dummy")
    keyboard.add(btn_quota_value, btn_quota_label)
    # حجم فایل: مقدار در چپ (قابل کلیک)، برچسب در راست
    if lang == "en":
        btn_size_value = InlineKeyboardButton(f"{max_file_size} MB", callback_data="setting_size")
        btn_size_label = InlineKeyboardButton("📦 Max File Size", callback_data="dummy")
    else:
        btn_size_value = InlineKeyboardButton(f"{max_file_size} MB", callback_data="setting_size")
        btn_size_label = InlineKeyboardButton("📦 حجم فایل", callback_data="dummy")
    keyboard.add(btn_size_value, btn_size_label)
    # محدودیت زمانی: مقدار در چپ (قابل کلیک)، برچسب در راست
    if lang == "en":
        rate_status = "✅ On" if rate_limit_enabled else "❌ Off"
        btn_rate_value = InlineKeyboardButton(f"{rate_limit_seconds}s ({rate_status})", callback_data="setting_rate_limit")
        btn_rate_label = InlineKeyboardButton("⏱️ Rate Limit", callback_data="dummy")
    else:
        rate_status = "✅ روشن" if rate_limit_enabled else "❌ خاموش"
        btn_rate_value = InlineKeyboardButton(f"{rate_limit_seconds}s ({rate_status})", callback_data="setting_rate_limit")
        btn_rate_label = InlineKeyboardButton("⏱️ محدودیت زمانی", callback_data="dummy")
    keyboard.add(btn_rate_value, btn_rate_label)
    # دکمه بازگشت (کل عرض)
    if lang == "en":
        btn_back = InlineKeyboardButton("🔙 Back", callback_data="admin_back")
    else:
        btn_back = InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")
    keyboard.add(btn_back)
    return keyboard

def get_settings_inline_keyboard(lang: str = "fa"):
    keyboard = InlineKeyboardMarkup(row_width=2)
    if lang == "en":
        btn_quota = InlineKeyboardButton("📊 Daily Quota", callback_data="setting_quota")
        btn_size = InlineKeyboardButton("📦 File Size", callback_data="setting_size")
        btn_active = InlineKeyboardButton("🔄 Bot Status", callback_data="setting_active")
        btn_rate = InlineKeyboardButton("⏱️ Rate Limit", callback_data="setting_rate_limit")
        btn_back = InlineKeyboardButton("🔙 Back", callback_data="admin_back")
    else:
        btn_quota = InlineKeyboardButton("📊 سقف دانلود", callback_data="setting_quota")
        btn_size = InlineKeyboardButton("📦 حجم فایل", callback_data="setting_size")
        btn_active = InlineKeyboardButton("🔄 وضعیت ربات", callback_data="setting_active")
        btn_rate = InlineKeyboardButton("⏱️ محدودیت زمانی", callback_data="setting_rate_limit")
        btn_back = InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")
    keyboard.add(btn_quota, btn_size)
    keyboard.add(btn_active, btn_rate)
    keyboard.add(btn_back)
    return keyboard

def get_rate_limit_keyboard(lang: str = "fa"):
    keyboard = InlineKeyboardMarkup(row_width=2)
    if lang == "en":
        btn_enable = InlineKeyboardButton("✅ Enable", callback_data="rate_limit_enable")
        btn_disable = InlineKeyboardButton("❌ Disable", callback_data="rate_limit_disable")
        btn_10s = InlineKeyboardButton("⏱️ 10s", callback_data="rate_limit_10")
        btn_30s = InlineKeyboardButton("⏱️ 30s", callback_data="rate_limit_30")
        btn_60s = InlineKeyboardButton("⏱️ 60s", callback_data="rate_limit_60")
        btn_120s = InlineKeyboardButton("⏱️ 120s", callback_data="rate_limit_120")
        btn_back = InlineKeyboardButton("🔙 Back", callback_data="admin_back")
    else:
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

def get_back_keyboard(lang: str = "fa"):
    keyboard = InlineKeyboardMarkup()
    if lang == "en":
        btn_back = InlineKeyboardButton("🔙 Back", callback_data="admin_back")
    else:
        btn_back = InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")
    keyboard.add(btn_back)
    return keyboard

# ===================================================
# 📋 کامندها (برای منوی ربات)
# ===================================================
COMMANDS_FA = [
    BotCommand("start", "شروع و نمایش راهنما"),
    BotCommand("language", "تغییر زبان ربات"),
]
COMMANDS_EN = [
    BotCommand("start", "Start and show help"),
    BotCommand("language", "Change bot language"),
]
COMMANDS = COMMANDS_FA
