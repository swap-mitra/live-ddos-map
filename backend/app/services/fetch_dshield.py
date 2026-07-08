from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from app.schemas import AttackType, CandidateEvent, SourceName

logger = logging.getLogger(__name__)

DSHIELD_URL = "https://isc.sans.edu/api/topips/records/{limit}?json"


async def fetch_dshield_top_ips(
    client: httpx.AsyncClient,
    *,
    limit: int = 100,
) -> list[CandidateEvent]:
    """Fetch top attacking IPs from SANS Internet Storm Center (DShield).

    No API key required.
    """
    url = DSHIELD_URL.format(limit=limit)
    try:
        response = await client.get(url)
        response.raise_for_status()
    except Exception as exc:
        logger.warning("Failed to fetch from DShield API: %s; skipping", exc)
        return []

    try:
        payload = response.json()
    except Exception as exc:
        logger.warning("Failed to parse DShield JSON: %s; skipping", exc)
        return []

    top_ips = payload.get("topips", {})
    ip_records = top_ips.get("ipaddress", [])

    # Handle single item returned as dict instead of list
    if isinstance(ip_records, dict):
        ip_records = [ip_records]

    events: list[CandidateEvent] = []
    ts = datetime.now(timezone.utc)

    for record in ip_records:
        ip = record.get("source")
        if not ip:
            continue

        rank = int(record.get("rank") or 0)
        reports = int(record.get("reports") or 0)
        targets = int(record.get("targets") or 0)

        # Set confidence based on rank/reports/targets relative intensity
        confidence = 0.5 + min(0.4, (reports / 10000.0) + (targets / 500.0))

        events.append(
            CandidateEvent(
                ip=ip,
                source=SourceName.DSHIELD,
                raw_source_id=f"dshield:{ip}:{rank}",
                type_hint=AttackType.SCANNER,
                source_confidence=min(1.0, confidence),
                features={
                    "dshield_rank": rank,
                    "dshield_reports": reports,
                    "dshield_targets": targets,
                },
                ts=ts,
            )
        )

    return events
