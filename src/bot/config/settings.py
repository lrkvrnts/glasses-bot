"""Application settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlsplit, urlunsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

_COMPOSE_HOSTS = frozenset({"postgres", "redis"})


def running_in_docker() -> bool:
    """True внутри контейнера (есть /.dockerenv)."""
    return Path("/.dockerenv").exists()


def _runtime_hostname(host: str) -> str:
    """Имена сервисов Compose на хосте резолвятся в localhost."""
    if host in _COMPOSE_HOSTS and not running_in_docker():
        return "localhost"
    return host


def _rewrite_compose_url(url: str) -> str:
    """redis://redis:6379/0 → redis://localhost:6379/0 вне Docker."""
    parts = urlsplit(url)
    hostname = parts.hostname
    if hostname is None or hostname not in _COMPOSE_HOSTS or running_in_docker():
        return url
    netloc = parts.netloc.replace(hostname, "localhost", 1)
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def _parse_csv_ints(value: str | list[int]) -> list[int]:
    """Парсит CSV-строку с int-ами. Пустая строка → []."""
    if isinstance(value, list):
        return value
    if not value or not value.strip():
        return []
    return [int(x.strip()) for x in value.split(",") if x.strip()]


class Settings(BaseSettings):
    """Main application settings."""

    # Bot / Webhook
    bot_token: str = Field(alias="BOT_TOKEN")
    bot_mode: Literal["webhook", "polling"] = Field(default="webhook", alias="BOT_MODE")
    webhook_url: str = Field(alias="WEBHOOK_URL")
    webhook_path: str = Field(default="/webhook", alias="WEBHOOK_PATH")
    webhook_secret: str = Field(alias="WEBHOOK_SECRET")
    webhook_host: str = Field(default="0.0.0.0", alias="WEBHOOK_HOST")
    webhook_port: int = Field(default=8080, alias="WEBHOOK_PORT")
    # NoDecode отключает автоматический JSON-парсинг → парсим CSV в validator
    admins_telegram_ids: Annotated[list[int], NoDecode] = Field(
        default_factory=list, alias="ADMINS_TELEGRAM_IDS"
    )

    # DB
    db_host: str = Field(alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str = Field(alias="DB_NAME")
    db_user: str = Field(alias="DB_USER")
    db_password: str = Field(alias="DB_PASSWORD")

    # Redis
    redis_url: str = Field(alias="REDIS_URL")

    # Celery
    celery_broker_url: str = Field(alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(alias="CELERY_RESULT_BACKEND")

    # Ozon
    ozon_api_base: str = Field(default="https://api-seller.ozon.ru", alias="OZON_API_BASE")
    ozon_api_timeout: int = Field(default=30, alias="OZON_API_TIMEOUT")
    ozon_rate_limit_rps: float = Field(default=5.0, alias="OZON_RATE_LIMIT_RPS")
    encryption_key: str = Field(alias="ENCRYPTION_KEY")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: str = Field(default="./logs/bot.log", alias="LOG_FILE")
    log_rotation: str = Field(default="100 MB", alias="LOG_ROTATION")
    log_retention: str = Field(default="14 days", alias="LOG_RETENTION")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("webhook_path")
    @classmethod
    def _normalize_webhook_path(cls, v: str) -> str:
        """Path for Telegram, not a domain. 'ruglasses.site' → '/webhook'."""
        raw = (v or "/webhook").strip()
        if not raw.startswith("/") and "." in raw:
            return "/webhook"
        if not raw.startswith("/"):
            raw = f"/{raw}"
        return raw.rstrip("/") or "/webhook"

    @field_validator("webhook_url")
    @classmethod
    def _strip_webhook_url(cls, v: str) -> str:
        return v.strip().rstrip("/")

    @field_validator("admins_telegram_ids", mode="before")
    @classmethod
    def _parse_admins(cls, v: object) -> list[int]:
        """Парсит ADMINS_TELEGRAM_IDS как CSV (например: '111,222,333')."""
        if isinstance(v, str):
            return _parse_csv_ints(v)
        if isinstance(v, list):
            return v
        return []

    @field_validator("redis_url", "celery_broker_url", "celery_result_backend")
    @classmethod
    def _localhost_outside_docker(cls, v: str) -> str:
        return _rewrite_compose_url(v)

    @property
    def database_url(self) -> str:
        """Async PostgreSQL DSN."""
        host = _runtime_hostname(self.db_host)
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{host}:{self.db_port}/{self.db_name}"
        )

    @property
    def database_url_sync(self) -> str:
        """Sync PostgreSQL DSN (для Alembic offline)."""
        host = _runtime_hostname(self.db_host)
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{host}:{self.db_port}/{self.db_name}"
        )

    @property
    def webhook_full_url(self) -> str:
        """Полный URL webhook с secret в path."""
        return f"{self.webhook_url.rstrip('/')}{self.webhook_path}/{self.webhook_secret}"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()  # type: ignore[call-arg]
