import { useEffect, useMemo, useRef, useState } from "react";
import { Rocket } from "lucide-react";
import { useNavigate } from "react-router-dom";

const planets = [
  { name: "Face Mesh Analysis", color: "hsl(250, 70%, 60%)" },
  { name: "Deepfake Detection", color: "hsl(180, 80%, 60%)" },
  { name: "Temporal Coherence", color: "hsl(280, 70%, 65%)" },
  { name: "Audio Sync Check", color: "hsl(200, 75%, 60%)" },
  { name: "Artifact Detection", color: "hsl(160, 80%, 55%)" },
];

export const SpaceshipJourney = () => {
  const navigate = useNavigate();

  // overall progress [0..1] and which planet is active
  const [progress, setProgress] = useState(0);
  const [currentPlanet, setCurrentPlanet] = useState(0);

  // flashing frame overlay (kept from your original)
  const [showFrame, setShowFrame] = useState(false);

  const wrapRef = useRef<HTMLDivElement | null>(null);

  // === timing ===
  const segmentMs = 3000; // each planet glows for 3s
  const totalMs = segmentMs * planets.length;

  // smooth progress + equal planet segments
  useEffect(() => {
    const prefersReduced =
      window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;

    if (prefersReduced) {
      setProgress(1);
      setCurrentPlanet(planets.length - 1);
      const t = setTimeout(() => navigate("/dashboard"), 600);
      return () => clearTimeout(t);
    }

    let start: number | null = null;
    let rafId: number | null = null;

    const step = (ts: number) => {
      if (start === null) start = ts;
      const p = Math.min(1, (ts - start) / totalMs);
      setProgress(p);

      // split [0,1] into N equal segments
      const idx = Math.min(planets.length - 1, Math.floor(p * planets.length));
      setCurrentPlanet(idx);

      if (p < 1) {
        rafId = requestAnimationFrame(step);
      } else {
        setTimeout(() => navigate("/dashboard"), 800);
      }
    };

    rafId = requestAnimationFrame(step);
    return () => {
      if (rafId) cancelAnimationFrame(rafId);
    };
  }, [navigate, totalMs]);

  // flashing preview every 2s (unchanged)
  useEffect(() => {
    const interval = setInterval(() => {
      setShowFrame(true);
      const off = setTimeout(() => setShowFrame(false), 800);
      return () => clearTimeout(off);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  // kept in case you want it later; unused now
  useMemo(() => Math.floor(progress * planets.length), [progress]);

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden px-4">
      {/* PLANETS + TRACK share the same container width */}
      <div ref={wrapRef} className="relative w-full max-w-6xl">
        {/* --- Planets row --- */}
        <div className="flex items-center justify-center gap-32 w-full">
          {planets.map((planet, index) => (
            <div
              key={planet.name}
              className={[
                "relative transition-all duration-700 transform",
                index === currentPlanet ? "scale-125 opacity-100" : "scale-100 opacity-40",
                index < currentPlanet ? "opacity-20" : "",
              ].join(" ")}
            >
              <div
                className="w-32 h-32 rounded-full animate-drift"
                style={{
                  background: `radial-gradient(circle at 30% 30%, ${planet.color}, hsl(240 15% 8%))`,
                  boxShadow: `0 0 60px ${planet.color}`,
                }}
              />
              <p className="text-center mt-4 font-medium text-sm">{planet.name}</p>

              {index === currentPlanet && (
                <div className="absolute -top-8 left-1/2 -translate-x-1/2 whitespace-nowrap">
                  <span className="text-xs text-accent font-bold animate-pulse">Analyzing...</span>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* --- Full-width rocket progress track under planets --- */}
        <div className="mt-16 sm:mt-20 md:mt-24">
          {/* No overflow-hidden so the rocket can sit above the bar */}
          <div className="relative h-3 w-full rounded-full bg-[hsl(240_15%_10%)] border border-border">
            {/* filled portion (behind) */}
            <div
              className="absolute inset-y-0 left-0 bg-primary/40 z-0"
              style={{ width: `${(progress * 100).toFixed(2)}%` }}
            />

            {/* subtle moving sheen */}
            <div
              className="absolute inset-y-0 z-0"
              style={{
                left: `${(progress * 100).toFixed(2)}%`,
                width: "18%",
                transform: "translateX(-50%)",
                background:
                  "linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.12) 50%, rgba(255,255,255,0) 100%)",
                opacity: 0.35,
              }}
            />

            {/* rocket riding the edge — lifted above the bar */}
            <div
              className="absolute -top-6 z-10 pointer-events-none"
              style={{ left: `calc(${(progress * 100).toFixed(2)}% - 16px)` }}
              aria-hidden
            >
              <div className="relative">
                <div className="absolute inset-0 blur-lg rounded-full opacity-60 animate-pulse-glow" />
                <Rocket className="w-8 h-8 text-primary relative z-10" />
              </div>
            </div>
          </div>

          {/* (Removed) segmented mini-pills and Processing label */}
        </div>
      </div>

      {/* --- Flashing frame preview overlay (unchanged) --- */}
      {showFrame && (
        <div className="fixed inset-0 z-30 flex items-center justify-center pointer-events-none">
          <div className="w-96 h-64 bg-card border-2 border-destructive rounded-lg animate-pulse-glow">
            <div className="w-full h-full flex items-center justify-center text-destructive font-bold">
              SUSPICIOUS FRAME DETECTED
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
