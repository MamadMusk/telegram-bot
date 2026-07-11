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
📥 <b>کل دانلودها:</b> {downloads}""",
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
    "force_sub_add_prompt": "📝 آیدی کانال جدید را با @ وارد کنید:\nمثال: @Myثال: @MyChannel",
    "Channel",
    "force_sub_addedforce_sub_added": "✅ ک": "✅ کانانال {channel} با موفقیتال {channel} با موفقیت اضافه شد اضافه شد.",
    "force_sub_removed":.",
    "force_sub "❌ ک_removed": "❌ کانال {channelانال {channel} با موفقیت} با موفقیت حذف شد حذف شد.",
    "force_sub_not_found.",
    "force_sub_not_found": "": "❌ کانال {❌ کانال {channel} در لیchannel} در لیستست پیدا نشد.",
    "force پیدا نشد.",
    "force_sub_verified":_sub_verified": "✅ عضویت شما تأ "✅ عضویت شما تأییدیید شد! حالا شد! حالا می‌توانید از ربات استفاده کنید.",
 می‌توانید از ربات    استفاده کنید.",
    "admin_list": "admin_list": """📋 <b>لیست ادمین """📋 <b>لیست ادمین‌ها</b‌ها</b>

{admins}
________________>

{admins}
_________________
🔹 <b>_
🔹 <b>نقشنقش‌ها:</b‌ها:</b>
• owner ->
• owner - مالک ربات مالک ربات (دسترسی (دسترسی کامل)
• super کامل)
• super - دست - دسترسی کامل به جزرسی کامل به جز حذف owner حذف owner
• moderator -
• moderator - مدیریت کاربران مدیریت کاربران
• viewer - فقط
• viewer - فقط مشاهده""",
    "admin_add مشاهده""",
    "admin_add_prompt": "_prompt": "👤 آیدی👤 آیدی عددی کاربر جدید را برای افزود عددی کاربر جدیدن به عنوان ا را برای افزودن به عنوان ادمین وارد کنید:",
    "دمین وارد کنید:",
    "admin_add_successadmin_add_success": "✅ کاربر با موفقیت به": "✅ کاربر با موفقیت به عنوان ادمین عنوان ادمین اضافه شد.\ اضافه شد.\nنقشnنقش: {role}: {role}",
    "admin",
    "admin_remove_success": "❌_remove_success": "❌ کاربر از لیست کاربر از لیست ادمین‌ها حذ ادمین‌ها حذف شد.",
   ف شد.",
    "admin_invalid_id": "❌ آیدی وارد "admin_invalid_id": "❌ آیدی وارد شده معتبر نیست شده معتبر نیست.",
    "admin_cant_remove.",
    "admin_cant_remove_self": "_self": "❌ نمی‌توانید خود❌ نمی‌توانید خودتان را حذتان را حذف کنید!",
    "admin_cف کنید!",
    "admin_cant_remove_ant_remove_owner": "owner": "❌ نمی‌❌ نمی‌توانید مالکتوانید مالک ربات را ح ربات را حذف یا ویرذف یا ویرایش کنید!ایش کنید!",
    "admin_no_permission": "",
    "admin_no⛔ شما دسترسی لازم برای_permission": "⛔ شما دسترسی لازم برای این کار را ندار این کار را ندارید.",
    "admin_expired":ید.",
    "admin_expired": "⛔ "⛔ دسترسی شما منقضی شده دسترسی شما منقضی شده است. لطف است. لطفاً با ادماً با ادمین اصلی تماس بگیرید.",
   ین اصلی تماس بگیرید.",
    "admin_permissions "admin_permissions_header": """_header": """🔐 <b>🔐 <b>دسترسیدسترسی‌های ادم‌های ادمین</bین</b>

👤 {name} (ID:>

👤 {name {user_id} (ID: {user_id})
📋 نقش: {role}

•})
📋 نقش: مشاهده آ {role}

• مشاهده آمار: {statsمار: {stats}
• ار}
• ارسال همگانیسال همگانی: {broadcast: {broadcast}
• قفل اسپان}
• قفل اسپانسر:سر: {force {force_sub}
• تنظ_sub}
• تنظیماتیمات: {: {settings}
• مدیریت ادمینsettings}
• مدیریت ادمین‌ها: {‌ها: {admins}
""admins}
""",
    "per",
    "permission_toggle_smission_toggle_success": "✅uccess": "✅ دسترسی {perm دسترسی {perm} برای ادمین {user_id} برای ادمین {user_id} تغییر کرد.",
    "settings_list} تغییر کرد.",
    "settings_list": """": """⚙️ <b⚙️ <b>تنظیم>تنظیمات ربات</ات ربات</b>

📌 <b>کانb>

📌 <b>کانال‌هایال‌های اجباری:</b> {ch اجباری:</b> {channels}
📌annels}
📌 <b>س <b>سقف دانلود روزانه:</b> {dailyقف دانلود روزانه:</b> {daily_quota}_quota} 
📌 <b 
📌 <b>حداکثر حجم فایل>حداکثر حجم فایل:</b> {max_file_size:</b> {max_file_size}} MB
📌 <b>و MB
📌 <b>وضعیت ربات:</b> {ضعیت ربات:</b> {is_activeis_active}
📌 <b>محد}
📌 <b>محدودیت زمانی:</b>ودیت زمانی:</b> {rate_limit_status {rate_limit_status} ({rate_limit_seconds} ث} ({rate_limit_seconds} ثانیه)""انیه)""",
    "settings_updated": "",
    "settings_updated": "✅ تنظیمات✅ تنظیمات با موفقیت به با موفقیت به‌روزرسانی شد‌روزرسانی شد.",
    "settings_.",
    "settings_quota_prompt": "📊quota_prompt": "📊 سقف دان سقف دانلود روزانه رالود روزانه را به عدد وارد کنید به عدد وارد کنید (0 = نامحدود): (0 = نامحدود):",
    "settings_size_prompt": "",
    "settings_size_prompt": "📦 حداکثر حجم ف📦 حداایل را به مگکثر حجم فایل را به مگابابایت وارد کنید:",
   ایت وارد کنید:",
    "rate_limit_status "rate_limit_status": """": """⏱️⏱️ <b>تنظ <b>تنظیمات محدودیمات محدودیت زمانی بین دانیت زمانی بین دانلودها</b>

وضعیت: {statusلودها</b}
زمان انتظ>

وضعیت: {statusار: {seconds}
زمان انتظار: {seconds} ثانیه} ثانیه

کاربر بعد

کاربر بعد از هر دانلود از هر دانلود باید {seconds} باید {seconds} ثانیه ص ثانیه صبر کند تا بتوانبر کند تا بتواند لد لینک بعدی راینک بعدی را ار ارسال کند.

برایسال کند.

برای تغییر، روی د تغییر، روی دکمه‌های زیر کلیککمه‌ کنید:""های زیر کلیک کنید:""",
    "rate_limit_enabled": "",
    "rate_limit_enabled":✅ محدودیت "✅ محدودیت زمانی فعال شد! زمان انتظار زمانی فعال شد! زمان انتظار: {seconds}: {seconds} ثانیه ثانیه",
    "rate_limit_dis",
    "rate_limit_disabled": "abled": "❌ محدودیت زمانی غیرف❌ محدودیت زمانی غیرفعال شد.",
   عال شد.",
    "rate_limit_ch "rate_limit_changed": "anged": "⏱️ زمان انتظار به⏱️ زمان انتظار به {seconds} ث {seconds} ثانیه تغییر کردانیه تغییر کرد.",
    "rate.",
    "rate_limit_wait":_limit_wait": "⏳ "⏳ لطفاً { لطفاً {seconds} ثانیseconds} ثانیه صه صبر کنید تا بتوانبر کنید تا بتوانید لید لینک بعدیینک بعدی را ارسال کنید را ارسال کنید.\nزمان باقی‌.\nزمان باقی‌مانده: {مانده: {remaining} ثانیremaining} ثانیه",
    "admin_report": """ه",
    "admin_report": """📊 <b📊 <b>گزارش روزانه ربات</b>گزارش روزانه ربات>

📅 تاریخ:</b>

📅 تاریخ: {date {date}
👥 کل کاربران}
👥 کل کاربران: {users: {users}
🆕 کاربران جدید}
🆕 کاربران جدید امروز: { امروز: {new_users}
📥new_users}
📥 کل دانلود کل دانلودها: {downloadها: {downloads}
📥 دانلودهای امروs}
📥 دانلودهای امروز: {todayز: {today_downloads_downloads}
❌ خطا}
❌ خطاهای امروز:های امروز: {errors}
"" {errors}
""",
}

MESSAGES_EN =",
}

MESSAGES_EN = {
    "start": {
    "start": """🎬 Welcome """🎬 Welcome to Downloader Bot to Downloader Bot!

Send your Instagram!

Send your Instagram link to download link to download.

📸.

📸 Instagram | 🐦 X Instagram | 🐦 X | 📱 TikTok | 📱 TikTok | 📌 Pinterest | 📌 Pinterest
📷 Snap
📷 Snapchat | 🌐 Facebook |chat | 🌐 Facebook | 🎧 SoundCloud 🎧 SoundCloud
💬 Thread
💬 Threadss | 🔗 Red | 🔗 Reddit |dit | 🎥 Likee"" 🎥 Likee""",
    "lang",
    "lang_selection": "🌍 Please select your language:\n_selection": "🌍 Please selectلطفاً زبان your language:\nلطفاً زبان مورد نظر خود را مورد نظر خود را انتخاب کنید:",
    "lang_ch انتخاب کنید:",
    "lang_changed": "✅anged": "✅ Language changed to Persian Language changed to Persian successfully.",
    " successfully.",
    "lang_changed_en": "✅ Languagelang_changed_en": "✅ Language changed to English successfully changed to English successfully.",
    "lang_prompt": ".",
    "lang_prompt": "🌍 To change language, click the button below:🌍 To change language, click the button below:",
    "downloading": "⏳ Downloading...",
    "downloading": "⏳ Downloading...",
    "invalid",
    "invalid_link": "_link": "❌ Please send a valid Instagram link❌ Please send a valid Instagram link.",
    "download.",
    "download_failed": "❌ Download failed_failed": "❌ Download failed. Post might. Post might be private or deleted.",
    "send be private or deleted.",
   _error": " "send_error": "❌ Error sending file❌ Error sending file: {error}",
    "caption: {error}",
    "caption": "🤍Downloaded by @": "🤍Downloaded by @iBBDownloadiBBDownloaderBot",
   erBot",
    "admin_welcome "admin_welcome": "": "🛠 Welcome to Admin🛠 Welcome to Admin Panel.\nPlease select an option: Panel.\nPlease select an option:",
    "stats",
    "stats_text": """_text": """📊 <b>📊 <b>Bot Statistics</bBot Statistics</b>

👥>

👥 <b>Total Users:</b> { <b>Total Users:</b> {total}
total}
🆕 <b🆕 <b>Today:</b>Today:</b> {today> {today}
📈}
📈 <b>Last Week:</b> <b>Last {week Week:</b> {week}
📅 <b>}
📅 <b>Last Month:</b> {monthLast Month:</b> {month}
📥 <b}
📥 <b>Total Downloads:</>Total Downloads:</b> {downloadb> {downloads}""s}""",
    "broad",
    "broadcastcast_prompt": "📝 Write the message_prompt": "📝 to send to Write the message to send to all users:",
    "broadcast_preview": " all users:",
    "broadcast_preview": "📨 <b📨 <b>Broadcast Preview</b>\n>Broadcast Preview</b>\n\n{message}\\n{message}\n\n👥 Recipients: {count}\n\nn\n👥 Recipients: {count}\n\nAre you sure youAre you sure you want to send want to send?",
    "broad?",
    "broadcast_cancelledcast_cancelled": "❌": "❌ Broadcast cancelled.",
    Broadcast cancelled.",
    "broadcast_s "broadcast_success": "✅uccess": "✅ Broadcast completed successfully!\ Broadcast completed successfully!\n\n📊 <b>Reportn\n📊:</b>\n <b>Report:</b>\n• Total Users• Total Users: {total}\n• Success: {total}\n• Success: {success}\: {success}\n• Failed:n• Failed: {failed} {failed}",
    "broadcast",
    "broadcast_progress": "📨 <b_progress": ">Sending broadcast...</b>\n📨 <b>Sending broadcast...</b>\n\n\n• Sent: {• Sent: {sent} / {total} ({sent} / {total} ({percentpercent}%)\n}%)\n• Remaining: {• Remaining: {remaining}\nremaining}\n• Failed: {• Failed: {failed}\n\nfailed}\n\nClick button to updateClick button to update.",
    "broadcast_failed":.",
    "broad "❌ Broadcast error: {errorcast_failed": "❌ Broadcast error: {error}",
    "}",
    "broadcast_empty":broadcast_empty": "❌ Message "❌ Message cannot be empty cannot be empty.",
    "force_sub_prompt": """.",
    "force_sub_prompt": """🔒 <b🔒 <b>Force Subscribe Settings>Force Subscribe Settings</b>

Current</b>

Current channels:
{ channels:
{channelschannels}

📌 Click below to}

📌 Click below to <b>add <b>add</b> a</b> a channel.
 channel.
📌 Click on each channel to <b>📌 Click on each channel to <b>remove</b>remove</ it.""",
   b> it.""",
    "force_sub_ "force_sub_required": """required": """🔒 <b>To access the bot🔒 <b>To access the bot, please join the following channels first 🔑, please join the following channels first</b>

{channels 🔑</b}

After joining, click>

{channels}

After joining, click the button below."" the button below.""",
    "force_sub_add_prompt",
    "force_sub_add_prompt": "📝 Enter new channel ID": "📝 Enter new channel with @:\n ID with @:\nExample: @MyChannel",
    "Example: @MyChannel",
    "force_sub_addedforce_sub_added": "✅ Channel": "✅ Channel {channel} added successfully.",
    " {channel} added successfully.",
    "force_sub_remforce_sub_removed": "❌ Channel {channeloved": "❌ Channel {channel} removed successfully} removed successfully.",
    "force_sub_not_found": "❌ Channel.",
    "force_sub_not_found": "❌ Channel {channel} not {channel} not found.",
    "force_sub_verified found.",
    "force_sub_verified": "✅ Your": "✅ Your membership verified! You can now use the membership verified! You can now use the bot.",
    " bot.",
    "admin_list": """📋 <badmin_list": """📋 <b>Admins List>Admins List</b>

{</b>

{admins}
_________________
🔹admins}
_________________
🔹 <b>Roles:</b>
• owner - Full access <b>Roles:</b>
• owner - Full access
• super - Full
• super - Full access except removing owner
• moderator access except removing owner
• moderator - User - User management
• viewer management
• viewer - View only""",
    "admin - View only""",
    "admin_add_prompt": "👤 Enter user_add_prompt": "👤 Enter user ID to add as admin: ID to add as admin:",
    "admin_add_success": "",
    "admin_add✅ User added as_success": "✅ User added as admin successfully.\nRole: {role admin successfully.\n}",
    "Role: {role}",
    "admin_remove_sadmin_remove_success": "uccess": "❌ Admin removed successfully❌ Admin removed successfully.",
    "admin.",
    "admin_invalid_id": "❌ Invalid_invalid_id": ID.",
    " "❌ Invalidadmin_cant_ ID.",
    "admin_cant_remove_self": "❌ Youremove_self": "❌ You cannot remove cannot remove yourself! yourself!",
    "admin",
    "admin_cant_remove_owner": "_cant_remove_owner": "❌ You cannot❌ You cannot remove or edit the owner!",
    "admin_no_per remove or edit the owner!",
    "admin_no_permission": "mission": "⛔ You don⛔ You don't have permission for't have permission for this action.",
    this action.",
    "admin_expired": " "admin_expired": "⛔ Your access has⛔ Your access has expired. Please contact the main admin expired. Please contact.",
    "admin_per the main admin.",
    "admin_permissions_header": """missions_header": """🔐 <b>Admin Permissions🔐 <b>Admin Permissions</b</b>

👤 {name} (ID: {>

👤 {name} (ID: {user_iduser_id})
📋 Role: {})
📋 Role: {role}

• Viewrole}

• View Stats: {stats}
• Send Stats: {stats}
• Send Broadcast: {broad Broadcast: {broadcast}
• Managecast}
• Manage Force Subscribe: { Force Subscribe: {force_sub}
•force_sub}
• Manage Settings: { Manage Settings: {settings}
• Managesettings}
• Manage Admins: { Admins: {admins}
""admins}
""",
    "per",
    "permission_toggle_success": "✅mission_toggle_success": "✅ Permission {perm Permission {perm} for admin {user_id} changed} for admin {user_id} changed.",
    "settings.",
    "settings_list": """_list": """⚙️ <b>Bot Settings</⚙️ <b>Bot Settings</b>

📌 <b>Force Channels:</b>b>

📌 <b>Force Channels:</b> {channels {channels}
📌 <b>Daily Quota}
📌 <b:</b> {>Daily Quota:</b> {daily_quota} 
📌 <b>Maxdaily_quota} 
📌 <b>Max File Size:</b File Size:</b> {max_file> {max_file_size} MB_size} MB
📌 <b
📌 <b>Bot Status:</>Bot Status:</b> {is_active}
📌b> {is_active}
📌 <b>Rate Limit:</b> <b>Rate Limit:</b> {rate_limit_status {rate_limit_status} ({rate_limit} ({rate_limit_seconds} seconds_seconds} seconds)""",
   )""",
    "settings_updated": "✅ Settings "settings_updated updated successfully.",
   ": "✅ Settings updated successfully.",
    "settings_quota_prompt": "settings_qu "📊 Enterota_prompt": "📊 Enter daily quota number ( daily quota number (0 = unlimited):",
    "settings0 = unlimited):",
    "settings_size_prompt":_size_prompt": "📦 Enter "📦 Enter max file size in MB:",
    max file size in MB:",
    "rate_limit_status "rate_limit_status": """⏱️": """⏱️ <b>Rate Limit <b>Rate Limit Settings</b>

Status: {status Settings</b>

Status: {status}
Wait time: {seconds} seconds

Users}
Wait time: {seconds} seconds

Users must wait { must wait {seconds} seconds between downloads.

Clickseconds} seconds between downloads.

Click buttons buttons below to change: below to change:""",
    """",
    "rate_limit_enabled": "✅ Raterate_limit_enabled": "✅ Rate limit enabled! Wait limit enabled! Wait time: {seconds} seconds",
    time: {seconds} seconds",
 "rate_limit_dis    "rate_limit_disabled": "abled": "❌ Rate limit disabled❌ Rate limit disabled.",
    "rate.",
    "rate_limit_changed":_limit_changed": "⏱️ Wait time changed "⏱️ Wait time changed to {seconds} to {seconds} seconds.",
    "rate_limit seconds.",
    "rate_limit_wait_wait": "": "⏳ Please wait {⏳ Please wait {seconds}seconds} seconds before sending another link seconds before sending another link.\nRemaining.\nRemaining: {remaining}: {remaining} seconds",
    " seconds",
    "admin_report": """📊 <badmin_report": """📊 <b>Daily Bot Report>Daily Bot Report</b</b>

📅 Date: {>

📅 Date: {date}
👥date}
👥 Total Users: {users Total Users: {users}
🆕 New Users}
🆕 New Users Today: {new Today: {new_users_users}
📥 Total Downloads:}
📥 Total Downloads: {downloads}
📥 Downloads Today {downloads}
📥 Downloads Today: {today: {today_downloads_downloads}
❌ Errors Today}
❌ Errors Today: {errors: {errors}
""",
}

#}
""",
}

# ================================================= ===================================================
#==
# 🔧 توابع دریافت پیام بر 🔧 توابع دریافت پیام بر اساس زبان
# اساس زبان
# =================================================== ===================================================
def
def get_message(key get_message(key: str, lang: str, lang: str = ": str = "fa") -> strfa") -> str:
    """در:
    """دریافت پیامیافت پیام بر اساس زبان کاربر بر اساس زبان کاربر"""
    if lang"""
    if lang == "en == "en":
        return MESS":
        return MESSAGES_EN.get(keyAGES_EN.get(key, MESSAGES_FA.get(key, MESSAGES_FA.get(key, key))
   , key))
    return MESSAGES return MESSAGES_FA.get(key_FA.get(key, key)

#, key)

# Ali Aliasesases for for backward compatibility
M backward compatibility
MESSAGES = MESSAGES_FAESSAGES = MESSAGES_FA

# ===================================================
#

# ===================================================
# ⌨ ⌨️ دکمه‌️ دکمه‌های شیشههای شیشه‌ای (Reply‌ای (Reply Keyboard)
# = Keyboard)
# =====================================================================================================
def get_admin_key
def get_admin_keyboard(langboard(lang:: str = "fa"):
    keyboard str = "fa"):
    keyboard = ReplyKeyboardMark = ReplyKeyboardMarkup(resize_keyup(resize_keyboard=True, rowboard=True, row_width=2_width=2)
    if lang ==)
    if lang == "en":
        "en":
        btn_stats = Keyboard btn_stats = KeyboardButton("📊 Statistics")
        btnButton("📊 Statistics")
        btn_broadcast =_broadcast = KeyboardButton("📨 Broadcast")
        btn_force_sub KeyboardButton("📨 Broadcast")
        btn_force_sub = KeyboardButton(" = KeyboardButton("🔒 Force Subscribe🔒 Force Subscribe")
        btn_ad")
        btn_admins = KeyboardButtonmins = KeyboardButton("📋 Manage("📋 Manage Admins")
        Admins")
        btn_settings = Keyboard btn_settings = KeyboardButton("⚙Button("⚙️ Settings")
   ️ Settings")
    else:
        btn_stats = KeyboardButton else:
        btn("📊 آ_stats = KeyboardButton("📊 آمار ربات")
        btnمار ربات")
        btn_broadcast = KeyboardButton_broadcast = KeyboardButton("📨 ار("📨 ارسال همگانی")
سال همگانی")
        btn_        btn_force_sub = Keyboardforce_sub = KeyboardButton("🔒 قButton("🔒فل اسپانسر")
        قفل اسپانسر")
        btn_admins = KeyboardButton(" btn_admins = KeyboardButton("📋 مدیریت ادمین‌ها")
        btn_settings = KeyboardButton("⚙️📋 مدیریت ادمین‌ها")
        btn_settings = KeyboardButton("⚙️ تنظیمات ربات")
    keyboard تنظیمات ربات")
    keyboard.add(btn.add(btn_stats, btn_broad_stats, btn_broadcast)
    keyboardcast)
    keyboard.add(btn_force_sub, btn_admins)
   .add(btn_force_sub, btn keyboard.add(btn_admins)
   _settings)
    return keyboard

def get keyboard.add(btn_settings)
_user_keyboard    return keyboard

def get():
    return ReplyKeyboardMarkup(resize_user_keyboard():
    return ReplyKeyboardMarkup(resize_keyboard=True, row_width=1_keyboard=True,)

# ===================================================
# row_width=1)

# ================================= 🔐 دک==================
# 🔐 دکمه‌هایمه‌های شیشه‌ شیشه‌ای (Inline Keyboardای (Inline Keyboard)
# =================================)
# ===================================================
def==================
def get_language_key get_language_keyboard():
    keyboardboard():
    keyboard = InlineKeyboard = InlineKeyboardMarkup(rowMarkup(row_width=2_width=2)
    btn_fa)
    btn_fa = InlineKeyboard = InlineKeyboardButton("🇮Button("🇮🇷 فارسی",🇷 فارسی", callback_data="lang_fa")
    callback_data="lang_fa")
    btn_en = In btn_en = InlineKeyboardButton("lineKeyboardButton("🇬🇧🇬🇧 English", callback_data English", callback_data="lang_en="lang_en")
    keyboard.add(btn_fa")
    keyboard.add(btn_fa, btn_en)
   , btn_en)
    return keyboard

def get_stats_refresh return keyboard

def_keyboard():
    get_stats_refresh_keyboard():
    keyboard = InlineKeyboardMarkup keyboard = Inline()
    btn_refKeyboardMarkup()
    btn_refresh = Inlineresh = InlineKeyboardButton("KeyboardButton("🔄 Refresh", callback🔄 Refresh", callback_data="refresh_stats")
    keyboard_data="refresh_stats")
    keyboard.add(btn.add(btn_ref_refresh)
    return keyboard

def getresh)
    return_force_sub_key keyboard

def get_force_sub_keyboard(channelsboard(channels):
    keyboard = In):
    keyboard = InlineKeyboardMarkuplineKeyboardMarkup(row_width=1)
    for channel(row_width=1)
    for channel in channels:
        in channels:
        btn = Inline btn = InlineKeyboardButton(fKeyboardButton(f""📢 {channel📢 {channel}", url=f"}", url=f"https://t.me/{channel.replace('https://t.me/{channel.replace('@', '')@', '')}")
        keyboard}")
        keyboard.add.add(btn)
    btn_verify =(btn)
    btn_verify = InlineKeyboardButton InlineKeyboardButton("✅("✅ Verify", callback_data="force Verify", callback_data="force_sub_verify_sub_verify")
    keyboard.add(btn_verify")
    keyboard.add(btn_verify)
    return keyboard)
    return keyboard

def get_confirm

def get_confirm_keyboard(lang_keyboard(lang: str = ": str = "fa"):
    keyboardfa"):
    keyboard = InlineKeyboardMarkup(row_width = InlineKeyboardMarkup(row_width=2)
   =2)
    if lang == "en":
        btn if lang == "en":
        btn_confirm = In_confirm = InlineKeyboardButton("lineKeyboardButton("✅ Confirm & Send", callback_data="✅ Confirm & Send", callback_data="broadcast_confirmbroadcast_confirm")
        btn_cancel =")
        btn_cancel = InlineKeyboardButton(" InlineKeyboardButton("❌ Cancel", callback❌ Cancel", callback_data="broadcast_cancel")
   _data="broadcast_cancel")
    else:
        btn else:
        btn_confirm = In_confirm = InlineKeyboardButton("lineKeyboardButton("✅ تأیید✅ تأیید و ارسال", callback_data="broad و ارسال", callback_data="broadcast_confirm")
        btncast_confirm")
        btn_cancel = In_cancel = InlineKeyboardlineKeyboardButton("❌Button("❌ لغو", callback لغو", callback_data="broadcast_data="broadcast_cancel")
   _cancel")
    keyboard.add(btn keyboard.add(btn_confirm, btn_cancel)
   _confirm, btn_cancel return keyboard

def)
    return keyboard

def get_broadcast_cancel_keyboard get_broadcast_cancel_keyboard(lang: str(lang: str = "fa = "fa"):
    keyboard = In"):
    keyboard = InlineKeyboardMarklineKeyboardMarkup()
    if lang == "enup()
    if lang":
        btn_c == "enancel = InlineKeyboardButton("":
        btn_cancel = InlineKeyboardButton("❌❌ Cancel", callback_data Cancel", callback_data="broadcast_c="broadcast_cancel_start")
   ancel_start")
    else else:
:
        btn_cancel = Inline        btn_cancel = InlineKeyboardButton("❌ لغو ارسال", callbackKeyboardButton("❌ لغو_data="broadcast ارسال", callback_data="broadcast_cancel_start")
    keyboard.add_cancel_start(btn_cancel")
    keyboard.add(btn_cancel)
    return keyboard)
    return keyboard

def get_broad

def get_broadcast_progress_keycast_progress_keyboard(lang:board(lang: str = "fa str = "fa"):
    keyboard ="):
    keyboard = InlineKeyboardMark InlineKeyboardMarkup(row_width=up(row_width=2)
    if lang == "en2)
    if lang == "en":
        btn_refresh = Inline":
        btn_refresh = InlineKeyboardButton("KeyboardButton("🔄 Update", callback🔄 Update", callback_data="broadcast_data="broadcast_refresh")
       _refresh")
        btn_cancel = btn_cancel = InlineKeyboardButton InlineKeyboardButton("⏹("⏹️ Stop", callback️ Stop", callback_data="broadcast_data="broadcast_cancel_force")
    else_cancel_force")
    else:
        btn_ref:
        btn_refreshresh = InlineKeyboard = InlineKeyboardButton("🔄Button("🔄 بروزرسانی بروزرسانی وضعیت", callback_data="broadcast_refresh")
        وضعیت", callback_data="broadcast_refresh")
        btn_cancel = btn_cancel = InlineKeyboardButton InlineKeyboardButton("⏹("⏹️ توقف ار️ توقف ارسال", callback_data="broadcast_cسال", callback_dataancel_force="broadcast_cancel_force")
    keyboard.add(")
    keyboard.add(btn_refresh,btn_refresh, btn_c btn_cancelancel)
    return keyboard)
    return keyboard

def get_admin_list

def get_admin_list_inline_keyboard(admins,_inline_keyboard current_user_id,(admins, current_user_id lang: str = "fa"):
, lang: str = "fa"):
       keyboard = Inline keyboard = InlineKeyboardMarkup(rowKeyboardMarkup(row_width=1_width=1)
    for admin in)
    for admin in admins:
 admins:
               uid = admin[' uid = admin['user_id']
user_id']
               name = admin.get name = admin.get('first_name('first_name',', 'Unknown')
        username = admin.get 'Unknown')
        username = admin.get('username', '('username', '')
        role =')
        role = admin.get('role admin.get('role', 'view', 'viewer')
        roleer')
        role_icon = "👑" if_icon = "👑" if role == " role == "owner" else "owner" else "⭐"⭐" if role if role == "super" == "super" else "🔹 else "🔹"
        label ="
        label = f"{role_ f"{role_icon} {nameicon} {name} (@{username} (@{username})"
        if admin.get('exp})"
        if admin.get('expire_date'):
            labelire_date'):
            label += " += " ⏳"
        ⏳"
        btn = Inline btn = InlineKeyboardButton(label,KeyboardButton(label, callback_data=f" callback_data=f"admin_view_{uidadmin_view_{uid}")
        keyboard.add}")
        keyboard.add(btn)
   (btn)
    if lang == "en":
        keyboard if lang == ".add(InlineKeyboarden":
        keyboard.add(InlineKeyboardButton("➕ AddButton("➕ Add Admin", callback_data Admin", callback_data="admin_add="admin_add"))
        keyboard.add("))
        keyboard.add(InlineKeyboardButton("InlineKeyboardButton("🔙🔙 Back", callback_data="admin Back", callback_data="admin_back"))
    else:
        keyboard.add_back"))
    else:
        keyboard.add(Inline(InlineKeyboardButtonKeyboardButton("➕ افز("➕ افزودن ادمودن ادمین", callback_dataین", callback_data="admin_add="admin_add"))
        keyboard.add(InlineKeyboardButton(""))
        keyboard.add(InlineKeyboardButton("🔙 بازگشت", callback_data🔙 بازگشت", callback_data="admin_back="admin_back"))
   "))
    return keyboard

def get_admin_per return keyboard

def get_admin_permissions_keyboard(missions_keyboard(admin_user_id,admin_user_id, permissions, is_ permissions, is_owner=False, lang: str = "owner=False, lang: str = "fa"):
    keyboard = InlineKeyboardfa"):
    keyboard = InlineKeyboardMarkup(row_widthMarkup(row_width=2)
   =2)
    if if lang == " lang == "en":
        permen":
        perm_labels = {
_labels = {
            "can_view_stats": "            "can_view_stats👁️ View Stats": "",
            "can_send👁️ View Stats",
            "can_broadcast": "_send_broadcast": "📨 Broadcast",
📨 Broadcast",
                       "can_manage_force_sub": "can_manage_force_sub": "🔒 Force "🔒 Force Subscribe",
            " Subscribe",
            "can_can_manage_settingsmanage_settings": "⚙️ Settings",
           ": "⚙️ Settings",
            "can_manage "can_manage_admins": "👥 Manage Adm_admins": "ins"
       👥 Manage Admins"
        }
        remove_label = }
        remove_label = "❌ Remove "❌ Remove Admin"
        back Admin"
        back_label = "🔙 Back to List_label = "🔙 Back to List"
"
    else    else:
        perm_labels =:
        perm_labels = {
            "can_view_stats": " {
            "can_view_stats": "👁️ مشاه👁️ مشاهده آمارده آمار",
            "can_send_broadcast",
            "can_s": "📨end_broadcast": "📨 ارسال همگانی",
            "can ارسال همگانی",
            "can_manage__manage_force_sub": "force_sub": "🔒 قفل🔒 قفل اسپانسر",
            " اسپانسر",
            "can_manage_settingscan_manage_settings": "⚙️ تنظیمات",
            "can": "⚙️ تنظیمات",
            "can_manage_admins": "👥_manage_admins": "👥 مدیریت ادم مدیریت ادمین‌هاین‌ها"
        }
        remove_label = ""
        }
        remove_label = "❌ حذ❌ حذف ادمین"
        back_label = "🔙ف ادمین"
        back_label = "🔙 بازگشت به بازگشت به لیست"
    
    for perm_key لیست"
    
    for perm_key, perm_label in, perm_label in perm_labels.items():
        status = " perm_labels.items():
        status =✅" if permissions "✅" if permissions.get(perm_key, False) else.get(perm_key, False) else "❌ "❌"
        btn = In"
        btn = InlineKeyboardlineKeyboardButton(
            f"{statusButton(
            f"{status} {perm_label}",
            callback_data=f"admin} {perm_label}",
            callback_data=f"admin_perm_toggle_perm_toggle_{admin_user_id}_{perm_key_{admin_user_id}_{perm_key}"
        )
        keyboard}"
        )
        keyboard.add(btn.add(btn)
    if not is_owner:
       )
    if not is_owner:
        keyboard.add(Inline keyboard.add(InlineKeyboardButton(remove_label, callback_data=f"admin_KeyboardButton(remove_label, callback_data=f"admin_remove_{admin_user_id}"))
    keyboard.add(Inlineremove_{admin_user_id}"))
    keyboard.add(InlineKeyboardButton(backKeyboardButton(back_label, callback_data="admin_list_back_label, callback_data="admin_list_back"))
    return keyboard"))
    return keyboard

def get_force_sub_inline

def get_force_sub_inline_keyboard(ch_keyboard(channels, lang: str = "faannels, lang: str = "fa"):
    keyboard ="):
    keyboard = InlineKeyboardMarkup(row InlineKeyboardMarkup(row_width=_width=1)
    for1)
    for channel in channels:
        if lang == channel in channels:
        if lang "en":
            == "en":
            btn_remove = btn_remove = InlineKeyboardButton InlineKeyboardButton(f"❌ Remove {channel}",(f"❌ Remove {channel}", callback_data=f" callback_data=f"force_sub_remove_{channel}")
       force_sub_remove_{channel}")
        else:
            btn else:
            btn_remove = In_remove = InlineKeyboardButton(flineKeyboardButton(f"❌ ح"❌ حذف {channelذف {channel}", callback_data=f"force_sub_}", callback_data=f"force_sub_remove_{channel}")
        keyboard.add(remove_{channelbtn_remove}")
        keyboard.add(btn_remove)
    if lang == "en":
        btn_add = In)
    if lang == "en":
        btn_add =lineKeyboardButton(" InlineKeyboardButton("➕ Add Channel➕ Add Channel", callback_data="", callback_data="force_sub_add")
        btn_back =force_sub_add")
        btn_back = InlineKeyboardButton InlineKeyboardButton("🔙 Back("🔙 Back", callback_data="admin_back")
    else:
", callback_data="        btn_add = Inlineadmin_back")
    else:
        btnKeyboardButton("➕ افز_add = Inlineودن کانال", callbackKeyboardButton("➕ افزودن کانال", callback_data="force_sub_data="force_sub_add")
        btn_back = InlineKeyboardButton("_add")
        btn_back = InlineKeyboardButton("🔙 بازگشت", callback_data="🔙 بازگشت", callback_data="admin_back")
   admin_back")
    keyboard.add(btn_add keyboard.add(btn_add)
)
    keyboard.add(btn_back    keyboard.add(btn_back)
    return keyboard)
    return keyboard

def get_settings_inline_keyboard

def get_settings_inline_keyboard(lang: str(lang: str = "fa"):
    = "fa"):
    keyboard = In keyboard = InlineKeyboardMarkuplineKeyboardMarkup(row_width=2)
    if lang == "en(row_width=2)
    if lang == "en":
        btn_qu":
        btn_quota = InlineKeyboardButton("ota = InlineKeyboardButton("📊 Daily Quota📊 Daily Quota", callback_data="setting_quota", callback_data="setting")
        btn_size_quota")
        btn_size = InlineKeyboardButton("📦 = InlineKeyboard File Size", callbackButton("📦 File Size", callback_data="setting_size_data="setting_size")
        btn_active = InlineKeyboard")
        btn_active = InlineKeyboardButton("🔄Button("🔄 Bot Status", callback_data="setting_active Bot Status", callback_data="setting_active")
        btn_rate")
        btn_rate = InlineKeyboardButton(" = InlineKeyboardButton("⏱️ Rate Limit⏱️ Rate Limit", callback_data="", callback_data="setting_rate_limit")
        btnsetting_rate_limit")
        btn_back =_back = InlineKeyboardButton InlineKeyboardButton("🔙 Back", callback_data="("🔙 Back", callback_data="admin_back")
   admin_back")
    else:
        btn_quota = else:
        btn InlineKeyboardButton_quota = InlineKeyboardButton("📊 س("📊 سقف دانلود", callback_data="قف دانلودsetting_quota", callback_data="setting_quota")
        btn_size = InlineKeyboard")
        btn_sizeButton("📦 = InlineKeyboardButton("📦 حجم فایل", حجم فایل", callback_data="setting callback_data="setting_size")
        btn_size")
        btn_active = Inline_active = InlineKeyboardButton("🔄 وضعیت رKeyboardButton("بات", callback_data🔄 وضعیت ربات", callback_data="setting_active")
        btn_rate =="setting_active")
        btn_rate = InlineKeyboardButton InlineKeyboardButton("⏱("⏱️ محدودیت️ محدودیت زمانی", callback_data="setting_rate زمانی", callback_data="setting_rate_limit")
        btn_limit")
        btn_back = Inline_back = InlineKeyboardButton("KeyboardButton("🔙 بازگشت", callback_data="🔙 بازگشت", callback_data="admin_back")
    keyboard.add(btnadmin_back")
    keyboard.add(btn_quota, btn_size)
   _quota, keyboard.add(btn btn_size)
    keyboard.add(btn_active, btn_rate_active, btn_rate)
    keyboard.add(btn_back)
    keyboard.add(btn_back)
    return keyboard)
    return keyboard

def get_rate_limit_keyboard(lang: str =

def get_rate_limit_keyboard(lang: str = "fa"):
    keyboard = Inline "fa"):
    keyboard = InlineKeyboardMarkup(row_width=2)
    if lang ==KeyboardMarkup(row_width=2)
    if lang == "en":
        btn_enable = InlineKeyboardButton "en":
        btn_enable = InlineKeyboardButton("✅ Enable", callback_data="rate_limit_enable("✅ Enable", callback_data="rate_limit_enable")
        btn_d")
        btn_disable = Inlineisable = InlineKeyboardKeyboardButton("❌ Disable", callback_data="rateButton("❌ Disable", callback_data="rate_limit_disable")
        btn_10s = Inline_limit_disable")
        btn_10s = InlineKeyboardButton("⏱️ KeyboardButton("⏱️ 10s", callback10s", callback_data="rate_limit_10")
        btn_30s_data="rate_limit_10")
        btn_30s = InlineKeyboard = InlineKeyboardButton("⏱️ 30Button("⏱️ 30s", callback_datas", callback_data="rate_limit_30")
        btn_60s =="rate_limit_30")
        btn_60s = InlineKeyboardButton InlineKeyboardButton("⏱️ 60s("⏱️ 60s", callback_data="rate_limit_60")
        btn_", callback_data="rate_limit_60")
        btn_120s = In120s = InlineKeyboardButton("⏱️ 120s",lineKeyboardButton("⏱️ 120s", callback_data="rate callback_data="rate_limit_120")
        btn_back = InlineKeyboardButton("🔙 Back_limit_120")
        btn_back = InlineKeyboardButton("🔙 Back", callback_data="admin_back")
   ", callback_data="admin_back")
    else:
        btn_enable = In else:
        btn_enable = InlineKeyboardButton("lineKeyboardButton("✅ فعال", callback_data="rate_limit✅ فعال", callback_enable")
       _data="rate_limit_enable")
        btn_disable = btn_disable = InlineKeyboardButton InlineKeyboardButton("❌ غیرفعال", callback("❌ غیر_data="rate_limit_disable")
        btn_10sفعال", callback_data="rate_limit_disable")
        = InlineKeyboard btn_10s = InlineKeyboardButton("⏱️ ۱۰ ثانیه",Button("⏱️ ۱۰ callback_data="rate ثانیه", callback_data="rate_limit_10_limit_10")
        btn_30")
        btn_30s = InlineKeyboardButton("⏱️ s = InlineKeyboardButton("⏱۳۰ ثانیه", callback_data️ ۳۰ ثانیه", callback_data="rate_limit_="rate_limit_30")
        btn_60s = InlineKeyboardButton30")
        btn_60s = InlineKeyboardButton("⏱("⏱️ ۶۰️ ۶۰ ثانیه", ثانیه", callback_data="rate_limit_60")
        btn_120s = Inline callback_data="rate_limit_60")
        btn_120KeyboardButton("⏱️ ۱۲۰ ثانیs = InlineKeyboardButton("⏱️ ۱۲۰ ثانیه", callback_dataه", callback_data="rate_limit_120")
        btn="rate_limit_120")
        btn_back = Inline_back = InlineKeyboardButton("🔙 بازگشت", callback_data="KeyboardButton("🔙 بازگشت", callback_data="admin_back")
    keyboard.add(btn_enable, btnadmin_back")
    keyboard.add(btn_enable, btn_disable)
    keyboard.add(btn_disable)
    keyboard.add(btn_10s_10s, btn_30s, btn_30s, btn_60s, btn, btn_60s, btn_120s)
   _120s)
    keyboard.add(btn_back)
    return keyboard

def get keyboard.add(btn_back)
    return keyboard

def get_back_keyboard_back_keyboard(lang: str = "fa(lang: str = "fa"):
    keyboard = In"):
    keyboard = InlineKeyboardMarkuplineKeyboardMarkup()
    if lang()
    if lang == "en == "en":
        btn_back = InlineKeyboardButton":
        btn_back = InlineKeyboardButton("("🔙 Back🔙 Back", callback_data="", callback_data="admin_back")
    else:
        btnadmin_back")
    else:
        btn_back = Inline_back = InlineKeyboardButton("KeyboardButton("🔙 بازگشت", callback_data🔙 بازگشت="admin_back")
   ", callback_data="admin_back")
    keyboard.add(btn keyboard.add(btn_back)
    return keyboard

# =_back)
    return keyboard

# =====================================================================================================
# 📋 کامندها
# ===================================================
COMMANDS
# 📋 کامندها
# ===================================================
COMMANDS_FA =_FA = [
    BotCommand(" [
    BotCommand("start", "شروع و نمایش راهstart", "شروع و نمایش راهنما"),
   نما"),
    BotCommand("language", "تغ BotCommand("language", "تغییر زبان رباتییر زبان ربات"),
]

COMMANDS_EN = [
   "),
]

COMMANDS_EN = [
    BotCommand BotCommand("start", "Start and("start", "Start and show help"),
    show help"),
    BotCommand("language", "Change bot BotCommand("language", "Change bot language"),
]
