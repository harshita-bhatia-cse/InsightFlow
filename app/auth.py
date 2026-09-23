from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.database.models import User

APP_SECRET_KEY = os.getenv("APP_SECRET_KEY", "insightflow-dev-secret-key")


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200000)
    return f"pbkdf2_sha256$200000${salt.hex()}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = password_hash.split("$")
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(digest_hex)
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
    return hmac.compare_digest(actual, expected)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def create_access_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "exp": int(time.time()) + 86400,
    }
    payload_json = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    encoded_payload = _b64url_encode(payload_json)
    signing_input = encoded_payload.encode("utf-8")
    signature = hmac.new(APP_SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{encoded_payload}.{_b64url_encode(signature)}"


def verify_token(token: str) -> dict[str, Any]:
    try:
        payload_part, signature_part = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid token format.") from exc

    signing_input = payload_part.encode("utf-8")
    expected = _b64url_encode(
        hmac.new(APP_SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    )

    if not hmac.compare_digest(signature_part, expected):
        raise HTTPException(status_code=401, detail="Token signature is invalid.")

    try:
        payload = json.loads(_b64url_decode(payload_part).decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=401, detail="Token payload is invalid.") from exc

    if payload.get("exp", 0) < int(time.time()):
        raise HTTPException(status_code=401, detail="Token has expired.")

    return payload


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.query(User).filter(User.email == email).one_or_none()


def get_user_by_id(session: Session, user_id: int) -> User | None:
    return session.get(User, user_id)


def register_user(email: str, username: str, password: str, role: str = "viewer") -> User:
    session = SessionLocal()
    try:
        email = email.strip().lower()
        username = username.strip()

        if not email or not username or not password:
            raise HTTPException(status_code=400, detail="Email, username, and password are required.")
        if get_user_by_email(session, email) is not None:
            raise HTTPException(status_code=409, detail="A user with this email already exists.")

        if role not in {"admin", "analyst", "viewer", "uploader"}:
            raise HTTPException(status_code=400, detail="Unsupported role.")

        user = User(
            email=email,
            username=username,
            password_hash=hash_password(password),
            role=role,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    finally:
        session.close()


def authenticate_user(email: str, password: str) -> User | None:
    session = SessionLocal()
    try:
        user = get_user_by_email(session, email.strip().lower())
        if user is None:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
    finally:
        session.close()


def get_current_user_from_token(token: str) -> User:
    payload = verify_token(token)
    session = SessionLocal()
    try:
        user = session.get(User, int(payload["sub"]))
        if user is None:
            raise HTTPException(status_code=401, detail="User not found.")
        return user
    finally:
        session.close()


def require_roles(*roles: str):
    def dependency(authorization: str | None = Header(default=None)):
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = authorization.split(" ", 1)[1]
        user = get_current_user_from_token(token)

        if roles and user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )

        return user

    return dependency
