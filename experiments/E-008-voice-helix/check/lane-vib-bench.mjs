// Live vibrato after a note (laneVib, the page's own code) in headless Chrome: held notes 1.2-2.2 s over five voices (110-660 Hz),
// straight or vibrato (rate 4.5-7 Hz, half-width 0.15-0.6 st), with or without cycle-to-cycle jitter (rate and width ±30 % per cycle), breath noise.
// Frames: the worker's YIN + ingest, without the take's Viterbi (as live). Read 0.2 s after the note stops.
// Usage: node check/lane-vib-bench.mjs http://localhost:<port>/
import { chromium } from 'playwright';
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()), p = await b.newPage(); await p.goto(process.argv[2]); await p.waitForTimeout(1000);
const rows = await p.evaluate(async () => { const sr = 48000, out = []; let seed = 5; const R = () => (seed = seed * 16807 % 2147483647) / 2147483647;
  for (const m of [45, 52, 60, 69, 76]) for (const kind of ['straight', 'even', 'jitter']) for (let r = 0; r < 8; r++) { const dur = 1.2 + R(), start = 0.3, n = Math.round(sr * (start + dur + 0.6)), buf = mkBuf(n, sr), x = buf.getChannelData(0);
    const rate = 4.5 + R() * 2.5, ext = 0.15 + R() * 0.45; let ph = 0, vp = R() * 6, cr = rate, ce = ext;
    for (let i = 0; i < n; i++) { const s = i / sr; if (s < start || s > start + dur) { x[i] = 0.002 * (R() * 2 - 1); continue; } const u = s - start; const pv = vp; vp += 2 * Math.PI * cr / sr;
      if (kind === 'jitter' && Math.floor(pv / (2 * Math.PI)) !== Math.floor(vp / (2 * Math.PI))) { cr = rate * (1 + 0.6 * (R() - 0.5)); ce = ext * (1 + 0.6 * (R() - 0.5)); }
      const mid = m + (kind === 'straight' ? 0 : ce * Math.sin(vp)); ph += 2 * Math.PI * 440 * 2 ** ((mid - 69) / 12) / sr;
      let v = 0; for (let h = 1; h <= 8; h++) v += Math.sin(h * ph) / (h * h); x[i] = 0.2 * Math.min(1, u / 0.03, (dur - u) / 0.03) * (v + 0.02 * (R() * 2 - 1)); }
    const fs = await trackTake(buf), st = new Stats(); for (const f of fs) ingest(st, f, 'take'); const fr = st.rec.frames, z = start + dur;
    const e = laneVib(fr.filter(f => f.t <= z + 0.2), z + 0.2); out.push({ m, kind, rate, ext, e }); } return out; });
for (const kind of ['straight', 'even', 'jitter']) { const a = rows.filter(r => r.kind === kind), v = a.filter(r => r.e && r.e.rate), dr = v.map(r => r.e.rate - r.rate), de = v.map(r => r.e.ext - r.ext);
  const ms = q => q.length ? `${(q.reduce((s, x) => s + x, 0) / q.length).toFixed(2)} (max |${Math.max(...q.map(Math.abs)).toFixed(2)}|)` : '-';
  console.log(`${kind}: n ${a.length}, vibrato said ${v.length}, straight said ${a.filter(r => r.e && r.e.straight).length}, rate err ${ms(dr)} Hz, width err ${ms(de)} st, truth in ± ${v.filter(r => r.e.pm != null && Math.abs(r.e.rate - r.rate) <= r.e.pm).length}/${v.filter(r => r.e.pm != null).length}, even ${v.filter(r => r.e.even === true).length}, uneven ${v.filter(r => r.e.even === false).length}`); }
await b.close();
