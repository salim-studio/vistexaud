"""Audio tasks: numpy-only spectral features, no heavy deps. Mirrors MediaPipe Audio Tasks."""
from __future__ import annotations
import time
import numpy as np
from vistexaud.core.packet import Packet
from vistexaud.tasks.base import BaseTask, TaskResult, unwrap

class VoiceActivityDetector(BaseTask):
    task_name = "vad"
    def open(self, options=None):
        super().open(options); self.thresh = (options or {}).get("energy_thresh", 0.01)
    def process(self, packet: Packet):
        from vistexaud.core.types import AudioChunk
        t0 = time.perf_counter()
        p = unwrap(packet.payload)
        if p is None:
            return packet  # passthrough when chained without original
        s = p.samples if isinstance(p, AudioChunk) else np.asarray(p, dtype=np.float32)
        energy = float(np.mean(s.astype(np.float32) ** 2)) if s.size else 0.0
        speech = energy > self.thresh
        return Packet(TaskResult("vad", {"speech": speech, "energy": energy},
                      (time.perf_counter()-t0)*1000), stream="vad")

class AudioClassifier(BaseTask):
    """Spectral heuristic: speech vs music vs silence vs noise (zero-model, ~0.2ms)."""
    task_name = "audio_classifier"
    def process(self, packet: Packet):
        from vistexaud.core.types import AudioChunk
        t0 = time.perf_counter()
        p = unwrap(packet.payload)
        if p is None:
            return packet  # passthrough when chained without original
        if isinstance(p, AudioChunk):
            s, sr = p.samples.astype(np.float32), p.sample_rate
        else:
            s, sr = np.asarray(p, dtype=np.float32), 16000
        if s.size < 256:
            return Packet(TaskResult("audio_classifier", {"label": "silence", "score": 1.0}, 0.0), stream="audio_class")
        spec = np.abs(np.fft.rfft(s * np.hanning(len(s))))
        freqs = np.fft.rfftfreq(len(s), 1 / sr)
        centroid = float(np.sum(freqs * spec) / (np.sum(spec) + 1e-9))
        zcr = float(np.mean(np.abs(np.diff(np.sign(s))) > 0))
        energy = float(np.mean(s ** 2))
        if energy < 1e-4: label, score = "silence", 0.99
        elif centroid < 1200 and zcr < 0.15: label, score = "speech", 0.8
        elif centroid > 2500 and zcr > 0.2: label, score = "music", 0.7
        else: label, score = "noise", 0.6
        return Packet(TaskResult("audio_classifier",
                      {"label": label, "score": score, "centroid": centroid, "zcr": zcr, "energy": energy},
                      (time.perf_counter()-t0)*1000), stream="audio_class")

class PitchEstimator(BaseTask):
    task_name = "pitch_estimator"
    def process(self, packet: Packet):
        from vistexaud.core.types import AudioChunk
        t0 = time.perf_counter()
        p = unwrap(packet.payload)
        if p is None:
            return packet  # passthrough when chained without original
        if isinstance(p, AudioChunk):
            s, sr = p.samples.astype(np.float32), p.sample_rate
        else:
            s, sr = np.asarray(p, dtype=np.float32), 16000
        s = s - np.mean(s)
        corr = np.correlate(s, s, mode="full")[len(s)-1:]
        corr[: int(sr/500)] = 0  # ignore >500Hz
        peak = int(np.argmax(corr)) if corr.size else 0
        pitch = float(sr / peak) if peak > 0 else 0.0
        return Packet(TaskResult("pitch_estimator", {"pitch_hz": pitch}, (time.perf_counter()-t0)*1000), stream="pitch")
