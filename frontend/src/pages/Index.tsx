import { StarField } from "@/components/StarField";
import { VideoUpload } from "@/components/VideoUpload";
import { Sparkles } from "lucide-react";

const Index = () => {
  return (
    <div className="min-h-screen relative">
      <StarField />
      
      <div className="relative z-10 pt-20 pb-12 px-4">
        {/* Hero Section */}
        <div className="text-center space-y-6 mb-12">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-primary/30 bg-primary/5 backdrop-blur-sm">
            <Sparkles className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium">AI-Powered Detection System</span>
          </div>
          
          <h1 className="text-6xl md:text-7xl font-bold glow-text">
            NovaGuard AI
          </h1>
          
          <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto">
            Advanced video analysis to detect AI-generated content using
            state-of-the-art machine learning algorithms
          </p>
        </div>

        {/* Upload Section */}
        <VideoUpload />

        {/* Features */}
        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {[
            {
              title: "Multi-Metric Analysis",
              description: "5+ detection algorithms working in parallel",
            },
            {
              title: "Real-time Processing",
              description: "Get results in seconds, not minutes",
            },
            {
              title: "Detailed Reports",
              description: "Comprehensive breakdown of every metric",
            },
          ].map((feature) => (
            <div
              key={feature.title}
              className="p-6 rounded-xl cosmic-border bg-card/30 backdrop-blur-sm hover:bg-card/50 transition-all"
            >
              <h3 className="text-lg font-bold mb-2">{feature.title}</h3>
              <p className="text-sm text-muted-foreground">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Index;
