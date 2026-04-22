"""Feature and state layer schema

Revision ID: 20260422_0003
Revises: 20260422_0002
Create Date: 2026-04-22 01:15:00
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260422_0003"
down_revision = "20260422_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shipment_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("shipment_key", sa.String(length=128), nullable=False),
        sa.Column("latest_event_id", sa.Integer(), nullable=True),
        sa.Column("last_source", sa.String(length=32), nullable=False),
        sa.Column("last_event_type", sa.String(length=80), nullable=False),
        sa.Column("last_entity_id", sa.String(length=128), nullable=True),
        sa.Column("event_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("avg_severity", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_severity", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("provisional_dri", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("feature_vector", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["latest_event_id"], ["ingestion_events.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("shipment_key"),
    )

    op.create_index(op.f("ix_shipment_snapshots_id"), "shipment_snapshots", ["id"], unique=False)
    op.create_index(
        op.f("ix_shipment_snapshots_shipment_key"),
        "shipment_snapshots",
        ["shipment_key"],
        unique=True,
    )
    op.create_index(
        op.f("ix_shipment_snapshots_latest_event_id"),
        "shipment_snapshots",
        ["latest_event_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_shipment_snapshots_last_source"),
        "shipment_snapshots",
        ["last_source"],
        unique=False,
    )
    op.create_index(
        op.f("ix_shipment_snapshots_last_event_type"),
        "shipment_snapshots",
        ["last_event_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_shipment_snapshots_last_entity_id"),
        "shipment_snapshots",
        ["last_entity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_shipment_snapshots_last_occurred_at"),
        "shipment_snapshots",
        ["last_occurred_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_shipment_snapshots_updated_at"),
        "shipment_snapshots",
        ["updated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_shipment_snapshots_updated_at"), table_name="shipment_snapshots")
    op.drop_index(op.f("ix_shipment_snapshots_last_occurred_at"), table_name="shipment_snapshots")
    op.drop_index(op.f("ix_shipment_snapshots_last_entity_id"), table_name="shipment_snapshots")
    op.drop_index(op.f("ix_shipment_snapshots_last_event_type"), table_name="shipment_snapshots")
    op.drop_index(op.f("ix_shipment_snapshots_last_source"), table_name="shipment_snapshots")
    op.drop_index(op.f("ix_shipment_snapshots_latest_event_id"), table_name="shipment_snapshots")
    op.drop_index(op.f("ix_shipment_snapshots_shipment_key"), table_name="shipment_snapshots")
    op.drop_index(op.f("ix_shipment_snapshots_id"), table_name="shipment_snapshots")
    op.drop_table("shipment_snapshots")
