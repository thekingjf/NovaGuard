import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { StarField } from "@/components/StarField";
import { SpaceshipJourney } from "@/components/SpaceshipJourney";

const Analysis = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Listen for analysis completion
    const handleAnalysisComplete = () => {
      console.log("Analysis complete, navigating to dashboard...");
      setTimeout(() => {
        navigate("/dashboard");
      }, 2000); // Give user 2 seconds to see the completion
    };

    window.addEventListener("analysisComplete", handleAnalysisComplete);

    return () => {
      window.removeEventListener("analysisComplete", handleAnalysisComplete);
    };
  }, [navigate]);

  return (
    <div className="min-h-screen relative">
      <StarField />
      <SpaceshipJourney />
    </div>
  );
};

export default Analysis;
