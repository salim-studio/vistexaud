"""Unified Vis+Tex+Aud pipeline example (multimodal)."""
from vistexaud.core.graph import Graph
from vistexaud.text.text_tasks import LanguageDetector, TextClassifier, Summarizer, TextEmbedder
from vistexaud.audio.audio_tasks import VoiceActivityDetector, AudioClassifier
from vistexaud.core.types import TextDoc, AudioChunk
import numpy as np

# text branch
tg = Graph([LanguageDetector(), TextClassifier(), Summarizer()])
print(tg.run_parallel(TextDoc("Today's football match. AI software analyzes the performance. Markets rally on tech earnings.")))

# audio branch (synthetic 440Hz tone)
sr = 16000
tone = (0.3*np.sin(2*np.pi*440*np.linspace(0,1,sr,endpoint=False))).astype(np.float32)
ag = Graph([VoiceActivityDetector(), AudioClassifier()])
print(ag.run_parallel(AudioChunk(tone, sr)))
print(tg.report()); print(ag.report())
