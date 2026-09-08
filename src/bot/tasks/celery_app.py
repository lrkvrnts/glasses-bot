"""Celery application."""

from __future__ import annotations

from celery import Celery
from kombu import Exchange, Queue

from bot.config.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "ozon_bot",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["bot.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("bulk", Exchange("bulk"), routing_key="bulk"),
    ),
    task_routes={
        "bot.tasks.bulk_*": {"queue": "bulk"},
    },
)
