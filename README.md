<p align="center">
  <img src="docs/assets/logo.svg" width="160" alt="vistexaud logo"/>
</p>

<h1 align="center">vistexaud</h1>

<p align="center"><strong>VISion + TEXt + AUDio — one fast pipeline for live media.</strong></p>

<p align="center">
  <img src="https://img.shields.io/badge/python-%3E%3D3.9-3776AB?logo=python&logoColor=white" alt="python"/>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="license"/>
  <img src="https://img.shields.io/badge/text-12k_docs%2Fs-06B6D4" alt="text speed"/>
  <img src="https://img.shields.io/badge/vision-realtime-7C3AED" alt="vision"/>
  <img src="https://img.shields.io/badge/audio-realtime-F59E0B" alt="audio"/>
</p>

Pure-Python streaming framework for **images, text, and sound**. Install in seconds, run offline, and chain tasks into live pipelines with per-node timing built in.

## Why vistexaud

- **Zero model downloads required** — OpenCV + NumPy heuristics run on first launch (~0.08 ms/doc for text, single-digit ms for vision).
- **Optional ONNX upgrade** — plug a YuNet/YOLO ONNX file for higher accuracy when you need it.
- **Live-first streaming** — `Pipeline` uses a worker thread with backpressure (drops the oldest frame instead of lagging).
- **Observable by default** — `graph.report()` shows calls and average ms per node.
- **One API for three modalities** — every task is a `BaseTask` with `process(packet) -> packet`.

## Install

```bash
pip install opencv-python numpy
# optional accuracy boost:
pip install onnxruntime
# from source:
git clone https://github.com/salim-studio/vistexaud.git
cd vistexaud
pip install -e .
```

## Quickstart

```python
from vistexaud.core.graph import Graph
from vistexaud.core.types import TextDoc, AudioChunk
from vistexaud.text.text_tasks import LanguageDetector, TextClassifier, Summarizer
from vistexaud.audio.audio_tasks import VoiceActivityDetector, AudioClassifier

text = Graph([LanguageDetector(), TextClassifier(), Summarizer()])
print(text.run_parallel(TextDoc("A football match analyzed by AI software")))

import numpy as np
sr = 16000
tone = (0.3 * np.sin(2 * np.pi * 220 * np.linspace(0, 1, sr, endpoint=False))).astype(np.float32)
audio = Graph([VoiceActivityDetector(), AudioClassifier()])
print(audio.run_parallel(AudioChunk(tone, sr)))
```

```python
import cv2
from vistexaud.core.graph import Graph
from vistexaud.vision.detectors import FaceDetector, MotionDetector
from vistexaud.utils.helpers import draw_detections

g = Graph([FaceDetector(), MotionDetector()])
cap = cv2.VideoCapture(0)
while True:
    ok, frame = cap.read()
    if not ok:
        break
    for result in g.run_parallel(frame).values():
        frame = draw_detections(frame, result.output)
    cv2.imshow("vistexaud", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
print(g.report())
```

## CLI

```bash
python -m vistexaud.cli vision --source 0        # live camera: faces
python -m vistexaud.cli vision --source 0 --all  # live camera: faces + motion
python -m vistexaud.cli text --text "A football match analyzed by AI"
python -m vistexaud.cli audio                    # synthetic-tone audio demo
python -m vistexaud.cli bench                    # speed benchmark
```

## Architecture

```
vistexaud/
  core/    Packet | Calculator | Graph / Pipeline | ImageFrame / AudioChunk / TextDoc
  vision/  FaceDetector | HandTracker | PoseEstimator | MotionDetector
  text/    LanguageDetector | TextClassifier | TextEmbedder | Summarizer
  audio/   VoiceActivityDetector | AudioClassifier | PitchEstimator
  utils/   FPSMeter | draw_detections | Camera
```

- **Sequential**: `graph.process_one(payload)` chains A → B → C.
- **Parallel branches**: `graph.run_parallel(payload)` runs every node on the same input.
- **Streaming**: `Pipeline(nodes, on_result=...)` adds a threaded queue with backpressure.

## Tasks

| Modality | Task                  | Method (default)              | Needs download |
|----------|-----------------------|-------------------------------|----------------|
| Vision   | FaceDetector          | Haar cascade / YuNet (ONNX)   | No / optional  |
| Vision   | HandTracker           | Skin-color + contours         | No             |
| Vision   | PoseEstimator         | HOG person + skeleton         | No             |
| Vision   | MotionDetector        | Background subtraction (MOG2) | No             |
| Text     | LanguageDetector      | Script statistics             | No             |
| Text     | TextClassifier        | Keyword scoring               | No             |
| Text     | TextEmbedder          | Hashing vector, L2-normalized | No             |
| Text     | Summarizer            | Frequency-ranked extractive   | No             |
| Audio    | VoiceActivityDetector | Short-time energy             | No             |
| Audio    | AudioClassifier       | Spectral heuristic            | No             |
| Audio    | PitchEstimator        | Autocorrelation               | No             |

## Custom task (one minute)

```python
from vistexaud.tasks.base import BaseTask, TaskResult
from vistexaud.core.packet import Packet

class MyFilter(BaseTask):
    task_name = "my_filter"

    def process(self, packet: Packet):
        return Packet(TaskResult("my_filter", packet.payload[::-1]), stream="out")
```

## Benchmarks (reference machine)

- Text branch (3 tasks): ~9,000–12,000 docs/s, ~0.1 ms/doc.
- Vision (VGA frame): face check <1 ms, motion ~6 ms, hand ~2 ms.
- Run your own: `python -m vistexaud.cli bench`, then `graph.report()`.

## Brand

Identity, palette, and logo usage live in [`docs/BRANDING.md`](docs/BRANDING.md). Mark: `docs/assets/logo.svg`.

---

Copyright (c) 2026 salim-slimani. MIT License — see [LICENSE](LICENSE).
