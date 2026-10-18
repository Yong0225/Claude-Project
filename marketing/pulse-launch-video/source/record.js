// Records real Pulse app footage frame by frame under a virtual clock.
// Usage: node record.js <scratch> [clipName...]
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs = require('fs');
const S = process.argv[2];
const only = process.argv.slice(3);
const FPS = 30, DT = 1000 / FPS;
const ease = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;

const todayISO = () => { const d = new Date(); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); };

// each clip: tab to start on, optional data tweak, duration, and timed actions
const CLIPS = {
  log: {
    tab: 'log', dur: 9.6, clearToday: true,
    acts: [
      { at: 2.45, tap: 'step:leads' },
      { at: 3.7, tap: 'step:replied' }, { at: 4.2, tap: 'step:meeting' }, { at: 4.75, tap: 'step:won' },
      { at: 5.5, tap: 'step:leads' }, { at: 5.9, tap: 'step:contacted' }, { at: 6.3, tap: 'step:opened' },
      { at: 7.3, tap: 'step:leads' }, { at: 7.7, tap: 'step:contacted' },
    ],
  },
  metrics: {
    tab: 'metrics', dur: 12.8,
    acts: [
      { at: 1.4, scroll: 1500, dur: 7.0 },
      { at: 8.6, scroll: 'row:CAC', dur: 0.9 },
      { at: 9.7, tap: 'row:CAC' },
    ],
  },
  overview: {
    tab: 'overview', dur: 9.6,
    acts: [
      { at: 1.55, tap: 'seg:Week' }, { at: 2.15, tap: 'seg:Month' }, { at: 2.6, tap: 'seg:Quarter' }, { at: 3.1, tap: 'seg:Year' },
      { at: 3.9, tap: 'seg:Month' },
      { at: 4.1, scroll: 'h:Trend', dur: 0.8 },
      { at: 5.0, scroll: 'h:Funnel', dur: 0.8 },
      { at: 5.9, scroll: 'h:Highlights', dur: 1.0 },
    ],
  },
  goals: {
    tab: 'overview', dur: 5.4,
    acts: [{ at: 0.4, tap: 'tab:goals' }],
  },
};

async function target(p, spec) {
  const [kind, arg] = spec.split(':');
  let loc;
  if (kind === 'step') loc = p.locator(`button.step[data-step="${arg}"][data-d="1"]`);
  else if (kind === 'seg') loc = p.locator('main .seg button, .seg button', { hasText: new RegExp('^' + arg + '$') }).first();
  else if (kind === 'row') loc = p.locator(`[data-open^="metric:"] .t1`, { hasText: new RegExp('^' + arg + '$') }).first();
  else if (kind === 'h') loc = p.locator('h2, .h2, b, .card > .srow b, .card b', { hasText: new RegExp('^' + arg + '$') }).first();
  else if (kind === 'tab') loc = p.locator(`.tabbar button[data-tab="${arg}"], nav.tabbar [data-tab="${arg}"]`).first();
  else if (kind === 'prev') loc = p.locator('[data-pn="-1"]').first();
  else if (kind === 'next') loc = p.locator('[data-pn="1"]').first();
  return loc;
}

(async () => {
  const b = await chromium.launch();
  for (const [name, clip] of Object.entries(CLIPS)) {
    if (only.length && !only.includes(name)) continue;
    const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: 'en-US', colorScheme: 'dark' });
    await ctx.addInitScript({ path: S + '/shim.js' });
    const p = await ctx.newPage();
    p.on('pageerror', e => console.log('PAGEERR', e.message));
    await p.goto('http://localhost:8765/');
    await p.evaluate(() => __advance(600));
    await p.click('[data-act="sample"]'); await p.evaluate(() => __advance(800));
    await p.evaluate(([clear, td]) => {
      const d = JSON.parse(localStorage.getItem('pulse.v1'));
      d.settings.hz = false; d.settings.theme = 'dark';
      if (clear) d.entries = d.entries.filter(e => e.date !== td);
      localStorage.setItem('pulse.v1', JSON.stringify(d));
    }, [!!clip.clearToday, todayISO()]);
    await p.reload(); await p.evaluate(() => __advance(400));
    if (clip.tab !== 'overview') await p.evaluate(t => document.querySelector(`button[data-tab="${t}"]`).click(), clip.tab);
    await p.evaluate(() => { scrollTo(0, 0); __advance(2500); });
    // the log tab shows the stage ids; check the ones we tap exist
    const dir = `${S}/clips/${name}`; fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true });
    const meta = { fps: FPS, frames: 0, taps: [] };
    const acts = clip.acts.map(a => ({ ...a, done: false }));
    let tween = null;
    const N = Math.round(clip.dur * FPS);
    for (let f = 0; f < N; f++) {
      const t = f / FPS;
      for (const a of acts) {
        if (a.done || a.at > t + 1e-6) continue;
        a.done = true;
        if (a.tap) {
          const loc = await target(p, a.tap);
          if (!(await loc.count())) { console.log('MISSING', name, a.tap); continue; }
          const bb = await loc.boundingBox();
          meta.taps.push({ t, x: bb.x + bb.width / 2, y: bb.y + bb.height / 2 });
          await loc.evaluate(el => (el.closest('button,[role="button"],[data-open]') || el).click());
        } else if (a.scroll !== undefined) {
          let to = a.scroll;
          if (typeof to === 'string') {
            const loc = await target(p, to);
            if (!(await loc.count())) { console.log('MISSING', name, to); continue; }
            to = await loc.evaluate(el => el.getBoundingClientRect().top + scrollY - 110);
          }
          const from = await p.evaluate(() => scrollY);
          tween = { t0: t, dur: a.dur, from, to };
        }
      }
      if (tween) {
        const k = Math.min(1, (t - tween.t0) / tween.dur);
        await p.evaluate(y => scrollTo(0, y), tween.from + (tween.to - tween.from) * ease(k));
        if (k >= 1) tween = null;
      }
      await p.screenshot({ path: `${dir}/${String(f).padStart(4, '0')}.jpg`, type: 'jpeg', quality: 90 });
      await p.evaluate(dt => __advance(dt), DT);
    }
    meta.frames = N;
    fs.writeFileSync(`${dir}/meta.json`, JSON.stringify(meta));
    console.log(name, N, 'frames', meta.taps.length, 'taps');
    await ctx.close();
  }
  await b.close();
})();
