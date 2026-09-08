"""Logging configuration."""

from __future__ import annotations

import sys

from loguru import logger

from bot.config.settings import Settings


def setup_logging(settings: Settings) -> None:
    """Configure loguru logger."""
    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.log_level,
        serialize=True,
        backtrace=True,
        diagnose=False,
    )
    try:
        logger.add(
            settings.log_file,
            level=settings.log_level,
            rotation=settings.log_rotation,
            retention=settings.log_retention,
            serialize=True,
        )
    except OSError as exc:
        logger.warning(
            "Cannot write log file, stdout only",
            path=settings.log_file,
            error=str(exc),
        )
    logger.info("Logging configured", level=settings.log_level)
