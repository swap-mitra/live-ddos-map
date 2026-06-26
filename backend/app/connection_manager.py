from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket

from app.schemas import AttackEvent, StoredEvent


logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts event deltas."""

    def __init__(self, *, target_lat: float = 37.7749, target_lng: float = -122.4194) -> None:
        self.active_connections: list[WebSocket] = []
        self.target_lat = target_lat
        self.target_lng = target_lng

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket client connected; total=%s", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("WebSocket client disconnected; total=%s", len(self.active_connections))

    async def send_personal_message(self, message: dict[str, Any], websocket: WebSocket) -> None:
        try:
            await websocket.send_text(json.dumps(message, default=_json_default))
        except Exception as exc:
            logger.warning("Failed to send personal message: %s", exc)
            self.disconnect(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        if not self.active_connections:
            return

        dead_connections: list[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message, default=_json_default))
            except Exception as exc:
                logger.warning("Failed to broadcast to client: %s", exc)
                dead_connections.append(connection)

        for connection in dead_connections:
            self.disconnect(connection)

    async def broadcast_events(self, events: list[StoredEvent]) -> None:
        if not events:
            return
        
        from app.schemas import event_to_api
        
        api_events = [
            event_to_api(event, target_lat=self.target_lat, target_lng=self.target_lng)
            for event in events
        ]
        await self.broadcast({"kind": "events", "events": api_events})

    async def send_heartbeat(self) -> None:
        await self.broadcast({
            "kind": "heartbeat",
            "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        })


def _json_default(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat().replace("+00:00", "Z")
    if hasattr(obj, "model_dump"):
        return obj.model_dump(by_alias=True)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
