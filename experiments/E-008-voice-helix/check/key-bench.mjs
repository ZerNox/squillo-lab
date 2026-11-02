// The scale of a take: takeKey, the page's own code, headless Chrome.
// Synthetic: tonal random-walk diatonic melodies, 40 and 60 notes, 24 keys, notes SD 12 ¢, 10 % a semitone off the scale. Truth known; a proxy for real melodies.
// Real: vocadito (Bittner et al. 2021, CC BY 4.0, not shipped) through the take path. No key labels: page's notes against annotator A1's notes, agreement only.
// Usage: node check/key-bench.mjs http://localhost:<port>/ /path/to/vocadito
import { chromium } from 'playwright'; import fs from 'node:fs'; import path from 'node:path';
const [url, dir] = process.argv.slice(2);
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()), p = await b.newPage();
await p.route('**/vocadito/**', r => r.fulfill({ body: fs.readFileSync(path.join(dir, 'Audio', path.basename(new URL(r.request().url()).pathname))) }));
await p.goto(url); await p.waitForTimeout(1000);
const wil = (k, n) => { const c = k / Math.max(1, n), z = 1.96, d = 1 + z * z / n, m = (c + z * z / 2 / n) / d, e = z * Math.sqrt(c * (1 - c) / n + z * z / 4 / n / n) / d; return `${k}/${n} = ${(100 * c).toFixed(1)} % (${(100 * (m - e)).toFixed(1)}-${(100 * (m + e)).toFixed(1)})`; };
console.log(await p.evaluate(() => { let seed = 7; const rnd = () => (seed = seed * 16807 % 2147483647) / 2147483647, g = () => Math.sqrt(-2 * Math.log(rnd() || 1e-9)) * Math.cos(6.283185 * rnd()), o = {};
  for (const L of [40, 60]) { let sure = 0, ok = 0; for (let r = 0; r < 600; r++) { const sc = r % 12, P = []; for (let m = 48; m < 84; m++) if (MAJOR.includes((m - sc + 120) % 12)) P.push(m); let i = 10, t = 0; const N = [];
      for (let k = 0; k < L; k++) { i = Math.max(0, Math.min(P.length - 1, i + Math.round(g() * 1.5))); const d = 0.25 + rnd() * 0.75, m = P[i] + (rnd() < 0.1 ? (rnd() < 0.5 ? 1 : -1) : 0); N.push({ m, t0: t, t1: t + d }); t += d; }
      const q = takeKey(N, 0); if (q && q.sure >= KEYQ.S) { sure++; if (q.sc === sc) ok++; } } o[L] = [sure, ok]; } return o; }));
const meta = fs.readFileSync(path.join(dir, 'vocadito_metadata.csv'), 'utf8').trim().split('\n').slice(1).map(l => l.split(','));
let said = 0, long = 0, both = 0, agr = 0;
for (const [id] of meta) { const A = fs.readFileSync(path.join(dir, `Annotations/Notes/vocadito_${id}_notesA1.csv`), 'utf8').trim().split('\n').map(l => l.split(',').map(Number));
  const r = await p.evaluate(async ([id, A]) => { const ab = await (await fetch(`vocadito/vocadito_${id}.wav`)).arrayBuffer(), buf = await new OfflineAudioContext(1, 1, 44100).decodeAudioData(ab), fs = await trackTake(buf); viterbiF0(fs); trimEdges(fs, buf); const st = new Stats(); for (const f of fs) ingest(st, f, 'take');
    const a = takeAspects(st), k = a.key, med = A.map(([t, f, d]) => ({ med: 69 + 12 * Math.log2(f / 440), t0: t, t1: t + d, wob: 3 })); let x = 0, y = 0; for (const n of med) { const q = 6.283185 * (n.med - Math.round(n.med)); x += Math.cos(q); y += Math.sin(q); } const o = Math.atan2(y, x) / 6.283185, ka = takeKey(notePerf(med, o, []), o), S = KEYQ.S;
    return { n: a.perf.length, s: k && k.sure >= S ? k.sc : -1, sa: ka ? ka.sc : -1 }; }, [id, A]);
  if (r.n >= 30) long++; if (r.s >= 0) { said++; if (r.sa >= 0) { both++; if (r.s === r.sa) agr++; } } }
console.log(`vocadito: 30+ notes ${long}/${meta.length}, scale said ${said}, agrees with annotator notes ${wil(agr, both)}`);
await b.close();
