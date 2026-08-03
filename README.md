# Live DDoS Map

Live DDoS Map is a real-time DDoS attack visualization dashboard that displays high-risk internet attack signals as animated arcs on a 3D WebGL globe. The project demonstrates a complete data pipeline combining threat intelligence aggregation, geolocation enrichment, ML confidence scoring, WebSocket streaming, and interactive web visualization.

The project is built around one principle: threat intelligence should be observable, scored, and visualized in real time.

## Why This Exists

Security operations teams require high-fidelity, real-time visibility into incoming threats. However, raw threat feeds are often noisy, distributed across multiple proprietary or public APIs, and lack consistent confidence estimation. 

Live DDoS Map changes the ingestion and analysis model. Instead of presenting disjointed and raw IP lists, the system aggregates multiple open-source feeds (Cloudflare Radar, AbuseIPDB, GreyNoise, SANS DShield, and Stamparm's IPsum), geolocates candidate IPs offline using MaxMind GeoLite2, and applies a Gradient Boosting Classifier to score and filter out low-confidence signals before broadcasting the results to an interactive 3D WebGL globe.

This gives the system three practical security properties:

- **Aggregated Intelligence**: Combines global telemetry (Cloudflare Radar) with IP reputation (AbuseIPDB), honeypot/scanner activity (GreyNoise), and top threat lists (SANS DShield, IPsum).
- **ML Confidence Scoring**: A machine learning model filters out low-confidence events before they reach the operator.
- **Low-Latency Streaming**: An active WebSocket connection pushes events and snapshot updates directly to the interactive 3D dashboard.

## System Overview

```mermaid
flowchart LR
  abuse["AbuseIPDB API"]
  cloudflare["Cloudflare Radar API"]
  greynoise["GreyNoise API"]
  dshield["SANS DShield API"]
  ipsum["IPsum Threat Feed"]
  poller["AttackPoller Scheduler"]
  normalizer["Normalizer & Geo Enricher"]
  ml["ML Confidence Scorer"]
  db["SQLite DB (events.db)"]
  ws["WebSocket Manager"]
  ui["Next.js 3D Dashboard"]

  cloudflare --> poller
  abuse --> poller
  greynoise --> poller
  dshield --> poller
  ipsum --> poller
  poller --> normalizer
  normalizer --> ml
  ml -->|confidence >= threshold| db
  db --> ws
  ws -->|real-time push| ui
```

The core backend is designed to be lightweight, single-process, and asynchronous. Most surrounding code exists to make the threat data pipeline visible, testable, and easy to run from local development through production.

## Ingestion & Scoring Lifecycle

```mermaid
sequenceDiagram
  participant Sources as Threat Sources (CF, AbuseIPDB, GreyNoise, DShield, IPsum)
  participant Poller as AttackPoller
  participant Enricher as Normalizer & Geo (MaxMind)
  participant ML as ML Scorer
  participant DB as SQLite DB
  participant WS as WebSocket Manager
  participant UI as Next.js Dashboard

  loop Every 60 Seconds
    Poller->>Sources: Poll candidate event data
    Sources-->>Poller: Raw payload
    Poller->>Enricher: Normalize & Geolocate IP
    Enricher-->>Poller: Geolocated CandidateEvent
    Poller->>ML: Extract features & score event
    ML-->>Poller: Confidence score (0.0-1.0)
    alt Score >= MIN_EVENT_SCORE
      Poller->>DB: Save accepted event (TTL 24h)
      Poller->>WS: Broadcast accepted event
      WS->>UI: Stream new event over WebSocket
      UI->>UI: Render animated arc on 3D Globe
    else Score < MIN_EVENT_SCORE
      Poller->>Poller: Discard low-confidence event
    end
  end
```

The system recognizes three states for ingestion records:

- `Candidate`: A raw event fetched from a threat intelligence source.
- `Accepted`: An event whose ML confidence score meets or exceeds `MIN_EVENT_SCORE`, stored in SQLite and streamed to the frontend.
- `Discarded`: An event that fell below the score threshold and was ignored.

## Pipeline Components

The core application lives under [backend/app](file:///C:/projects/live-ddos-map/backend/app).

Key roles & components:
- `FastAPI application` ([backend/app/main.py](file:///C:/projects/live-ddos-map/backend/app/main.py)): Coordinates HTTP REST endpoints and the WebSocket connection.
- `scheduler` ([backend/app/scheduler.py](file:///C:/projects/live-ddos-map/backend/app/scheduler.py)): Periodic job scheduler (APScheduler) triggering polling routines.
- `database` ([backend/app/db.py](file:///C:/projects/live-ddos-map/backend/app/db.py)): Manages asynchronous connections to the local SQLite database.
- `connection manager` ([backend/app/connection_manager.py](file:///C:/projects/live-ddos-map/backend/app/connection_manager.py)): Manages active WebSockets and handles broadcasting to active clients.
- `config` ([backend/app/config.py](file:///C:/projects/live-ddos-map/backend/app/config.py)): Handles environment variable definitions and defaults.

Core services:
- `fetchers`: fetch raw signals from [Cloudflare Radar](file:///C:/projects/live-ddos-map/backend/app/services/fetch_cloudflare.py), [AbuseIPDB](file:///C:/projects/live-ddos-map/backend/app/services/fetch_abuseipdb.py), [GreyNoise](file:///C:/projects/live-ddos-map/backend/app/services/fetch_greynoise.py), [SANS DShield](file:///C:/projects/live-ddos-map/backend/app/services/fetch_dshield.py), and [IPsum](file:///C:/projects/live-ddos-map/backend/app/services/fetch_ipsum.py).
- `normalizer` ([backend/app/services/normalizer.py](file:///C:/projects/live-ddos-map/backend/app/services/normalizer.py)): normalizes raw payloads to a standard schema.
- `geolocation` ([backend/app/services/geo.py](file:///C:/projects/live-ddos-map/backend/app/services/geo.py)): queries the MaxMind offline GeoLite2 database.
- `features` ([backend/app/services/features.py](file:///C:/projects/live-ddos-map/backend/app/services/features.py)): extracts model features from candidate events.
- `scorer` ([backend/app/services/scorer.py](file:///C:/projects/live-ddos-map/backend/app/services/scorer.py)): classifies and scores the events with scikit-learn.

## Trust Boundaries

```mermaid
flowchart TB
  subgraph Ingestion["Ingestion Layer (External APIs)"]
    cf["Cloudflare Radar"]
    abuse["AbuseIPDB"]
    gn["GreyNoise"]
    ds["SANS DShield"]
    ip["IPsum"]
  end

  subgraph Processing["Processing & Scoring Layer"]
    geo["MaxMind GeoLite2 (Local DB)"]
    ml["Gradient Boosting Classifier"]
    sqlite["SQLite Local Store"]
  end

  subgraph Distribution["Distribution Layer"]
    fastapi["FastAPI App"]
    ws["WebSocket Server"]
  end

  subgraph Visualization["Client Visualization Layer"]
    ui["Next.js App"]
    globe["WebGL 3D Globe (react-globe.gl / three.js)"]
  end

  cf --> geo
  abuse --> geo
  gn --> geo
  ds --> geo
  ip --> geo
  geo --> ml
  ml --> sqlite
  sqlite --> fastapi
  fastapi --> ws
  ws --> ui
  ui --> globe
```

The system ingests raw untrusted threat intelligence data. Geolocation, ML feature extraction, and ML scoring act as security boundaries to prevent noise and bad telemetry from reaching the persistence layer (SQLite) and active visualization dashboards.

## Repository Layout

- [backend](file:///C:/projects/live-ddos-map/backend): FastAPI backend, database handling, and ML scoring.
- [frontend](file:///C:/projects/live-ddos-map/frontend): Next.js app with App Router and WebGL Globe dashboard.

Important scripts:
- [train_model.py](file:///C:/projects/live-ddos-map/backend/scripts/train_model.py): script for training the Gradient Boosting Classifier.
- [collect_training_data.py](file:///C:/projects/live-ddos-map/backend/scripts/collect_training_data.py): script for accumulating threat feeds for training.
- [test_websocket_manual.py](file:///C:/projects/live-ddos-map/backend/scripts/test_websocket_manual.py): terminal script for testing live WebSockets.

## Features

- Real-Time 3D WebGL Globe visualization using react-globe.gl / three.js, with animated attack arcs, impact rings, and zoom/rotate camera controls
- Multi-source intelligence polling (AbuseIPDB, GreyNoise, Cloudflare Radar, SANS DShield, and Stamparm's IPsum)
- Machine Learning (Gradient Boosting Classifier) confidence estimation
- Offline city-level IP geolocation using MaxMind GeoLite2
- SQLite database persistent storage with a rolling 24-hour retention window (automatic pruning)
- Dynamic WebSocket subscription broadcasting snapshot and delta payloads
- Interactive sidebar analytics with country rankings and attack type charts
- Single-process backend architecture, optimizing resource usage

## Local Development

Install dependencies and set up the environment:

### Backend Setup

1. Navigate to the backend directory:
```powershell
cd backend
```

2. Install backend dependencies:
```powershell
pip install -e ".[dev]"
```

3. Download the MaxMind GeoLite2 City database:
   - Sign up for a free account at [MaxMind](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data).
   - Download `GeoLite2-City.mmdb` and place it in the `backend/data` directory (e.g. `backend/data/GeoLite2-City.mmdb`).

4. Copy the environment configuration:
```powershell
copy .env.example .env
```
Ensure variables such as `ABUSEIPDB_KEY` and `GREYNOISE_KEY` are configured.

5. Run the FastAPI development server:
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. Navigate to the frontend directory:
```powershell
cd ../frontend
```

2. Install frontend dependencies:
```powershell
npm install
```

3. Copy the environment configuration:
```powershell
copy .env.local.example .env.local
```

4. Run the Next.js development server:
```powershell
npm run dev
```

The frontend will be available locally at `http://localhost:3000`.

## ML Confidence Scoring

### Feature Engineering

The confidence scorer translates candidate events into 21-dimensional numeric feature vectors:
1. **source_confidence**: Source-reported/inferred adapter confidence score (0.0 to 1.0)
2. **abuse_confidence_score**: Normalized AbuseIPDB confidence (0.0 to 1.0)
3. **greynoise_malicious**: Binary flag for GreyNoise malicious classification
4. **greynoise_suspicious**: Binary flag for GreyNoise suspicious classification
5. **greynoise_benign**: Binary flag for GreyNoise benign classification
6. **greynoise_noise**: Binary flag for GreyNoise internet background noise
7. **greynoise_riot**: Binary flag for GreyNoise common business services (RIOT)
8. **source_count**: Number of unique intelligence sources reporting the same event (1 to 5)
9. **cloudflare_ddos_trend**: Binary flag indicating active Cloudflare Radar DDoS trend
10. **cloudflare_latest_value_log**: Log-scaled Cloudflare Radar trend bucket value
11. **has_ip**: Binary flag indicating if candidate has an IP address
12. **has_asn**: Binary flag indicating presence of ASN metadata
13. **has_country**: Binary flag indicating presence of country metadata
14. **type_volumetric**: One-hot flag for Volumetric attack type hint
15. **type_amplification**: One-hot flag for Amplification attack type hint
16. **type_application**: One-hot flag for Application-layer attack type hint
17. **type_scanner**: One-hot flag for Scanner/reconnaissance attack type hint
18. **source_abuseipdb**: One-hot flag indicating AbuseIPDB origin
19. **source_greynoise**: One-hot flag indicating GreyNoise origin
20. **source_cloudflare_radar**: One-hot flag indicating Cloudflare Radar origin
21. **event_age_minutes**: Freshness in minutes (0 to 1440, capped at 24 hours)

Feature mappings and preparation are defined in [backend/app/services/features.py](file:///C:/projects/live-ddos-map/backend/app/services/features.py).

### Training Model

To train the model on local training data, run the model training script:
```powershell
python scripts/train_model.py
```
This generates the following artifacts:
- `backend/app/ml/model.joblib` - Serialized scikit-learn model
- `backend/app/ml/features.json` - Feature names and preprocessing metadata
- `backend/app/ml/metrics.json` - Training/validation performance metrics

### Heuristic Fallback

If the ML model is disabled or unavailable, you can use a deterministic fallback scoring mechanism by configuring:
```env
ENABLE_HEURISTIC_SCORER=true
```

## API Reference

### `GET /health`
Returns pipeline health status.

**Response:**
```json
{
  "status": "ok",
  "service": "live-ddos-map-backend"
}
```

### `GET /api/snapshot`
Returns the recent list of attacks from the rolling SQLite window.

**Query Parameters:**
- `limit` (optional): Max events to return (default: 200, max: 500)

**Response:**
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
      "ts": "2026-07-08T12:00:00Z"
    }
  ]
}
```

### `WS /ws/attacks`
Maintains a WebSocket channel for streaming live events.

**Initial Snapshot Payload:**
```json
{
  "kind": "snapshot",
  "events": [...]
}
```

**Live Delta Payload:**
```json
{
  "kind": "events",
  "events": [...]
}
```

## Public Deployment

Both the backend and frontend are connected directly to this GitHub repository on Render and Vercel respectively. Each push to `main` triggers its own build and deploy automatically — there is no separate deploy step in GitHub Actions; CI (`.github/workflows/ci.yml`) only runs tests and a build check.

### Backend Deployment (Render)
1. Create a new Web Service on Render, connect it to this GitHub repository, and set the root directory to `backend` so Render builds `backend/Dockerfile`.
2. Add a persistent disk mounted at `/data` for the SQLite database (and the MaxMind `.mmdb` file if using local-database geolocation mode instead of the web service mode).
3. Configure environment variables in the Render dashboard matching `.env.example`, including `WS_ALLOWED_ORIGINS` set to the deployed Vercel domain.
4. Render builds the container and runs `uvicorn app.main:app --host 0.0.0.0 --port $PORT` automatically (see `backend/Dockerfile`); no manual start command configuration is required.

### Frontend Deployment (Vercel)
1. Import the project into Vercel and set the root directory to `frontend`.
2. Configure `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL` to point to the deployed Render backend (e.g. `https://your-service.onrender.com` and `wss://your-service.onrender.com/ws/attacks`).

## Security & Limitations

- **Confidence scores are probabilistic**: Scores estimate the likelihood of active attack behavior; they do not serve as definitive proof.
- **Single-process backend**: SQLite is designed for light workloads and 60-second polling intervals. It is not suitable for high-throughput write workloads.
- **Unauthenticated dashboard**: The visualization dashboard is public and has no access control features.
- **MaxMind GeoLite2 Accuracy**: Free database has ~80% city-level accuracy.

## Verification

Run backend unit and integration tests:
```powershell
pytest
```

Build the frontend to verify compilation:
```powershell
npm run build
```

Run a manual socket subscription validation:
```powershell
python scripts/test_websocket_manual.py
```

## Attribution

Globe textures (`frontend/public/textures/`) are the [three-globe](https://github.com/vasturiano/three-globe) example
imagery, derived from NASA Blue Marble / Black Marble. `earth-night.jpg` is the Black Marble night-lights composite;
`night-sky.png` is the starfield backdrop.
