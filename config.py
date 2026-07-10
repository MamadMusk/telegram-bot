"""
config.py — تنظیمات اصلی ربات (بدون وابستگی به pydantic)
"""

import os
from typing import List, Optional

# ===== تنظیمات اصلی (از env) =====
TOKEN = os.getenv("BOT_TOKEN", "8837695158:AAETrphGJh6wS1bmCXHOFB7-r4YPx0n8KR8")

# ===== آیدی ادمین‌های اصلی (از env) =====
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "1085150385")
ADMIN_IDS: List[int] = [
    int(x.strip()) for x in ADMIN_IDS_STR.split(",")
    if x.strip().isdigit()
]

# ===== مسیر دیتابیس =====
DB_PATH = os.getenv("DB_PATH", "users.db")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")

# ===== تنظیمات پیش‌فرض =====
DEFAULT_SETTINGS = {
    "welcome_message": "👋 سلام! به ربات دانلود اینستاگرام خوش آمدید.\n\nلینک پست یا ریلز اینستاگرام را بفرستید تا آن را برایتان دانلود کنم.",
    "daily_quota": "10",
    "max_file_size": "50",
    "is_active": "True",
    "broadcast_in_progress": "False",
    "force_channels": "",
}

# ============================================================
#  🔍 توابع کمکی
# ============================================================

def get_db_setting(key: str, default: Optional[str] = None) -> str:
    try:
        from database import get_setting as db_get
        val = db_get(key)
        if val is not None:
            return val
    except Exception:
        pass
    return default or DEFAULT_SETTINGS.get(key, "")


def get_db_setting_int(key: str, default: int = 0) -> int:
    try:
        val = get_db_setting(key)
        return int(val) if val else default
    except (ValueError, TypeError):
        return default


def get_db_setting_bool(key: str, default: bool = False) -> bool:
    val = get_db_setting(key)
    if val is None:
        return default
    return val.lower() in ("true", "1", "yes", "on")


def is_admin(user_id: int) -> bool:
    if user_id in ADMIN_IDS:
        return True
    try:
        from database import is_admin as db_is_admin
        return db_is_admin(user_id)
    except Exception:
        return False


def is_super_admin(user_id: int) -> bool:
    if user_id in ADMIN_IDS:
        return True
    try:
        from database import is_super_admin as db_is_super
        return db_is_super(user_id)
    except Exception:
        return False


def get_force_channels() -> List[str]:
    try:
        from database import get_force_channels_list
        return get_force_channels_list()
    except Exception:
        return []


def set_force_channels(channels: List[str]) -> None:
    try:
        from database import set_force_channels_list
        set_force_channels_list(channels)
    except Exception:
        pass
