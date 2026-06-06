from __future__ import annotations

import asyncio
import logging

import httpx

from app.schemas import AttackType, CandidateEvent, SourceName


logger = logging.getLogger(__name__)

COMMUNITY_URL = "https://api.greynoise.io/v3/community/{ip}"


async def fetch_greynoise_for_ips(
    client: httpx.AsyncClient,
    *,
    api_key: str | None,
    ips: list[str],
    limit: int,
) -> list[CandidateEvent]:
    """Look up candidate IPs in GreyNoise Community API."""

    if not api_key:
        logger.info("Skipping GreyNoise fetch because GREYNOISE_KEY is not set")
        return []

    limited_ips = ips[:limit]
    if not limited_ips:
        return []

    tasks = [_fetch_one(client, api_key=api_key, ip=ip) for ip in limited_ips]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    events: list[CandidateEvent] = []
    for result in results:
        if isinstance(result, Exception):
            logger.warning("GreyNoise lookup failed: %s", result)
            continue
        if result:
            events.append(result)
    return events


async def _fetch_one(
    client: httpx.AsyncClient,
    *,
    api_key: str,
    ip: str,
) -> CandidateEvent | None:
    response = await client.get(
        COMMUNITY_URL.format(ip=ip),
        headers={"key": api_key, "Accept": "application/json"},
    )
    response.raise_for_status()
    payload = response.json()

    classification = str(payload.get("classification") or "unknown").lower()
    noise = bool(payload.get("noise"))
    riot = bool(payload.get("riot"))
    if not noise and classification in {"unknown", "benign"}:
        return None

    confidence = 0.75 if classification == "malicious" else 0.55 if noise else 0.25
    return CandidateEvent(
        ip=ip,
        source=SourceName.GREYNOISE,
        raw_source_id=f"greynoise:{ip}:{payload.get('last_seen') or ''}",
        type_hint=AttackType.SCANNER,
        source_confidence=confidence,
        asn=payload.get("asn"),
        features={
            "greynoise_classification": classification,
            "greynoise_noise": noise,
            "greynoise_riot": riot,
            "greynoise_name": payload.get("name"),
            "greynoise_link": payload.get("link"),
            "last_seen": payload.get("last_seen"),
        },
    )

