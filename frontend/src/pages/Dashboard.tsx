import { StarField } from "@/components/StarField";
import { MetricCard } from "@/components/MetricCard";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2, XCircle, AlertCircle } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";


interface FrameDetail {
  sharp_var?: number;
  high_ratio?: number;
  edge_glitch?: number;
  block_energy?: number;
  chroma_mismatch?: number;
}

interface AnalysisResults {
  decision: boolean;
  confidence?: number;
  video_score: number;
  frames_scored: number;
  fps?: number;
  verdict?: string;
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

  useEffect(() => {
    // Retrieve results from sessionStorage
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
      <div className="min-h-screen relative py-12 px-4">
        <StarField />
        <div className="max-w-7xl mx-auto space-y-8 relative z-10">
          <div className="text-center space-y-4">
            <h1 className="text-5xl font-bold glow-text">No Analysis Results</h1>
            <p className="text-muted-foreground text-lg">
              Please upload a video to analyze
            </p>
            <Button onClick={() => navigate("/")} className="mt-4">
              Upload Video
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Extract metrics from results
  const isDeepfake = analysisResults.decision;
  const confidence = analysisResults.confidence || (analysisResults.video_score * 100);
  const confidenceLevel = confidence >= 75 ? "High" : confidence >= 50 ? "Medium" : "Low";

  // Create metrics from frame details if available
  const sampleFrame = analysisResults.frame_details?.[0] || {};
  const metrics = [
    {
      name: "Sharpness Variance",
      score: Math.min(100, (sampleFrame.sharp_var || 0) * 10),
      details: `Value: ${(sampleFrame.sharp_var || 0).toFixed(3)}`,
      color: "hsl(250, 70%, 60%)",
    },
    {
      name: "High Frequency Ratio",
      score: Math.min(100, (sampleFrame.high_ratio || 0) * 100),
      details: `Value: ${(sampleFrame.high_ratio || 0).toFixed(3)}`,
      color: "hsl(180, 80%, 60%)",
    },
    {
      name: "Edge Glitch Score",
      score: Math.min(100, (sampleFrame.edge_glitch || 0) * 50),
      details: `Value: ${(sampleFrame.edge_glitch || 0).toFixed(3)}`,
      color: "hsl(280, 70%, 65%)",
    },
    {
      name: "Block Energy",
      score: Math.min(100, (sampleFrame.block_energy || 0) * 2),
      details: `Value: ${(sampleFrame.block_energy || 0).toFixed(3)}`,
      color: "hsl(200, 75%, 60%)",
    },
    {
      name: "Chroma Mismatch",
      score: Math.min(100, (sampleFrame.chroma_mismatch || 0) * 100),
      details: `Value: ${(sampleFrame.chroma_mismatch || 0).toFixed(3)}`,
      color: "hsl(160, 80%, 55%)",
    },
  ];

  return (
    <div className="min-h-screen relative py-12 px-4">
      <StarField />

      <div className="max-w-7xl mx-auto space-y-8 relative z-10">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-5xl font-bold glow-text">Analysis Complete</h1>
          <p className="text-muted-foreground text-lg">
            {videoInfo?.name || "Video"} - {analysisResults.frames_scored} frames analyzed
          </p>
        </div>

        {/* Final Verdict Card */}
        <Card className="cosmic-border bg-card/50 backdrop-blur-sm p-8 max-w-2xl mx-auto">
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <h2 className="text-2xl font-bold">Final Verdict</h2>
              <p className="text-muted-foreground">
                Analyzed {analysisResults.frames_scored} frames at {analysisResults.fps?.toFixed(1)} FPS
              </p>
            </div>
            <div className="text-right">
              <div className="flex items-center gap-3 justify-end mb-2">
                {isDeepfake ? (
                  <img
                    src="/icons/red-x.png"
                    alt="Deepfake detected"
                    width={48}
                    height={48}
                    className="w-12 h-12 animate-pulse-glow"
                  />
                ) : (
                  <img
                    src="/icons/green-check.png"
                    alt="Clean"
                    width={48}
                    height={48}
                    className="w-12 h-12 animate-pulse-glow"
                  />
                )}
              </div>
              <p
                className={`text-3xl font-bold ${
                  isDeepfake ? "text-destructive" : "text-green-500"
                }`}
              >
                {analysisResults.verdict || (isDeepfake ? "DEEPFAKE DETECTED" : "AUTHENTIC")}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                {confidenceLevel} Confidence
              </p>
            </div>
          </div>

          <div className="mt-6 p-4 bg-secondary/50 rounded-lg border border-border">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-accent mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium mb-1">Overall Score: {confidence.toFixed(1)}%</p>
                <p className="text-sm text-muted-foreground">
                  Video score: {(analysisResults.video_score * 100).toFixed(1)}%
                  (threshold: {(analysisResults.threshold_used * 100).toFixed(1)}%,
                  hits: {analysisResults.k_hits}/{analysisResults.k_required})
                </p>
              </div>
            </div>
          </div>

          {/* Debug: Raw Results */}
          <details className="mt-6">
            <summary className="cursor-pointer text-sm font-medium text-muted-foreground hover:text-foreground">
              Show Raw Analysis Data (Debug)
            </summary>
            <pre className="mt-2 p-4 bg-secondary/30 rounded text-xs overflow-auto max-h-96">
              {JSON.stringify(analysisResults, null, 2)}
            </pre>
          </details>
        </Card>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {metrics.map((metric) => (
            <MetricCard key={metric.name} {...metric} />
          ))}
        </div>

        {/* Actions */}
        <div className="flex justify-center gap-4 pt-8">
          <Button
            variant="outline"
            size="lg"
            onClick={() => {
              sessionStorage.removeItem("analysisResults");
              sessionStorage.removeItem("uploadedVideo");
              navigate("/");
            }}
            className="cosmic-border hover:shadow-[var(--glow-accent)] transition-all"
          >
            Analyze Another Video
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
