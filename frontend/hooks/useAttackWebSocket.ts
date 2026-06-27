import { useEffect, useRef, useCallback } from "react";
import { useAttackStore } from "@/store/useAttackStore";
import { getWebSocketURL, fetchSnapshot } from "@/lib/api";
import type { WebSocketMessage } from "@/lib/types";

const RECONNECT_DELAYS = [1000, 2000, 5000, 10000, 30000];
const MAX_RECONNECT_ATTEMPTS = 5;

export function useAttackWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const mountedRef = useRef(true);

  const { hydrate, addEvents, setStatus } = useAttackStore();

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
            addEvents(message.events);
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
  }, [hydrate, addEvents, setStatus]);

  const fallbackToSnapshot = useCallback(async () => {
    try {
      const data = await fetchSnapshot();
      hydrate(data.events);
      setStatus("closed");
    } catch (error) {
      console.error("Failed to fetch snapshot fallback:", error);
    }
  }, [hydrate, setStatus]);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);
}
