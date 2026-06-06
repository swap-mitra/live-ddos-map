from __future__ import annotations

import logging
from collections.abc import Callable, Iterable

from app.schemas import AttackType, CandidateEvent, EventCreate, feature_value
from app.services.geo import GeoLocator


logger = logging.getLogger(__name__)


ScoreFn = Callable[[CandidateEvent], float]


def normalize_candidates(
    candidates: Iterable[CandidateEvent],
    *,
    geo_locator: GeoLocator,
    score_candidate: ScoreFn,
    min_score: float,
) -> list[EventCreate]:
    """Convert fetched candidates into scored database-ready events.

    Candidates without coordinates are geolocated by IP. If the pipeline still
    cannot place them on the globe, they are skipped rather than stored.
    """

    events: list[EventCreate] = []
    seen_keys: set[str] = set()

    for candidate in candidates:
        dedupe_key = _dedupe_key(candidate)
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)

        enriched = _with_geo(candidate, geo_locator)
        if enriched.lat is None or enriched.lng is None:
            logger.debug("Skipping candidate without usable coordinates: %s", enriched.raw_source_id)
            continue

        score = score_candidate(enriched)
        if score < min_score:
            continue

        features = {key: feature_value(value) for key, value in enriched.features.items()}
        events.append(
            EventCreate(
                ip=enriched.ip,
                lat=enriched.lat,
                lng=enriched.lng,
                country=enriched.country,
                country_code=enriched.country_code,
                asn=enriched.asn,
                score=score,
                type=enriched.type_hint or AttackType.UNKNOWN,
                source=enriched.source,
                raw_source_id=enriched.raw_source_id,
                features=features,
                ts=enriched.ts,
            )
        )

    return events


def _with_geo(candidate: CandidateEvent, geo_locator: GeoLocator) -> CandidateEvent:
    if candidate.lat is not None and candidate.lng is not None:
        return candidate

    result = geo_locator.lookup_ip(candidate.ip)
    if not result:
        return candidate

    return candidate.model_copy(
        update={
            "lat": result.lat,
            "lng": result.lng,
            "country": candidate.country or result.country,
            "country_code": candidate.country_code or result.country_code,
            "asn": candidate.asn or result.asn,
        }
    )


def _dedupe_key(candidate: CandidateEvent) -> str:
    if candidate.raw_source_id:
        return f"{candidate.source}:{candidate.raw_source_id}"
    if candidate.ip:
        return f"{candidate.source}:ip:{candidate.ip}"
    return f"{candidate.source}:geo:{candidate.country_code}:{candidate.ts.isoformat()[:16]}"
