// Long notes across days (laneDays, the page's own code) in headless Chrome. A pool of live wobble readings (laneSteady on the
// worker's frames) from synthetic held notes at wobble SD 4, 8 and 16 ¢ over five voices; then days of 3-12 notes drawn from the pools:
// today and earlier days at the same wobble (any 'steadier'/'less steady' is false) and today at half the earlier wobble (claim is right).
// Usage: node check/lane-days-bench.mjs http://localhost:<port>/
import { chromium } from 'playwright';
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()), p = await b.newPage(); await p.goto(process.argv[2]); await p.waitForTimeout(1000);
const res = await p.evaluate(async () => { const sr = 48000; let seed = 11; const R = () => (seed = seed * 16807 % 2147483647) / 2147483647;
  const note = async (m, wsd) => { const dur = 1.2 + R(), start = 0.3, n = Math.round(sr * (start + dur + 0.6)), buf = mkBuf(n, sr), x = buf.getChannelData(0);
    let ph = 0, w = 0, w2 = 0; const a = Math.exp(-2 * Math.PI * 8 / sr);
    for (let i = 0; i < n; i++) { const s = i / sr; w = a * w + (1 - a) * (R() * 2 - 1); w2 = a * w2 + (1 - a) * w; if (s < start || s > start + dur) { x[i] = 0.002 * (R() * 2 - 1); continue; } const u = s - start;
      const mid = m + w2 * wsd / 100 * 160; ph += 2 * Math.PI * 440 * 2 ** ((mid - 69) / 12) / sr;
      let v = 0; for (let h = 1; h <= 8; h++) v += Math.sin(h * ph) / (h * h); x[i] = 0.2 * Math.min(1, u / 0.03, (dur - u) / 0.03) * (v + 0.02 * (R() * 2 - 1)); }
    const fs = await trackTake(buf), st = new Stats(); for (const f of fs) ingest(st, f, 'take'); const fr = st.rec.frames, z = start + dur;
    const e = laneSteady(fr.filter(f => f.t <= z + 0.2), z + 0.2); return e ? e.wob : null; };
  const pool = {}; for (const wsd of [4, 8, 16]) { pool[wsd] = []; for (const m of [45, 52, 60, 69, 76]) for (let r = 0; r < 8; r++) { const q = await note(m, wsd); if (q != null) pool[wsd].push(q); } }
  const now = new Date('2026-11-03T12:00').getTime(), draw = (w, n, d) => Array.from({ length: n }, () => ({ d, wob: pool[w][Math.floor(R() * pool[w].length)] }));
  const run = (wt, we) => { const out = { said: 0, right: 0, wrong: 0, n: 0 }; for (let k = 0; k < 400; k++) { const nt = 3 + Math.floor(R() * 10), ne = 3 + Math.floor(R() * 20);
      const L = [...draw(we, ne, now - (1 + Math.floor(R() * 12)) * 864e5), ...draw(wt, nt, now - 3600e3)], D = laneDays(L, now); out.n++;
      if (D.v && D.v !== 'level with') { out.said++; if ((D.v === 'steadier than') === (wt < we)) out.right++; else out.wrong++; } } return out; };
  const pm = {}; for (const k in pool) { const s = pool[k].slice().sort((x, y) => x - y); pm[k] = [s.length, s[s.length >> 1], s[0], s[s.length - 1]]; }
  return { pm, same4: run(4, 4), same8: run(8, 8), same16: run(16, 16), half: run(8, 16), half2: run(4, 8), worse: run(16, 8) }; });
for (const [k, v] of Object.entries(res.pm)) console.log(`wobble SD ${k} ¢: ${v[0]} notes read, live wob median ${v[1].toFixed(1)} [${v[2].toFixed(1)}-${v[3].toFixed(1)}] ¢`);
for (const k of ['same4', 'same8', 'same16', 'half', 'half2', 'worse']) { const r = res[k]; console.log(`${k}: change said ${r.said}/${r.n} (right way ${r.right}, wrong way ${r.wrong})`); }
await b.close();
