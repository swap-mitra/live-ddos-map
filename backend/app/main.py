from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.connection_manager import ConnectionManager
from app.db import EventRepository
from app.scheduler import AttackPoller, build_scheduler
from app.schemas import HealthResponse, SnapshotResponse, event_to_api
from app.services.geo import GeoLocator
from app.services.scorer import build_scorer


logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        repository = EventRepository(settings.db_path)
        await repository.initialize()

        geo_locator = GeoLocator(
            settings.maxmind_db_path,
            account_id=settings.maxmind_account_id,
            license_key=settings.maxmind_license_key,
        )
        scorer = build_scorer(settings)
        connection_manager = ConnectionManager(
            target_lat=settings.target_lat,
            target_lng=settings.target_lng,
        )
        
        poller = AttackPoller(
            settings=settings,
            repository=repository,
            geo_locator=geo_locator,
            scorer=scorer,
            broadcast=connection_manager.broadcast_events,
        )

        scheduler = None
        if settings.enable_scheduler:
            scheduler = build_scheduler(poller, settings)
            scheduler.add_job(
                connection_manager.send_heartbeat,
                trigger="interval",
                seconds=settings.ws_heartbeat_interval_seconds,
                id="websocket-heartbeat",
                coalesce=True,
                max_instances=1,
            )
            scheduler.start()

        app.state.settings = settings
        app.state.repository = repository
        app.state.geo_locator = geo_locator
        app.state.scorer = scorer
        app.state.poller = poller
        app.state.scheduler = scheduler
        app.state.connection_manager = connection_manager

        try:
            yield
        finally:
            if scheduler:
                scheduler.shutdown(wait=False)
            await geo_locator.close()

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

    @app.websocket("/ws/attacks")
    async def websocket_attacks(websocket: WebSocket) -> None:
        connection_manager: ConnectionManager = websocket.app.state.connection_manager
        repository: EventRepository = websocket.app.state.repository
        
        origin = websocket.headers.get("origin")
        if origin and origin not in settings.allowed_origins:
            logger.warning("Rejected WebSocket connection from unauthorized origin: %s", origin)
            await websocket.close(code=1008)
            return
        
        await connection_manager.connect(websocket)
        
        try:
            recent_events = await repository.list_recent_events(limit=200)
            snapshot_payload = {
                "kind": "snapshot",
                "events": [
                    event_to_api(
                        event,
                        target_lat=settings.target_lat,
                        target_lng=settings.target_lng,
                    )
                    for event in recent_events
                ],
            }
            await connection_manager.send_personal_message(snapshot_payload, websocket)
            
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            connection_manager.disconnect(websocket)
        except Exception as exc:
            logger.warning("WebSocket error: %s", exc)
            connection_manager.disconnect(websocket)

    return app


app = create_app()
