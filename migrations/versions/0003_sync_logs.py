"""add sync_logs table

Revision ID: 0003_sync_logs
Revises: 0002_products
Create Date: 2026-09-02 13:40:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_sync_logs"
down_revision: str | Sequence[str] | None = "0002_products"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sync_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("seller_id", sa.Integer(), nullable=False),
        sa.Column("user_telegram_id", sa.Integer(), nullable=False),
        sa.Column("operation", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("items_total", sa.Integer(), server_default="0", nullable=False),
        sa.Column("items_success", sa.Integer(), server_default="0", nullable=False),
        sa.Column("items_failed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("celery_task_id", sa.String(length=64), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["seller_id"], ["seller_accounts.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_sync_logs_seller_id", "sync_logs", ["seller_id"])
    op.create_index("ix_sync_logs_user_telegram_id", "sync_logs", ["user_telegram_id"])
    op.create_index("ix_sync_logs_celery_task_id", "sync_logs", ["celery_task_id"])


def downgrade() -> None:
    op.drop_index("ix_sync_logs_celery_task_id", table_name="sync_logs")
    op.drop_index("ix_sync_logs_user_telegram_id", table_name="sync_logs")
    op.drop_index("ix_sync_logs_seller_id", table_name="sync_logs")
    op.drop_table("sync_logs")
