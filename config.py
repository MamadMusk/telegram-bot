"""
config.py — تنظیمات اصلی ربات و توابع کمکی.

همه تنظیمات از متغیرهای محیطی (Environment Variables) خوانده می‌شوند.
برای شخصی‌سازی، فایل .env را ویرایش کنید.
"""

import os
from typing import List, Optional

# ============================================================
#  🔐 متغیرهای اصلی (از .env یا Render)
# ============================================================

# توکن ربات تلگرام
TOKEN = os.getenv("BOT_TOKEN", "8837695158:AAETrphGJh6wS1bmCXHOFB7-r4YPx0n8KR8")

# آیدی عددی ادمین‌های اصلی (با کاما جدا شده)
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "1085150385")
ADMIN_IDS: List[int] = [
    int(x.strip()) for x in ADMIN_IDS_STR.split(",")
    if x.strip().isdigit()
]

# مسیر دیتابیس
DB_PATH = os.getenv("DB_PATH", "users.db")

# مسیر ذخیره فایل‌های دانلود
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")

# ============================================================
#  📦 تنظیمات پیش‌فرض (برای fallback)
# ============================================================

DEFAULT_SETTINGS: dict = {
    "welcome_message": "👋 سلام! به ربات دانلود اینستاگرام خوش آمدید.\n\nلینک پست یا ریلز اینستاگرام را بفرستید تا آن را برایتان دانلود کنم.",
    "daily_quota": "10",
    "max_file_size": "50",
    "is_active": "True",
    "broadcast_in_progress": "False",
    "force_channels": "",
}

# ============================================================
#  🔍 توابع کمکی برای خواندن تنظیمات از دیتابیس
# ============================================================

def get_db_setting(key: str, default: Optional[str] = None) -> str:
    """
    خواندن یک تنظیم از دیتابیس.
    اگر در دیتابیس نبود، از DEFAULT_SETTINGS یا default استفاده می‌کند.
    """
    try:
        from database import get_setting as db_get
        val = db_get(key)
        if val is not None:
            return val
    except Exception:
        pass
    return default or DEFAULT_SETTINGS.get(key, "")


def get_db_setting_int(key: str, default: int = 0) -> int:
    """خواندن تنظیم به صورت عدد صحیح"""
    try:
        val = get_db_setting(key)
        return int(val) if val else default
    except (ValueError, TypeError):
        return default


def get_db_setting_bool(key: str, default: bool = False) -> bool:
    """خواندن تنظیم به صورت بولین"""
    val = get_db_setting(key)
    if val is None:
        return default
    return val.lower() in ("true", "1", "yes", "on")


def is_admin(user_id: int) -> bool:
    """
    بررسی ادمین بودن کاربر.
    ابتدا از ADMIN_IDS (env) چک می‌کند، سپس از دیتابیس.
    """
    if user_id in ADMIN_IDS:
        return True
    try:
        from database import is_admin as db_is_admin
        return db_is_admin(user_id)
    except Exception:
        return False


def is_super_admin(user_id: int) -> bool:
    """
    بررسی ادمین اصلی بودن (دسترسی کامل).
    ابتدا از ADMIN_IDS (env) چک می‌کند، سپس role='super' از دیتابیس.
    """
    if user_id in ADMIN_IDS:
        return True
    try:
        from database import is_super_admin as db_is_super
        return db_is_super(user_id)
    except Exception:
        return False


def get_force_channels() -> List[str]:
    """دریافت لیست کانال‌های اجباری از دیتابیس"""
    try:
        from database import get_force_channels_list
        return get_force_channels_list()
    except Exception:
        return []


def set_force_channels(channels: List[str]) -> None:
    """ذخیره لیست کانال‌های اجباری در دیتابیس"""
    try:
        from database import set_force_channels_list
        set_force_channels_list(channels)
    except Exception:
        pass

# ============================================================
#  ✅ تابع یکپارچه برای دریافت تنظیمات (با کش ساده)
# ============================================================

# کش ساده برای کاهش ترافیک دیتابیس (اختیاری)
_SETTINGS_CACHE: dict = {}
_SETTINGS_CACHE_TIME: dict = {}
_CACHE_TTL = 60  # 60 ثانیه


def get_setting_cached(key: str, default: Optional[str] = None, ttl: int = _CACHE_TTL) -> str:
    """
    خواندن تنظیم با کش ساده.
    بعد از ttl ثانیه، دوباره از دیتابیس می‌خواند.
    """
    import time
    now = time.time()
    if key in _SETTINGS_CACHE and (now - _SETTINGS_CACHE_TIME.get(key, 0)) < ttl:
        return _SETTINGS_CACHE[key]
    
    value = get_db_setting(key, default)
    _SETTINGS_CACHE[key] = value
    _SETTINGS_CACHE_TIME[key] = now
    return value


def invalidate_cache() -> None:
    """پاک کردن کش تنظیمات (بعد از به‌روزرسانی)"""
    _SETTINGS_CACHE.clear()
    _SETTINGS_CACHE_TIME.clear()
