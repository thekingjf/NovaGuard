#!/usr/bin/env python3
"""Flask API server for NovaGuard deepfake detection."""
from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
import uuid
import sys

sys.path.insert(0, str(Path(__file__).parent))

# Import the scoring function from runner.py
from runner import score_single_video

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = Path(__file__).parent / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)
HEATMAP_FOLDER = Path(__file__).parent / "out" / "heatmaps"
HEATMAP_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {'mp4', 'mov', 'mkv', 'avi', 'webm', 'm4v'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "NovaGuard API"})

@app.route('/api/analyze', methods=['POST'])
def analyze():
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400
    file = request.files['video']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400
    try:
        from werkzeug.utils import secure_filename
        original_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{original_filename}"
        filepath = UPLOAD_FOLDER / unique_filename
        file.save(str(filepath))

        print(f"[INFO] Analyzing video: {original_filename}")

        # Use runner.py's score_single_video function
        results = score_single_video(
            video_path=filepath,
            every=3,
            tau=0.6,
            percentile=95.0,
            heatmap_root=HEATMAP_FOLDER,
            save_first_n_heatmaps=50
        )

        # Check for errors in results
        if "error" in results:
            print(f"[ERROR] {results['error']}")
            return jsonify(results), 500

        # Add user-friendly verdict field
        results["verdict"] = "DEEPFAKE DETECTED" if results["decision"] else "AUTHENTIC"
        results["confidence"] = float(results["video_score"] * 100)

        # Extract frame details for frontend (first 10 frames)
        results["frame_details"] = results.get("per_frame", [])[:10]

        print(f"[INFO] Analysis complete: {results.get('verdict', 'Unknown')}")
        print(f"[INFO] Frames scored: {results.get('frames_scored', 0)}, Score: {results.get('video_score', 0):.3f}")

        return jsonify(results), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting NovaGuard API Server...")
    print(f"📁 Upload folder: {UPLOAD_FOLDER.resolve()}")
    app.run(host='0.0.0.0', port=5001, debug=True)
