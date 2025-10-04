import torch
from torch.utils.data import DataLoader, Dataset

class CropDataset(Dataset):
    def __init__(self, crops, mean, std):
        self.crops = crops
        self.mean = torch.tensor(mean).view(3,1,1)
        self.std  = torch.tensor(std).view(3,1,1)

    def __len__(self): return len(self.crops)

    def __getitem__(self, i):
        img = self.crops[i]  # HWC, uint8 RGB
        t = torch.from_numpy(img).permute(2,0,1).float() / 255.0
        t = (t - self.mean) / self.std
        return t

@torch.no_grad()
def run_inference(model, crops, batch_size=64, half=False, device='cuda'):
    if len(crops) == 0:
        return torch.empty((0,2))
    ds = CropDataset(crops, mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
    dl = DataLoader(ds, batch_size=batch_size, shuffle=False, num_workers=2, pin_memory=True)
    model.eval().to(device)
    if half: model.half()
    logits_all = []
    for x in dl:
        x = x.to(device)
        if half: x = x.half()
        logits = model(x)  # [B,2]
        logits_all.append(logits.float().cpu())
    return torch.cat(logits_all, dim=0)  # [N,2]

def aggregate_logits(logits_2c):
    # Probability of "fake" assumed at index 1
    fake_logits = logits_2c[:,1] - logits_2c[:,0]  # equivalent to logit(p_fake) for 2-class softmax
    video_logit = fake_logits.mean()
    p_fake = torch.sigmoid(video_logit).item()
    return p_fake, video_logit.item()
