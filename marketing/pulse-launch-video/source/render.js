const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const { spawn } = require('child_process');
const S = process.argv[2], FPS = 30, DUR = 90, FF = process.argv[3];
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  p.on('pageerror', e => console.log('PAGEERR', e.message));
  await p.goto('http://localhost:8766/'); await p.evaluate(() => window.ready);
  const ff = spawn(FF, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-tune', 'animation', `${S}/video_noaudio.mp4`], { stdio: ['pipe', 'inherit', 'inherit'] });
  const N = FPS * DUR, t0 = Date.now();
  for (let f = 0; f < N; f++) {
    await p.evaluate(t => frame(t), f / FPS);
    const buf = await p.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % 300 === 0) console.log(f, ((Date.now() - t0) / 1000).toFixed(0) + 's');
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  await b.close(); console.log('done', ((Date.now() - t0) / 1000).toFixed(0) + 's');
})();
