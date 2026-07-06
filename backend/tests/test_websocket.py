from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.schemas import AttackType, EventCreate, SourceName


@pytest.fixture
def test_settings(tmp_path):
    settings = Settings()
    settings.db_path = tmp_path / "test.db"
    settings.enable_scheduler = False
    settings.maxmind_db_path = None
    return settings


@pytest.fixture
def test_app(test_settings):
    return create_app(test_settings)


@pytest.fixture
def test_client(test_app):
    with TestClient(test_app) as client:
        yield client


async def test_websocket_sends_snapshot_on_connect(test_app, test_client):
    repository = test_app.state.repository
    
    event = EventCreate(
        ip="192.0.2.1",
        lat=35.6895,
        lng=139.6917,
        country="Japan",
        country_code="JP",
        asn="AS64500",
        score=0.85,
        type=AttackType.VOLUMETRIC,
        source=SourceName.SYNTHETIC,
    )
    await repository.insert_events([event])
    
    with test_client.websocket_connect("/ws/attacks") as websocket:
        data = websocket.receive_json()
        
        assert data["kind"] == "snapshot"
        assert "events" in data
        assert len(data["events"]) == 1
        assert data["events"][0]["ip"] == "192.0.2.1"
        assert data["events"][0]["startLat"] == 35.6895
        assert data["events"][0]["country"] == "Japan"


async def test_websocket_broadcasts_new_events(test_app, test_client):
    connection_manager = test_app.state.connection_manager
    repository = test_app.state.repository
    
    with test_client.websocket_connect("/ws/attacks") as websocket:
        snapshot = websocket.receive_json()
        assert snapshot["kind"] == "snapshot"
        
        event = EventCreate(
            ip="198.51.100.1",
            lat=40.7128,
            lng=-74.0060,
            country="United States",
            country_code="US",
            score=0.75,
            type=AttackType.SCANNER,
            source=SourceName.ABUSEIPDB,
        )
        stored = await repository.insert_events([event])
        await connection_manager.broadcast_events(stored)
        
        data = websocket.receive_json()
        assert data["kind"] == "events"
        assert len(data["events"]) == 1
        assert data["events"][0]["ip"] == "198.51.100.1"


def test_websocket_connection_and_disconnect(test_client):
    with test_client.websocket_connect("/ws/attacks") as websocket:
        data = websocket.receive_json()
        assert data["kind"] == "snapshot"
