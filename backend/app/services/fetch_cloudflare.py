from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from app.schemas import AttackType, CandidateEvent, SourceName


logger = logging.getLogger(__name__)

LAYER3_TIMESERIES_URL = "https://api.cloudflare.com/client/v4/radar/attacks/layer3/timeseries_groups"

# Coarse country centroids keep aggregate Radar signals renderable on the globe.
COUNTRY_CENTROIDS: dict[str, tuple[float, float, str]] = {
    "US": (39.8283, -98.5795, "United States"),
    "IN": (20.5937, 78.9629, "India"),
    "BR": (-14.2350, -51.9253, "Brazil"),
    "DE": (51.1657, 10.4515, "Germany"),
    "GB": (55.3781, -3.4360, "United Kingdom"),
    "JP": (36.2048, 138.2529, "Japan"),
    "AU": (-25.2744, 133.7751, "Australia"),
}


async def fetch_cloudflare_radar(
    client: httpx.AsyncClient, *, api_token: str | None = None
) -> list[CandidateEvent]:
    """Fetch aggregate network-layer DDoS trends from Cloudflare Radar.

    Radar data is trend-oriented, so these events may not have source IPs.
    Requires a Cloudflare API token (Radar reads are not available anonymously).
    """

    if not api_token:
        logger.info("Skipping Cloudflare Radar fetch because CLOUDFLARE_API_TOKEN is not set")
        return []

    try:
        response = await client.get(
            LAYER3_TIMESERIES_URL,
            params={"dateRange": "1h", "name": "ddos"},
            headers={"Authorization": f"Bearer {api_token}"},
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logger.warning("Cloudflare Radar returned %s; skipping", exc.response.status_code)
        return []

    payload = response.json()
    result = payload.get("result") or {}
    series = result.get("ddos") or {}
    timestamps = result.get("timestamps") or []

    # The API response is aggregate. We emit one conservative trend event if
    # the most recent bucket is non-zero and let future phases refine geography.
    values = [float(value or 0.0) for value in series.values()] if isinstance(series, dict) else []
    latest_value = values[-1] if values else 0.0
    if latest_value <= 0:
        return []

    ts = _parse_ts(timestamps[-1]) if timestamps else datetime.now(timezone.utc)
    lat, lng, country = COUNTRY_CENTROIDS["US"]
    return [
        CandidateEvent(
            ip=None,
            lat=lat,
            lng=lng,
            country=country,
            country_code="US",
            source=SourceName.CLOUDFLARE_RADAR,
            raw_source_id=f"cloudflare:layer3:{ts.isoformat()}",
            type_hint=AttackType.VOLUMETRIC,
            source_confidence=0.6,
            features={
                "cloudflare_ddos_trend": True,
                "cloudflare_latest_value": latest_value,
            },
            ts=ts,
        )
    ]


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)

