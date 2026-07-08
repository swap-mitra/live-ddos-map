from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
import httpx
import pytest

from app.schemas import AttackType, SourceName
from app.services.fetch_dshield import fetch_dshield_top_ips
from app.services.fetch_ipsum import fetch_ipsum_raw, parse_ipsum_candidates


@pytest.mark.asyncio
async def test_fetch_dshield_top_ips_success():
    mock_response = {
        "topips": {
            "ipaddress": [
                {
                    "rank": "1",
                    "source": "8.8.8.8",
                    "reports": "1000",
                    "targets": "50",
                }
            ]
        }
    }
    
    # Mock httpx.Response
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_type = mock_response
    mock_resp.json.return_value = mock_response
    
    # Mock httpx.AsyncClient
    client = MagicMock(spec=httpx.AsyncClient)
    client.get = AsyncMock(return_value=mock_resp)

    events = await fetch_dshield_top_ips(client)

    client.get.assert_called_once_with("https://isc.sans.edu/api/topips/records/100?json")
    assert len(events) == 1
    event = events[0]
    assert event.ip == "8.8.8.8"
    assert event.source == SourceName.DSHIELD
    assert event.type_hint == AttackType.SCANNER
    assert event.features["dshield_rank"] == 1
    assert event.features["dshield_reports"] == 1000
    assert event.features["dshield_targets"] == 50


@pytest.mark.asyncio
async def test_fetch_ipsum_raw_success():
    mock_text = (
        "# Some comments\n"
        "# More comments\n"
        "1.1.1.1\t5\n"
        "2.2.2.2\t2\n"  # should be filtered out because score < 3
        "3.3.3.3\t10\n"
    )
    
    # Mock httpx.Response
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.text = mock_text
    
    # Mock httpx.AsyncClient
    client = MagicMock(spec=httpx.AsyncClient)
    client.get = AsyncMock(return_value=mock_resp)

    records = await fetch_ipsum_raw(client)

    client.get.assert_called_once_with("https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt")
    assert len(records) == 2
    assert records[0] == {"ip": "1.1.1.1", "score": 5}
    assert records[1] == {"ip": "3.3.3.3", "score": 10}


def test_parse_ipsum_candidates():
    records = [
        {"ip": "1.1.1.1", "score": 5},
        {"ip": "3.3.3.3", "score": 10},
    ]
    candidates = parse_ipsum_candidates(records, sample_size=5)

    assert len(candidates) == 2
    ips = {c.ip for c in candidates}
    assert ips == {"1.1.1.1", "3.3.3.3"}
    for candidate in candidates:
        assert candidate.source == SourceName.IPSUM
        assert candidate.type_hint == AttackType.SCANNER
        assert "ipsum_blacklist_hits" in candidate.features
