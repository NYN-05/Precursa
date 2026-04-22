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
