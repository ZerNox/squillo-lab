// Timing per take (takeTiming: pulseFit over take-path note onsets) in headless Chrome.
// 1. Synthetic: 24-note melodies on a pulse (steps 0.3-0.6 s, notes 1-4 steps long, half legato), five voice types, onset jitter
//    SD 0/15/30/60 ms, tempo change 0 or ±15 %. Reported: spread estimate per jitter, error of change, pulse found.
// 2. Control: the same melodies with no pulse (note lengths free, 0.25-1.3 s): how often a pulse is falsely found.
// 3. vocadito (Bittner et al. 2021, CC BY 4.0, https://zenodo.org/records/5578807, not shipped): pulseFit on the page's onsets vs on annotated note onsets (A1, notes of 0.2 s or more, as the page keeps).
// Usage: node check/timing-bench.mjs http://localhost:<port>/ [/path/to/vocadito] [melodies per cell, default 2]
import { chromium } from 'playwright'; import fs from 'node:fs'; import path from 'node:path';
const [url, dir] = process.argv.slice(2), N = +(process.argv[4] ?? 2);
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()); const p = await b.newPage();
if (dir) await p.route('**/vocadito/**', r => r.fulfill({ body: fs.readFileSync(path.join(dir, 'Audio', path.basename(new URL(r.request().url()).pathname))) }));
await p.goto(url); await p.waitForTimeout(1000);
const syn = await p.evaluate(async N => {
  let seed = 11; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647, gau = () => Math.sqrt(-2 * Math.log(rnd() + 1e-12)) * Math.cos(2 * Math.PI * rnd());
  const voices = { bass: 45, tenor: 55, alto: 60, soprano: 67, child: 64 }, scale = [0, 2, 4, 5, 7, 9, 11, 12], out = [];
  const run = async (vn, base, on, end, legato, extra) => { const sr = 48000, n = Math.round(sr * (end + 0.5)), x = new Float32Array(n); let ph = 0, last = -1;
    for (let k = 0; k < on.length; k++) { let m; do m = base + scale[Math.floor(rnd() * 8)]; while (m === last); last = m; const f = 440 * 2 ** ((m - 69) / 12), a = Math.round(on[k] * sr), d = (k + 1 < on.length ? on[k + 1] : end) - on[k] - (legato ? 0 : 0.08), l = Math.round(d * sr);
      for (let i = 0; i < l && a + i < n; i++) { const u = i / sr; ph += 2 * Math.PI * f / sr; const e = Math.min(1, u / 0.02, (d - u) / 0.02); let v = 0; for (let h = 1; h * f < 6000; h++) v += Math.sin(h * ph) / h; x[a + i] = e * (0.2 * v + 0.004 * (rnd() - 0.5)); } }
    const buf = mkBuf(n, sr); buf.getChannelData(0).set(x); const F = await trackTake(buf); viterbiF0(F); trimEdges(F, buf); const S = new Stats(); for (const m of F) ingest(S, m, 'take'); const r = takeTiming(S.rec.frames); out.push({ vn, ...extra, legato, found: r ? r.pulse : false, sd: r && r.sd, ci: r && r.ci, change: r && r.change, step: r && r.step, ratio: r && r.ratio }); };
  for (const [vn, base] of Object.entries(voices)) for (let r = 0; r < N; r++) for (const legato of [false, true]) {
    for (const J of [0, 15, 30, 60]) for (const C of [0, 15, -15]) { const T = 0.3 + 0.3 * rnd(); let g = 0.3; const on = []; for (let k = 0; k < 24; k++) { const P = T * (1 + C / 100 * k / 23); on.push(g + J / 1000 * gau()); g += P * [1, 1, 2, 2, 3, 4][Math.floor(rnd() * 6)]; }
      on.sort((a, b) => a - b); await run(vn, base, on, g, legato, { J, C, T }); }
    let g = 0.3; const on = []; for (let k = 0; k < 24; k++) { on.push(g); g += 0.25 + 1.05 * rnd(); } await run(vn, base, on, g, legato, { free: 1 }); await run(vn, base, on.map(x => x * 0.8), g * 0.8, legato, { free: 1 }); }
  return out; }, N);
const q = (a, f) => a.slice().sort((x, y) => x - y)[Math.floor(f * (a.length - 1))], ms = a => { const m = a.reduce((s, x) => s + x, 0) / a.length; return [m, Math.sqrt(a.reduce((s, x) => s + (x - m) ** 2, 0) / Math.max(1, a.length - 1))]; };
const P = syn.filter(r => !r.free), F = syn.filter(r => r.free);
for (const J of [0, 15, 30, 60]) { const a = P.filter(r => r.J === J), f = a.filter(r => r.found), [m, s] = ms(f.map(r => r.sd)), ce = f.map(r => r.change - r.C); console.log(`jitter ${J} ms: pulse found ${f.length}/${a.length}; spread ${m.toFixed(1)} (SD ${s.toFixed(1)}), median ${q(f.map(r => r.sd), 0.5).toFixed(1)}; ratio p50 ${q(a.map(r => r.ratio), 0.5).toFixed(3)}; change error mean ${ms(ce)[0].toFixed(1)} SD ${ms(ce)[1].toFixed(1)} %; truth inside ± ${f.filter(r => Math.abs(r.sd - J) <= r.ci + 5).length}/${f.length} (±+5 ms)`); }
for (const l of [false, true]) { const f = P.filter(r => r.legato === l && r.found && r.J === 0); console.log(`  ${l ? 'legato' : 'gapped'} J=0 spread median ${q(f.map(r => r.sd), 0.5).toFixed(1)}`); }
console.log(`no pulse control: falsely found ${F.filter(r => r.found).length}/${F.length}; ratio p10 ${q(F.map(r => r.ratio), 0.1).toFixed(3)} p50 ${q(F.map(r => r.ratio), 0.5).toFixed(3)}`);
if (dir) { const meta = fs.readFileSync(path.join(dir, 'vocadito_metadata.csv'), 'utf8').trim().split('\n').slice(1).map(l => l.split(',')), rows = [];
  for (const [id] of meta) { const on = fs.readFileSync(path.join(dir, 'Annotations/Notes', `vocadito_${id}_notesA1.csv`), 'utf8').trim().split('\n').map(l => l.split(',').map(Number)).filter(n => n[2] >= 0.2).map(n => n[0]);
    rows.push(await p.evaluate(async ([id, on]) => { const ab = await (await fetch(`vocadito/vocadito_${id}.wav`)).arrayBuffer(), buf = await new OfflineAudioContext(1, 1, 44100).decodeAudioData(ab); const F = await trackTake(buf); viterbiF0(F); trimEdges(F, buf); const S = new Stats(); for (const m of F) ingest(S, m, 'take'); const e = takeTiming(S.rec.frames), t = pulseFit(on); return { id, e, t }; }, [id, on])); }
  const both = rows.filter(r => r.e && r.t), de = both.map(r => r.e.sd - r.t.sd), dc = both.map(r => r.e.change - r.t.change);
  const R = both.map(r => r.e.ratio), Rt = both.map(r => r.t.ratio); console.log(`vocadito: ${both.length}/${rows.length} measured; pulse page ${both.filter(r => r.e.pulse).length}, truth ${both.filter(r => r.t.pulse).length}, both ${both.filter(r => r.e.pulse && r.t.pulse).length}; ratio page p50 ${q(R, 0.5).toFixed(3)}, truth p50 ${q(Rt, 0.5).toFixed(3)}`);
  const pp = both.filter(r => r.e.pulse && r.t.pulse), d2 = pp.map(r => r.e.sd - r.t.sd), d3 = pp.map(r => r.e.change - r.t.change); if (pp.length > 1) console.log(`  both pulsed (${pp.length}): spread page - truth ${ms(d2)[0].toFixed(1)} ms (SD ${ms(d2)[1].toFixed(1)}); truth spread median ${q(pp.map(r => r.t.sd), 0.5).toFixed(0)}; change diff ${ms(d3)[0].toFixed(1)} (SD ${ms(d3)[1].toFixed(1)}) %; step agrees within 5 % or by 2×: ${pp.filter(r => [0.5, 1, 2].some(k => Math.abs(r.e.step / r.t.step / k - 1) < 0.05)).length}`); }
await b.close();
