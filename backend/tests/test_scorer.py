from app.schemas import CandidateEvent, SourceName
from app.services.scorer import HeuristicScorer


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

