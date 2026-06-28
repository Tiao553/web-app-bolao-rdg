"""
Applies the database schema using SQLAlchemy metadata (idempotent).
Runs before the server starts in production.
"""
from __future__ import annotations

import os
import sys

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import NullPool


def normalize_database_url(database_url: str) -> str:
    database_url = database_url.strip().strip("'\"")
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://") and "+" not in database_url.split("://", 1)[0]:
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


def build_connect_args(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {
        "connect_timeout": 10,
        "prepare_threshold": None,
    }


def run_migrations() -> None:
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        print("ERROR: DATABASE_URL is not set", flush=True)
        sys.exit(1)

    # Delay import so DATABASE_URL is set before settings load
    from app.models.schema import Base

    engine = create_engine(
        normalize_database_url(database_url),
        connect_args=build_connect_args(database_url),
        poolclass=NullPool,
    )

    print("Running schema migration (create_all) …", flush=True)
    with engine.begin() as conn:
        # Create enums explicitly (SQLAlchemy won't create them via create_all
        # when using server_default string values without checkfirst)
        conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE access_status_enum AS ENUM ('PENDING','APPROVED','REJECTED','BLOCKED');
            EXCEPTION WHEN duplicate_object THEN NULL; END $$;

            DO $$ BEGIN
                CREATE TYPE competition_phase_enum AS ENUM (
                    'GROUP_STAGE','ROUND_OF_32','ROUND_OF_16',
                    'QUARTER_FINAL','SEMI_FINAL','THIRD_PLACE','FINAL'
                );
            EXCEPTION WHEN duplicate_object THEN NULL; END $$;

            DO $$ BEGIN
                CREATE TYPE competition_prediction_type_enum AS ENUM ('CHAMPION','TOP_SCORER');
            EXCEPTION WHEN duplicate_object THEN NULL; END $$;

            DO $$ BEGIN
                CREATE TYPE sync_provider_enum AS ENUM (
                    'THE_SPORTS_DB','API_FOOTBALL','GOOGLE_SHEETS','ADMIN','SEED'
                );
            EXCEPTION WHEN duplicate_object THEN NULL; END $$;

            DO $$ BEGIN
                CREATE TYPE sync_log_provider_enum AS ENUM (
                    'THE_SPORTS_DB','API_FOOTBALL','GOOGLE_SHEETS','ADMIN','SEED'
                );
            EXCEPTION WHEN duplicate_object THEN NULL; END $$;

            DO $$ BEGIN
                CREATE TYPE sync_log_status_enum AS ENUM ('SUCCESS','FAILURE','SKIPPED');
            EXCEPTION WHEN duplicate_object THEN NULL; END $$;
        """))

    Base.metadata.create_all(engine, checkfirst=True)

    # Incremental: add is_active column if missing (migration 0002)
    with engine.connect() as conn:
        inspector = inspect(conn)
        cols = [c["name"] for c in inspector.get_columns("users")]
        if "is_active" not in cols:
            print("Applying migration 0002: adding users.is_active …", flush=True)
            with engine.begin() as wconn:
                wconn.execute(text(
                    "ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true"
                ))
                wconn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_users_is_active ON users (is_active)"
                ))

        # competition_windows.force_locked_phases (added later)
        cw_cols = [c["name"] for c in inspector.get_columns("competition_windows")]
        if "force_locked_phases" not in cw_cols:
            print("Applying migration: adding competition_windows.force_locked_phases …", flush=True)
            with engine.begin() as wconn:
                wconn.execute(text(
                    "ALTER TABLE competition_windows ADD COLUMN force_locked_phases INTEGER"
                ))

        if engine.dialect.name == "postgresql":
            with engine.begin() as wconn:
                wconn.execute(text(
                    "ALTER TYPE sync_provider_enum ADD VALUE IF NOT EXISTS 'THE_SPORTS_DB'"
                ))
                wconn.execute(text(
                    "ALTER TYPE sync_log_provider_enum ADD VALUE IF NOT EXISTS 'THE_SPORTS_DB'"
                ))

    print("Schema up to date.", flush=True)


if __name__ == "__main__":
    run_migrations()
