// Register lean (takeLean over the take path: trackTake, viterbiF0, trimEdges, ingest) in headless Chrome.
// 1. Synthetic: 18-note melodies (0.6-1.2 s, 1.5 octaves) over five voices, note error N(0, 12 ¢), half with vibrato, some with a -40 ¢ key drift; the top of the range leans by a known amount, linear in pitch. Truth = the same notes' group difference.
// 2. vocadito (Bittner et al. 2021, CC BY 4.0, not shipped): lean from page pitch against lean from the hand-corrected f0.
// Usage: node check/lean-bench.mjs http://localhost:<port>/ [/path/to/vocadito] [melodies per cell, default 2; 0 skips synthetic]
import { chromium } from 'playwright'; import fs from 'node:fs'; import path from 'node:path';
const [url, dir] = process.argv.slice(2), N = +(process.argv[4] ?? 2);
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()); const p = await b.newPage();
if (dir) await p.route('**/vocadito/**', r => r.fulfill({ body: fs.readFileSync(path.join(dir, 'Audio', path.basename(new URL(r.request().url()).pathname))) }));
await p.goto(url); await p.waitForTimeout(1000);
const syn = await p.evaluate(async N => {
  let seed = 11; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647, gau = () => Math.sqrt(-2 * Math.log(rnd() + 1e-12)) * Math.cos(2 * Math.PI * rnd());
  const voices = { bass: 43, tenor: 52, alto: 58, soprano: 65, child: 62 }, scale = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19], out = [];
  for (const [vn, base] of Object.entries(voices)) for (const L of [-40, -25, -15, 0, 15, 25, 40]) for (let r = 0; r < N; r++) {
    const sr = 48000, K = 18, durs = Array.from({ length: K }, () => 0.6 + 0.6 * rnd()), gap = 0.15, tot = durs.reduce((s, d) => s + d + gap, 0), n = Math.round(sr * tot), x = new Float32Array(n);
    const vib = rnd() < 0.5, D = rnd() < 0.3 ? -40 : 0, deg = durs.map(() => scale[Math.floor(rnd() * 12)]), notes = deg.map(g => base + g + (L / 100) * (g / 19 - 0.5) * 1.5 + 0.12 * gau());
    let i0 = 0, ph = 0; for (let k = 0; k < K; k++) { const len = Math.round(durs[k] * sr);
      for (let i = 0; i < len; i++) { const s = (i0 + i) / sr, u = i / sr, m = notes[k] + D / 100 * s / tot + (vib ? 0.5 * Math.sin(2 * Math.PI * 5.5 * s) : 0), f = 440 * Math.pow(2, (m - 69) / 12);
        ph += 2 * Math.PI * f / sr; const env = Math.min(1, u / 0.04, (durs[k] - u) / 0.04); let v = 0; for (let h = 1; h * f < 8000; h++) v += Math.sin(h * ph) / h; x[i0 + i] = env * (0.2 * v + 0.004 * (rnd() - 0.5)); }
      i0 += len + Math.round(gap * sr); ph = 0; }
    const buf = mkBuf(n, sr); buf.getChannelData(0).set(x); const F = await trackTake(buf); viterbiF0(F); trimEdges(F, buf); const S = new Stats(); for (const m of F) ingest(S, m, 'take');
    const d = takeLean(S.rec.frames); out.push({ vn, L, R: d ? d.R : 0, alt: d ? d.alt : 0, est: d ? d.cents : null, ci: d ? d.ci : null, say: d ? leanLine(d, false).length > 0 : false }); }
  return out; }, N);
const ms = a => { const m = a.reduce((s, x) => s + x, 0) / a.length; return [m, Math.sqrt(a.reduce((s, x) => s + (x - m) ** 2, 0) / Math.max(1, a.length - 1))]; };
if (N) { const ok = syn.filter(r => r.est !== null); console.log(`synthetic: ${ok.length}/${syn.length} read`);
  for (const L of [-40, -25, -15, 0, 15, 25, 40]) { const a = ok.filter(r => r.L === L), [m, s] = ms(a.map(r => r.est)); console.log(`  lean ${L}: estimate ${m.toFixed(1)} SD ${s.toFixed(1)}, said ${a.filter(r => r.say).length}/${a.length}, wrong way ${a.filter(r => r.say && L && Math.sign(r.est) !== Math.sign(L)).length}, median ± ${ms(a.map(r => r.ci))[0].toFixed(0)}, R ${ms(a.map(r => r.R))[0].toFixed(2)} alt ${ms(a.map(r => r.alt))[0].toFixed(2)}`); } }
if (dir) { const ids = fs.readFileSync(path.join(dir, 'vocadito_metadata.csv'), 'utf8').trim().split('\n').slice(1).map(l => l.split(',')[0]), rows = [];
  for (const id of ids) { const truth = fs.readFileSync(path.join(dir, 'Annotations/F0', `vocadito_${id}_f0.csv`), 'utf8').trim().split('\n').map(l => l.split(',').map(Number));
    rows.push(await p.evaluate(async ([id, truth]) => { const ab = await (await fetch(`vocadito/vocadito_${id}.wav`)).arrayBuffer(), buf = await new OfflineAudioContext(1, 1, 44100).decodeAudioData(ab);
      const F = await trackTake(buf); viterbiF0(F); trimEdges(F, buf); const S = new Stats(); for (const m of F) ingest(S, m, 'take'); const est = takeLean(S.rec.frames);
      const T = []; let j = 0; const off = 0.0025 - (Math.min(Math.floor(buf.sampleRate / 60), 4096 - 1024) + 512) / buf.sampleRate;
      for (const f of S.rec.frames) { const t = f.t + off; while (j + 1 < truth.length && truth[j + 1][0] <= t) j++; const g = truth[j] ? truth[j][1] : 0; T.push({ t: f.t, voiced: g > 0, ok: g > 0, midi: g > 0 ? 69 + 12 * Math.log2(g / 440) : 0 }); }
      const tru = takeLean(T); return { id, R: est && est.R, alt: est && est.alt, est: est && est.cents, ci: est && est.ci, say: leanLine(est, false).length > 0, good: leanLine(est, true).length > 0, tru: tru && tru.cents, tci: tru && tru.ci, tsay: leanLine(tru, false).length > 0 }; }, [id, truth])); }
  const both = rows.filter(r => r.est !== null && r.tru !== null), e = both.map(r => r.est - r.tru), [m, s] = ms(e);
  console.log(`vocadito: ${rows.filter(r => r.est !== null).length}/${rows.length} read by page, ${both.length} by both; page - truth ${m.toFixed(1)} (SD ${s.toFixed(1)}); page says ${both.filter(r => r.say).length}, praise ${both.filter(r => r.good).length}, hand f0 says ${both.filter(r => r.tsay).length}, both say same way ${both.filter(r => r.say && r.tsay && r.est * r.tru > 0).length}, page says truth does not ${both.filter(r => r.say && !r.tsay).length}, opposite ${both.filter(r => r.say && r.est * r.tru < 0).length}, truth inside ± ${both.filter(r => Math.abs(r.est - r.tru) <= r.ci).length}`);
  for (const r of both) console.log(`  ${r.id}: R ${r.R.toFixed(2)} alt ${r.alt.toFixed(2)} page ${r.est.toFixed(0)} ± ${r.ci.toFixed(0)}${r.say ? ' SAY' : ''}, truth ${r.tru.toFixed(0)} ± ${r.tci.toFixed(0)}${r.tsay ? ' SAY' : ''}`); }
await b.close();
