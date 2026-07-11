"""
database.py — Unified database layer with PostgreSQL and SQLite support.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone

from config import ADMIN_IDS

logger = logging.getLogger(__name__)

# ===== انتخاب نوع دیتابیس =====
DATABASE_URL = os.getenv("DATABASE_URL", "")

if DATABASE_URL:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    def get_conn():
        return psycopg2.connect(DATABASE_URL)
    
    def dict_factory(cursor, row):
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
    
    DB_TYPE = "postgres"
else:
    import sqlite3
    import threading
    _write_lock = threading.Lock()
    DB_PATH = os.getenv("DB_PATH", "users.db")
    
    def get_conn():
        os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
        conn = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA busy_timeout=30000;")
        return conn
    
    DB_TYPE = "sqlite"

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def init_db():
    """ایجاد جداول"""
    with get_conn() as conn:
        c = conn.cursor()
        
        if DB_TYPE == "postgres":
            c.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id            BIGINT PRIMARY KEY,
                    username      TEXT,
                    first_name    TEXT,
                    last_name     TEXT,
                    joined_date   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_banned     INTEGER DEFAULT 0,
                    is_premium    INTEGER DEFAULT 0,
                    last_seen     TIMESTAMP,
                    language      TEXT DEFAULT 'fa'
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    id            SERIAL PRIMARY KEY,
                    user_id       BIGINT NOT NULL,
                    post_url      TEXT NOT NULL,
                    platform      TEXT DEFAULT 'instagram',
                    status        TEXT DEFAULT 'success',
                    file_size_kb  INTEGER,
                    download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                    user_id      BIGINT NOT NULL,
                    quota_date   DATE NOT NULL,
                    count        INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, quota_date)
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    user_id      BIGINT PRIMARY KEY,
                    role         TEXT DEFAULT 'viewer',
                    added_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    permissions  TEXT DEFAULT '{}',
                    expire_date  TIMESTAMP
                )
            """)
        else:
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
                    language      TEXT DEFAULT 'fa'
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
                    download_date TEXT DEFAULT (datetime('now'))
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
                    PRIMARY KEY (user_id, quota_date)
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    user_id      INTEGER PRIMARY KEY,
                    role         TEXT DEFAULT 'viewer',
                    added_at     TEXT DEFAULT (datetime('now')),
                    permissions  TEXT DEFAULT '{}',
                    expire_date  TEXT
                )
            """)
        
        # ===== Default settings =====
        defaults = [
            ("is_active", "True"),
            ("max_file_size", "50"),
            ("daily_quota", "10"),
            ("broadcast_in_progress", "False"),
            ("force_channels", ""),
            ("rate_limit_enabled", "False"),
            ("rate_limit_seconds", "30"),
        ]
        for key, value in defaults:
            try:
                if DB_TYPE == "postgres":
                    c.execute("INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO NOTHING", (key, value))
                else:
                    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))
            except:
                pass
        
        # ===== Seed admins =====
        for admin_id in ADMIN_IDS:
            try:
                if DB_TYPE == "postgres":
                    c.execute("""
                        INSERT INTO admins (user_id, role, permissions, expire_date) 
                        VALUES (%s, 'owner', %s, NULL) 
                        ON CONFLICT (user_id) DO NOTHING
                    """, (admin_id, json.dumps({
                        "can_view_stats": True,
                        "can_send_broadcast": True,
                        "can_manage_force_sub": True,
                        "can_manage_settings": True,
                        "can_manage_admins": True,
                        "can_remove_owner": False
                    })))
                else:
                    c.execute("""
                        INSERT OR IGNORE INTO admins (user_id, role, permissions, expire_date) 
                        VALUES (?, 'owner', ?, NULL)
                    """, (admin_id, json.dumps({
                        "can_view_stats": True,
                        "can_send_broadcast": True,
                        "can_manage_force_sub": True,
                        "can_manage_settings": True,
                        "can_manage_admins": True,
                        "can_remove_owner": False
                    })))
            except:
                pass
        
        if DB_TYPE == "postgres":
            c.execute("CREATE INDEX IF NOT EXISTS idx_downloads_user ON downloads(user_id);")
            c.execute("CREATE INDEX IF NOT EXISTS idx_downloads_date ON downloads(download_date DESC);")
            c.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
        else:
            c.execute("CREATE INDEX IF NOT EXISTS idx_downloads_user ON downloads(user_id);")
            c.execute("CREATE INDEX IF NOT EXISTS idx_downloads_date ON downloads(download_date DESC);")
            c.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
        
        conn.commit()
    
    print(f"✅ Database initialized ({DB_TYPE})")

# ============================================================
#  توابع اصلی (مشترک بین SQLite و PostgreSQL)
# ============================================================

def add_user(user_id: int, username: Optional[str], first_name: Optional[str],
             last_name: Optional[str], language: str = "fa") -> None:
    with get_conn() as conn:
        c = conn.cursor()
        if DB_TYPE == "postgres":
            c.execute("""
                INSERT INTO users (id, username, first_name, last_name, last_seen, language)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    last_seen = EXCLUDED.last_seen
            """, (user_id, username, first_name, last_name, _now_iso(), language))
        else:
            c.execute("""
                INSERT INTO users (id, username, first_name, last_name, last_seen, language)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    last_seen = excluded.last_seen
            """, (user_id, username, first_name, last_name, _now_iso(), language))
        conn.commit()

def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        c = conn.cursor()
        if DB_TYPE == "postgres":
            c.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = c.fetchone()
            if row:
                return dict_factory(c, row)
        else:
            c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = c.fetchone()
            if row:
                return dict(row)
        return None

def get_user_language(user_id: int) -> str:
    with get_conn() as conn:
        c = conn.cursor()
        if DB_TYPE == "postgres":
            c.execute("SELECT language FROM users WHERE id = %s", (user_id,))
            row = c.fetchone()
            return row[0] if row else "fa"
        else:
            c.execute("SELECT language FROM users WHERE id = ?", (user_id,))
            row = c.fetchone()
            return row["language"] if row else "fa"

def set_user_language(user_id: int, language: str) -> None:
    with get_conn() as conn:
        c = conn.cursor()
        if DB_TYPE == "postgres":
            c.execute("UPDATE users SET language = %s WHERE id = %s", (language, user_id))
        else:
            c.execute("UPDATE users SET language = ? WHERE id = ?", (language, user_id))
        conn.commit()

def get_all_users() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        c = conn.cursor()
        if DB_TYPE == "postgres":
            c.execute("SELECT * FROM users ORDER BY joined_date DESC")
            rows = c.fetchall()
            return [dict_factory(c, row) for row in rows]
        else:
            c.execute("SELECT * FROM users ORDER BY joined_date DESC")
            rows = c.fetchall()
            return [dict(row) for row in rows]

def get_user_count() -> int:
    with get_conn() as conn:
        c = conn.cursor()
        if DB_TYPE == "postgres":
            c.execute("SELECT COUNT(*) FROM users")
            return c.fetchone()[0]
        else:
            c.execute("SELECT COUNT(*) FROM users")
            return c.fetchone()[0]

def get_all_admins() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        c = conn.cursor()
        if DB_TYPE == "postgres":
            c.execute("""
                SELECT a.user_id, a.role, a.added_at, a.permissions, a.expire_date,
                       u.username, u.first_name, u.last_name
                FROM admins a
                LEFT JOIN users u ON a.user_id = u.id
                ORDER BY a.added_at ASC
            """)
            rows = c.fetchall()
            result = []
            for row in rows:
                d = dict_factory(c, row)
                if d['user_id'] in ADMIN_IDS:
                    d['role'] = 'owner'
                result.append(d)
            return result
        else:
            c.execute("""
                SELECT a.user_id, a.role, a.added_at, a.permissions, a.expire_date,
                       u.username, u.first_name, u.last_name
                FROM admins a
                LEFT JOIN users u ON a.user_id = u.id
                ORDER BY a.added_at ASC
            """)
            rows = c.fetchall()
            result = []
            for row in rows:
                d = dict(row)
                if d['user_id'] in ADMIN_IDS:
                    d['role'] = 'owner'
                result.append(d)
            return result

def get_stats() -> Dict[str, int]:
    with get_conn() as conn:
        c = conn.cursor()
        if DB_TYPE == "postgres":
            c.execute("SELECT COUNT(*) FROM users")
            users = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM downloads")
            downloads = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
            banned = c.fetchone()[0]
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            c.execute("SELECT COUNT(*) FROM downloads WHERE DATE(download_date) = %s", (today,))
            today_downloads = c.fetchone()[0]
            c.execute("SELECT COUNT(DISTINCT user_id) FROM downloads WHERE download_date >= NOW() - INTERVAL '7 days'")
            active_users_7d = c.fetchone()[0]
        else:
            c.execute("SELECT COUNT(*) FROM users")
            users = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM downloads")
            downloads = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
            banned = c.fetchone()[0]
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            c.execute("SELECT COUNT(*) FROM downloads WHERE date(download_date) = ?", (today,))
            today_downloads = c.fetchone()[0]
            c.execute("SELECT COUNT(DISTINCT user_id) FROM downloads WHERE download_date >= datetime('now', '-7 days')")
            active_users_7d = c.fetchone()[0]
        return {
            "users": users,
            "downloads": downloads,
            "banned": banned,
            "today_downloads": today_downloads,
            "active_users_7d": active_users_7d,
        }

def get_total_downloads() -> int:
    with get_conn() as conn:
        c = conn.cursor()
        if DB_TYPE == "postgres":
            c.execute("SELECT COUNT(*) FROM downloads")
            return c.fetchone()[0]
        else:
            c.execute("SELECT COUNT(*) FROM downloads")
            return c.fetchone()[0]

def increment_download(user_id: int) -> None:
    with get_conn() as conn:
        c = conn.cursor()
        if DB_TYPE == "postgres":
            c.execute("INSERT INTO downloads (user_id, post_url, platform, status) VALUES (%s, '', 'instagram', 'success')", (user_id,))
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            c.execute("""
                INSERT INTO daily_quota (user_id, quota_date, count) 
                VALUES (%s, %s, 1) 
                ON CONFLICT (user_id, quota_date) DO UPDATE SET count = count + 1
            """, (user_id, today))
        else:
            c.execute("INSERT INTO downloads (user_id, post_url, platform, status) VALUES (?, '', 'instagram', 'success')", (user_id,))
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            c.execute("""
                INSERT INTO daily_quota (user_id, quota_date, count) 
                VALUES (?, ?, 1) 
                ON CONFLICT(user_id, quota_date) DO UPDATE SET count = count + 1
            """, (user_id, today))
        conn.commit()

def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    with get_conn() as conn:
        c = conn.cursor()
        if DB_TYPE == "postgres":
            c.execute("SELECT value FROM settings WHERE key = %s", (key,))
            row = c.fetchone()
            return row[0] if row else default
        else:
            c.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = c.fetchone()
            return row["value"] if row else default

def set_setting(key: str, value: str) -> None:
    with get_conn() as conn:
        c = conn.cursor()
        if DB_TYPE == "postgres":
            c.execute("INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = %s", (key, value, value))
        else:
            c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()

def get_force_channels_list() -> List[str]:
    channels_str = get_setting("force_channels", "")
    if not channels_str:
        return []
    return [ch.strip() for ch in channels_str.split(",") if ch.strip()]

def add_force_channel(channel: str) -> None:
    channels = get_force_channels_list()
    if channel not in channels:
        channels.append(channel)
        set_setting("force_channels", ",".join(channels))

def remove_force_channel(channel: str) -> bool:
    channels = get_force_channels_list()
    if channel in channels:
        channels.remove(channel)
        set_setting("force_channels", ",".join(channels))
        return True
    return False

def is_admin(user_id: int) -> bool:
    if user_id in ADMIN_IDS:
        return True
    with get_conn() as conn:
        c = conn.cursor()
        if DB_TYPE == "postgres":
            c.execute("SELECT 1 FROM admins WHERE user_id = %s", (user_id,))
            return c.fetchone() is not None
        else:
            c.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
            return c.fetchone() is not None

def add_admin(user_id: int, role: str = "viewer") -> None:
    perms = {
        "can_view_stats": True,
        "can_send_broadcast": False,
        "can_manage_force_sub": False,
        "can_manage_settings": False,
        "can_manage_admins": False,
        "can_remove_owner": False
    }
    with get_conn() as conn:
        c = conn.cursor()
        if DB_TYPE == "postgres":
            c.execute("""
                INSERT INTO admins (user_id, role, permissions) 
                VALUES (%s, %s, %s) 
                ON CONFLICT (user_id) DO UPDATE SET role = %s, permissions = %s
            """, (user_id, role, json.dumps(perms), role, json.dumps(perms)))
        else:
            c.execute("""
                INSERT OR REPLACE INTO admins (user_id, role, permissions) 
                VALUES (?, ?, ?)
            """, (user_id, role, json.dumps(perms)))
        conn.commit()

def remove_admin(user_id: int) -> None:
    if user_id in ADMIN_IDS:
        return
    with get_conn() as conn:
        c = conn.cursor()
        if DB_TYPE == "postgres":
            c.execute("DELETE FROM admins WHERE user_id = %s", (user_id,))
        else:
            c.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
        conn.commit()

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
    default = {
        "can_view_stats": True,
        "can_send_broadcast": False,
        "can_manage_force_sub": False,
        "can_manage_settings": False,
        "can_manage_admins": False,
        "can_remove_owner": False
    }
    with get_conn() as conn:
        c = conn.cursor()
        if DB_TYPE == "postgres":
            c.execute("SELECT permissions FROM admins WHERE user_id = %s", (user_id,))
            row = c.fetchone()
            if row and row[0]:
                try:
                    perms = json.loads(row[0])
                    default.update(perms)
                except:
                    pass
        else:
            c.execute("SELECT permissions FROM admins WHERE user_id = ?", (user_id,))
            row = c.fetchone()
            if row and row["permissions"]:
                try:
                    perms = json.loads(row["permissions"])
                    default.update(perms)
                except:
                    pass
    return default

def update_admin_permissions(user_id: int, permissions: Dict[str, bool]) -> bool:
    if user_id in ADMIN_IDS:
        return False
    with get_conn() as conn:
        c = conn.cursor()
        if DB_TYPE == "postgres":
            c.execute("UPDATE admins SET permissions = %s WHERE user_id = %s", (json.dumps(permissions), user_id))
        else:
            c.execute("UPDATE admins SET permissions = ? WHERE user_id = ?", (json.dumps(permissions), user_id))
        conn.commit()
        return True

def get_admin_role(user_id: int) -> Optional[str]:
    if user_id in ADMIN_IDS:
        return "owner"
    with get_conn() as conn:
        c = conn.cursor()
        if DB_TYPE == "postgres":
            c.execute("SELECT role FROM admins WHERE user_id = %s", (user_id,))
            row = c.fetchone()
            return row[0] if row else None
        else:
            c.execute("SELECT role FROM admins WHERE user_id = ?", (user_id,))
            row = c.fetchone()
            return row["role"] if row else None

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
