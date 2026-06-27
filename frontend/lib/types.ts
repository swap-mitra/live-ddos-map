export interface AttackEvent {
  id: number;
  ip: string | null;
  startLat: number;
  startLng: number;
  endLat: number;
  endLng: number;
  country: string | null;
  countryCode: string | null;
  asn: string | null;
  score: number;
  type: "volumetric" | "amplification" | "application" | "scanner" | "unknown";
  source: string;
  ts: string;
}

export interface SnapshotResponse {
  events: AttackEvent[];
}

export interface WebSocketMessage {
  kind: "snapshot" | "events" | "heartbeat";
  events?: AttackEvent[];
  ts?: string;
}

export type ConnectionStatus = "connecting" | "open" | "closed" | "error";
