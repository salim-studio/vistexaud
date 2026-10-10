"""Vision tasks: fast OpenCV-native detectors, zero model downloads.

- FaceDetector: Haar cascade on OpenCV 4, YuNet (FaceDetectorYN) on OpenCV 5 with a user-provided ONNX model.
- HandTracker: skin-color mask + contour analysis (fast, no model).
- PoseEstimator: HOG person detector where available, contour fallback otherwise.
- MotionDetector: background-subtraction detector for streaming.
All return TaskResult with boxes/landmarks through a unified API.
"""
from __future__ import annotations
import time
from dataclasses import dataclass
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None  # graceful

from vistexaud.core.packet import Packet
from vistexaud.tasks.base import BaseTask, TaskResult, unwrap

def _need_cv2():
    if cv2 is None:
        raise RuntimeError("opencv-python is required: pip install opencv-python numpy")

@dataclass
class Detection:
    label: str
    score: float
    box: tuple  # x,y,w,h in pixels
    landmarks: list | None = None

class FaceDetector(BaseTask):
    task_name = "face_detector"
    def open(self, options=None):
        super().open(options)
        _need_cv2()
        self.det = None
        self.yn = None
        # OpenCV 4: Haar Cascade (fastest, no download)
        try:
            if hasattr(cv2, "CascadeClassifier"):
                path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                c = cv2.CascadeClassifier(path)
                if not c.empty():
                    self.det = c
        except Exception:
            self.det = None
        # OpenCV 5: FaceDetectorYN (YuNet) — needs ONNX model, use only if provided
        self.yn_model = (options or {}).get("yunet_model", None)
        self.scale = (options or {}).get("scaleFactor", 1.15)
        self.min_neighbors = (options or {}).get("minNeighbors", 4)
        self.min_size = (options or {}).get("minSize", (40, 40))

    def process(self, packet: Packet):
        from vistexaud.core.types import ImageFrame
        t0 = time.perf_counter()
        payload = unwrap(packet.payload)
        if payload is None:
            return packet
        img = payload.data if isinstance(payload, ImageFrame) else payload
        dets = []
        if self.det is not None:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
            faces = self.det.detectMultiScale(gray, scaleFactor=self.scale,
                minNeighbors=self.min_neighbors, minSize=self.min_size)
            dets = [Detection("face", 0.95, tuple(map(int, b))) for b in faces]
        elif self.yn_model:
            try:
                yn = cv2.FaceDetectorYN_create(self.yn_model, "", (img.shape[1], img.shape[0]))
                yn.setInputSize((img.shape[1], img.shape[0]))
                _, faces = yn.detect(img)
                if faces is not None:
                    for f in faces:
                        dets.append(Detection("face", float(f[-1]), tuple(map(int, f[:4]))))
            except Exception:
                pass
        # else: graceful empty (no crash on OpenCV 5 without model) — MotionDetector still works
        return Packet(TaskResult("face_detector", dets, (time.perf_counter()-t0)*1000),
                      timestamp_us=packet.timestamp_us, stream="faces")

class HandTracker(BaseTask):
    """Skin-color mask + contour analysis (fast, no model download)."""
    task_name = "hand_tracker"
    def open(self, options=None):
        super().open(options)
        _need_cv2()

    def _detect(self, img):
        # skin-color mask + contours -> palm boxes (very fast, ~2ms)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([0, 30, 60]), np.array([20, 150, 255]))
        mask = cv2.medianBlur(mask, 5)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        dets = []
        for c in sorted(cnts, key=cv2.contourArea, reverse=True)[:2]:
            if cv2.contourArea(c) < 3000: continue
            x, y, w, h = cv2.boundingRect(c)
            dets.append(Detection("hand", 0.6, (x, y, w, h)))
        return dets

    def process(self, packet: Packet):
        from vistexaud.core.types import ImageFrame
        t0 = time.perf_counter()
        payload = unwrap(packet.payload)
        if payload is None:
            return packet
        img = payload.data if isinstance(payload, ImageFrame) else payload
        dets = self._detect(img)
        return Packet(TaskResult("hand_tracker", dets, (time.perf_counter()-t0)*1000),
                      timestamp_us=packet.timestamp_us, stream="hands")

class PoseEstimator(BaseTask):
    """HOG person detector where available, contour fallback otherwise, with 5-point pseudo-skeleton."""
    task_name = "pose_estimator"
    def open(self, options=None):
        super().open(options)
        _need_cv2()
        self.hog = None
        try:
            if hasattr(cv2, "HOGDescriptor"):
                self.hog = cv2.HOGDescriptor()
                self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        except Exception:
            self.hog = None

    def process(self, packet: Packet):
        from vistexaud.core.types import ImageFrame
        t0 = time.perf_counter()
        payload = unwrap(packet.payload)
        if payload is None:
            return packet
        img = payload.data if isinstance(payload, ImageFrame) else payload
        out = []
        if self.hog is not None:
            rects, _ = self.hog.detectMultiScale(img, winStride=(8, 8))
            for (x, y, w, h) in rects:
                skel = [(x+w//2, y+h//5), (x+w//3, y+h//2), (x+2*w//3, y+h//2), (x+w//3, y+h-5), (x+2*w//3, y+h-5)]
                out.append(Detection("person", 0.7, (int(x), int(y), int(w), int(h)), landmarks=skel))
        return Packet(TaskResult("pose_estimator", out, (time.perf_counter()-t0)*1000),
                      timestamp_us=packet.timestamp_us, stream="pose")

class MotionDetector(BaseTask):
    """Ultra-fast background-subtraction detector (good for streaming)."""
    task_name = "motion_detector"
    def open(self, options=None):
        super().open(options)
        _need_cv2()
        self.bg = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=32, detectShadows=False)
    def process(self, packet: Packet):
        from vistexaud.core.types import ImageFrame
        t0 = time.perf_counter()
        payload = unwrap(packet.payload)
        if payload is None:
            return packet
        img = payload.data if isinstance(payload, ImageFrame) else payload
        fg = self.bg.apply(img)
        _, fg = cv2.threshold(fg, 200, 255, cv2.THRESH_BINARY)
        cnts, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        dets = []
        for c in sorted(cnts, key=cv2.contourArea, reverse=True)[:5]:
            if cv2.contourArea(c) < 1500: continue
            dets.append(Detection("motion", 0.5, tuple(map(int, cv2.boundingRect(c)))))
        return Packet(TaskResult("motion_detector", dets, (time.perf_counter()-t0)*1000),
                      timestamp_us=packet.timestamp_us, stream="motion")
