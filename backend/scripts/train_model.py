from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import joblib
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.schemas import AttackType, CandidateEvent, SourceName  # noqa: E402
from app.services.features import DEFAULT_FEATURE_NAMES, extract_features, feature_spec  # noqa: E402


BACKEND_DIR = Path(__file__).resolve().parents[1]
ML_DIR = BACKEND_DIR / "app" / "ml"


def seed_examples() -> list[tuple[CandidateEvent, int]]:
    now = datetime.now(timezone.utc)
    examples: list[tuple[CandidateEvent, int]] = [
        (
            CandidateEvent(
                ip="203.0.113.10",
                source=SourceName.ABUSEIPDB,
                type_hint=AttackType.SCANNER,
                source_confidence=0.95,
                country_code="US",
                asn="AS64500",
                features={"abuse_confidence_score": 95, "source_count": 2},
                ts=now - timedelta(minutes=5),
            ),
            1,
        ),
        (
            CandidateEvent(
                ip="198.51.100.24",
                source=SourceName.GREYNOISE,
                type_hint=AttackType.SCANNER,
                source_confidence=0.85,
                country_code="DE",
                features={
                    "greynoise_classification": "malicious",
                    "greynoise_noise": True,
                    "source_count": 2,
                },
                ts=now - timedelta(minutes=8),
            ),
            1,
        ),
        (
            CandidateEvent(
                source=SourceName.CLOUDFLARE_RADAR,
                type_hint=AttackType.VOLUMETRIC,
                source_confidence=0.7,
                country_code="IN",
                features={"cloudflare_ddos_trend": True, "cloudflare_latest_value": 1200},
                ts=now - timedelta(minutes=3),
            ),
            1,
        ),
        (
            CandidateEvent(
                ip="192.0.2.88",
                source=SourceName.GREYNOISE,
                type_hint=AttackType.UNKNOWN,
                source_confidence=0.15,
                features={"greynoise_classification": "benign", "greynoise_riot": True},
                ts=now - timedelta(minutes=60),
            ),
            0,
        ),
        (
            CandidateEvent(
                ip="192.0.2.11",
                source=SourceName.ABUSEIPDB,
                type_hint=AttackType.UNKNOWN,
                source_confidence=0.1,
                features={"abuse_confidence_score": 5},
                ts=now - timedelta(minutes=90),
            ),
            0,
        ),
        (
            CandidateEvent(
                source=SourceName.CLOUDFLARE_RADAR,
                type_hint=AttackType.UNKNOWN,
                source_confidence=0.2,
                features={"cloudflare_ddos_trend": False, "cloudflare_latest_value": 0},
                ts=now - timedelta(minutes=120),
            ),
            0,
        ),
    ]

    # Duplicate with small confidence variations so the baseline has enough
    # examples for a deterministic train/test split.
    expanded: list[tuple[CandidateEvent, int]] = []
    for candidate, label in examples:
        for offset in (0.0, -0.08, 0.06):
            expanded.append(
                (
                    candidate.model_copy(
                        update={
                            "source_confidence": max(
                                0.0,
                                min(1.0, candidate.source_confidence + offset),
                            )
                        }
                    ),
                    label,
                )
            )
    return expanded


def train() -> None:
    ML_DIR.mkdir(parents=True, exist_ok=True)
    examples = seed_examples()
    now = datetime.now(timezone.utc)
    feature_names = DEFAULT_FEATURE_NAMES
    x = [extract_features(candidate, as_of=now, feature_names=feature_names) for candidate, _ in examples]
    y = [label for _, label in examples]

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.33,
        random_state=42,
        stratify=y,
    )
    model = GradientBoostingClassifier(random_state=42)
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)
    metrics = {
        "model": "GradientBoostingClassifier",
        "training_status": "synthetic seed baseline",
        "training_examples": len(x_train),
        "validation_examples": len(x_test),
        "validation_accuracy": accuracy_score(y_test, predictions),
        "feature_spec_version": 1,
        "notes": [
            "This is a deterministic baseline for local development.",
            "Replace with labels collected from real source responses before production use.",
        ],
    }

    joblib.dump(model, ML_DIR / "model.joblib")
    with (ML_DIR / "features.json").open("w", encoding="utf-8") as file:
        json.dump(feature_spec(), file, indent=2)
        file.write("\n")
    with (ML_DIR / "metrics.json").open("w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2)
        file.write("\n")

    print(f"Wrote model artifacts to {ML_DIR}")


if __name__ == "__main__":
    train()
