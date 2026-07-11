"""
database.py — Unified SQLite database layer (sync).

این فایل شامل تمام توابع ارتباط با دیتابیس است.
"""

import os
import sqlite3
import threading
import json
import logging
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Iterator, List, Optional, Tuple

from config import DB_PATH, ADMIN_IDS

_write_lock = threading.Lock()
logger = logging.getLogger(__name__)


def _now_iso() -> str:
    """Return current UTC timestamp as ISO string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    """Yield a SQLite connection with row factory enabled."""
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA busy_timeout=30000;")
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """ایجاد جداول و مقداردهی اولیه دیتابیس."""
    with get_conn() as conn:
        c = conn.cursor()

        # ─── Users ───
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY,
                username      TEXT,
                first_name    TEXT,
                last_name     TEXT,
                joined_date   TEXT DEFAULT (datetime('now')),
                is_banned     INTEGER DEFAULT 0,
                is_premium    INTEGER DEFAULT 0,
                last_seen     TEXT,
                language      TEXT DEFAULT 'fa',
                premium_expire TEXT DEFAULT NULL,
                admin_expire   TEXT DEFAULT NULL,
                premium_daily_quota INTEGER DEFAULT NULL,
                premium_max_file_size INTEGER DEFAULT NULL,
                premium_rate_limit INTEGER DEFAULT NULL
            )
        """)

        # ─── Downloads (با پشتیبانی از خطا) ───
        c.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL,
                post_url      TEXT NOT NULL,
                platform      TEXT DEFAULT 'unknown',
                status        TEXT DEFAULT 'success',
                file_size_kb  INTEGER,
                error_message TEXT,
                download_date TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        # ─── Settings ───
        c.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # ─── Daily quota ───
        c.execute("""
            CREATE TABLE IF NOT EXISTS daily_quota (
                user_id      INTEGER NOT NULL,
                quota_date   TEXT NOT NULL,
                count        INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, quota_date),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        # ─── Admins ───
        c.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id      INTEGER PRIMARY KEY,
                role         TEXT DEFAULT 'viewer',
                added_at     TEXT DEFAULT (datetime('now')),
                permissions  TEXT DEFAULT '{}',
                expire_date  TEXT
            )
        """)

        # ─── Default settings ───
        defaults = [
            ("is_active", "True"),
            ("max_file_size", "50"),
            ("daily_quota", "10"),
            ("broadcast_in_progress", "False"),
            ("force_channels", ""),
            ("rate_limit_enabled", "False"),
            ("rate_limit_seconds", "30"),
            ("premium_default_daily_quota", "20"),
            ("premium_default_max_file_size", "100"),
            ("premium_default_rate_limit", "10"),
        ]
        for key, value in defaults:
            c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))

        # ─── Seed admins from ADMIN_IDS ───
        for admin_id in ADMIN_IDS:
            c.execute(
                "INSERT OR IGNORE INTO admins (user_id, role, permissions, expire_date) VALUES (?, 'owner', ?, NULL)",
                (admin_id, json.dumps({
                    "can_view_stats": True,
                    "can_send_broadcast": True,
                    "can_manage_force_sub": True,
                    "can_manage_settings": True,
                    "can_manage_admins": True,
                    "can_manage_premium": True,
                    "can_remove_owner": False
                }))
            )

        # ─── Indexes ───
        c.execute("CREATE INDEX IF NOT EXISTS idx_downloads_user ON downloads(user_id);")
        c.execute("CREATE INDEX IF NOT EXISTS idx_downloads_date ON downloads(download_date DESC);")
        c.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")

        conn.commit()

    print(f"✅ Database initialized at {DB_PATH}")


# ============================================================
#  Users (با پشتیبانی از Premium و تاریخ انقضا)
# ============================================================

def add_user(user_id: int, username: Optional[str], first_name: Optional[str],
             last_name: Optional[str], language: str = "fa") -> None:
    """ثبت کاربر جدید یا به‌روزرسانی اطلاعات."""
    with _write_lock, get_conn() as conn:
        conn.execute(
            """
            INSERT INTO users (id, username, first_name, last_name, last_seen, language)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                username   = excluded.username,
                first_name = excluded.first_name,
                last_name  = excluded.last_name,
                last_seen  = excluded.last_seen
            """,
            (user_id, username, first_name, last_name, _now_iso(), language),
        )


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """دریافت اطلاعات کامل یک کاربر."""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def get_user_language(user_id: int) -> str:
    """دریافت زبان کاربر."""
    with get_conn() as conn:
        row = conn.execute("SELECT language FROM users WHERE id = ?", (user_id,)).fetchone()
        return row["language"] if row else "fa"


def set_user_language(user_id: int, language: str) -> None:
    """تنظیم زبان کاربر."""
    with _write_lock, get_conn() as conn:
        conn.execute("UPDATE users SET language = ? WHERE id = ?", (language, user_id))


def get_all_users() -> List[Dict[str, Any]]:
    """دریافت لیست همه کاربران."""
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY joined_date DESC").fetchall()
        return [dict(row) for row in rows]


def get_user_count() -> int:
    """تعداد کل کاربران."""
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
        return row[0] if row else 0


def is_banned(user_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT is_banned FROM users WHERE id = ?", (user_id,)).fetchone()
        return bool(row and row["is_banned"])


def ban_user(user_id: int) -> None:
    with _write_lock, get_conn() as conn:
        conn.execute("UPDATE users SET is_banned = 1 WHERE id = ?", (user_id,))


def unban_user(user_id: int) -> None:
    with _write_lock, get_conn() as conn:
        conn.execute("UPDATE users SET is_banned = 0 WHERE id = ?", (user_id,))


# ============================================================
#  Premium Users (کاربران ویژه)
# ============================================================

def is_premium_user(user_id: int) -> bool:
    """بررسی کاربر ویژه بودن (با در نظر گرفتن تاریخ انقضا)."""
    with get_conn() as conn:
        row = conn.execute("SELECT is_premium, premium_expire FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return False
        if row["is_premium"] == 0:
            return False
        expire = row["premium_expire"]
        if expire:
            try:
                expire_date = datetime.fromisoformat(expire)
                if datetime.now(timezone.utc) > expire_date:
                    return False  # منقضی شده
            except:
                pass
        return True


def set_premium_status(user_id: int, enabled: bool, expire_days: Optional[int] = None,
                       daily_quota: Optional[int] = None, max_file_size: Optional[int] = None,
                       rate_limit: Optional[int] = None) -> None:
    """تنظیم وضعیت کاربر ویژه با تنظیمات دلخواه."""
    with _write_lock, get_conn() as conn:
        expire_str = None
        if enabled and expire_days is not None and expire_days > 0:
            expire_date = datetime.now(timezone.utc) + timedelta(days=expire_days)
            expire_str = expire_date.isoformat(timespec="seconds")
        conn.execute(
            """
            UPDATE users SET
                is_premium = ?,
                premium_expire = ?,
                premium_daily_quota = ?,
                premium_max_file_size = ?,
                premium_rate_limit = ?
            WHERE id = ?
            """,
            (1 if enabled else 0, expire_str, daily_quota, max_file_size, rate_limit, user_id)
        )


def get_premium_settings(user_id: int) -> Dict[str, Any]:
    """دریافت تنظیمات ویژه کاربر."""
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT is_premium, premium_expire, premium_daily_quota,
                   premium_max_file_size, premium_rate_limit
            FROM users WHERE id = ?
            """,
            (user_id,)
        ).fetchone()
        if not row:
            return {"is_premium": False}
        result = dict(row)
        if result.get("premium_expire"):
            try:
                expire = datetime.fromisoformat(result["premium_expire"])
                now = datetime.now(timezone.utc)
                if expire > now:
                    result["days_left"] = (expire - now).days
                else:
                    result["days_left"] = 0
            except:
                result["days_left"] = 0
        else:
            result["days_left"] = None
        return result


def get_all_premium_users() -> List[Dict[str, Any]]:
    """دریافت لیست همه کاربران ویژه فعال."""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT * FROM users WHERE is_premium = 1
            ORDER BY joined_date DESC
        """).fetchall()
        result = []
        for row in rows:
            user = dict(row)
            if user.get("premium_expire"):
                try:
                    expire = datetime.fromisoformat(user["premium_expire"])
                    now = datetime.now(timezone.utc)
                    if expire > now:
                        user["days_left"] = (expire - now).days
                    else:
                        user["days_left"] = 0
                except:
                    user["days_left"] = 0
            else:
                user["days_left"] = None
            result.append(user)
        return result


def get_premium_user_count() -> int:
    """تعداد کاربران ویژه فعال."""
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1").fetchone()
        return row[0] if row else 0


def set_admin_expire(user_id: int, expire_days: Optional[int] = None) -> None:
    """تنظیم تاریخ انقضای ادمین."""
    if user_id in ADMIN_IDS:
        return
    with _write_lock, get_conn() as conn:
        expire_str = None
        if expire_days is not None and expire_days > 0:
            expire_date = datetime.now(timezone.utc) + timedelta(days=expire_days)
            expire_str = expire_date.isoformat(timespec="seconds")
        conn.execute("UPDATE admins SET expire_date = ? WHERE user_id = ?", (expire_str, user_id))
        conn.execute("UPDATE users SET admin_expire = ? WHERE id = ?", (expire_str, user_id))


def is_admin_expired(user_id: int) -> bool:
    """بررسی منقضی شدن ادمین."""
    if user_id in ADMIN_IDS:
        return False
    with get_conn() as conn:
        row = conn.execute("SELECT expire_date FROM admins WHERE user_id = ?", (user_id,)).fetchone()
        if not row or not row["expire_date"]:
            return False
        try:
            expire = datetime.fromisoformat(row["expire_date"])
            return datetime.now(timezone.utc) > expire
        except:
            return False


# ============================================================
#  Daily Quota
# ============================================================

def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def get_quota(user_id: int) -> int:
    today = _today_str()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT count FROM daily_quota WHERE user_id = ? AND quota_date = ?",
            (user_id, today),
        ).fetchone()
        return row["count"] if row else 0


def increment_quota(user_id: int) -> int:
    today = _today_str()
    with _write_lock, get_conn() as conn:
        conn.execute(
            """
            INSERT INTO daily_quota (user_id, quota_date, count)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id, quota_date) DO UPDATE SET count = count + 1
            """,
            (user_id, today),
        )
        row = conn.execute(
            "SELECT count FROM daily_quota WHERE user_id = ? AND quota_date = ?",
            (user_id, today),
        ).fetchone()
        return row["count"] if row else 1


def check_quota(user_id: int) -> Tuple[bool, int, int]:
    """بررسی سقف دانلود روزانه (با در نظر گرفتن وضعیت Premium)."""
    premium_settings = get_premium_settings(user_id)
    if premium_settings.get("is_premium") and premium_settings.get("premium_daily_quota") is not None:
        limit = premium_settings["premium_daily_quota"]
    else:
        limit_str = get_setting("daily_quota", "10")
        limit = int(limit_str) if limit_str else 10
    used = get_quota(user_id)
    if limit <= 0:
        return True, used, 0
    return (used < limit), used, limit


# ============================================================
#  Download Functions
# ============================================================

def increment_download(user_id: int) -> None:
    """ثبت یک دانلود جدید و افزایش سقف روزانه."""
    with _write_lock, get_conn() as conn:
        conn.execute(
            "INSERT INTO downloads (user_id, post_url, platform, status) VALUES (?, '', 'instagram', 'success')",
            (user_id,)
        )
        today = _today_str()
        conn.execute(
            """
            INSERT INTO daily_quota (user_id, quota_date, count)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id, quota_date) DO UPDATE SET count = count + 1
            """,
            (user_id, today),
        )


def add_download(user_id: int, post_url: str, platform: str = "unknown",
                 status: str = "success", file_size_kb: Optional[int] = None,
                 error_message: Optional[str] = None) -> None:
    """ثبت دانلود با اطلاعات کامل (برای گزارش‌ها)."""
    with _write_lock, get_conn() as conn:
        conn.execute(
            """
            INSERT INTO downloads (user_id, post_url, platform, status, file_size_kb, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, post_url, platform, status, file_size_kb, error_message)
        )
        if status == "success":
            today = _today_str()
            conn.execute(
                """
                INSERT INTO daily_quota (user_id, quota_date, count)
                VALUES (?, ?, 1)
                ON CONFLICT(user_id, quota_date) DO UPDATE SET count = count + 1
                """,
                (user_id, today),
            )


def get_total_downloads() -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) FROM downloads").fetchone()
        return row[0] if row else 0


def get_failed_downloads_today() -> int:
    """دریافت تعداد دانلودهای ناموفق امروز."""
    today = _today_str()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM downloads WHERE status = 'failed' AND date(download_date) = ?",
            (today,)
        ).fetchone()
        return row[0] if row else 0


def get_new_users_today() -> int:
    """دریافت تعداد کاربران جدید امروز."""
    today = _today_str()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM users WHERE date(joined_date) = ?",
            (today,)
        ).fetchone()
        return row[0] if row else 0


# ============================================================
#  Settings
# ============================================================

def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    with _write_lock, get_conn() as conn:
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))


def get_all_settings() -> Dict[str, str]:
    with get_conn() as conn:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
        return {r["key"]: r["value"] for r in rows}


# ============================================================
#  Force Subscribe
# ============================================================

def get_force_channels_list() -> List[str]:
    channels_str = get_setting("force_channels", "")
    if not channels_str:
        return []
    return [ch.strip() for ch in channels_str.split(",") if ch.strip()]


def set_force_channels_list(channels: List[str]) -> None:
    set_setting("force_channels", ",".join(channels))


def add_force_channel(channel: str) -> None:
    channels = get_force_channels_list()
    if channel not in channels:
        channels.append(channel)
        set_force_channels_list(channels)


def remove_force_channel(channel: str) -> bool:
    channels = get_force_channels_list()
    if channel in channels:
        channels.remove(channel)
        set_force_channels_list(channels)
        return True
    return False


# ============================================================
#  Rate Limit
# ============================================================

def get_rate_limit_enabled() -> bool:
    val = get_setting("rate_limit_enabled", "False")
    return val.lower() == "true"


def set_rate_limit_enabled(enabled: bool) -> None:
    set_setting("rate_limit_enabled", "True" if enabled else "False")


def get_rate_limit_seconds() -> int:
    val = get_setting("rate_limit_seconds", "30")
    try:
        return int(val)
    except ValueError:
        return 30


def set_rate_limit_seconds(seconds: int) -> None:
    set_setting("rate_limit_seconds", str(seconds))


# ============================================================
#  Stats
# ============================================================

def get_stats() -> Dict[str, int]:
    with get_conn() as conn:
        users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        downloads = conn.execute("SELECT COUNT(*) FROM downloads").fetchone()[0]
        banned = conn.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1").fetchone()[0]
        today = _today_str()
        today_downloads = conn.execute(
            "SELECT COUNT(*) FROM downloads WHERE date(download_date) = ?",
            (today,),
        ).fetchone()[0]
        active_users_7d = conn.execute(
            "SELECT COUNT(DISTINCT user_id) FROM downloads WHERE download_date >= datetime('now', '-7 days')"
        ).fetchone()[0]
        premium_users = get_premium_user_count()
        return {
            "users": users,
            "downloads": downloads,
            "banned": banned,
            "today_downloads": today_downloads,
            "active_users_7d": active_users_7d,
            "premium_users": premium_users,
        }


# ============================================================
#  Admins (RBAC)
# ============================================================

def is_admin(user_id: int) -> bool:
    if user_id in ADMIN_IDS:
        return True
    with get_conn() as conn:
        row = conn.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,)).fetchone()
        return row is not None


def get_admin_role(user_id: int) -> Optional[str]:
    if user_id in ADMIN_IDS:
        return "owner"
    with get_conn() as conn:
        row = conn.execute("SELECT role FROM admins WHERE user_id = ?", (user_id,)).fetchone()
        return row["role"] if row else None


def get_admin_permissions(user_id: int) -> Dict[str, bool]:
    if user_id in ADMIN_IDS:
        return {
            "can_view_stats": True,
            "can_send_broadcast": True,
            "can_manage_force_sub": True,
            "can_manage_settings": True,
            "can_manage_admins": True,
            "can_manage_premium": True,
            "can_remove_owner": False
        }
    if is_admin_expired(user_id):
        return {
            "can_view_stats": False,
            "can_send_broadcast": False,
            "can_manage_force_sub": False,
            "can_manage_settings": False,
            "can_manage_admins": False,
            "can_manage_premium": False,
            "can_remove_owner": False
        }
    with get_conn() as conn:
        row = conn.execute("SELECT permissions FROM admins WHERE user_id = ?", (user_id,)).fetchone()
        if row and row["permissions"]:
            try:
                perms = json.loads(row["permissions"])
                default_perms = {
                    "can_view_stats": True,
                    "can_send_broadcast": False,
                    "can_manage_force_sub": False,
                    "can_manage_settings": False,
                    "can_manage_admins": False,
                    "can_manage_premium": False,
                    "can_remove_owner": False
                }
                default_perms.update(perms)
                return default_perms
            except json.JSONDecodeError:
                pass
    return {
        "can_view_stats": True,
        "can_send_broadcast": False,
        "can_manage_force_sub": False,
        "can_manage_settings": False,
        "can_manage_admins": False,
        "can_manage_premium": False,
        "can_remove_owner": False
    }


def update_admin_permissions(user_id: int, permissions: Dict[str, bool]) -> bool:
    if user_id in ADMIN_IDS:
        return False
    with _write_lock, get_conn() as conn:
        conn.execute(
            "UPDATE admins SET permissions = ? WHERE user_id = ?",
            (json.dumps(permissions), user_id)
        )
        return True


def add_admin(user_id: int, role: str = "viewer", permissions: Optional[Dict[str, bool]] = None,
              expire_days: Optional[int] = None) -> None:
    if permissions is None:
        permissions = {
            "can_view_stats": True,
            "can_send_broadcast": False,
            "can_manage_force_sub": False,
            "can_manage_settings": False,
            "can_manage_admins": False,
            "can_manage_premium": False,
            "can_remove_owner": False
        }
    expire_str = None
    if expire_days is not None and expire_days > 0:
        expire_date = datetime.now(timezone.utc) + timedelta(days=expire_days)
        expire_str = expire_date.isoformat(timespec="seconds")
    with _write_lock, get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO admins (user_id, role, permissions, expire_date) VALUES (?, ?, ?, ?)",
            (user_id, role, json.dumps(permissions), expire_str)
        )
        conn.execute("UPDATE users SET admin_expire = ? WHERE id = ?", (expire_str, user_id))


def remove_admin(user_id: int) -> None:
    if user_id in ADMIN_IDS:
        return
    with _write_lock, get_conn() as conn:
        conn.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
        conn.execute("UPDATE users SET admin_expire = NULL WHERE id = ?", (user_id,))


def get_all_admins() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT a.user_id, a.role, a.added_at, a.permissions, a.expire_date,
                   u.username, u.first_name, u.last_name
            FROM admins a
            LEFT JOIN users u ON a.user_id = u.id
            ORDER BY a.added_at ASC
        """).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d['user_id'] in ADMIN_IDS:
                d['role'] = 'owner'
                d['permissions'] = json.dumps({
                    "can_view_stats": True,
                    "can_send_broadcast": True,
                    "can_manage_force_sub": True,
                    "can_manage_settings": True,
                    "can_manage_admins": True,
                    "can_manage_premium": True,
                    "can_remove_owner": False
                })
                d['expire_date'] = None
            result.append(d)
        return result


def get_admin_role(user_id: int) -> Optional[str]:
    if user_id in ADMIN_IDS:
        return "owner"
    with get_conn() as conn:
        row = conn.execute("SELECT role FROM admins WHERE user_id = ?", (user_id,)).fetchone()
        return row["role"] if row else None


# ============================================================
#  Broadcast
# ============================================================

def get_all_user_ids(include_banned: bool = False) -> List[int]:
    with get_conn() as conn:
        if include_banned:
            rows = conn.execute("SELECT id FROM users").fetchall()
        else:
            rows = conn.execute("SELECT id FROM users WHERE is_banned = 0").fetchall()
        return [r["id"] for r in rows]


# ============================================================
#  Premium User Management Functions
# ============================================================

def toggle_premium_user(user_id: int, enabled: bool, expire_days: Optional[int] = None,
                        daily_quota: Optional[int] = None, max_file_size: Optional[int] = None,
                        rate_limit: Optional[int] = None) -> None:
    set_premium_status(user_id, enabled, expire_days, daily_quota, max_file_size, rate_limit)


def remove_premium_user(user_id: int) -> None:
    with _write_lock, get_conn() as conn:
        conn.execute("""
            UPDATE users SET
                is_premium = 0,
                premium_expire = NULL,
                premium_daily_quota = NULL,
                premium_max_file_size = NULL,
                premium_rate_limit = NULL
            WHERE id = ?
        """, (user_id,))


def get_premium_user_details(user_id: int) -> Optional[Dict[str, Any]]:
    user = get_user(user_id)
    if not user or user.get("is_premium") != 1:
        return None
    settings = get_premium_settings(user_id)
    user.update(settings)
    return user


# ============================================================
#  Rate Limit with Premium Override
# ============================================================

def get_user_rate_limit(user_id: int) -> int:
    premium_settings = get_premium_settings(user_id)
    if premium_settings.get("is_premium") and premium_settings.get("premium_rate_limit") is not None:
        return premium_settings["premium_rate_limit"]
    return get_rate_limit_seconds()


def get_user_max_file_size(user_id: int) -> int:
    premium_settings = get_premium_settings(user_id)
    if premium_settings.get("is_premium") and premium_settings.get("premium_max_file_size") is not None:
        return premium_settings["premium_max_file_size"]
    val = get_setting("max_file_size", "50")
    try:
        return int(val)
    except:
        return 50


def get_user_daily_quota(user_id: int) -> int:
    premium_settings = get_premium_settings(user_id)
    if premium_settings.get("is_premium") and premium_settings.get("premium_daily_quota") is not None:
        return premium_settings["premium_daily_quota"]
    val = get_setting("daily_quota", "10")
    try:
        return int(val)
    except:
        return 10


def is_user_exempt_from_force_subscribe(user_id: int) -> bool:
    if is_admin(user_id):
        return True
    return is_premium_user(user_id)
