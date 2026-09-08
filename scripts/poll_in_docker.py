"""Polling-режим для запуска внутри Docker-контейнера.

Используется в docker-compose.yml как entrypoint сервиса bot.
"""
from __future__ import annotations

import asyncio
import sys

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from bot.bot_app.dispatcher import build_dispatcher
from bot.config.logging import setup_logging
from bot.config.settings import get_settings


async def main() -> None:
    settings = get_settings()
    setup_logging(settings)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = build_dispatcher(settings)

    # Удаляем webhook, чтобы polling заработал
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Starting in POLLING mode (Docker)")

    try:
        await dp.start_polling(
            bot, allowed_updates=dp.resolve_used_update_types()
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
