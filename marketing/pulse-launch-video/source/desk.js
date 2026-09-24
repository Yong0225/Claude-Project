const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const S = process.argv[2];
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport:{width:1440,height:900}, deviceScaleFactor:1, locale:'en-US', colorScheme:'dark' });
  await ctx.addInitScript({ path: S + '/shim.js' });
  const p = await ctx.newPage();
  await p.goto('http://localhost:8765/'); await p.evaluate(() => __advance(600));
  await p.click('[data-act="sample"]'); await p.evaluate(() => __advance(800));
  await p.evaluate(() => { const d = JSON.parse(localStorage.getItem('pulse.v1')); d.settings.hz = false; localStorage.setItem('pulse.v1', JSON.stringify(d)); });
  await p.reload(); await p.evaluate(() => __advance(3000));
  await p.screenshot({ path: S + '/comp/desktop.jpg', type:'jpeg', quality: 90 });
  await b.close();
})();
