"""
config.py — Single source of truth for all configuration.

Uses pydantic-settings to load from environment variables / .env file.
No more hardcoded secrets, no more parallel config systems.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from .env"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── Telegram ───
    BOT_TOKEN: str
    ADMIN_IDS: str = ""  # comma-separated string, parsed below

    # ─── Bot behavior ───
    DAILY_QUOTA: int = 20
    MAX_FILE_SIZE_MB: int = 50
    DOWNLOAD_TIMEOUT: int = 120

    # ─── Admin panel ───
    ADMIN_USER: str = "admin"
    ADMIN_PASS: str = "change_me"
    PANEL_HOST: str = "0.0.0.0"
    PANEL_PORT: int = 8000
    SECRET_KEY: str = "dev-secret-change-me"

    # ─── Database ───
    DB_PATH: str = "./data/bot_data.db"

    # ─── Instagram (optional) ───
    INSTAGRAM_USERNAME: str = ""
    INSTAGRAM_PASSWORD: str = ""

    # ─── Logging ───
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/bot.log"

    @field_validator("BOT_TOKEN")
    @classmethod
    def _bot_token_not_empty(cls, v: str) -> str:
        if not v or v == "your_bot_token_here":
            raise ValueError(
                "BOT_TOKEN must be set in .env. Get it from @BotFather."
            )
        return v

    @field_validator("ADMIN_IDS")
    @classmethod
    def _parse_admin_ids(cls, v: str) -> str:
        # Normalize: trim, remove duplicates, keep as comma-separated string
        if not v:
            return ""
        ids = [x.strip() for x in v.split(",") if x.strip().isdigit()]
        return ",".join(sorted(set(ids)))

    @property
    def admin_id_list(self) -> List[int]:
        """ADMIN_IDS as a list of ints."""
        if not self.ADMIN_IDS:
            return []
        return [int(x) for x in self.ADMIN_IDS.split(",") if x.strip()]

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_id_list


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — instantiate once per process."""
    return Settings()  # type: ignore[call-arg]


# Convenience module-level access (do not use in tests)
try:
    settings = get_settings()
except Exception as e:  # pragma: no cover
    import sys
    print(f"❌ Configuration error: {e}", file=sys.stderr)
    print("💡 Copy .env.example to .env and fill in your values.", file=sys.stderr)
    settings = None  # type: ignore[assignment]
