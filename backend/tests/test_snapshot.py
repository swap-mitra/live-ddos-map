import asyncio
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.config import Settings
from app.schemas import TARGET_POOL, AttackType, EventCreate, SourceName, target_for
from app.main import create_app


def test_snapshot_returns_inserted_events(tmp_path):
    settings = Settings()
    settings.db_path = tmp_path / "events.db"
    settings.enable_scheduler = False
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

    event = payload["events"][0]
    pool = ((settings.target_lat, settings.target_lng), *TARGET_POOL)
    assert (event["endLat"], event["endLng"]) in pool


def test_targets_fan_out_across_the_pool():
    """Arcs must not all converge on one point — consecutive ids get different targets."""
    kwargs = {"target_lat": 37.7749, "target_lng": -122.4194}
    targets = [target_for(event_id, **kwargs) for event_id in range(len(TARGET_POOL) + 1)]

    assert len(set(targets)) == len(targets)
    assert targets[0] == (37.7749, -122.4194)  # the configured target still leads
    assert target_for(0, **kwargs) == target_for(len(targets), **kwargs)  # stable by id

