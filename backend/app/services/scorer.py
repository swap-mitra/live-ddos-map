from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Protocol

import joblib

from app.config import Settings
from app.schemas import CandidateEvent
from app.services.features import DEFAULT_FEATURE_NAMES, extract_features


logger = logging.getLogger(__name__)


class ConfidenceScorer(Protocol):
    mode: str

    def score(self, candidate: CandidateEvent) -> float:
        """Return a confidence score from 0.0 to 1.0."""


def clamp_score(value: float) -> float:
    return max(0.0, min(1.0, value))


class ModelScorer:
    """Runtime scorer backed by a serialized scikit-learn style classifier."""

    mode = "model"

    def __init__(self, model_path: Path, *, feature_names: tuple[str, ...]) -> None:
        self.model_path = model_path
        self.feature_names = feature_names
        self.model = joblib.load(model_path)

    def score(self, candidate: CandidateEvent) -> float:
        vector = extract_features(candidate, feature_names=self.feature_names)
        matrix = [vector]

        if hasattr(self.model, "predict_proba"):
            probabilities = self.model.predict_proba(matrix)
            return clamp_score(float(probabilities[0][1]))

        if hasattr(self.model, "decision_function"):
            decision = float(self.model.decision_function(matrix)[0])
            return clamp_score(1.0 / (1.0 + pow(2.718281828459045, -decision)))

        prediction = self.model.predict(matrix)
        return clamp_score(float(prediction[0]))


class HeuristicScorer:
    """Deterministic fallback when a trained artifact is unavailable.

    The heuristic is intentionally simple and deterministic so tests and local
    development do not depend on a serialized ML artifact.
    """

    mode = "heuristic"

    def score(self, candidate: CandidateEvent) -> float:
        score = candidate.source_confidence
        features = candidate.features

        abuse_score = features.get("abuse_confidence_score")
        if isinstance(abuse_score, int | float):
            score = max(score, float(abuse_score) / 100.0)

        classification = str(features.get("greynoise_classification") or "").lower()
        if classification == "malicious":
            score = max(score, 0.85)
        elif classification == "suspicious":
            score = max(score, 0.65)
        elif classification == "benign":
            score = min(score, 0.35)

        source_count = features.get("source_count")
        if isinstance(source_count, int | float) and source_count > 1:
            score += min(0.15, 0.05 * (float(source_count) - 1.0))

        if features.get("cloudflare_ddos_trend") is True:
            score += 0.1

        return clamp_score(score)


def build_scorer(settings: Settings) -> ConfidenceScorer:
    """Create the production scorer, falling back only when explicitly allowed."""

    model_path = settings.model_path
    if model_path.exists():
        feature_names = load_feature_names(model_path.with_name("features.json"))
        scorer = ModelScorer(model_path, feature_names=feature_names)
        logger.info("Loaded ML scorer from %s with %s features", model_path, len(feature_names))
        return scorer

    if settings.enable_heuristic_scorer:
        logger.warning(
            "Model artifact %s is missing; using heuristic scorer because fallback is enabled",
            model_path,
        )
        return HeuristicScorer()

    raise RuntimeError(
        f"Model artifact {model_path} is missing and ENABLE_HEURISTIC_SCORER is disabled"
    )


def load_feature_names(features_path: Path) -> tuple[str, ...]:
    if not features_path.exists():
        logger.warning("Feature spec %s is missing; using built-in feature order", features_path)
        return DEFAULT_FEATURE_NAMES

    with features_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    names = payload.get("feature_names")
    if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
        raise ValueError(f"Feature spec {features_path} must contain a string feature_names list")

    return tuple(names)
