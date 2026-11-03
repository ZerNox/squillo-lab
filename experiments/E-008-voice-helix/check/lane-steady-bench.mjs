// Live steadiness after a note (laneSteady, the page's own code) in headless Chrome: held notes 1.2-2.2 s over five voices (110-660 Hz),
// with random pitch wobble (smoothed noise, SD 0, 4, 8, 16 ¢) and half of them with even vibrato on top; breath noise.
// Frames: the worker's YIN + ingest (as live). Read 0.2 s after the note stops. Also the take's note wobble (segNotes) on the same frames,
// and the "steadiest" claim: sequences of 5 notes at one wobble (any claim is false), and 4 at 16 ¢ then one at 4 ¢ (claim is right).
// Usage: node check/lane-steady-bench.mjs http://localhost:<port>/
import { chromium } from 'playwright';
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()), p = await b.newPage(); await p.goto(process.argv[2]); await p.waitForTimeout(1000);
const rows = await p.evaluate(async () => { const sr = 48000, out = []; let seed = 7; const R = () => (seed = seed * 16807 % 2147483647) / 2147483647;
  const note = async (m, wsd, vib) => { const dur = 1.2 + R(), start = 0.3, n = Math.round(sr * (start + dur + 0.6)), buf = mkBuf(n, sr), x = buf.getChannelData(0);
    const rate = 4.5 + R() * 2.5, ext = 0.15 + R() * 0.35; let ph = 0, vp = R() * 6, w = 0, w2 = 0; const a = Math.exp(-2 * Math.PI * 8 / sr), g = Math.sqrt((1 - a * a) * (1 - a * a)) * 2.2;
    for (let i = 0; i < n; i++) { const s = i / sr; const u1 = R() * 2 - 1; w = a * w + (1 - a) * u1; w2 = a * w2 + (1 - a) * w; if (s < start || s > start + dur) { x[i] = 0.002 * (R() * 2 - 1); continue; } const u = s - start;
      vp += 2 * Math.PI * rate / sr; const mid = m + (vib ? ext * Math.sin(vp) : 0) + w2 * wsd / 100 * 160; ph += 2 * Math.PI * 440 * 2 ** ((mid - 69) / 12) / sr;
      let v = 0; for (let h = 1; h <= 8; h++) v += Math.sin(h * ph) / (h * h); x[i] = 0.2 * Math.min(1, u / 0.03, (dur - u) / 0.03) * (v + 0.02 * (R() * 2 - 1)); }
    const fs = await trackTake(buf), st = new Stats(); for (const f of fs) ingest(st, f, 'take'); const fr = st.rec.frames, z = start + dur;
    const e = laneSteady(fr.filter(f => f.t <= z + 0.2), z + 0.2), sn = segNotes(fr).filter(q => q.t1 - q.t0 > 0.8); return { e, take: sn.length ? sn[0].wob : null }; };
  for (const m of [45, 52, 60, 69, 76]) for (const wsd of [0, 4, 8, 16]) for (const vib of [false, true]) for (let r = 0; r < 3; r++) out.push({ kind: 'one', m, wsd, vib, ...(await note(m, wsd, vib)) });
  for (const m of [45, 60, 76]) for (const wsd of [4, 8, 16]) for (let r = 0; r < 4; r++) { const prev = [], said = []; for (let j = 0; j < 5; j++) { const q = await note(m, wsd, false); if (q.e) { const T = laneSteadyText({ ...q.e, t: j * 10 }, prev); said.push(T.best); prev.push({ ...q.e, t: j * 10 }); } } out.push({ kind: 'same', said }); }
  for (const m of [45, 60, 76]) for (let r = 0; r < 6; r++) { const prev = []; let last = null; for (let j = 0; j < 5; j++) { const q = await note(m, j < 4 ? 16 : 4, false); if (q.e) { const T = laneSteadyText({ ...q.e, t: j * 10 }, prev); last = j === 4 ? T.best : last; prev.push({ ...q.e, t: j * 10 }); } } out.push({ kind: 'drop', said: last }); }
  return out; });
const one = rows.filter(r => r.kind === 'one'), f = x => x.toFixed(1);
for (const vib of [false, true]) for (const wsd of [0, 4, 8, 16]) { const a = one.filter(r => r.vib === vib && r.wsd === wsd), v = a.filter(r => r.e), w = v.map(r => r.e.wob).sort((x, y) => x - y), d = v.filter(r => r.take != null).map(r => r.e.wob - r.take);
  console.log(`${vib ? 'vibrato' : 'straight'} wobble SD ${wsd} ¢: read ${v.length}/${a.length}, live wob median ${f(w[w.length >> 1])} [${f(w[0])}-${f(w[w.length - 1])}] ¢, ± median ${f(v.map(r => r.e.pm).sort((x, y) => x - y)[v.length >> 1])}, live - take ${d.length ? f(d.reduce((s, x) => s + x, 0) / d.length) + ' (max |' + f(Math.max(...d.map(Math.abs))) + '|)' : '-'}`); }
const same = rows.filter(r => r.kind === 'same').flatMap(r => r.said.slice(1)), drop = rows.filter(r => r.kind === 'drop');
console.log(`steadiest claimed on same-wobble notes: ${same.filter(Boolean).length}/${same.length}; on a 4 ¢ note after four 16 ¢: ${drop.filter(r => r.said).length}/${drop.length}`);
await b.close();
