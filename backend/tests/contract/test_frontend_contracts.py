from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.models.schema import (
    AccessStatus,
    Base,
    CompetitionPhase,
    CompetitionPrediction,
    CompetitionWindow,
    Match,
    MatchPrediction,
    PredictionType,
    User,
)
from app.services.frontend_contract_service import FrontendContractService


def make_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)
    return factory()


def configure_test_settings() -> None:
    os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    get_settings.cache_clear()


def test_member_contracts_expose_mock_driven_shapes() -> None:
    configure_test_settings()
    db_session = make_session()
    try:
        user = User(
            id=uuid4(),
            email="approved@example.com",
            full_name="Approved User",
            password_hash="hash",
            access_status=AccessStatus.APPROVED,
            is_admin=False,
        )
        db_session.add(user)
        db_session.add(
            CompetitionWindow(
                name="default",
                prediction_close_at=datetime.now(timezone.utc) + timedelta(days=1),
                explore_release_at=datetime.now(timezone.utc) + timedelta(days=2),
                is_active=True,
            )
        )
        match = Match(
            external_provider=None,
            external_id="seed-1",
            phase=CompetitionPhase.GROUP_STAGE,
            group_name="C",
            starts_at=datetime.now(timezone.utc),
            home_team_name="Brazil",
            away_team_name="Japan",
            home_team_fifa_code="BRA",
            away_team_fifa_code="JPN",
            involves_brazil=True,
            status="FT",
            official_home_goals=2,
            official_away_goals=0,
        )
        db_session.add(match)
        db_session.flush()
        db_session.add(
            MatchPrediction(
                user_id=user.id,
                match_id=match.id,
                home_goals=2,
                away_goals=0,
                points_awarded=6,
            )
        )
        db_session.add(
            CompetitionPrediction(
                user_id=user.id,
                prediction_type=PredictionType.CHAMPION,
                selection_key="BRA",
                selection_label="Brazil",
                points_awarded=10,
            )
        )
        db_session.commit()
        service = FrontendContractService(db_session)
        results = service.build_member_results(user=user)
        bracket = service.build_member_bracket(user=user)
        assert results.summary.totalPoints == 16
        assert results.matches[0].homeTeam == "Brasil"
        assert results.matches[0].homeFlag == "🇧🇷"
        assert bracket.championPrediction == "Brazil"
        assert len(bracket.thirdPlaceSlots) == 8
    finally:
        db_session.close()


def test_admin_contracts_expose_screen_summary_shapes() -> None:
    configure_test_settings()
    db_session = make_session()
    try:
        admin = User(
            id=uuid4(),
            email="admin@example.com",
            full_name="Admin User",
            password_hash="hash",
            access_status=AccessStatus.APPROVED,
            is_admin=True,
        )
        db_session.add(admin)
        db_session.add(
            CompetitionWindow(
                name="default",
                prediction_close_at=datetime.now(timezone.utc) + timedelta(days=1),
                explore_release_at=datetime.now(timezone.utc) + timedelta(days=2),
                is_active=True,
            )
        )
        db_session.commit()
        service = FrontendContractService(db_session)
        dashboard = service.build_admin_dashboard()
        integration = service.build_admin_integration()
        settings = service.build_admin_settings()
        assert dashboard.users.total == 1
        assert integration.primaryProvider == "THE_SPORTS_DB"
        assert integration.activeProvider == "THE_SPORTS_DB"
        assert settings.scoring["exact_points"] == 3
    finally:
        db_session.close()
