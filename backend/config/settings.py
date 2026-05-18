"""
Task 14: Environment Variable Validation with Pydantic BaseSettings.
Single source of truth for all configuration. Validates on import and
prints a clear startup summary.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """All environment variables with types, defaults, and validation."""

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Database
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")

    # Telegram
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")

    # AI
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")

    # External APIs
    fred_api_key: str = Field(default="", alias="FRED_API_KEY")

    # Render
    render_external_url: Optional[str] = Field(default=None, alias="RENDER_EXTERNAL_URL")

    class Config:
        env_file = str(Path(__file__).resolve().parent.parent.parent / ".env")
        env_file_encoding = "utf-8"
        populate_by_name = True

    # ─── Feature Flags (derived) ─────────────────────────────

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    @property
    def gemini_enabled(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def postgres_enabled(self) -> bool:
        return bool(self.database_url)

    @property
    def fred_enabled(self) -> bool:
        return bool(self.fred_api_key)

    def print_startup_summary(self):
        """Print a clear config summary on server start."""

        def _status(enabled: bool) -> str:
            return "✅ ON" if enabled else "❌ OFF"

        print("\n" + "=" * 55)
        print("  MarketPulse Agent Alpha v3.0 — Config Summary")
        print("=" * 55)
        print(f"  Server ........... {self.host}:{self.port}")
        print(f"  Database ......... {_status(self.postgres_enabled)} {'(PostgreSQL)' if self.postgres_enabled else '(SQLite fallback)'}")
        print(f"  Telegram Bot ..... {_status(self.telegram_enabled)}")
        print(f"  Gemini AI ........ {_status(self.gemini_enabled)}")
        print(f"  FRED Macro ....... {_status(self.fred_enabled)}")
        print(f"  Render Deploy .... {_status(bool(self.render_external_url))}")
        print("=" * 55 + "\n")

        if not self.telegram_enabled:
            print("  ⚠️  TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing — daily briefings disabled.")
        if not self.gemini_enabled:
            print("  ⚠️  GEMINI_API_KEY missing — AI trade explainer disabled.")


# Singleton — validated on first import
settings = Settings()
