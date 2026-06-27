"use client";

import { useAttackStore } from "@/store/useAttackStore";

export default function StatusBar() {
  const status = useAttackStore((state) => state.status);
  const events = useAttackStore((state) => state.events);

  const statusColors = {
    connecting: "bg-yellow-500",
    open: "bg-green-500",
    closed: "bg-gray-500",
    error: "bg-red-500",
  };

  const statusLabels = {
    connecting: "Connecting",
    open: "Live",
    closed: "Disconnected",
    error: "Error",
  };

  return (
    <div className="flex items-center justify-between px-6 py-3 bg-zinc-900 border-b border-zinc-800">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${statusColors[status]} ${
              status === "open" ? "animate-pulse" : ""
            }`}
          />
          <span className="text-sm text-zinc-400">{statusLabels[status]}</span>
        </div>
        <div className="text-sm text-zinc-400">
          <span className="text-zinc-200 font-semibold">{events.length}</span>{" "}
          events
        </div>
      </div>
      <div className="text-xs text-zinc-500">Live DDoS Map</div>
    </div>
  );
}
