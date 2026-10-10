"""CLI: vistexaud demo / bench — practical entry point."""
from __future__ import annotations
import argparse, time

def cmd_vision(args):
    import cv2
    from vistexaud.core.graph import Graph
    from vistexaud.vision.detectors import FaceDetector, MotionDetector
    from vistexaud.utils.helpers import draw_detections, FPSMeter
    g = Graph([FaceDetector(), MotionDetector()] if args.all else [FaceDetector()])
    src = args.source
    try: src = int(src)
    except Exception: pass
    cap = cv2.VideoCapture(src)
    fps = FPSMeter()
    print("vistexaud vision — press Q to quit")
    while True:
        ok, frame = cap.read()
        if not ok: break
        res = g.run_parallel(frame)
        for r in res.values():
            if r and hasattr(r, "output") and isinstance(r.output, list):
                frame = draw_detections(frame, r.output)
        f = fps.tick()
        cv2.putText(frame, f"vistexaud {f:.1f} FPS", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.imshow("vistexaud - vision", frame)
        if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")): break
    cap.release(); cv2.destroyAllWindows()
    print(g.report())

def cmd_text(args):
    from vistexaud.core.graph import Graph
    from vistexaud.text.text_tasks import LanguageDetector, TextClassifier, Summarizer
    from vistexaud.core.types import TextDoc
    g = Graph([LanguageDetector(), TextClassifier(), Summarizer()])
    doc = TextDoc(args.text)
    print(g.run_parallel(doc))
    print(g.report())

def cmd_audio(args):
    import numpy as np
    from vistexaud.core.graph import Graph
    from vistexaud.core.types import AudioChunk
    from vistexaud.audio.audio_tasks import VoiceActivityDetector, AudioClassifier, PitchEstimator
    sr = 16000; t = np.linspace(0, 1, sr, endpoint=False)
    tone = (0.3 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)  # synthetic demo
    g = Graph([VoiceActivityDetector(), AudioClassifier(), PitchEstimator()])
    print(g.run_parallel(AudioChunk(tone, sr)))
    print(g.report())

def cmd_bench(_):
    import numpy as np
    from vistexaud.core.graph import Graph
    from vistexaud.text.text_tasks import LanguageDetector, TextClassifier, TextEmbedder
    from vistexaud.core.types import TextDoc
    g = Graph([LanguageDetector(), TextClassifier(), TextEmbedder()])
    t0 = time.perf_counter(); N = 500
    for _ in range(N):
        g.run_parallel(TextDoc("الذكاء الاصطناعي والرياضة مباراة كرة AI software"))
    dt = time.perf_counter() - t0
    print(f"text pipeline: {N/dt:.0f} docs/sec, {dt/N*1000:.3f} ms/doc")
    print(g.report())

def main(argv=None):
    ap = argparse.ArgumentParser(prog="vistexaud", description="vistexaud — fast unified Vision/Text/Audio")
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("vision", help="live camera face/motion demo"); v.add_argument("--source", default="0"); v.add_argument("--all", action="store_true"); v.set_defaults(fn=cmd_vision)
    t = sub.add_parser("text", help="text pipeline demo"); t.add_argument("--text", default="مباراة كرة القدم والذكاء الاصطناعي AI"); t.set_defaults(fn=cmd_text)
    a = sub.add_parser("audio", help="audio pipeline demo (synthetic)"); a.set_defaults(fn=cmd_audio)
    b = sub.add_parser("bench", help="speed benchmark"); b.set_defaults(fn=cmd_bench)
    args = ap.parse_args(argv); args.fn(args)

if __name__ == "__main__":
    main()
