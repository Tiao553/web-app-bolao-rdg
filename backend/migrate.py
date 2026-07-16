"""
Applies the database schema using SQLAlchemy metadata (idempotent).
Runs before the server starts in production.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.orm import Session
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

    # Backfill the independently managed third-place phase for databases created
    # before it was added to the canonical phase schedule.
    from app.models.schema import CompetitionPhase, CompetitionPhaseConfig

    third_place_starts_at = datetime.fromisoformat("2026-07-18T19:00:00+00:00")
    with Session(engine) as session:
        final_config = session.scalar(
            select(CompetitionPhaseConfig).where(
                CompetitionPhaseConfig.phase_key == "final"
            )
        )
        if final_config is not None and final_config.sort_order == 8:
            final_config.sort_order = 9
            session.flush()

        third_place_config = session.scalar(
            select(CompetitionPhaseConfig).where(
                CompetitionPhaseConfig.phase_key == "thirdPlace"
            )
        )
        if third_place_config is None:
            session.add(
                CompetitionPhaseConfig(
                    phase_key="thirdPlace",
                    label="3º lugar",
                    phase=CompetitionPhase.THIRD_PLACE,
                    stage_round=None,
                    sort_order=8,
                    first_match_starts_at=third_place_starts_at,
                    lock_at=third_place_starts_at - timedelta(minutes=30),
                    explore_at=third_place_starts_at - timedelta(minutes=30),
                    is_force_locked=False,
                    is_active=True,
                )
            )

        session.commit()

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
