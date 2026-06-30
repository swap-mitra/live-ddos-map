"use client";

import { useEffect, useRef, useCallback, useMemo } from "react";
import createGlobe from "cobe";
import { useAttackStore } from "@/store/useAttackStore";


export default function GlobeView() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const events = useAttackStore((state) => state.events);
  const phiRef = useRef(0);
  const globeInstanceRef = useRef<ReturnType<typeof createGlobe> | null>(null);
  const pointerInteracting = useRef<number | null>(null);
  const pointerInteractionMovement = useRef(0);

  // Build markers from DDoS events
  const markers = useMemo(() => {
    const recentEvents = events.slice(-100);
    return recentEvents.map((event) => ({
      location: [event.startLat, event.startLng] as [number, number],
      size: 0.03 + event.score * 0.05,
    }));
  }, [events]);

  const initGlobe = useCallback(() => {
    if (!canvasRef.current || !containerRef.current) return;

    // Destroy previous instance
    if (globeInstanceRef.current) {
      globeInstanceRef.current.destroy();
      globeInstanceRef.current = null;
    }

    const container = containerRef.current;
    const width = container.offsetWidth;
    const height = container.offsetHeight;
    const size = Math.min(width, height);

    if (size === 0) {
      requestAnimationFrame(initGlobe);
      return;
    }

    globeInstanceRef.current = createGlobe(canvasRef.current, {
      devicePixelRatio: 2,
      width: size * 2,
      height: size * 2,
      phi: 0,
      theta: 0.3,
      dark: 1,
      diffuse: 1.2,
      mapSamples: 16000,
      mapBrightness: 6,
      baseColor: [0.3, 0.3, 0.3],
      markerColor: [0.9, 0.3, 0.3],
      glowColor: [0.08, 0.08, 0.15],
      markers,
      onRender: (state: Record<string, unknown>) => {
        // Apply interactive movement + auto rotation
        state.phi =
          phiRef.current + pointerInteractionMovement.current;
        phiRef.current += 0.003;

        // Responsive resize
        if (containerRef.current) {
          const w = containerRef.current.offsetWidth;
          const h = containerRef.current.offsetHeight;
          const s = Math.min(w, h);
          state.width = s * 2;
          state.height = s * 2;
        }
      },
    });
  }, [markers]);

  // Pointer interaction handlers for drag-to-rotate
  const handlePointerDown = useCallback(
    (e: React.PointerEvent<HTMLCanvasElement>) => {
      pointerInteracting.current =
        e.clientX - pointerInteractionMovement.current;
      if (canvasRef.current) {
        canvasRef.current.style.cursor = "grabbing";
      }
    },
    []
  );

  const handlePointerUp = useCallback(() => {
    pointerInteracting.current = null;
    if (canvasRef.current) {
      canvasRef.current.style.cursor = "grab";
    }
  }, []);

  const handlePointerOut = useCallback(() => {
    pointerInteracting.current = null;
    if (canvasRef.current) {
      canvasRef.current.style.cursor = "grab";
    }
  }, []);

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (pointerInteracting.current !== null) {
        const delta = e.clientX - pointerInteracting.current;
        pointerInteractionMovement.current = delta / 200;
      }
    },
    []
  );

  const handleTouchMove = useCallback(
    (e: React.TouchEvent<HTMLCanvasElement>) => {
      if (pointerInteracting.current !== null && e.touches[0]) {
        const delta = e.touches[0].clientX - pointerInteracting.current;
        pointerInteractionMovement.current = delta / 100;
      }
    },
    []
  );

  useEffect(() => {
    initGlobe();

    const handleResize = () => {
      initGlobe();
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      if (globeInstanceRef.current) {
        globeInstanceRef.current.destroy();
        globeInstanceRef.current = null;
      }
    };
  }, [initGlobe]);

  return (
    <div
      ref={containerRef}
      className="globe-container"
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        overflow: "hidden",
      }}
    >
      {/* Radial gradient mask — Aceternity UI signature effect */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(circle at 50% 50%, transparent 30%, rgba(9, 9, 11, 0.6) 60%, rgba(9, 9, 11, 1) 80%)",
          pointerEvents: "none",
          zIndex: 10,
        }}
      />
      {/* Bottom fade gradient */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: "40%",
          background:
            "linear-gradient(to top, rgba(9, 9, 11, 1) 0%, transparent 100%)",
          pointerEvents: "none",
          zIndex: 11,
        }}
      />
      <canvas
        ref={canvasRef}
        onPointerDown={handlePointerDown}
        onPointerUp={handlePointerUp}
        onPointerOut={handlePointerOut}
        onMouseMove={handleMouseMove}
        onTouchMove={handleTouchMove}
        style={{
          width: "100%",
          height: "100%",
          maxWidth: "100%",
          contain: "layout paint size",
          cursor: "grab",
          aspectRatio: "1",
          opacity: 1,
        }}
      />
    </div>
  );
}
