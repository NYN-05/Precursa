from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import DeadLetterEvent, IdempotencyRecord
from app.services.observability import metrics

T = TypeVar("T")


def run_with_retries(
    db: Session,
    operation: Callable[[], T],
    *,
    source: str,
    operation_name: str,
    payload: dict[str, Any],
    attempts: int = 3,
) -> T:
    last_error: Exception | None = None
    for _attempt in range(1, attempts + 1):
        try:
            return operation()
        except Exception as exc:  # pragma: no cover - tests cover DLQ through explicit failure
            last_error = exc
            metrics.increment("retry_attempts_total")

    dead_letter = DeadLetterEvent(
        source=source,
        operation=operation_name,
        payload=payload,
        error_message=str(last_error) if last_error else "unknown error",
        retry_count=attempts,
        status="open",
    )
    db.add(dead_letter)
    db.flush()
    metrics.increment("dead_letter_events_total")
    if last_error:
        raise last_error
    raise RuntimeError("Operation failed without an exception")


def get_or_create_idempotent_response(
    db: Session,
    key: str,
    scope: str,
    create_response: Callable[[], dict[str, Any]],
) -> tuple[dict[str, Any], bool]:
    existing = db.scalar(select(IdempotencyRecord).where(IdempotencyRecord.key == key))
    if existing is not None:
        return existing.response, False

    response = create_response()
    record = IdempotencyRecord(key=key, scope=scope, response=response)
    db.add(record)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(select(IdempotencyRecord).where(IdempotencyRecord.key == key))
        if existing is not None:
            return existing.response, False
        raise
    return response, True


def list_dead_letters(db: Session, limit: int = 50) -> list[DeadLetterEvent]:
    query = select(DeadLetterEvent).order_by(
        desc(DeadLetterEvent.created_at),
        desc(DeadLetterEvent.id),
    ).limit(limit)
    return list(db.scalars(query).all())
