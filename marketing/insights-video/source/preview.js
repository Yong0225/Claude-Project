// Screenshots frame(t) at the given times: node preview.js <outdir> t1 t2 ...
const { chromium } = require('playwright'); const path = require('path');
(async () => {
  const [out, ...ts] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', e => console.log('PAGEERR', e.message)); p.on('console', m => m.type() === 'error' && console.log('ERR', m.text()));
  await p.goto('file://' + path.join(__dirname, 'comp/index.html')); await p.evaluate(() => window.ready);
  for (const t of ts) { await p.evaluate(t => frame(t), +t); await p.screenshot({ path: `${out}/f_${t}.png`, scale: 'css' }); }
  await b.close();
})();
