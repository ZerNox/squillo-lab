// Long notes across days (laneDays, the page's own code) in headless Chrome. A pool of live wobble readings (laneSteady on the
// worker's frames) from synthetic held notes at wobble SD 4, 8 and 16 ¢ over five voices; then days of 3-12 notes drawn from the pools:
// today and earlier days at the same wobble (any 'steadier'/'less steady' is false) and today at half the earlier wobble (claim is right).
// Starts and endings: notes that slide in from and fall away by 0, 40 or 80 ¢ (laneStart, laneEnd read 0.3 s after the stop), same day pairs.
// Swell: notes swelling 0, 8 or 16 dB (laneSwell), same day pairs, higher counts as better.
// Vibrato: rate 5.0/5.8 Hz, width 0.25/0.5 st, 5 % cycle jitter (laneVib), same day pairs; described, never better.
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
  const note2 = async (m, D) => { const dur = 1.2 + R(), start = 0.3, n = Math.round(sr * (start + dur + 0.6)), buf = mkBuf(n, sr), x = buf.getChannelData(0); let ph = 0, w = 0, w2 = 0; const a = Math.exp(-2 * Math.PI * 8 / sr);
    for (let i = 0; i < n; i++) { const s = i / sr; w = a * w + (1 - a) * (R() * 2 - 1); w2 = a * w2 + (1 - a) * w; if (s < start || s > start + dur) { x[i] = 0.002 * (R() * 2 - 1); continue; } const u = s - start;
      const mid = m - D / 100 * (Math.max(0, 1 - u / 0.12) ** 2 + Math.max(0, 1 - (dur - u) / 0.2) ** 2) + w2 * 4 / 100 * 160; ph += 2 * Math.PI * 440 * 2 ** ((mid - 69) / 12) / sr;
      let v = 0; for (let h = 1; h <= 8; h++) v += Math.sin(h * ph) / (h * h); x[i] = 0.2 * Math.min(1, u / 0.03, (dur - u) / 0.03) * (v + 0.02 * (R() * 2 - 1)); }
    const fs = await trackTake(buf), st = new Stats(); for (const f of fs) ingest(st, f, 'take'); const fr = st.rec.frames, z = start + dur, h = fr.filter(f => f.t <= z + 0.3);
    const g = laneStart(h, z + 0.3), e = laneEnd(h, z + 0.3); return { st: g ? Math.round(Math.abs(g.c)) : null, en: e ? Math.round(Math.abs(e.c)) : null }; };
  const P2 = {}; for (const D of [0, 40, 80]) { P2[D] = []; for (const m of [45, 52, 60, 69, 76]) for (let r = 0; r < 8; r++) P2[D].push(await note2(m, D)); }
  const run2 = (k, dt, de) => { const out = { said: 0, right: 0, wrong: 0, n: 0 }; const dr = (D, n, d) => { const q = P2[D].filter(r => r[k] != null); return Array.from({ length: n }, () => ({ d, [k]: q[Math.floor(R() * q.length)][k] })); };
    for (let j = 0; j < 400; j++) { const L = [...dr(de, 3 + Math.floor(R() * 20), now - (1 + Math.floor(R() * 12)) * 864e5), ...dr(dt, 3 + Math.floor(R() * 10), now - 3600e3)], D = laneDays(L, now, k); out.n++;
      if (D.v && !/level/.test(D.v)) { out.said++; if (D.good === (dt < de)) out.right++; else out.wrong++; } } return out; };
  const se = {}; for (const k of ['st', 'en']) { for (const D of [0, 40, 80]) { const v = P2[D].map(r => r[k]).filter(x => x != null).sort((x, y) => x - y); se[`${k} ${D} ¢ read ${v.length}/40, median`] = v[v.length >> 1]; }
    for (const [a, c] of [[0, 0], [40, 40], [80, 80], [0, 40], [40, 80], [0, 80], [80, 40]]) se[`${k} today ${a} vs earlier ${c}`] = run2(k, a, c); }
  // Swell: notes that rise and fall by 0, 8 or 16 dB peaking mid-note (laneSwell, 0.3 s after the stop); higher counts as better.
  const note3 = async (m, G) => { const dur = 1.2 + R(), start = 0.3, n = Math.round(sr * (start + dur + 0.6)), buf = mkBuf(n, sr), x = buf.getChannelData(0); let ph = 0, w = 0, w2 = 0; const a = Math.exp(-2 * Math.PI * 8 / sr);
    for (let i = 0; i < n; i++) { const s = i / sr; w = a * w + (1 - a) * (R() * 2 - 1); w2 = a * w2 + (1 - a) * w; if (s < start || s > start + dur) { x[i] = 0.002 * (R() * 2 - 1); continue; } const u = s - start;
      const mid = m + w2 * 4 / 100 * 160; ph += 2 * Math.PI * 440 * 2 ** ((mid - 69) / 12) / sr; let v = 0; for (let h = 1; h <= 8; h++) v += Math.sin(h * ph) / (h * h);
      x[i] = 0.2 * 10 ** (-G * (1 - Math.sin(Math.PI * u / dur)) / 20) * Math.min(1, u / 0.03, (dur - u) / 0.03) * (v + 0.02 * (R() * 2 - 1)); }
    const fs = await trackTake(buf), st = new Stats(); for (const f of fs) ingest(st, f, 'take'); const fr = st.rec.frames, z = start + dur, e = laneSwell(fr.filter(f => f.t <= z + 0.3), z + 0.3); return e ? +e.w.toFixed(1) : null; };
  const P3 = {}; for (const G of [0, 8, 16]) { P3[G] = []; for (const m of [45, 52, 60, 69, 76]) for (let r = 0; r < 8; r++) { const q = await note3(m, G); if (q != null) P3[G].push(q); } }
  for (const G of [0, 8, 16]) { const v = P3[G].slice().sort((x, y) => x - y); se[`sw ${G} dB read ${v.length}/40, median`] = v[v.length >> 1]; }
  for (const [a, c] of [[0, 0], [8, 8], [16, 16], [8, 0], [16, 8], [16, 0], [0, 8]]) { const out = { said: 0, right: 0, wrong: 0, n: 0 }, dr = (G, n, d) => Array.from({ length: n }, () => ({ d, sw: P3[G][Math.floor(R() * P3[G].length)] }));
    for (let j = 0; j < 400; j++) { const D = laneDays([...dr(c, 3 + Math.floor(R() * 20), now - (1 + Math.floor(R() * 12)) * 864e5), ...dr(a, 3 + Math.floor(R() * 10), now - 3600e3)], now, 'sw'); out.n++;
      if (D.v && !/level/.test(D.v)) { out.said++; if (D.good === (a > c)) out.right++; else out.wrong++; } } se[`sw today ${a} vs earlier ${c} dB`] = out; }
  // Vibrato: notes at rate 5.0/5.8 Hz and width 0.25/0.5 st (sine extent), rate and extent jittered 5 % per cycle (laneVib, 0.3 s after the stop); described, not rated.
  const note4 = async (m, rt, ex) => { const dur = 1.6 + R(), start = 0.3, n = Math.round(sr * (start + dur + 0.6)), buf = mkBuf(n, sr), x = buf.getChannelData(0); let ph = 0, vp = 0, rr = rt, ee = ex, lastc = 0;
    for (let i = 0; i < n; i++) { const s = i / sr; if (s < start || s > start + dur) { x[i] = 0.002 * (R() * 2 - 1); continue; } const u = s - start; vp += 2 * Math.PI * rr / sr; const c = Math.floor(vp / (2 * Math.PI)); if (c !== lastc) { lastc = c; rr = rt * (1 + 0.05 * (R() * 2 - 1)); ee = ex * (1 + 0.05 * (R() * 2 - 1)); }
      const mid = m + ee * Math.sin(vp) * Math.min(1, u / 0.3); ph += 2 * Math.PI * 440 * 2 ** ((mid - 69) / 12) / sr; let v = 0; for (let h = 1; h <= 8; h++) v += Math.sin(h * ph) / (h * h); x[i] = 0.2 * Math.min(1, u / 0.03, (dur - u) / 0.03) * (v + 0.02 * (R() * 2 - 1)); }
    const fs = await trackTake(buf), st = new Stats(); for (const f of fs) ingest(st, f, 'take'); const fr = st.rec.frames, z = start + dur, e = laneVib(fr.filter(f => f.t <= z + 0.3), z + 0.3); return e && e.rate ? { vr: e.rate, vx: e.ext } : null; };
  const P4 = {}; for (const [rt, ex] of [[5, 0.25], [5.8, 0.25], [5, 0.5]]) { const kk = rt + '/' + ex; P4[kk] = []; for (const m of [45, 52, 60, 69, 76]) for (let r = 0; r < 8; r++) { const q = await note4(m, rt, ex); if (q) P4[kk].push(q); } }
  for (const kk in P4) { const v = P4[kk], md = a => a.slice().sort((x, y) => x - y)[a.length >> 1]; se[`vib ${kk} read ${v.length}/40, median rate ${md(v.map(q => q.vr)).toFixed(2)} Hz, width ${md(v.map(q => q.vx)).toFixed(3)} st`] = ''; }
  for (const [k, a, c] of [['vr', '5/0.25', '5/0.25'], ['vr', '5.8/0.25', '5/0.25'], ['vr', '5/0.25', '5.8/0.25'], ['vx', '5/0.25', '5/0.25'], ['vx', '5/0.5', '5/0.25'], ['vx', '5/0.25', '5/0.5'], ['vx', '5.8/0.25', '5/0.25'], ['vr', '5/0.5', '5/0.25']]) {
    const out = { said: 0, right: 0, wrong: 0, n: 0 }, dr = (G, n, d) => Array.from({ length: n }, () => ({ d, [k]: P4[G][Math.floor(R() * P4[G].length)][k] })), hi = (G) => k === 'vr' ? +G.split('/')[0] : +G.split('/')[1];
    for (let j = 0; j < 400; j++) { const D = laneDays([...dr(c, 3 + Math.floor(R() * 20), now - (1 + Math.floor(R() * 12)) * 864e5), ...dr(a, 3 + Math.floor(R() * 10), now - 3600e3)], now, k); out.n++;
      if (D.v && !/level/.test(D.v)) { out.said++; if (/faster|wider/.test(D.v) === (hi(a) > hi(c))) out.right++; else out.wrong++; } } se[`${k} today ${a} vs earlier ${c}`] = out; }
  const pm = {}; for (const k in pool) { const s = pool[k].slice().sort((x, y) => x - y); pm[k] = [s.length, s[s.length >> 1], s[0], s[s.length - 1]]; }
  // Warm-up (warmLane): notes carrying wobble, start and ending together; earlier days' notes at wobble 8 ¢ and 40 ¢ slides; the newest day level (any step is false),
  // starts and endings drawn independently; then wobble 16 ¢ (step 'wob' right), then 80 ¢ endings (step 'en' right). Newest day yesterday, warm-up today.
  const pk = a => a[Math.floor(R() * a.length)], wn = (w, D, n, d, De = D) => Array.from({ length: n }, () => ({ d, wob: pk(pool[w]), st: pk(P2[D]).st, en: pk(P2[De]).en }));
  const wrun = (wt, dt, want, et = dt) => { const o = { n: 0, step: 0, right: 0 }; for (let j = 0; j < 400; j++) { const L = [...wn(8, 40, 3 + Math.floor(R() * 20), now - (2 + Math.floor(R() * 11)) * 864e5), ...wn(wt, dt, 3 + Math.floor(R() * 10), now - 864e5 - 3600e3, et)], g = warmLane(L, now); o.n++; if (g) { o.step++; if (g.k === want) o.right++; } } return o; };
  // By note (laneByNote): 2-5 note names, 3-12 notes each over 14 days, all at wobble 8 ¢ (any name is false), then one note at 16 ¢ (least steady right) or 4 ¢ (steadiest right).
  const NN = ['A3', 'C4', 'E4', 'G4', 'B4'], brun = (odd) => { const o = { n: 0, said: 0, right: 0, wrong: 0 }; for (let j = 0; j < 400; j++) { const k = 2 + Math.floor(R() * 4), L = [];
      for (let i = 0; i < k; i++) { const w = i === 0 && odd ? odd : 8; for (let r = 3 + Math.floor(R() * 10); r--;) L.push({ d: now - Math.floor(R() * 13) * 864e5 - 3600e3, n: NN[i], wob: pk(pool[w]) }); }
      const q = laneByNote(L, now); o.n++; const want = odd ? (odd < 8 ? 'lo' : 'hi') : ''; for (const s of ['lo', 'hi']) if (q[s]) { o.said++; if (s === want && q[s] === 'A3') o.right++; else o.wrong++; } } return o; };
  // By vowel: same test keyed on the vowel; 2-5 vowels, each note's label wrong 12 % of the time (the 87.6 % whole-note rate), wrong label drawn from the others.
  const VV = [...'aeiou'], vrun = (odd) => { const o = { n: 0, said: 0, right: 0, wrong: 0 }; for (let j = 0; j < 400; j++) { const k = 2 + Math.floor(R() * 4), L = [];
      for (let i = 0; i < k; i++) { const w = i === 0 && odd ? odd : 8; for (let r = 3 + Math.floor(R() * 10); r--;) { let v = i; if (R() < 0.124) v = (i + 1 + Math.floor(R() * (k - 1))) % k; L.push({ d: now - Math.floor(R() * 13) * 864e5 - 3600e3, n: 'A3', vow: VV[v], wob: pk(pool[w]) }); } }
      const q = laneByNote(L, now, 'vow'); o.n++; const want = odd ? (odd < 8 ? 'lo' : 'hi') : ''; for (const s of ['lo', 'hi']) if (q[s]) { o.said++; if (s === want && q[s] === 'a') o.right++; else o.wrong++; } } return o; };
  se['by vowel all 8 ¢'] = vrun(0); se['by vowel one at 16 ¢'] = vrun(16); se['by vowel one at 4 ¢'] = vrun(4);
  se['by note all 8 ¢'] = brun(0); se['by note one at 16 ¢'] = brun(16); se['by note one at 4 ¢'] = brun(4);
  se['warm-up level'] = wrun(8, 40, null); se['warm-up wobble doubled'] = wrun(16, 40, 'wob'); se['warm-up endings 80 vs 40'] = wrun(8, 40, 'en', 80);
  return { pm, same4: run(4, 4), same8: run(8, 8), same16: run(16, 16), half: run(8, 16), half2: run(4, 8), worse: run(16, 8), se }; });
for (const [k, v] of Object.entries(res.pm)) console.log(`wobble SD ${k} ¢: ${v[0]} notes read, live wob median ${v[1].toFixed(1)} [${v[2].toFixed(1)}-${v[3].toFixed(1)}] ¢`);
for (const k of ['same4', 'same8', 'same16', 'half', 'half2', 'worse']) { const r = res[k]; console.log(`${k}: change said ${r.said}/${r.n} (right way ${r.right}, wrong way ${r.wrong})`); }
for (const [k, v] of Object.entries(res.se)) console.log(k + ': ' + (typeof v === 'object' && v ? (v.step != null ? `step added ${v.step}/${v.n} (right aspect ${v.right})` : `change said ${v.said}/${v.n} (right way ${v.right}, wrong way ${v.wrong})`) : v));
await b.close();
