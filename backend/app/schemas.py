from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


JsonScalar = str | int | float | bool | None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AttackType(StrEnum):
    VOLUMETRIC = "volumetric"
    AMPLIFICATION = "amplification"
    APPLICATION = "application"
    SCANNER = "scanner"
    UNKNOWN = "unknown"


class SourceName(StrEnum):
    CLOUDFLARE_RADAR = "cloudflare_radar"
    ABUSEIPDB = "abuseipdb"
    GREYNOISE = "greynoise"
    SYNTHETIC = "synthetic"
    COMBINED = "combined"


class CandidateEvent(BaseModel):
    """Common shape returned by source fetchers before scoring and persistence."""

    ip: str | None = None
    lat: float | None = Field(default=None, ge=-90.0, le=90.0)
    lng: float | None = Field(default=None, ge=-180.0, le=180.0)
    country: str | None = None
    country_code: str | None = None
    asn: str | None = None
    source: SourceName
    raw_source_id: str | None = None
    type_hint: AttackType | None = None
    source_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    features: dict[str, JsonScalar] = Field(default_factory=dict)
    ts: datetime = Field(default_factory=utc_now)

    @field_validator("ts")
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class EventCreate(BaseModel):
    ip: str | None = None
    lat: float = Field(ge=-90.0, le=90.0)
    lng: float = Field(ge=-180.0, le=180.0)
    country: str | None = None
    country_code: str | None = None
    asn: str | None = None
    score: float = Field(ge=0.0, le=1.0)
    type: AttackType
    source: SourceName
    raw_source_id: str | None = None
    features: dict[str, JsonScalar] = Field(default_factory=dict)
    ts: datetime = Field(default_factory=utc_now)

    @field_validator("ts")
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class StoredEvent(EventCreate):
    id: int


class AttackEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    ip: str | None = None
    start_lat: float = Field(serialization_alias="startLat")
    start_lng: float = Field(serialization_alias="startLng")
    end_lat: float = Field(serialization_alias="endLat")
    end_lng: float = Field(serialization_alias="endLng")
    country: str | None = None
    country_code: str | None = Field(default=None, serialization_alias="countryCode")
    asn: str | None = None
    score: float
    type: AttackType
    source: SourceName
    ts: datetime


class SnapshotResponse(BaseModel):
    events: list[AttackEvent]


class HealthResponse(BaseModel):
    status: str
    service: str


def event_to_api(event: StoredEvent, *, target_lat: float, target_lng: float) -> AttackEvent:
    return AttackEvent(
        id=event.id,
        ip=event.ip,
        start_lat=event.lat,
        start_lng=event.lng,
        end_lat=target_lat,
        end_lng=target_lng,
        country=event.country,
        country_code=event.country_code,
        asn=event.asn,
        score=event.score,
        type=event.type,
        source=event.source,
        ts=event.ts,
    )


def feature_value(value: Any) -> JsonScalar:
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    return str(value)

