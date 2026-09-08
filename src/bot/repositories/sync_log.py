"""SyncLogRepository."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select

from bot.db.models import SyncLog
from bot.repositories.base import BaseRepository


class SyncLogRepository(BaseRepository[SyncLog]):
    model = SyncLog

    async def list_for_user(self, telegram_id: int, limit: int = 20) -> list[SyncLog]:
        result = await self._session.execute(
            select(SyncLog)
            .where(SyncLog.user_telegram_id == telegram_id)
            .order_by(SyncLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars())

    async def mark_failed(
        self,
        sync_log: SyncLog,
        error: str,
        errors_file: str | None = None,
    ) -> None:
        sync_log.status = "failed"
        sync_log.error = error
        if errors_file:
            sync_log.error = f"{error}\n[errors_file={errors_file}]"
        sync_log.finished_at = datetime.now(UTC)
        await self._session.flush()

    async def mark_completed(self, sync_log: SyncLog) -> None:
        sync_log.status = "completed"
        sync_log.finished_at = datetime.now(UTC)
        await self._session.flush()
