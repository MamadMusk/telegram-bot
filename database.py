"""
database.py — Unified SQLite database layer (sync).
"""

from __future__ import annotations

import os
import sqlite3
import threading
import json
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional, Tuple

from config import DB_PATH, ADMIN_IDS

_write_lock = threading.Lock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
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
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)

    with get_conn() as conn:
        c = conn.cursor()

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

        c.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS daily_quota (
                user_id      INTEGER NOT NULL,
                quota_date   TEXT NOT NULL,
                count        INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, quota_date),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id    INTEGER PRIMARY KEY,
                role       TEXT DEFAULT 'viewer',
                added_at   TEXT DEFAULT (datetime('now')),
                permissions TEXT DEFAULT '{}'
            )
        """)

        defaults = [
            ("welcome_message", "👋 سلام! به ربات دانلود اینستاگرام خوش آمدید."),
            ("is_active", "True"),
            ("max_file_size", "50"),
            ("daily_quota", "10"),
            ("broadcast_in_progress", "False"),
            ("force_channels", ""),
            ("rate_limit_enabled", "False"),
            ("rate_limit_seconds", "30"),
        ]
        c.executemany("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", defaults)

        for admin_id in ADMIN_IDS:
            c.execute(
                "INSERT OR IGNORE INTO admins (user_id, role, permissions) VALUES (?, 'owner', ?)",
                (admin_id, json.dumps({
                    "can_view_stats": True,
                    "can_send_broadcast": True,
                    "can_manage_force_sub": True,
                    "can_manage_settings": True,
                    "can_manage_admins": True,
                    "can_remove_owner": False
                }))
            )

        c.execute("CREATE INDEX IF NOT EXISTS idx_downloads_user ON downloads(user_id);")
        c.execute("CREATE INDEX IF NOT EXISTS idx_downloads_date ON downloads(download_date DESC);")
        c.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")

    print("✅ Database initialized at", DB_PATH)


# ============================================================
#  Users
# ============================================================
def add_user(user_id: int, username: Optional[str], first_name: Optional[str],
             last_name: Optional[str]) -> None:
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
        row = conn.execute("SELECT is_banned FROM users WHERE id = ?", (user_id,)).fetchone()
        return bool(row and row["is_banned"])


def ban_user(user_id: int) -> None:
    with _write_lock, get_conn() as conn:
        conn.execute("UPDATE users SET is_banned = 1 WHERE id = ?", (user_id,))


def unban_user(user_id: int) -> None:
    with _write_lock, get_conn() as conn:
        conn.execute("UPDATE users SET is_banned = 0 WHERE id = ?", (user_id,))


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def get_users_paginated(
    page: int = 1, size: int = 50, search: str = ""
) -> Tuple[List[Dict[str, Any]], int]:
    offset = max(0, (page - 1) * size)
    with get_conn() as conn:
        if search:
            like = f"%{search}%"
            total = conn.execute(
                "SELECT COUNT(*) FROM users WHERE username LIKE ? OR first_name LIKE ? OR last_name LIKE ? OR CAST(id AS TEXT) LIKE ?",
                (like, like, like, like),
            ).fetchone()[0]
            rows = conn.execute(
                "SELECT * FROM users WHERE username LIKE ? OR first_name LIKE ? OR last_name LIKE ? OR CAST(id AS TEXT) LIKE ? ORDER BY joined_date DESC LIMIT ? OFFSET ?",
                (like, like, like, like, size, offset),
            ).fetchall()
        else:
            total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            rows = conn.execute("SELECT * FROM users ORDER BY joined_date DESC LIMIT ? OFFSET ?", (size, offset)).fetchall()
        return [dict(r) for r in rows], total


# ============================================================
#  Downloads
# ============================================================
def add_download(user_id: int, post_url: str, platform: str = "instagram",
                 status: str = "success", file_size_kb: Optional[int] = None) -> None:
    with _write_lock, get_conn() as conn:
        conn.execute(
            "INSERT INTO downloads (user_id, post_url, platform, status, file_size_kb) VALUES (?, ?, ?, ?, ?)",
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


def increment_download(user_id: int) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _write_lock, get_conn() as conn:
        conn.execute(
            "INSERT INTO downloads (user_id, post_url, platform, status) VALUES (?, '', 'instagram', 'success')",
            (user_id,)
        )
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
#  Daily quota
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
    limit_str = get_setting("daily_quota", "10")
    limit = int(limit_str) if limit_str else 10
    used = get_quota(user_id)
    user = get_user(user_id)
    if user and user.get("is_premium"):
        return True, used, 0
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
        banned = conn.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1").fetchone()[0]
        today = _today_str()
        today_downloads = conn.execute(
            "SELECT COUNT(*) FROM downloads WHERE date(download_date) = ?",
            (today,),
        ).fetchone()[0]
        active_users_7d = conn.execute(
            "SELECT COUNT(DISTINCT user_id) FROM downloads WHERE download_date >= datetime('now', '-7 days')"
        ).fetchone()[0]
        return {
            "users": users,
            "downloads": downloads,
            "banned": banned,
            "today_downloads": today_downloads,
            "active_users_7d": active_users_7d,
        }


def get_daily_download_series(days: int = 30) -> List[Dict[str, Any]]:
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
            "can_remove_owner": False
        }
    with get_conn() as conn:
        row = conn.execute(
            "SELECT permissions FROM admins WHERE user_id = ?", (user_id,)
        ).fetchone()
        if row and row["permissions"]:
            try:
                perms = json.loads(row["permissions"])
                default_perms = {
                    "can_view_stats": True,
                    "can_send_broadcast": False,
                    "can_manage_force_sub": False,
                    "can_manage_settings": False,
                    "can_manage_admins": False,
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
        "can_remove_owner": False
    }


def update_admin_permissions(user_id: int, permissions: Dict[str, bool]) -> None:
    if user_id in ADMIN_IDS:
        return
    with _write_lock, get_conn() as conn:
        conn.execute(
            "UPDATE admins SET permissions = ? WHERE user_id = ?",
            (json.dumps(permissions), user_id)
        )


def add_admin(user_id: int, role: str = "viewer", permissions: Optional[Dict[str, bool]] = None) -> None:
    if permissions is None:
        permissions = {
            "can_view_stats": True,
            "can_send_broadcast": False,
            "can_manage_force_sub": False,
            "can_manage_settings": False,
            "can_manage_admins": False,
            "can_remove_owner": False
        }
    with _write_lock, get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO admins (user_id, role, permissions) VALUES (?, ?, ?)",
            (user_id, role, json.dumps(permissions))
        )


def remove_admin(user_id: int) -> None:
    if user_id in ADMIN_IDS:
        return
    with _write_lock, get_conn() as conn:
        conn.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))


def get_all_admins() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT a.user_id, a.role, a.added_at, a.permissions,
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
                    "can_remove_owner": False
                })
            result.append(d)
        return result


def is_super_admin(user_id: int) -> bool:
    if user_id in ADMIN_IDS:
        return True
    with get_conn() as conn:
        row = conn.execute("SELECT role FROM admins WHERE user_id = ?", (user_id,)).fetchone()
        return row and row["role"] in ["super", "owner"]


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
#  Broadcast
# ============================================================
def get_all_user_ids(include_banned: bool = False) -> List[int]:
    with get_conn() as conn:
        if include_banned:
            rows = conn.execute("SELECT id FROM users").fetchall()
        else:
            rows = conn.execute("SELECT id FROM users WHERE is_banned = 0").fetchall()
        return [r["id"] for r in rows]


def get_all_users() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY joined_date DESC").fetchall()
        return [dict(r) for r in rows]


def get_user_count() -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
        return row[0] if row else 0


def get_all_users_count() -> int:
    return get_user_count()
