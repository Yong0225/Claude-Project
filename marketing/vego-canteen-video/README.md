# VEGO CANTEEN 蔬食堂: website vs. no website (visitor POV)

`vego-website-vs-no-website.mp4`: 1:04, vertical 1080×1920, 60 fps, H.264 + AAC, loudness −14 LUFS. All on-screen text is in Chinese. There is no voiceover; the video uses a synthesized score and sound design.

It is a pitch video for the VEGO CANTEEN owner. It follows one hungry customer on a Friday at 7:12pm, twice: once with only Google Maps + Facebook, and once with the website.

## Story

| Time | Scene |
|---|---|
| 0–6s | 星期五晚上，肚子饿了。 Then a split title: 没有网站 / 有网站, 同一家餐厅 · 同一位客人 |
| 6–29s | **A · 没有网站.** Maps search, 4.9 rating (470 reviews). Four questions float around the phone: 有什么菜？今天有开吗？哪里停车？可以订位吗？ The customer flips through photos but finds no menu. Maps pushes the app download. Facebook shows a login wall. A Messenger message goes unanswered: 晚餐时间，老板在厨房忙 (fast-forward 7:16 → 7:31). The questions turn red ✕, and the customer thinks 算了，去别家吧。 |
| 29–32s | Rewind (clock runs back to 7:12), then an iris opens into the warm palette |
| 32–51s | **B · 有网站.** Google result for vegocanteen.my, the site's own loader, then the hero (素食，也可以吃得好过瘾。), 十大必点, hours with "营业中", open-air parking + Google 导航 / Waze, 订位, then WhatsApp with the site's prefilled 「你好，蔬食堂！我想订位。」. Each question turns into a green ✓. Done by 7:14. |
| 51–57s | Side by side: 19 分钟 (放弃，去了别家) vs 2 分钟 (今晚 8 点，4 位) |
| 57–64s | 客人不会等。好食物，值得被一眼看见。 Then the end card: VEGO CANTEEN 蔬食堂 · vegocanteen.my · 情境模拟 · 画面为示意 |

## Sources and what is illustrative

- Rating, review count, price range, category and the "open in the app" prompt come from the live Google Maps listing (Sept 2026). The mobile Facebook login wall is real: the page shows nothing without logging in.
- Website copy, dish names, hours, parking note and the WhatsApp prefill text come from the client's `index.html`.
- Photos: the 6 images in `source/comp/img/` are customer photos from the Google Maps listing. They are used because the site's own `assets/img/*` files were not available. The site's `logo.png` was not available either, so the round 「蔬」 emblem is a stand-in.
- The Facebook page, the Messenger chat, the website and the WhatsApp screens are recreated in HTML, not screen-recorded. The timings (19 vs 2 minutes) are a scenario, and the end card labels them 情境模拟.

To swap in the real site assets, replace `hero` / `.feat .img` backgrounds and the `.emb` emblem in `source/comp/index.html`, then re-render.

## Rebuilding

Tools: Node + Playwright (Chromium), ffmpeg, Python with `numpy scipy soundfile pillow`.

1. Fonts (not committed, ~50 MB): download from `github.com/google/fonts` (`ofl/`) into `source/comp/fonts/`: `NotoSerifSC.ttf`, `NotoSansSC.ttf`, `Manrope.ttf` (variable fonts, rename them without `[wght]`), `YoungSerif-Regular.ttf`, `MaShanZheng-Regular.ttf`.
2. Preview single frames: `node source/preview.js 12.5 40` (writes `prev/f*.png`; run from `source/`, needs a `prev/` folder). `comp/index.html?t=12.5` also shows one frame in a browser.
3. Render: from `source/`, run `node render.js 60 <i> 4 out` for i = 0..3 (4 parallel workers). Each worker writes `out/seg<i>.mp4`. `FFMPEG=/path/to/ffmpeg` overrides the binary.
4. Audio: dump the sound-effect cue list with `JSON.stringify(SFX())` from the page into `out/sfx.json`, then run `python audio.py out/sfx.json out/mix.wav`. Music and sound-effect timings follow `T` in `comp/index.html` (mirrored at the top of `audio.py`).
5. Concat the segments, then mux: `-c:v libx264 -crf 19 -preset slow -af loudnorm=I=-14:TP=-1.5 -c:a aac -b:a 192k -movflags +faststart`.

Everything is deterministic: `frame(t)` in `comp/index.html` is a pure function of time.
