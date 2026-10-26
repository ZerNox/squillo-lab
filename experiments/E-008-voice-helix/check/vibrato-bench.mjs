// Vibrato rate and extent, measured with the page's own code (trackTake, viterbiF0, trimEdges, ingest: the
// same path as a take) in headless Chrome. Synthetic sustained notes (2 s, 40 ms ramps) over five voice
// types (bass to child), harmonic source with breath noise at -20 dB, small jitter; vibrato rate 4-8 Hz,
// extent (peak) 0.15-1.5 st, rate jittered ±5 % cycle to cycle; plus straight notes (slow random drift ±10 ¢)
// for false detections. Truth per note: rate and peak extent. Estimate: median of the page's vibrato chip
// (vibRate, vibExt) over the note's frames 0.9-1.9 s after its onset. ± = 1.96 SE over notes.
// Usage: node check/vibrato-bench.mjs http://localhost:<port>/ [notes per voice, default 24] [seed]
import { chromium } from 'playwright';
const url = process.argv[2], N = +(process.argv[3] || 24), SEED = +(process.argv[4] || 7);
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()); const p = await b.newPage(); await p.goto(url); await p.waitForTimeout(1000);
if (process.env.VIT) await p.evaluate(v => Object.assign(VIT, JSON.parse(v)), process.env.VIT);
const rows = await p.evaluate(async ([N, SEED]) => {
  let seed = SEED; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const voices = { bass: [82, 165], tenor: [130, 330], alto: [175, 525], soprano: [262, 880], child: [250, 700] };
  const out = [];
  for (const [vn, [lo, hi]] of Object.entries(voices)) {
    const sr = 44100, nd = 2, gap = 0.4, notes = [];
    for (let k = 0; k < N; k++) notes.push({ f: lo * Math.pow(hi / lo, rnd()), straight: k % 4 === 3, sag: k % 2 === 1 ? (rnd() < 0.5 ? -1 : 1) * 0.6 : 0, rate: 4 + 4 * rnd(), ext: 0.15 * Math.pow(10, rnd()), jr: [0.05, 0.15, 0.3][k % 3], je: [0, 0.2, 0.4][(k >> 2) % 3] });
    const n = Math.round(sr * N * (nd + gap)), x = new Float32Array(n); let ph = 0, vph = 0, vr = 0, ve = 1, drift = 0;
    for (let i = 0; i < n; i++) { const s = i / sr, k = Math.floor(s / (nd + gap)), u = s - k * (nd + gap), q = notes[k];
      if (u > nd || !q) { ph = 0; vph = 0; x[i] = 0.001 * (rnd() - 0.5); continue; }
      if (i % 441 === 0) { drift = 0.97 * drift + 0.03 * 10 * (rnd() - 0.5) * 2; }
      if (vph === 0 || Math.floor(vph / (2 * Math.PI)) !== Math.floor((vph + 2 * Math.PI * vr / sr) / (2 * Math.PI))) { vr = q.rate * (1 + 2 * q.jr * (rnd() - 0.5)); ve = 1 + 2 * q.je * (rnd() - 0.5); }
      vph += 2 * Math.PI * vr / sr;
      const st = (q.straight ? 0 : q.ext * ve * Math.sin(vph)) + drift / 100 + q.sag * (u / nd - 0.5), f = q.f * Math.pow(2, st / 12) * (1 + 0.002 * (rnd() - 0.5));
      ph += 2 * Math.PI * f / sr; const env = Math.min(1, u / 0.04, (nd - u) / 0.04);
      let v = 0; for (let h = 1; h * f < 8000; h++) v += Math.sin(h * ph) / h;
      x[i] = 0.25 * env * (v + 0.1 * (rnd() - 0.5) * 2 * 0.6); }
    const ac = new OfflineAudioContext(1, n, sr), buf = ac.createBuffer(1, n, sr); buf.copyToChannel(x, 0);
    const fs = await trackTake(buf); viterbiF0(fs); trimEdges(fs, buf); const S = new Stats(); for (const m of fs) ingest(S, m, 'take');
    const TV = takeVibrato(S), vt = notes.filter(q => !q.straight); out.push({ take: vn, n: TV.n, long: TV.long, rate: TV.rate, ext: TV.ext, tRate: vt.reduce((t, q) => t + q.rate, 0) / vt.length, tExt: vt.reduce((t, q) => t + q.ext, 0) / vt.length, nv: vt.length });
    const snaps = S.rec.snaps, fr = S.rec.frames;
    notes.forEach((q, k) => { const t0 = k * (nd + gap) + 0.9, t1 = k * (nd + gap) + 1.9, R = [], E = []; let tot = 0;
      for (let i = 0; i < fr.length; i++) { if (fr[i].t < t0 || fr[i].t > t1) continue; tot++; if (snaps[i].vibRate) { R.push(snaps[i].vibRate); E.push(snaps[i].vibExt); } }
      const med = a => a.length ? a.sort((x, y) => x - y)[a.length >> 1] : 0;
      const m = []; for (let i = 0; i < fr.length; i++) if (fr[i].t >= k * (nd + gap) + 0.2 && fr[i].t <= k * (nd + gap) + 1.8 && fr[i].f0 > 0) m.push(69 + 12 * Math.log2(fr[i].f0 / 440)); const P = m.length > 40 ? vibPiece(m, 0) : {};
      out.push({ vn, straight: q.straight, rate: q.rate, ext: q.ext, sag: !!q.sag, det: R.length > tot / 2, eR: med(R), eE: med(E), jr: q.jr, je: q.je, rcv: P.rateCV, ecv: P.extCV }); });
  }
  for (const id of ['f2_vibrato', 'f2_straight', 'f2_caro_vibrato', 'f2_caro_straight', 'm2_vibrato', 'm2_straight', 'm2_caro_vibrato', 'm2_caro_straight']) {
    const ab = await (await fetch(`demo/${id}.mp3`)).arrayBuffer(), buf = await new OfflineAudioContext(1, 1, 44100).decodeAudioData(ab);
    const fs = await trackTake(buf); viterbiF0(fs); trimEdges(fs, buf); const S = new Stats(); for (const m of fs) ingest(S, m, 'take'); out.push({ real: id, ...takeVibrato(S) }); }
  return out;
}, [N, SEED]);
const takes = rows.filter(r => r.take), reals = rows.filter(r => r.real); rows.splice(0, rows.length, ...rows.filter(r => !r.take && !r.real));
await b.close();
const ms = v => { const m = v.reduce((s, x) => s + x, 0) / v.length, sd = Math.sqrt(v.reduce((s, x) => s + (x - m) ** 2, 0) / Math.max(1, v.length - 1)); return [m, 1.96 * sd / Math.sqrt(v.length)]; };
const pc = a => { const [m, e] = ms(a.map(x => +x)); return `${(100 * m).toFixed(1)} ± ${(100 * e).toFixed(1)} %`; };
const q = (a, f) => { const s = [...a].sort((x, y) => x - y); return s[Math.min(s.length - 1, Math.floor(f * s.length))]; };
const vib = rows.filter(r => !r.straight), st = rows.filter(r => r.straight), big = vib.filter(r => r.ext >= 0.3), small = vib.filter(r => r.ext < 0.3);
console.log(`vibrato notes ${vib.length}: detected ${pc(vib.map(r => r.det))}; extent ≥ 0.3 st ${pc(big.map(r => r.det))} (n=${big.length}); < 0.3 st ${pc(small.map(r => r.det))} (n=${small.length})`);
for (const g of [false, true]) { const a = vib.filter(r => r.sag === g && r.ext >= 0.3 && r.det); console.log(`  ${g ? 'sliding 0.6 st over the note' : 'level note'}: detected ${pc(vib.filter(r => r.sag === g).map(r => r.det))}, rate med err ${q(a.map(r => Math.abs(r.eR - r.rate)), 0.5).toFixed(2)} Hz p90 ${q(a.map(r => Math.abs(r.eR - r.rate)), 0.9).toFixed(2)}, extent ratio ${ms(a.map(r => r.eE / r.ext - 1)).map(x => (100 * x).toFixed(0)).join(' ± ')} %`); }
console.log(`straight notes ${st.length} (${st.filter(r=>r.sag).length} sliding): vibrato reported ${pc(st.map(r => r.det))}, sliding ${pc(st.filter(r=>r.sag).map(r=>r.det))}`);
console.log(`straight notes ${st.length}: vibrato reported ${pc(st.map(r => r.det))}`);
const d = big.filter(r => r.det), rE = d.map(r => Math.abs(r.eR - r.rate)), eE = d.map(r => Math.abs(r.eE - r.ext)), eRel = d.map(r => r.eE / r.ext - 1);
console.log(`detected, extent ≥ 0.3 st (n=${d.length}): rate |error| median ${q(rE, 0.5).toFixed(2)} Hz, p90 ${q(rE, 0.9).toFixed(2)}; mean signed ${ms(d.map(r => r.eR - r.rate)).map(v => v.toFixed(2)).join(' ± ')} Hz`);
console.log(`  extent |error| median ${q(eE, 0.5).toFixed(3)} st, p90 ${q(eE, 0.9).toFixed(3)}; ratio est/true - 1 mean ${ms(eRel).map(v => (100 * v).toFixed(1)).join(' ± ')} %`);
for (const v of ['bass', 'tenor', 'alto', 'soprano', 'child']) { const a = d.filter(r => r.vn === v); if (a.length) console.log(`  ${v}: n=${a.length} rate med ${q(a.map(r => Math.abs(r.eR - r.rate)), 0.5).toFixed(2)} Hz, extent ratio ${ms(a.map(r => r.eE / r.ext - 1)).map(x => (100 * x).toFixed(0)).join(' ± ')} %`); }
for (const t of takes) console.log(`take ${t.take}: vibrato on ${t.n} of ${t.long} long notes (truth ${t.nv}); rate ${t.rate.map(v => v.toFixed(2)).join(' ± ')} Hz (truth mean ${t.tRate.toFixed(2)}), extent ${t.ext.map(v => v.toFixed(2)).join(' ± ')} st (truth mean ${t.tExt.toFixed(2)})`);
for (const t of reals) console.log(`VocalSet ${t.real}: vibrato on ${t.n} of ${t.long} long notes${t.rate ? `, ${t.rate.map(v => v === null ? '' : v.toFixed(2)).join(' ± ')} Hz, ±${t.ext.map(v => v === null ? '' : v.toFixed(2)).join(' ± ')} st` : ''}`);
// Regularity: true CV of a uniform ±j jitter is j/√3 (rate) and j/√3 (extent multiplier).
for (const [key, tk, lv] of [['rcv', 'jr', [0.05, 0.15, 0.3]], ['ecv', 'je', [0, 0.2, 0.4]]]) for (const j of lv) {
  const a = rows.filter(r => !r.straight && r.ext >= 0.3 && r[tk] === j && r[key] !== undefined).map(r => 100 * r[key]);
  if (a.length) console.log(`regularity ${key === 'rcv' ? 'rate' : 'extent'} jitter ±${100 * j} % (true CV ${(100 * j / Math.sqrt(3)).toFixed(1)} %): estimated CV ${ms(a).map(v => v.toFixed(1)).join(' ± ')} % (n=${a.length}), p10-p90 ${q(a, 0.1).toFixed(1)}-${q(a, 0.9).toFixed(1)}`); }
for (const t of reals) if (t.rcv) console.log(`VocalSet ${t.real}: rate CV ${t.rcv.map(v => v === null ? '' : v.toFixed(1)).join(' ± ')} %, extent CV ${t.ecv.map(v => v === null ? '' : v.toFixed(1)).join(' ± ')} %`);
