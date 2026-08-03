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

export type AttackType = AttackEvent["type"];

/** Shared by the globe arcs/points and the threat-vector chart legend. */
export const TYPE_COLORS: Record<AttackType, string> = {
  volumetric: "#ef4444", // Neon Red
  amplification: "#f59e0b", // Neon Orange/Amber
  application: "#a855f7", // Neon Purple
  scanner: "#06b6d4", // Neon Cyan
  unknown: "#71717a", // Zinc Gray
};

export interface SnapshotResponse {
  events: AttackEvent[];
}

export interface WebSocketMessage {
  kind: "snapshot" | "events" | "heartbeat";
  events?: AttackEvent[];
  ts?: string;
}

export type ConnectionStatus = "connecting" | "open" | "closed" | "error";
