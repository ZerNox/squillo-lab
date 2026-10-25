// Pitch tracker for takes, measured with the page's own code (trackTake, viterbiF0) in headless Chrome.
// Synthetic phrases with known f0 over voice types (bass 82-165 Hz, tenor, alto, soprano 262-880 Hz,
// child 250-700 Hz) and conditions: clean; breathy (noise at -12 dB of the voice); weak fundamental
// (belt-like, H1 -20 dB); heavy vibrato (±100 ¢ at 6.5 Hz); jittery untrained (±40 ¢ drift, 2 % jitter).
// Frames: voiced in truth and analysed. Gross error: more than 50 ¢ from truth; octave: within 50 ¢ of
// 2x or 0.5x. Before = the live tracker's pitch; after = Viterbi over the whole take.
// Usage: node check/pitch-bench.mjs http://localhost:<port>/ [phrases per cell, default 4] [seed]
import { chromium } from 'playwright';
const url = process.argv[2], N = +(process.argv[3] || 4), SEED = +(process.argv[4] || 11);
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()); const p = await b.newPage(); await p.goto(url); await p.waitForTimeout(1000);
const r = await p.evaluate(async ([N, SEED]) => {
  let seed = SEED; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const voices = { bass: [82, 165], tenor: [130, 330], alto: [175, 525], soprano: [262, 880], child: [250, 700] };
  const conds = ['clean', 'breathy', 'weakH1', 'vibrato', 'untrained'];
  const res = {};
  for (const [vn, [lo, hi]] of Object.entries(voices)) for (const cn of conds) {
    const acc = { n: 0, gB: 0, gA: 0, oB: 0, oA: 0, uB: 0, uA: 0, fv: 0, fvA: 0, fvB: 0, cB: [], cA: [] };
    for (let t = 0; t < N; t++) {
      const sr = 48000, K = 8, nd = 0.5 + 0.6 * rnd(), gap = 0.2, n = Math.round(sr * K * (nd + gap)), x = new Float32Array(n), tf = new Float32Array(Math.ceil(n / 240));
      const notes = Array.from({ length: K }, () => lo * Math.pow(hi / lo, rnd()));
      const vr = cn === 'vibrato' ? 1 : 0.25, vf = 5 + 2 * rnd();
      let ph = 0, jit = 0, drift = 0;
      for (let i = 0; i < n; i++) { const s = i / sr, k = Math.floor(s / (nd + gap)), u = s - k * (nd + gap);
        if (u > nd) { ph = 0; if (i % 240 === 0) tf[i / 240] = 0; x[i] = 0.002 * (rnd() - 0.5); continue; }
        if (i % 240 === 0) { jit = (cn === 'untrained' ? 0.02 : 0.003) * (rnd() - 0.5); if (cn === 'untrained') drift = 0.98 * drift + 0.02 * 2 * (rnd() - 0.5) * 40; }
        const f = notes[k] * Math.pow(2, (vr * Math.sin(2 * Math.PI * vf * s) + drift / 100) / 12) * (1 + jit);
        if (i % 240 === 0) tf[i / 240] = f;
        ph += 2 * Math.PI * f / sr; const env = Math.min(1, u / 0.04, (nd - u) / 0.04);
        let v = 0; for (let h = 1; h * f < 8000; h++) v += (cn === 'weakH1' && h === 1 ? 0.1 : 1) * Math.sin(h * ph) / Math.pow(h, cn === 'breathy' ? 1.4 : 1);
        const nz = cn === 'breathy' ? 0.25 * (rnd() - 0.5) * 2 * 0.6 : 0.004 * (rnd() - 0.5);
        x[i] = env * (0.2 * v + nz); }
      const buf = mkBuf(n, sr); buf.getChannelData(0).set(x);
      const fs = await trackTake(buf); const before = fs.map(m => ({ v: m.voiced, f: m.f0 })); viterbiF0(fs);
      fs.forEach((m, i) => { const tc = m.t + 0.0025 - (Math.min(Math.floor(sr / 60), 4096 - 1024) + 512) / sr, j = Math.round(tc * sr / 240); const T = j >= 0 && j < tf.length ? tf[j] : 0;
        // skip frames within 40 ms of a note edge (the truth there is ambiguous)
        const ok = j - 8 >= 0 && j + 8 < tf.length && tf[j - 8] > 0 && tf[j + 8] > 0;
        if (T > 0 && ok) { acc.n++; for (const [v, f, g, o, u, c] of [[before[i].v, before[i].f, 'gB', 'oB', 'uB', acc.cB], [m.voiced, m.f0, 'gA', 'oA', 'uA', acc.cA]]) {
            if (!v) { acc[u]++; continue; } const ce = 1200 * Math.log2(f / T); if (Math.abs(ce) > 50) { acc[g]++; if (Math.abs(Math.abs(ce) - 1200) < 50) acc[o]++; } else c.push(Math.abs(ce)); } }
        else if (T === 0 && j >= 0 && j < tf.length && (j - 8 < 0 || tf[j - 8] === 0) && (j + 8 >= tf.length || tf[j + 8] === 0)) { acc.fv++; if (before[i].v) acc.fvB++; if (m.voiced) acc.fvA++; } });
    }
    const med = a => { a.sort((x, y) => x - y); return a.length ? a[a.length >> 1] : 0; };
    res[vn + '/' + cn] = { n: acc.n, grossB: acc.gB / acc.n, grossA: acc.gA / acc.n, octB: acc.oB / acc.n, octA: acc.oA / acc.n, missB: acc.uB / acc.n, missA: acc.uA / acc.n, faB: acc.fvB / Math.max(1, acc.fv), faA: acc.fvA / Math.max(1, acc.fv), medB: med(acc.cB), medA: med(acc.cA) };
  }
  return res;
}, [N, SEED]);
await b.close();
const pc = v => (100 * v).toFixed(1).padStart(5);
console.log('cell                 frames  gross% before→after  octave%  missed-voiced%  false-voiced%  median¢');
let T = { n: 0, gB: 0, gA: 0, oB: 0, oA: 0, mB: 0, mA: 0 };
for (const [k, v] of Object.entries(r)) { console.log(k.padEnd(20), String(v.n).padStart(6), pc(v.grossB), '→', pc(v.grossA), '  ', pc(v.octB), '→', pc(v.octA), '  ', pc(v.missB), '→', pc(v.missA), '  ', pc(v.faB), '→', pc(v.faA), '  ', v.medB.toFixed(1), '→', v.medA.toFixed(1));
  T.n += v.n; T.gB += v.grossB * v.n; T.gA += v.grossA * v.n; T.oB += v.octB * v.n; T.oA += v.octA * v.n; T.mB += v.missB * v.n; T.mA += v.missA * v.n; }
console.log('ALL frames', T.n, 'gross', pc(T.gB / T.n), '→', pc(T.gA / T.n), 'octave', pc(T.oB / T.n), '→', pc(T.oA / T.n), 'missed', pc(T.mB / T.n), '→', pc(T.mA / T.n));
console.log('RPA (voiced, within 50 ¢)', pc(1 - (T.gB + T.mB) / T.n), '→', pc(1 - (T.gA + T.mA) / T.n));
