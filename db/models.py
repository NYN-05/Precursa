from datetime import datetime

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
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="joined",
    )


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    users: Mapped[list[User]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles",
    )


class IngestionEvent(Base):
    __tablename__ = "ingestion_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_event_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    dedupe_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entity_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    severity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)


class ShipmentSnapshot(Base):
    __tablename__ = "shipment_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    shipment_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    latest_event_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("ingestion_events.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    last_source: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    last_event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    last_entity_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_severity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    last_severity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    last_occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    provisional_dri: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    feature_vector: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
    )
