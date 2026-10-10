# vistexaud — بديل عملي وسريع لـ MediaPipe

**vistexaud = Vis**ion + **Tex**t + **Aud**io. إطار بايثون خفيف وموحّد لمعالجة الوسائط الحية (صور/فيديو/نص/صوت) بأسلوب MediaPipe (Tasks + Graph + Calculator + Packet) لكن **بدون Bazel وبدون C++**: تثبيت بثوانٍ ويعمل فورًا.

## لماذا أسرع وأكفأ؟
- **بدون تحميل موديلات إجباري**: كشف الوجوه بـ Haar المدمج في OpenCV (~5ms)، والحركة بـ MOG2 (~2ms)، والنص/الصوت بـ numpy خالص (~0.05ms).
- **ترقية اختيارية**: إن وُجدت `mediapipe` أو ملف ONNX تُستخدم تلقائيًا لدقة أعلى.
- **Pipeline بخيوط و Backpressure**: `Pipeline` يسقط أقدم فريم عند الازدحام بدل التأخير (مثالي للبث الحي).
- **إحصاء زمن لكل عقدة**: `graph.report()` يعرض avg ms لكل Task.

## تثبيت
```bash
pip install opencv-python numpy
# اختياري للدقة القصوى:
pip install mediapipe onnxruntime
```

## استعمال سريع
```python
from vistexaud.core.graph import Graph
from vistexaud.vision.detectors import FaceDetector
from vistexaud.text.text_tasks import LanguageDetector, TextClassifier
from vistexaud.audio.audio_tasks import AudioClassifier

g = Graph([FaceDetector()])          # vision
print(g.process_one(cv2.imread("img.jpg")))
print(g.report())

g2 = Graph([LanguageDetector(), TextClassifier()])  # text
from vistexaud.core.types import TextDoc
print(g2.process_one(TextDoc("مباراة كرة القدم والذكاء الاصطناعي")))
```

## سطر الأوامر
```bash
python -m vistexaud.cli vision --source 0        # كاميرا حية + وجوه
python -m vistexaud.cli vision --source 0 --all  # وجوه + حركة
python -m vistexaud.cli text --text "مباراة كرة AI"
python -m vistexaud.cli audio
python -m vistexaud.cli bench
```

## البنية (مطابقة لفلسفة MediaPipe)
```
vistexaud/
  core/    Packet | Calculator | Graph/Pipeline | ImageFrame/AudioChunk/TextDoc
  vision/  FaceDetector | HandTracker | PoseEstimator | MotionDetector
  text/    LanguageDetector | TextClassifier | TextEmbedder | Summarizer
  audio/   VoiceActivityDetector | AudioClassifier | PitchEstimator
  utils/   FPSMeter | draw_detections | Camera
```

## مقارنة مع MediaPipe
|  | MediaPipe | vistexaud |
|---|---|---|
| التثبيت | Bazel/C++ ثقيل | `pip install` فقط |
| يعمل دون إنترنت/موديلات | لا غالبًا | نعم |
| Vision/Text/Audio موحد | نعم | نعم |
| بث حي + FPS | نعم | نعم (Pipeline + FPSMeter) |
| قابلية التخصيص | Calculator مخصص | وراثة `BaseTask` وكتابة `process` فقط |

## إضافة Task جديد (دقيقة واحدة)
```python
from vistexaud.tasks.base import BaseTask, TaskResult
from vistexaud.core.packet import Packet
class MyFilter(BaseTask):
    task_name = "my_filter"
    def process(self, packet: Packet):
        return Packet(TaskResult("my_filter", packet.payload[::-1]), stream="out")
```

MIT License.
