# backend/run_test_data.py
from pathlib import Path
import argparse, json, csv
import numpy as np
import cv2
import texture_model as tm

try:
    from weights import THRESH_VIDEO as THRESH_PREF
except Exception:
    try:
        from weights import THRESH as THRESH_PREF
    except Exception:
        THRESH_PREF = 0.5

SUFFIXES = {'.mp4', '.mov', '.mkv', '.avi', '.webm', '.m4v'}
HAAR = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

def open_video(path: Path):
    for api in (cv2.CAP_FFMPEG, cv2.CAP_AVFOUNDATION, cv2.CAP_ANY):
        cap = cv2.VideoCapture(str(path), api)
        if cap.isOpened(): return cap
    return cv2.VideoCapture(str(path))

def get_face_crop(frame, target=256, pad_frac=0.12):
    g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = HAAR.detectMultiScale(g, 1.1, 5, minSize=(80, 80))
    if len(faces) == 0:
        return cv2.resize(frame, (target, target), cv2.INTER_AREA)
    x, y, w, h = max(faces, key=lambda f: f[2]*f[3])
    pad = int(pad_frac * max(w, h))
    H, W = frame.shape[:2]
    x1 = max(x - pad, 0); y1 = max(y - pad, 0)
    x2 = min(x + w + pad, W); y2 = min(y + h + pad, H)
    return cv2.resize(frame[y1:y2, x1:x2], (target, target), cv2.INTER_AREA)

def ema_series(values, alpha):
    out, prev = [], None
    for v in values:
        prev = v if prev is None else alpha * v + (1 - alpha) * prev
        out.append(float(prev))
    return out

def score_video(video_path: Path, every: int, target_tau: float, perc: float,
                heatmap_dir: Path | None, save_first_n_heatmaps: int = 20):
    cap = open_video(video_path)
    if not cap.isOpened():
        print(f"[warn] cannot open: {video_path.name}")
        return None

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    # dynamic alpha from target time constant (seconds)
    alpha = float(min(0.6, max(0.15, 1.0 - np.exp(- (every / max(1.0, fps)) / target_tau ))))

    idx = 0
    susp = []
    if heatmap_dir:
        heatmap_dir.mkdir(parents=True, exist_ok=True)
    saved_hm = 0

    while True:
        ok, frame = cap.read()
        if not ok: break
        if idx % every:
            idx += 1; continue
        face = get_face_crop(frame, target=256)
        d = tm.frame_score(face)
        susp.append(float(d["suspicion"]))
        if heatmap_dir and saved_hm < save_first_n_heatmaps:
            out_path = heatmap_dir / f"{video_path.stem}_heat_{idx:06d}.jpg"
            cv2.imwrite(str(out_path), d["overlay"]); saved_hm += 1
        idx += 1

    cap.release()
    if not susp:
        return {"video": str(video_path), "frames_scored": 0, "video_score": None, "decision": None}

    ema = ema_series(susp, alpha)
    video_score = float(np.percentile(ema, perc))

    thr = THRESH_PREF
    # guard: require at least K smoothed frames across threshold
    k_required = max(3, len(ema) // 20)  # ~5% of sampled frames, min 3
    decision = (video_score >= thr) and (sum(s >= thr for s in ema) >= k_required)

    return {
        "video": str(video_path),
        "frames_scored": len(susp),
        "fps": float(fps),
        "alpha": alpha,
        "percentile": perc,
        "video_score": video_score,
        "threshold_used": float(thr),
        "k_required": int(k_required),
        "k_hits": int(sum(s >= thr for s in ema)),
        "decision": bool(decision)
    }

def score_folder(data_dir: Path, every: int, target_tau: float, perc: float,
                 out_csv: Path | None, out_json: Path | None, heatmaps: Path | None):
    vids = [p for p in data_dir.rglob('*') if p.suffix.lower() in SUFFIXES]
    if not vids:
        print(f"[error] no videos under {data_dir}"); return
    print(f"[info] found {len(vids)} videos under {data_dir}")

    writer = None; csv_file = None
    if out_csv:
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        csv_file = out_csv.open("w", newline="")
        writer = csv.DictWriter(csv_file, fieldnames=[
            "video","frames_scored","fps","alpha","percentile",
            "video_score","threshold_used","k_required","k_hits","decision"
        ])
        writer.writeheader()

    all_results = []
    try:
        for vp in vids:
            print(f"[info] scoring {vp.name} …")
            res = score_video(vp, every=every, target_tau=target_tau, perc=perc, heatmap_dir=heatmaps)
            if res is None: 
                print(f"[warn] skipped {vp.name}"); continue
            all_results.append(res)
            print(f"  frames={res['frames_scored']} score={res['video_score']:.3f} "
                  f"thr={res['threshold_used']:.3f} hits={res['k_hits']}/{res['k_required']} "
                  f"→ decision={res['decision']}")
            if writer: writer.writerow(res)
    finally:
        if csv_file: csv_file.close()

    if out_json:
        out_json.parent.mkdir(parents=True, exist_ok=True)
        with out_json.open("w") as f:
            json.dump(all_results, f, indent=2)
        print(f"[info] wrote JSON -> {out_json.resolve()}")
    print("[done]")

def main():
    ap = argparse.ArgumentParser(description="Video-level scoring with EMA+pXX.")
    base = Path(__file__).resolve().parent
    ap.add_argument("--data-dir", default=str(base / "test_data"))
    ap.add_argument("--every", type=int, default=3, help="Sample every Nth frame.")
    ap.add_argument("--tau", type=float, default=0.6, help="EMA time constant (seconds) for smoothing.")
    ap.add_argument("--percentile", type=float, default=95.0, help="Percentile over EMA series.")
    ap.add_argument("--out-csv", default=str(base / "out" / "videos.csv"))
    ap.add_argument("--out-json", default=str(base / "out" / "videos.json"))
    ap.add_argument("--heatmaps", default=str(base / "out" / "heatmaps"))
    args = ap.parse_args()

    score_folder(
        data_dir=Path(args.data_dir),
        every=args.every, target_tau=args.tau, perc=args.percentile,
        out_csv=Path(args.out_csv), out_json=Path(args.out_json),
        heatmaps=Path(args.heatmaps)
    )

if __name__ == "__main__":
    main()
