"use client";

import { useAttackStore } from "@/store/useAttackStore";
import { useMemo } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

const TYPE_COLORS: Record<string, string> = {
  volumetric: "#ef4444",
  amplification: "#f59e0b",
  application: "#a855f7",
  scanner: "#3b82f6",
  unknown: "#6b7280",
};

const TYPE_LABELS: Record<string, string> = {
  volumetric: "Volumetric",
  amplification: "Amplification",
  application: "Application",
  scanner: "Scanner",
  unknown: "Unknown",
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
        color: TYPE_COLORS[type] || "#6b7280",
      }))
      .sort((a, b) => b.value - a.value);
  }, [events]);

  if (chartData.length === 0) {
    return (
      <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
        <h3 className="text-sm font-semibold text-zinc-300 mb-3">
          Attack Types
        </h3>
        <p className="text-xs text-zinc-500">No data available</p>
      </div>
    );
  }

  return (
    <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
      <h3 className="text-sm font-semibold text-zinc-300 mb-3">
        Attack Types
      </h3>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={40}
              outerRadius={70}
              paddingAngle={2}
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: "#18181b",
                border: "1px solid #27272a",
                borderRadius: "0.5rem",
                color: "#e4e4e7",
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-2 space-y-1">
        {chartData.map((item) => (
          <div key={item.name} className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: item.color }}
              />
              <span className="text-xs text-zinc-400">{item.name}</span>
            </div>
            <span className="text-xs text-zinc-300">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
