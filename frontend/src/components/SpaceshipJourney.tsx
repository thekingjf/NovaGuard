import { useEffect, useMemo, useRef, useState } from "react";
import { Rocket } from "lucide-react";

const planets = [
  { name: "Face Mesh Analysis", color: "hsl(250, 70%, 60%)" },
  { name: "Deepfake Detection", color: "hsl(180, 80%, 60%)" },
  { name: "Temporal Coherence", color: "hsl(280, 70%, 65%)" },
  { name: "Audio Sync Check", color: "hsl(200, 75%, 60%)" },
  { name: "Artifact Detection", color: "hsl(160, 80%, 55%)" },
];

interface SpaceshipJourneyProps {
  analysisComplete?: boolean;
  onProgressComplete?: () => void;
}

export const SpaceshipJourney = ({ analysisComplete = false, onProgressComplete }: SpaceshipJourneyProps) => {
  // overall progress [0..1] and which planet is active
  const [progress, setProgress] = useState(0);
  const [currentPlanet, setCurrentPlanet] = useState(0);
  const [waitingForAnalysis, setWaitingForAnalysis] = useState(false);

  // flashing frame overlay (kept from your original)
  const [showFrame, setShowFrame] = useState(false);

  const wrapRef = useRef<HTMLDivElement | null>(null);
  // refs to avoid restarting the animation loop when props/state change
  const analysisCompleteRef = useRef(analysisComplete);
  const onCompleteRef = useRef(onProgressComplete);
  const frozenRef = useRef(false);
  const resumeStartRef = useRef<number | null>(null);
  const startRef = useRef<number | null>(null);
  const progressRef = useRef(0);

  useEffect(() => {
    analysisCompleteRef.current = analysisComplete;
  }, [analysisComplete]);

  useEffect(() => {
    onCompleteRef.current = onProgressComplete;
  }, [onProgressComplete]);

  // === timing ===
  const segmentMs = 3000; // each planet glows for 3s
  const totalMs = segmentMs * planets.length;
  const freezePoint = 0.88; // Freeze at 88% if analysis not complete

  // smooth progress + equal planet segments (single RAF loop; do not restart on state changes)
  useEffect(() => {
    let rafId: number | null = null;

    const step = (ts: number) => {
      if (startRef.current === null) startRef.current = ts;
      const elapsed = ts - startRef.current;

      // Natural linear progression
      const pLinear = Math.min(1, elapsed / totalMs);
      let p = pLinear;

      if (!frozenRef.current) {
        // Engage freeze at 88% if analysis isn't done yet
        if (pLinear >= freezePoint && !analysisCompleteRef.current) {
          p = freezePoint;
          frozenRef.current = true;
          resumeStartRef.current = null;
          setWaitingForAnalysis(true);
        }
      } else {
        // While frozen, either stay at 88% or resume to 100% once analysis completes
        if (!analysisCompleteRef.current) {
          p = freezePoint;
        } else {
          if (resumeStartRef.current === null) {
            resumeStartRef.current = ts;
          }
          const resumeElapsed = ts - resumeStartRef.current;
          const remainingTime = totalMs * (1 - freezePoint); // 12% of total time
          const frac = Math.min(1, resumeElapsed / remainingTime);
          p = freezePoint + frac * (1 - freezePoint);
        }
      }

      // Update UI state
      if (p !== progressRef.current) {
        progressRef.current = p;
        setProgress(p);
        const idx = Math.min(planets.length - 1, Math.floor(p * planets.length));
        setCurrentPlanet(idx);
      }

      // Continue or finish
      if (p < 1) {
        rafId = requestAnimationFrame(step);
      } else {
        // Only navigate once both: progress reached 100% AND analysis is complete
        if (analysisCompleteRef.current) {
          const t = setTimeout(() => onCompleteRef.current?.(), 600);
          // clear the timeout on unmount
          // store it on the rafId var temporarily using negative sentinel
          // but we'll rely on effect cleanup instead
        } else {
          // Safety: shouldn't happen because we freeze at 88% until complete
          rafId = requestAnimationFrame(step);
        }
      }
    };

    rafId = requestAnimationFrame(step);
    return () => {
      if (rafId) cancelAnimationFrame(rafId);
    };
  }, [totalMs, freezePoint]); // constants; effect effectively runs once

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
                  <span className="text-xs text-accent font-bold animate-pulse">
                    {waitingForAnalysis && progress >= freezePoint ? "Processing..." : "Analyzing..."}
                  </span>
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

          {/* Status message when waiting */}
          {waitingForAnalysis && !analysisComplete && (
            <div className="mt-4 text-center">
              <p className="text-sm text-accent animate-pulse">
                Finalizing analysis, please wait...
              </p>
            </div>
          )}

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
