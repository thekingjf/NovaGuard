import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { StarField } from "@/components/StarField";
import { SpaceshipJourney } from "@/components/SpaceshipJourney";

const Analysis = () => {
  const navigate = useNavigate();
  const [analysisComplete, setAnalysisComplete] = useState(false);

  useEffect(() => {
    // Listen for analysis completion
    const handleAnalysisComplete = () => {
      console.log("Analysis complete, signaling to progress bar...");
      setAnalysisComplete(true);
    };

    window.addEventListener("analysisComplete", handleAnalysisComplete);

    return () => {
      window.removeEventListener("analysisComplete", handleAnalysisComplete);
    };
  }, []);

  const handleProgressComplete = () => {
    console.log("Progress bar complete, navigating to dashboard...");
    navigate("/dashboard");
  };

  return (
    <div className="min-h-screen relative">
      <StarField />
      <SpaceshipJourney
        analysisComplete={analysisComplete}
        onProgressComplete={handleProgressComplete}
      />
    </div>
  );
};

export default Analysis;
