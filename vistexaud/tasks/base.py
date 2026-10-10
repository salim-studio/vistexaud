"""BaseTask: unified task API (process(image|text|audio))."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from vistexaud.core.calculator import Calculator
from vistexaud.core.packet import Packet

@dataclass
class TaskResult:
    task: str
    output: Any
    latency_ms: float = 0.0
    meta: dict = field(default_factory=dict)

def unwrap(payload: Any) -> Any:
    """If a previous TaskResult flows into the next node, recover original input."""
    if isinstance(payload, TaskResult):
        inp = payload.meta.get("_input", None)
        return inp if inp is not None else None
    return payload

class BaseTask(Calculator):
    task_name: str = "base"
    @property
    def name(self): return self.task_name
    @name.setter
    def name(self, v): self.task_name = v
