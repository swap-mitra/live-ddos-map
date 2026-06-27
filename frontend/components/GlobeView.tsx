"use client";

import { useEffect, useRef } from "react";
import createGlobe, { COBEOptions } from "cobe";
import { useAttackStore } from "@/store/useAttackStore";

export default function GlobeView() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const events = useAttackStore((state) => state.events);
  const phiRef = useRef(0);

  useEffect(() => {
    if (!canvasRef.current) return;

    let width = 0;

    const onResize = () => {
      if (canvasRef.current) {
        width = canvasRef.current.offsetWidth;
      }
    };
    window.addEventListener("resize", onResize);
    onResize();

    const globe = createGlobe(canvasRef.current, {
      devicePixelRatio: 2,
      width: width * 2,
      height: width * 2,
      phi: 0,
      theta: 0.3,
      dark: 1,
      diffuse: 1.2,
      mapSamples: 16000,
      mapBrightness: 6,
      baseColor: [0.1, 0.1, 0.15],
      markerColor: [0.9, 0.3, 0.3],
      glowColor: [0.2, 0.2, 0.3],
      markers: events.slice(-100).map((event) => ({
        location: [event.startLat, event.startLng],
        size: 0.03 + event.score * 0.05,
      })),
    } as COBEOptions);

    let animationFrameId: number;
    const animate = () => {
      if (canvasRef.current) {
        phiRef.current += 0.002;
      }
      animationFrameId = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      globe.destroy();
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", onResize);
    };
  }, [events]);

  return (
    <div className="w-full h-full flex items-center justify-center">
      <canvas
        ref={canvasRef}
        style={{
          width: "100%",
          height: "100%",
          maxWidth: "100%",
          aspectRatio: 1,
        }}
      />
    </div>
  );
}
