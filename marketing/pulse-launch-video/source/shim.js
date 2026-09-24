// virtual clock: rAF, timers, performance.now and Web Animations advance only via __advance(ms)
(() => {
  let vnow = 0; const perfNow = performance.now.bind(performance); const base = perfNow();
  let rafQ = [], rafId = 0, timers = new Map(), tId = 0;
  performance.now = () => base + vnow;
  window.requestAnimationFrame = cb => { const id = ++rafId; rafQ.push([id, cb]); return id; };
  window.cancelAnimationFrame = id => { rafQ = rafQ.filter(r => r[0] !== id); };
  window.setTimeout = (cb, ms = 0, ...a) => { const id = ++tId; timers.set(id, { at: vnow + Math.max(0, +ms || 0), cb, a }); return id; };
  window.setInterval = (cb, ms = 0, ...a) => { const id = ++tId; timers.set(id, { at: vnow + Math.max(1, +ms || 0), cb, a, every: Math.max(1, +ms || 0) }); return id; };
  window.clearTimeout = window.clearInterval = id => timers.delete(id);
  const runTimers = () => {
    for (let guard = 0; guard < 1000; guard++) {
      let best = null;
      for (const [id, t] of timers) if (t.at <= vnow && (!best || t.at < best[1].at)) best = [id, t];
      if (!best) return;
      const [id, t] = best;
      if (t.every) t.at += t.every; else timers.delete(id);
      try { typeof t.cb === 'function' ? t.cb(...t.a) : eval(t.cb); } catch (e) { console.error(e); }
    }
  };
  const seen = new WeakSet();
  window.__advance = (ms) => {
    const steps = Math.max(1, Math.round(ms / 16.667)), dt = ms / steps;
    for (let i = 0; i < steps; i++) {
      vnow += dt; runTimers();
      const q = rafQ; rafQ = []; const ts = base + vnow;
      for (const [, cb] of q) { try { cb(ts); } catch (e) { console.error(e); } }
      for (const a of document.getAnimations()) {
        if (!seen.has(a)) { seen.add(a); a.pause(); a.__t = 0; }
        a.__t += dt; try { a.currentTime = a.__t; } catch (e) {}
      }
    }
  };
})();
