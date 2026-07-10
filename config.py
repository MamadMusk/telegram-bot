"""
config.py — تنظیمات اصلی ربات با pydantic
"""

import os
from typing import List, Optional
from pydantic import BaseModel, field_validator


class Settings(BaseModel):
    """مدل تنظیمات با اعتبارسنجی خودکار"""
    
    TOKEN: str = "8837695158:AAETrphGJh6wS1bmCXHOFB7-r4YPx0n8KR8"
    ADMIN_IDS: List[int] = []
    DB_PATH: str = "users.db"
    DOWNLOAD_DIR: str = "downloads"

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        """تبدیل رشته‌ی ADMIN_IDS به لیست اعداد"""
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip().isdigit()]
        return v


# ===== خواندن از محیط (Environment Variables) =====
_settings = Settings(
    TOKEN=os.getenv("BOT_TOKEN", "8837695158:AAETrphGJh6wS1bmCXHOFB7-r4YPx0n8KR8"),
    ADMIN_IDS=os.getenv("ADMIN_IDS", "1085150385"),
    DB_PATH=os.getenv("DB_PATH", "users.db"),
    DOWNLOAD_DIR=os.getenv("DOWNLOAD_DIR", "downloads"),
)

# ===== صادر کردن متغیرها =====
TOKEN = _settings.TOKEN
ADMIN_IDS = _settings.ADMIN_IDS
DB_PATH = _settings.DB_PATH
DOWNLOAD_DIR = _settings.DOWNLOAD_DIR

# ============================================================
#  🔍 توابع کمکی (مشابه قبل)
# ============================================================

def is_admin(user_id: int) -> bool:
    """بررسی ادمین بودن کاربر (از env یا دیتابیس)"""
    if user_id in ADMIN_IDS:
        return True
    try:
        from database import is_admin as db_is_admin
        return db_is_admin(user_id)
    except Exception:
        return False


def is_super_admin(user_id: int) -> bool:
    """بررسی ادمین اصلی بودن"""
    if user_id in ADMIN_IDS:
        return True
    try:
        from database import is_super_admin as db_is_super
        return db_is_super(user_id)
    except Exception:
        return False


# ============================================================
#  📦 تنظیمات پیش‌فرض برای fallback
# ============================================================

DEFAULT_SETTINGS = {
    "welcome_message": "👋 سلام! به ربات دانلود اینستاگرام خوش آمدید.\n\nلینک پست یا ریلز اینستاگرام را بفرستید تا آن را برایتان دانلود کنم.",
    "daily_quota": "10",
    "max_file_size": "50",
    "is_active": "True",
    "broadcast_in_progress": "False",
    "force_channels": "",
}


def get_db_setting(key: str, default: Optional[str] = None) -> str:
    """خواندن یک تنظیم از دیتابیس"""
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


def get_force_channels() -> List[str]:
    """دریافت لیست کانال‌های اجباری"""
    try:
        from database import get_force_channels_list
        return get_force_channels_list()
    except Exception:
        return []


def set_force_channels(channels: List[str]) -> None:
    """ذخیره لیست کانال‌های اجباری"""
    try:
        from database import set_force_channels_list
        set_force_channels_list(channels)
    except Exception:
        pass
