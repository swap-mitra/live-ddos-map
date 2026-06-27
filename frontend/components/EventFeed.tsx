"use client";

import { useAttackStore } from "@/store/useAttackStore";

export default function EventFeed() {
  const events = useAttackStore((state) => state.events);
  const recentEvents = events.slice(-10).reverse();

  if (recentEvents.length === 0) {
    return (
      <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
        <h3 className="text-sm font-semibold text-zinc-300 mb-3">
          Recent Events
        </h3>
        <p className="text-xs text-zinc-500">No events yet</p>
      </div>
    );
  }

  const typeColors: Record<string, string> = {
    volumetric: "text-red-400",
    amplification: "text-amber-400",
    application: "text-purple-400",
    scanner: "text-blue-400",
    unknown: "text-gray-400",
  };

  return (
    <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
      <h3 className="text-sm font-semibold text-zinc-300 mb-3">
        Recent Events
      </h3>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {recentEvents.map((event) => (
          <div
            key={event.id}
            className="text-xs p-2 bg-zinc-800 rounded border border-zinc-700"
          >
            <div className="flex items-center justify-between mb-1">
              <span className={`font-semibold ${typeColors[event.type]}`}>
                {event.type}
              </span>
              <span className="text-zinc-500">
                {event.countryCode || "N/A"}
              </span>
            </div>
            <div className="text-zinc-400">
              {event.ip || "Aggregate"} • Score: {event.score.toFixed(2)}
            </div>
            <div className="text-zinc-500 text-[10px] mt-1">
              {new Date(event.ts).toLocaleTimeString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
