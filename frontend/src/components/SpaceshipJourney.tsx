import { useState, useEffect } from "react";
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
  const [currentPlanet, setCurrentPlanet] = useState(0);
  const [showFrame, setShowFrame] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const planetInterval = setInterval(() => {
      setCurrentPlanet((prev) => {
        if (prev >= planets.length - 1) {
          clearInterval(planetInterval);
          setTimeout(() => navigate("/dashboard"), 1500);
          return prev;
        }
        return prev + 1;
      });
    }, 3000);

    const frameInterval = setInterval(() => {
      setShowFrame(true);
      setTimeout(() => setShowFrame(false), 800);
    }, 2000);

    return () => {
      clearInterval(planetInterval);
      clearInterval(frameInterval);
    };
  }, [navigate]);

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden px-4">
      {/* Spaceship */}
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 animate-float z-20">
        <div className="relative">
          <div className="absolute inset-0 blur-xl bg-primary/30 rounded-full animate-pulse-glow" />
          <Rocket className="w-24 h-24 text-primary relative z-10" />
        </div>
      </div>

      {/* Planets */}
      <div className="flex items-center justify-center gap-32 w-full max-w-6xl">
        {planets.map((planet, index) => (
          <div
            key={planet.name}
            className={`
              relative transition-all duration-700 transform
              ${index === currentPlanet ? "scale-125 opacity-100" : "scale-100 opacity-40"}
              ${index < currentPlanet ? "opacity-20" : ""}
            `}
          >
            <div 
              className="w-32 h-32 rounded-full animate-drift"
              style={{
                background: `radial-gradient(circle at 30% 30%, ${planet.color}, hsl(240 15% 8%))`,
                boxShadow: `0 0 60px ${planet.color}`,
              }}
            />
            <p className="text-center mt-4 font-medium text-sm">
              {planet.name}
            </p>
            {index === currentPlanet && (
              <div className="absolute -top-8 left-1/2 -translate-x-1/2 whitespace-nowrap">
                <span className="text-xs text-accent font-bold animate-pulse">
                  Analyzing...
                </span>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Progress indicator */}
      <div className="absolute bottom-20 left-1/2 -translate-x-1/2 text-center space-y-2">
        <div className="flex gap-2 justify-center">
          {planets.map((_, index) => (
            <div
              key={index}
              className={`
                h-2 w-12 rounded-full transition-all duration-500
                ${index <= currentPlanet ? "bg-primary" : "bg-border"}
              `}
            />
          ))}
        </div>
        <p className="text-muted-foreground text-sm">
          Processing: {currentPlanet + 1} / {planets.length}
        </p>
      </div>

      {/* Flashing frame preview */}
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
