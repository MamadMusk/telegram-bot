"""
bot.py — Telegram bot (aiogram 3.x, async).

Features:
  - /start, /help, /stats, /quota commands
  - Instagram / TikTok / YouTube / Twitter URL detection
  - Inline mode (@bot <url>) for use in any chat
  - Rate limiting (daily quota per user)
  - Ban check
  - is_active check (master switch from admin panel)
  - max_file_size check (Telegram 50MB limit)
  - Graceful shutdown on SIGINT/SIGTERM
  - Structured logging
  - Auto-cleanup of downloaded files (tempdir per request)
"""
from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from contextlib import suppress
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    FSInputFile, InlineQueryResultPhoto, InlineQueryResultVideo,
    InlineQueryResultsButton, Message, User, InlineQuery,
)
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from config import settings
from database import (
    init_db, add_user, add_download, is_banned, check_quota,
    increment_quota, get_stats, is_admin, get_setting,
)
from downloader import download, detect_platform, is_file_too_large, DownloadResult

# ============================================================
#  Logging
# ============================================================

def setup_logging() -> None:
    """Configure rotating file + console logging."""
    os.makedirs(os.path.dirname(settings.LOG_FILE) or ".", exist_ok=True)

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # File handler (rotating)
    from logging.handlers import RotatingFileHandler
    file_h = RotatingFileHandler(
        settings.LOG_FILE, maxBytes=5_000_000, backupCount=5, encoding="utf-8"
    )
    file_h.setFormatter(logging.Formatter(fmt, datefmt))
    root.addHandler(file_h)

    # Console handler
    console_h = logging.StreamHandler(sys.stdout)
    console_h.setFormatter(logging.Formatter(fmt, datefmt))
    root.addHandler(console_h)


logger = logging.getLogger("bot")


# ============================================================
#  Bot & Dispatcher
# ============================================================

bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()


# ============================================================
#  Helpers
# ============================================================

def _user_display_name(user: User) -> str:
    parts = [user.first_name or "", user.last_name or ""]
    name = " ".join(p for p in parts if p).strip()
    if not name:
        name = f"@{user.username}" if user.username else f"User #{user.id}"
    return name


async def _register_user(user: User) -> None:
    """Insert/update user in DB. Runs in thread pool since DB is sync."""
    await asyncio.to_thread(
        add_user,
        user.id,
        user.username,
        user.first_name,
        user.last_name,
    )


async def _send_status_message(message: Message, text: str) -> Message:
    """Send a status message and return it for later editing/deletion."""
    return await message.reply(text)


async def _send_download_result(
    message: Message,
    user: User,
    url: str,
    status_msg: Message,
) -> None:
    """Download and send files to user, with full error handling."""
    result: Optional[DownloadResult] = None
    try:
        # Run sync download in thread pool
        result = await asyncio.to_thread(download, url)

        if not result.files:
            await status_msg.edit_text("❌ هیچ فایلی برای این لینک پیدا نشد.")
            return

        await status_msg.edit_text(
            f"📤 در حال ارسال {len(result.files)} فایل..."
        )

        sent_count = 0
        for file_path in result.files:
            try:
                # Check file size before sending
                if is_file_too_large(file_path):
                    await message.reply(
                        f"⚠️ فایل <code>{os.path.basename(file_path)}</code> "
                        f"بیش از {settings.MAX_FILE_SIZE_MB} مگابایت است و "
                        f"نمی‌توان آن را ارسال کرد."
                    )
                    continue

                file = FSInputFile(file_path)
                caption = result.caption or ""
                # Truncate per Telegram limit
                if file_path.lower().endswith((".jpg", ".jpeg", ".png")):
                    caption = caption[:1024]
                else:
                    caption = caption[:4096]

                if file_path.lower().endswith((".mp4", ".mov", ".webm")):
                    await message.answer_video(file, caption=caption)
                else:
                    await message.answer_photo(file, caption=caption)
                sent_count += 1

            except TelegramBadRequest as e:
                logger.error("Telegram error sending %s: %s", file_path, e)
                await message.reply(
                    f"⚠️ خطا در ارسال فایل <code>{os.path.basename(file_path)}</code>: "
                    f"<code>{str(e)[:200]}</code>"
                )
            except Exception as e:
                logger.exception("Unexpected error sending file %s", file_path)
                await message.reply(
                    f"⚠️ خطای غیرمنتظره در ارسال فایل: <code>{str(e)[:200]}</code>"
                )

        # Record successful download in DB
        await asyncio.to_thread(
            add_download,
            user.id, url, result.platform, "success", result.file_size_kb,
        )
        # Increment daily quota
        await asyncio.to_thread(increment_quota, user.id)

        # Edit status to success
        if sent_count > 0:
            with suppress(TelegramBadRequest):
                await status_msg.delete()
            await message.reply(
                f"✅ {sent_count} فایل با موفقیت ارسال شد. "
                f"سهمیه امروز شما: {(await asyncio.to_thread(__get_user_quota_used, user.id))} استفاده شده."
            )
        else:
            await status_msg.edit_text("❌ هیچ فایلی ارسال نشد.")

    except ValueError as e:
        await status_msg.edit_text(f"❌ {e}")
    except Exception as e:
        logger.exception("Download failed for %s", url)
        await status_msg.edit_text(
            f"❌ خطا در دانلود: <code>{str(e)[:300]}</code>"
        )
        # Record failed download
        try:
            await asyncio.to_thread(
                add_download, user.id, url, "unknown", "failed", None,
            )
        except Exception:
            pass
    finally:
        if result is not None:
            await asyncio.to_thread(result.cleanup)


def __get_user_quota_used(user_id: int) -> int:
    """Helper to fetch quota count (sync)."""
    from database import get_quota
    return get_quota(user_id)


# ============================================================
#  Command handlers
# ============================================================

@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Welcome message (from DB settings, fallback to default)."""
    user = message.from_user
    if user:
        await _register_user(user)

    welcome = await asyncio.to_thread(
        get_setting, "welcome_message",
        "👋 سلام! به ربات دانلود خوش آمدید.\n\n"
        "لینک پست یا ریلز اینستاگرام (یا تیک‌تاک، یوتیوب شورتز، توییتر) را بفرستید."
    )
    await message.answer(welcome)


@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Help message."""
    help_text = (
        "📖 <b>راهنمای ربات</b>\n\n"
        "📥 <b>نحوه استفاده:</b>\n"
        "کافیست لینک پست یا ریلز را در چت بفرستید. ربات به‌صورت خودکار آن را دانلود "
        "و ارسال می‌کند.\n\n"
        "🌐 <b>پلتفرم‌های پشتیبانی‌شده:</b>\n"
        "• Instagram (پست، ریلز، استوری)\n"
        "• TikTok (ویدیو)\n"
        "• YouTube Shorts\n"
        "• Twitter/X (ویدیو و عکس)\n\n"
        "⚡ <b>دستورات:</b>\n"
        "/start — پیام خوش‌آمدگویی\n"
        "/help — همین راهنما\n"
        "/quota — سهمیه باقی‌مانده امروز\n"
        "/stats — آمار کلی ربات\n"
        "/id — شناسه عددی شما (برای ادمین)\n\n"
        "📊 <b>محدودیت:</b>\n"
        f"هر کاربر می‌تواند روزانه {settings.DAILY_QUOTA} دانلود داشته باشد. "
        "کاربران Premium بدون محدودیت هستند."
    )
    await message.answer(help_text)


@dp.message(Command("quota"))
async def cmd_quota(message: Message) -> None:
    """Show user's remaining daily quota."""
    user = message.from_user
    if not user:
        return

    allowed, used, limit = await asyncio.to_thread(check_quota, user.id)
    if limit == 0:
        await message.answer(
            f"📊 سهمیه امروز شما: <b>نامحدود</b> (Premium)\n"
            f"استفاده شده: {used}"
        )
    else:
        remaining = max(0, limit - used)
        await message.answer(
            f"📊 <b>سهمیه امروز شما</b>\n\n"
            f"استفاده شده: <b>{used}</b> از {limit}\n"
            f"باقی‌مانده: <b>{remaining}</b>\n\n"
            f"سهمیه هر ۲۴ ساعت بازنشانی می‌شود (UTC)."
        )


@dp.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """Show bot stats (public)."""
    stats = await asyncio.to_thread(get_stats)
    text = (
        "📊 <b>آمار ربات</b>\n\n"
        f"👥 کل کاربران: <b>{stats['users']}</b>\n"
        f"📥 کل دانلودها: <b>{stats['downloads']}</b>\n"
        f"📈 دانلودهای امروز: <b>{stats['today_downloads']}</b>\n"
        f"🔥 کاربران فعال (۷ روز): <b>{stats['active_users_7d']}</b>\n"
    )
    await message.answer(text)


@dp.message(Command("id"))
async def cmd_id(message: Message) -> None:
    """Return the user's numeric ID (useful for admin setup)."""
    user = message.from_user
    if not user:
        return
    is_admin_flag = "✅ ادمین" if is_admin(user.id) else "❌ غیرادمین"
    await message.answer(
        f"🆔 <b>اطلاعات شما</b>\n\n"
        f"شناسه عددی: <code>{user.id}</code>\n"
        f"نام کاربری: @{user.username}\n"
        f"نام: {_user_display_name(user)}\n"
        f"وضعیت: {is_admin_flag}"
    )


# ============================================================
#  Inline mode (@bot <url>)
# ============================================================

@dp.inline_query()
async def inline_query_handler(query: InlineQuery) -> None:
    """Handle @bot <url> inline queries."""
    url = query.query.strip()
    if not url:
        await query.answer(
            results=[],
            button=InlineQueryResultsButton(
                text="📋 لینک پست اینستاگرام، تیک‌تاک، یوتیوب یا توییتر را بنویسید...",
                start="help",
            ),
            cache_time=5,
        )
        return

    platform = detect_platform(url)
    if not platform:
        await query.answer(
            results=[],
            button=InlineQueryResultsButton(
                text="❌ لینک پشتیبانی نمی‌شود",
                start="help",
            ),
            cache_time=5,
        )
        return

    # Acknowledge with a placeholder — actual download happens via "switch to PM"
    await query.answer(
        results=[],
        button=InlineQueryResultsButton(
            text=f"📥 برای دانلود، اینجا کلیک کنید ({platform})",
            start=f"dl:{url}",
        ),
        cache_time=10,
    )


@dp.message(Command("dl"))
async def cmd_dl(message: Message, command: CommandObject) -> None:
    """Handle /dl <url> from inline mode button press (deep link)."""
    if not command.args:
        return
    args = command.args.strip()
    # Could be "dl:URL" form from deep link
    if args.startswith("dl:"):
        args = args[3:].strip()
    if not args:
        return

    # Treat as a regular URL message
    message.text = args
    await handle_url_message(message)


# ============================================================
#  URL message handler (the main download trigger)
# ============================================================

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_url_message(message: Message) -> None:
    """Handle any non-command text message — check for URL."""
    user = message.from_user
    if not user:
        return

    # Register user (idempotent)
    await _register_user(user)

    text = message.text.strip()
    platform = detect_platform(text)

    if not platform:
        await message.answer(
            "❗ لطفاً یک لینک معتبر از اینستاگرام، تیک‌تاک، یوتیوب شورتز، یا توییتر "
            "ارسال کنید. برای راهنما /help را بفرستید."
        )
        return

    # 1. Check ban
    if await asyncio.to_thread(is_banned, user.id):
        await message.answer("🚫 حساب شما مسدود است. در صورت اشتباه با ادمین تماس بگیرید.")
        return

    # 2. Check if bot is active (master switch)
    is_active = await asyncio.to_thread(get_setting, "is_active", "True")
    if is_active != "True":
        await message.answer("🔴 ربات موقتاً غیرفعال است. لطفاً بعداً تلاش کنید.")
        return

    # 3. Check daily quota
    allowed, used, limit = await asyncio.to_thread(check_quota, user.id)
    if not allowed:
        await message.answer(
            f"⏰ سهمیه دانلود امروز شما ({limit}) تمام شده است.\n"
            f"سهمیه هر ۲۴ ساعت (UTC) بازنشانی می‌شود.\n"
            f"استفاده شده: {used}"
        )
        return

    # 4. Send status and start download
    status_msg = await _send_status_message(
        message,
        f"⏳ در حال دانلود از <b>{platform}</b>...\n"
        f"سهمیه: {used + 1}/{limit}" if limit > 0
        else f"⏳ در حال دانلود از <b>{platform}</b>..."
    )

    await _send_download_result(message, user, text, status_msg)


# ============================================================
#  Lifecycle
# ============================================================

shutdown_event = asyncio.Event()


def _signal_handler(signum, frame):
    """Handle SIGINT/SIGTERM for graceful shutdown."""
    sig_name = signal.Signals(signum).name
    logger.info("📡 Received %s, initiating graceful shutdown...", sig_name)
    shutdown_event.set()


async def main() -> None:
    """Entry point."""
    setup_logging()
    logger.info("=" * 60)
    logger.info("🚀 TelegramBot v2.0 starting up...")
    logger.info("=" * 60)

    # Initialize database
    await asyncio.to_thread(init_db)
    logger.info("✅ Database initialized")

    # Register signal handlers
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Start polling (this runs until stopped)
    logger.info("🤖 Bot is online. Press Ctrl+C to stop.")

    try:
        # Run polling and shutdown event concurrently
        polling_task = asyncio.create_task(
            dp.start_polling(bot, handle_signals=False)
        )
        shutdown_task = asyncio.create_task(shutdown_event.wait())

        # Wait for either to complete
        done, pending = await asyncio.wait(
            {polling_task, shutdown_task},
            return_when=asyncio.FIRST_COMPLETED,
        )

        # Cancel the other task
        for task in pending:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    except Exception:
        logger.exception("Fatal error in main loop")
    finally:
        logger.info("🔒 Shutting down bot...")
        await bot.session.close()
        logger.info("👋 Goodbye!")


if __name__ == "__main__":
    # Set event loop policy for Windows compatibility
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
