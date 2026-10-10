"""Calculator: base processing node of the vistexaud pipeline."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict
from vistexaud.core.packet import Packet

class Calculator(ABC):
    name: str = "calculator"

    def open(self, options: Dict[str, Any] | None = None) -> None:
        self.options = options or {}

    @abstractmethod
    def process(self, packet: Packet) -> Packet | list[Packet] | None:
        ...

    def close(self) -> None:
        pass

    def __call__(self, packet: Packet):
        return self.process(packet)
