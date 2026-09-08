"""Bot entrypoint."""

from __future__ import annotations

import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from loguru import logger

from bot.bot_app.dispatcher import build_dispatcher
from bot.config.logging import setup_logging
from bot.config.settings import Settings, get_settings
from bot.health import healthz

_WEBHOOK_HINT = (
    "WEBHOOK_URL must be a public HTTPS hostname that Telegram can resolve "
    "(your domain or a tunnel). A t.me bot link will not work. "
    "For local Docker without a public domain, set BOT_MODE=polling."
)


async def on_startup(bot: Bot) -> None:
    """Drop webhook in polling. Webhook registration happens after HTTP bind."""
    settings = get_settings()
    if settings.bot_mode == "polling":
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Polling mode: webhook not registered")


async def _register_telegram_webhook(bot: Bot, settings: Settings) -> None:
    """Call setWebhook after /healthz is already listening."""
    url = settings.webhook_full_url
    if "t.me" in settings.webhook_url.lower():
        logger.error("Failed to set webhook. {}", _WEBHOOK_HINT, url=url)
        return
    try:
        await bot.set_webhook(
            url=url,
            secret_token=settings.webhook_secret,
            drop_pending_updates=True,
        )
    except TelegramBadRequest:
        logger.error("Failed to set webhook. {}", _WEBHOOK_HINT, url=url)
        return
    logger.info("Webhook set", url=url)


async def on_shutdown(bot: Bot) -> None:
    """Remove webhook on bot shutdown."""
    await bot.delete_webhook()
    logger.info("Webhook deleted")


async def _serve_healthz(settings: Settings) -> web.AppRunner:
    """HTTP /healthz for Docker healthcheck (polling mode)."""
    app = web.Application()
    app.router.add_get("/healthz", healthz)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.webhook_host, settings.webhook_port)
    await site.start()
    return runner


async def _run_polling(bot: Bot, dp: Dispatcher, settings: Settings) -> None:
    runner = await _serve_healthz(settings)
    logger.info(
        "Starting bot in polling mode",
        host=settings.webhook_host,
        port=settings.webhook_port,
    )
    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()


async def _run_webhook(bot: Bot, dp: Dispatcher, settings: Settings) -> None:
    app = web.Application()
    app.router.add_get("/healthz", healthz)

    webhook_path = f"{settings.webhook_path}/{settings.webhook_secret}"
    handler = SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=settings.webhook_secret)
    handler.register(app, path=webhook_path)
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.webhook_host, settings.webhook_port)
    await site.start()
    logger.info("Starting bot", host=settings.webhook_host, port=settings.webhook_port)
    # HTTP already up so Docker healthcheck can pass even if Telegram is slow/blocked.
    await _register_telegram_webhook(bot, settings)
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


async def main() -> None:
    """Run the bot in webhook or polling mode."""
    settings = get_settings()
    setup_logging(settings)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = build_dispatcher(settings)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        if settings.bot_mode == "polling":
            await _run_polling(bot, dp, settings)
        else:
            await _run_webhook(bot, dp, settings)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
