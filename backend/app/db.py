from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import aiosqlite

from app.schemas import AttackType, EventCreate, SourceName, StoredEvent


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ip TEXT,
  lat REAL NOT NULL,
  lng REAL NOT NULL,
  country TEXT,
  country_code TEXT,
  asn TEXT,
  score REAL NOT NULL,
  type TEXT NOT NULL,
  source TEXT NOT NULL,
  raw_source_id TEXT,
  features_json TEXT,
  ts TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_ts ON events (ts);
CREATE INDEX IF NOT EXISTS idx_events_score ON events (score);
CREATE INDEX IF NOT EXISTS idx_events_country ON events (country_code);
"""


def utc_iso(value: datetime) -> str:
    value = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


class EventRepository:
    """Small SQLite repository for the rolling attack event window."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    async def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(SCHEMA_SQL)
            await db.commit()

    async def insert_events(self, events: Iterable[EventCreate]) -> list[StoredEvent]:
        inserted: list[StoredEvent] = []
        event_list = list(events)
        if not event_list:
            return inserted

        async with aiosqlite.connect(self.db_path) as db:
            for event in event_list:
                cursor = await db.execute(
                    """
                    INSERT INTO events (
                      ip, lat, lng, country, country_code, asn, score, type,
                      source, raw_source_id, features_json, ts
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.ip,
                        event.lat,
                        event.lng,
                        event.country,
                        event.country_code,
                        event.asn,
                        event.score,
                        event.type.value,
                        event.source.value,
                        event.raw_source_id,
                        json.dumps(event.features, sort_keys=True),
                        utc_iso(event.ts),
                    ),
                )
                inserted.append(StoredEvent(id=cursor.lastrowid, **event.model_dump()))
            await db.commit()
        return inserted

    async def list_recent_events(self, *, limit: int = 200) -> list[StoredEvent]:
        safe_limit = min(max(limit, 0), 500)
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT *
                FROM events
                ORDER BY ts DESC, id DESC
                LIMIT ?
                """,
                (safe_limit,),
            )
            rows = await cursor.fetchall()
        return [self._row_to_event(row) for row in rows]

    async def purge_older_than(self, cutoff: datetime) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("DELETE FROM events WHERE ts < ?", (utc_iso(cutoff),))
            await db.commit()
            return cursor.rowcount

    @staticmethod
    def _row_to_event(row: aiosqlite.Row) -> StoredEvent:
        return StoredEvent(
            id=row["id"],
            ip=row["ip"],
            lat=row["lat"],
            lng=row["lng"],
            country=row["country"],
            country_code=row["country_code"],
            asn=row["asn"],
            score=row["score"],
            type=AttackType(row["type"]),
            source=SourceName(row["source"]),
            raw_source_id=row["raw_source_id"],
            features=json.loads(row["features_json"] or "{}"),
            ts=parse_utc(row["ts"]),
        )

