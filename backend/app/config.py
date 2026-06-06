from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables.

    Defaults are development-friendly. Production should set every secret and
    path explicitly in Railway.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    service_name: str = "live-ddos-map-backend"
    db_path: Path = Field(default=BACKEND_DIR / "data" / "events.db", alias="DDOS_DB_PATH")
    maxmind_db_path: Path | None = Field(default=None, alias="MAXMIND_DB_PATH")
    abuseipdb_key: str | None = Field(default=None, alias="ABUSEIPDB_KEY")
    greynoise_key: str | None = Field(default=None, alias="GREYNOISE_KEY")
    ws_allowed_origins: str = Field(
        default="http://localhost:3000",
        alias="WS_ALLOWED_ORIGINS",
    )
    poll_interval_seconds: int = Field(default=60, ge=10, alias="POLL_INTERVAL_SECONDS")
    event_ttl_hours: int = Field(default=24, ge=1, alias="EVENT_TTL_HOURS")
    min_event_score: float = Field(default=0.5, ge=0.0, le=1.0, alias="MIN_EVENT_SCORE")
    model_path: Path = Field(default=BACKEND_DIR / "app" / "ml" / "model.joblib", alias="MODEL_PATH")
    enable_heuristic_scorer: bool = Field(default=True, alias="ENABLE_HEURISTIC_SCORER")
    enable_scheduler: bool = Field(default=True, alias="ENABLE_SCHEDULER")
    source_timeout_seconds: float = Field(default=10.0, gt=0.0, alias="SOURCE_TIMEOUT_SECONDS")
    abuseipdb_blacklist_limit: int = Field(default=50, ge=1, le=10000, alias="ABUSEIPDB_BLACKLIST_LIMIT")
    greynoise_lookup_limit: int = Field(default=25, ge=0, le=1000, alias="GREYNOISE_LOOKUP_LIMIT")
    target_lat: float = Field(default=37.7749, ge=-90.0, le=90.0, alias="TARGET_LAT")
    target_lng: float = Field(default=-122.4194, ge=-180.0, le=180.0, alias="TARGET_LNG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ws_allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

