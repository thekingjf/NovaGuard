# backend/build_dataset.py
from pathlib import Path
import argparse, csv
import numpy as np, cv2

# Keep in sync with scaler_values/texture_model
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
    vb = g[:, 7::8] - g[:, 8::8]
    hb = g[7::8, :] - g[8::8, :]
    return float(np.mean(np.abs(vb)) + np.mean(np.abs(hb)))

def chroma_luma_mismatch(bgr):
    yuv = cv2.cvtColor(bgr, cv2.COLOR_BGR2YUV)
    Y, U, V = [x.astype(np.float32) for x in cv2.split(yuv)]
    Gy = cv2.Sobel(Y, cv2.CV_32F, 1, 1)
    Gu = cv2.Sobel(U, cv2.CV_32F, 1, 1)
    Gv = cv2.Sobel(V, cv2.CV_32F, 1, 1)
    cu = np.corrcoef(Gy.ravel(), Gu.ravel())[0, 1]
    cv = np.corrcoef(Gy.ravel(), Gv.ravel())[0, 1]
    return float(1.0 - 0.5*(cu + cv))

HAAR = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
def get_face(bgr, target=256):
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    faces = HAAR.detectMultiScale(g, 1.1, 5, minSize=(80,80))
    if len(faces)==0:
        return cv2.resize(bgr,(target,target),cv2.INTER_AREA)
    x,y,w,h = max(faces, key=lambda f:f[2]*f[3])
    return cv2.resize(bgr[y:y+h, x:x+w], (target,target), cv2.INTER_AREA)

def extract_rows(video_path, label, every=5, max_frames=300):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"[warn] cannot open: {video_path.name}"); return []
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    rows, idx, saved = [], 0, 0
    while True:
        ok, frame = cap.read()
        if not ok: break
        if idx % every:
            idx += 1; continue
        face = get_face(frame)
        gray = preprocess_gray(face)
        m1 = compute_sharpness(gray)
        m2 = compute_high_ratio(gray)
        H, W = gray.shape
        y0 = int(H * ROI_LOWER_FRAC)
        m3 = edge_glitch_score(gray[y0:H, :])
        m4 = block_boundary_energy(gray)
        m5 = chroma_luma_mismatch(face)
        rows.append(dict(video=video_path.name, label=label, frame_idx=idx,
                         time_sec=round(idx/float(fps),3),
                         sharp_var=m1, high_ratio=m2, edge_glitch=m3,
                         block_energy=m4, chroma_mismatch=m5))
        saved += 1
        if saved >= max_frames: break
        idx += 1
    cap.release()
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--real-dir", default="backend/real_data")
    ap.add_argument("--fake-dir", default="backend/test_data")
    ap.add_argument("--out-csv",  default="backend/dataset.csv")
    ap.add_argument("--every", type=int, default=5)
    ap.add_argument("--max-frames", type=int, default=300)
    args = ap.parse_args()

    suf = {".mp4",".mov",".mkv",".avi",".webm",".m4v"}
    real = [p for p in Path(args.real_dir).rglob("*") if p.suffix.lower() in suf]
    fake = [p for p in Path(args.fake_dir).rglob("*") if p.suffix.lower() in suf]
    if not real: raise SystemExit(f"No real videos in {args.real_dir}")
    if not fake: raise SystemExit(f"No fake videos in {args.fake_dir}")
    print(f"[info] real={len(real)}  fake={len(fake)}")

    out = Path(args.out_csv); out.parent.mkdir(parents=True, exist_ok=True)
    cols = ["video","label","frame_idx","time_sec","sharp_var","high_ratio","edge_glitch","block_energy","chroma_mismatch"]
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for p in real:
            for r in extract_rows(p, label=0, every=args.every, max_frames=args.max_frames): w.writerow(r)
        for p in fake:
            for r in extract_rows(p, label=1, every=args.every, max_frames=args.max_frames): w.writerow(r)
    print(f"[done] wrote {out.resolve()}")

if __name__ == "__main__":
    main()
