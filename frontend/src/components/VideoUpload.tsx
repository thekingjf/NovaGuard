import { useState, useCallback } from "react";
import { Upload, Video } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

const API_URL = "http://localhost:5001/api";

export const VideoUpload = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const navigate = useNavigate();

  const uploadVideo = async (file: File) => {
    setIsUploading(true);
    const formData = new FormData();
    formData.append("video", file);

    try {
      // Store the file info in sessionStorage for the analysis page
      sessionStorage.setItem("uploadedVideo", JSON.stringify({
        name: file.name,
        size: file.size,
        type: file.type
      }));

      // Navigate to analysis page immediately
      toast.success("Video uploaded! Starting analysis...");
      navigate("/analysis");

      // Start the analysis in the background
      const response = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`);
      }

      const results = await response.json();

      // Store results in sessionStorage
      sessionStorage.setItem("analysisResults", JSON.stringify(results));

      // Trigger a custom event to notify the Analysis page
      window.dispatchEvent(new Event("analysisComplete"));

    } catch (error) {
      console.error("Error analyzing video:", error);
      toast.error("Failed to analyze video. Please try again.");
      sessionStorage.removeItem("uploadedVideo");
      navigate("/");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    const videoFile = files.find((file) => file.type.startsWith("video/"));

    if (videoFile) {
      uploadVideo(videoFile);
    } else {
      toast.error("Please upload a valid video file (.mp4)");
    }
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type.startsWith("video/")) {
      uploadVideo(file);
    } else {
      toast.error("Please upload a valid video file (.mp4)");
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          relative w-full max-w-2xl p-12 rounded-2xl border-2 border-dashed
          transition-all duration-300
          ${isDragging
            ? "border-primary bg-primary/10 scale-105"
            : "border-border hover:border-primary/50 hover:bg-card/50"
          }
        `}
      >
        <div className="flex flex-col items-center gap-6 text-center">
          <div className="relative">
            <div className="absolute inset-0 animate-pulse-glow rounded-full" />
            <div className="relative p-6 bg-primary/10 rounded-full">
              {isDragging ? (
                <Video className="w-16 h-16 text-primary" />
              ) : (
                <Upload className="w-16 h-16 text-primary" />
              )}
            </div>
          </div>

          <div className="space-y-2">
            <h2 className="text-3xl font-bold glow-text">
              Upload Your Video
            </h2>
            <p className="text-muted-foreground text-lg">
              Drag and drop your .mp4 file here, or click to browse
            </p>
          </div>

          <input
            type="file"
            accept="video/mp4,video/*"
            onChange={handleFileInput}
            className="hidden"
            id="video-input"
          />

          <Button
            variant="default"
            size="lg"
            className="relative bg-gradient-to-r from-primary to-accent text-white hover:shadow-[var(--glow-cosmic)] transition-all duration-300"
            onClick={() => document.getElementById("video-input")?.click()}
          >
            Select Video File
          </Button>

          <p className="text-sm text-muted-foreground">
            Supported formats: MP4, AVI, MOV (max 500MB)
          </p>
        </div>
      </div>
    </div>
  );
};
