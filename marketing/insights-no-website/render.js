// Renders slides.html to 1080x1350 PNGs (2x). Run: NODE_PATH=$(npm root -g) node render.js
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 1400 }, deviceScaleFactor: 2 });
  p.on('console', m => m.type() === 'error' && console.log('console error:', m.text()));
  await p.goto('file://' + path.join(__dirname, 'slides.html'), { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  for (const id of ['s1', 's2', 's3']) {
    const el = await p.$('#' + id);

    console.log(id, 'spare px:', await el.evaluate(s => { const cs = getComputedStyle(s); let h = 0; for (const c of s.children) { const m = getComputedStyle(c); h += c.scrollHeight + (c.classList.contains('foot') ? 0 : parseFloat(m.marginTop)) + parseFloat(m.marginBottom); } return Math.round(s.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom) - h); }));
    await el.screenshot({ path: path.join(__dirname, `insight-0${id[1]}.png`) });
  }
  await b.close();
})();
