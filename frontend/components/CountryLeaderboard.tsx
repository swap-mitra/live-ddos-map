"use client";

import { useAttackStore } from "@/store/useAttackStore";
import { useMemo } from "react";

export default function CountryLeaderboard() {
  const events = useAttackStore((state) => state.events);

  const topCountries = useMemo(() => {
    const countryMap = new Map<string, { code: string; count: number }>();

    events.forEach((event) => {
      if (event.countryCode && event.country) {
        const existing = countryMap.get(event.countryCode);
        if (existing) {
          existing.count += 1;
        } else {
          countryMap.set(event.countryCode, {
            code: event.countryCode,
            count: 1,
          });
        }
      }
    });

    return Array.from(countryMap.entries())
      .map(([code, data]) => ({
        code,
        count: data.count,
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);
  }, [events]);

  if (topCountries.length === 0) {
    return (
      <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
        <h3 className="text-sm font-semibold text-zinc-300 mb-3">
          Top Countries
        </h3>
        <p className="text-xs text-zinc-500">No data available</p>
      </div>
    );
  }

  const maxCount = topCountries[0].count;

  return (
    <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
      <h3 className="text-sm font-semibold text-zinc-300 mb-3">
        Top Countries
      </h3>
      <div className="space-y-2">
        {topCountries.map((country) => (
          <div key={country.code} className="flex items-center gap-2">
            <div className="text-xs font-mono text-zinc-400 w-8">
              {country.code}
            </div>
            <div className="flex-1 bg-zinc-800 rounded-full h-2 overflow-hidden">
              <div
                className="bg-red-500 h-full transition-all duration-500"
                style={{
                  width: `${(country.count / maxCount) * 100}%`,
                }}
              />
            </div>
            <div className="text-xs text-zinc-400 w-8 text-right">
              {country.count}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
