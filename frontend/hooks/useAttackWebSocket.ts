import { useEffect, useRef, useCallback } from "react";
import { useAttackStore } from "@/store/useAttackStore";
import { getWebSocketURL, fetchSnapshot } from "@/lib/api";
import type { WebSocketMessage, AttackEvent } from "@/lib/types";

const RECONNECT_DELAYS = [1000, 2000, 5000, 10000, 30000];
const MAX_RECONNECT_ATTEMPTS = 5;
const FALLBACK_RETRY_INTERVAL_MS = 30000;

export function useAttackWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const mountedRef = useRef(true);
  const eventBufferRef = useRef<AttackEvent[]>([]);
  const batchTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const connectRef = useRef<() => void>(() => {});

  const { hydrate, addEvents, setStatus } = useAttackStore();

  const flushEvents = useCallback(() => {
    if (eventBufferRef.current.length > 0) {
      addEvents(eventBufferRef.current);
      eventBufferRef.current = [];
    }
    batchTimeoutRef.current = null;
  }, [addEvents]);

  const fallbackToSnapshot = useCallback(async () => {
    try {
      const data = await fetchSnapshot();
      if (mountedRef.current) hydrate(data.events);
    } catch (error) {
      console.error("Failed to fetch snapshot fallback:", error);
    }
    if (!mountedRef.current) return;
    setStatus("closed");
    // Don't give up permanently — keep retrying the live connection so the
    // dashboard recovers on its own once the backend/network comes back.
    reconnectTimeoutRef.current = setTimeout(() => {
      reconnectAttemptRef.current = 0;
      connectRef.current();
    }, FALLBACK_RETRY_INTERVAL_MS);
  }, [hydrate, setStatus]);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;

    setStatus("connecting");

    try {
      const ws = new WebSocket(getWebSocketURL());
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) return;
        setStatus("open");
        reconnectAttemptRef.current = 0;
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          if (message.kind === "snapshot" && message.events) {
            hydrate(message.events);
          } else if (message.kind === "events" && message.events) {
            eventBufferRef.current.push(...message.events);
            if (!batchTimeoutRef.current) {
              batchTimeoutRef.current = setTimeout(() => {
                flushEvents();
              }, 2000);
            }
          }
        } catch (error) {
          console.error("Failed to parse WebSocket message:", error);
        }
      };

      ws.onerror = () => {
        if (!mountedRef.current) return;
        setStatus("error");
      };

      ws.onclose = () => {
        if (!mountedRef.current) return;
        setStatus("closed");

        if (reconnectAttemptRef.current < MAX_RECONNECT_ATTEMPTS) {
          const delay =
            RECONNECT_DELAYS[
              Math.min(reconnectAttemptRef.current, RECONNECT_DELAYS.length - 1)
            ];
          reconnectAttemptRef.current += 1;

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        } else {
          fallbackToSnapshot();
        }
      };
    } catch (error) {
      console.error("WebSocket connection failed:", error);
      setStatus("error");
      fallbackToSnapshot();
    }
  }, [setStatus, flushEvents, fallbackToSnapshot]);

  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (batchTimeoutRef.current) {
        clearTimeout(batchTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);
}
