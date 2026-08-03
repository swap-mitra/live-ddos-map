"use client";

import { useEffect, useRef, useState, useMemo } from "react";
import Globe, { GlobeMethods } from "react-globe.gl";
import { useAttackStore } from "@/store/useAttackStore";
import { TYPE_COLORS, type AttackEvent } from "@/lib/types";

const TARGET_COLOR = "#22c55e";

// Arcs are the expensive layer; the store holds up to MAX_EVENTS (500).
const MAX_ARCS = 60;
const MAX_RINGS = 25;

type Ring = { lat: number; lng: number };
type Point = { lat: number; lng: number; type: AttackEvent["type"]; score: number };

export default function GlobeView() {
  const containerRef = useRef<HTMLDivElement>(null);
  const globeRef = useRef<GlobeMethods | undefined>(undefined);
  const events = useAttackStore((state) => state.events);
  const [size, setSize] = useState({ w: 0, h: 0 });
  const mounted = size.w > 0;

  // react-globe.gl needs explicit pixel dimensions.
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const observer = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      setSize({ w: Math.round(width), h: Math.round(height) });
    });
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const globe = globeRef.current;
    if (!globe) return;

    const controls = globe.controls();
    controls.enableZoom = true;
    controls.minDistance = 180;
    controls.maxDistance = 500;
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.enablePan = false; // panning just off-centres the globe
    controls.rotateSpeed = 0.55;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.35;

    // Hand rotation over to the user while they're dragging.
    const pause = () => {
      controls.autoRotate = false;
    };
    const resume = () => {
      controls.autoRotate = true;
    };
    controls.addEventListener("start", pause);
    controls.addEventListener("end", resume);

    globe.pointOfView({ lat: 20, lng: 0, altitude: 2.2 });

    return () => {
      controls.removeEventListener("start", pause);
      controls.removeEventListener("end", resume);
    };
  }, [mounted]); // controls() only exists once the globe has mounted

  const arcs = useMemo(() => events.slice(-MAX_ARCS), [events]);

  // Rings self-propagate on a repeat period, so old targets simply fall out of
  // this window as new events arrive — no per-ring timers to manage.
  const rings = useMemo(() => {
    const seen = new Set<string>();
    const list: Ring[] = [];
    events.slice(-MAX_RINGS).forEach((event) => {
      const key = `${event.endLat},${event.endLng}`;
      if (seen.has(key)) return;
      seen.add(key);
      list.push({ lat: event.endLat, lng: event.endLng });
    });
    return list;
  }, [events]);

  const points = useMemo(() => {
    const seen = new Set<string>();
    const list: Point[] = [];
    events.slice(-MAX_ARCS).forEach((event) => {
      const key = `${event.startLat.toFixed(2)},${event.startLng.toFixed(2)}`;
      if (seen.has(key)) return;
      seen.add(key);
      list.push({
        lat: event.startLat,
        lng: event.startLng,
        type: event.type,
        score: event.score,
      });
    });
    return list;
  }, [events]);

  return (
    <div
      ref={containerRef}
      className="globe-container"
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        overflow: "hidden",
        cursor: "grab",
      }}
    >
      {mounted && (
        <Globe
          ref={globeRef}
          width={size.w}
          height={size.h}
          backgroundColor="rgba(0,0,0,0)"
          globeImageUrl="/textures/earth-night.jpg"
          backgroundImageUrl="/textures/night-sky.png"
          showAtmosphere={false}
          rendererConfig={{
            antialias: true,
            alpha: true,
            powerPreference: "high-performance",
          }}
          arcsData={arcs}
          arcStartLat={(d) => (d as AttackEvent).startLat}
          arcStartLng={(d) => (d as AttackEvent).startLng}
          arcEndLat={(d) => (d as AttackEvent).endLat}
          arcEndLng={(d) => (d as AttackEvent).endLng}
          arcColor={(d: object) => [
            TYPE_COLORS[(d as AttackEvent).type],
            TARGET_COLOR,
          ]}
          arcStroke={(d) => 0.3 + (d as AttackEvent).score * 0.5}
          arcAltitudeAutoScale={0.4}
          arcDashLength={0.4}
          arcDashGap={2}
          arcDashInitialGap={(d) => ((d as AttackEvent).id % 20) / 10}
          arcDashAnimateTime={2200}
          // Default is 1000ms: with a WS batch landing every ~2s the whole arc
          // set would re-animate its entry on each flush and visibly stutter.
          arcsTransitionDuration={0}
          ringsData={rings}
          ringColor={() => (t: number) => `rgba(239, 68, 68, ${1 - t})`}
          ringMaxRadius={4}
          ringPropagationSpeed={2}
          ringRepeatPeriod={900}
          pointsData={points}
          pointLat={(d) => (d as Point).lat}
          pointLng={(d) => (d as Point).lng}
          pointColor={(d) => TYPE_COLORS[(d as Point).type]}
          pointAltitude={(d) => 0.01 + (d as Point).score * 0.06}
          pointRadius={0.22}
          pointsTransitionDuration={0}
        />
      )}
    </div>
  );
}
