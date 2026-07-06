"use client";

import { useState } from "react";
import { useAttackStore } from "@/store/useAttackStore";

export default function StatusBar() {
  const status = useAttackStore((state) => state.status);
  const events = useAttackStore((state) => state.events);
  const [isModalOpen, setIsModalOpen] = useState(false);

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
    <div className="flex items-center justify-between px-6 py-3 bg-zinc-900 border-b border-zinc-800 relative z-20">
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
      
      <div className="flex items-center gap-4">
        <button
          onClick={() => setIsModalOpen(true)}
          className="text-xs px-2.5 py-1 bg-zinc-800 hover:bg-zinc-700 active:bg-zinc-800 border border-zinc-700 text-zinc-300 rounded font-medium transition-colors cursor-pointer"
        >
          How it works
        </button>
        <div className="text-xs text-zinc-500 select-none">Live DDoS Map</div>
      </div>

      {isModalOpen && (
        <div 
          className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200"
          onClick={() => setIsModalOpen(false)}
        >
          <div 
            className="bg-zinc-900 border border-zinc-800 rounded-xl max-w-lg w-full p-6 text-zinc-100 shadow-2xl relative animate-in zoom-in-95 duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-4 right-4 text-zinc-400 hover:text-zinc-200 text-lg transition-colors cursor-pointer"
              aria-label="Close modal"
            >
              ✕
            </button>
            <h3 className="text-base font-semibold border-b border-zinc-800 pb-3 mb-4 flex items-center gap-2 text-zinc-100">
              🛡️ How it works
            </h3>
            
            <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
              <div>
                <h4 className="text-xs font-semibold text-red-400 uppercase tracking-wider mb-1">
                  1. Multi-Source Threat Intelligence Ingestion
                </h4>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  Every 60 seconds, the backend polls public threat intelligence APIs, including <strong>Cloudflare Radar</strong> (aggregate country traffic trends), <strong>AbuseIPDB</strong> (community-reported malicious IPs), and <strong>GreyNoise</strong> (internet-wide scanner and attack IP metrics).
                </p>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-amber-500 uppercase tracking-wider mb-1">
                  2. Geolocation Enrichment
                </h4>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  Incoming IP addresses are geolocated using the offline <strong>MaxMind GeoLite2</strong> database to determine coordinates, country codes, and ASNs. If MaxMind API credentials are provided, it accesses the GeoLite2 Web Service.
                </p>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-purple-400 uppercase tracking-wider mb-1">
                  3. Machine Learning Confidence Scoring
                </h4>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  A lightweight <strong>Gradient Boosting Classifier</strong> scores normalized threat signals to predict if they represent active DDoS activity. It evaluates features like AbuseIPDB reports, GreyNoise classifications, source agreements, and Cloudflare trend intensity. Any candidate event with a confidence score below <code>0.50</code> is filtered out.
                </p>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-1">
                  4. Real-time Visualization
                </h4>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  Clients connect to a backend WebSocket stream which pushes the initial 24-hour event history snapshot and then broadcasts delta updates. The frontend uses a dark 3D WebGL globe to map source coordinates as animated markers.
                </p>
              </div>
            </div>

            <div className="mt-6 border-t border-zinc-800 pt-4 flex justify-end">
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-xs px-4 py-2 bg-zinc-800 hover:bg-zinc-700 active:bg-zinc-800 text-zinc-200 border border-zinc-700 rounded transition-colors cursor-pointer font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
