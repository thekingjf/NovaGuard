# deepfake_xception_pm.py
import torch
import torch.nn as nn
import pretrainedmodels  # Cadene's
from torch import Tensor

class PMXception(nn.Module):
    """
    FaceForensics++-style Xception from 'pretrainedmodels'.
    Expects 299x299, normalize to mean=std=0.5 (i.e., scale to [-1,1]).
    """
    def __init__(self, num_classes=2):
        super().__init__()
        self.base = pretrainedmodels.__dict__['xception'](pretrained=None)  # no ImageNet init
        # Replace classifier to 2-way head (FF++ uses this)
        in_ch = self.base.last_linear.in_features
        self.base.last_linear = nn.Linear(in_ch, num_classes)

        self.register_buffer('temperature', torch.tensor(1.0))

    def forward(self, x: Tensor) -> Tensor:
        return self.base(x)  # [B,2]

    def set_temperature(self, t: float):
        self.temperature = torch.tensor(float(t))
