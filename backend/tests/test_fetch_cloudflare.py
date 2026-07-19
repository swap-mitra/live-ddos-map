from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.schemas import SourceName
from app.services.fetch_cloudflare import fetch_cloudflare_radar


@pytest.mark.asyncio
async def test_fetch_cloudflare_radar_skips_without_token():
    client = MagicMock(spec=httpx.AsyncClient)
    client.get = AsyncMock()

    events = await fetch_cloudflare_radar(client, api_token=None)

    assert events == []
    client.get.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_cloudflare_radar_sends_bearer_token_when_configured():
    mock_response = {
        "result": {
            "ddos": {"0": 1, "1": 5},
            "timestamps": ["2026-07-19T00:00:00Z", "2026-07-19T01:00:00Z"],
        }
    }
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_response
    mock_resp.raise_for_status = MagicMock()

    client = MagicMock(spec=httpx.AsyncClient)
    client.get = AsyncMock(return_value=mock_resp)

    events = await fetch_cloudflare_radar(client, api_token="test-token")

    client.get.assert_called_once()
    _, kwargs = client.get.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer test-token"
    assert len(events) == 1
    assert events[0].source == SourceName.CLOUDFLARE_RADAR
