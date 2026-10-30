// Pitch drift per take (takeDrift over takeNotes: the take path, trackTake, viterbiF0, trimEdges, ingest) in headless Chrome.
// 1. Synthetic: 16-note scale melodies (0.6-1.2 s notes, 0.15 s gaps, about 20 s) over five voice types, each note's
//    intonation off by N(0, 12 ¢), half with vibrato (±0.5 st, 5.5 Hz), with a known linear drift of -100..+60 ¢ over
//    the take. Reported: error (estimate - truth) mean, SD, p90 |error|, and how often truth lies inside the ±.
// 2. vocadito (Bittner et al. 2021, CC BY 4.0, https://zenodo.org/records/5578807, not shipped): drift from the page's
//    pitch against drift from the hand-corrected f0 run through the same takeNotes/takeDrift. Also the spread across singers.
// Usage: node check/drift-bench.mjs http://localhost:<port>/ [/path/to/vocadito] [melodies per cell, default 3; 0 skips synthetic]
import { chromium } from 'playwright'; import fs from 'node:fs'; import path from 'node:path';
const [url, dir] = process.argv.slice(2), N = +(process.argv[4] ?? 3);
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()); const p = await b.newPage();
if (dir) await p.route('**/vocadito/**', r => r.fulfill({ body: fs.readFileSync(path.join(dir, 'Audio', path.basename(new URL(r.request().url()).pathname))) }));
await p.goto(url); await p.waitForTimeout(1000);
const syn = await p.evaluate(async N => {
  let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647, gau = () => Math.sqrt(-2 * Math.log(rnd() + 1e-12)) * Math.cos(2 * Math.PI * rnd());
  const voices = { bass: 45, tenor: 55, alto: 60, soprano: 67, child: 64 }, scale = [0, 2, 4, 5, 7, 9, 11, 12], out = [];
  for (const [vn, base] of Object.entries(voices)) for (const D of [-100, -50, -20, 0, 20, 60]) for (let r = 0; r < N; r++) {
    const sr = 48000, K = 16, durs = Array.from({ length: K }, () => 0.6 + 0.6 * rnd()), gap = 0.15, tot = durs.reduce((s, d) => s + d + gap, 0), n = Math.round(sr * tot), x = new Float32Array(n);
    const vib = rnd() < 0.5, notes = durs.map(() => base + scale[Math.floor(rnd() * 8)] + 0.12 * gau());
    let i0 = 0, ph = 0; for (let k = 0; k < K; k++) { const len = Math.round(durs[k] * sr);
      for (let i = 0; i < len; i++) { const s = (i0 + i) / sr, u = i / sr, m = notes[k] + D / 100 * s / tot + (vib ? 0.5 * Math.sin(2 * Math.PI * 5.5 * s) : 0), f = 440 * Math.pow(2, (m - 69) / 12);
        ph += 2 * Math.PI * f / sr; const env = Math.min(1, u / 0.04, (durs[k] - u) / 0.04); let v = 0; for (let h = 1; h * f < 8000; h++) v += Math.sin(h * ph) / h; x[i0 + i] = env * (0.2 * v + 0.004 * (rnd() - 0.5)); }
      i0 += len + Math.round(gap * sr); ph = 0; }
    const buf = mkBuf(n, sr); buf.getChannelData(0).set(x); const F = await trackTake(buf); viterbiF0(F); trimEdges(F, buf); const S = new Stats(); for (const m of F) ingest(S, m, 'take');
    const d = takeDrift(S.rec.frames); out.push({ vn, D, est: d ? d.cents : null, ci: d ? d.ci : null }); }
  return out; }, N);
const q = (a, f) => a.slice().sort((x, y) => x - y)[Math.floor(f * (a.length - 1))], ms = a => { const m = a.reduce((s, x) => s + x, 0) / a.length; return [m, Math.sqrt(a.reduce((s, x) => s + (x - m) ** 2, 0) / (a.length - 1))]; };
const ok = syn.filter(r => r.est !== null), e = ok.map(r => r.est - r.D), [em, es] = ms(e);
if (N) { console.log(`synthetic: ${ok.length}/${syn.length} measured; error ${em.toFixed(1)} ± ${(1.96 * es / Math.sqrt(e.length)).toFixed(1)} ¢ (SD ${es.toFixed(1)}), p90 |error| ${q(e.map(Math.abs), 0.9).toFixed(1)} ¢; truth inside ± ${ok.filter(r => Math.abs(r.est - r.D) <= r.ci).length}/${ok.length}; median ± ${q(ok.map(r => r.ci), 0.5).toFixed(1)} ¢`);
for (const D of [-100, -50, -20, 0, 20, 60]) { const a = ok.filter(r => r.D === D).map(r => r.est); const [m, s] = ms(a); console.log(`  drift ${D}: estimate ${m.toFixed(1)} (SD ${s.toFixed(1)}), |est| beyond its ± ${ok.filter(r => r.D === D && Math.abs(r.est) > r.ci).length}/${a.length}`); }
for (const v of ['bass', 'tenor', 'alto', 'soprano', 'child']) { const a = ok.filter(r => r.vn === v).map(r => r.est - r.D); console.log(`  ${v}: error SD ${ms(a)[1].toFixed(1)}, mean ${ms(a)[0].toFixed(1)}`); } }
if (dir) {
  const meta = fs.readFileSync(path.join(dir, 'vocadito_metadata.csv'), 'utf8').trim().split('\n').slice(1).map(l => l.split(','));
  const rows = [];
  for (const [id] of meta) {
    const truth = fs.readFileSync(path.join(dir, 'Annotations/F0', `vocadito_${id}_f0.csv`), 'utf8').trim().split('\n').map(l => l.split(',').map(Number));
    rows.push(await p.evaluate(async ([id, truth]) => { const ab = await (await fetch(`vocadito/vocadito_${id}.wav`)).arrayBuffer(), buf = await new OfflineAudioContext(1, 1, 44100).decodeAudioData(ab);
      const F = await trackTake(buf); viterbiF0(F); trimEdges(F, buf); const S = new Stats(); for (const m of F) ingest(S, m, 'take'); const est = takeDrift(S.rec.frames);
      const T = []; let j = 0; const off = 0.0025 - (Math.min(Math.floor(buf.sampleRate / 60), 4096 - 1024) + 512) / buf.sampleRate;
      for (const f of S.rec.frames) { const t = f.t + off; while (j + 1 < truth.length && truth[j + 1][0] <= t) j++; const g = truth[j] ? truth[j][1] : 0; T.push({ t: f.t, voiced: g > 0, ok: g > 0, midi: g > 0 ? 69 + 12 * Math.log2(g / 440) : 0 }); }
      const tru = takeDrift(T); return { id, est: est && est.cents, ci: est && est.ci, tru: tru && tru.cents, tci: tru && tru.ci, span: tru && tru.span }; }, [id, truth]));
  }
  const both = rows.filter(r => r.est !== null && r.tru !== null), de = both.map(r => r.est - r.tru), [dm, ds] = ms(de);
  console.log(`vocadito: ${both.length}/${rows.length} clips with 8 notes over 8 s; page - truth ${dm.toFixed(1)} ± ${(1.96 * ds / Math.sqrt(de.length)).toFixed(1)} ¢ (SD ${ds.toFixed(1)}), p90 |diff| ${q(de.map(Math.abs), 0.9).toFixed(1)}; same side beyond ± ${both.filter(r => Math.abs(r.tru) > r.tci).length} truth-drifting clips, page agrees in sign on ${both.filter(r => Math.abs(r.tru) > r.tci && Math.sign(r.est) === Math.sign(r.tru)).length}`);
  const t = both.map(r => r.tru); console.log(`  truth drift across clips: median |drift| ${q(t.map(Math.abs), 0.5).toFixed(1)} ¢, p90 ${q(t.map(Math.abs), 0.9).toFixed(1)}, flat ${t.filter(x => x < 0).length}/${t.length}; span median ${q(both.map(r => r.span), 0.5).toFixed(0)} s; beyond own ± ${both.filter(r => Math.abs(r.tru) > r.tci).length}`);
  for (const r of both) console.log(`  ${r.id}: page ${r.est.toFixed(0)} ± ${r.ci.toFixed(0)}, truth ${r.tru.toFixed(0)} ± ${r.tci.toFixed(0)}`);
}
await b.close();
