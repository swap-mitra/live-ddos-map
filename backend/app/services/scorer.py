from __future__ import annotations

from app.schemas import CandidateEvent


def clamp_score(value: float) -> float:
    return max(0.0, min(1.0, value))


class HeuristicScorer:
    """Phase 1 scorer used until the trained model lands in Phase 2.

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

