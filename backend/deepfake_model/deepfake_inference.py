# deepfake_inference.py
import torch
from torch.utils.data import DataLoader, Dataset

class CropDataset(Dataset):
    def __init__(self, crops, mean, std):
        self.crops = crops
        self.mean = torch.tensor(mean).view(3,1,1)
        self.std  = torch.tensor(std).view(3,1,1)

    def __len__(self): return len(self.crops)

    def __getitem__(self, i):
        img = self.crops[i]  # HWC uint8 RGB
        t = torch.from_numpy(img).permute(2,0,1).float() / 255.0
        t = (t - self.mean) / self.std
        return t

@torch.no_grad()
def run_inference(model, crops, mean, std, batch_size=64, half=True, device="cuda", size=299):
    """
    Run the model on a list of face crops.

    Args:
        model: torch.nn.Module
        crops: list of HxWxC numpy arrays (uint8 or float), RGB or BGR is fine
        mean, std: iterable of 3 floats (channel-wise), e.g. [0.5,0.5,0.5]
        batch_size: inference batch size
        half: if True, try FP16; will only be used when device starts with 'cuda'
        device: 'cuda' or 'cpu'
        size: side length to resize crops to (e.g., 299 for Xception)

    Returns:
        torch.FloatTensor of logits on CPU with shape [N, num_classes]
    """
    import numpy as np
    import torch
    import cv2

    # no crops → empty logits
    if not crops:
        return torch.empty((0, 2))

    # only enable half precision on CUDA
    use_half = bool(half) and str(device).startswith("cuda")

    model = model.to(device).eval()
    if use_half:
        model.half()

    # prepare normalization tensors
    mean = np.asarray(mean, dtype=np.float32).reshape(3, 1, 1)
    std = np.asarray(std, dtype=np.float32).reshape(3, 1, 1)

    def preprocess(img):
        # img: HxWxC (uint8/float), possible gray/RGBA
        if img.ndim == 2:
            img = np.repeat(img[..., None], 3, axis=2)
        if img.shape[2] == 4:  # RGBA → RGB
            img = img[:, :, :3]

        img = img.astype(np.float32)
        if img.max() > 1.0:
            img /= 255.0

        # resize with area interpolation for downscale quality
        img = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)

        # HWC → CHW and normalize
        img = np.transpose(img, (2, 0, 1))
        img = (img - mean) / std
        t = torch.from_numpy(img)  # float32 CHW
        return t

    tensors = [preprocess(c) for c in crops]

    all_logits = []
    n = len(tensors)
    i = 0
    while i < n:
        batch = tensors[i : i + batch_size]
        x = torch.stack(batch, dim=0)  # [B,3,H,W]
        if use_half:
            x = x.half()
        x = x.to(device, non_blocking=True)

        with torch.no_grad():
            logits = model(x)

        all_logits.append(logits.detach().to("cpu"))
        i += batch_size

    return torch.cat(all_logits, dim=0)



def aggregate_logits(logits, head_type="2c", fake_index=1, temperature=1.0):
    if head_type == "1c":
        fake_log = logits.view(-1)
    else:
        fi = int(fake_index); other = 1 - fi
        fake_log = logits[:, fi] - logits[:, other]
    video_logit = fake_log.mean() / max(float(temperature), 1e-6)
    p_fake = torch.sigmoid(video_logit).item()
    return p_fake, video_logit.item()
