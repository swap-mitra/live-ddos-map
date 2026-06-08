import json

from app.schemas import CandidateEvent, SourceName
from app.config import Settings
from app.services.features import DEFAULT_FEATURE_NAMES
from app.services.scorer import HeuristicScorer, build_scorer


class FixedProbabilityModel:
    def predict_proba(self, matrix):
        return [[0.22, 0.78] for _ in matrix]


def test_heuristic_scorer_uses_abuse_score_and_clamps():
    scorer = HeuristicScorer()
    score = scorer.score(
        CandidateEvent(
            source=SourceName.SYNTHETIC,
            source_confidence=0.2,
            features={
                "abuse_confidence_score": 98,
                "source_count": 10,
                "cloudflare_ddos_trend": True,
            },
        )
    )

    assert score == 1.0


def test_heuristic_scorer_treats_benign_greynoise_as_low_confidence():
    scorer = HeuristicScorer()
    score = scorer.score(
        CandidateEvent(
            source=SourceName.SYNTHETIC,
            source_confidence=0.9,
            features={"greynoise_classification": "benign"},
        )
    )

    assert score == 0.35


def test_build_scorer_uses_heuristic_when_model_is_missing_and_fallback_enabled(tmp_path):
    settings = Settings(
        db_path=tmp_path / "events.db",
        model_path=tmp_path / "missing.joblib",
        enable_heuristic_scorer=True,
    )

    scorer = build_scorer(settings)

    assert scorer.mode == "heuristic"


def test_build_scorer_fails_when_model_is_missing_and_fallback_disabled(tmp_path):
    settings = Settings(
        db_path=tmp_path / "events.db",
        model_path=tmp_path / "missing.joblib",
        enable_heuristic_scorer=False,
    )

    try:
        build_scorer(settings)
    except RuntimeError as exc:
        assert "ENABLE_HEURISTIC_SCORER" in str(exc)
    else:
        raise AssertionError("Expected missing model to fail when fallback is disabled")


def test_build_scorer_loads_model_and_feature_spec(tmp_path):
    import joblib

    model_path = tmp_path / "model.joblib"
    features_path = tmp_path / "features.json"
    joblib.dump(FixedProbabilityModel(), model_path)
    features_path.write_text(
        json.dumps({"feature_names": list(DEFAULT_FEATURE_NAMES)}),
        encoding="utf-8",
    )
    settings = Settings(
        db_path=tmp_path / "events.db",
        model_path=model_path,
        enable_heuristic_scorer=False,
    )

    scorer = build_scorer(settings)
    score = scorer.score(CandidateEvent(source=SourceName.SYNTHETIC))

    assert scorer.mode == "model"
    assert score == 0.78
