from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    ValidationError,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

TerminalStatus = Literal["FT", "AET", "PEN"]


class AppSectionSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    environment: str
    timezone: str


class ScoringSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exact_points: int = Field(ge=0)
    result_points: int = Field(ge=0)
    brazil_multiplier: int = Field(ge=1)
    champion_points: int = Field(ge=0)
    top_scorer_points: int = Field(ge=0)


class SyncSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    post_match_offset_minutes: int = Field(ge=0)
    allowed_terminal_statuses: tuple[TerminalStatus, ...]
    max_runs_per_day: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_allowed_terminal_statuses(self) -> SyncSettings:
        if len(self.allowed_terminal_statuses) == 0:
            msg = (
                "sync.allowed_terminal_statuses must contain at least one "
                "terminal status"
            )
            raise ValueError(msg)
        if len(set(self.allowed_terminal_statuses)) != len(
            self.allowed_terminal_statuses
        ):
            msg = "sync.allowed_terminal_statuses must not contain duplicates"
            raise ValueError(msg)
        return self


class CompetitionSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    prediction_close_at: datetime = Field(alias="predictionCloseAt")
    explore_release_at: datetime = Field(alias="exploreReleaseAt")

    @model_validator(mode="after")
    def validate_release_window(self) -> CompetitionSettings:
        if self.explore_release_at < self.prediction_close_at:
            msg = (
                "competition.exploreReleaseAt must be greater than or equal to "
                "competition.predictionCloseAt"
            )
            raise ValueError(msg)
        return self


class FileSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app: AppSectionSettings
    scoring: ScoringSettings
    sync: SyncSettings
    competition: CompetitionSettings


class EnvironmentSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    api_football_key: SecretStr | None = Field(default=None, alias="API_FOOTBALL_KEY")
    sync_admin_token: SecretStr | None = Field(default=None, alias="SYNC_ADMIN_TOKEN")

    @model_validator(mode="after")
    def validate_database_url(self) -> EnvironmentSettings:
        if self.database_url is None or self.database_url.strip() == "":
            msg = "DATABASE_URL environment variable is required"
            raise ValueError(msg)
        return self


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app: AppSectionSettings
    scoring: ScoringSettings
    sync: SyncSettings
    competition: CompetitionSettings
    database_url: str
    api_football_key: SecretStr | None
    sync_admin_token: SecretStr | None


def get_config_file_path() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "app-settings.yaml"


def load_yaml_settings(config_path: Path | None = None) -> FileSettings:
    resolved_path = config_path or get_config_file_path()
    raw_content = resolved_path.read_text(encoding="utf-8")
    payload = yaml.safe_load(raw_content) or {}
    if not isinstance(payload, dict):
        msg = (
            f"Invalid YAML structure in {resolved_path}: expected a mapping "
            "at the root"
        )
        raise ValueError(msg)
    return FileSettings.model_validate(payload)


def load_environment_settings() -> EnvironmentSettings:
    try:
        return EnvironmentSettings()
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    file_settings = load_yaml_settings()
    environment_settings = load_environment_settings()
    return Settings(
        app=file_settings.app,
        scoring=file_settings.scoring,
        sync=file_settings.sync,
        competition=file_settings.competition,
        database_url=environment_settings.database_url or "",
        api_football_key=environment_settings.api_football_key,
        sync_admin_token=environment_settings.sync_admin_token,
    )


def print_settings() -> None:
    settings = get_settings()
    print(
        settings.model_dump_json(
            indent=2,
            exclude={"api_football_key", "sync_admin_token"},
        )
    )
