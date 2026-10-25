// Pitch tracker for takes on real singing: vocadito (Bittner et al. 2021, 40 solo a cappella excerpts, 29 singers,
// 7 languages, f0 annotated; CC BY 4.0, https://zenodo.org/records/5578807). Not shipped: download to a folder first.
// Runs the page's own code (trackTake, viterbiF0) in headless Chrome. Each page frame (20 ms hop) is compared with the
// nearest annotation (5.8 ms grid). Metrics as mir_eval melody: RPA (truth voiced, estimate voiced and within 50 ¢),
// RCA (same, octave errors forgiven), voicing recall, false alarm (truth unvoiced, estimate voiced), overall accuracy.
// Frame time = m.t + 2.5 ms - analysis window as in pitch-bench.mjs; a lag sweep reports the best global lag too.
// ± = 1.96 SE over the 40 clips. Usage: node check/vocadito-bench.mjs http://localhost:<port>/ /path/to/vocadito
import { chromium } from 'playwright'; import fs from 'node:fs'; import path from 'node:path';
const [url, dir] = process.argv.slice(2);
const meta = fs.readFileSync(path.join(dir, 'vocadito_metadata.csv'), 'utf8').trim().split('\n').slice(1).map(l => l.split(','));
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()); const p = await b.newPage();
await p.route('**/vocadito/**', r => r.fulfill({ body: fs.readFileSync(path.join(dir, 'Audio', path.basename(new URL(r.request().url()).pathname))) }));
await p.goto(url); await p.waitForTimeout(1000);
const lags = process.env.VIT ? [0] : [-60, -40, -20, -10, 0, 10, 20, 40, 60]; if (process.env.VIT) await p.evaluate(v => Object.assign(VIT, JSON.parse(v)), process.env.VIT); // VIT='{"U":0.6}': try other Viterbi costs
const rows = [];
for (const [id, singer, avg] of meta) {
  const truth = fs.readFileSync(path.join(dir, 'Annotations/F0', `vocadito_${id}_f0.csv`), 'utf8').trim().split('\n').map(l => +l.split(',')[1]);
  const est = await p.evaluate(async id => { const ab = await (await fetch(`vocadito/vocadito_${id}.wav`)).arrayBuffer();
    const ac = new OfflineAudioContext(1, 1, 44100); const buf = await ac.decodeAudioData(ab);
    const fs = await trackTake(buf); viterbiF0(fs); const sr = buf.sampleRate, off = 0.0025 - (Math.min(Math.floor(sr / 60), 4096 - 1024) + 512) / sr;
    return fs.map(m => [m.t + off, m.voiced ? m.f0 : 0]); }, id);
  const H = 256 / 44100, score = lag => { const a = { tv: 0, hit: 0, chr: 0, vr: 0, tu: 0, fa: 0, ok: 0, n: 0 };
    for (const [t, f] of est) { const j = Math.round((t + lag / 1000) / H); if (j < 0 || j >= truth.length) continue; const T = truth[j]; a.n++;
      if (T > 0) { a.tv++; if (f > 0) { a.vr++; const c = 1200 * Math.log2(f / T); if (Math.abs(c) <= 50) { a.hit++; a.ok++; } const cc = ((c % 1200) + 1800) % 1200 - 600; if (Math.abs(cc) <= 50) a.chr++; } }
      else { a.tu++; if (f > 0) a.fa++; else a.ok++; } } return a; };
  const r = Object.fromEntries(lags.map(l => [l, score(l)]));
  rows.push({ id, singer, avg: +avg, r });
}
await b.close();
const ms = v => { const m = v.reduce((s, x) => s + x, 0) / v.length, sd = Math.sqrt(v.reduce((s, x) => s + (x - m) ** 2, 0) / (v.length - 1)); return [m, 1.96 * sd / Math.sqrt(v.length)]; };
const f = ([m, e]) => `${(100 * m).toFixed(1)} ± ${(100 * e).toFixed(1)}`;
for (const l of lags) { const g = k => rows.map(x => x.r[l][k]); const s = (k, d) => rows.map(x => x.r[l][k] / Math.max(1, x.r[l][d]));
  const tot = k => rows.reduce((S, x) => S + x.r[l][k], 0);
  console.log(`lag ${String(l).padStart(3)} ms  RPA ${f(ms(s('hit', 'tv')))}  RCA ${f(ms(s('chr', 'tv')))}  VR ${f(ms(s('vr', 'tv')))}  FA ${f(ms(s('fa', 'tu')))}  OA ${f(ms(s('ok', 'n')))}  pooled RPA ${(100 * tot('hit') / tot('tv')).toFixed(1)}`); }
console.log('per clip at lag 0 (id singer avgMIDI RPA RCA VR FA):');
for (const x of rows) { const a = x.r[0]; console.log(x.id, x.singer, x.avg, (100 * a.hit / a.tv).toFixed(1), (100 * a.chr / a.tv).toFixed(1), (100 * a.vr / a.tv).toFixed(1), (100 * a.fa / Math.max(1, a.tu)).toFixed(1)); }
const lo = rows.filter(x => x.avg < 57), hi = rows.filter(x => x.avg >= 57), rpa = R => ms(R.map(x => x.r[0].hit / x.r[0].tv));
console.log(`low voices (avg < A3, n=${lo.length}) RPA ${f(rpa(lo))}; high (n=${hi.length}) RPA ${f(rpa(hi))}`);
