from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import IngestionEvent
from app.ingestion.mock_adapters import generate_mock_payload
from app.ingestion.normalizer import SUPPORTED_SOURCES, normalize_event


def ingest_event(db: Session, source: str, payload: dict) -> tuple[IngestionEvent, bool]:
    if source not in SUPPORTED_SOURCES:
        raise ValueError(f"Unsupported source: {source}")

    canonical = normalize_event(source, payload)

    existing = db.scalar(select(IngestionEvent).where(IngestionEvent.dedupe_key == canonical.dedupe_key))
    if existing is not None:
        return existing, False

    event = IngestionEvent(
        source=canonical.source,
        source_event_id=canonical.source_event_id,
        dedupe_key=canonical.dedupe_key,
        event_type=canonical.event_type,
        entity_id=canonical.entity_id,
        severity=canonical.severity,
        occurred_at=canonical.occurred_at,
        payload=canonical.payload,
    )
    db.add(event)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(select(IngestionEvent).where(IngestionEvent.dedupe_key == canonical.dedupe_key))
        if existing is None:
            raise
        return existing, False

    db.refresh(event)
    return event, True


def ingest_mock_events(db: Session, source: str, count: int) -> list[tuple[IngestionEvent, bool]]:
    results: list[tuple[IngestionEvent, bool]] = []
    for _ in range(count):
        payload = generate_mock_payload(source)
        results.append(ingest_event(db, source, payload))
    return results


def list_ingestion_events(db: Session, source: str | None, limit: int) -> list[IngestionEvent]:
    query = select(IngestionEvent)
    if source:
        query = query.where(IngestionEvent.source == source)

    query = query.order_by(desc(IngestionEvent.ingested_at)).limit(limit)
    return list(db.scalars(query).all())
