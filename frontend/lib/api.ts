import type { SnapshotResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchSnapshot(limit = 200): Promise<SnapshotResponse> {
  const response = await fetch(`${API_URL}/api/snapshot?limit=${limit}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch snapshot: ${response.statusText}`);
  }
  return response.json();
}

export function getWebSocketURL(): string {
  return process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/attacks";
}
