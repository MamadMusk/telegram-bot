# TelegramBot v2.0

ربات تلگرام فارسی برای دانلود از اینستاگرام، تیک‌تاک، یوتیوب شورتز و توییتر، با پنل ادمین FastAPI و دیتابیس SQLite.

## ✨ امکانات

- 📥 پشتیبانی از ۴ پلتفرم: Instagram، TikTok، YouTube Shorts، Twitter/X
- 🔄 استراتژی دانلود دوگانه: اول instaloader، در صورت شکست yt-dlp با کوکی
- ⚡ Inline mode (`@bot <url>`) — دانلود بدون خروج از چت
- 🚦 سیستم سهمیه روزانه برای هر کاربر (با پشتیبانی از Premium)
- 🔐 پنل ادمین با HTTP Basic Auth + CSRF protection
- 📊 داشبورد با نمودار ۳۰ روز اخیر (Chart.js)
- 🔍 جستجو و صفحه‌بندی در لیست کاربران و دانلودها
- 📢 ارسال همگانی واقعی (با rate limit ایمن)
- 🚫 سیستم ban/unban کاربران
- 📝 تنظیمات runtime (پیام خوش‌آمد، وضعیت ربات، سهمیه، حجم فایل)
- 🐳 Docker پشتیبانی می‌شود
- 📝 logging ساختارافزوده با rotation

## 📋 پیش‌نیازها

- Python 3.12+
- Telegram Bot Token (از [@BotFather](https://t.me/BotFather))
- ffmpeg (برای merge ویدیو/صدا در yt-dlp)

## 🚀 نصب و راه‌اندازی

### روش ۱: Docker (توصیه‌شده)

```bash
# ۱. کلون کنید
git clone <your-repo-url>
cd TelegramBot

# ۲. فایل .env بسازید
cp .env.example .env
# حالا فایل .env را ویرایش کنید و مقادیر را پر کنید

# ۳. اجرا
docker compose up -d

# مشاهده لاگ‌ها
docker compose logs -f
```

### روش ۲: نصب دستی

```bash
# ۱. کلون و وارد پوشه شوید
git clone <your-repo-url>
cd TelegramBot

# ۲. محیط مجازی بسازید
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# ۳. وابستگی‌ها را نصب کنید
pip install -r requirements.txt

# ۴. ffmpeg نصب کنید (در اوبونتو)
sudo apt install ffmpeg

# ۵. فایل .env بسازید
cp .env.example .env
# فایل .env را ویرایش کنید

# ۶. اجرای ربات
python bot.py

# ۷. در ترمینال جداگانه، اجرای پنل ادمین
uvicorn admin_panel:app --host 0.0.0.0 --port 8000
```

## ⚙️ تنظیمات

فایل `.env` را با مقادیر واقعی پر کنید:

| متغیر | توضیح | پیش‌فرض |
|------|------|---------|
| `BOT_TOKEN` | توکن ربات از BotFather | (الزامی) |
| `ADMIN_IDS` | شناسه عددی ادمین‌ها (با کاما جدا کنید) | (الزامی) |
| `ADMIN_USER` | نام کاربری پنل ادمین | `admin` |
| `ADMIN_PASS` | رمز عبور پنل ادمین | (تغییر دهید!) |
| `SECRET_KEY` | کلید امضای session (۶۴ کاراکتر تصادفی) | (تغییر دهید!) |
| `DAILY_QUOTA` | سهمیه روزانه هر کاربر | `20` |
| `MAX_FILE_SIZE_MB` | حداکثر حجم فایل (MB) | `50` |
| `INSTAGRAM_USERNAME` | (اختیاری) برای پست‌های private | خالی |
| `INSTAGRAM_PASSWORD` | (اختیاری) | خالی |

برای پیدا کردن شناسه عددی خود، به [@userinfobot](https://t.me/userinfobot) پیام بدهید.

## 📖 راهنمای استفاده

### برای کاربران

1. ربات را در تلگرام `/start` کنید
2. لینک پست یا ریلز اینستاگرام (یا تیک‌تاک/یوتیوب شورتز/توییتر) را بفرستید
3. ربات فایل را دانلود و ارسال می‌کند

**دستورات:**
- `/start` — پیام خوش‌آمدگویی
- `/help` — راهنما
- `/quota` — سهمیه باقی‌مانده
- `/stats` — آمار ربات
- `/id` — شناسه عددی شما

**Inline mode:** در هر چتی بنویسید `@your_bot <url>` و روی دکمه کلیک کنید.

### برای ادمین‌ها

۱. پنل ادمین در آدرس `http://your-server:8000` در دسترس است.
۲. با `ADMIN_USER` و `ADMIN_PASS` وارد شوید.
۳. می‌توانید:
   - 📊 داشبورد آمار را ببینید
   - 👥 کاربران را مدیریت (ban/unban، جستجو، صفحه‌بندی)
   - 📥 تاریخچه دانلودها را ببینید
   - 📢 پیام همگانی بفرستید
   - ⚙️ تنظیمات ربات را تغییر دهید

## 🔒 امنیت

- ✅ تمام secretها در `.env` قرار دارند (هرگز در repo commit نشود)
- ✅ پنل ادمین با HTTP Basic Auth محافظت می‌شود
- ✅ CSRF protection روی تمام POST endpoints
- ✅ Jinja2 autoescape برای جلوگیری از XSS
- ✅ SQLite با WAL mode برای عملکرد بهتر
- ✅ Throttling در broadcast (۲۰ پیام/ثانیه)

**نکته مهم:** اگر فایل `cookies.txt` برای دسترسی به پست‌های private اینستاگرام استفاده می‌کنید، آن را هرگز در repo قرار ندهید.

## 🛠️ توسعه

### ساختار پروژه

```
TelegramBot/
├── bot.py              # ربات (aiogram 3.x, async)
├── admin_panel.py      # پنل ادمین (FastAPI, sync)
├── config.py           # تنظیمات (pydantic-settings)
├── database.py         # لایه دیتابیس (SQLite, sync)
├── downloader.py       # دانلودر (instaloader + yt-dlp)
├── templates/          # قالب‌های Jinja2
│   ├── _base.html
│   ├── dashboard.html
│   ├── users.html
│   ├── downloads.html
│   ├── broadcast.html
│   └── settings.html
├── static/             # فایل‌های استاتیک (اختیاری)
├── .env.example        # الگوی تنظیمات
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### اضافه‌کردن پلتفرم جدید

در `downloader.py`، الگو را به `URL_PATTERNS` اضافه کنید:

```python
"facebook": re.compile(
    r"(?:https?://)?(?:www\.)?facebook\.com/.*?/videos/(\d+)",
    re.IGNORECASE,
),
```

yt-dlp به‌طور خودکار آن را دانلود می‌کند.

### اجرای تست‌ها

```bash
pytest
```

## 📝 لایسنس

MIT

## 🤝 مشارکت

Pull request ها welcome هستند! لطفاً قبل از submit:
۱. کد را با `black` فرمت کنید
۲. type hintها را نگه دارید
۳. تست اضافه کنید (در صورت امکان)
