"""Курсорная пагинация списков Ozon в Telegram."""

from __future__ import annotations

import math


def remember_next_cursor(cursors: list[str], page: int, next_last_id: str) -> list[str]:
    """cursors[i] — cursor/last_id для запроса страницы i."""
    out = list(cursors)
    next_idx = page + 1
    if not next_last_id:
        return out[:next_idx]
    if next_idx < len(out):
        out[next_idx] = next_last_id
        return out
    if next_idx == len(out):
        out.append(next_last_id)
        return out
    raise ValueError("страницы нужно листать по порядку")


def page_count(total: int, page_size: int) -> int:
    return max(1, math.ceil(total / page_size) if total else 1)


def safe_xlsx_stem(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name)
    return (cleaned[:40] or "cabinet")
