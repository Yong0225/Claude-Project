// Renders comp/index.html frame by frame (virtual time via frame(t)) and pipes to ffmpeg.
// usage: node render.js <out.mp4> <ffmpeg> [duration=65] [query e.g. "?logo=1"]
const { chromium } = require('playwright'); const { spawn } = require('child_process'); const path = require('path');
const [OUT, FF, DURS = '65', Q = ''] = process.argv.slice(2), FPS = 30, DUR = +DURS;
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', e => console.log('PAGEERR', e.message));
  await p.goto('file://' + path.join(__dirname, 'comp/index.html') + Q); await p.evaluate(() => window.ready);
  const ff = spawn(FF, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-tune', 'animation', OUT], { stdio: ['pipe', 'inherit', 'inherit'] });
  const N = Math.round(FPS * DUR), t0 = Date.now();
  for (let f = 0; f < N; f++) {
    await p.evaluate(t => frame(t), f / FPS);
    const buf = await p.screenshot({ type: 'jpeg', quality: 94 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % 300 === 0) console.log(f, '/', N, ((Date.now() - t0) / 1000).toFixed(0) + 's');
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  await b.close(); console.log('done', ((Date.now() - t0) / 1000).toFixed(0) + 's');
})();
