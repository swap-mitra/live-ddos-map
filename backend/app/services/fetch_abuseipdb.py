from __future__ import annotations

import logging

import httpx

from app.schemas import AttackType, CandidateEvent, SourceName


logger = logging.getLogger(__name__)

BLACKLIST_URL = "https://api.abuseipdb.com/api/v2/blacklist"


async def fetch_abuseipdb_blacklist(
    client: httpx.AsyncClient,
    *,
    api_key: str | None,
    limit: int,
) -> list[CandidateEvent]:
    """Fetch high-confidence abusive IPs from AbuseIPDB when a key is configured."""

    if not api_key:
        logger.info("Skipping AbuseIPDB fetch because ABUSEIPDB_KEY is not set")
        return []

    response = await client.get(
        BLACKLIST_URL,
        headers={"Key": api_key, "Accept": "application/json"},
        params={"confidenceMinimum": 75, "limit": limit},
    )
    response.raise_for_status()
    payload = response.json()
    rows = payload.get("data", [])
    events: list[CandidateEvent] = []

    for row in rows:
        ip = row.get("ipAddress")
        if not ip:
            continue
        confidence = float(row.get("abuseConfidenceScore") or 0.0)
        last_reported = row.get("lastReportedAt")
        events.append(
            CandidateEvent(
                ip=ip,
                source=SourceName.ABUSEIPDB,
                raw_source_id=f"abuseipdb:{ip}:{last_reported or ''}",
                type_hint=AttackType.SCANNER,
                source_confidence=max(0.0, min(1.0, confidence / 100.0)),
                country_code=row.get("countryCode"),
                features={
                    "abuse_confidence_score": confidence,
                    "total_reports": row.get("totalReports"),
                    "last_reported_at": last_reported,
                },
            )
        )

    return events
