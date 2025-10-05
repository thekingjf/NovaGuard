# backend/texture_model.py
import cv2, numpy as np
from scaler_values import scaler  # loads mean/std from cache

# Try to use learned weights; fall back to simple ones
try:
    from weights import W, B
except Exception:
    W = np.array([0.4, 0.4, 0.2, 0.0, 0.0], dtype=np.float32)  # if only 3 features in cache, scaler will raise until you refit
    B = 0.0

# -------- Tunables (quick knobs) --------
FACE_SIZE      = 256
ROI_LOWER_FRAC = 0.55   # lower fraction for mouth/cheek ROI
LAPLACIAN_KS   = (3, 5) # multi-scale Laplacian
FFT_DIVISOR    = 12     # high-pass cutoff radius = min(H,W)//divisor
EDGE_TILE      = 8      # smaller = more sensitive to local jitter
SOBEL_K        = 3
CLAHE_CLIP     = 2.0
CLAHE_TILE     = (8, 8)
GAUSS_BLUR_K   = 3      # set to 0 to disable

# -------- Helpers (must match dataset/scaler feature defs) --------
def preprocess_gray(face_bgr):
    yuv = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2YUV)
    Y = yuv[:, :, 0]
    clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP, tileGridSize=CLAHE_TILE)
    Y = clahe.apply(Y)
    if GAUSS_BLUR_K and GAUSS_BLUR_K >= 3:
        Y = cv2.GaussianBlur(Y, (GAUSS_BLUR_K, GAUSS_BLUR_K), 0)
    return Y

def compute_sharpness(gray):
    vars_ = [cv2.Laplacian(gray, cv2.CV_32F, ksize=k).var() for k in LAPLACIAN_KS]
    lap_for_heat = cv2.Laplacian(gray, cv2.CV_32F, ksize=LAPLACIAN_KS[0])
    return float(np.mean(vars_)), lap_for_heat

def compute_high_ratio(gray):
    H, W = gray.shape
    win = np.outer(np.hanning(H), np.hanning(W)).astype(np.float32)
    F = np.fft.fftshift(np.fft.fft2(gray * win))
    mag = (np.abs(F) ** 2).astype(np.float32)
    cy, cx = H // 2, W // 2
    r0 = max(2, min(H, W) // FFT_DIVISOR)
    Y, X = np.ogrid[:H, :W]
    mask_hi = (Y - cy) ** 2 + (X - cx) ** 2 >= (r0 * r0)
    hi = float(mag[mask_hi].sum())
    tot = float(mag.sum()) + 1e-8
    return hi / tot

def edge_glitch_score(gray_roi):
    gx = cv2.Sobel(gray_roi, cv2.CV_32F, 1, 0, ksize=SOBEL_K)
    gy = cv2.Sobel(gray_roi, cv2.CV_32F, 0, 1, ksize=SOBEL_K)
    G  = np.sqrt(gx*gx + gy*gy)
    Gn = G / (G.mean() + 1e-8)  # normalize per-ROI
    win, vals = EDGE_TILE, []
    H, W = Gn.shape
    for y in range(0, H - win + 1, win):
        for x in range(0, W - win + 1, win):
            vals.append(Gn[y:y+win, x:x+win].std())
    if not vals:
        return 0.0
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


def chroma_luma_mismatch(face_bgr):
    yuv = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2YUV)
    Y, U, V = [x.astype(np.float32) for x in cv2.split(yuv)]
    Gy = cv2.Sobel(Y, cv2.CV_32F, 1, 1)
    Gu = cv2.Sobel(U, cv2.CV_32F, 1, 1)
    Gv = cv2.Sobel(V, cv2.CV_32F, 1, 1)
    cu = np.corrcoef(Gy.ravel(), Gu.ravel())[0, 1]
    cv = np.corrcoef(Gy.ravel(), Gv.ravel())[0, 1]
    return float(1.0 - 0.5 * (cu + cv))

def heatmap_from_laplacian(face_bgr, lap):
    hm = (255 * (np.abs(lap) / (np.abs(lap).max() + 1e-8))).astype(np.uint8)
    hm = cv2.applyColorMap(hm, cv2.COLORMAP_JET)
    return cv2.addWeighted(face_bgr, 0.65, hm, 0.35, 0)

# -------- Public API --------
def frame_score(face_bgr):
    gray = preprocess_gray(face_bgr)

    sharp_var, lap = compute_sharpness(gray)
    high_ratio = compute_high_ratio(gray)

    H, W = gray.shape
    y0 = int(H * ROI_LOWER_FRAC)
    edge_glitch = edge_glitch_score(gray[y0:H, :])

    blk = block_boundary_energy(gray)
    clm = chroma_luma_mismatch(face_bgr)

    feats = np.array([sharp_var, high_ratio, edge_glitch, blk, clm], dtype=np.float32)
    z = scaler.transform([feats])[0]  # z-score with REAL-only stats

    Wv = np.asarray(W, dtype=np.float32).reshape(-1)
    Zv = np.asarray(z, dtype=np.float32).reshape(-1)
    if Wv.shape[0] != Zv.shape[0]:
        if Wv.shape[0] < Zv.shape[0]:
            Wv = np.pad(Wv, (0, Zv.shape[0]-Wv.shape[0]), constant_values=0.0)
        else:
            Wv = Wv[:Zv.shape[0]]
    raw = float(np.dot(Wv, Zv) + float(B))
    suspicion = 1.0 / (1.0 + np.exp(-raw))
    overlay = heatmap_from_laplacian(face_bgr, lap)

    return dict(
        sharp_var=float(sharp_var),
        high_ratio=float(high_ratio),
        edge_glitch=float(edge_glitch),
        block_energy=float(blk),
        chroma_mismatch=float(clm),
        suspicion=float(suspicion),
        overlay=overlay,
    )
