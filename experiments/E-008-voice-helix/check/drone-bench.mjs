// A drone leaking into the mic: the Lane's reading (laneRead, page code) in headless Chrome on synthetic notes with the page's drone (DRONE.h) mixed in on the target note, at levels against the voice.
// 5 voices (A2-E5), offsets ±10-40 ¢, straight or vibrato ±0.5 st, 240 or so reads each. Usage: node check/drone-bench.mjs http://localhost:<port>/
import { chromium } from 'playwright';
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()), p = await b.newPage(); await p.goto(process.argv[2]); await p.waitForTimeout(1000);
const rows = await p.evaluate(async () => { const sr = 48000, out = []; let seed = 1; const R = () => (seed = seed * 16807 % 2147483647) / 2147483647;
  for (const db of [-99, -24, -18, -12, -6]) for (const vib of [0, 0.5]) for (const m of [45, 52, 60, 69, 76]) for (const off of [-40, -20, -10, 10, 20, 40]) { const n = sr * 3, buf = mkBuf(n, sr), x = buf.getChannelData(0), df = 440 * 2 ** ((m - 69) / 12), A = 0.2 * 10 ** (db / 20); let ph = 0;
    for (let i = 0; i < n; i++) { const s = i / sr; let d = 0; DRONE.h.forEach((a, k) => d += a * Math.sin(2 * Math.PI * (k + 1) * df * s)); x[i] = A * d; if (s < .4 || s > 2.6) continue; const u = s - .4; ph += 2 * Math.PI * 440 * 2 ** ((m + off / 100 + vib * Math.sin(2 * Math.PI * 5.5 * u) - 69) / 12) / sr; let v = 0; for (let h = 1; h <= 8; h++) v += Math.sin(h * ph) / (h * h); x[i] += .2 * Math.min(1, u / .03, (2.2 - u) / .03) * (v + .02 * (R() * 2 - 1)); }
    const fs = await trackTake(buf), st = new Stats(); for (const f of fs) ingest(st, f, 'take'); const fr = st.rec.frames;
    for (let t = 1; t < 2.5; t += .1) { const r = laneRead(fr.filter(f => f.t <= t), t, m); out.push({ db, vib, e: r ? Math.abs(r.c - off) : null }); } } return out; });
for (const vib of [0, 0.5]) for (const db of [-99, -24, -18, -12, -6]) { const a = rows.filter(r => r.db === db && r.vib === vib), e = a.map(r => r.e).filter(x => x !== null).sort((x, y) => x - y);
  console.log(`vibrato ${vib} st, drone ${db} dB: read ${e.length}/${a.length}, median ${e[e.length >> 1].toFixed(1)}, p95 ${e[e.length * .95 | 0].toFixed(1)}, max ${e.at(-1).toFixed(1)} ¢`); }
await b.close();
