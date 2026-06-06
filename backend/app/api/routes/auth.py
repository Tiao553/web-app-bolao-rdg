from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.security import (
    attach_session_cookie,
    build_auth_error,
    clear_session_cookie,
    create_user_session,
    is_secure_cookie_enabled,
    hash_password,
    hash_session_token,
    read_session_token_from_request,
    revoke_user_session,
    verify_password,
)
from app.models.schema import AccessStatus, PasswordResetToken, User, UserSession
from app.repositories.queries import (
    CompetitionWindowSnapshot,
    get_active_competition_window,
    get_active_db_session_by_token_hash,
    get_db_session,
    get_user_by_email,
)
from app.services.email_service import EmailService

router = APIRouter(prefix="/api/auth", tags=["auth"])


class AuthUserResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    email: str
    name: str
    accessStatus: AccessStatus
    isAdmin: bool
    lastLoginAt: datetime | None


class CompetitionWindowPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    predictionCloseAt: datetime
    exploreReleaseAt: datetime


class SessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    authenticated: bool
    user: AuthUserResponse | None
    competition: CompetitionWindowPayload
    now: datetime


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=255)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str = Field(min_length=8, max_length=255)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def build_user_response(user: User) -> AuthUserResponse:
    return AuthUserResponse(
        id=user.id,
        email=user.email,
        name=user.full_name,
        accessStatus=user.access_status,
        isAdmin=user.is_admin,
        lastLoginAt=user.last_login_at,
    )


def build_competition_payload(
    competition_window: CompetitionWindowSnapshot,
) -> CompetitionWindowPayload:
    return CompetitionWindowPayload(
        predictionCloseAt=competition_window.prediction_close_at,
        exploreReleaseAt=competition_window.explore_release_at,
    )


def build_session_response(
    competition_window: CompetitionWindowSnapshot,
    *,
    user: User | None,
) -> SessionResponse:
    return SessionResponse(
        authenticated=user is not None,
        user=build_user_response(user) if user is not None else None,
        competition=build_competition_payload(competition_window),
        now=utc_now(),
    )
async def parse_register_request(request: Request) -> RegisterRequest:
    payload = await _read_request_payload(request)
    full_name = _extract_text(payload, "full_name") or _extract_text(payload, "name")
    if full_name is None:
        raise build_auth_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="missing_name",
            message="Name is required",
        )
    return RegisterRequest(
        email=_extract_text(payload, "email") or "",
        full_name=full_name,
        password=_extract_text(payload, "password") or "",
    )


async def parse_login_request(request: Request) -> LoginRequest:
    payload = await _read_request_payload(request)
    return LoginRequest(
        email=_extract_text(payload, "email") or "",
        password=_extract_text(payload, "password") or "",
    )


async def _read_request_payload(request: Request) -> dict[str, Any]:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = await request.json()
        if isinstance(payload, dict):
            return payload
    form = await request.form()
    return {key: value for key, value in form.items()}


def _extract_text(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if isinstance(value, str):
        normalized = value.strip()
        return normalized or None
    return None


def resolve_current_user(
    request: Request,
    db_session: Session,
) -> User | None:
    token = read_session_token_from_request(request)
    if token is None:
        return None
    token_hash = hash_session_token(token)
    db_user_session = get_active_db_session_by_token_hash(db_session, token_hash)
    if db_user_session is None:
        return None
    db_user_session.last_seen_at = utc_now()
    db_session.add(db_user_session)
    db_session.flush()
    return db_user_session.user


@router.post(
    "/register",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: Request,
    response: Response,
    db_session: Session = Depends(get_db_session),
) -> SessionResponse:
    payload = await parse_register_request(request)
    normalized_email = normalize_email(str(payload.email))
    existing_user = get_user_by_email(db_session, normalized_email)
    if existing_user is not None:
        raise build_auth_error(
            status_code=status.HTTP_409_CONFLICT,
            code="email_already_registered",
            message="A user with this email already exists",
        )

    user = User(
        email=normalized_email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        access_status=AccessStatus.PENDING,
        is_admin=False,
    )
    db_session.add(user)
    db_session.flush()

    user_session, raw_token = create_user_session(db_session, user)
    attach_session_cookie(
        response,
        raw_token,
        expires_at=user_session.expires_at,
        secure=is_secure_cookie_enabled(),
    )
    competition_window = get_active_competition_window(db_session)
    return build_session_response(competition_window, user=user)


@router.post(
    "/login",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
)
async def login(
    request: Request,
    response: Response,
    db_session: Session = Depends(get_db_session),
) -> SessionResponse:
    payload = await parse_login_request(request)
    normalized_email = normalize_email(str(payload.email))
    user = get_user_by_email(db_session, normalized_email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise build_auth_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_credentials",
            message="Invalid email or password",
        )
    if not user.is_active:
        raise build_auth_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="user_inactive",
            message="User account is inactive",
        )

    user.last_login_at = utc_now()
    db_session.add(user)
    db_session.flush()

    user_session, raw_token = create_user_session(db_session, user)
    attach_session_cookie(
        response,
        raw_token,
        expires_at=user_session.expires_at,
        secure=is_secure_cookie_enabled(),
    )
    competition_window = get_active_competition_window(db_session)
    return build_session_response(competition_window, user=user)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    request: Request,
    response: Response,
    db_session: Session = Depends(get_db_session),
) -> Response:
    token = read_session_token_from_request(request)
    if token is not None:
        token_hash = hash_session_token(token)
        db_user_session = get_active_db_session_by_token_hash(db_session, token_hash)
        if db_user_session is not None:
            revoke_user_session(db_session, db_user_session)
    clear_session_cookie(response)
    return response


@router.get(
    "/session",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
)
def get_session(
    request: Request,
    db_session: Session = Depends(get_db_session),
) -> SessionResponse:
    user = resolve_current_user(request, db_session)
    competition_window = get_active_competition_window(db_session)
    return build_session_response(competition_window, user=user)


# ── Password Reset ─────────────────────────────────────────────────────────────

RESET_TOKEN_TTL = timedelta(hours=1)


class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str


class ForgotPasswordResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=1)
    password: str = Field(min_length=8, max_length=255)


class ResetPasswordResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    status_code=status.HTTP_200_OK,
)
async def forgot_password(
    request: Request,
    db_session: Session = Depends(get_db_session),
) -> ForgotPasswordResponse:
    """Solicita recuperação de senha."""
    payload = await _read_request_payload(request)
    email = _extract_text(payload, "email") or ""
    normalized_email = normalize_email(email)

    # Busca usuário (sempre retorna sucesso para não revelar existência)
    user = get_user_by_email(db_session, normalized_email)

    if user is not None and user.is_active:
        # Gera token seguro
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = utc_now() + RESET_TOKEN_TTL

        # Salva no banco
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        db_session.add(reset_token)
        db_session.flush()

        # Envia email
        EmailService().send_password_reset_email(user.email, raw_token)

    # Mensagem genérica para não revelar se email existe
    return ForgotPasswordResponse(
        message="Se o email existir em nossa base, você receberá instruções em instantes."
    )


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    status_code=status.HTTP_200_OK,
)
def reset_password(
    payload: ResetPasswordRequest,
    db_session: Session = Depends(get_db_session),
) -> ResetPasswordResponse:
    """Redefine a senha usando token."""
    token_hash = hashlib.sha256(payload.token.encode()).hexdigest()

    # Busca token válido
    statement = (
        select(PasswordResetToken)
        .where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.expires_at > utc_now(),
            PasswordResetToken.used_at.is_(None),
        )
    )
    reset_token = db_session.scalar(statement)

    if reset_token is None:
        raise build_auth_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="invalid_token",
            message="Token inválido ou expirado",
        )

    # Atualiza senha do usuário
    user = reset_token.user
    user.password_hash = hash_password(payload.password)
    db_session.add(user)

    # Marca token como usado
    reset_token.used_at = utc_now()
    db_session.add(reset_token)

    # Revoga todas as sessões do usuário por segurança
    db_session.execute(
        update(UserSession)
        .where(
            UserSession.user_id == user.id,
            UserSession.revoked_at.is_(None),
        )
        .values(revoked_at=utc_now())
    )

    db_session.flush()

    return ResetPasswordResponse(message="Senha redefinida com sucesso.")
