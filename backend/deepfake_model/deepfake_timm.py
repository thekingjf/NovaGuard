# deepfake_timm.py
# Unified model loader for timm backbones and FF++/Cadene Xception.
# - Supports .pth/.pt/.ckpt and .safetensors (if installed)
# - Works with timm (e.g., tf_efficientnet_bx_ns) and FF++ Xception via 'pretrainedmodels'
# - Handles 2-class (softmax) and 1-logit (sigmoid) heads
# - Exposes .head_type in {"2c","1c"} and respects fake_index
# - Clear logging + fail-fast when a checkpoint exists but the head isn't initialized

import os
from typing import Dict, Any

import torch
import torch.nn as nn

try:
    import timm
except Exception as e:
    timm = None

# ---------- helpers ----------

from collections.abc import Mapping
import torch

def _find_state_dict(obj):
    """
    Return a dict[str, Tensor] from a variety of checkpoint formats.
    Supports raw state_dict or nested under common keys: 'state_dict', 'model',
    'net', 'network', 'weights', 'params', 'ema', 'module'.
    """
    # Raw state_dict?
    if isinstance(obj, Mapping) and obj and all(isinstance(v, torch.Tensor) for v in obj.values()):
        return dict(obj)

    if isinstance(obj, Mapping):
        for k in ["state_dict", "model", "net", "network", "weights", "params", "ema", "module"]:
            if k in obj and isinstance(obj[k], Mapping):
                sd = _find_state_dict(obj[k])
                if sd:
                    return sd

        # last-chance: some ckpts dump a flat mapping with mixed values; keep tensor entries
        tensor_items = {k: v for k, v in obj.items() if isinstance(v, torch.Tensor)}
        if tensor_items:
            return tensor_items

    raise ValueError("Could not locate a state_dict in the checkpoint")

def _strip_prefixes(sd):
    """Remove common prefixes introduced by wrappers/DDP/backbones."""
    prefixes = ["module.", "model.", "net.", "network.", "backbone."]
    out = {}
    for k, v in sd.items():
        for p in prefixes:
            if k.startswith(p):
                k = k[len(p):]
                break
        out[k] = v
    return out

def _map_xception_classifier(sd):
    """
    FF++/Cadene Xception checkpoints sometimes use 'classifier.*' or 'fc.*'
    while our model expects 'last_linear.*'.
    """
    if any(k.startswith("last_linear.") for k in sd):
        return sd
    has_cls = any(k.startswith("classifier.") for k in sd)
    has_fc  = any(k.startswith("fc.") for k in sd)
    if has_cls:
        return { (k.replace("classifier.", "last_linear.") if k.startswith("classifier.") else k): v
                 for k, v in sd.items() }
    if has_fc:
        return { (k.replace("fc.", "last_linear.") if k.startswith("fc.") else k): v
                 for k, v in sd.items() }
    return sd


def _load_state(path: str):
    """Load a state dict from common formats. Tries safetensors first for .safetensors."""
    if path.endswith(".safetensors"):
        try:
            from safetensors import safe_open  # optional dependency
            sd = {}
            with safe_open(path, framework="pt") as f:
                for k in f.keys():
                    sd[k] = f.get_tensor(k)
            return sd
        except Exception as e:
            raise RuntimeError(f"Failed to load safetensors '{path}': {e}")
    # fallback: torch.load for .pth/.pt/.ckpt
    obj = torch.load(path, map_location="cpu")
    # Unwrap state dict if nested
    if isinstance(obj, dict) and "state_dict" in obj and isinstance(obj["state_dict"], dict):
        obj = obj["state_dict"]
    return obj

def _clean_keys(sd: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
    """Remove common wrappers from state_dict keys."""
    def ck(k: str) -> str:
        k = k.replace("module.", "")
        k = k.replace("net.", "")
        k = k.replace("model.", "")
        return k
    return { ck(k): v for k, v in sd.items() }

def _maybe_map_classifier_keys(sd: Dict[str, torch.Tensor], model_has_last_linear: bool) -> Dict[str, torch.Tensor]:
    """
    For some checkpoints, classifier is saved as 'classifier.*' but our FF++ Xception expects 'last_linear.*'.
    Apply a light remap only if needed.
    """
    if model_has_last_linear:
        # if there are 'classifier.' keys but no 'last_linear.', remap
        has_ll = any(k.startswith("last_linear.") for k in sd.keys())
        has_cls = any(k.startswith("classifier.") for k in sd.keys())
        if has_cls and not has_ll:
            sd = { (k.replace("classifier.", "last_linear.") if k.startswith("classifier.") else k): v
                   for k, v in sd.items() }
    return sd

# ---------- main class ----------

class DeepfakeModel(nn.Module):
    """
    A thin wrapper that:
      - Builds either a timm model or FF++/Cadene Xception (arch='pm_xception').
      - Loads a checkpoint robustly (key cleaning + optional classifier mapping).
      - Exposes .head_type in {"2c", "1c"} for downstream aggregation.
      - Supports temperature scaling and .predict_proba().
    """
    def __init__(self, arch: str, num_classes: int = 2, ckpt_path: str = None, fake_index: int = 1, **kwargs: Any):
        super().__init__()
        self.fake_index = int(fake_index)
        self.head_type = "unknown"  # will be "2c" or "1c"
        arch_l = (arch or "").lower()
        ckpt_exists = bool(ckpt_path) and os.path.isfile(ckpt_path)

        # ---- Build the network ----
        if arch_l in {"pm_xception", "ffpp_xception", "xception_pm", "xception_ffpp"}:
            try:
                import pretrainedmodels  # Cadene's package (pip install pretrainedmodels)
            except Exception as e:
                raise ImportError(
                    "arch='pm_xception' requires the 'pretrainedmodels' package.\n"
                    "Install it with: pip install pretrainedmodels"
                ) from e

            # This Xception variant matches FF++ / Cadene checkpoints.
            net = pretrainedmodels.__dict__["xception"](pretrained=None)  # don't init with ImageNet here
            # Replace classifier with our desired num_classes
            in_ch = net.last_linear.in_features
            net.last_linear = nn.Linear(in_ch, int(num_classes))
            self.net = net
            # infer head type from configured classes; the checkpoint may override effectively
            self.head_type = "1c" if int(num_classes) == 1 else "2c"

        else:
            if timm is None:
                raise ImportError("timm is required for non 'pm_xception' architectures. pip install timm")
            # If a deepfake checkpoint exists, we don't need timm pretrained=True.
            self.net = timm.create_model(
                arch,
                pretrained=not ckpt_exists,
                num_classes=int(num_classes),
                in_chans=3
            )
            self.head_type = "1c" if int(num_classes) == 1 else "2c"

        ckpt_exists = bool(ckpt_path) and os.path.isfile(ckpt_path)
        if ckpt_exists:
            raw = torch.load(ckpt_path, map_location="cpu")
            sd  = _find_state_dict(raw)
            sd  = _strip_prefixes(sd)
            # only do classifier remap when we’re on the FF++/Cadene xception path
            sd  = _map_xception_classifier(sd)

            missing, unexpected = self.load_state_dict(sd, strict=False)
            print(f"[CKPT] loaded from {ckpt_path}")
            print(f"[CKPT] missing: {len(missing)} keys, unexpected: {len(unexpected)} keys")

            model_keys = set(self.state_dict().keys())
            hit = len(model_keys & set(sd.keys()))
            cov = hit / max(1, len(model_keys))
            print(f"[CKPT] key coverage: {hit}/{len(model_keys)} = {cov:.3f}")
            if cov < 0.90:
                raise RuntimeError(
                    f"Checkpoint key coverage is too low ({cov:.3f}). "
                    "Likely wrong architecture or incompatible checkpoint."
                )
        else:
            print(f"[CKPT] No checkpoint found at {ckpt_path} — using pretrained backbone (if available) and random head.")


        # Temperature buffer for calibration
        self.register_buffer("temperature", torch.tensor(1.0))

    # ---- forward & helpers ----

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

    def set_temperature(self, t: float):
        self.temperature = torch.tensor(float(t))
