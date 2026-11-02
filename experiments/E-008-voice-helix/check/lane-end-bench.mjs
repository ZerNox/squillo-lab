// Live note endings (laneEnd, the page's own code) in headless Chrome: single held notes (0.6-1.6 s) over five voices (110-660 Hz),
// straight or vibrato (±0.5 st, 4.5-7 Hz), whose pitch moves by a known amount over the last 0.2 s while the level fades by half, breath noise.
// Frames: the worker's YIN + ingest, without the take's Viterbi (as live). Read 0.2 s after the note stops.
// Usage: node check/lane-end-bench.mjs http://localhost:<port>/
import { chromium } from 'playwright';
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()), p = await b.newPage(); await p.goto(process.argv[2]); await p.waitForTimeout(1000);
const MOVES = [-80, -40, -20, 0, 20, 40];
const rows = await p.evaluate(async (MOVES) => { const sr = 48000, out = []; let seed = 3; const R = () => (seed = seed * 16807 % 2147483647) / 2147483647;
  for (const m of [45, 52, 60, 69, 76]) for (const D of MOVES) for (const vib of [0, 0.5]) for (let r = 0; r < 4; r++) { const dur = 0.6 + R(), start = 0.3, n = Math.round(sr * (start + dur + 0.6)), buf = mkBuf(n, sr), x = buf.getChannelData(0); let ph = 0; const w = R() * 6, rate = 4.5 + R() * 2.5;
    for (let i = 0; i < n; i++) { const s = i / sr; if (s < start || s > start + dur) { x[i] = 0.002 * (R() * 2 - 1); continue; } const u = s - start, rel = Math.max(0, (u - (dur - 0.2)) / 0.2), mid = m + D / 100 * rel + vib * Math.sin(2 * Math.PI * rate * u + w); ph += 2 * Math.PI * 440 * 2 ** ((mid - 69) / 12) / sr;
      let v = 0; for (let h = 1; h <= 8; h++) v += Math.sin(h * ph) / (h * h); x[i] = 0.2 * Math.min(1, u / 0.03, (dur - u) / 0.03) * (1 - 0.5 * rel) * (v + 0.02 * (R() * 2 - 1)); }
    const fs = await trackTake(buf), st = new Stats(); for (const f of fs) ingest(st, f, 'take'); const fr = st.rec.frames, z = start + dur;
    const h = fr.filter(f => f.t <= z + 0.2), e = laneEnd(h, z + 0.2); out.push({ m, D, vib, e: e && { c: e.c, pm: e.pm, say: e.say, held: e.held } }); } return out; }, MOVES);
for (const D of MOVES) { const a = rows.filter(r => r.D === D), ok = a.filter(r => r.e), c = ok.map(r => r.e.c), mu = c.reduce((s, x) => s + x, 0) / c.length, sd = Math.sqrt(c.reduce((s, x) => s + (x - mu) ** 2, 0) / (c.length - 1));
  console.log(`move ${D}: read ${ok.length}/${a.length}, mean ${mu.toFixed(1)} SD ${sd.toFixed(1)} ¢, said ${ok.filter(r => r.e.say).length}, wrong way ${ok.filter(r => r.e.say && Math.sign(r.e.c) !== Math.sign(D)).length}, held ${ok.filter(r => r.e.held).length}; vib said ${ok.filter(r => r.vib && r.e.say).length}/${ok.filter(r => r.vib).length}`); }
await b.close();
