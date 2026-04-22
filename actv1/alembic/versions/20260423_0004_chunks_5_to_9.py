# ruff: noqa: E501
"""Chunks 5-9 route, agent, realtime, proof, and hardening schema

Revision ID: 20260423_0004
Revises: 20260422_0003
Create Date: 2026-04-23 01:00:00
"""

import sqlalchemy as sa

from alembic import op

revision = "20260423_0004"
down_revision = "20260422_0003"
branch_labels = None
depends_on = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )
    ]


def upgrade() -> None:
    op.create_table(
        "routes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("shipment_key", sa.String(length=128), nullable=False),
        sa.Column("path", sa.JSON(), nullable=False),
        sa.Column("waypoints", sa.JSON(), nullable=False),
        sa.Column("cost_usd", sa.Float(), nullable=False),
        sa.Column("eta_hours", sa.Float(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("carbon_kg", sa.Float(), nullable=False),
        sa.Column("tariff_delta_usd", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("policy_penalty_usd", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("composite_score", sa.Float(), nullable=False),
        sa.Column("lp_score", sa.Float(), nullable=False),
        sa.Column("constraints_applied", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("solver_status", sa.String(length=50), nullable=False),
        sa.Column("selected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_routes_id"), "routes", ["id"], unique=False)
    op.create_index(op.f("ix_routes_shipment_key"), "routes", ["shipment_key"], unique=False)
    op.create_index(op.f("ix_routes_created_at"), "routes", ["created_at"], unique=False)

    op.create_table(
        "agent_overrides",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("shipment_key", sa.String(length=128), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("requested_by", sa.String(length=80), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("shipment_key"),
    )
    op.create_index(op.f("ix_agent_overrides_id"), "agent_overrides", ["id"], unique=False)
    op.create_index(
        op.f("ix_agent_overrides_shipment_key"),
        "agent_overrides",
        ["shipment_key"],
        unique=True,
    )

    op.create_table(
        "agent_actions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("shipment_key", sa.String(length=128), nullable=False),
        sa.Column("action_type", sa.String(length=50), nullable=False),
        sa.Column("dri_at_action", sa.Integer(), nullable=False),
        sa.Column("route_selected_id", sa.Integer(), nullable=True),
        sa.Column("shap_top_factor", sa.String(length=100), nullable=True),
        sa.Column("lp_constraints_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("roi_defended_usd", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "approval_status",
            sa.String(length=40),
            nullable=False,
            server_default=sa.text("'auto_approved'"),
        ),
        sa.Column("overridden_by_ops", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("replay_data", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("state_snapshot", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column(
            "executed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["route_selected_id"], ["routes.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_actions_id"), "agent_actions", ["id"], unique=False)
    op.create_index(op.f("ix_agent_actions_shipment_key"), "agent_actions", ["shipment_key"], unique=False)
    op.create_index(op.f("ix_agent_actions_action_type"), "agent_actions", ["action_type"], unique=False)
    op.create_index(op.f("ix_agent_actions_executed_at"), "agent_actions", ["executed_at"], unique=False)

    op.create_table(
        "notification_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("shipment_key", sa.String(length=128), nullable=False),
        sa.Column("channel", sa.String(length=50), nullable=False),
        sa.Column("recipient", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default=sa.text("'sent'")),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notification_records_id"), "notification_records", ["id"], unique=False)
    op.create_index(
        op.f("ix_notification_records_shipment_key"),
        "notification_records",
        ["shipment_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notification_records_created_at"),
        "notification_records",
        ["created_at"],
        unique=False,
    )

    op.create_table(
        "copilot_interactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("shipment_key", sa.String(length=128), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("grounded_on", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("shap_factors_used", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("route_constraints_used", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_copilot_interactions_id"), "copilot_interactions", ["id"], unique=False)
    op.create_index(
        op.f("ix_copilot_interactions_shipment_key"),
        "copilot_interactions",
        ["shipment_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_copilot_interactions_created_at"),
        "copilot_interactions",
        ["created_at"],
        unique=False,
    )

    op.create_table(
        "what_if_simulations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("shipment_key", sa.String(length=128), nullable=False),
        sa.Column("scenario", sa.JSON(), nullable=False),
        sa.Column("projected_dri", sa.Integer(), nullable=False),
        sa.Column("projected_routes", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("explanation", sa.Text(), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_what_if_simulations_id"), "what_if_simulations", ["id"], unique=False)
    op.create_index(
        op.f("ix_what_if_simulations_shipment_key"),
        "what_if_simulations",
        ["shipment_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_what_if_simulations_created_at"),
        "what_if_simulations",
        ["created_at"],
        unique=False,
    )

    op.create_table(
        "backtest_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scenario", sa.String(length=80), nullable=False),
        sa.Column("flag_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("grounding_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("industry_response_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("precursa_lead_minutes", sa.Float(), nullable=True),
        sa.Column("timeline", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_backtest_results_id"), "backtest_results", ["id"], unique=False)
    op.create_index(op.f("ix_backtest_results_scenario"), "backtest_results", ["scenario"], unique=False)
    op.create_index(op.f("ix_backtest_results_created_at"), "backtest_results", ["created_at"], unique=False)

    op.create_table(
        "wargame_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disturber_events_fired", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("healer_actions_taken", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("total_roi_defended_usd", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'running'")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_wargame_sessions_id"), "wargame_sessions", ["id"], unique=False)
    op.create_index(op.f("ix_wargame_sessions_started_at"), "wargame_sessions", ["started_at"], unique=False)

    op.create_table(
        "wargame_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("actor", sa.String(length=30), nullable=False),
        sa.Column("event_type", sa.String(length=60), nullable=False),
        sa.Column("affected_port", sa.String(length=80), nullable=True),
        sa.Column("severity", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("affected_shipment_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("potential_loss_usd", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("roi_defended_usd", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        *_timestamps(),
        sa.ForeignKeyConstraint(["session_id"], ["wargame_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_wargame_events_id"), "wargame_events", ["id"], unique=False)
    op.create_index(op.f("ix_wargame_events_session_id"), "wargame_events", ["session_id"], unique=False)
    op.create_index(op.f("ix_wargame_events_actor"), "wargame_events", ["actor"], unique=False)
    op.create_index(op.f("ix_wargame_events_created_at"), "wargame_events", ["created_at"], unique=False)

    op.create_table(
        "dead_letter_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("operation", sa.String(length=120), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(length=30), nullable=False, server_default=sa.text("'open'")),
        *_timestamps(),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_dead_letter_events_id"), "dead_letter_events", ["id"], unique=False)
    op.create_index(op.f("ix_dead_letter_events_source"), "dead_letter_events", ["source"], unique=False)
    op.create_index(op.f("ix_dead_letter_events_created_at"), "dead_letter_events", ["created_at"], unique=False)

    op.create_table(
        "idempotency_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=160), nullable=False),
        sa.Column("scope", sa.String(length=80), nullable=False),
        sa.Column("response", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index(op.f("ix_idempotency_records_id"), "idempotency_records", ["id"], unique=False)
    op.create_index(op.f("ix_idempotency_records_key"), "idempotency_records", ["key"], unique=True)
    op.create_index(op.f("ix_idempotency_records_scope"), "idempotency_records", ["scope"], unique=False)
    op.create_index(
        op.f("ix_idempotency_records_created_at"),
        "idempotency_records",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    for index_name, table_name in (
        (op.f("ix_idempotency_records_created_at"), "idempotency_records"),
        (op.f("ix_idempotency_records_scope"), "idempotency_records"),
        (op.f("ix_idempotency_records_key"), "idempotency_records"),
        (op.f("ix_idempotency_records_id"), "idempotency_records"),
    ):
        op.drop_index(index_name, table_name=table_name)
    op.drop_table("idempotency_records")

    for index_name, table_name in (
        (op.f("ix_dead_letter_events_created_at"), "dead_letter_events"),
        (op.f("ix_dead_letter_events_source"), "dead_letter_events"),
        (op.f("ix_dead_letter_events_id"), "dead_letter_events"),
    ):
        op.drop_index(index_name, table_name=table_name)
    op.drop_table("dead_letter_events")

    for index_name, table_name in (
        (op.f("ix_wargame_events_created_at"), "wargame_events"),
        (op.f("ix_wargame_events_actor"), "wargame_events"),
        (op.f("ix_wargame_events_session_id"), "wargame_events"),
        (op.f("ix_wargame_events_id"), "wargame_events"),
    ):
        op.drop_index(index_name, table_name=table_name)
    op.drop_table("wargame_events")

    op.drop_index(op.f("ix_wargame_sessions_started_at"), table_name="wargame_sessions")
    op.drop_index(op.f("ix_wargame_sessions_id"), table_name="wargame_sessions")
    op.drop_table("wargame_sessions")

    op.drop_index(op.f("ix_backtest_results_created_at"), table_name="backtest_results")
    op.drop_index(op.f("ix_backtest_results_scenario"), table_name="backtest_results")
    op.drop_index(op.f("ix_backtest_results_id"), table_name="backtest_results")
    op.drop_table("backtest_results")

    op.drop_index(op.f("ix_what_if_simulations_created_at"), table_name="what_if_simulations")
    op.drop_index(op.f("ix_what_if_simulations_shipment_key"), table_name="what_if_simulations")
    op.drop_index(op.f("ix_what_if_simulations_id"), table_name="what_if_simulations")
    op.drop_table("what_if_simulations")

    op.drop_index(op.f("ix_copilot_interactions_created_at"), table_name="copilot_interactions")
    op.drop_index(op.f("ix_copilot_interactions_shipment_key"), table_name="copilot_interactions")
    op.drop_index(op.f("ix_copilot_interactions_id"), table_name="copilot_interactions")
    op.drop_table("copilot_interactions")

    op.drop_index(op.f("ix_notification_records_created_at"), table_name="notification_records")
    op.drop_index(op.f("ix_notification_records_shipment_key"), table_name="notification_records")
    op.drop_index(op.f("ix_notification_records_id"), table_name="notification_records")
    op.drop_table("notification_records")

    op.drop_index(op.f("ix_agent_actions_executed_at"), table_name="agent_actions")
    op.drop_index(op.f("ix_agent_actions_action_type"), table_name="agent_actions")
    op.drop_index(op.f("ix_agent_actions_shipment_key"), table_name="agent_actions")
    op.drop_index(op.f("ix_agent_actions_id"), table_name="agent_actions")
    op.drop_table("agent_actions")

    op.drop_index(op.f("ix_agent_overrides_shipment_key"), table_name="agent_overrides")
    op.drop_index(op.f("ix_agent_overrides_id"), table_name="agent_overrides")
    op.drop_table("agent_overrides")

    op.drop_index(op.f("ix_routes_created_at"), table_name="routes")
    op.drop_index(op.f("ix_routes_shipment_key"), table_name="routes")
    op.drop_index(op.f("ix_routes_id"), table_name="routes")
    op.drop_table("routes")
