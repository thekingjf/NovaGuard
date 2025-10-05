import { StarField } from "@/components/StarField";
import { MetricCard } from "@/components/MetricCard";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2, XCircle, AlertCircle } from "lucide-react";
import { useNavigate } from "react-router-dom";

const metrics = [
  {
    name: "Face Mesh Analysis",
    score: 78,
    details: "Detected irregularities in facial landmarks",
    color: "hsl(250, 70%, 60%)",
  },
  {
    name: "Deepfake Detection",
    score: 85,
    details: "High probability of synthetic generation",
    color: "hsl(180, 80%, 60%)",
  },
  {
    name: "Temporal Coherence",
    score: 62,
    details: "Frame-to-frame inconsistencies found",
    color: "hsl(280, 70%, 65%)",
  },
  {
    name: "Audio Sync Check",
    score: 41,
    details: "Minor lip-sync discrepancies detected",
    color: "hsl(200, 75%, 60%)",
  },
  {
    name: "Artifact Detection",
    score: 73,
    details: "Visual artifacts present in multiple frames",
    color: "hsl(160, 80%, 55%)",
  },
];

const Dashboard = () => {
  const navigate = useNavigate();
  const averageScore = Math.round(
    metrics.reduce((sum, m) => sum + m.score, 0) / metrics.length
  );

  const isAIGenerated = averageScore >= 60;
  const confidence = averageScore >= 75 ? "High" : averageScore >= 50 ? "Medium" : "Low";

  return (
    <div className="min-h-screen relative py-12 px-4">
      <StarField />

      <div className="max-w-7xl mx-auto space-y-8 relative z-10">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-5xl font-bold glow-text">Analysis Complete</h1>
          <p className="text-muted-foreground text-lg">
            Comprehensive AI detection results
          </p>
        </div>

        {/* Final Verdict Card */}
        <Card className="cosmic-border bg-card/50 backdrop-blur-sm p-8 max-w-2xl mx-auto">
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <h2 className="text-2xl font-bold">Final Verdict</h2>
              <p className="text-muted-foreground">
                Based on {metrics.length} detection metrics
              </p>
            </div>
            <div className="text-right">
              <div className="flex items-center gap-3 justify-end mb-2">
                {isAIGenerated ? (
                  <XCircle className="w-12 h-12 text-destructive animate-pulse-glow" />
                ) : (
                  <CheckCircle2 className="w-12 h-12 text-green-500 animate-pulse-glow" />
                )}
              </div>
              <p
                className={`text-3xl font-bold ${
                  isAIGenerated ? "text-destructive" : "text-green-500"
                }`}
              >
                {isAIGenerated ? "AI Generated" : "Likely Authentic"}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                {confidence} Confidence
              </p>
            </div>
          </div>

          <div className="mt-6 p-4 bg-secondary/50 rounded-lg border border-border">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-accent mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium mb-1">Overall AI Score: {averageScore}%</p>
                <p className="text-sm text-muted-foreground">
                  This video shows a {averageScore}% likelihood of being AI-generated based on
                  multiple detection algorithms analyzing facial features, temporal
                  consistency, and visual artifacts.
                </p>
              </div>
            </div>
          </div>
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
            onClick={() => navigate("/")}
            className="cosmic-border hover:shadow-[var(--glow-accent)] transition-all"
          >
            Analyze Another Video
          </Button>
          <Button
            size="lg"
            className="bg-gradient-to-r from-primary to-accent text-white hover:shadow-[var(--glow-cosmic)] transition-all"
          >
            Download Report
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
