"use client";

import { useAttackStore } from "@/store/useAttackStore";

export default function EventFeed() {
  const events = useAttackStore((state) => state.events);
  const recentEvents = events.slice(-30).reverse();

  const typeColors: Record<string, string> = {
    volumetric: "text-red-400 font-bold",
    amplification: "text-amber-500 font-bold",
    application: "text-purple-400 font-bold",
    scanner: "text-cyan-400 font-bold",
    unknown: "text-zinc-500",
  };

  const typeColorsBg: Record<string, string> = {
    volumetric: "rgba(239, 68, 68, 0.05)",
    amplification: "rgba(245, 158, 11, 0.05)",
    application: "rgba(168, 85, 247, 0.05)",
    scanner: "rgba(6, 182, 212, 0.05)",
    unknown: "rgba(113, 113, 122, 0.05)",
  };

  const typeBorders: Record<string, string> = {
    volumetric: "border-red-950/40 hover:border-red-500/30",
    amplification: "border-amber-950/40 hover:border-amber-500/30",
    application: "border-purple-950/40 hover:border-purple-500/30",
    scanner: "border-cyan-950/40 hover:border-cyan-500/30",
    unknown: "border-zinc-800/40 hover:border-zinc-500/30",
  };

  return (
    <div className="relative flex flex-col h-full bg-zinc-950/65 backdrop-blur-xl border border-zinc-800/80 rounded-lg p-4 shadow-[0_0_20px_rgba(0,0,0,0.85)] overflow-hidden">
      {/* HUD Corner Ticks */}
      <div className="absolute top-0 left-0 w-2 h-2 border-t-2 border-l-2 border-red-500/70" />
      <div className="absolute top-0 right-0 w-2 h-2 border-t-2 border-r-2 border-red-500/70" />
      <div className="absolute bottom-0 left-0 w-2 h-2 border-b-2 border-l-2 border-red-500/70" />
      <div className="absolute bottom-0 right-0 w-2 h-2 border-b-2 border-r-2 border-red-500/70" />

      <h3 className="text-xs font-mono font-bold text-red-500 tracking-wider mb-3 uppercase flex-shrink-0">
        // LIVE MONITORING FEED
      </h3>
      
      {recentEvents.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-xs font-mono text-zinc-500 tracking-widest animate-pulse">
            CONNECTING TO NETWORK SOCKET...
          </p>
        </div>
      ) : (
        <div className="flex-1 space-y-2 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
          {recentEvents.map((event) => (
            <div
              key={event.id}
              className={`text-[10px] p-2.5 rounded border font-mono transition-all duration-300 ${typeBorders[event.type]}`}
              style={{
                backgroundColor: typeColorsBg[event.type]
              }}
            >
              <div className="flex items-center justify-between mb-1.5 border-b border-zinc-900 pb-1">
                <span className={`uppercase tracking-wider ${typeColors[event.type]}`}>
                  &gt; {event.type}
                </span>
                <span className="text-zinc-500 text-[9px] font-bold">
                  {event.countryCode || "GLOBAL"}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-1 text-zinc-400">
                <div>
                  IP: <span className="text-zinc-300 font-bold">{event.ip || "AGGREGATED"}</span>
                </div>
                <div className="text-right">
                  CONFIDENCE: <span className="text-red-400 font-bold font-mono">{(event.score * 100).toFixed(0)}%</span>
                </div>
              </div>
              <div className="flex justify-between items-center text-[9px] text-zinc-500 mt-1.5 pt-1 border-t border-zinc-900/50">
                <span>SRC: {event.source.toUpperCase()}</span>
                <span>{new Date(event.ts).toLocaleTimeString()} UTC</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
