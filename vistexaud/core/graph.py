"""Graph + Pipeline: fast sequential/threaded DAG execution.

Design goals:
- pure Python, pip install in seconds
- threaded streaming with bounded queues (backpressure) for speed
- per-node timing stats for efficiency analysis
"""
from __future__ import annotations
import time
import queue
import threading
from dataclasses import dataclass, field
from typing import Any, Callable
from vistexaud.core.packet import Packet
from vistexaud.core.calculator import Calculator

@dataclass
class NodeStat:
    calls: int = 0
    total_ms: float = 0.0
    @property
    def avg_ms(self): return self.total_ms / max(1, self.calls)

class Graph:
    """Linear (or branched via list return) pipeline: A -> B -> C."""
    def __init__(self, nodes: list[Calculator] | None = None):
        self.nodes: list[Calculator] = nodes or []
        self.stats: dict[str, NodeStat] = {}
        for n in self.nodes:
            n.open()
            self.stats[n.name] = NodeStat()

    def add(self, calc: Calculator) -> "Graph":
        calc.open()
        self.nodes.append(calc)
        self.stats[calc.name] = NodeStat()
        return self

    def process_one(self, payload: Any, stream: str = "input") -> Any:
        """Sequential chain A -> B -> C. Each TaskResult carries _input=original for traceability."""
        packets: list[Packet] = [Packet(payload, stream=stream)]
        original = payload
        for node in self.nodes:
            out: list[Packet] = []
            st = self.stats[node.name]
            for p in packets:
                t0 = time.perf_counter()
                r = node.process(p)
                st.calls += 1
                st.total_ms += (time.perf_counter() - t0) * 1000
                if r is None:
                    continue
                rs = r if isinstance(r, list) else [r]
                for pkt in rs:
                    try:
                        if hasattr(pkt.payload, "meta") and isinstance(pkt.payload.meta, dict):
                            pkt.payload.meta.setdefault("_input", original)
                    except Exception:
                        pass
                out.extend(rs)
            packets = out
            if not packets:
                return None
        if len(packets) == 1:
            return packets[0].payload
        return [p.payload for p in packets]

    def run_parallel(self, payload: Any, stream: str = "input") -> dict:
        """Run every node independently on the SAME input (parallel branches). Fast + practical."""
        import time as _t
        out = {}
        for node in self.nodes:
            st = self.stats[node.name]
            t0 = _t.perf_counter()
            r = node.process(Packet(payload, stream=stream))
            st.calls += 1
            st.total_ms += (_t.perf_counter() - t0) * 1000
            if r is None:
                continue
            pkt = r[0] if isinstance(r, list) else r
            out[node.name] = pkt.payload
        return out

    def report(self) -> str:
        return "\n".join(f"{k}: {v.calls} calls, avg {v.avg_ms:.2f}ms" for k, v in self.stats.items())

    def close(self):
        for n in self.nodes:
            try: n.close()
            except Exception: pass


class Pipeline(Graph):
    """Streaming pipeline with worker thread + callback (for live camera/mic)."""
    def __init__(self, nodes=None, max_queue: int = 8, on_result: Callable | None = None):
        super().__init__(nodes)
        self.q: queue.Queue = queue.Queue(maxsize=max_queue)
        self.on_result = on_result
        self._stop = threading.Event()
        self._th: threading.Thread | None = None
        self.fps = 0.0

    def _loop(self):
        n = 0; t0 = time.time()
        while not self._stop.is_set():
            try:
                payload = self.q.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                res = self.process_one(payload)
                n += 1
                if self.on_result and res is not None:
                    self.on_result(res)
            except Exception:
                continue
            now = time.time()
            if now - t0 >= 1.0:
                self.fps = n / (now - t0); n = 0; t0 = now

    def start(self):
        self._stop.clear()
        self._th = threading.Thread(target=self._loop, daemon=True)
        self._th.start()
        return self

    def submit(self, payload: Any, drop_if_full: bool = True) -> bool:
        try:
            self.q.put_nowait(payload)
            return True
        except queue.Full:
            if drop_if_full:
                try: self.q.get_nowait()
                except queue.Empty: pass
                try: self.q.put_nowait(payload); return True
                except queue.Full: return False
            return False

    def stop(self):
        self._stop.set()
        if self._th: self._th.join(timeout=1.0)
        self.close()
