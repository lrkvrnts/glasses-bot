"""Dispatcher setup."""

from __future__ import annotations

from aiogram import Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from bot.bot_app.handlers import (
    bind_router,
    help_router,
    prices_router,
    products_list_router,
    products_upload_router,
    seller_list_router,
    start_router,
    status_router,
    stocks_router,
    uploads_router,
)
from bot.bot_app.handlers.errors import router as errors_router
from bot.bot_app.middlewares import DbSessionMiddleware, MenuResetFSMMiddleware, UserMiddleware
from bot.config.settings import Settings


def build_dispatcher(settings: Settings) -> Dispatcher:
    """Собирает dispatcher с middleware и роутерами."""
    # FSM storage: Redis если доступен, иначе Memory
    storage: RedisStorage | MemoryStorage
    try:
        redis = Redis.from_url(settings.redis_url)
        storage = RedisStorage(redis=redis)
    except Exception:
        storage = MemoryStorage()

    dp = Dispatcher(
        storage=storage,
        name="main",
    )
    dp["default"] = DefaultBotProperties(parse_mode=ParseMode.HTML)

    # Middlewares (порядок важен)
    dp.message.middleware.register(MenuResetFSMMiddleware())
    dp.message.middleware.register(DbSessionMiddleware())
    dp.message.middleware.register(UserMiddleware())
    dp.callback_query.middleware.register(DbSessionMiddleware())
    dp.callback_query.middleware.register(UserMiddleware())

    # Routers (порядок важен — более специфичные раньше)
    dp.include_router(start_router)
    dp.include_router(bind_router)
    dp.include_router(seller_list_router)
    dp.include_router(products_list_router)
    dp.include_router(products_upload_router)
    dp.include_router(status_router)
    dp.include_router(stocks_router)
    dp.include_router(prices_router)
    dp.include_router(uploads_router)
    dp.include_router(help_router)
    # errors_router last (catch-all)
    dp.include_router(errors_router)

    return dp
