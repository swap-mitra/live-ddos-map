"use client";

import CountryLeaderboard from "./CountryLeaderboard";
import AttackTypeChart from "./AttackTypeChart";
import EventFeed from "./EventFeed";

export default function Sidebar() {
  return (
    <div className="w-full lg:w-96 bg-zinc-950 border-l border-zinc-800 overflow-y-auto">
      <div className="p-4 space-y-4">
        <CountryLeaderboard />
        <AttackTypeChart />
        <EventFeed />
      </div>
    </div>
  );
}
