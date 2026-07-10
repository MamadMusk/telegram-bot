"""
database.py — Unified SQLite database layer (sync).

Single source of truth for schema, migrations, and queries.
Includes: users, downloads, settings, daily_quota (rate limiting), admins.

All functions are SYNC (not async). They are designed to be called from:
  - bot.py (aiogram handlers can call sync functions in thread pool via asyncio.to_thread)
  - admin_panel.py (FastAPI sync def endpoints run in threadpool automatically)
"""
from __future__ import annotations

import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional, Tuple

from config import DB_PATH, ADMIN_IDS

# Module-level lock for write operations (SQLite doesn't handle concurrent
# writes well; we serialize them ourselves).
_write_lock = threading.Lock()


def _now_iso() -> str:
    """Current UTC timestamp as ISO string with timezone."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ============================================================
#  Connection helpers
# ============================================================

@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    """Yield a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA busy_timeout=30000;")
    try:
        yield conn
    finally:
        conn.close()


# ============================================================
#  Schema initialization & migrations
# ============================================================

def init_db() -> None:
    """Create all tables if not exists, run migrations."""
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)

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
                last_seen     TEXT
            )
        """)

        # ─── Downloads ───
        c.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL,
                post_url      TEXT NOT NULL,
                platform      TEXT DEFAULT 'instagram',
                status        TEXT DEFAULT 'success',
                file_size_kb  INTEGER,
                download_date TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        # ─── Settings (key-value) ───
        c.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # ─── Daily quota (rate limiting) ───
        c.execute("""
            CREATE TABLE IF NOT EXISTS daily_quota (
                user_id      INTEGER NOT NULL,
                quota_date   TEXT NOT NULL,
                count        INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, quota_date),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        # ─── Admins (RBAC) ───
        c.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id    INTEGER PRIMARY KEY,
                role       TEXT DEFAULT 'viewer',
                added_at   TEXT DEFAULT (datetime('now'))
            )
        """)

        # ─── Default settings ───
        defaults: List[Tuple[str, str]] = [
            ("welcome_message", "👋 سلام! به ربات دانلود اینستاگرام خوش آمدید.\n\nلینک پست یا ریلز اینستاگرام را بفرستید تا آن را برایتان دانلود کنم."),
            ("is_active", "True"),
            ("max_file_size", "50"),
            ("daily_quota", "10"),
            ("broadcast_in_progress", "False"),
            ("force_channels", ""),
        ]
        c.executemany(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            defaults,
        )

        # ─── Seed admins from ADMIN_IDS env ───
        for admin_id in ADMIN_IDS:
            c.execute(
                "INSERT OR IGNORE INTO admins (user_id, role) VALUES (?, 'super')",
                (admin_id,),
            )

        # ─── Indexes for performance ───
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_downloads_user "
            "ON downloads(user_id);"
        )
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_downloads_date "
            "ON downloads(download_date DESC);"
        )
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_username "
            "ON users(username);"
        )

    print("✅ Database initialized at", DB_PATH)


# ============================================================
#  Users
# ============================================================

def add_user(user_id: int, username: Optional[str], first_name: Optional[str],
             last_name: Optional[str]) -> None:
    """Insert a new user (idempotent). Updates last_seen if exists."""
    with _write_lock, get_conn() as conn:
        conn.execute(
            """
            INSERT INTO users (id, username, first_name, last_name, last_seen)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                username   = excluded.username,
                first_name = excluded.first_name,
                last_name  = excluded.last_name,
                last_seen  = excluded.last_seen
            """,
            (user_id, username, first_name, last_name, _now_iso()),
        )


def is_banned(user_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT is_banned FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return bool(row and row["is_banned"])


def ban_user(user_id: int) -> None:
    with _write_lock, get_conn() as conn:
        conn.execute(
            "UPDATE users SET is_banned = 1 WHERE id = ?", (user_id,)
        )


def unban_user(user_id: int) -> None:
    with _write_lock, get_conn() as conn:
        conn.execute(
            "UPDATE users SET is_banned = 0 WHERE id = ?", (user_id,)
        )


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None


def get_users_paginated(
    page: int = 1, size: int = 50, search: str = ""
) -> Tuple[List[Dict[str, Any]], int]:
    """Return (users, total_count) for given page."""
    offset = max(0, (page - 1) * size)
    with get_conn() as conn:
        if search:
            like = f"%{search}%"
            total = conn.execute(
                "SELECT COUNT(*) FROM users "
                "WHERE username LIKE ? OR first_name LIKE ? OR last_name LIKE ? "
                "OR CAST(id AS TEXT) LIKE ?",
                (like, like, like, like),
            ).fetchone()[0]
            rows = conn.execute(
                "SELECT * FROM users "
                "WHERE username LIKE ? OR first_name LIKE ? OR last_name LIKE ? "
                "OR CAST(id AS TEXT) LIKE ? "
                "ORDER BY joined_date DESC LIMIT ? OFFSET ?",
                (like, like, like, like, size, offset),
            ).fetchall()
        else:
            total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            rows = conn.execute(
                "SELECT * FROM users ORDER BY joined_date DESC LIMIT ? OFFSET ?",
                (size, offset),
            ).fetchall()
        return [dict(r) for r in rows], total


# ============================================================
#  Downloads
# ============================================================

def add_download(user_id: int, post_url: str, platform: str = "instagram",
                 status: str = "success", file_size_kb: Optional[int] = None) -> None:
    with _write_lock, get_conn() as conn:
        conn.execute(
            """
            INSERT INTO downloads (user_id, post_url, platform, status, file_size_kb)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, post_url, platform, status, file_size_kb),
        )


def get_recent_downloads(limit: int = 10) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT d.*, u.username, u.first_name
            FROM downloads d
            LEFT JOIN users u ON d.user_id = u.id
            ORDER BY d.download_date DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_downloads_paginated(
    page: int = 1, size: int = 50
) -> Tuple[List[Dict[str, Any]], int]:
    offset = max(0, (page - 1) * size)
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM downloads").fetchone()[0]
        rows = conn.execute(
            """
            SELECT d.*, u.username, u.first_name
            FROM downloads d
            LEFT JOIN users u ON d.user_id = u.id
            ORDER BY d.download_date DESC
            LIMIT ? OFFSET ?
            """,
            (size, offset),
        ).fetchall()
        return [dict(r) for r in rows], total


def increment_download() -> None:
    """افزایش تعداد دانلودهای امروز (برای آمار)"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _write_lock, get_conn() as conn:
        conn.execute(
            """
            INSERT INTO daily_quota (user_id, quota_date, count)
            VALUES (0, ?, 1)
            ON CONFLICT(user_id, quota_date) DO UPDATE SET count = count + 1
            """,
            (today,),
        )


def get_total_downloads() -> int:
    """تعداد کل دانلودهای انجام شده"""
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) FROM downloads").fetchone()
        return row[0] if row else 0


# ============================================================
#  Settings (key-value)
# ============================================================

def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    with _write_lock, get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )


def get_all_settings() -> Dict[str, str]:
    with get_conn() as conn:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
        return {r["key"]: r["value"] for r in rows}


# ============================================================
#  Daily quota (rate limiting)
# ============================================================

def _today_str() -> str:
    """Return today's date as YYYY-MM-DD in UTC."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def get_quota(user_id: int) -> int:
    """Return number of downloads user has made today."""
    today = _today_str()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT count FROM daily_quota WHERE user_id = ? AND quota_date = ?",
            (user_id, today),
        ).fetchone()
        return row["count"] if row else 0


def increment_quota(user_id: int) -> int:
    """Atomically increment the user's daily quota count, return new value."""
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
    """Returns (allowed, used_today, limit). Limit=0 means unlimited."""
    limit_str = get_setting("daily_quota", "10")
    limit = int(limit_str) if limit_str else 10
    used = get_quota(user_id)

    # Premium users bypass quota
    user = get_user(user_id)
    if user and user.get("is_premium"):
        return True, used, 0  # unlimited

    if limit <= 0:
        return True, used, 0
    return (used < limit), used, limit


# ============================================================
#  Stats
# ============================================================

def get_stats() -> Dict[str, int]:
    with get_conn() as conn:
        users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        downloads = conn.execute("SELECT COUNT(*) FROM downloads").fetchone()[0]
        banned = conn.execute(
            "SELECT COUNT(*) FROM users WHERE is_banned = 1"
        ).fetchone()[0]
        today = _today_str()
        today_downloads = conn.execute(
            "SELECT COUNT(*) FROM downloads WHERE date(download_date) = ?",
            (today,),
        ).fetchone()[0]
        active_users_7d = conn.execute(
            "SELECT COUNT(DISTINCT user_id) FROM downloads "
            "WHERE download_date >= datetime('now', '-7 days')"
        ).fetchone()[0]
        return {
            "users": users,
            "downloads": downloads,
            "banned": banned,
            "today_downloads": today_downloads,
            "active_users_7d": active_users_7d,
        }


def get_daily_download_series(days: int = 30) -> List[Dict[str, Any]]:
    """Return last N days of download counts for charting."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT date(download_date) as d, COUNT(*) as c
            FROM downloads
            WHERE download_date >= datetime('now', ?)
            GROUP BY date(download_date)
            ORDER BY d ASC
            """,
            (f"-{days} days",),
        ).fetchall()
        return [{"date": r["d"], "count": r["c"]} for r in rows]


# ============================================================
#  Admins (RBAC)
# ============================================================

def is_admin(user_id: int) -> bool:
    """True if user is in admins table OR in ADMIN_IDS env setting."""
    if user_id in ADMIN_IDS:
        return True
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM admins WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row is not None


def get_admin_role(user_id: int) -> Optional[str]:
    """Return role string ('super', 'moderator', 'viewer') or None."""
    if user_id in ADMIN_IDS:
        return "super"
    with get_conn() as conn:
        row = conn.execute(
            "SELECT role FROM admins WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row["role"] if row else None


def add_admin(user_id: int, role: str = "viewer") -> None:
    with _write_lock, get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO admins (user_id, role) VALUES (?, ?)",
            (user_id, role),
        )


def remove_admin(user_id: int) -> None:
    with _write_lock, get_conn() as conn:
        conn.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))


def get_all_admins() -> List[Dict[str, Any]]:
    """دریافت لیست کامل ادمین‌ها با جزئیات"""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT a.user_id, a.role, a.added_at, u.username, u.first_name, u.last_name
            FROM admins a
            LEFT JOIN users u ON a.user_id = u.id
            ORDER BY a.added_at ASC
        """).fetchall()
        return [dict(r) for r in rows]


def update_admin_role(user_id: int, new_role: str) -> None:
    """به‌روزرسانی نقش ادمین (super/moderator/viewer)"""
    with _write_lock, get_conn() as conn:
        conn.execute(
            "UPDATE admins SET role = ? WHERE user_id = ?",
            (new_role, user_id),
        )


def is_super_admin(user_id: int) -> bool:
    """بررسی ادمین اصلی بودن (از env یا role='super')"""
    if user_id in ADMIN_IDS:
        return True
    with get_conn() as conn:
        row = conn.execute(
            "SELECT role FROM admins WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row and row["role"] == "super"


# ============================================================
#  🔧 توابع جدید برای قفل اسپانسر (Force Subscribe)
# ============================================================

def get_force_channels_list() -> List[str]:
    """دریافت لیست کانال‌های اجباری از تنظیمات"""
    channels_str = get_setting("force_channels", "")
    if not channels_str:
        return []
    return [ch.strip() for ch in channels_str.split(",") if ch.strip()]


def set_force_channels_list(channels: List[str]) -> None:
    """ذخیره لیست کانال‌های اجباری"""
    set_setting("force_channels", ",".join(channels))


def add_force_channel(channel: str) -> None:
    """افزودن کانال به لیست اجباری"""
    channels = get_force_channels_list()
    if channel not in channels:
        channels.append(channel)
        set_force_channels_list(channels)


def remove_force_channel(channel: str) -> bool:
    """حذف کانال از لیست اجباری"""
    channels = get_force_channels_list()
    if channel in channels:
        channels.remove(channel)
        set_force_channels_list(channels)
        return True
    return False


# ============================================================
#  Broadcast
# ============================================================

def get_all_user_ids(include_banned: bool = False) -> List[int]:
    with get_conn() as conn:
        if include_banned:
            rows = conn.execute("SELECT id FROM users").fetchall()
        else:
            rows = conn.execute(
                "SELECT id FROM users WHERE is_banned = 0"
            ).fetchall()
        return [r["id"] for r in rows]


def get_all_users() -> List[Dict[str, Any]]:
    """دریافت لیست کامل کاربران"""
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY joined_date DESC").fetchall()
        return [dict(r) for r in rows]


def get_user_count() -> int:
    """تعداد کل کاربران"""
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
        return row[0] if row else 0


def get_all_users_count() -> int:
    """تعداد کل کاربران (alias برای get_user_count)"""
    return get_user_count()


# ============================================================
#  Module-level init
# ============================================================

# Do NOT auto-init at import time. Caller (bot.py, admin_panel.py) must call
# init_db() explicitly. This avoids surprises in tests and during migrations.
