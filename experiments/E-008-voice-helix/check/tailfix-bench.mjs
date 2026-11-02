// Held ending, heard: does the "spotless" render (improveTake, amount 1) remove a note-ending sag? Synthetic 16-note takes over five
// voices (as tail-bench.mjs), each note falling or rising by a known amount over its last 0.2 s; the render is re-tracked by the page's
// take path and takeTail read on it. Usage: node check/tailfix-bench.mjs http://localhost:<port>/ [melodies per cell, default 2]
import { chromium } from 'playwright';
const [url] = process.argv.slice(2), N = +(process.argv[3] ?? 2), MOVES = [-80, -40, 0, 40];
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()); const p = await b.newPage();
await p.goto(url); await p.waitForTimeout(1000);
const rows = await p.evaluate(async ([N, MOVES]) => {
  let seed = 11; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647, gau = () => Math.sqrt(-2 * Math.log(rnd() + 1e-12)) * Math.cos(2 * Math.PI * rnd());
  const voices = { bass: 43, tenor: 52, alto: 58, soprano: 65, child: 62 }, scale = [0, 2, 4, 5, 7, 9, 11, 12], out = [];
  const read = async buf => { const F = await trackTake(buf); viterbiF0(F); trimEdges(F, buf); const S = new Stats(); for (const m of F) ingest(S, m, 'take'); return S; };
  for (const [vn, base] of Object.entries(voices)) for (const D of MOVES) for (let r = 0; r < N; r++) {
    const sr = 48000, K = 16, durs = Array.from({ length: K }, () => 0.6 + 0.8 * rnd()), gap = 0.15, tot = durs.reduce((s, d) => s + d + gap, 0), n = Math.round(sr * tot), x = new Float32Array(n);
    const vib = rnd() < 0.5, notes = durs.map(() => base + scale[Math.floor(rnd() * 8)] + 0.12 * gau()), mv = durs.map(() => (D + 10 * gau()) / 100);
    let i0 = 0, ph = 0; for (let k = 0; k < K; k++) { const len = Math.round(durs[k] * sr);
      for (let i = 0; i < len; i++) { const s = (i0 + i) / sr, u = i / sr, rel = Math.max(0, (u - (durs[k] - 0.2)) / 0.2), m = notes[k] + mv[k] * rel + (vib ? 0.5 * Math.sin(2 * Math.PI * 5.5 * s) : 0), f = 440 * Math.pow(2, (m - 69) / 12);
        ph += 2 * Math.PI * f / sr; const env = Math.min(1, u / 0.04, (durs[k] - u) / 0.03) * (1 - 0.5 * rel); let v = 0; for (let h = 1; h * f < 8000; h++) v += Math.sin(h * ph) / h; x[i0 + i] = env * (0.2 * v + 0.004 * (rnd() - 0.5)); }
      i0 += len + Math.round(gap * sr); ph = 0; }
    const buf = mkBuf(n, sr); buf.getChannelData(0).set(x); const S = await read(buf), t = takeTail(S.rec.frames);
    const sc = await scanTake(buf), sp = improveTake(buf, sc.frames, 1, sc.aspects.off), t2 = takeTail((await read(sp)).rec.frames), w = t && t.worst;
    out.push({ vn, D, vib, before: t ? t.cents : null, after: t2 ? t2.cents : null, w: w ? w.c : null }); }
  return out; }, [N, MOVES]);
const ms = a => { const m = a.reduce((s, x) => s + x, 0) / a.length; return [m, Math.sqrt(a.reduce((s, x) => s + (x - m) ** 2, 0) / Math.max(1, a.length - 1))]; };
for (const D of MOVES) { const a = rows.filter(r => r.D === D && r.before !== null && r.after !== null), [bm] = ms(a.map(r => r.before)), [am, as] = ms(a.map(r => r.after));
  console.log(`move ${D}: take ${bm.toFixed(1)} ¢ → spotless ${am.toFixed(1)} (SD ${as.toFixed(1)}), n ${a.length}/${rows.filter(r => r.D === D).length}; worst note picked same way ${a.filter(r => D && r.w !== null && Math.sign(r.w) === Math.sign(D)).length}`); }
await b.close();
