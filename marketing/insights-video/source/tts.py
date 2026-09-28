"""Voiceover: one wav per scene, synthesized phrase by phrase so on-screen text can cue to each phrase.
usage: python tts.py <work> <dir with kokoro-v1.0.onnx + voices-v1.0.bin>
writes <work>/vo/<scene>.wav and <work>/vo/cues.json {scene: {"dur": s, "at": [phrase start offsets]}}"""
import json, sys, soundfile as sf, numpy as np
from kokoro_onnx import Kokoro
S, T = sys.argv[1], sys.argv[2]
k = Kokoro(f"{T}/kokoro-v1.0.onnx", f"{T}/voices-v1.0.bin")
GAP = {',': .12, '.': .28, '?': .32, ':': .2}
cues = {}
for key, phrases in json.load(open(f"{S}/script.json")):
    parts, at, t = [], [], 0.0
    for ph in phrases:
        a, sr = k.create(ph, voice="af_heart", speed=1.0, lang="en-us")
        idx = np.where(np.abs(a) > 0.01)[0]; a = a[max(0, idx[0] - int(.03 * sr)): idx[-1] + int(.1 * sr)]
        at.append(round(t, 3)); parts.append(a); t += len(a) / sr
        g = GAP.get(ph.strip()[-1], .15); parts.append(np.zeros(int(g * sr))); t += g
    a = np.concatenate(parts[:-1]); sf.write(f"{S}/vo/{key}.wav", a, sr)
    cues[key] = {"dur": round(len(a) / sr, 3), "at": at}
    print(key, cues[key], flush=True)
json.dump(cues, open(f"{S}/vo/cues.json", "w"), indent=1)
