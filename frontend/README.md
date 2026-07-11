# Live DDoS Map - Frontend

Real-time DDoS attack visualization dashboard built with Next.js 14, displaying attack events on an interactive 3D globe.

## Features

- **Live WebSocket Connection**: Real-time attack event updates from the backend
- **Interactive 3D Globe**: Animated globe built with COBE showing attack source locations
- **Analytics Dashboard**: 
  - Top countries by attack count
  - Attack type breakdown (volumetric, amplification, application, scanner, unknown)
  - Recent events feed
  - Live connection status
- **Dark Theme**: Optimized for threat operations dashboard aesthetic
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Zustand** - State management
- **COBE** - 3D globe visualization
- **Recharts** - Charts and data visualization
- **WebSocket API** - Real-time data streaming

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx       # Root layout with metadata
│   ├── page.tsx         # Main dashboard page
│   └── globals.css      # Global styles
├── components/
│   ├── GlobeView.tsx    # 3D globe visualization
│   ├── StatusBar.tsx    # Connection status and event count
│   ├── Sidebar.tsx      # Analytics sidebar container
│   ├── CountryLeaderboard.tsx  # Top countries widget
│   ├── AttackTypeChart.tsx     # Attack type breakdown chart
│   └── EventFeed.tsx    # Recent events list
├── hooks/
│   └── useAttackWebSocket.ts   # WebSocket connection hook
├── lib/
│   ├── api.ts           # API client functions
│   └── types.ts         # TypeScript type definitions
└── store/
    └── useAttackStore.ts  # Zustand store for attack events
```

## Environment Variables

Create a `.env.local` file:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/attacks
```

For production deployment on Vercel, set:

```bash
NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
NEXT_PUBLIC_WS_URL=wss://your-backend-url.railway.app/ws/attacks
```

## Development

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Build

Build for production:

```bash
npm run build
```

Start production server:

```bash
npm start
```

## State Management

The application uses Zustand for state management with the following store structure:

```typescript
{
  events: AttackEvent[];           // Array of attack events (max 500)
  status: ConnectionStatus;        // WebSocket connection status
  lastMessageAt: string | null;    // Timestamp of last received message
  hydrate: (events) => void;       // Load initial snapshot
  addEvents: (events) => void;     // Add new events (deduplicated)
  setStatus: (status) => void;     // Update connection status
}
```

## WebSocket Protocol

The frontend connects to `WS /ws/attacks` and expects messages in this format:

**Initial snapshot on connect:**
```json
{
  "kind": "snapshot",
  "events": [...]
}
```

**Live event deltas:**
```json
{
  "kind": "events",
  "events": [...]
}
```

**Heartbeat (optional):**
```json
{
  "kind": "heartbeat",
  "ts": "2026-06-27T00:00:00Z"
}
```

## Event Data Model

```typescript
interface AttackEvent {
  id: number;
  ip: string | null;
  startLat: number;      // Source latitude
  startLng: number;      // Source longitude
  endLat: number;        // Target latitude
  endLng: number;        // Target longitude
  country: string | null;
  countryCode: string | null;
  asn: string | null;
  score: number;         // Confidence score 0.0-1.0
  type: "volumetric" | "amplification" | "application" | "scanner" | "unknown";
  source: string;
  ts: string;            // ISO 8601 timestamp
}
```

## Deployment

### Vercel (Recommended)

1. Connect your GitHub repository to Vercel
2. Configure environment variables in Vercel dashboard
3. Deploy automatically on push to main

### Manual Deployment

```bash
npm run build
npm start
```

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

WebGL is required for the globe visualization.

## Performance

- Maximum 500 events stored in memory
- Events deduplicated by ID
- Globe updates throttled to avoid excessive re-renders
- Dynamic imports for client-only components (SSR disabled for globe)

## Known Limitations

- No arc visualization between source and target coordinates (markers only)
- Maximum 100 markers displayed on globe for performance

## License

See root repository for license information.
