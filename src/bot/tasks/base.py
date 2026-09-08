"""Base Celery task with DB session."""

from __future__ import annotations

from typing import Any

from celery import Task


class DbTask(Task):
    """Базовый класс Celery Task, дающий доступ к AsyncSession.

    Конкретные задачи должны принимать session как первый аргумент.
    """

    abstract = True

    def run(self, *args: Any, **kwargs: Any) -> Any:  # type: ignore[override]
        raise NotImplementedError

    async def execute(self, session, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError
