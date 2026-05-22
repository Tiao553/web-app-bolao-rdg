from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Final

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.models.schema import AccessStatus, User, UserSession
from app.repositories.queries import get_active_db_session_by_token_hash, get_db_session

SESSION_COOKIE_NAME: Final[str] = "bolao_session"
SESSION_TTL: Final[timedelta] = timedelta(days=7)
PASSWORD_HASH_ALGORITHM: Final[str] = "scrypt"
SCRYPT_N: Final[int] = 2**14
SCRYPT_R: Final[int] = 8
SCRYPT_P: Final[int] = 1
SCRYPT_SALT_BYTES: Final[int] = 16
SCRYPT_KEY_LENGTH: Final[int] = 64
DB_SESSION_DEPENDENCY = Depends(get_db_session)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_auth_error(
    *,
    status_code: int,
    code: str,
    message: str,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
    )


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(SCRYPT_SALT_BYTES)
    derived_key = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=SCRYPT_KEY_LENGTH,
    )
    salt_b64 = base64.urlsafe_b64encode(salt).decode("utf-8")
    key_b64 = base64.urlsafe_b64encode(derived_key).decode("utf-8")
    return (
        f"{PASSWORD_HASH_ALGORITHM}${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}"
        f"${salt_b64}${key_b64}"
    )


def verify_password(password: str, password_hash: str) -> bool:
    parts = password_hash.split("$")
    if len(parts) != 6:
        return False
    algorithm, n_raw, r_raw, p_raw, salt_b64, key_b64 = parts
    if algorithm != PASSWORD_HASH_ALGORITHM:
        return False
    try:
        salt = base64.urlsafe_b64decode(salt_b64.encode("utf-8"))
        expected_key = base64.urlsafe_b64decode(key_b64.encode("utf-8"))
        derived_key = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=int(n_raw),
            r=int(r_raw),
            p=int(p_raw),
            dklen=len(expected_key),
        )
    except (TypeError, ValueError):
        return False
    return hmac.compare_digest(derived_key, expected_key)


def create_session_token() -> str:
    return secrets.token_urlsafe(48)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_user_session(
    db_session: Session,
    user: User,
    *,
    ttl: timedelta = SESSION_TTL,
) -> tuple[UserSession, str]:
    raw_token = create_session_token()
    expires_at = utc_now() + ttl
    user_session = UserSession(
        user_id=user.id,
        token_hash=hash_session_token(raw_token),
        expires_at=expires_at,
    )
    db_session.add(user_session)
    db_session.flush()
    return user_session, raw_token


def attach_session_cookie(
    response: Response,
    token: str,
    *,
    expires_at: datetime,
    secure: bool,
) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=secure,
        samesite="lax",
        expires=expires_at,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
    )


def read_session_token_from_request(request: Request) -> str | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token is None or token.strip() == "":
        return None
    return token


def revoke_user_session(
    db_session: Session,
    user_session: UserSession,
    *,
    revoked_at: datetime | None = None,
) -> UserSession:
    user_session.revoked_at = revoked_at or utc_now()
    db_session.add(user_session)
    db_session.flush()
    return user_session


def get_current_user(
    request: Request,
    db_session: Session = DB_SESSION_DEPENDENCY,
) -> User:
    token = read_session_token_from_request(request)
    if token is None:
        raise build_auth_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="authentication_required",
            message="Authentication is required",
        )
    token_hash = hash_session_token(token)
    db_user_session = get_active_db_session_by_token_hash(db_session, token_hash)
    if db_user_session is None:
        raise build_auth_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_session",
            message="Session is invalid or expired",
        )
    db_user_session.last_seen_at = utc_now()
    db_session.add(db_user_session)
    db_session.flush()
    return db_user_session.user


CURRENT_USER_DEPENDENCY = Depends(get_current_user)


def require_authenticated_user(user: User = CURRENT_USER_DEPENDENCY) -> User:
    return user


def require_approved_user(user: User = CURRENT_USER_DEPENDENCY) -> User:
    if user.access_status is not AccessStatus.APPROVED:
        raise build_auth_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="user_not_approved",
            message="User is not approved for competition access",
        )
    return user


def require_admin_user(user: User = CURRENT_USER_DEPENDENCY) -> User:
    if not user.is_admin:
        raise build_auth_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="admin_required",
            message="Administrator access is required",
        )
    return user


def can_access_competition(user: User) -> bool:
    return user.access_status is AccessStatus.APPROVED
