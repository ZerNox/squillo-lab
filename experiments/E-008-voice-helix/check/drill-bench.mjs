// Sing it again (tryRead, the page's own code) in headless Chrome on synthetic held notes with known offset from the target: 5 voices (110-660 Hz), offsets -60..60 ¢,
// straight or vibrato (±0.5 st, 5.5 Hz), a 150 ms scoop in, breath noise, slow wander. Also on VocalSet (CC BY 4.0, not shipped) if a dir is given: long tones read, then read again resampled by a known number of cents (same note, truth is the shift).
// Usage: node check/drill-bench.mjs http://localhost:<port>/ [vocalset dir] [max files]
import { chromium } from 'playwright'; import fs from 'node:fs'; import path from 'node:path';
const [url, dir0, max] = process.argv.slice(2), dir = dir0 && path.resolve(dir0);
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()), p = await b.newPage(); await p.goto(url); await p.waitForTimeout(1000);
const syn = await p.evaluate(async () => { const sr = 48000, out = []; let seed = 1; const R = () => (seed = seed * 16807 % 2147483647) / 2147483647;
  for (const m of [45, 52, 60, 69, 76]) for (const off of [-60, -30, -10, 0, 20, 45]) for (const vib of [0, 0.5]) { const T = 3, n = sr * T, buf = mkBuf(n, sr), x = buf.getChannelData(0); let ph = 0, w = R() * 6; const start = 0.4;
    for (let i = 0; i < n; i++) { const s = i / sr; if (s < start || s > start + 2.2) continue; const u = s - start, mid = m + off / 100 + vib * Math.sin(2 * Math.PI * 5.5 * u + w) + 0.05 * Math.sin(2 * Math.PI * 0.7 * u + w) - (u < 0.15 ? 1 - u / 0.15 : 0); ph += 2 * Math.PI * 440 * Math.pow(2, (mid - 69) / 12) / sr;
      let v = 0; for (let h = 1; h <= 8; h++) v += Math.sin(h * ph) / (h * h); x[i] = 0.2 * Math.min(1, u / 0.03, (2.2 - u) / 0.03) * (v + 0.02 * (R() * 2 - 1)); }
    const r = await tryRead(buf, m); out.push({ m, off, vib, c: r && r.c, e: r && r.e }); } return out; });
const stat = (rows, name) => { const ok = rows.filter(r => r.c !== null), err = ok.map(r => r.c - r.off), md = err.reduce((a, c) => a + c, 0) / err.length, sd = Math.sqrt(err.reduce((a, c) => a + (c - md) ** 2, 0) / err.length), a = err.map(Math.abs).sort((x, y) => x - y);
  console.log(`${name}: read ${ok.length}/${rows.length}, bias ${md.toFixed(1)}, SD ${sd.toFixed(1)}, median |error| ${a[a.length >> 1].toFixed(1)}, max ${a[a.length - 1].toFixed(1)} ¢, truth inside ± ${ok.filter(r => Math.abs(r.c - r.off) <= r.e).length}/${ok.length}, median ± ${ok.map(r => r.e).sort((x, y) => x - y)[ok.length >> 1].toFixed(1)}`); };
stat(syn.filter(r => !r.vib), 'synthetic straight'); stat(syn.filter(r => r.vib), 'synthetic vibrato');
if (dir) { const files = []; const walk = d => { for (const e of fs.readdirSync(d, { withFileTypes: true })) { const f = path.join(d, e.name); if (e.isDirectory()) walk(f); else if (/_long_(straight|vibrato).*\.wav$/.test(e.name)) files.push(f); } }; walk(dir);
  await p.route('**/vs/**', r => r.fulfill({ body: fs.readFileSync(decodeURIComponent(new URL(r.request().url()).pathname.slice(3))) }));
  const rows = []; const pick = files.sort().filter((_, i, a) => i % Math.max(1, Math.floor(a.length / (+max || 40))) === 0);
  for (const f of pick) { const r = await p.evaluate(async ([f]) => { const ab = await (await fetch('vs/' + encodeURI(f).replace(/^\//, ''))).arrayBuffer(), d = await new OfflineAudioContext(1, 1, 44100).decodeAudioData(ab), x = d.getChannelData(0), best = 3 * 44100; if (x.length < 44100) return null;
      const slice = (s) => { const k = Math.pow(2, s / 1200), n = Math.min(Math.floor(x.length / k), Math.floor(4 * 44100)), bf = mkBuf(n, 44100), y = bf.getChannelData(0); for (let i = 0; i < n; i++) { const u = i * k, a = Math.floor(u), q = u - a; y[i] = x[a] * (1 - q) + (x[a + 1] || 0) * q; } return bf; };
      const z = await tryRead(slice(0), 60); if (!z) return null; const m = 60 + z.c / 100; const out = []; for (const s of [-40, 25]) { const q = await tryRead(slice(s), m); out.push(q && { off: s, c: q.c, e: q.e }); } return out; }, [f]); if (r) rows.push(...r.filter(Boolean)); }
  stat(rows, `VocalSet ${pick.length} files, shifted`); }
await b.close();
