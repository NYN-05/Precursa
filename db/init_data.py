from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from db.models import Role, User


def seed_default_roles_and_admin(db: Session) -> None:
    existing_roles = {role.name for role in db.scalars(select(Role)).all()}

    for role_name in settings.allowed_roles:
        if role_name not in existing_roles:
            db.add(Role(name=role_name))

    db.flush()

    admin_user = db.scalar(select(User).where(User.username == settings.default_admin_username))
    if admin_user is None:
        admin_user = User(
            username=settings.default_admin_username,
            hashed_password=get_password_hash(settings.default_admin_password),
            is_active=True,
        )
        admin_user.roles = db.scalars(select(Role)).all()
        db.add(admin_user)

    db.commit()
