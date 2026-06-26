import { create } from "zustand";
import type { AttackEvent, ConnectionStatus } from "@/lib/types";

interface AttackStore {
  events: AttackEvent[];
  status: ConnectionStatus;
  lastMessageAt: string | null;
  hydrate: (events: AttackEvent[]) => void;
  addEvents: (events: AttackEvent[]) => void;
  setStatus: (status: ConnectionStatus) => void;
  setLastMessageAt: (ts: string) => void;
}

const MAX_EVENTS = 500;

export const useAttackStore = create<AttackStore>((set) => ({
  events: [],
  status: "connecting",
  lastMessageAt: null,

  hydrate: (events) =>
    set({
      events: events.slice(-MAX_EVENTS),
      lastMessageAt: new Date().toISOString(),
    }),

  addEvents: (newEvents) =>
    set((state) => {
      const existingIds = new Set(state.events.map((e) => e.id));
      const uniqueNewEvents = newEvents.filter((e) => !existingIds.has(e.id));
      const combined = [...state.events, ...uniqueNewEvents];
      return {
        events: combined.slice(-MAX_EVENTS),
        lastMessageAt: new Date().toISOString(),
      };
    }),

  setStatus: (status) => set({ status }),

  setLastMessageAt: (ts) => set({ lastMessageAt: ts }),
}));
