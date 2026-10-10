"""Lightweight zero-copy containers."""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any, Optional
import numpy as np


@dataclass(slots=True)
class ImageFrame:
    data: np.ndarray  # BGR uint8 HxWxC
    timestamp_us: int = field(default_factory=lambda: int(time.time() * 1e6))
    source: str = "camera"
    meta: dict = field(default_factory=dict)

    @property
    def width(self): return self.data.shape[1] if self.data.ndim >= 2 else 0
    @property
    def height(self): return self.data.shape[0] if self.data.ndim >= 2 else 0


@dataclass(slots=True)
class AudioChunk:
    samples: np.ndarray  # float32 mono
    sample_rate: int = 16000
    timestamp_us: int = field(default_factory=lambda: int(time.time() * 1e6))
    meta: dict = field(default_factory=dict)


@dataclass(slots=True)
class TextDoc:
    text: str
    lang: str = "unknown"
    timestamp_us: int = field(default_factory=lambda: int(time.time() * 1e6))
    meta: dict = field(default_factory=dict)
