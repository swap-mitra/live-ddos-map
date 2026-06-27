#!/usr/bin/env python
"""Manual smoke test for WebSocket endpoint.

Run the backend with:
    uvicorn app.main:app --reload

Then run this script in another terminal:
    python scripts/test_websocket_manual.py
"""

import asyncio
import json

import websockets


async def test_websocket():
    uri = "ws://localhost:8000/ws/attacks"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected! Waiting for snapshot...")
            
            message = await websocket.recv()
            data = json.loads(message)
            
            print(f"Received: {data.get('kind')}")
            print(f"Events count: {len(data.get('events', []))}")
            
            if data.get("kind") == "snapshot":
                print("✓ WebSocket snapshot received successfully")
                if data.get("events"):
                    print(f"✓ Sample event: {data['events'][0]}")
                else:
                    print("✓ Empty snapshot (no events yet)")
                return True
            else:
                print("✗ Expected snapshot, got:", data.get("kind"))
                return False
    except Exception as exc:
        print(f"✗ Connection failed: {exc}")
        print("Make sure the backend is running: uvicorn app.main:app --reload")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_websocket())
    exit(0 if success else 1)
