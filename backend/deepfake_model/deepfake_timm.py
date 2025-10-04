# Load pretrained deepfake classifier

import torch, timm
import os
from torch import nn

class DeepfakeModel(nn.Module):
    def __init__(self, arch, num_classes=2, ckpt_path=None):
        super().__init__()
        self.net = timm.create_model(arch, pretrained=False, num_classes=num_classes, in_chans=3)
        if ckpt_path and os.path.isfile(ckpt_path):
            state = torch.load(ckpt_path, map_location='cpu')
            raw = state['state_dict'] if isinstance(state, dict) and 'state_dict' in state else state

            # common prefix cleaners
            def _clean(k):
                return k.replace('module.', '').replace('net.', '').replace('model.', '')
            raw = { _clean(k): v for k, v in raw.items() }

            missing, unexpected = self.load_state_dict(raw, strict=False)
            print(f"[CKPT] loaded from {ckpt_path}")
            print(f"[CKPT] missing: {len(missing)} keys, unexpected: {len(unexpected)} keys")

            # check head stats
            head = self.net.get_classifier() if hasattr(self.net, 'get_classifier') else getattr(self.net, 'classifier', None)
            if hasattr(head, 'weight'):
                wmean = head.weight.detach().abs().mean().item()
                print(f"[CKPT] classifier |w| mean = {wmean:.6f}")

            key = 'state_dict' if 'state_dict' in state else None
            self.load_state_dict(state[key] if key else state, strict=False)
        self.register_buffer('temperature', torch.tensor(1.0))

    def forward(self, x):
        logits = self.net(x)  # [B,2] => assume index 1 = "fake"
        return logits

    def set_temperature(self, t):
        self.temperature = torch.tensor(float(t))

    @torch.no_grad()
    def predict_proba(self, x):
        logits = self.forward(x) / self.temperature
        return torch.softmax(logits, dim=1)
