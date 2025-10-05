import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface MetricCardProps {
  name: string;
  score: number;
  details: string;
  color: string;
}

export const MetricCard = ({ name, score, details, color }: MetricCardProps) => {
  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-destructive";
    if (score >= 50) return "text-yellow-500";
    return "text-green-500";
  };

  const getProgressColor = (score: number) => {
    if (score >= 80) return "bg-destructive";
    if (score >= 50) return "bg-yellow-500";
    return "bg-green-500";
  };

  return (
    <Card className="p-6 cosmic-border bg-card/50 backdrop-blur-sm hover:shadow-[var(--shadow-card)] transition-all duration-300">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-xl font-bold">{name}</h3>
          <p className="text-sm text-muted-foreground mt-1">{details}</p>
        </div>
        <div 
          className="w-12 h-12 rounded-full animate-pulse-glow"
          style={{ 
            background: `radial-gradient(circle, ${color}, transparent)`,
            boxShadow: `0 0 30px ${color}`,
          }}
        />
      </div>
      
      <div className="space-y-2">
        <div className="flex justify-between items-baseline">
          <span className="text-sm text-muted-foreground">AI Detection Score</span>
          <span className={`text-2xl font-bold ${getScoreColor(score)}`}>
            {score}%
          </span>
        </div>
        <div className="relative">
          <Progress value={score} className="h-2" />
          <div 
            className={`absolute top-0 left-0 h-2 rounded-full transition-all ${getProgressColor(score)}`}
            style={{ width: `${score}%` }}
          />
        </div>
      </div>
    </Card>
  );
};
