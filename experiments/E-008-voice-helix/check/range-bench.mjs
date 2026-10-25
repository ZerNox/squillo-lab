// Range finder, measured with the page's own code (rangeAnalyse: trackTake → Viterbi → heldExtremes) in headless Chrome.
// Synthetic voices, 8 harmonics, jitter and breath noise, over six voices (true lowest 41-60 MIDI, highest 17-28 st above).
// Step 1: a comfortable note, slide down over 1.5 s to the lowest, hold 1 s with 5.5 Hz vibrato (±0.2-0.6 st), then
// 0.6 s of a weak sub-pitch rattle (fry-like: 30-45 Hz pulses). Step 2: slide up to the highest, lighter tilt, hold 1 s,
// vibrato. Step 3: a siren, low to high to low, with a 2.5 st jump at a passaggio. Error: found minus true held pitch, st.
// Usage: node check/range-bench.mjs http://localhost:<port>/ [trials per voice, default 5]
import { chromium } from 'playwright';
const url = process.argv[2], N = +(process.argv[3] || 5);
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()); const p = await b.newPage(); await p.goto(url); await p.waitForTimeout(1000);
const r = await p.evaluate(async N => {
  let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647, sr = 48000;
  const render = (T, path, tilt, breath) => { const n = Math.round(sr * T), x = new Float32Array(n); let ph = 0, jit = 0;
    for (let i = 0; i < n; i++) { const s = i / sr, q = path(s); if (i % 480 === 0) jit = 0.004 * (rnd() - 0.5);
      const env = Math.min(1, s / 0.05, (T - s) / 0.05); if (q.fry) { const f = 30 + 15 * rnd(); x[i] = env * 0.2 * (((i % Math.round(sr / f)) < 40) ? 1 : 0) + breath * (rnd() - 0.5); continue; }
      ph += 2 * Math.PI * 440 * Math.pow(2, (q.m - 69) / 12) * (1 + jit) / sr; let v = 0; for (let h = 1; h <= 8; h++) v += Math.sin(h * ph) / Math.pow(h, q.t || tilt);
      x[i] = env * 0.25 * v + breath * (rnd() - 0.5); }
    const buf = mkBuf(n, sr); buf.getChannelData(0).set(x); return buf; };
  const lo = [], hi = [], br = { hit: 0, of: 0 }; let fail = 0;
  for (const L of [41, 45, 48, 52, 55, 60]) for (let t = 0; t < N; t++) {
    const H = L + 17 + 11 * rnd(), C = L + 7 + 3 * rnd(), vib = 0.2 + 0.4 * rnd(), breath = 0.005 + 0.03 * rnd(), P = L + 9 + 4 * rnd();
    const s1 = render(4, s => s < 0.4 ? { m: C } : s < 1.9 ? { m: C + (L - C) * (s - 0.4) / 1.5 } : s < 2.9 ? { m: L + vib * Math.sin(2 * Math.PI * 5.5 * (s - 1.9)) } : s < 3.5 ? { fry: 1 } : { m: L }, 1, breath);
    const s2 = render(3.6, s => s < 0.4 ? { m: C, t: 1 } : s < 2.2 ? { m: C + (H - C) * (s - 0.4) / 1.8, t: 1.6 } : { m: H + vib * Math.sin(2 * Math.PI * 5.5 * (s - 2.2)), t: 1.8 }, 1, breath);
    const sir = s => { const u = s < 3 ? L + 2 + (H - L - 4) * s / 3 : L + 2 + (H - L - 4) * Math.max(0, 1 - (s - 3) / 3); const up = s < 3; const th = up ? P : P - 1.5; return u >= th ? { m: u + 1.25, t: 1.8 } : { m: u - 1.25, t: 1 }; };
    const s3 = render(6.2, sir, 1, breath);
    localStorage.removeItem(RANGE_KEY); const res = await rangeAnalyse([s1, s2, s3]);
    if (!res) { fail++; continue; } lo.push(res.mn - L); hi.push(res.mx - H);
    br.of += 2; for (const tb of [P, P - 1.5]) if ((res.br || []).some(m => Math.abs(m - tb) <= 1.5)) br.hit++; }
  localStorage.removeItem(RANGE_KEY);
  const q = (v, f) => { const s = v.map(Math.abs).sort((a, b) => a - b); return +s[Math.min(s.length - 1, Math.floor(s.length * f))].toFixed(2); };
  const mean = v => +(v.reduce((a, b) => a + b, 0) / v.length).toFixed(2);
  return { n: lo.length, fail, lowMed: q(lo, 0.5), lowP90: q(lo, 0.9), lowBias: mean(lo), highMed: q(hi, 0.5), highP90: q(hi, 0.9), highBias: mean(hi), within1: +((lo.concat(hi).filter(e => Math.abs(e) <= 1).length) / (2 * lo.length)).toFixed(3), breaks: `${br.hit}/${br.of}` }; }, N);
await b.close(); console.log(JSON.stringify(r));
