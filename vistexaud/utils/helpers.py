"""Perf + drawing + IO helpers for speed."""
from __future__ import annotations
import time
from collections import deque

class FPSMeter:
    def __init__(self, window: int = 30):
        self.t = deque(maxlen=window)
    def tick(self) -> float:
        self.t.append(time.perf_counter())
        if len(self.t) < 2: return 0.0
        return (len(self.t)-1) / max(1e-9, self.t[-1]-self.t[0])
    def reset(self): self.t.clear()

def draw_detections(img, detections):
    try:
        import cv2
    except ImportError:
        return img
    for d in detections or []:
        x, y, w, h = [int(v) for v in d.box]
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(img, f"{d.label} {d.score:.2f}", (x, y-6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1)
        if d.landmarks:
            for p in d.landmarks[:33]:
                try:
                    if len(p) == 2: cx, cy = int(p[0]), int(p[1])
                    else: cx, cy = int(p[0]*img.shape[1]), int(p[1]*img.shape[0])
                    cv2.circle(img, (cx, cy), 2, (255, 0, 0), -1)
                except Exception: pass
    return img

class Camera:
    def __init__(self, source=0, width=640, height=480):
        import cv2
        self.cap = cv2.VideoCapture(source)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    def read(self):
        import cv2
        ok, f = self.cap.read()
        return f if ok else None
    def release(self):
        self.cap.release()
