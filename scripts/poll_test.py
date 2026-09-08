"""Polling-режим для локального тестирования.

Использование:
    poetry run python scripts/poll_test.py

Бот стартует в polling-режиме (long polling вместо webhook).
Подходит для разработки без Docker/HTTPS/домена.
"""
from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from bot.bot_app.dispatcher import build_dispatcher
from bot.config.settings import get_settings


async def main() -> None:
    settings = get_settings()

    # В polling-режиме URL/secret не нужны, но dispatcher их требует
    # Подменим дефолтами чтобы не падать
    if not settings.webhook_url or "example.com" in settings.webhook_url:
        # Ничего не делаем, dispatcher всё равно собирается,
        # просто setWebhook вызывать не будем
        pass

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = build_dispatcher(settings)

    logger.info("Starting in POLLING mode (no webhook)")
    logger.warning(
        "Не запускай poll_test.py одновременно с Docker-ботом: "
        "один BOT_TOKEN — только один getUpdates."
    )
    logger.info("Press Ctrl+C to stop")

    # Удаляем webhook, чтобы polling заработал
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
