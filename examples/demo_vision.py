"""Vision example: image file or camera."""
import sys
from vistexaud.core.graph import Graph
from vistexaud.vision.detectors import FaceDetector, MotionDetector

def main(path=None):
    import cv2
    g = Graph([FaceDetector()])
    if path:
        img = cv2.imread(path)
        assert img is not None, f"cannot read {path}"
        print(g.process_one(img))
    else:
        cap = cv2.VideoCapture(0)
        from vistexaud.utils.helpers import draw_detections
        while True:
            ok, f = cap.read()
            if not ok: break
            r = g.process_one(f)
            f = draw_detections(f, r.output if r else [])
            cv2.imshow("vistexaud", f)
            if cv2.waitKey(1) & 0xFF == ord("q"): break
        cap.release(); cv2.destroyAllWindows()
    print(g.report())

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
