from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_health_returns_ok(tmp_path):
    settings = Settings(db_path=tmp_path / "events.db", enable_scheduler=False)
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "live-ddos-map-backend"}

