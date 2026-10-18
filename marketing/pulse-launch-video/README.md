# Pulse — launch video (VSL)

`Pulse-launch-video.mp4` — 1:30, 1920×1080, 30 fps, H.264 + AAC, loudness −15 LUFS.

Real app footage (sample data, dark mode, Hormozi mode off) recorded frame by frame, inside an animated composition, with an English voiceover, a synthesized music bed and UI sound effects.

## Voiceover script

**hook** — What did your last customer actually cost you? If you had to stop and think, this video is for you.

**problem** — Most small business owners run on gut feel. The numbers are scattered across spreadsheets, notes, and memory. So you never see where your funnel is leaking, or whether your marketing is actually paying for itself.

**reveal** — Meet Pulse. The simplest way to track the numbers that grow your business.

**log** — Logging takes seconds. A new lead? Tap plus. A reply, a meeting, a sale? Tap, tap, tap. Every step of your funnel, counted as it happens.

**metrics** — Then Pulse does the math. Conversion rates. Customer acquisition cost. Return on ad spend. Profit margins. Lifetime value. Every metric, calculated for you, with the formula right there.

**overview** — Your overview shows the week, month, quarter, or year at a glance. Trends, your funnel, and plain English highlights that point straight at your biggest drop-off.

**honest** — And it's honest. Halfway through the month, it compares you with the same days of last month, so a slow start never looks like a slump.

**goals** — Set a goal on any number, and Pulse tells you if you're on pace, while there's still time to act.

**sync** — It works offline, syncs your phone and laptop with a one-time pairing code, and there's no account to create.

**cta** — Stop guessing. Start knowing. Open Pulse today, it's free. Add it to your home screen, and log your first day in under a minute.

## Rebuilding

Everything is offline and deterministic. Tools: Node + Playwright (Chromium), Python with `kokoro-onnx soundfile scipy numpy pillow qrcode imageio-ffmpeg`, the Kokoro model files (`kokoro-v1.0.onnx`, `voices-v1.0.bin` from the kokoro-onnx GitHub releases) and the Inter font installed as the default sans-serif.

1. Serve the app: `python -m http.server 8765 --directory business-tracker`
2. `python source/tts.py <work>` — voiceover per scene (voice `af_heart`) into `<work>/vo/` (expects `<work>/script.json` and `<work>/tts/`)
3. `node source/record.js <work>` — records the app clips into `<work>/clips/`. `shim.js` puts the page on a virtual clock (requestAnimationFrame, timers, performance.now, Web Animations), so the app's spring animations are captured frame-exact. `node source/desk.js <work>` takes the laptop screenshot.
4. Copy `source/comp/` to `<work>/comp/`, link `<work>/clips` into it and serve it on port 8766; `node source/render.js <work> <ffmpeg>` renders the composition (`frame(t)` in `comp/index.html`)
5. `python source/audio.py <work>` → `mix.wav`; mux with ffmpeg (`loudnorm=I=-15:TP=-1.5`, 48 kHz AAC)

Scene timings in `comp/index.html` and `audio.py` follow the voiceover offsets listed in `audio.py` (`OFF`).
