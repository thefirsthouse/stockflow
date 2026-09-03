from datetime import timedelta

import pytest
from jose import jwt
from pydantic import ValidationError

from config import settings
from users.auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    verify_password,
)
from users.models import User
from users.schemas import UserCreateSchema


def test_user_create_schema_validates_email_and_password():
    schema = UserCreateSchema(
        username="alice",
        email="alice@example.com",
        first_name="Alice",
        last_name="Example",
        password="password123",
    )

    assert schema.email == "alice@example.com"


def test_user_create_schema_rejects_invalid_email_and_short_password():
    with pytest.raises(ValidationError):
        UserCreateSchema(
            username="alice",
            email="not-email",
            first_name="Alice",
            last_name="Example",
            password="short",
        )


def test_password_hash_can_be_verified():
    hashed_password = get_password_hash("password123")

    assert hashed_password != "password123"
    assert verify_password("password123", hashed_password)
    assert not verify_password("wrong-password", hashed_password)


def test_create_access_token_contains_subject():
    token = create_access_token({"sub": "alice"}, expires_delta=timedelta(minutes=5))
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

    assert payload["sub"] == "alice"
    assert "exp" in payload


async def test_authenticate_user_returns_user_for_valid_credentials(db_session):
    user = User(
        username="alice",
        email="alice@example.com",
        first_name="Alice",
        last_name="Example",
        hashed_password=get_password_hash("password123"),
    )
    db_session.add(user)
    await db_session.commit()

    authenticated_user = await authenticate_user(db_session, "alice", "password123")

    assert authenticated_user is not None
    assert authenticated_user.username == "alice"


async def test_authenticate_user_returns_none_for_invalid_credentials(db_session):
    user = User(
        username="alice",
        email="alice@example.com",
        first_name="Alice",
        last_name="Example",
        hashed_password=get_password_hash("password123"),
    )
    db_session.add(user)
    await db_session.commit()

    assert await authenticate_user(db_session, "alice", "wrong-password") is None
    assert await authenticate_user(db_session, "unknown", "password123") is None
