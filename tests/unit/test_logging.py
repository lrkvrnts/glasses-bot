"""Logging should not crash the process if the log file is not writable."""

from __future__ import annotations

from pathlib import Path

from bot.config.logging import setup_logging
from bot.config.settings import get_settings


def test_setup_logging_survives_unwritable_file(set_env, tmp_path: Path, monkeypatch) -> None:
    blocked = tmp_path / "missing-dir" / "bot.log"
    monkeypatch.setenv("LOG_FILE", str(blocked))

    from bot.config.settings import get_settings as _gs

    _gs.cache_clear()
    settings = get_settings()
    setup_logging(settings)
