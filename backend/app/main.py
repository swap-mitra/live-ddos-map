from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.db import EventRepository
from app.scheduler import AttackPoller, build_scheduler
from app.schemas import HealthResponse, SnapshotResponse, event_to_api
from app.services.geo import GeoLocator
from app.services.scorer import HeuristicScorer


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        repository = EventRepository(settings.db_path)
        await repository.initialize()

        geo_locator = GeoLocator(settings.maxmind_db_path)
        scorer = HeuristicScorer()
        poller = AttackPoller(
            settings=settings,
            repository=repository,
            geo_locator=geo_locator,
            scorer=scorer,
        )

        scheduler = None
        if settings.enable_scheduler:
            scheduler = build_scheduler(poller, settings)
            scheduler.start()

        app.state.settings = settings
        app.state.repository = repository
        app.state.geo_locator = geo_locator
        app.state.scorer = scorer
        app.state.poller = poller
        app.state.scheduler = scheduler

        try:
            yield
        finally:
            if scheduler:
                scheduler.shutdown(wait=False)
            geo_locator.close()

    app = FastAPI(
        title="Live DDoS Map Backend",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(status="ok", service=settings.service_name)

    @app.get("/api/snapshot", response_model=SnapshotResponse)
    async def snapshot(
        request: Request,
        limit: int = Query(default=200, ge=1, le=500),
    ) -> SnapshotResponse:
        repository: EventRepository = request.app.state.repository
        recent_events = await repository.list_recent_events(limit=limit)
        return SnapshotResponse(
            events=[
                event_to_api(
                    event,
                    target_lat=settings.target_lat,
                    target_lng=settings.target_lng,
                )
                for event in recent_events
            ]
        )

    return app


app = create_app()

