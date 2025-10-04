import numpy as np
import torch

@torch.no_grad()
def bootstrap_ci(fake_logits, B=500, alpha=0.05):
    if fake_logits.numel() == 0:
        return (float('nan'), float('nan'))
    fl = fake_logits.numpy()
    samples = []
    n = len(fl)
    rng = np.random.default_rng(1337)
    for _ in range(B):
        idx = rng.integers(0, n, size=n)
        m = fl[idx].mean()
        samples.append(1/(1+np.exp(-m)))
    lo, hi = np.quantile(samples, [alpha/2, 1-alpha/2])
    return float(lo), float(hi)
