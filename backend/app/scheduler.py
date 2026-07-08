from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import Settings
from app.db import EventRepository
from app.schemas import CandidateEvent, StoredEvent
from app.services.fetch_abuseipdb import fetch_abuseipdb_blacklist
from app.services.fetch_cloudflare import fetch_cloudflare_radar
from app.services.fetch_greynoise import fetch_greynoise_for_ips
from app.services.geo import GeoLocator
from app.services.normalizer import normalize_candidates
from app.services.scorer import ConfidenceScorer


logger = logging.getLogger(__name__)

BroadcastFn = Callable[[list[StoredEvent]], Awaitable[None]]


class AttackPoller:
    """Coordinates fetch, enrich, score, store, and optional broadcast work."""

    def __init__(
        self,
        *,
        settings: Settings,
        repository: EventRepository,
        geo_locator: GeoLocator,
        scorer: ConfidenceScorer,
        broadcast: BroadcastFn | None = None,
    ) -> None:
        self.settings = settings
        self.repository = repository
        self.geo_locator = geo_locator
        self.scorer = scorer
        self.broadcast = broadcast
        self._ipsum_cache: list[dict[str, str | int]] = []

    async def refresh_ipsum_cache(self, client: httpx.AsyncClient) -> None:
        from app.services.fetch_ipsum import fetch_ipsum_raw
        records = await fetch_ipsum_raw(client)
        if records:
            self._ipsum_cache = records
            logger.info("IPsum cache refreshed; count=%s", len(records))

    async def refresh_ipsum_cache_job(self) -> None:
        logger.info("Running daily scheduled IPsum cache refresh")
        timeout = httpx.Timeout(self.settings.source_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            await self.refresh_ipsum_cache(client)

    async def poll_once(self) -> list[StoredEvent]:
        logger.info("Starting attack poll cycle")
        candidates = await self._fetch_candidates()
        logger.info("Fetched %s candidate events", len(candidates))

        events = await normalize_candidates(
            candidates,
            geo_locator=self.geo_locator,
            score_candidate=self.scorer.score,
            min_score=self.settings.min_event_score,
        )
        inserted = await self.repository.insert_events(events)
        purged = await self.repository.purge_older_than(
            datetime.now(timezone.utc) - timedelta(hours=self.settings.event_ttl_hours)
        )

        if inserted and self.broadcast:
            await self.broadcast(inserted)

        logger.info(
            "Poll cycle complete: inserted=%s purged=%s scorer=%s",
            len(inserted),
            purged,
            self.scorer.mode,
        )
        return inserted

    async def _fetch_candidates(self) -> list[CandidateEvent]:
        timeout = httpx.Timeout(self.settings.source_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            from app.services.fetch_dshield import fetch_dshield_top_ips
            from app.services.fetch_ipsum import parse_ipsum_candidates

            cloudflare_task = _safe_fetch("cloudflare_radar", fetch_cloudflare_radar(client))
            abuse_task = _safe_fetch(
                "abuseipdb",
                fetch_abuseipdb_blacklist(
                    client,
                    api_key=self.settings.abuseipdb_key,
                    limit=self.settings.abuseipdb_blacklist_limit,
                ),
            )
            dshield_task = _safe_fetch(
                "dshield",
                fetch_dshield_top_ips(
                    client,
                    limit=self.settings.abuseipdb_blacklist_limit,
                ),
            )

            cloudflare_events, abuse_events, dshield_events = await asyncio.gather(
                cloudflare_task,
                abuse_task,
                dshield_task,
            )

            ipsum_events = parse_ipsum_candidates(
                self._ipsum_cache,
                sample_size=15,
            )

            all_events = [*cloudflare_events, *abuse_events, *dshield_events, *ipsum_events]

            candidate_ips = [event.ip for event in all_events if event.ip]
            greynoise_events = await _safe_fetch(
                "greynoise",
                fetch_greynoise_for_ips(
                    client,
                    api_key=self.settings.greynoise_key,
                    ips=candidate_ips,
                    limit=self.settings.greynoise_lookup_limit,
                ),
            )

        return [*all_events, *greynoise_events]


async def _safe_fetch(name: str, awaitable: Awaitable[list[CandidateEvent]]) -> list[CandidateEvent]:
    try:
        return await awaitable
    except Exception as exc:
        logger.warning("%s fetch failed: %s", name, exc)
        return []


def build_scheduler(poller: AttackPoller, settings: Settings) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=timezone.utc)
    scheduler.add_job(
        poller.poll_once,
        trigger="interval",
        seconds=settings.poll_interval_seconds,
        id="attack-poll",
        coalesce=True,
        max_instances=1,
        next_run_time=datetime.now(timezone.utc),
    )
    # Refresh IPsum cache once every 24 hours
    scheduler.add_job(
        poller.refresh_ipsum_cache_job,
        trigger="interval",
        hours=24,
        id="ipsum-cache-refresh",
        coalesce=True,
        max_instances=1,
    )
    return scheduler
