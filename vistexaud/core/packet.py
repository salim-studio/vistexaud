"""Packet: lightweight timestamped envelope for streaming data."""
from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Any

@dataclass(slots=True)
class Packet:
    payload: Any
    timestamp_us: int = 0
    stream: str = "input"

    def __post_init__(self):
        if not self.timestamp_us:
            self.timestamp_us = int(time.time() * 1e6)

    def get(self): return self.payload
    def empty(self): return self.payload is None
