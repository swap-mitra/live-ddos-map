from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import httpx

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config import Settings  # noqa: E402
from app.services.fetch_abuseipdb import fetch_abuseipdb_blacklist  # noqa: E402
from app.services.fetch_cloudflare import fetch_cloudflare_radar  # noqa: E402
from app.services.fetch_greynoise import fetch_greynoise_for_ips  # noqa: E402


async def collect(output: Path, limit: int) -> int:
    settings = Settings()
    timeout = httpx.Timeout(settings.source_timeout_seconds)

    async with httpx.AsyncClient(timeout=timeout) as client:
        cloudflare_events = await fetch_cloudflare_radar(client)
        abuse_events = await fetch_abuseipdb_blacklist(
            client,
            api_key=settings.abuseipdb_key,
            limit=limit,
        )
        ips = [event.ip for event in abuse_events if event.ip]
        greynoise_events = await fetch_greynoise_for_ips(
            client,
            api_key=settings.greynoise_key,
            ips=ips,
            limit=min(limit, settings.greynoise_lookup_limit),
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    events = [*cloudflare_events, *abuse_events, *greynoise_events]
    with output.open("a", encoding="utf-8") as file:
        for event in events:
            file.write(json.dumps(event.model_dump(mode="json"), sort_keys=True))
            file.write("\n")
    return len(events)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect candidate events for ML labeling.")
    parser.add_argument("--output", type=Path, default=Path("backend/raw_data/candidates.jsonl"))
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    count = asyncio.run(collect(args.output, args.limit))
    print(f"Wrote {count} candidate examples to {args.output}")


if __name__ == "__main__":
    main()
