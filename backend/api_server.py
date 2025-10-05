#!/usr/bin/env python3
"""Flask API server for NovaGuard deepfake detection (Vercel-friendly)."""
from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
import uuid
import sys

# Make local modules importable (runner.py lives next to this file)
sys.path.insert(0, str(Path(__file__).parent))

app = Flask(__name__)
CORS(app)

# ---- Serverless-safe paths (only /tmp is writable on Vercel) ----
UPLOAD_FOLDER = Path("/tmp/uploads"); UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
HEATMAP_FOLDER = Path("/tmp/heatmaps"); HEATMAP_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {'mp4', 'mov', 'mkv', 'avi', 'webm', 'm4v'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Vercel request body limit is ~4.5 MB; keep below to avoid 413s.
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ------------------ Health ------------------
@app.get("/health")
def health():
    return {"ok": True, "service": "NovaGuard API"}

# ------------------ Analyze -----------------
@app.post("/analyze")
def analyze():
    # Lazy imports so health works without heavy deps
    from werkzeug.utils import secure_filename
    from runner import score_single_video

    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    file = request.files['video']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    try:
        original = secure_filename(file.filename)
        unique = f"{uuid.uuid4()}_{original}"
        filepath = UPLOAD_FOLDER / unique
        file.save(str(filepath))

        results = score_single_video(
            video_path=filepath,
            every=3,
            tau=0.6,
            percentile=95.0,
            heatmap_root=HEATMAP_FOLDER,
            save_first_n_heatmaps=50
        )

        if isinstance(results, dict) and "error" in results:
            return jsonify(results), 500

        results["verdict"] = "DEEPFAKE DETECTED" if results.get("decision") else "AUTHENTIC"
        if "video_score" in results:
            results["confidence"] = float(results["video_score"] * 100)
        results["frame_details"] = (results.get("per_frame") or [])[:10]

        return jsonify(results), 200
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("🚀 Starting NovaGuard API Server (local)")
    print(f"📁 Upload folder: {UPLOAD_FOLDER.resolve()}")
    app.run(host="0.0.0.0", port=5001, debug=True)

handler = app