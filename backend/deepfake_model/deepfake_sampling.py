# Video Sampling

import torch, cv2, math
import numpy as np
from facenet_pytorch import MTCNN
from torchvision.transforms import functional as TF

def _resize_with_aspect(img, size):
    h,w = img.shape[:2]; s = size / max(h,w)
    return cv2.resize(img, (int(w*s), int(h*s)), interpolation=cv2.INTER_LINEAR)

class FaceSampler:
    def __init__(self, fps=8, input_size=224, margin=0.25, min_face=80, align_eyes=True, device='cpu'):
        self.target_fps = fps
        self.size = input_size
        self.margin = margin
        self.min_face = min_face
        self.align_eyes = align_eyes
        self.detector = MTCNN(keep_all=True, device=device)

    def _crop_expand(self, img, box):
        h, w = img.shape[:2]
        x1,y1,x2,y2 = [int(v) for v in box]
        bw, bh = x2-x1, y2-y1
        mx, my = int(bw*self.margin), int(bh*self.margin)
        x1, y1 = max(0, x1-mx), max(0, y1-my)
        x2, y2 = min(w, x2+mx), min(h, y2+my)
        return img[y1:y2, x1:x2]

    def _align(self, img, eyes):  # simple rotation alignment if both eyes are available
        (lx,ly), (rx,ry) = eyes
        dx, dy = (rx-lx), (ry-ly)
        angle = math.degrees(math.atan2(dy, dx))
        M = cv2.getRotationMatrix2D(((img.shape[1])/2, (img.shape[0])/2), angle, 1.0)
        return cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), flags=cv2.INTER_LINEAR)

    def _choose_face(self, boxes):
        # choose largest area
        areas = [(b[2]-b[0])*(b[3]-b[1]) for b in boxes]
        return int(np.argmax(areas)) if len(areas) else None

    def sample(self, video_path, max_frames=256):
        # decode video with OpenCV (ok for baseline); replace with decord if preferred
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened(): raise RuntimeError(f"Cannot open {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        step = max(1, int(round(fps / self.target_fps)))
        frames, idx = [], 0

        while True:
            ret, frame = cap.read()
            if not ret: break
            if idx % step == 0:
                frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            idx += 1
            if len(frames) >= max_frames: break
        cap.release()

        crops, meta = [], []
        for i, img in enumerate(frames):
            boxes, probs, landmarks = self.detector.detect(img, landmarks=True)
            if boxes is not None and len(boxes) > 0:
                keep = [i for i,(b,p) in enumerate(zip(boxes, probs)) if (p is None or p >= 0.90)]
                if keep:
                    j = self._choose_face(boxes)
                    box = boxes[j]
                    if (box[2]-box[0]) >= self.min_face and (box[3]-box[1]) >= self.min_face:
                        crop = self._crop_expand(img, box)
                        if self.align_eyes and landmarks is not None and landmarks[j] is not None:
                            left_eye, right_eye = landmarks[j][0], landmarks[j][1]
                            crop = self._align(crop, (left_eye, right_eye))
                        crop = cv2.resize(crop, (self.size, self.size), interpolation=cv2.INTER_LINEAR)
                        crops.append(crop)
                        meta.append({'frame_idx': i, 'face': True})
                        continue
            # fallback: center crop when no face
            h,w = img.shape[:2]
            m = min(h,w); y0, x0 = (h-m)//2, (w-m)//2
            crop = cv2.resize(img[y0:y0+m, x0:x0+m], (self.size, self.size), interpolation=cv2.INTER_LINEAR)
            crops.append(crop); meta.append({'frame_idx': i, 'face': False})
        return np.stack(crops) if crops else np.zeros((0, self.size, self.size, 3), dtype=np.uint8), meta
