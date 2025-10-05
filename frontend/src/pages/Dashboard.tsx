import React, { useState, useEffect } from "react";
import { StarField } from "@/components/StarField";
import { Button } from "@/components/ui/button";
import { AlertCircle, HelpCircle, ArrowLeft, CheckCircle, XCircle } from "lucide-react";
import { useNavigate } from "react-router-dom";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface FrameDetail {
  sharp_var?: number;
  high_ratio?: number;
  edge_glitch?: number;
  block_energy?: number;
  chroma_mismatch?: number;
}

interface AnalysisResults {
  decision: boolean;              // true => AI-generated, false => authentic
  confidence?: number;
  video_score: number;
  frames_scored: number;
  fps?: number;
  verdict?: string;               // ignored for display (we enforce our own labels)
  threshold_used: number;
  k_hits: number;
  k_required: number;
  frame_details?: FrameDetail[];
}

interface VideoInfo {
  name?: string;
}

const Dashboard = () => {
  const navigate = useNavigate();
  const [analysisResults, setAnalysisResults] = useState<AnalysisResults | null>(null);
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX / window.innerWidth, y: e.clientY / window.innerHeight });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  useEffect(() => {
    const resultsStr = sessionStorage.getItem("analysisResults");
    const videoStr = sessionStorage.getItem("uploadedVideo");

    if (resultsStr) {
      const results = JSON.parse(resultsStr);
      setAnalysisResults(results);
      console.log("Analysis results:", results);
    }

    if (videoStr) {
      const video = JSON.parse(videoStr);
      setVideoInfo(video);
    }
  }, []);

  if (!analysisResults) {
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

        <div className="relative z-10 flex items-center justify-center min-h-screen px-4">
          <div className="text-center space-y-8 max-w-2xl mx-auto">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-full blur-3xl" />
              <h1 className="relative text-6xl md:text-7xl font-bold bg-gradient-to-r from-white via-purple-200 to-white bg-clip-text text-transparent">
                No Analysis Results
              </h1>
            </div>
            <p className="text-xl text-gray-400">
              Please upload a video to analyze
            </p>
            <Button
              onClick={() => navigate("/")}
              size="lg"
              className="relative bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white px-8 py-6 text-lg rounded-2xl transition-all duration-300 hover:scale-105 hover:shadow-[0_0_40px_rgba(168,85,247,0.4)]"
            >
              Upload Video
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // --- Verdict mapping (authoritative) ---
  // If your backend uses the opposite meaning, flip this boolean.
  const isAI = !!analysisResults.decision;                 // true -> AI Generated, false -> Authentic
  const verdictText = isAI ? "AI Generated" : "Authentic";
  const verdictColor = isAI ? "text-destructive" : "text-green-500";
  const iconSrc     = isAI ? "/icons/red-x.svg" : "/icons/green-check.png";
  const iconAlt     = isAI ? "AI generated" : "Authentic";

  // Confidence display (falls back to video_score * 100)
  const confidence = analysisResults.confidence ?? analysisResults.video_score * 100;
  const confidenceLevel = confidence >= 75 ? "High" : confidence >= 50 ? "Medium" : "Low";

  // Example metrics from first frame (optional)
  const sampleFrame = analysisResults.frame_details?.[0] || {};
  // Metric descriptions for tooltips
  const metricDescriptions = {
    "Sharpness Variance": "Measures edge clarity using multi-scale Laplacian analysis. AI-generated content often shows unnaturally smooth or overly sharp edges.",
    "High Frequency Ratio": "Analyzes the ratio of high-frequency components in the Fourier spectrum. Deepfakes typically lack natural high-frequency details.",
    "Edge Glitch Score": "Detects inconsistencies in edge boundaries across small tiles. AI generation can create subtle artifacts at edge transitions.",
    "Block Energy": "Examines compression grid patterns at 8x8 block boundaries. Deepfakes often show unusual block boundary energy.",
    "Chroma Mismatch": "Checks color channel consistency. AI-generated faces may have unnatural color relationships between channels."
  };

  const metrics = [
    {
      name: "Sharpness Variance",
      score: Math.min(100, (sampleFrame.sharp_var || 0) * 10),
      value: (sampleFrame.sharp_var || 0).toFixed(3),
      color: "from-purple-500 to-pink-500",
    },
    {
      name: "High Frequency Ratio",
      score: Math.min(100, (sampleFrame.high_ratio || 0) * 100),
      value: (sampleFrame.high_ratio || 0).toFixed(3),
      color: "from-blue-500 to-cyan-500",
    },
    {
      name: "Edge Glitch Score",
      score: Math.min(100, (sampleFrame.edge_glitch || 0) * 50),
      value: (sampleFrame.edge_glitch || 0).toFixed(3),
      color: "from-green-500 to-emerald-500",
    },
    {
      name: "Block Energy",
      score: Math.min(100, (sampleFrame.block_energy || 0) * 2),
      value: (sampleFrame.block_energy || 0).toFixed(3),
      color: "from-orange-500 to-red-500",
    },
    {
      name: "Chroma Mismatch",
      score: Math.min(100, (sampleFrame.chroma_mismatch || 0) * 100),
      value: (sampleFrame.chroma_mismatch || 0).toFixed(3),
      color: "from-indigo-500 to-purple-500",
    },
  ];

  return (
    <TooltipProvider>
      <div className="min-h-screen relative">
        <StarField />

        {/* Mouse-following gradient overlay */}
        <div
          className="fixed inset-0 opacity-40 pointer-events-none z-[1]"
          style={{
            background: `radial-gradient(circle at ${mousePosition.x * 100}% ${mousePosition.y * 100}%, rgba(139, 92, 246, 0.3), transparent 40%)`,
          }}
        />

        <div className="relative z-10 min-h-screen py-16 px-8">
          <div className="max-w-7xl mx-auto space-y-12">
            {/* Header with back button */}
            <div className="flex items-center justify-between">
              <Button
                variant="ghost"
                onClick={() => {
                  sessionStorage.removeItem("analysisResults");
                  sessionStorage.removeItem("uploadedVideo");
                  navigate("/");
                }}
                className="group"
              >
                <ArrowLeft className="w-5 h-5 mr-2 group-hover:-translate-x-1 transition-transform" />
                Back to Home
              </Button>
            </div>

            {/* Page Title */}
            <div className="text-center space-y-4">
              <h1 className="text-6xl md:text-7xl font-bold bg-gradient-to-r from-white via-purple-200 to-white bg-clip-text text-transparent">
                Analysis Complete
              </h1>
              <p className="text-xl text-gray-400">
                {videoInfo?.name || "Video"} - {analysisResults.frames_scored} frames analyzed
              </p>
            </div>

            {/* Final Verdict Card - Ultra Modern */}
            <div className="relative max-w-4xl mx-auto">
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/20 via-pink-500/10 to-transparent rounded-3xl blur-2xl" />

              <div className="relative p-8 md:p-12 rounded-3xl bg-white/5 backdrop-blur-xl border border-white/10">
                <div className="flex flex-col md:flex-row items-center justify-between gap-8">
                  <div className="space-y-4 text-center md:text-left">
                    <h2 className="text-3xl md:text-4xl font-bold text-white">Final Verdict</h2>
                    <p className="text-gray-400 text-lg">
                      Analyzed {analysisResults.frames_scored} frames at {analysisResults.fps?.toFixed(1)} FPS
                    </p>
                  </div>

                  <div className="text-center">
                    <div className="flex items-center justify-center gap-4 mb-4">
                      {/* Verdict Icon with glow */}
                      <div className="relative">
                        <div
                          className={`absolute inset-0 rounded-full blur-2xl ${
                            isAI ? "bg-red-500/40" : "bg-green-500/40"
                          }`}
                        />
                        {isAI ? (
                          <XCircle className="relative w-20 h-20 text-red-500" />
                        ) : (
                          <CheckCircle className="relative w-20 h-20 text-green-500" />
                        )}
                      </div>
                    </div>

                    <p className={`text-4xl md:text-5xl font-bold mb-2 ${verdictColor}`}>
                      {verdictText}
                    </p>
                    <p className="text-sm text-gray-400">
                      {confidenceLevel} Confidence
                    </p>
                  </div>
                </div>

                {/* Score Details */}
                <div className="mt-8 p-6 bg-white/5 rounded-2xl border border-white/10">
                  <div className="flex items-start gap-4">
                    <AlertCircle className="w-6 h-6 text-purple-400 mt-1 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-xl font-bold text-white mb-2">
                        Overall Score: {confidence.toFixed(1)}%
                      </p>
                      <p className="text-sm text-gray-400">
                        Video score: {(analysisResults.video_score * 100).toFixed(1)}%
                        (threshold: {(analysisResults.threshold_used * 100).toFixed(1)}%,
                        hits: {analysisResults.k_hits}/{analysisResults.k_required})
                      </p>
                    </div>
                  </div>
                </div>

                {/* Debug Data - Collapsed */}
                <details className="mt-6 group">
                  <summary className="cursor-pointer text-sm font-medium text-gray-400 hover:text-white transition-colors list-none">
                    <span className="flex items-center gap-2">
                      <span className="group-open:rotate-90 transition-transform">▶</span>
                      Show Raw Analysis Data (Debug)
                    </span>
                  </summary>
                  <pre className="mt-4 p-4 bg-black/30 rounded-xl text-xs overflow-auto max-h-96 text-gray-300">
                    {JSON.stringify(analysisResults, null, 2)}
                  </pre>
                </details>
              </div>
            </div>

            {/* Detection Metrics Section */}
            <div className="space-y-8">
              <div className="text-center">
                <h2 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
                  Detection Metrics
                </h2>
                <p className="text-lg text-gray-400 max-w-2xl mx-auto">
                  Five powerful algorithms working in harmony to expose the truth
                </p>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {metrics.map((metric, index) => (
                  <div
                    key={metric.name}
                    className="group relative p-8 rounded-3xl bg-white/5 backdrop-blur-xl border border-white/10 hover:bg-white/10 transition-all duration-500 hover:scale-105 hover:-translate-y-2"
                    style={{
                      animationDelay: `${index * 0.1}s`,
                    }}
                  >
                    <div className={`absolute inset-0 rounded-3xl bg-gradient-to-br ${metric.color} opacity-0 group-hover:opacity-10 transition-opacity duration-500`} />

                    {/* Metric Header with Tooltip */}
                    <div className="flex items-start justify-between mb-6">
                      <h3 className="text-xl font-bold text-white pr-2">{metric.name}</h3>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <button className="text-gray-400 hover:text-white transition-colors">
                            <HelpCircle className="w-5 h-5" />
                          </button>
                        </TooltipTrigger>
                        <TooltipContent className="max-w-xs bg-black/90 border-white/20 text-white">
                          <p className="text-sm">{metricDescriptions[metric.name as keyof typeof metricDescriptions]}</p>
                        </TooltipContent>
                      </Tooltip>
                    </div>

                    {/* Metric Value */}
                    <div className="mb-4">
                      <div className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                        {metric.value}
                      </div>
                      <div className="text-sm text-gray-400 mt-1">
                        AI Detection Score
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                      <div
                        className={`h-full bg-gradient-to-r ${metric.color} rounded-full transition-all duration-1000 group-hover:w-full`}
                        style={{ width: `${metric.score}%` }}
                      />
                    </div>

                    {/* Score Percentage */}
                    <div className="mt-3 text-right">
                      <span className="text-sm font-semibold text-gray-400">
                        {metric.score.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Action Button */}
            <div className="flex justify-center pt-8">
              <Button
                size="lg"
                onClick={() => {
                  sessionStorage.removeItem("analysisResults");
                  sessionStorage.removeItem("uploadedVideo");
                  navigate("/");
                }}
                className="relative bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white px-8 py-6 text-lg rounded-2xl transition-all duration-300 hover:scale-105 hover:shadow-[0_0_40px_rgba(168,85,247,0.4)]"
              >
                Analyze Another Video
              </Button>
            </div>
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
};

export default Dashboard;
