from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.models import Role, User


def seed_default_roles_and_admin(db: Session) -> None:
    roles_by_name: dict[str, Role] = {}
    for role_name in settings.allowed_roles:
        role = db.scalar(select(Role).where(Role.name == role_name))
        if role is None:
            role = Role(name=role_name)
            db.add(role)
            db.flush()
        roles_by_name[role_name] = role

    admin = db.scalar(select(User).where(User.username == settings.default_admin_username))
    if admin is None:
        admin = User(
            username=settings.default_admin_username,
            hashed_password=get_password_hash(settings.default_admin_password),
            is_active=True,
        )
        db.add(admin)

    admin.roles = [roles_by_name["admin"]]
    db.commit()

    seed_shipments(db)


def seed_shipments(db: Session) -> None:
    from app.db.models import ShipmentSnapshot
    from datetime import datetime, timezone
    from app.services.feature_state import cache_shipment_snapshot

    shipments = [
        ("SHIP-001", "Mumbai", "Rotterdam", "pharma"),
        ("SHIP-002", "Shanghai", "Los Angeles", "ecommerce"),
        ("SHIP-003", "Singapore", "Hamburg", "general"),
        ("SHIP-004", "Chennai", "Felixstowe", "cold_chain"),
        ("SHIP-005", "Jebel Ali", "Antwerp", "fmcg"),
        ("SHIP-006", "Colombo", "Rotterdam", "pharma"),
        ("SHIP-007", "Busan", "Savannah", "general"),
        ("SHIP-008", "Mumbai", "Singapore", "ecommerce"),
    ]

    for key, origin, dest, cargo in shipments:
        existing = db.query(ShipmentSnapshot).filter(ShipmentSnapshot.shipment_key == key).first()
        if not existing:
            snapshot = ShipmentSnapshot(
                shipment_key=key,
                last_source="initial_seed",
                last_event_type="load",
                event_count=1,
                last_occurred_at=datetime.now(timezone.utc),
                feature_vector={
                    "origin_port": origin,
                    "destination_port": dest,
                    "cargo_type": cargo,
                    "status": "in_transit",
                    "current_route": [origin, dest]
                }
            )
            db.add(snapshot)
            db.flush()
            cache_shipment_snapshot(snapshot)
    
    db.commit()
