from collections.abc import Callable
from typing import TypedDict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.models import User
from app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/token")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/token", auto_error=False)


class AuthContext(TypedDict):
    username: str
    roles: list[str]


async def get_current_user_context(
    db: Session = Depends(get_db), token: str | None = Depends(oauth2_scheme_optional)
) -> AuthContext:
    if settings.mvp_mode:
        if not token:
            return {"username": "mvp_admin", "roles": ["admin"]}
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_access_token(token)
    username = payload.get("sub")

    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.scalar(
        select(User)
        .options(joinedload(User.roles))
        .where(User.username == username, User.is_active.is_(True))
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive or does not exist",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"username": user.username, "roles": [role.name for role in user.roles]}


def require_roles(*required_roles: str) -> Callable[[AuthContext], AuthContext]:
    required = set(required_roles)

    async def _role_checker(
        context: AuthContext = Depends(get_current_user_context),
    ) -> AuthContext:
        if required.isdisjoint(set(context["roles"])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return context

    return _role_checker
