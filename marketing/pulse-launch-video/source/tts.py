import json, sys, soundfile as sf, numpy as np
from kokoro_onnx import Kokoro
S = sys.argv[1]
k = Kokoro(f"{S}/tts/kokoro-v1.0.onnx", f"{S}/tts/voices-v1.0.bin")
out = {}
for key, text in json.load(open(f"{S}/script.json")):
    a, sr = k.create(text, voice="af_heart", speed=1.0, lang="en-us")
    # trim leading/trailing silence
    idx = np.where(np.abs(a) > 0.01)[0]; a = a[max(0, idx[0]-int(.03*sr)): idx[-1]+int(.12*sr)]
    sf.write(f"{S}/vo/{key}.wav", a, sr); out[key] = round(len(a)/sr, 3)
    print(key, out[key], flush=True)
json.dump(out, open(f"{S}/vo/durations.json", "w"), indent=1)
