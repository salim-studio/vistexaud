"""Text tasks: zero-dependency, fast (regex/statistics)."""
from __future__ import annotations
import re, math, time
from collections import Counter
from vistexaud.core.packet import Packet
from vistexaud.tasks.base import BaseTask, TaskResult, unwrap

_AR = re.compile(r'[\u0600-\u06FF]')
_EN = re.compile(r'[A-Za-z]')

class LanguageDetector(BaseTask):
    task_name = "language_detector"
    def process(self, packet: Packet):
        from vistexaud.core.types import TextDoc
        t0 = time.perf_counter()
        p = unwrap(packet.payload)
        if p is None:
            return packet  # passthrough when chained without original
        txt = p.text if isinstance(p, TextDoc) else str(p)
        ar = len(_AR.findall(txt)); en = len(_EN.findall(txt))
        if ar > en and ar > 2: lang = "ar"
        elif en > ar and en > 2: lang = "en"
        elif en == 0 and ar == 0: lang = "unknown"
        else: lang = "mixed"
        return Packet(TaskResult("language_detector", {"lang": lang, "ar": ar, "en": en},
                      (time.perf_counter()-t0)*1000), stream="lang")

class TextClassifier(BaseTask):
    """Tiny keyword classifier (sports/tech/health/...) - trains in ms, runs in µs."""
    task_name = "text_classifier"
    KEYWORDS = {
        "sport": ["كرة", "مباراة", "رياضة", "football", "match", "sport", "goal"],
        "tech": ["ذكاء", "حاسوب", "تقنية", "برنامج", "ai", "software", "computer", "model"],
        "health": ["صحة", "طبيب", "دواء", "health", "doctor", "medical"],
        "economy": ["اقتصاد", "سوق", "مال", "بنك", "economy", "market", "bank", "money"],
    }
    def process(self, packet: Packet):
        from vistexaud.core.types import TextDoc
        t0 = time.perf_counter()
        p = unwrap(packet.payload)
        if p is None:
            return packet  # passthrough when chained without original
        txt = (p.text if isinstance(p, TextDoc) else str(p)).lower()
        scores = {k: sum(1 for w in v if w.lower() in txt) for k, v in self.KEYWORDS.items()}
        label = max(scores, key=scores.get)
        if scores[label] == 0: label = "general"
        return Packet(TaskResult("text_classifier", {"label": label, "scores": scores},
                      (time.perf_counter()-t0)*1000), stream="text_class")

class TextEmbedder(BaseTask):
    """Hashing embedder: fixed-dim float vector, L2-normalized. Fast + no model download."""
    task_name = "text_embedder"
    def open(self, options=None):
        super().open(options); self.dim = (options or {}).get("dim", 128)
    def process(self, packet: Packet):
        from vistexaud.core.types import TextDoc
        import numpy as np
        t0 = time.perf_counter()
        p = unwrap(packet.payload)
        if p is None:
            return packet  # passthrough when chained without original
        txt = p.text if isinstance(p, TextDoc) else str(p)
        toks = re.findall(r'\w+', txt.lower())
        v = np.zeros(self.dim, dtype=np.float32)
        for t in toks:
            v[hash(t) % self.dim] += 1.0
        n = float(np.linalg.norm(v));  v = v / n if n else v
        return Packet(TaskResult("text_embedder", v, (time.perf_counter()-t0)*1000), stream="embed")

class Summarizer(BaseTask):
    """Extractive summarizer: top-N sentences by word frequency."""
    task_name = "summarizer"
    def open(self, options=None):
        super().open(options); self.max_sentences = (options or {}).get("max_sentences", 2)
    def process(self, packet: Packet):
        from vistexaud.core.types import TextDoc
        t0 = time.perf_counter()
        p = unwrap(packet.payload)
        if p is None:
            return packet  # passthrough when chained without original
        txt = p.text if isinstance(p, TextDoc) else str(p)
        sents = [s.strip() for s in re.split(r'[.!؟?\n]+', txt) if s.strip()]
        if not sents:
            return Packet(TaskResult("summarizer", "", 0.0), stream="summary")
        freq = Counter(re.findall(r'\w+', txt.lower()))
        scored = sorted(sents, key=lambda s: sum(freq[w.lower()] for w in re.findall(r'\w+', s)), reverse=True)
        summ = ". ".join(scored[:self.max_sentences])
        return Packet(TaskResult("summarizer", summ, (time.perf_counter()-t0)*1000), stream="summary")
