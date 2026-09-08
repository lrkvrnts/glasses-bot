"""Tests for application settings."""

from __future__ import annotations


def test_settings_loads_from_env(set_env):
    """Settings загружает значения из env."""
    from bot.config.settings import get_settings

    settings = get_settings()

    assert settings.bot_token == "test:token"
    assert settings.webhook_url == "https://bot.example.com"
    assert settings.webhook_secret == "supersecret"


def test_settings_database_url_async(set_env):
    """Async DSN содержит asyncpg драйвер."""
    from bot.config.settings import get_settings

    settings = get_settings()

    assert settings.database_url == (
        "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db"
    )


def test_settings_compose_db_host_rewritten_outside_docker(set_env, monkeypatch):
    """На хосте DB_HOST=postgres в DSN становится localhost."""
    monkeypatch.setenv("DB_HOST", "postgres")
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/0")

    from bot.config import settings as settings_mod

    monkeypatch.setattr(settings_mod, "running_in_docker", lambda: False)

    settings = settings_mod.get_settings()

    assert settings.database_url == (
        "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db"
    )
    assert settings.redis_url == "redis://localhost:6379/0"


def test_settings_database_url_sync(set_env):
    """Sync DSN для Alembic без asyncpg."""
    from bot.config.settings import get_settings

    settings = get_settings()

    assert settings.database_url_sync == ("postgresql://test_user:test_pass@localhost:5432/test_db")


def test_settings_webhook_full_url(set_env):
    """webhook_full_url объединяет URL + path + secret."""
    from bot.config.settings import get_settings

    settings = get_settings()

    assert settings.webhook_full_url == "https://bot.example.com/webhook/supersecret"


def test_settings_webhook_path_domain_coerced_to_default(set_env, monkeypatch):
    """Если в WEBHOOK_PATH по ошибке домен — используем /webhook."""
    monkeypatch.setenv("WEBHOOK_PATH", "ruglasses.site")

    from bot.config.settings import get_settings

    settings = get_settings()

    assert settings.webhook_path == "/webhook"
    assert settings.webhook_full_url == "https://bot.example.com/webhook/supersecret"


def test_settings_get_settings_is_cached(set_env):
    """get_settings возвращает один и тот же инстанс."""
    from bot.config.settings import get_settings

    s1 = get_settings()
    s2 = get_settings()

    assert s1 is s2


def test_settings_missing_required_raises(monkeypatch):
    """Без обязательной переменной Settings падает с ValidationError."""
    import pytest
    from pydantic import ValidationError

    from bot.config.settings import Settings

    monkeypatch.delenv("BOT_TOKEN", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_default_values(set_env):
    """Defaults применяются, если env не переопределяет."""
    from bot.config.settings import get_settings

    settings = get_settings()

    assert settings.webhook_path == "/webhook"
    assert settings.webhook_port == 8080
    assert settings.ozon_api_base == "https://api-seller.ozon.ru"
    assert settings.ozon_rate_limit_rps == 5.0
    assert settings.log_level == "INFO"


def test_settings_admins_telegram_ids_parsed_from_csv(set_env, monkeypatch):
    """Список ADMINS_TELEGRAM_IDS парсится из CSV-строки."""
    monkeypatch.setenv("ADMINS_TELEGRAM_IDS", "111,222,333")

    from bot.config.settings import get_settings

    settings = get_settings()

    assert settings.admins_telegram_ids == [111, 222, 333]


def test_settings_admins_telegram_ids_empty_by_default(set_env, monkeypatch):
    """Если ADMINS_TELEGRAM_IDS не задан — пустой список."""
    monkeypatch.setenv("ADMINS_TELEGRAM_IDS", "")

    from bot.config.settings import get_settings

    settings = get_settings()

    assert settings.admins_telegram_ids == []
