# backend/scaler_values.py
from pathlib import Path
import argparse
import numpy as np
import cv2

CACHE_PATH = Path(__file__).resolve().parent / "scaler_values_cache.npz"

# --- same tunables/features as texture_model.py (must match) ---
ROI_LOWER_FRAC = 0.55
LAPLACIAN_KS   = (3, 5)
FFT_DIVISOR    = 12
EDGE_TILE      = 8
SOBEL_K        = 3
CLAHE_CLIP     = 2.0
CLAHE_TILE     = (8, 8)
GAUSS_BLUR_K   = 3

def preprocess_gray(bgr):
    yuv = cv2.cvtColor(bgr, cv2.COLOR_BGR2YUV)
    Y = yuv[:, :, 0]
    clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP, tileGridSize=CLAHE_TILE)
    Y = clahe.apply(Y)
    if GAUSS_BLUR_K and GAUSS_BLUR_K >= 3:
        Y = cv2.GaussianBlur(Y, (GAUSS_BLUR_K, GAUSS_BLUR_K), 0)
    return Y

def compute_sharpness(gray):
    vars_ = [cv2.Laplacian(gray, cv2.CV_32F, ksize=k).var() for k in LAPLACIAN_KS]
    return float(np.mean(vars_))

def compute_high_ratio(gray):
    H, W = gray.shape
    win = np.outer(np.hanning(H), np.hanning(W)).astype(np.float32)
    F = np.fft.fftshift(np.fft.fft2(gray * win))
    mag = (np.abs(F)**2).astype(np.float32)
    cy, cx = H//2, W//2
    r0 = max(2, min(H, W)//FFT_DIVISOR)
    Y, X = np.ogrid[:H, :W]
    mask_hi = (Y-cy)**2 + (X-cx)**2 >= (r0*r0)
    hi = float(mag[mask_hi].sum())
    tot = float(mag.sum()) + 1e-8
    return hi / tot

def edge_glitch_score(gray_roi):
    gx = cv2.Sobel(gray_roi, cv2.CV_32F, 1, 0, ksize=SOBEL_K)
    gy = cv2.Sobel(gray_roi, cv2.CV_32F, 0, 1, ksize=SOBEL_K)
    G  = np.sqrt(gx*gx + gy*gy)
    Gn = G / (G.mean() + 1e-8)
    win, vals = EDGE_TILE, []
    H, W = Gn.shape
    for y in range(0, H - win + 1, win):
        for x in range(0, W - win + 1, win):
            vals.append(Gn[y:y+win, x:x+win].std())
    if not vals: return 0.0
    vals = np.array(vals, np.float32)
    return float(np.percentile(vals, 90) - np.median(vals))

def block_boundary_energy(gray):
    g = gray.astype(np.float32)
    H, W = g.shape

    # Vertical 8x8 boundaries: compare col k vs k+1 for k = 7,15,23,..., up to W-2
    vb_left  = g[:, 7:-1:8]   # stops at W-2 at most → length N
    vb_right = g[:, 8::8]     # starts at 8 → length N
    if vb_left.size == 0 or vb_right.size == 0:
        v_mean = 0.0
    else:
        v_mean = float(np.mean(np.abs(vb_left - vb_right)))

    # Horizontal 8x8 boundaries: compare row k vs k+1 for k = 7,15,23,..., up to H-2
    hb_top   = g[7:-1:8, :]   # length M
    hb_bot   = g[8::8,  :]    # length M
    if hb_top.size == 0 or hb_bot.size == 0:
        h_mean = 0.0
    else:
        h_mean = float(np.mean(np.abs(hb_top - hb_bot)))

    return v_mean + h_mean


def chroma_luma_mismatch(bgr):
    yuv = cv2.cvtColor(bgr, cv2.COLOR_BGR2YUV)
    Y, U, V = [x.astype(np.float32) for x in cv2.split(yuv)]
    Gy = cv2.Sobel(Y, cv2.CV_32F, 1, 1)
    Gu = cv2.Sobel(U, cv2.CV_32F, 1, 1)
    Gv = cv2.Sobel(V, cv2.CV_32F, 1, 1)
    cu = np.corrcoef(Gy.ravel(), Gu.ravel())[0, 1]
    cv = np.corrcoef(Gy.ravel(), Gv.ravel())[0, 1]
    return float(1.0 - 0.5 * (cu + cv))

# --- simple face crop (fallback to whole frame) ---
HAAR = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
def face_crop(bgr, target=256):
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    faces = HAAR.detectMultiScale(g, 1.1, 5, minSize=(80, 80))
    if len(faces) == 0:
        return cv2.resize(bgr, (target, target), cv2.INTER_AREA)
    x, y, w, h = max(faces, key=lambda f: f[2]*f[3])
    return cv2.resize(bgr[y:y+h, x:x+w], (target, target), cv2.INTER_AREA)

def feature_vector(face_bgr):
    gray = preprocess_gray(face_bgr)
    m1 = compute_sharpness(gray)
    m2 = compute_high_ratio(gray)
    H, W = gray.shape
    y0 = int(H * ROI_LOWER_FRAC)
    m3 = edge_glitch_score(gray[y0:H, :])
    m4 = block_boundary_energy(gray)
    m5 = chroma_luma_mismatch(face_bgr)
    return np.array([m1, m2, m3, m4, m5], dtype=np.float32)

# --- scaler class + loader ---
class FixedScaler:
    def __init__(self, mean, scale):
        self.mean  = np.asarray(mean,  dtype=np.float32).ravel()
        self.scale = np.asarray(scale, dtype=np.float32).ravel()
        if self.mean.shape != self.scale.shape:
            raise ValueError("mean and scale must have same shape")
    def transform(self, X):
        X = np.asarray(X, dtype=np.float32)
        return (X - self.mean) / (self.scale + 1e-8)

def _load_from_cache(path: Path = CACHE_PATH) -> FixedScaler:
    if not path.exists():
        print(f"[scaler_values] WARNING: cache missing at {path}. Using identity scaler.")
        return FixedScaler([0,0,0,0,0], [1,1,1,1,1])
    d = np.load(path)
    return FixedScaler(d["mean"], d["scale"])

# Export on import
scaler = _load_from_cache()

# --- CLI: fit scaler on REAL videos and save cache ---
def _fit_from_folder(real_dir: Path, every=5, max_frames=400):
    suf = {".mp4",".mov",".mkv",".avi",".webm",".m4v"}
    vids = [p for p in real_dir.rglob("*") if p.suffix.lower() in suf]
    if not vids:
        raise SystemExit(f"No videos in {real_dir}")
    X = []
    for vp in vids:
        cap = cv2.VideoCapture(str(vp))
        if not cap.isOpened():
            print(f"[warn] skip {vp.name}"); continue
        idx = saved = 0
        while True:
            ok, f = cap.read()
            if not ok: break
            if idx % every:
                idx += 1; continue
            face = face_crop(f)
            X.append(feature_vector(face))
            saved += 1; idx += 1
            if saved >= max_frames: break
        cap.release()
    X = np.array(X, np.float32)
    if len(X) < 20:
        raise SystemExit(f"Too few samples: {len(X)}")
    mean, std = X.mean(0), X.std(0)
    np.savez_compressed(CACHE_PATH, mean=mean.astype(np.float32), scale=std.astype(np.float32))
    print(f"[ok] wrote {CACHE_PATH}")
    print("[mean]", mean)
    print("[std ]", std)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--real-dir", default=str(Path(__file__).resolve().parent / "real_data"))
    ap.add_argument("--every", type=int, default=5)
    ap.add_argument("--max-frames", type=int, default=400)
    ap.add_argument("--print-stats", dest="print_stats", action="store_true")
    ap.add_argument("--fit", action="store_true", help="Fit scaler cache from real videos")
    args = ap.parse_args()

    if args.fit:
        _fit_from_folder(Path(args.real_dir), every=args.every, max_frames=args.max_frames)

    if args.print_stats:
        s = _load_from_cache()
        print("cache:", CACHE_PATH)
        print("mean =", s.mean)
        print("std  =", s.scale)


    if args.fit:
        _fit_from_folder(Path(args.real_dir), every=args.every, max_frames=args.max_frames)
    if args.print_stats:
        s = _load_from_cache()
        print("cache:", CACHE_PATH)
        print("mean =", s.mean)
        print("std  =", s.scale)
