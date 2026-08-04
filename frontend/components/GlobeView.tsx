"use client";

import { useEffect, useRef, useState, useMemo } from "react";
import Globe, { GlobeMethods } from "react-globe.gl";
import { useAttackStore } from "@/store/useAttackStore";
import { TYPE_COLORS, type AttackEvent } from "@/lib/types";

// Kept as "r, g, b" so the pulse can fade them out through rgba().
const TARGET_RGB = "34, 197, 94";
const ORIGIN_RGB = "252, 165, 165";

// The store holds up to MAX_EVENTS (500); only the tail is worth drawing.
const MAX_POINTS = 100;
const MAX_TARGETS = 25;
const MAX_ORIGIN_LABELS = 6;

/** Names for backend/app/schemas.py TARGET_POOL, keyed to 3dp so float
 *  serialisation can't miss. An unlisted target just renders without a name. */
const TARGET_NAMES: Record<string, string> = {
  "37.775,-122.419": "SAN FRANCISCO",
  "40.713,-74.006": "NEW YORK",
  "51.507,-0.128": "LONDON",
  "50.111,8.682": "FRANKFURT",
  "1.352,103.820": "SINGAPORE",
  "35.676,139.650": "TOKYO",
  "-33.869,151.209": "SYDNEY",
  "52.368,4.904": "AMSTERDAM",
  "19.076,72.878": "MUMBAI",
  "-23.550,-46.633": "SAO PAULO",
};

const coordKey = (lat: number, lng: number) => `${lat.toFixed(3)},${lng.toFixed(3)}`;

type Target = { lat: number; lng: number };
type Point = { lat: number; lng: number; type: AttackEvent["type"]; score: number };
/** Doubles as the rings layer — every named location pulses in its own colour. */
type Label = { lat: number; lng: number; text: string; rgb: string; size: number };

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

  // Old targets simply fall out of this window as new events arrive.
  const targets = useMemo(() => {
    const seen = new Set<string>();
    const list: Target[] = [];
    events.slice(-MAX_TARGETS).forEach((event) => {
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
    events.slice(-MAX_POINTS).forEach((event) => {
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

  // Named targets under attack, plus the countries sending the most traffic.
  // Origin names come straight off the wire — no lookup table to drift.
  const labels = useMemo(() => {
    const list: Label[] = targets.map((target) => ({
      lat: target.lat,
      lng: target.lng,
      text: TARGET_NAMES[coordKey(target.lat, target.lng)] ?? "",
      rgb: TARGET_RGB,
      size: 0.55,
    }));

    const byCountry = new Map<string, { count: number; lat: number; lng: number }>();
    events.forEach((event) => {
      if (!event.country) return;
      const entry = byCountry.get(event.country);
      if (entry) {
        entry.count += 1;
        entry.lat = event.startLat;
        entry.lng = event.startLng;
      } else {
        byCountry.set(event.country, { count: 1, lat: event.startLat, lng: event.startLng });
      }
    });

    Array.from(byCountry.entries())
      .sort((a, b) => b[1].count - a[1].count)
      .slice(0, MAX_ORIGIN_LABELS)
      .forEach(([country, { lat, lng }]) => {
        list.push({ lat, lng, text: country.toUpperCase(), rgb: ORIGIN_RGB, size: 0.45 });
      });

    return list.filter((label) => label.text);
  }, [events, targets]);

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
          // Same array as the labels: every named location gets the pulse.
          ringsData={labels}
          ringColor={(d: object) => (t: number) => `rgba(${(d as Label).rgb}, ${1 - t})`}
          ringMaxRadius={3.5}
          ringPropagationSpeed={1.6}
          ringRepeatPeriod={1100}
          pointsData={points}
          pointLat={(d) => (d as Point).lat}
          pointLng={(d) => (d as Point).lng}
          pointColor={(d) => TYPE_COLORS[(d as Point).type]}
          // Flat discs, not columns — score reads as size instead of height.
          pointAltitude={0.001}
          pointRadius={(d) => 0.18 + (d as Point).score * 0.14}
          // Default is 1000ms: with a WS batch landing every ~2s the whole set
          // would re-animate its entry on each flush and visibly stutter.
          pointsTransitionDuration={0}
          labelsData={labels}
          labelLat={(d) => (d as Label).lat}
          labelLng={(d) => (d as Label).lng}
          labelText={(d) => (d as Label).text}
          labelColor={(d) => `rgb(${(d as Label).rgb})`}
          labelSize={(d) => (d as Label).size}
          labelDotRadius={0.28}
          labelAltitude={0.012}
          labelResolution={2}
          labelsTransitionDuration={0}
        />
      )}
    </div>
  );
}
