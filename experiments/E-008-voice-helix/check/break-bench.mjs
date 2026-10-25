// Register breaks on glides, measured with the page's own code (scanTake → st frames → registerBreaks) in headless Chrome.
// Synthetic sirens, 8 harmonics, light jitter and noise, over four voices (low starts 98, 147, 220, 330 Hz), up an
// octave and a half in 3 s and back. "break": at a random passaggio (5-11 st above the start) the pitch jumps 2-4 st
// in the direction of travel (up on the way up, down on the way down, 1-2 st lower: hysteresis) and the harmonic
// tilt changes (lighter register above). "clean": the same siren with no jump. "legato": a scale of held notes with
// 5.5 Hz vibrato (±0.5 st), steps of 1-2 st. "vibrato": one sustained note, vibrato ±1 st. Hit: a break found within
// ±1.5 st of the true one, same direction. False: any break found that matches none.
// Usage: node check/break-bench.mjs http://localhost:<port>/ [trials per class and voice, default 6]
import { chromium } from 'playwright';
const url = process.argv[2], N = +(process.argv[3] || 6);
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()); const p = await b.newPage(); await p.goto(url); await p.waitForTimeout(1000);
const r = await p.evaluate(async N => {
  let seed = 11; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const res = { break: { hit: 0, of: 0, fp: 0, err: [] }, clean: { fp: 0, n: 0 }, legato: { fp: 0, n: 0 }, vibrato: { fp: 0, n: 0 } };
  for (const F of [98, 147, 220, 330]) for (const cls of ['break', 'clean', 'legato', 'vibrato']) for (let t = 0; t < N; t++) {
    const sr = 48000, T = 6.4, n = Math.round(sr * T), x = new Float32Array(n), P = 5 + 6 * rnd(), J = 2 + 2 * rnd(), H = 1 + rnd();
    const m0 = 69 + 12 * Math.log2(F / 440), deg = [0, 2, 4, 5, 7, 9, 7, 5, 4, 2, 0];
    // siren path in semitones above start: up 18 in 3 s, hold 0.2 s, down; with a jump past P (up) and past P-H (down)
    const path = s => { if (cls === 'legato') { const k = Math.min(deg.length - 1, Math.floor(s / 0.55)); return deg[k] + 0.5 * Math.sin(2 * Math.PI * 5.5 * s); }
      if (cls === 'vibrato') return 7 + Math.sin(2 * Math.PI * 5.5 * s);
      const u = s < 0.2 ? 0 : s < 3.2 ? (s - 0.2) / 3 * 18 : s < 3.4 ? 18 : Math.max(0, 18 - (s - 3.4) / 3 * 18); return u; };
    // in the "break" class the lower register runs J/2 below the path and the upper J/2 above, so the switch is a jump
    const pitch = s => { const u = path(s); if (cls !== 'break') return { m: u, hi: u > 9 }; const up = s < 3.3, th = up ? P : P - H;
      const hi = u >= th; return { m: hi ? u + J / 2 : u - J / 2, hi }; };
    let ph = 0, jit = 0, trueBr = [];
    let prevHi = null;
    for (let i = 0; i < n; i++) { const s = i / sr, q = pitch(s);
      if (cls === 'break' && prevHi !== null && q.hi !== prevHi) trueBr.push({ t: s, m: m0 + (s < 3.3 ? P : P - H), d: q.hi ? 1 : -1 }); prevHi = q.hi;
      if (i % 480 === 0) jit = 0.003 * (rnd() - 0.5);
      const f = 440 * Math.pow(2, (m0 + q.m - 69) / 12) * (1 + jit); ph += 2 * Math.PI * f / sr;
      const env = Math.min(1, s / 0.05, (T - s) / 0.05), tilt = q.hi ? 1.8 : 1;
      let v = 0; for (let h = 1; h <= 8; h++) v += Math.sin(h * ph) / Math.pow(h, tilt); x[i] = env * (0.25 * v + 0.01 * (rnd() - 0.5)); }
    const buf = mkBuf(n, sr); buf.getChannelData(0).set(x);
    const fs = await trackTake(buf); viterbiF0(fs); const st = new Stats(); for (const m of fs) ingest(st, m, 'take');
    const br = registerBreaks(st.rec.frames), used = new Set();
    if (cls === 'break') { for (const tb of trueBr) { res.break.of++; const k = br.findIndex((q, j) => !used.has(j) && Math.abs(q.m - tb.m) <= 1.5 && Math.sign(q.j) === tb.d && Math.abs(q.t - tb.t) < 0.3);
        if (k >= 0) { used.add(k); res.break.hit++; res.break.err.push(Math.abs(br[k].m - tb.m)); } } res.break.fp += br.length - used.size; }
    else { res[cls].fp += br.length; res[cls].n++; } }
  const e = res.break.err.sort((a, b) => a - b); res.break.errMed = +e[e.length >> 1].toFixed(2); res.break.errP90 = +e[Math.floor(e.length * 0.9)].toFixed(2); delete res.break.err;
  return res; }, N);
// Real voices without sirens: the 14 VocalSet clips and the two public-domain references; breaks found there are listed (some may be real).
const real = await p.evaluate(async () => { const ids = ['f2', 'm2'].flatMap(v => ['belt', 'breathy', 'caro_straight', 'caro_vibrato', 'straight', 'vibrato', 'vocal_fry'].map(k => `demo/${v}_${k}.mp3`)).concat(['ref/polished.mp3', 'ref/rough.mp3']);
  const o = []; for (const u of ids) { const q = await fetch(u); if (!q.ok) continue; const buf = await new OfflineAudioContext(1, 1, 48000).decodeAudioData(await q.arrayBuffer());
    const fs = await trackTake(buf); viterbiF0(fs); const st = new Stats(); for (const m of fs) ingest(st, m, 'take'); o.push([u, registerBreaks(st.rec.frames).length, +buf.duration.toFixed(0)]); } return o; });
await b.close();
console.log(JSON.stringify(r));
console.log('breaks found:', `${r.break.hit}/${r.break.of}`, 'false on break sirens:', r.break.fp, '| false on clean sirens:', r.clean.fp, '/', r.clean.n, 'legato:', r.legato.fp, '/', r.legato.n, 'vibrato:', r.vibrato.fp, '/', r.vibrato.n);
console.log('real clips (breaks, seconds):', JSON.stringify(real));
