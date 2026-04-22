# ruff: noqa: E501
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    users: Mapped[list[User]] = relationship(
        secondary=user_roles,
        back_populates="roles",
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    roles: Mapped[list[Role]] = relationship(
        secondary=user_roles,
        back_populates="users",
    )


class IngestionEvent(Base):
    __tablename__ = "ingestion_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    source_event_id: Mapped[str | None] = mapped_column(String(128), index=True)
    dedupe_key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(128), index=True)
    severity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class ShipmentSnapshot(Base):
    __tablename__ = "shipment_snapshots"
    __table_args__ = (UniqueConstraint("shipment_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    shipment_key: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    latest_event_id: Mapped[int | None] = mapped_column(
        ForeignKey("ingestion_events.id", ondelete="SET NULL"),
        index=True,
    )
    last_source: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    last_event_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    last_entity_id: Mapped[str | None] = mapped_column(String(128), index=True)
    event_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_severity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_severity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    provisional_dri: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    feature_vector: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        index=True,
    )

    latest_event: Mapped[IngestionEvent | None] = relationship()


class RouteRecord(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    shipment_key: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    path: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    waypoints: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False)
    eta_hours: Mapped[float] = mapped_column(Float, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    carbon_kg: Mapped[float] = mapped_column(Float, nullable=False)
    tariff_delta_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    policy_penalty_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    composite_score: Mapped[float] = mapped_column(Float, nullable=False)
    lp_score: Mapped[float] = mapped_column(Float, nullable=False)
    constraints_applied: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    solver_status: Mapped[str] = mapped_column(String(50), nullable=False)
    selected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class AgentOverride(Base):
    __tablename__ = "agent_overrides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    shipment_key: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by: Mapped[str] = mapped_column(String(80), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class AgentAction(Base):
    __tablename__ = "agent_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    shipment_key: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    dri_at_action: Mapped[int] = mapped_column(Integer, nullable=False)
    route_selected_id: Mapped[int | None] = mapped_column(ForeignKey("routes.id", ondelete="SET NULL"))
    shap_top_factor: Mapped[str | None] = mapped_column(String(100))
    lp_constraints_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    roi_defended_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    approval_status: Mapped[str] = mapped_column(String(40), default="auto_approved", nullable=False)
    overridden_by_ops: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    replay_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    state_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

    selected_route: Mapped[RouteRecord | None] = relationship()


class NotificationRecord(Base):
    __tablename__ = "notification_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    shipment_key: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    recipient: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="sent", nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class CopilotInteraction(Base):
    __tablename__ = "copilot_interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    shipment_key: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    grounded_on: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    shap_factors_used: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    route_constraints_used: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class WhatIfSimulation(Base):
    __tablename__ = "what_if_simulations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    shipment_key: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    scenario: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    projected_dri: Mapped[int] = mapped_column(Integer, nullable=False)
    projected_routes: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    scenario: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    flag_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    grounding_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    industry_response_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    precursa_lead_minutes: Mapped[float | None] = mapped_column(Float)
    timeline: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class WargameSession(Base):
    __tablename__ = "wargame_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    disturber_events_fired: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    healer_actions_taken: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_roi_defended_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="running", nullable=False)

    events: Mapped[list[WargameEvent]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class WargameEvent(Base):
    __tablename__ = "wargame_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("wargame_sessions.id", ondelete="CASCADE"), index=True)
    actor: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    affected_port: Mapped[str | None] = mapped_column(String(80))
    severity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    affected_shipment_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    potential_loss_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    roi_defended_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

    session: Mapped[WargameSession] = relationship(back_populates="events")


class DeadLetterEvent(Base):
    __tablename__ = "dead_letter_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    operation: Mapped[str] = mapped_column(String(120), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    scope: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    response: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
