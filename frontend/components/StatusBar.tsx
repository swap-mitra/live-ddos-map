"use client";

import { useState } from "react";
import { useAttackStore } from "@/store/useAttackStore";

export default function StatusBar() {
  const status = useAttackStore((state) => state.status);
  const events = useAttackStore((state) => state.events);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const statusColors = {
    connecting: "bg-yellow-500 shadow-[0_0_8px_#eab308]",
    open: "bg-green-500 shadow-[0_0_8px_#22c55e]",
    closed: "bg-zinc-500 shadow-[0_0_8px_#71717a]",
    error: "bg-red-500 shadow-[0_0_8px_#ef4444]",
  };

  const statusLabels = {
    connecting: "CONNECTING TO FEED...",
    open: "LIVE STREAM ACTIVE",
    closed: "FEED OFFLINE",
    error: "CONNECTION ERROR",
  };

  return (
    <div className="relative flex items-center justify-between px-6 py-2.5 bg-zinc-950/65 backdrop-blur-xl border border-zinc-800/80 rounded-lg shadow-[0_4px_30px_rgba(0,0,0,0.8)] z-30">
      {/* High-tech Corner Accents */}
      <div className="absolute top-0 left-0 w-2 h-1 border-t border-l border-red-500/70" />
      <div className="absolute top-0 right-0 w-2 h-1 border-t border-r border-red-500/70" />
      <div className="absolute bottom-0 left-0 w-2 h-1 border-b border-l border-red-500/70" />
      <div className="absolute bottom-0 right-0 w-2 h-1 border-b border-r border-red-500/70" />

      <div className="flex items-center gap-6 font-mono text-xs">
        <div className="flex items-center gap-2.5">
          <div
            className={`w-2 h-2 rounded-full ${statusColors[status]} ${
              status === "open" ? "animate-pulse" : ""
            }`}
          />
          <span className="text-zinc-300 font-bold tracking-widest">{statusLabels[status]}</span>
        </div>
        <div className="h-4 w-[1px] bg-zinc-800" />
        <div className="text-zinc-400">
          EVENTS CAPTURED: <span className="text-red-400 font-bold font-mono">{events.length}</span>
        </div>
      </div>
      
      <div className="flex items-center gap-4">
        <button
          onClick={() => setIsModalOpen(true)}
          className="font-mono text-[10px] uppercase tracking-wider px-3 py-1 bg-red-950/20 hover:bg-red-900/30 active:bg-red-950/40 border border-red-900/50 text-red-400 rounded transition-all cursor-pointer font-bold shadow-[0_0_8px_rgba(239,68,68,0.1)]"
        >
          System Info
        </button>
        <div className="text-[10px] font-mono tracking-widest text-zinc-500 select-none uppercase font-bold">CYBER THREAT MAP v0.1</div>
      </div>

      {isModalOpen && (
        <div 
          className="fixed inset-0 bg-black/85 backdrop-blur-md z-50 flex items-center justify-center p-4"
          onClick={() => setIsModalOpen(false)}
        >
          <div 
            className="bg-zinc-950/90 border border-zinc-800 rounded-lg max-w-lg w-full p-6 text-zinc-100 shadow-[0_0_30px_rgba(239,68,68,0.15)] relative"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Corner decorations for modal */}
            <div className="absolute top-0 left-0 w-3.5 h-3.5 border-t-2 border-l-2 border-red-500" />
            <div className="absolute top-0 right-0 w-3.5 h-3.5 border-t-2 border-r-2 border-red-500" />
            <div className="absolute bottom-0 left-0 w-3.5 h-3.5 border-b-2 border-l-2 border-red-500" />
            <div className="absolute bottom-0 right-0 w-3.5 h-3.5 border-b-2 border-r-2 border-red-500" />

            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-4 right-4 text-zinc-400 hover:text-red-400 font-mono text-xs transition-colors cursor-pointer"
              aria-label="Close modal"
            >
              [ ESC ]
            </button>
            <h3 className="text-sm font-mono font-bold tracking-widest border-b border-zinc-850 pb-3 mb-4 text-red-500 flex items-center gap-2 uppercase">
              // THREAT MAP ARCHITECTURE
            </h3>
            
            <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-1 font-mono text-xs">
              <div>
                <h4 className="font-bold text-zinc-300 uppercase mb-1">
                  &gt; Ingestion Engine
                </h4>
                <p className="text-zinc-500 leading-relaxed text-[11px]">
                  Aggregates malicious traffic signals at 60-second intervals from Cloudflare Radar, AbuseIPDB, and GreyNoise.
                </p>
              </div>

              <div>
                <h4 className="font-bold text-zinc-300 uppercase mb-1">
                  &gt; Geo-Enrichment
                </h4>
                <p className="text-zinc-500 leading-relaxed text-[11px]">
                  Enriches incoming IP reports with country codes, ASNs, and coordinates utilizing the MaxMind GeoLite2 Service.
                </p>
              </div>

              <div>
                <h4 className="font-bold text-zinc-300 uppercase mb-1">
                  &gt; ML Classification
                </h4>
                <p className="text-zinc-500 leading-relaxed text-[11px]">
                  Evaluates normalizer features with a Gradient Boosting Classifier. Predicts DDoS score (0.0-1.0) and discards signals &lt; 0.50 score.
                </p>
              </div>

              <div>
                <h4 className="font-bold text-zinc-300 uppercase mb-1">
                  &gt; Visual Broadcast
                </h4>
                <p className="text-zinc-500 leading-relaxed text-[11px]">
                  WebSockets feed deltas to a 3D WebGL globe. Arcs map volumetric (red), amplification (amber), application (purple), and scanner (blue) activity.
                </p>
              </div>
            </div>

            <div className="mt-6 border-t border-zinc-800 pt-4 flex justify-end">
              <button
                onClick={() => setIsModalOpen(false)}
                className="font-mono text-xs px-4 py-1.5 bg-red-950/20 hover:bg-red-900/30 text-red-400 border border-red-900/50 rounded transition-colors cursor-pointer font-bold"
              >
                DISMISS
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
