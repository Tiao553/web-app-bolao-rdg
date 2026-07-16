from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models.schema import Base, CompetitionPhase, CompetitionPhaseConfig
from app.seed.seeder import _seed_phase_configs


def test_phase_config_seed_adds_third_place_once_before_final() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        assert _seed_phase_configs(session) == 10
        session.commit()

        configs = list(
            session.scalars(
                select(CompetitionPhaseConfig).order_by(CompetitionPhaseConfig.sort_order)
            )
        )
        third_place = next(config for config in configs if config.phase_key == "thirdPlace")
        final = next(config for config in configs if config.phase_key == "final")

        assert third_place.label == "3º lugar"
        assert third_place.phase == CompetitionPhase.THIRD_PLACE
        assert third_place.sort_order == 8
        assert third_place.first_match_starts_at is not None
        assert third_place.first_match_starts_at.isoformat() == "2026-07-18T19:00:00"
        assert third_place.lock_at.isoformat() == "2026-07-18T18:30:00"
        assert third_place.explore_at == third_place.lock_at
        assert final.sort_order == 9

        assert _seed_phase_configs(session) == 0
