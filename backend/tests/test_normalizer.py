from app.schemas import AttackType, CandidateEvent, SourceName
from app.services.geo import GeoResult
from app.services.normalizer import normalize_candidates
from app.services.scorer import HeuristicScorer


class StubGeoLocator:
    def lookup_ip(self, ip):
        if ip == "8.8.8.8":
            return GeoResult(
                lat=37.386,
                lng=-122.0838,
                country="United States",
                country_code="US",
                asn="AS15169",
            )
        return None


def test_normalizer_geolocates_scores_and_dedupes_candidates():
    scorer = HeuristicScorer()
    candidates = [
        CandidateEvent(
            ip="8.8.8.8",
            source=SourceName.SYNTHETIC,
            raw_source_id="same",
            type_hint=AttackType.SCANNER,
            source_confidence=0.8,
        ),
        CandidateEvent(
            ip="8.8.8.8",
            source=SourceName.SYNTHETIC,
            raw_source_id="same",
            type_hint=AttackType.SCANNER,
            source_confidence=0.8,
        ),
    ]

    events = normalize_candidates(
        candidates,
        geo_locator=StubGeoLocator(),
        score_candidate=scorer.score,
        min_score=0.5,
    )

    assert len(events) == 1
    assert events[0].lat == 37.386
    assert events[0].country_code == "US"
    assert events[0].score == 0.8


def test_normalizer_skips_candidates_without_coordinates():
    events = normalize_candidates(
        [
            CandidateEvent(
                ip="192.0.2.1",
                source=SourceName.SYNTHETIC,
                source_confidence=0.95,
            )
        ],
        geo_locator=StubGeoLocator(),
        score_candidate=HeuristicScorer().score,
        min_score=0.5,
    )

    assert events == []

