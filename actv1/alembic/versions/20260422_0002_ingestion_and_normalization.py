"""Ingestion and normalization schema

Revision ID: 20260422_0002
Revises: 20260422_0001
Create Date: 2026-04-22 00:30:00
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260422_0002"
down_revision = "20260422_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingestion_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("source_event_id", sa.String(length=128), nullable=True),
        sa.Column("dedupe_key", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.String(length=128), nullable=True),
        sa.Column("severity", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dedupe_key"),
    )

    op.create_index(op.f("ix_ingestion_events_id"), "ingestion_events", ["id"], unique=False)
    op.create_index(
        op.f("ix_ingestion_events_source"),
        "ingestion_events",
        ["source"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ingestion_events_source_event_id"),
        "ingestion_events",
        ["source_event_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ingestion_events_dedupe_key"),
        "ingestion_events",
        ["dedupe_key"],
        unique=True,
    )
    op.create_index(
        op.f("ix_ingestion_events_event_type"),
        "ingestion_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ingestion_events_entity_id"),
        "ingestion_events",
        ["entity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ingestion_events_occurred_at"),
        "ingestion_events",
        ["occurred_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ingestion_events_ingested_at"),
        "ingestion_events",
        ["ingested_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_ingestion_events_ingested_at"), table_name="ingestion_events")
    op.drop_index(op.f("ix_ingestion_events_occurred_at"), table_name="ingestion_events")
    op.drop_index(op.f("ix_ingestion_events_entity_id"), table_name="ingestion_events")
    op.drop_index(op.f("ix_ingestion_events_event_type"), table_name="ingestion_events")
    op.drop_index(op.f("ix_ingestion_events_dedupe_key"), table_name="ingestion_events")
    op.drop_index(op.f("ix_ingestion_events_source_event_id"), table_name="ingestion_events")
    op.drop_index(op.f("ix_ingestion_events_source"), table_name="ingestion_events")
    op.drop_index(op.f("ix_ingestion_events_id"), table_name="ingestion_events")
    op.drop_table("ingestion_events")
