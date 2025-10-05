import React, { useState, useEffect, useRef } from 'react';
import { StarField } from "@/components/StarField";
import { VideoUpload } from "@/components/VideoUpload";
import { Shield, Zap, Brain, Eye, Layers, ChevronDown, Play, ArrowRight } from 'lucide-react';

const Index = () => {
  const [scrollY, setScrollY] = useState(0);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const heroRef = useRef(null);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    const handleMouseMove = (e) => {
      setMousePosition({ x: e.clientX / window.innerWidth, y: e.clientY / window.innerHeight });
    };

    window.addEventListener('scroll', handleScroll);
    window.addEventListener('mousemove', handleMouseMove);
    return () => {
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

  const metrics = [
    { name: "Edge Clarity", icon: Eye, color: "from-purple-500 to-pink-500", value: "98.7%" },
    { name: "Texture Balance", icon: Layers, color: "from-blue-500 to-cyan-500", value: "0.012" },
    { name: "Boundary Jitter", icon: Zap, color: "from-green-500 to-emerald-500", value: "Low" },
    { name: "Compression Grid", icon: Shield, color: "from-orange-500 to-red-500", value: "Clear" },
    { name: "Color Consistency", icon: Brain, color: "from-indigo-500 to-purple-500", value: "High" },
  ];

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

      {/* Navigation Bar */}
      <nav className="fixed top-0 left-0 right-0 z-50 px-8 py-6">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-2">
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section ref={heroRef} className="relative min-h-screen flex items-center justify-center px-8 pt-20 z-10">
        <div
          className="relative z-10 text-center max-w-6xl mx-auto"
          style={{
            transform: `translateY(${Math.min(scrollY * 0.15, 100)}px)`,
          }}
        >
          {/* Main headline with gradient */}
          <h1 className="text-7xl md:text-8xl lg:text-9xl font-bold mb-8 leading-tight">
            <span className="block bg-gradient-to-r from-white via-purple-200 to-white bg-clip-text text-transparent animate-gradient-x">
              NovaGuard
            </span>
            <span className="block text-4xl md:text-5xl lg:text-6xl mt-4 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              AI Detection System
            </span>
          </h1>

          <p className="text-xl md:text-2xl text-gray-400 max-w-3xl mx-auto mb-12 leading-relaxed">
            Advanced video analysis to detect AI-generated content using
            machine learning algorithms
          </p>

          {/* Upload Section */}
          <div className="mb-16">
            <VideoUpload />
          </div>

          {/* Scroll indicator */}
          <div className="absolute bottom-10 left-1/2 transform -translate-x-1/2 animate-bounce">
            <ChevronDown className="w-8 h-8 text-purple-400" />
          </div>
        </div>

        {/* 3D rotating orb - made more visible */}
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 pointer-events-none z-0">
          <div className="w-[500px] h-[500px] animate-spin-slow">
            <div className="absolute inset-0 rounded-full bg-gradient-to-r from-purple-500/30 via-pink-500/20 to-transparent blur-2xl" />
            <div className="absolute inset-10 rounded-full bg-gradient-to-l from-blue-500/20 via-transparent to-purple-500/20 blur-xl" />
          </div>
        </div>
      </section>

      {/* Interactive Metrics Display */}
      <section className="relative py-32 px-8 z-10">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20">
            <h2 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
              Detection Metrics
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Five powerful algorithms working in harmony to expose the truth
            </p>
          </div>

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

                <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${metric.color} p-0.5 mb-6`}>
                  <div className="w-full h-full rounded-2xl bg-black flex items-center justify-center">
                    <metric.icon className="w-8 h-8 text-white" />
                  </div>
                </div>

                <h3 className="text-2xl font-bold mb-2 text-white">{metric.name}</h3>
                <div className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent mb-4">
                  {metric.value}
                </div>
                <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                  <div
                    className={`h-full bg-gradient-to-r ${metric.color} rounded-full transition-all duration-1000 group-hover:w-full`}
                    style={{ width: '70%' }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Feature Showcase */}
      <section className="relative py-32 px-8 z-10">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div>
              <h2 className="text-5xl md:text-6xl font-bold mb-8 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
                Unparalleled Precision
              </h2>
              <p className="text-xl text-gray-400 mb-8 leading-relaxed">
                Our state-of-the-art algorithm analyzes every frame with microscopic attention to detail, examining edge patterns, texture consistency, and compression artifacts that are invisible to the human eye.
              </p>
              <div className="space-y-6">
                {['30 FPS Real-time Analysis', '70% Detection Accuracy', 'Multi-format Support'].map((feature) => (
                  <div key={feature} className="flex items-center gap-4">
                    <div className="w-2 h-2 rounded-full bg-gradient-to-r from-purple-400 to-pink-400" />
                    <span className="text-lg text-gray-300">{feature}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="relative">
              <div className="aspect-video rounded-3xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 backdrop-blur-xl border border-white/10 flex items-center justify-center group cursor-pointer hover:scale-105 transition-transform duration-500">
                <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-purple-500/10 to-transparent" />
                <Play className="w-20 h-20 text-white/80 group-hover:scale-110 transition-transform" />
              </div>
              {/* Floating elements */}
              <div className="absolute -top-4 -right-4 w-24 h-24 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 animate-float opacity-40" style={{ animationDelay: '0s' }} />
              <div className="absolute -bottom-4 -left-4 w-32 h-32 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 animate-float opacity-40" style={{ animationDelay: '2s' }} />
            </div>
          </div>
        </div>
      </section>

      <style jsx>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-20px); }
        }
        @keyframes gradient-x {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
        @keyframes spin-slow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .animate-float {
          animation: float 6s ease-in-out infinite;
        }
        .animate-gradient-x {
          background-size: 200% 200%;
          animation: gradient-x 4s ease infinite;
        }
        .animate-spin-slow {
          animation: spin-slow 20s linear infinite;
        }
      `}</style>
    </div>
  );
};

export default Index;
