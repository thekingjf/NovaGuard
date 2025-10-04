import cv2, numpy as np
from scaler_values import scaler

# optional guard so missing mediapipe doesn't break import
try:
    import mediapipe as mp
    mp_face = mp.solutions.face_mesh
    mp_det  = mp.solutions.face_detection
except Exception:
    mp = mp_face = mp_det = None

# Defined funciton to take the laplacian (edge detection) where gray is an array and checks with a discrete laplacian 
# how different a pixel is from its neighbors (weighted sum) and it returns that and the variance.   
def compute_sharpness(gray):
    lap = cv2.Laplacian(gray, cv2.CV_32F, ksize=3)
    return lap.var(), lap

# Takes image into freq. domain, centers, and squares magnitudes. The center holds low freq. 
# so defines a small square and zeros it out leaving high frequencies powers then returns ratio power in high freq over power in all
# frequncies. r picks square relative to image, and e8 prevents division by 0. Closer to 1 = more fine details/edges. Closer to 0 = 
# image dominated by low frequencies/smooth content
def compute_high_ratio(gray):
    F = np.fft.fft2(gray); F = np.fft.fftshift(F); mag = np.abs(F)**2
    r = min(gray.shape)//12
    h = mag.copy()
    H, W = mag.shape; cy, cx = H//2, W//2
    h[cy-r:cy+r, cx-r:cx+r] = 0
    return float(h.sum()/(mag.sum()+1e-8))

# Makes edge-strength map to measure how "jittery" edges are to STD and returns "score" of how much those tiles j
# itter compared to median tiles (after dividng into 16x16 tiles). Bigger score = messier region. Lower score = more uniform. 
# AI tends to leave messy edges in its content. 
def edge_glitch_score(gray_roi):
    gx = cv2.Sobel(gray_roi, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray_roi, cv2.CV_32F, 0, 1, ksize=3)
    G  = np.sqrt(gx*gx + gy*gy)
    win, vals = 16, []
    for y in range(0, G.shape[0]-win+1, win):
        for x in range(0, G.shape[1]-win+1, win):
            vals.append(G[y:y+win, x:x+win].std())
    return float(np.percentile(vals, 95) - np.median(vals))

# This creates a heatmap that points out extraneous regions (over-sharp, noisy, artificed edges) with hotter colors and with 
# cooler colors, smoother, more natural regions. 
def heatmap_from_laplacian(face_bgr, lap):
    hm = (255 * (np.abs(lap) / (np.abs(lap).max()+1e-8))).astype(np.uint8)
    hm = cv2.applyColorMap(hm, cv2.COLORMAP_JET)
    return cv2.addWeighted(face_bgr, 0.65, hm, 0.35, 0)

# MediaPipe setup. Use detection to find the face box and then face mesh to detect facial keypoints. 
mp_face = mp.solutions.face_mesh
mp_det  = mp.solutions.face_detection

# Creates coordinates around mouth and finds smallest box around it with some error room and then returns that box. 
def mouth_roi_from_landmarks(face_bgr, landmarks):
    # simplest: bounding box around mouth indices (e.g., FaceMesh 78..308 inner/outer lips)
    H, W = face_bgr.shape[:2]
    mouth_ids = [78,80,81,82,13,312,311,310,308,14] 
    xs = [int(lm.x*W) for i, lm in enumerate(landmarks) if i in mouth_ids]
    ys = [int(lm.y*H) for i, lm in enumerate(landmarks) if i in mouth_ids]
    x1,y1,x2,y2 = max(min(xs)-6,0), max(min(ys)-6,0), min(max(xs)+6,W), min(max(ys)+6,H)
    return (x1,y1,x2,y2)

# First turns the image into grayscale. Computes two global features. Then picks a mouth-ish region and computes 
# how uneven the edges are. Next it normalizes and takes a weighted sum. It passes through a sigmoid where 1 = very suspicious. 
# Builds heatmap overlay for the user. Returns the three features, heatmap overlay, and suspicion score. 

def frame_score(face_bgr):
    import numpy as _np
    gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
    sharp_var, lap = compute_sharpness(gray)
    high_ratio = compute_high_ratio(gray)

    # mouth-ish ROI = lower half
    H, W = gray.shape
    edge_glitch = edge_glitch_score(gray[H // 2 : H, :])

    # normalize + combine
    z = scaler.transform([[sharp_var, high_ratio, edge_glitch]])[0]
    raw = 0.4 * z[0] + 0.4 * z[1] + 0.2 * z[2]
    suspicion = 1.0 / (1.0 + _np.exp(-raw))

    overlay = heatmap_from_laplacian(face_bgr, lap)
    return {
        "sharp_var": float(sharp_var),
        "high_ratio": float(high_ratio),
        "edge_glitch": float(edge_glitch),
        "suspicion": float(suspicion),
        "overlay": overlay,
    }
