"use client";

import { useAttackWebSocket } from "@/hooks/useAttackWebSocket";
import StatusBar from "@/components/StatusBar";
import CountryLeaderboard from "@/components/CountryLeaderboard";
import AttackTypeChart from "@/components/AttackTypeChart";
import EventFeed from "@/components/EventFeed";
import dynamic from "next/dynamic";

const GlobeView = dynamic(() => import("@/components/GlobeView"), {
  ssr: false,
});

export default function Home() {
  useAttackWebSocket();

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-black font-sans select-none text-zinc-100">
      {/* 1. Immersive Full-screen Globe Background */}
      <div className="absolute inset-0 w-full h-full z-0">
        <GlobeView />
      </div>

      {/* 2. Cyber HUD Grid and Scanline Overlay */}
      <div className="absolute inset-0 pointer-events-none z-10 bg-[linear-gradient(to_bottom,rgba(255,255,255,0.015)_1px,transparent_1px)] bg-[size:100%_6px] mix-blend-overlay opacity-60" />
      <div className="absolute inset-0 pointer-events-none z-10 bg-radial-gradient" 
        style={{
          background: "radial-gradient(circle at center, transparent 40%, rgba(3, 3, 5, 0.7) 80%, rgba(3, 3, 5, 0.95) 100%)"
        }}
      />

      {/* 3. Floating Glassmorphic Control Bar (Top) */}
      <div className="absolute top-4 left-4 right-4 z-30 pointer-events-auto">
        <StatusBar />
      </div>

      {/* 4. Floating Left Panel: Statistics & Analytics (Hidden on small screens) */}
      <div className="absolute left-4 top-20 bottom-4 w-80 lg:w-96 flex flex-col gap-4 z-20 overflow-y-auto pointer-events-auto pr-2 py-1 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent hidden md:flex">
        <CountryLeaderboard />
        <AttackTypeChart />
      </div>

      {/* 5. Floating Right Panel: Live Monitoring Logs (Hidden on small screens) */}
      <div className="absolute right-4 top-20 bottom-4 w-80 lg:w-96 flex-col z-20 overflow-y-auto pointer-events-auto pl-2 py-1 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent hidden md:flex">
        <div className="flex-1 flex flex-col h-full">
          <EventFeed />
        </div>
      </div>
    </div>
  );
}
