// Live swell after a note (laneSwell, the page's own code) in headless Chrome: held notes 1.2-2.6 s over five voices (110-660 Hz), level
// following a raised-cosine swell of D dB (0, 4, 8, 14, 20) peaking at 25, 50 or 75 % of the note, half with vibrato; breath noise.
// Frames: the worker's YIN + ingest (as live). Read 0.2 s after the note stops. Truth: p95 - p5 of the asked level over the same span.
// Also the take's estimator (takeDynamics) on the same frames. Usage: node check/lane-swell-bench.mjs http://localhost:<port>/
import { chromium } from 'playwright';
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()), p = await b.newPage(); await p.goto(process.argv[2]); await p.waitForTimeout(1000);
const rows = await p.evaluate(async () => { const sr = 48000, out = []; let seed = 11; const R = () => (seed = seed * 16807 % 2147483647) / 2147483647;
  for (const m of [45, 52, 60, 69, 76]) for (const D of [0, 4, 8, 14, 20]) for (const at of [0.25, 0.5, 0.75]) for (const vib of [false, true]) {
    const dur = 1.2 + R() * 1.4, start = 0.3, n = Math.round(sr * (start + dur + 0.6)), buf = mkBuf(n, sr), x = buf.getChannelData(0), rate = 4.5 + R() * 2, ext = 0.2 + R() * 0.3;
    const lev = u => { const q = u / dur; const ph = q < at ? q / at * Math.PI : Math.PI + (q - at) / (1 - at) * Math.PI; return D * (1 - Math.cos(ph)) / 2; };
    let ph = 0, vp = R() * 6; for (let i = 0; i < n; i++) { const s = i / sr; if (s < start || s > start + dur) { x[i] = 0.002 * (R() * 2 - 1); continue; } const u = s - start;
      vp += 2 * Math.PI * rate / sr; ph += 2 * Math.PI * 440 * 2 ** ((m + (vib ? ext * Math.sin(vp) : 0) - 69) / 12) / sr; let v = 0; for (let h = 1; h <= 8; h++) v += Math.sin(h * ph) / (h * h);
      x[i] = 0.25 * 10 ** ((lev(u) - D) / 20) * Math.min(1, u / 0.03, (dur - u) / 0.03) * (v + 0.02 * (R() * 2 - 1)); }
    const T = []; for (let u = 0.1; u <= dur - 0.1; u += 0.01) T.push(lev(u)); T.sort((a, c) => a - c); const truth = T[Math.floor(T.length * 0.95)] - T[Math.floor(T.length * 0.05)];
    const fs = await trackTake(buf), st = new Stats(); for (const f of fs) ingest(st, f, 'take'); const z = start + dur, e = laneSwell(st.rec.frames.filter(f => f.t <= z + 0.2), z + 0.2), td = takeDynamics(st);
    out.push({ m, D, at, vib, truth, e, txt: laneSwellText(e), take: td && td.runs.length ? td.runs[0].swell : null }); }
  return out; });
const f = x => x.toFixed(1);
for (const D of [0, 4, 8, 14, 20]) { const a = rows.filter(r => r.D === D), v = a.filter(r => r.e), err = v.map(r => r.e.w - r.truth), ins = v.filter(r => Math.abs(r.e.w - r.truth) <= r.e.pm).length, d = v.filter(r => r.take != null).map(r => r.e.w - r.take);
  const pk = D >= 8 ? v.filter(r => (r.e.at < 0.3 ? 0.25 : r.e.at > 0.7 ? 0.75 : 0.5) === r.at).length + '/' + v.length : '-';
  console.log(`D ${D} dB: read ${v.length}/${a.length}, error mean ${f(err.reduce((s, x) => s + x, 0) / err.length)} max |${f(Math.max(...err.map(Math.abs)))}| dB, truth inside ± ${ins}/${v.length}, peak place right ${pk}, live - take ${f(d.reduce((s, x) => s + x, 0) / d.length)} dB, 'level' ${v.filter(r => r.txt.s.startsWith('held level')).length}, 'messa di voce' ${v.filter(r => r.txt.real).length}`); }
await b.close();
