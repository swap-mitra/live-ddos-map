from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from app.schemas import AttackType, CandidateEvent, SourceName

logger = logging.getLogger(__name__)

IPSUM_URL = "https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt"


async def fetch_ipsum_raw(client: httpx.AsyncClient) -> list[dict[str, str | int]]:
    """Fetch and parse Stamparm's IPsum text list.

    Returns a list of dicts: [{'ip': '...', 'score': 5}, ...]
    """
    try:
        response = await client.get(IPSUM_URL)
        response.raise_for_status()
    except Exception as exc:
        logger.warning("Failed to fetch from IPsum repository: %s; skipping", exc)
        return []

    records: list[dict[str, str | int]] = []
    lines = response.text.splitlines()

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split()
        if len(parts) >= 2:
            ip = parts[0]
            try:
                score = int(parts[1])
                # We only track high confidence hits (on 3 or more blacklists) to keep the list clean
                if score >= 3:
                    records.append({"ip": ip, "score": score})
            except ValueError:
                continue

    logger.info("Fetched %s high-confidence IPs from IPsum list", len(records))
    return records


def parse_ipsum_candidates(
    records: list[dict[str, str | int]],
    *,
    sample_size: int = 15,
) -> list[CandidateEvent]:
    """Given a list of IPsum records, sample a batch and format them as CandidateEvents."""
    import random

    if not records:
        return []

    # Randomly sample a subset of the loaded high-confidence list
    sampled = random.sample(records, min(len(records), sample_size))
    events: list[CandidateEvent] = []
    ts = datetime.now(timezone.utc)

    for item in sampled:
        ip = str(item["ip"])
        score = int(item["score"])
        
        # IPsum score is blacklist hit count out of ~30. Let's map it to a confidence float.
        confidence = 0.5 + min(0.5, (score / 10.0))

        events.append(
            CandidateEvent(
                ip=ip,
                source=SourceName.IPSUM,
                raw_source_id=f"ipsum:{ip}:{ts.strftime('%Y%m%d')}",
                type_hint=AttackType.SCANNER,
                source_confidence=confidence,
                features={
                    "ipsum_blacklist_hits": score,
                },
                ts=ts,
            )
        )

    return events
