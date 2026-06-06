import asyncio
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.config import Settings
from app.schemas import AttackType, EventCreate, SourceName
from app.main import create_app


def test_snapshot_returns_inserted_events(tmp_path):
    settings = Settings(db_path=tmp_path / "events.db", enable_scheduler=False)
    app = create_app(settings)

    with TestClient(app) as client:
        repository = client.app.state.repository
        asyncio.run(
            repository.insert_events(
                [
                    EventCreate(
                        ip="8.8.8.8",
                        lat=37.386,
                        lng=-122.0838,
                        country="United States",
                        country_code="US",
                        asn="AS15169",
                        score=0.91,
                        type=AttackType.SCANNER,
                        source=SourceName.SYNTHETIC,
                        raw_source_id="test:8.8.8.8",
                        ts=datetime(2026, 6, 6, 12, 0, tzinfo=timezone.utc),
                    )
                ]
            )
        )

        response = client.get("/api/snapshot")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["events"]) == 1
    assert payload["events"][0]["ip"] == "8.8.8.8"
    assert payload["events"][0]["startLat"] == 37.386
    assert payload["events"][0]["endLat"] == settings.target_lat

