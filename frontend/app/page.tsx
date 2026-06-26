"use client";

import { useAttackWebSocket } from "@/hooks/useAttackWebSocket";
import StatusBar from "@/components/StatusBar";
import Sidebar from "@/components/Sidebar";
import dynamic from "next/dynamic";

const GlobeView = dynamic(() => import("@/components/GlobeView"), {
  ssr: false,
});

export default function Home() {
  useAttackWebSocket();

  return (
    <div className="flex flex-col h-screen">
      <StatusBar />
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 bg-zinc-950">
          <GlobeView />
        </div>
        <Sidebar />
      </div>
    </div>
  );
}
