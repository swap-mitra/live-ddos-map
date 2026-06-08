import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.schemas import AttackType, CandidateEvent, SourceName
from app.services.features import DEFAULT_FEATURE_NAMES, extract_features, feature_values


def test_extract_features_uses_documented_order():
    as_of = datetime(2026, 6, 8, 12, 0, tzinfo=timezone.utc)
    candidate = CandidateEvent(
        ip="8.8.8.8",
        source=SourceName.ABUSEIPDB,
        type_hint=AttackType.SCANNER,
        source_confidence=0.7,
        country_code="US",
        asn="AS15169",
        features={
            "abuse_confidence_score": 80,
            "source_count": 3,
            "greynoise_classification": "malicious",
            "greynoise_noise": True,
        },
        ts=as_of - timedelta(minutes=15),
    )

    values = feature_values(candidate, as_of=as_of)
    vector = extract_features(candidate, as_of=as_of)

    assert len(vector) == len(DEFAULT_FEATURE_NAMES)
    assert vector[0] == values[DEFAULT_FEATURE_NAMES[0]]
    assert values["abuse_confidence_score"] == 0.8
    assert values["greynoise_malicious"] == 1.0
    assert values["source_count"] == 3.0
    assert values["event_age_minutes"] == 15.0


def test_extract_features_defaults_missing_optional_values_to_zero():
    values = feature_values(CandidateEvent(source=SourceName.SYNTHETIC))

    assert values["abuse_confidence_score"] == 0.0
    assert values["greynoise_malicious"] == 0.0
    assert values["has_ip"] == 0.0


def test_feature_artifact_matches_code_feature_order():
    features_path = Path(__file__).resolve().parents[1] / "app" / "ml" / "features.json"
    payload = json.loads(features_path.read_text(encoding="utf-8"))

    assert payload["feature_names"] == list(DEFAULT_FEATURE_NAMES)
