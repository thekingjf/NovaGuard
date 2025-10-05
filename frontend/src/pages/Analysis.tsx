import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { StarField } from "@/components/StarField";
import { SpaceshipJourney } from "@/components/SpaceshipJourney";

const Analysis = () => {
  const navigate = useNavigate();
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    // Listen for analysis completion
    const handleAnalysisComplete = () => {
      console.log("Analysis complete, signaling to progress bar...");
      setAnalysisComplete(true);
    };
    const handleMouseMove = (e) => {
        setMousePosition({ x: e.clientX / window.innerWidth, y: e.clientY / window.innerHeight });
    };
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener("analysisComplete", handleAnalysisComplete);

    return () => {
      window.removeEventListener("analysisComplete", handleAnalysisComplete);
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

  const handleProgressComplete = () => {
    console.log("Progress bar complete, navigating to dashboard...");
    navigate("/dashboard");
  };

  return (
    <div className="min-h-screen relative">
      <StarField />
      {/* Mouse-following gradient overlay */}
      <div
        className="fixed inset-0 opacity-40 pointer-events-none z-[1]"
        style={{
          background: `radial-gradient(circle at ${mousePosition.x * 100}% ${mousePosition.y * 100}%, rgba(139, 92, 246, 0.3), transparent 40%)`,
        }}
      />
      <SpaceshipJourney
        analysisComplete={analysisComplete}
        onProgressComplete={handleProgressComplete}
      />
    </div>
  );
};

export default Analysis;
