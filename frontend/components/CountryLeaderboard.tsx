"use client";

import { useAttackStore } from "@/store/useAttackStore";
import { useMemo } from "react";

export default function CountryLeaderboard() {
  const events = useAttackStore((state) => state.events);

  const topCountries = useMemo(() => {
    const countryMap = new Map<string, { name: string; count: number }>();

    events.forEach((event) => {
      if (event.countryCode && event.country) {
        const existing = countryMap.get(event.countryCode);
        if (existing) {
          existing.count += 1;
        } else {
          countryMap.set(event.countryCode, {
            name: event.country,
            count: 1,
          });
        }
      }
    });

    return Array.from(countryMap.entries())
      .map(([code, data]) => ({
        code,
        name: data.name,
        count: data.count,
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);
  }, [events]);

  if (topCountries.length === 0) {
    return (
      <div className="relative bg-zinc-950/65 backdrop-blur-xl border border-zinc-800/80 rounded-lg p-4 shadow-[0_0_20px_rgba(0,0,0,0.85)]">
        <div className="absolute top-0 left-0 w-2 h-2 border-t-2 border-l-2 border-zinc-700" />
        <div className="absolute top-0 right-0 w-2 h-2 border-t-2 border-r-2 border-zinc-700" />
        <h3 className="text-xs font-mono font-bold text-zinc-400 tracking-wider mb-3 uppercase">
          // GEOGRAPHIC LEADERBOARD
        </h3>
        <p className="text-xs font-mono text-zinc-500">NO INCIDENTS REGISTERED</p>
      </div>
    );
  }

  const maxCount = topCountries[0].count;

  return (
    <div className="relative bg-zinc-950/65 backdrop-blur-xl border border-zinc-800/80 rounded-lg p-4 shadow-[0_0_20px_rgba(0,0,0,0.85)] overflow-hidden">
      {/* HUD Corner Ticks */}
      <div className="absolute top-0 left-0 w-2 h-2 border-t-2 border-l-2 border-red-500/70" />
      <div className="absolute top-0 right-0 w-2 h-2 border-t-2 border-r-2 border-red-500/70" />
      <div className="absolute bottom-0 left-0 w-2 h-2 border-b-2 border-l-2 border-red-500/70" />
      <div className="absolute bottom-0 right-0 w-2 h-2 border-b-2 border-r-2 border-red-500/70" />

      <h3 className="text-xs font-mono font-bold text-red-500 tracking-wider mb-4 uppercase">
        // GEOGRAPHIC LEADERBOARD
      </h3>
      <div className="space-y-3">
        {topCountries.map((country, index) => (
          <div key={country.code} className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between text-[11px] font-mono">
              <span className="text-zinc-300 font-bold">
                {index + 1}. {country.name.toUpperCase()} ({country.code})
              </span>
              <span className="text-red-400 font-bold">{country.count} DETECTIONS</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-zinc-900 border border-zinc-800/80 rounded h-2 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-red-600 to-red-500 h-full transition-all duration-700 shadow-[0_0_6px_#ef4444]"
                  style={{
                    width: `${(country.count / maxCount) * 100}%`,
                  }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
