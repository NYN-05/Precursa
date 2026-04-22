from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.models import Role, User


def _create_user_with_roles(db_session, username: str, password: str, roles: list[str]) -> User:
    role_objs = []
    for role_name in roles:
        role = db_session.scalar(select(Role).where(Role.name == role_name))
        if role is None:
            role = Role(name=role_name)
            db_session.add(role)
            db_session.flush()
        role_objs.append(role)

    user = User(
        username=username,
        hashed_password=get_password_hash(password),
        is_active=True,
    )
    user.roles = role_objs
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_login_and_me_endpoint(client, db_session):
    _create_user_with_roles(db_session, "alice", "secret123", ["ops_analyst"])

    token_response = client.post(
        "/api/v1/auth/token",
        data={"username": "alice", "password": "secret123"},
    )

    assert token_response.status_code == 200
    token = token_response.json()["access_token"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["username"] == "alice"
    assert "ops_analyst" in me_response.json()["roles"]


def test_admin_route_forbidden_for_non_admin(client, db_session):
    _create_user_with_roles(db_session, "bob", "secret123", ["auditor"])

    token_response = client.post(
        "/api/v1/auth/token",
        data={"username": "bob", "password": "secret123"},
    )
    token = token_response.json()["access_token"]

    admin_response = client.get(
        "/api/v1/protected/admin",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert admin_response.status_code == 403


def test_admin_route_allowed_for_admin(client, db_session):
    _create_user_with_roles(db_session, "carol", "secret123", ["admin"])

    token_response = client.post(
        "/api/v1/auth/token",
        data={"username": "carol", "password": "secret123"},
    )
    token = token_response.json()["access_token"]

    admin_response = client.get(
        "/api/v1/protected/admin",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert admin_response.status_code == 200
    assert admin_response.json()["role_check"] == "passed"
