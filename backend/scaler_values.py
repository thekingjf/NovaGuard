from pathlib import Path
import numpy as np

CACHE_PATH = Path(__file__).resolve().parent / "scaler_values_cache.npz"

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
        # Fall back to identity if the cache isn't there yet
        print(f"[scaler_values] WARNING: cache missing at {path}. Using identity scaler.")
        return FixedScaler([0,0,0], [1,1,1])
    d = np.load(path)
    return FixedScaler(d["mean"], d["scale"])

# ---- export on import (module-level, no indentation) ----
scaler = _load_from_cache()
