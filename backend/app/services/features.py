from __future__ import annotations

from datetime import datetime, timezone
from math import log1p
from typing import Any

from app.schemas import AttackType, CandidateEvent, SourceName


FEATURE_SPEC_VERSION = 1

FEATURES: tuple[dict[str, str], ...] = (
    {
        "name": "source_confidence",
        "description": "Confidence reported or inferred directly from the source adapter.",
    },
    {
        "name": "abuse_confidence_score",
        "description": "AbuseIPDB confidence normalized from 0-100 to 0-1.",
    },
    {
        "name": "greynoise_malicious",
        "description": "1 when GreyNoise classifies the IP as malicious.",
    },
    {
        "name": "greynoise_suspicious",
        "description": "1 when GreyNoise classifies the IP as suspicious.",
    },
    {
        "name": "greynoise_benign",
        "description": "1 when GreyNoise classifies the IP as benign.",
    },
    {
        "name": "greynoise_noise",
        "description": "1 when GreyNoise marks the IP as internet background noise.",
    },
    {
        "name": "greynoise_riot",
        "description": "1 when GreyNoise marks the IP as RIOT/common business service.",
    },
    {
        "name": "source_count",
        "description": "Number of independent sources reporting the same candidate.",
    },
    {
        "name": "cloudflare_ddos_trend",
        "description": "1 when Cloudflare Radar indicates a current DDoS trend.",
    },
    {
        "name": "cloudflare_latest_value_log",
        "description": "Log-scaled latest Cloudflare Radar trend bucket.",
    },
    {
        "name": "has_ip",
        "description": "1 when the candidate has a concrete IP address.",
    },
    {
        "name": "has_asn",
        "description": "1 when the candidate includes ASN metadata.",
    },
    {
        "name": "has_country",
        "description": "1 when the candidate includes country metadata.",
    },
    {
        "name": "type_volumetric",
        "description": "One-hot flag for volumetric attack hint.",
    },
    {
        "name": "type_amplification",
        "description": "One-hot flag for amplification attack hint.",
    },
    {
        "name": "type_application",
        "description": "One-hot flag for application-layer attack hint.",
    },
    {
        "name": "type_scanner",
        "description": "One-hot flag for scanner/botnet reconnaissance hint.",
    },
    {
        "name": "source_abuseipdb",
        "description": "One-hot flag for AbuseIPDB candidates.",
    },
    {
        "name": "source_greynoise",
        "description": "One-hot flag for GreyNoise candidates.",
    },
    {
        "name": "source_cloudflare_radar",
        "description": "One-hot flag for Cloudflare Radar candidates.",
    },
    {
        "name": "event_age_minutes",
        "description": "Candidate age in minutes, capped at one day.",
    },
)

DEFAULT_FEATURE_NAMES = tuple(feature["name"] for feature in FEATURES)


def feature_spec() -> dict[str, Any]:
    return {
        "version": FEATURE_SPEC_VERSION,
        "feature_names": list(DEFAULT_FEATURE_NAMES),
        "features": list(FEATURES),
    }


def extract_features(
    candidate: CandidateEvent,
    *,
    as_of: datetime | None = None,
    feature_names: tuple[str, ...] = DEFAULT_FEATURE_NAMES,
) -> list[float]:
    """Return the ordered numeric vector consumed by the runtime scorer.

    Keeping this transformation deterministic is more important than cleverness:
    the same function is used by training, tests, and production inference.
    """

    values = feature_values(candidate, as_of=as_of)
    return [values[name] for name in feature_names]


def feature_values(candidate: CandidateEvent, *, as_of: datetime | None = None) -> dict[str, float]:
    features = candidate.features
    classification = str(features.get("greynoise_classification") or "").lower()
    attack_type = candidate.type_hint or AttackType.UNKNOWN
    now = _ensure_utc(as_of or datetime.now(timezone.utc))
    event_ts = _ensure_utc(candidate.ts)
    age_minutes = max(0.0, min(1440.0, (now - event_ts).total_seconds() / 60.0))

    abuse_score = _number(features.get("abuse_confidence_score"))
    cloudflare_latest = max(0.0, _number(features.get("cloudflare_latest_value")))

    return {
        "source_confidence": _clamp(candidate.source_confidence),
        "abuse_confidence_score": _clamp(abuse_score / 100.0),
        "greynoise_malicious": _flag(classification == "malicious"),
        "greynoise_suspicious": _flag(classification == "suspicious"),
        "greynoise_benign": _flag(classification == "benign"),
        "greynoise_noise": _flag(features.get("greynoise_noise")),
        "greynoise_riot": _flag(features.get("greynoise_riot")),
        "source_count": max(0.0, min(5.0, _number(features.get("source_count")))),
        "cloudflare_ddos_trend": _flag(features.get("cloudflare_ddos_trend")),
        "cloudflare_latest_value_log": log1p(cloudflare_latest),
        "has_ip": _flag(candidate.ip),
        "has_asn": _flag(candidate.asn),
        "has_country": _flag(candidate.country_code or candidate.country),
        "type_volumetric": _flag(attack_type == AttackType.VOLUMETRIC),
        "type_amplification": _flag(attack_type == AttackType.AMPLIFICATION),
        "type_application": _flag(attack_type == AttackType.APPLICATION),
        "type_scanner": _flag(attack_type == AttackType.SCANNER),
        "source_abuseipdb": _flag(candidate.source == SourceName.ABUSEIPDB),
        "source_greynoise": _flag(candidate.source == SourceName.GREYNOISE),
        "source_cloudflare_radar": _flag(candidate.source == SourceName.CLOUDFLARE_RADAR),
        "event_age_minutes": age_minutes,
    }


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _flag(value: Any) -> float:
    return 1.0 if bool(value) else 0.0


def _number(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return 0.0
    return 0.0


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))

