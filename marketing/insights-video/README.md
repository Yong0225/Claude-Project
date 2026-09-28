# F&B insights — explainer video (findings 07–08)

Vertical 1080×1920, 30 fps, H.264 + AAC, loudness −14 LUFS. English voiceover, burned-in captions, synthesized music and sound effects. Made for IG / WhatsApp follow-ups to restaurant owners without a website.

- `insights-video.mp4` — 1:05, neutral research framing, no branding
- `insights-video-logo.mp4` — 1:08.5, same video plus a Y-STUDIO logo end card

## Data (verified at the source, not the originally supplied figures)

| Finding | On screen | Source |
|---|---|---|
| 01 Decision speed | 77% of diners check a restaurant's website before they go | MGH survey of 1,101 US diners, Aug 2019 (restaurantdive.com) |
| 02 First impressions | 75% judge a business's credibility by its website design | Stanford Web Credibility Project (B.J. Fogg) — all industries, not restaurant-specific |

The originally supplied "87% decide within 30 seconds (TripAdvisor × Ipsos)" and "12–15% higher perceived price (Cornell)" could not be found; the Cornell link points to an unrelated study on hotel downsizing. Do not use them.

## Voiceover script

**hook** — Five stars on Google. Thousands of followers on Instagram. So why are hungry customers still picking the place next door?

**stat1** — Here's what the research says. Seventy-seven percent of diners check a restaurant's website before they go.

**need** — They're hungry, and they decide fast. They want four things. The menu. The prices. Your hours. And a way to book.

**without** — Without a website, that means digging through Instagram highlights, guessing the prices, and waiting on a DM. Every extra step is a reason to leave.

**with** — With a website, it's one page. One tap. Table booked.

**stat2** — And there's a second cost. Stanford researchers found that seventy-five percent of people judge a business's credibility by its website design.

**judge** — So before anyone tastes your food, they've already judged it. A blurry menu photo says: is it worth it? A clean, simple site says: worth the price.

**end** — Your food is premium. Make the first impression match.

## Rebuilding

Tools: Node + Playwright (Chromium), Python with `kokoro-onnx soundfile scipy numpy imageio-ffmpeg`, and the Kokoro model files (`kokoro-v1.0.onnx`, `voices-v1.0.bin` from the kokoro-onnx GitHub releases, `model-files-v1.0`).

```
cd marketing/insights-video/source
./build.sh <workdir> <dir with the kokoro model files>
```

- `script.json` — the voiceover, split into phrases. `tts.py` synthesizes each phrase separately (voice `af_heart`) and writes `vo/cues.json` with each phrase's start, so on-screen text lands on the exact word.
- `comp/index.html` — the whole animation as a pure function `frame(t)`; `render.js` steps it frame by frame and pipes JPEGs to ffmpeg. `?logo=1` adds the logo end card. `preview.js <outdir> t1 t2 …` screenshots single moments.
- `audio.py` — music (tension → drop at "reason to leave" → major lift for "with a website" → groove → resolve), SFX on every cue, voice ducking.
- Scene offsets (`OFF`) must match in `comp/index.html` and `audio.py`. Fonts come from `../insights-no-website/fonts.css`.
