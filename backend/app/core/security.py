from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import threading
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from typing import Final

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.schema import AccessStatus, User, UserSession
from app.repositories.queries import get_active_db_session_by_token_hash, get_db_session

SESSION_COOKIE_NAME: Final[str] = "bolao_session"
CSRF_COOKIE_NAME: Final[str] = "bolao_csrf"
CSRF_HEADER_NAME: Final[str] = "x-csrf-token"
SESSION_TTL: Final[timedelta] = timedelta(days=7)
PASSWORD_HASH_ALGORITHM: Final[str] = "scrypt"
SCRYPT_N: Final[int] = 2**14
SCRYPT_R: Final[int] = 8
SCRYPT_P: Final[int] = 1
SCRYPT_SALT_BYTES: Final[int] = 16
SCRYPT_KEY_LENGTH: Final[int] = 64
DB_SESSION_DEPENDENCY = Depends(get_db_session)
_RATE_LIMIT_BUCKETS: dict[str, list[float]] = {}
_RATE_LIMIT_LOCK = threading.Lock()


def is_secure_cookie_enabled() -> bool:
    settings = get_settings()
    return settings.app.environment != "development"


def get_cookie_domain() -> str | None:
    settings = get_settings()
    if settings.session_cookie_domain is None:
        return None
    normalized = settings.session_cookie_domain.strip()
    return normalized or None


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
        domain=get_cookie_domain(),
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
        secure=is_secure_cookie_enabled(),
        domain=get_cookie_domain(),
    )


def ensure_csrf_cookie(response: Response) -> str:
    csrf_token = create_csrf_token()
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=is_secure_cookie_enabled(),
        samesite="lax",
        path="/",
        domain=get_cookie_domain(),
    )
    return csrf_token


def create_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def read_csrf_token_from_request(request: Request) -> str | None:
    token = request.cookies.get(CSRF_COOKIE_NAME)
    if token is None or token.strip() == "":
        return None
    return token


async def read_submitted_csrf_token(request: Request) -> str | None:
    header_token = request.headers.get(CSRF_HEADER_NAME)
    if header_token is not None and header_token.strip() != "":
        return header_token.strip()

    content_type = request.headers.get("content-type", "").lower()
    if (
        "application/x-www-form-urlencoded" in content_type
        or "multipart/form-data" in content_type
    ):
        form = await request.form()
        raw_value = form.get("csrf_token")
        if isinstance(raw_value, str):
            normalized = raw_value.strip()
            return normalized or None
    return None


def is_csrf_protected_request(request: Request) -> bool:
    if request.method.upper() not in {"POST", "PUT", "PATCH", "DELETE"}:
        return False
    path = request.url.path
    if path.startswith("/api/admin/"):
        return True
    if path.startswith("/api/auth/"):
        return path != "/api/auth/session"
    return path.startswith("/api/member/predictions/")


async def validate_csrf_request(request: Request) -> None:
    cookie_token = read_csrf_token_from_request(request)
    submitted_token = await read_submitted_csrf_token(request)
    if cookie_token is None or submitted_token is None:
        raise build_auth_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="csrf_token_missing",
            message="CSRF token is required",
        )
    if not hmac.compare_digest(cookie_token, submitted_token):
        raise build_auth_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="csrf_token_invalid",
            message="CSRF token is invalid",
        )

    if not is_trusted_origin(request):
        raise build_auth_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="untrusted_origin",
            message="Request origin is not allowed",
        )


def build_allowed_origins(settings: Settings) -> set[str]:
    origins = {
        origin.strip().rstrip("/")
        for origin in settings.frontend_origins
        if origin.strip() != ""
    }
    if settings.app.environment == "development":
        origins.update(
            {
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            }
        )
    return origins


def is_trusted_origin(request: Request) -> bool:
    settings = get_settings()
    allowed_origins = build_allowed_origins(settings)
    origin = request.headers.get("origin")
    referer = request.headers.get("referer")

    if origin is None and referer is None:
        return True

    candidate = origin or referer or ""
    parsed = urlparse(candidate)
    if parsed.scheme == "" or parsed.netloc == "":
        return False
    request_origin = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    return request_origin in allowed_origins


def resolve_rate_limit_bucket(request: Request) -> tuple[str, int, int] | None:
    path = request.url.path
    if request.method.upper() == "POST" and path == "/api/auth/login":
        return ("auth-login", 60, 10)
    if request.method.upper() == "POST" and path == "/api/auth/register":
        return ("auth-register", 300, 5)
    if request.method.upper() == "POST" and path.endswith("/reset-password"):
        return ("admin-reset-password", 600, 5)
    if request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"} and path.startswith("/api/admin/"):
        return ("admin-mutations", 60, 60)
    return None


def enforce_rate_limit(request: Request) -> None:
    bucket_config = resolve_rate_limit_bucket(request)
    if bucket_config is None:
        return

    bucket_name, window_seconds, max_requests = bucket_config
    client_ip = request.client.host if request.client is not None else "unknown"
    key = f"{bucket_name}:{client_ip}"
    now = datetime.now(timezone.utc).timestamp()
    cutoff = now - float(window_seconds)

    with _RATE_LIMIT_LOCK:
        hits = [timestamp for timestamp in _RATE_LIMIT_BUCKETS.get(key, []) if timestamp >= cutoff]
        if len(hits) >= max_requests:
            _RATE_LIMIT_BUCKETS[key] = hits
            raise build_auth_error(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                code="rate_limit_exceeded",
                message="Too many requests",
            )
        hits.append(now)
        _RATE_LIMIT_BUCKETS[key] = hits


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
    if not user.is_active:
        raise build_auth_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="user_inactive",
            message="User account is inactive",
        )
    return user


def require_approved_user(user: User = CURRENT_USER_DEPENDENCY) -> User:
    if not user.is_active:
        raise build_auth_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="user_inactive",
            message="User account is inactive",
        )
    if user.access_status is not AccessStatus.APPROVED:
        raise build_auth_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="user_not_approved",
            message="User is not approved for competition access",
        )
    return user


def require_admin_user(user: User = CURRENT_USER_DEPENDENCY) -> User:
    if not user.is_active:
        raise build_auth_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="user_inactive",
            message="User account is inactive",
        )
    if not user.is_admin:
        raise build_auth_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="admin_required",
            message="Administrator access is required",
        )
    return user


def can_access_competition(user: User) -> bool:
    return user.is_active and user.access_status is AccessStatus.APPROVED
