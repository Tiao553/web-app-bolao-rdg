from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.member import router as member_router
from app.core.config import Settings, get_settings


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ErrorDetail


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    service: str
    environment: str
    timestamp: datetime


def build_error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    payload = ErrorEnvelope(
        error=ErrorDetail(code=code, message=message, details=details),
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(mode="json"),
    )


def get_cors_origins(settings: Settings) -> list[str]:
    if settings.app.environment == "development":
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    return []


def get_cors_origin_regex(settings: Settings) -> str | None:
    if settings.app.environment == "development":
        return None
    return r"https://.*\.vercel\.app"


def configure_cors(app: FastAPI, settings: Settings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(settings),
        allow_origin_regex=get_cors_origin_regex(settings),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def extract_http_exception_detail(
    exc: HTTPException,
) -> tuple[str, str, dict[str, Any] | None]:
    if isinstance(exc.detail, dict):
        code = str(exc.detail.get("code", "http_error"))
        message = str(exc.detail.get("message", "Request failed"))
        raw_details = exc.detail.get("details")
        details = raw_details if isinstance(raw_details, dict) else None
        return code, message, details
    return "http_error", str(exc.detail), None


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        del request
        code, message, details = extract_http_exception_detail(exc)
        return build_error_response(
            status_code=exc.status_code,
            code=code,
            message=message,
            details=details,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        del request
        return build_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="validation_error",
            message="Request validation failed",
            details={"issues": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        del request
        del exc
        return build_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="internal_server_error",
            message="An unexpected error occurred",
        )


@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.settings = get_settings()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app.name,
        lifespan=app_lifespan,
    )
    configure_cors(app, settings)
    register_exception_handlers(app)
    app.include_router(auth_router)
    app.include_router(member_router)
    app.include_router(admin_router)

    @app.get(
        "/healthz",
        response_model=HealthResponse,
        tags=["system"],
    )
    async def healthz() -> HealthResponse:
        return HealthResponse(
            status="ok",
            service=settings.app.name,
            environment=settings.app.environment,
            timestamp=datetime.now(timezone.utc),
        )

    @app.get(
        "/readyz",
        response_model=HealthResponse,
        tags=["system"],
    )
    async def readyz() -> HealthResponse:
        return HealthResponse(
            status="ready",
            service=settings.app.name,
            environment=settings.app.environment,
            timestamp=datetime.now(timezone.utc),
        )

    return app


app = create_app()
