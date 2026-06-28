from __future__ import annotations

import migrate as migrate_module

from app.repositories.queries import build_connect_args as build_runtime_connect_args


def test_runtime_connect_args_disable_prepared_statements_for_postgres() -> None:
    connect_args = build_runtime_connect_args(
        "postgresql+psycopg://user:pass@aws-1-us-east-1.pooler.supabase.com:6543/dbname"
    )

    assert connect_args == {
        "connect_timeout": 10,
        "prepare_threshold": None,
    }


def test_migration_connect_args_disable_prepared_statements_for_postgres() -> None:
    connect_args = migrate_module.build_connect_args(
        "postgresql+psycopg://user:pass@aws-1-us-east-1.pooler.supabase.com:6543/dbname"
    )

    assert connect_args == {
        "connect_timeout": 10,
        "prepare_threshold": None,
    }


def test_sqlite_connect_args_remain_unchanged() -> None:
    connect_args = build_runtime_connect_args("sqlite+pysqlite:///:memory:")

    assert connect_args == {"check_same_thread": False}
