"use client";

import { useAttackStore } from "@/store/useAttackStore";
import { useMemo } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { TYPE_COLORS, type AttackType } from "@/lib/types";

const TYPE_LABELS: Record<string, string> = {
  volumetric: "VOLUMETRIC ATTACK",
  amplification: "AMPLIFICATION VECTOR",
  application: "APPLICATION OVERFLOW",
  scanner: "INTERNET PORTS SCANNER",
  unknown: "UNRESOLVED THREAT SIGNAL",
};

export default function AttackTypeChart() {
  const events = useAttackStore((state) => state.events);

  const chartData = useMemo(() => {
    const typeMap = new Map<string, number>();

    events.forEach((event) => {
      const current = typeMap.get(event.type) || 0;
      typeMap.set(event.type, current + 1);
    });

    return Array.from(typeMap.entries())
      .map(([type, count]) => ({
        name: TYPE_LABELS[type] || type,
        value: count,
        color: TYPE_COLORS[type as AttackType] || TYPE_COLORS.unknown,
      }))
      .sort((a, b) => b.value - a.value);
  }, [events]);

  if (chartData.length === 0) {
    return (
      <div className="relative bg-zinc-950/65 backdrop-blur-xl border border-zinc-800/80 rounded-lg p-4 shadow-[0_0_20px_rgba(0,0,0,0.85)]">
        <div className="absolute top-0 left-0 w-2 h-2 border-t-2 border-l-2 border-zinc-700" />
        <div className="absolute top-0 right-0 w-2 h-2 border-t-2 border-r-2 border-zinc-700" />
        <h3 className="text-xs font-mono font-bold text-zinc-400 tracking-wider mb-3 uppercase">
          {"// THREAT VECTOR BREAKDOWN"}
        </h3>
        <p className="text-xs font-mono text-zinc-500">NO ACTIVE VECTOR SIGNALS</p>
      </div>
    );
  }

  return (
    <div className="relative bg-zinc-950/65 backdrop-blur-xl border border-zinc-800/80 rounded-lg p-4 shadow-[0_0_20px_rgba(0,0,0,0.85)] overflow-hidden">
      {/* HUD Corner Ticks */}
      <div className="absolute top-0 left-0 w-2 h-2 border-t-2 border-l-2 border-red-500/70" />
      <div className="absolute top-0 right-0 w-2 h-2 border-t-2 border-r-2 border-red-500/70" />
      <div className="absolute bottom-0 left-0 w-2 h-2 border-b-2 border-l-2 border-red-500/70" />
      <div className="absolute bottom-0 right-0 w-2 h-2 border-b-2 border-r-2 border-red-500/70" />

      <h3 className="text-xs font-mono font-bold text-red-500 tracking-wider mb-2 uppercase">
        {"// THREAT VECTOR BREAKDOWN"}
      </h3>
      
      <div className="h-44 relative">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={45}
              outerRadius={65}
              paddingAngle={3}
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={entry.color} 
                  stroke="#09090b" 
                  strokeWidth={2}
                  style={{
                    filter: `drop-shadow(0 0 4px ${entry.color}44)`
                  }}
                />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: "rgba(9, 9, 11, 0.9)",
                border: "1px solid rgba(63, 63, 70, 0.8)",
                borderRadius: "0.25rem",
                color: "#e4e4e7",
                fontSize: "10px",
                fontFamily: "monospace",
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      
      <div className="mt-2 space-y-2 max-h-36 overflow-y-auto pr-1 scrollbar-thin">
        {chartData.map((item) => (
          <div key={item.name} className="flex items-center justify-between text-[10px] font-mono">
            <div className="flex items-center gap-2">
              <div
                className="w-2.5 h-2.5 rounded border border-black/50"
                style={{ 
                  backgroundColor: item.color,
                  boxShadow: `0 0 6px ${item.color}77`
                }}
              />
              <span className="text-zinc-400 font-medium">{item.name}</span>
            </div>
            <span className="text-zinc-200 font-bold">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
