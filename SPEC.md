# Live DDoS Map - Spec Driven Development Plan

Version: 0.1  
Status: implementation-ready draft  
Source artifact: `ddos-architecture.png`  
Primary audience: AI development agents working phase by phase

## 1. Product Intent

Build a live, portfolio-grade DDoS activity map that shows recent high-risk internet attack signals as animated arcs on a dark WebGL globe. The project should feel like a real-time threat operations dashboard while staying practical for free-tier hosting.

The core experience is:

1. A backend polls public/free threat and traffic sources every 60 seconds.
2. Raw source data is normalized into attack events.
3. Events are enriched with offline IP geolocation.
4. A lightweight ML scorer assigns a DDoS confidence score.
5. Recent events are stored in SQLite for the last 24 hours.
6. Connected clients receive an initial snapshot and live deltas over WebSocket.
7. A Next.js frontend renders arcs, counters, country rankings, attack type breakdowns, and a recent events feed.

This is not a full SIEM, SOC platform, or authoritative attribution system. It is a live visualization and engineering showcase that combines data ingestion, geolocation, ML confidence scoring, WebSockets, and WebGL.

## 2. Success Criteria

The finished project is successful when:

- The backend can run as one FastAPI process on Railway.
- The frontend can run as a static-ish Next.js shell on Vercel.
- The system works without Celery, Redis, Postgres, Kafka, or paid infrastructure.
- New events appear on the globe without manual refresh.
- The dashboard remains usable when a source API is slow, unavailable, or rate-limited.
- The README explains the architecture, data sources, ML features, setup, deployment, and limitations in plain language.
- A recruiter or reviewer can understand the data pipeline and see the live globe in action within one minute.

## 3. Non-Goals

- No user accounts or authentication.
- No payment, billing, or multi-tenant features.
- No long-term historical analytics beyond a rolling 24-hour SQLite window.
- No claim that every event is a confirmed DDoS incident.
- No backend worker fleet, queue system, or streaming platform.
- No SSR dependency for the globe page.
- No paid managed database.

## 4. Architecture Overview

### Runtime Topology

- Backend: FastAPI on Railway.
- Frontend: Next.js 14 App Router on Vercel.
- Storage: SQLite file mounted on a Railway persistent volume in production.
- Scheduler: APScheduler inside the FastAPI process.
- Realtime: FastAPI WebSocket endpoint.
- Visualization: three.js globe via Aceternity Globe or equivalent wrapper.
- State: Zustand store on the frontend.
- Charts: Recharts.
- Styling: Tailwind CSS plus shadcn/ui in dark mode.

### Data Flow

1. APScheduler triggers a poll every `POLL_INTERVAL_SECONDS` seconds, default `60`.
2. Fetchers call Cloudflare Radar, AbuseIPDB, and GreyNoise using async `httpx`.
3. Source responses are normalized into candidate attack events.
4. Candidate events are geolocated with MaxMind GeoLite2.
5. Feature engineering converts source signals into scorer inputs.
6. The ML scorer returns `score` in the range `0.0` to `1.0`.
7. Events below `MIN_EVENT_SCORE`, default `0.5`, are ignored for live broadcast.
8. Accepted events are inserted into SQLite.
9. Rows older than `EVENT_TTL_HOURS`, default `24`, are purged after each poll.
10. `GET /api/snapshot` returns recent events.
11. `WS /ws/attacks` sends a snapshot on connect and then event deltas after every poll.
12. The frontend WebSocket hook hydrates and appends events into Zustand.
13. The globe renders animated arcs from attacker/source location to target location.
14. Sidebar components derive stats from the Zustand event list.

## 5. Key Architecture Decisions

### Single Process Backend

Use FastAPI, APScheduler, and WebSockets in the same process. This keeps Railway hosting simple and cheap. Avoid Celery and Redis unless the project later outgrows free-tier constraints.

### SQLite Persistence

Use SQLite with `aiosqlite`. In development, the database can live under `backend/data/events.db`. In production, mount a Railway persistent volume and point `DDOS_DB_PATH` at that mounted path.

Do not rely on Railway ephemeral disk for production persistence. Ephemeral disk is acceptable for early smoke tests only.

### Offline Geolocation

Use MaxMind GeoLite2 City or Country database through `geoip2`. The `.mmdb` file should be available to the backend at startup via `MAXMIND_DB_PATH`.

If licensing or repository size makes committing the `.mmdb` file inappropriate, document a setup step and keep the file out of git.

### ML Scoring Scope

The model predicts confidence that a normalized signal is DDoS-relevant. It does not prove an attack occurred. The UI and README must use confidence language, not certainty language.

Use a pre-trained `joblib` artifact loaded once at FastAPI startup. If the model is missing in development, the backend may use a deterministic heuristic scorer, but production should load the trained artifact.

### Cloudflare Radar Granularity

Cloudflare Radar is country/traffic-trend oriented, not necessarily per-IP. Use it as a trend and geography signal. AbuseIPDB and GreyNoise should provide stronger per-IP reputation and scanner signals.

If a source does not provide an IP address, store `ip = null`, set `source` clearly, and still allow a country-level aggregate event if it is useful for the globe.

## 6. Proposed Repository Layout

The repo can start as a two-app workspace:

```text
live-ddos-map/
  SPEC.md
  README.md
  backend/
    pyproject.toml
    app/
      __init__.py
      main.py
      config.py
      db.py
      schemas.py
      scheduler.py
      connection_manager.py
      services/
        fetch_cloudflare.py
        fetch_abuseipdb.py
        fetch_greynoise.py
        geo.py
        scorer.py
        normalizer.py
      ml/
        model.joblib
        features.json
      data/
        .gitkeep
    scripts/
      train_model.py
      collect_training_data.py
    tests/
      test_health.py
      test_snapshot.py
      test_normalizer.py
      test_scorer.py
  frontend/
    package.json
    next.config.mjs
    tailwind.config.ts
    app/
      layout.tsx
      page.tsx
      globals.css
    components/
      GlobeView.tsx
      Sidebar.tsx
      StatusBar.tsx
      EventFeed.tsx
      CountryLeaderboard.tsx
      AttackTypeChart.tsx
    hooks/
      useAttackWebSocket.ts
    lib/
      api.ts
      types.ts
    store/
      useAttackStore.ts
  .github/
    workflows/
      ci.yml
```

Agents may adjust the structure to match chosen tooling, but should preserve the backend/frontend boundary and keep source-specific logic isolated.

## 7. Environment Variables

### Backend

| Name | Required | Default | Purpose |
| --- | --- | --- | --- |
| `DDOS_DB_PATH` | no | `backend/data/events.db` | SQLite file path. |
| `MAXMIND_DB_PATH` | yes for geo | none | Path to GeoLite2 `.mmdb`. |
| `ABUSEIPDB_KEY` | yes for AbuseIPDB | none | AbuseIPDB API key. |
| `GREYNOISE_KEY` | yes for GreyNoise | none | GreyNoise API key. |
| `WS_ALLOWED_ORIGINS` | yes in prod | `http://localhost:3000` | Comma-separated CORS/WebSocket origins. |
| `POLL_INTERVAL_SECONDS` | no | `60` | Scheduler interval. |
| `EVENT_TTL_HOURS` | no | `24` | Rolling event retention window. |
| `MIN_EVENT_SCORE` | no | `0.5` | Minimum score to broadcast/store as live event. |
| `MODEL_PATH` | no | `backend/app/ml/model.joblib` | ML model artifact path. |
| `ENABLE_HEURISTIC_SCORER` | no | `true` in dev | Allows fallback if model is unavailable. |
| `ENABLE_SCHEDULER` | no | `true` | Starts the in-process APScheduler poll loop. Disable in tests. |
| `SOURCE_TIMEOUT_SECONDS` | no | `10` | Per-request timeout for external source fetchers. |
| `ABUSEIPDB_BLACKLIST_LIMIT` | no | `50` | Maximum AbuseIPDB blacklist rows to fetch per poll. |
| `GREYNOISE_LOOKUP_LIMIT` | no | `25` | Maximum candidate IPs to enrich through GreyNoise per poll. |
| `TARGET_LAT` | no | backend host/demo city | Arc target latitude. |
| `TARGET_LNG` | no | backend host/demo city | Arc target longitude. |
| `LOG_LEVEL` | no | `INFO` | Runtime logging verbosity. |

### Frontend

| Name | Required | Default | Purpose |
| --- | --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | yes | `http://localhost:8000` | Backend REST base URL. |
| `NEXT_PUBLIC_WS_URL` | yes | `ws://localhost:8000/ws/attacks` | Backend WebSocket URL. |

## 8. Backend Data Model

Use one main `events` table for the rolling live feed.

```sql
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
```

Field notes:

- `lat` and `lng` represent the source/attacker or aggregate source geography.
- `ip` may be null for aggregate country-level signals.
- `type` should be one of `volumetric`, `amplification`, `application`, `scanner`, or `unknown`.
- `source` should be one of `cloudflare_radar`, `abuseipdb`, `greynoise`, or `combined`.
- `ts` must be ISO 8601 UTC.
- `features_json` is useful for debugging and ML transparency, but should stay compact.

## 9. API Contracts

### `GET /health`

Smoke-test endpoint.

Response:

```json
{
  "status": "ok",
  "service": "live-ddos-map-backend"
}
```

Acceptance:

- Returns HTTP 200.
- Does not require database or external API calls.

### `GET /api/snapshot`

Returns recent events in descending or ascending time order. The frontend should be able to render the result directly.

Query params:

- `limit`: optional integer, default `200`, max `500`.

Response:

```json
{
  "events": [
    {
      "id": 123,
      "ip": "203.0.113.10",
      "startLat": 35.6895,
      "startLng": 139.6917,
      "endLat": 37.7749,
      "endLng": -122.4194,
      "country": "Japan",
      "countryCode": "JP",
      "asn": "AS64500",
      "score": 0.84,
      "type": "volumetric",
      "source": "combined",
      "ts": "2026-06-06T12:00:00Z"
    }
  ]
}
```

Mapping:

- Database `lat` becomes API `startLat`.
- Database `lng` becomes API `startLng`.
- API `endLat` and `endLng` come from configured demo target location.

Acceptance:

- Returns HTTP 200 with an empty list when no data exists.
- Applies limit safely.
- Does not expose raw API responses or secrets.

### `WS /ws/attacks`

Realtime endpoint for the frontend.

On connect, send:

```json
{
  "kind": "snapshot",
  "events": []
}
```

After each poll, send only new accepted events:

```json
{
  "kind": "events",
  "events": []
}
```

Optional heartbeat:

```json
{
  "kind": "heartbeat",
  "ts": "2026-06-06T12:00:00Z"
}
```

Acceptance:

- Multiple clients can connect at the same time.
- A slow or disconnected client does not break polling.
- New clients see recent data immediately through the initial snapshot.
- CORS and WebSocket origin settings allow Vercel and localhost only.

## 10. Source Normalization

All fetchers should return a common candidate shape before database insertion:

```python
class CandidateEvent(BaseModel):
    ip: str | None
    lat: float | None
    lng: float | None
    country: str | None
    country_code: str | None
    asn: str | None
    source: str
    raw_source_id: str | None
    type_hint: str | None
    source_confidence: float
    features: dict[str, float | int | str | bool | None]
    ts: datetime
```

Normalizer responsibilities:

- Deduplicate obvious duplicates within a poll cycle.
- Prefer explicit source IP geolocation when available.
- Fall back to country centroid only for aggregate signals.
- Clamp all confidence values to `0.0` through `1.0`.
- Convert timestamps to UTC ISO 8601.
- Mark unclear attack types as `unknown`.

## 11. ML Confidence Scorer

### Feature Inputs

Initial feature set:

- AbuseIPDB confidence score.
- GreyNoise classification encoded as numeric features.
- Number of sources reporting the same IP or region.
- Cloudflare Radar country trend intensity, if applicable.
- ASN entropy or ASN risk proxy.
- IP has public routable address.
- Source age/freshness in minutes.
- Attack type hint.

The Phase 2 implementation keeps the exact ordered feature contract in
`backend/app/ml/features.json` and mirrors it in `backend/app/services/features.py`.
Any agent changing feature extraction must update both and keep the artifact
sync test passing.

### Model

Use `sklearn.ensemble.GradientBoostingClassifier` as the preferred baseline. Logistic regression is acceptable if training data is sparse and performance is easier to explain.

Artifacts:

- `model.joblib`: serialized trained model.
- `features.json`: ordered feature names and preprocessing details.
- `metrics.json`: training/validation metrics.

The first committed model may be a deterministic synthetic-seed baseline created
by `backend/scripts/train_model.py`. Treat it as a development artifact and
replace it with real labeled examples from `backend/scripts/collect_training_data.py`
before presenting the score as production-quality.

### Fallback Heuristic

Development fallback is allowed:

- High AbuseIPDB score increases confidence.
- Malicious GreyNoise classification increases confidence.
- Multiple source agreement increases confidence.
- Recent Cloudflare DDoS trend in the country increases confidence.

The fallback must be deterministic and clearly logged as a fallback.

### Acceptance

- Scorer returns a float from `0.0` to `1.0`.
- Missing optional features do not crash scoring.
- Model is loaded once at startup, not per request.
- A missing model in production should produce a clear startup error unless fallback is explicitly enabled.

## 12. Frontend Requirements

### Main View

The first screen should be the actual live map dashboard, not a marketing landing page.

Required elements:

- Full-viewport dark globe area.
- Animated attack arcs from source coordinates to target coordinates.
- Live connection indicator.
- Total live event count.
- Top countries list.
- Attack type breakdown.
- Recent events feed.
- Small "How it works" overlay or modal explaining data sources and confidence scoring.

### Globe

Use Aceternity Globe or a similar three.js-based component. Import the globe dynamically with SSR disabled:

```tsx
const Globe = dynamic(() => import("./GlobeView"), { ssr: false });
```

Arc visual rules:

- `volumetric`: red.
- `amplification`: amber.
- `application`: purple.
- `scanner`: blue.
- `unknown`: neutral gray.
- Opacity maps to score, with lower score appearing fainter.

### State

Use Zustand with this minimum store shape:

```ts
type AttackStore = {
  events: AttackEvent[];
  status: "connecting" | "open" | "closed" | "error";
  lastMessageAt: string | null;
  hydrate: (events: AttackEvent[]) => void;
  addEvents: (events: AttackEvent[]) => void;
  setStatus: (status: AttackStore["status"]) => void;
};
```

Store behavior:

- Keep at most the latest 500 events in memory.
- Deduplicate by `id`.
- Batch incoming events for up to 2 seconds before forcing expensive globe updates.

### WebSocket Hook

`useAttackWebSocket` responsibilities:

- Connect on mount.
- Hydrate store from `snapshot`.
- Append events from `events`.
- Reconnect with exponential backoff.
- Update connection status.
- Fall back to `GET /api/snapshot` if WebSocket fails repeatedly.

## 13. Quality Requirements

### Backend

- Use async `httpx` for network calls.
- Give each source a timeout.
- Log poll start, source counts, inserted count, broadcast count, and errors.
- A failing source must not fail the whole poll cycle.
- Purge old rows every poll cycle.
- Use typed Pydantic response models.
- Keep source API keys out of logs.

### Frontend

- No SSR crash from three.js.
- No layout shift when events arrive.
- No visible card-inside-card nesting.
- Dark threat-map theme, but avoid a one-note single-hue palette.
- Text must fit on mobile and desktop.
- Sidebar should remain readable on laptop widths.
- The dashboard must still show an empty/loading state gracefully.

### Documentation

README must include:

- Problem statement.
- Architecture diagram image.
- Local setup.
- Environment variables.
- Data source notes.
- ML scoring explanation.
- Deployment steps for Railway and Vercel.
- Known limitations.

## 14. Phase 1 Spec - Backend Skeleton And Data Pipeline

Estimated time: 3-4 days  
Primary outcome: real data flows into SQLite and snapshot API works.

### Scope

Build the FastAPI backend, local SQLite persistence, source fetcher interfaces, geolocation utility, scheduler, normalization pipeline, and snapshot endpoint.

### Tasks

- Scaffold Python backend with `uv` or Poetry.
- Add FastAPI app entrypoint.
- Add `GET /health`.
- Add settings loader in `config.py`.
- Add SQLite initialization and repository helpers.
- Add `events` schema and indexes.
- Add Pydantic schemas for database/API events.
- Add MaxMind geolocation service.
- Add async fetcher modules for Cloudflare Radar, AbuseIPDB, and GreyNoise.
- Add source normalization into `CandidateEvent`.
- Add scheduler that runs every 60 seconds.
- Insert normalized/enriched events into SQLite.
- Purge rows older than 24 hours after every poll.
- Add `GET /api/snapshot`.
- Add basic backend tests for health, snapshot, database insert/read, and normalization.

### Interfaces Produced

- `GET /health`.
- `GET /api/snapshot`.
- `events` SQLite table.
- Source fetcher function contracts.
- Normalized candidate event contract.

### Acceptance Criteria

- `GET /health` returns 200 locally.
- Backend starts without source API keys, with source fetchers logging disabled/skipped status.
- Backend can insert a synthetic event and return it from `/api/snapshot`.
- Scheduler logs poll cycle activity.
- Old rows are purged according to `EVENT_TTL_HOURS`.
- Source fetcher failures are logged but do not crash the app.
- Unit tests pass.

### Agent Notes

Do this phase before frontend work. The frontend depends on stable event shape. Keep any source-specific response parsing inside the relevant fetcher file.

## 15. Phase 2 Spec - ML Confidence Scorer

Estimated time: 2 days  
Primary outcome: each candidate event receives a useful confidence score.

### Scope

Create the training and runtime scoring path. The model can start simple, but the interfaces must be stable.

### Tasks

- Add training data collection script.
- Store raw API examples under a gitignored data folder.
- Define feature extraction in one reusable module.
- Train a `GradientBoostingClassifier` or logistic regression baseline.
- Save `model.joblib`, `features.json`, and `metrics.json`.
- Add runtime scorer service.
- Load model once at startup.
- Add deterministic heuristic fallback for local development.
- Add tests for feature extraction and scorer bounds.
- Wire scorer into the scheduler pipeline before database insertion.

### Interfaces Produced

- `score_candidate(candidate: CandidateEvent) -> float`.
- `extract_features(candidate: CandidateEvent) -> list[float]`.
- Model artifacts in a known path.

### Acceptance Criteria

- Scorer returns values between `0.0` and `1.0`.
- Missing optional source features do not crash scoring.
- Backend logs whether model or heuristic scorer is active.
- Events below `MIN_EVENT_SCORE` are filtered out.
- Model loads once at startup.
- Feature order is documented in `features.json`.

### Agent Notes

The score is a confidence score, not proof. Avoid UI or README language that says an IP definitely launched a DDoS attack.

## 16. Phase 3 Spec - WebSocket Live Push

Estimated time: 1-2 days  
Primary outcome: frontend clients can receive initial data and live deltas.

### Scope

Add WebSocket connection management and broadcast new accepted events after each poll.

### Tasks

- Add `ConnectionManager` class.
- Add `WS /ws/attacks`.
- Send snapshot immediately when a client connects.
- Track active connections.
- Broadcast only new events after each poll.
- Add optional heartbeat message.
- Add origin validation using `WS_ALLOWED_ORIGINS`.
- Add tests or manual smoke script for WebSocket connection.
- Ensure scheduler and WebSocket broadcast share event serialization code.

### Interfaces Produced

- `WS /ws/attacks`.
- WebSocket message contract with `snapshot`, `events`, and optional `heartbeat`.
- Broadcast function used by scheduler.

### Acceptance Criteria

- Client receives snapshot immediately on connect.
- Client receives deltas after scheduler inserts new events.
- Disconnecting one client does not break others.
- Invalid origins are rejected in production configuration.
- WebSocket payload matches the frontend `AttackEvent` type.

### Agent Notes

Do not broadcast the full snapshot after every poll. Broadcast only the delta to prevent needless frontend churn.

## 17. Phase 4 Spec - Frontend Globe And Sidebar

Estimated time: 4-5 days  
Primary outcome: live dashboard UI renders events from the backend.

### Scope

Build the Next.js app, dark dashboard UI, WebSocket integration, globe visualization, and sidebar analytics.

### Tasks

- Scaffold Next.js 14 App Router frontend.
- Configure Tailwind and shadcn/ui.
- Set dark mode as the default.
- Add shared `AttackEvent` TypeScript type.
- Add Zustand attack store.
- Add REST snapshot helper.
- Add `useAttackWebSocket` hook.
- Add dynamic-imported globe component with SSR disabled.
- Render attack arcs by event type and score.
- Add sidebar with:
  - live connection status,
  - event counter,
  - top 5 countries,
  - attack type breakdown,
  - recent 10 events.
- Add Recharts donut or compact chart for type breakdown.
- Add 2-second batching for high-volume event bursts.
- Add empty, loading, disconnected, and error states.
- Add a "How it works" modal or overlay.
- Run a browser smoke test against local backend data.

### Interfaces Consumed

- `GET /api/snapshot`.
- `WS /ws/attacks`.
- `NEXT_PUBLIC_API_URL`.
- `NEXT_PUBLIC_WS_URL`.

### Acceptance Criteria

- Page does not crash under SSR/build because of three.js.
- Dashboard renders with zero events.
- Dashboard hydrates from snapshot.
- Dashboard appends live WebSocket events.
- Globe arcs update without obvious layout shift.
- Sidebar stats update from the same Zustand event list.
- Mobile layout remains usable.
- Frontend build passes.

### Agent Notes

The first screen should be the actual product. Do not build a marketing hero first. Keep visual polish focused on the globe, status, and operational dashboard clarity.

## 18. Phase 5 Spec - Deploy And Portfolio Polish

Estimated time: 1-2 days  
Primary outcome: deployed demo, clear README, and portfolio-ready explanation.

### Scope

Deploy backend and frontend, configure environment variables, document the system, and add final explanatory polish.

### Tasks

- Deploy backend to Railway.
- Mount Railway persistent volume for SQLite and MaxMind file if needed.
- Configure backend env vars:
  - `ABUSEIPDB_KEY`
  - `GREYNOISE_KEY`
  - `MAXMIND_DB_PATH`
  - `DDOS_DB_PATH`
  - `WS_ALLOWED_ORIGINS`
  - scorer/model settings
- Deploy frontend to Vercel.
- Configure frontend env vars:
  - `NEXT_PUBLIC_API_URL`
  - `NEXT_PUBLIC_WS_URL`
- Confirm Vercel can connect to Railway WebSocket.
- Add GitHub Actions CI for backend tests and frontend build.
- Write README.
- Include `ddos-architecture.png` in README.
- Add "How it works" overlay in app.
- Record a 60-second demo video or GIF.
- Add deployment troubleshooting notes.

### Acceptance Criteria

- Production frontend loads.
- Production backend health endpoint returns 200.
- Production WebSocket connects from Vercel to Railway.
- Events appear on the deployed globe.
- README explains architecture and limitations clearly.
- No secrets are committed.
- Demo is understandable without the developer present.

### Agent Notes

Prioritize reliability and explanation over adding new features. This phase is where the project becomes portfolio material.

## 19. Cross-Phase Testing Strategy

Backend:

- Unit tests for config, normalization, feature extraction, scorer, and database repository.
- Integration tests for `/health` and `/api/snapshot`.
- Mock network calls for source fetchers.
- WebSocket smoke test for connect, snapshot, and delta.

Frontend:

- Type check and production build.
- Store reducer/action tests if test tooling is added.
- Browser smoke test for dashboard rendering.
- Manual check for empty state, disconnected state, and live event append.

End to end:

- Run backend locally with synthetic events.
- Run frontend locally against backend.
- Confirm snapshot and WebSocket flows.
- Confirm deployed Vercel app connects to deployed Railway backend.

## 20. Agent Development Rules

Every AI agent working on this repo should:

- Read this file before implementing.
- Identify the active phase before editing.
- Keep changes scoped to the active phase unless a dependency requires otherwise.
- Preserve the API and WebSocket contracts unless updating this spec in the same change.
- Add or update tests for behavior it changes.
- Avoid introducing paid infrastructure or extra services.
- Avoid committing secrets, `.env` files, raw API dumps, SQLite databases, or MaxMind files if licensing/size makes them unsuitable.
- Prefer small, reviewable commits by phase.
- Update README or this spec when implementation decisions differ from the plan.

## 21. Suggested Build Order

1. Phase 1: backend skeleton, schema, scheduler, source interfaces, snapshot.
2. Phase 2: scorer and model artifacts.
3. Phase 3: WebSocket connection manager and deltas.
4. Phase 4: frontend dashboard, globe, Zustand, sidebar.
5. Phase 5: deployment, README, demo polish.

Do not start visual frontend polish before the backend event contract is stable.

## 22. Known Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Source APIs are rate-limited or unavailable. | Timeouts, per-source error handling, cached/synthetic dev events, clear logs. |
| Cloudflare Radar data is aggregate, not per-IP. | Treat it as trend/geography signal; use nullable IP for aggregate events. |
| MaxMind file is missing in production. | Fail clearly or run country-centroid fallback only when explicitly enabled. |
| three.js breaks SSR. | Dynamic import globe with `ssr: false`. |
| WebSocket blocked by CORS/origin config. | Explicit `WS_ALLOWED_ORIGINS` and deploy smoke test. |
| SQLite file disappears on ephemeral disk. | Use Railway persistent volume in production. |
| ML score is interpreted as confirmed attack attribution. | Use confidence wording in UI and README. |
| High event volume causes React churn. | Store cap, dedupe, and 2-second batching before globe updates. |

## 23. Minimum Demo Path

If time is limited, build this path first:

1. Backend with synthetic plus one real source fetcher.
2. SQLite insert and `/api/snapshot`.
3. Heuristic scorer.
4. WebSocket snapshot and deltas.
5. Frontend globe with sidebar stats.
6. README with clear limitations.

This still demonstrates the end-to-end architecture without blocking on perfect ML or every external source.
