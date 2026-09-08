"""Shared pytest fixtures."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# CI has no .env; celery_app and EncryptionService import Settings at collection time.
_TEST_ENV = {
    "BOT_TOKEN": "test:token",
    "BOT_MODE": "polling",
    "WEBHOOK_URL": "https://bot.example.com",
    "WEBHOOK_PATH": "/webhook",
    "WEBHOOK_SECRET": "supersecret",
    "DB_HOST": "localhost",
    "DB_NAME": "test_db",
    "DB_USER": "test_user",
    "DB_PASSWORD": "test_pass",
    "REDIS_URL": "redis://localhost:6379/0",
    "CELERY_BROKER_URL": "redis://localhost:6379/1",
    "CELERY_RESULT_BACKEND": "redis://localhost:6379/2",
    "ENCRYPTION_KEY": "RmhpzvVz_QfGBcNCx4gPu-Ds6V-qU8cK-JSTu6_79Hw=",
}
for _key, _value in _TEST_ENV.items():
    os.environ.setdefault(_key, _value)

from bot.db.base import Base  # noqa: E402
from bot.db.models import *  # noqa: E402,F401,F403  # register all models


@pytest.fixture(autouse=True)
def clear_settings_cache() -> Iterator[None]:
    """Сбрасываем кеш get_settings между тестами."""
    from bot.config.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def env_vars() -> dict[str, str]:
    """Базовый набор env-переменных для Settings."""
    return dict(_TEST_ENV)


@pytest.fixture
def set_env(env_vars: dict[str, str]) -> Iterator[None]:
    """Устанавливает env_vars в окружение на время теста."""
    # Сохраняем только нужные ключи, чтобы не сломать существующие
    saved: dict[str, str | None] = {}
    for key in env_vars:
        saved[key] = os.environ.get(key)
        os.environ[key] = env_vars[key]
    yield
    for key, val in saved.items():
        if val is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = val


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    """In-memory SQLite session для unit-тестов репозиториев."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as s:
        yield s
    await engine.dispose()
