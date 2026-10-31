// The Lane's big reading (laneRead, the page's own code) in headless Chrome on synthetic held notes with a known offset: 5 voices (110-660 Hz), offsets -60..45 ¢, straight or vibrato (±0.5 st, 4.5-7 Hz),
// slow wander (truth at the window centre, so it counts), breath noise. Frames: the worker's YIN + ingest, without the take's Viterbi, read every 0.1 s from 0.6 s into the note.
// Usage: node check/lane-bench.mjs http://localhost:<port>/
import { chromium } from 'playwright';
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()), p = await b.newPage(); await p.goto(process.argv[2]); await p.waitForTimeout(1000);
const rows = await p.evaluate(async () => { const sr = 48000, out = []; let seed = 1; const R = () => (seed = seed * 16807 % 2147483647) / 2147483647;
  for (const m of [45, 52, 60, 69, 76]) for (const off of [-60, -30, -10, 0, 20, 45]) for (const vib of [0, 0.5]) { const n = sr * 3, buf = mkBuf(n, sr), x = buf.getChannelData(0); let ph = 0; const w = R() * 6, start = 0.4, rate = 4.5 + R() * 2.5;
    for (let i = 0; i < n; i++) { const s = i / sr; if (s < start || s > start + 2.2) continue; const u = s - start, mid = m + off / 100 + vib * Math.sin(2 * Math.PI * rate * u + w) + 0.05 * Math.sin(2 * Math.PI * 0.7 * u + w); ph += 2 * Math.PI * 440 * 2 ** ((mid - 69) / 12) / sr;
      let v = 0; for (let h = 1; h <= 8; h++) v += Math.sin(h * ph) / (h * h); x[i] = 0.2 * Math.min(1, u / 0.03, (2.2 - u) / 0.03) * (v + 0.02 * (R() * 2 - 1)); }
    const fs = await trackTake(buf), st = new Stats(); for (const f of fs) ingest(st, f, 'take'); const fr = st.rec.frames;
    for (let t = 1.0; t < 2.5; t += 0.1) { const h = fr.filter(f => f.t <= t), r = laneRead(h, t, m); out.push({ vib, off: off + 5 * Math.sin(2 * Math.PI * 0.7 * (t - 0.2 - start) + w), r: r && { c: r.c, pm: r.pm } }); } } return out; });
for (const v of [0, 0.5]) { const a = rows.filter(r => r.vib === v), ok = a.filter(r => r.r), e = ok.map(r => Math.abs(r.r.c - r.off)).sort((x, y) => x - y), pm = ok.map(r => r.r.pm).sort((x, y) => x - y);
  console.log(`vibrato ${v} st: read ${ok.length}/${a.length}, median |error| ${e[e.length >> 1].toFixed(1)}, p95 ${e[Math.floor(e.length * 0.95)].toFixed(1)}, max ${e[e.length - 1].toFixed(1)} ¢, median ± ${pm[pm.length >> 1].toFixed(1)}, truth inside ± ${(100 * ok.filter(r => Math.abs(r.r.c - r.off) <= r.r.pm).length / ok.length).toFixed(1)} %`); }
await b.close();
