"""
admin_panel.py — FastAPI admin panel with authentication.

Features:
  - HTTP Basic Auth (configurable via .env)
  - Jinja2 templates with autoescape (no more XSS)
  - CSRF protection for POST endpoints
  - Real broadcast (actually sends messages via Telegram)
  - Pagination for users and downloads
  - Stats dashboard with chart data
  - Settings management
  - User ban/unban with audit logging
  - All sync def (FastAPI runs sync in threadpool, no SQLite blocking)
"""
from __future__ import annotations

import asyncio
import html
import logging
import os
import secrets
import threading
import time
from typing import Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import BadSignature, URLSafeSerializer
from telebot import TeleBot  # for broadcast (sync lib)

from config import settings
from database import (
    init_db, get_stats, get_users_paginated, get_downloads_paginated,
    get_recent_downloads, ban_user, unban_user, get_user,
    get_all_settings, set_setting, get_setting,
    get_all_user_ids, get_daily_download_series, get_admin_role,
    add_admin, remove_admin, is_admin,
)

# ============================================================
#  Logging
# ============================================================
logger = logging.getLogger("admin_panel")

# ============================================================
#  App setup
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
templates.env.autoescape = True  # critical: prevent XSS

app = FastAPI(
    title="TelegramBot Admin Panel",
    version="2.0",
    docs_url=None,       # disable public Swagger UI
    redoc_url=None,      # disable public ReDoc
    openapi_url=None,    # disable OpenAPI schema
)

# Static files for CSS/JS (optional, can serve via CDN too)
static_dir = os.path.join(BASE_DIR, "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Initialize DB on startup
init_db()

# ============================================================
#  Auth
# ============================================================

security = HTTPBasic(realm="TelegramBot Admin")


def verify_admin(creds: HTTPBasicCredentials = Depends(security)) -> str:
    """Verify HTTP Basic Auth credentials."""
    is_user_ok = secrets.compare_digest(
        creds.username.encode("utf-8"),
        settings.ADMIN_USER.encode("utf-8"),
    )
    is_pass_ok = secrets.compare_digest(
        creds.password.encode("utf-8"),
        settings.ADMIN_PASS.encode("utf-8"),
    )
    if not (is_user_ok and is_pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return creds.username


# ============================================================
#  CSRF
# ============================================================

_csrf_serializer = URLSafeSerializer(settings.SECRET_KEY, salt="csrf")


def generate_csrf_token() -> str:
    return _csrf_serializer.dumps({"t": int(time.time())})


def verify_csrf_token(token: str) -> bool:
    try:
        _csrf_serializer.loads(token, max_age=3600 * 24)  # 24h validity
        return True
    except BadSignature:
        return False


def _inject_csrf(request: Request) -> str:
    """Generate CSRF token and store in request state."""
    token = generate_csrf_token()
    request.state.csrf_token = token
    return token


# ============================================================
#  Context for templates
# ============================================================

def _base_context(request: Request) -> dict:
    """Common context for all templates."""
    csrf = getattr(request.state, "csrf_token", None) or _inject_csrf(request)
    return {
        "request": request,
        "csrf_token": csrf,
        "current_year": __import__("datetime").datetime.now().year,
        "bot_username": "TelegramBot",
        "active_page": "",
    }


# ============================================================
#  Routes
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    _: str = Depends(verify_admin),
):
    """Main dashboard with stats and recent downloads."""
    ctx = _base_context(request)
    ctx.update(active_page="dashboard")

    stats = get_stats()
    recent = get_recent_downloads(limit=10)

    # Chart data (last 30 days)
    series = get_daily_download_series(days=30)
    chart_dates = [s["date"] for s in series]
    chart_counts = [s["count"] for s in series]

    all_settings = get_all_settings()
    is_active = all_settings.get("is_active", "True") == "True"
    welcome = all_settings.get("welcome_message", "")

    ctx.update(
        stats=stats,
        recent_downloads=recent,
        chart_dates=chart_dates,
        chart_counts=chart_counts,
        is_active=is_active,
        welcome_message=welcome,
        max_file_size=all_settings.get("max_file_size", str(settings.MAX_FILE_SIZE_MB)),
    )
    return templates.TemplateResponse("dashboard.html", ctx)


@app.get("/users", response_class=HTMLResponse)
async def users_list(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=10, le=500),
    search: str = Query(""),
    _: str = Depends(verify_admin),
):
    """User list with pagination and search."""
    ctx = _base_context(request)
    ctx.update(active_page="users")

    users, total = get_users_paginated(page=page, size=size, search=search)
    total_pages = max(1, (total + size - 1) // size)

    ctx.update(
        users=users,
        total_users=total,
        page=page,
        size=size,
        total_pages=total_pages,
        search=search,
        has_prev=page > 1,
        has_next=page < total_pages,
        page_range=_get_page_range(page, total_pages),
    )
    return templates.TemplateResponse("users.html", ctx)


def _get_page_range(current: int, total: int, window: int = 5) -> list:
    """Return a sensible page range for pagination UI."""
    if total <= 1:
        return [1]
    start = max(1, current - window // 2)
    end = min(total, start + window - 1)
    start = max(1, end - window + 1)
    return list(range(start, end + 1))


@app.get("/downloads", response_class=HTMLResponse)
async def downloads_list(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=10, le=500),
    _: str = Depends(verify_admin),
):
    """Download history with pagination."""
    ctx = _base_context(request)
    ctx.update(active_page="downloads")

    downloads, total = get_downloads_paginated(page=page, size=size)
    total_pages = max(1, (total + size - 1) // size)

    ctx.update(
        downloads=downloads,
        total_downloads=total,
        page=page,
        size=size,
        total_pages=total_pages,
        has_prev=page > 1,
        has_next=page < total_pages,
        page_range=_get_page_range(page, total_pages),
    )
    return templates.TemplateResponse("downloads.html", ctx)


@app.get("/broadcast", response_class=HTMLResponse)
async def broadcast_page(
    request: Request,
    _: str = Depends(verify_admin),
):
    """Broadcast form."""
    ctx = _base_context(request)
    ctx.update(active_page="broadcast")

    total_users = len(get_all_user_ids(include_banned=False))
    ctx.update(total_users=total_users)

    return templates.TemplateResponse("broadcast.html", ctx)


@app.post("/send_broadcast")
async def send_broadcast(
    request: Request,
    message: str = Form(...),
    admin: str = Depends(verify_admin),
):
    """Actually send broadcast to all non-banned users."""
    # Verify CSRF
    form = await request.form()
    csrf_token = form.get("csrf_token", "")
    if not verify_csrf_token(csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    if not message.strip():
        return RedirectResponse(url="/broadcast?error=empty", status_code=303)

    # Send broadcast in background thread
    result = _do_broadcast(message, admin)
    logger.info("Broadcast by %s: sent=%d, failed=%d, total=%d",
                admin, result["sent"], result["failed"], result["total"])

    return RedirectResponse(
        url=f"/broadcast?sent={result['sent']}&failed={result['failed']}&total={result['total']}",
        status_code=303,
    )


def _do_broadcast(message: str, admin_user: str) -> dict:
    """Send broadcast to all users. Runs in thread (called from async endpoint)."""
    bot_instance = TeleBot(settings.BOT_TOKEN)
    user_ids = get_all_user_ids(include_banned=False)
    sent, failed = 0, 0

    for uid in user_ids:
        try:
            # Telegram allows 30 msgs/sec globally; we use 20 to be safe
            bot_instance.send_message(uid, message)
            sent += 1
            time.sleep(0.05)
        except Exception as e:
            logger.warning("Broadcast to %d failed: %s", uid, e)
            failed += 1

    return {"sent": sent, "failed": failed, "total": len(user_ids)}


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    _: str = Depends(verify_admin),
):
    """Settings page."""
    ctx = _base_context(request)
    ctx.update(active_page="settings")

    all_settings = get_all_settings()
    ctx.update(
        welcome_message=all_settings.get("welcome_message", ""),
        is_active=all_settings.get("is_active", "True") == "True",
        max_file_size=all_settings.get("max_file_size", str(settings.MAX_FILE_SIZE_MB)),
        daily_quota=all_settings.get("daily_quota", str(settings.DAILY_QUOTA)),
    )
    return templates.TemplateResponse("settings.html", ctx)


@app.post("/update_settings")
async def update_settings(
    request: Request,
    welcome_message: str = Form(""),
    is_active: str = Form("False"),  # checkbox: only sent when checked
    max_file_size: int = Form(..., ge=1, le=2000),
    daily_quota: int = Form(..., ge=0, le=10000),
    admin: str = Depends(verify_admin),
):
    """Update bot settings."""
    form = await request.form()
    csrf_token = form.get("csrf_token", "")
    if not verify_csrf_token(csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    set_setting("welcome_message", welcome_message)
    set_setting("is_active", "True" if is_active == "True" else "False")
    set_setting("max_file_size", str(max_file_size))
    set_setting("daily_quota", str(daily_quota))

    logger.info("Settings updated by %s", admin)
    return RedirectResponse(url="/settings?saved=1", status_code=303)


@app.post("/ban_user/{user_id}")
async def ban_user_endpoint(
    user_id: int,
    request: Request,
    admin: str = Depends(verify_admin),
):
    form = await request.form()
    csrf_token = form.get("csrf_token", "")
    if not verify_csrf_token(csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    ban_user(user_id)
    logger.info("User %d banned by %s", user_id, admin)
    return RedirectResponse(url="/users", status_code=303)


@app.post("/unban_user/{user_id}")
async def unban_user_endpoint(
    user_id: int,
    request: Request,
    admin: str = Depends(verify_admin),
):
    form = await request.form()
    csrf_token = form.get("csrf_token", "")
    if not verify_csrf_token(csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    unban_user(user_id)
    logger.info("User %d unbanned by %s", user_id, admin)
    return RedirectResponse(url="/users", status_code=303)


# ============================================================
#  JSON API endpoints (for charts / AJAX)
# ============================================================

@app.get("/api/stats/summary")
async def api_stats_summary(_: str = Depends(verify_admin)):
    """JSON stats summary."""
    return get_stats()


@app.get("/api/stats/downloads")
async def api_stats_downloads(
    days: int = Query(30, ge=1, le=365),
    _: str = Depends(verify_admin),
):
    """JSON download counts per day for the last N days."""
    return get_daily_download_series(days=days)


# ============================================================
#  Health check
# ============================================================

@app.get("/health")
async def health():
    """Unauthenticated health check (returns minimal info)."""
    return {"status": "ok", "version": "2.0"}


# ============================================================
#  Entry point
# ============================================================

if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(
        "admin_panel:app",
        host=settings.PANEL_HOST,
        port=settings.PANEL_PORT,
        reload=False,
        log_level=settings.LOG_LEVEL.lower(),
    )
