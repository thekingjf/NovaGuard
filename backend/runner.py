from pathlib import Path
from typing import Optional, List
import argparse, json, time, sys
import numpy as np
import cv2

# Allow local imports when running as: python backend/runner.py <path>
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

import texture_model as tm  # must expose frame_score(face_bgr)

# Prefer video-level threshold; fall back to frame-level; else 0.5
try:
    from weights import THRESH_VIDEO as THRESH
except Exception:
    try:
        from weights import THRESH
    except Exception:
        THRESH = 0.5

SUFFIXES = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}

HAAR = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
def get_face_crop(frame_bgr, target: int = 256, pad_frac: float = 0.12):
    g = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    faces = HAAR.detectMultiScale(g, 1.1, 5, minSize=(80, 80))
    if len(faces) == 0:
        return cv2.resize(frame_bgr, (target, target), cv2.INTER_AREA)
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    H, W = frame_bgr.shape[:2]
    pad = int(pad_frac * max(w, h))
    x1, y1 = max(x - pad, 0), max(y - pad, 0)
    x2, y2 = min(x + w + pad, W), min(y + h + pad, H)
    return cv2.resize(frame_bgr[y1:y2, x1:x2], (target, target), cv2.INTER_AREA)

def open_video(path: Path):
    for api in (cv2.CAP_FFMPEG, cv2.CAP_AVFOUNDATION, cv2.CAP_ANY):
        cap = cv2.VideoCapture(str(path), api)
        if cap.isOpened():
            return cap
    return cv2.VideoCapture(str(path))

def ema_series(values: List[float], alpha: float) -> List[float]:
    out, prev = [], None
    for v in values:
        prev = v if prev is None else alpha * v + (1 - alpha) * prev
        out.append(float(prev))
    return out

def score_single_video(
    video_path: Path,
    every: int = 3,
    tau: float = 0.6,
    percentile: float = 95.0,
    heatmap_root: Optional[Path] = None,
    save_first_n_heatmaps: int = 50,
):
    cap = open_video(video_path)
    if not cap.isOpened():
        raise SystemExit(f"[error] cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    alpha = float(min(0.6, max(0.15, 1.0 - np.exp(- (every / max(1.0, fps)) / tau ))))

    heatmap_dir = None
    if heatmap_root:
        ts = time.strftime("%Y%m%d_%H%M%S")
        heatmap_dir = heatmap_root / f"{video_path.stem}_{ts}"
        heatmap_dir.mkdir(parents=True, exist_ok=True)

    susp_list, per_frame = [], []
    saved_hm, idx = 0, 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % every:
            idx += 1
            continue

        face = get_face_crop(frame, target=256)
        d = tm.frame_score(face)  # dict with metrics + 'overlay'

        if heatmap_dir is not None and saved_hm < save_first_n_heatmaps:
            out_im = heatmap_dir / f"{video_path.stem}_heat_{idx:06d}.jpg"
            cv2.imwrite(str(out_im), d["overlay"])
            saved_hm += 1

        df = {k: float(v) for k, v in d.items() if k != "overlay"}
        df["frame_idx"] = idx
        df["time_sec"] = round(idx / float(fps), 3)
        per_frame.append(df)

        susp_list.append(float(d["suspicion"]))
        idx += 1

    cap.release()

    if not susp_list:
        return {
            "video": str(video_path),
            "error": "No frames processed (empty/corrupt input or stride too large)."
        }

    ema = ema_series(susp_list, alpha=alpha)
    video_score = float(np.percentile(ema, percentile))
    k_required = max(3, len(ema) // 20)
    decision = (video_score >= THRESH) and (sum(s >= THRESH for s in ema) >= k_required)

    return {
        "video": str(video_path),
        "frames_scored": len(susp_list),
        "fps": float(fps),
        "ema_alpha": alpha,
        "aggregator": f"EMA+p{int(percentile)}",
        "threshold_used": float(THRESH),
        "video_score": video_score,
        "decision": bool(decision),
        "per_frame": per_frame,
        "heatmaps_dir": str(heatmap_dir) if heatmap_dir else None
    }

def main():
    ap = argparse.ArgumentParser(description="Score a single uploaded video and save heatmaps.")
    ap.add_argument("video_path", help="Path to the uploaded video. If not found, tries backend/uploads/<name>.")
    ap.add_argument("--every", type=int, default=3)
    ap.add_argument("--tau", type=float, default=0.6)
    ap.add_argument("--percentile", type=float, default=95.0)
    ap.add_argument("--heatmap-root", default=str(BACKEND_DIR / "out" / "heatmaps"))
    args = ap.parse_args()

    in_path = Path(args.video_path)
    if not in_path.exists():
        maybe = BACKEND_DIR / "uploads" / args.video_path
        if maybe.exists():
            in_path = maybe
        else:
            raise SystemExit(f"[error] file not found: {args.video_path}")

    if in_path.suffix.lower() not in SUFFIXES:
        print(f"[warn] unexpected extension {in_path.suffix}; attempting anyway…")

    heat_root = Path(args.heatmap_root)
    result = score_single_video(
        video_path=in_path,
        every=args.every,
        tau=args.tau,
        percentile=args.percentile,
        heatmap_root=heat_root,
        save_first_n_heatmaps=50
    )
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        # Emit JSON on fatal CLI errors so callers never get an empty file.
        print(json.dumps({"error": str(e) or "SystemExit"}, indent=2))
        raise
    except Exception as e:
        print(json.dumps({"error": repr(e)}, indent=2))
        raise
