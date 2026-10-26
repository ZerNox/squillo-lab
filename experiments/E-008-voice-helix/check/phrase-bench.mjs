// Same-phrase matcher (samePhrase, page code) on vocadito (CC BY 4.0, see vocadito-bench.mjs). Proxy for "the same
// song sung again": the earlier take is the clip itself slowed to 0.8x by the page's WSOLA (so every time is t/0.8)
// plus noise at -30 dB; queries are the phrases around 25/50/75 % of each clip. Hit: matched start and end within
// 0.3 s of truth. Impostors: the same queries against a different clip, to set the reject threshold (SP.max).
// Usage: node check/phrase-bench.mjs http://localhost:<port>/ /path/to/vocadito
import { chromium } from 'playwright'; import fs from 'node:fs'; import path from 'node:path';
const [url, dir] = process.argv.slice(2);
const ids = fs.readFileSync(path.join(dir, 'vocadito_metadata.csv'), 'utf8').trim().split('\n').slice(1).map(l => l.split(',')[0]);
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()); const p = await b.newPage();
await p.route('**/vocadito/**', r => r.fulfill({ body: fs.readFileSync(path.join(dir, 'Audio', path.basename(new URL(r.request().url()).pathname))) }));
await p.goto(url); await p.waitForTimeout(1000);
const res = await p.evaluate(async ids => {
  const F = async b => { const fs = await trackTake(b); viterbiF0(fs); trimEdges(fs, b); return fs.map(f => ({ t: Math.max(0, f.t - 0.02), f0: f.voiced ? f.f0 : 0 })); };
  const T = {}; for (const id of ids) { const ab = await (await fetch(`vocadito/vocadito_${id}.wav`)).arrayBuffer();
    const buf = await new OfflineAudioContext(1, 1, 44100).decodeAudioData(ab); const sl = wsola(buf, 0.8), y = sl.getChannelData(0);
    let s = 0; for (const v of y) s += v * v; const a = Math.sqrt(s / y.length) * 0.0316 * Math.sqrt(3); for (let i = 0; i < y.length; i++) y[i] += a * (2 * Math.random() - 1);
    T[id] = { q: await F(buf), r: await F(sl), d: buf.duration }; }
  const out = [];
  ids.forEach((id, k) => { const o = T[id], imp = T[ids[(k + 7) % ids.length]];
    for (const f of [0.25, 0.5, 0.75]) { const ph = phraseAround(o.q, f * o.d); if (!ph || ph.t1 - ph.t0 < 1) continue;
      const m = samePhrase(o.q, ph.t0, ph.t1, o.r), x = samePhrase(o.q, ph.t0, ph.t1, imp.r);
      out.push({ id, len: ph.t1 - ph.t0, hit: !!m && Math.abs(m.t0 - ph.t0 / 0.8) < 0.3 && Math.abs(m.t1 - ph.t1 / 0.8) < 0.3, c: m ? m.cost : 9, ci: x ? x.cost : 9 }); } });
  return out; }, ids);
await b.close();
const n = res.length, ci = (k, N) => { const q = k / N, e = 1.96 * Math.sqrt(q * (1 - q) / N); return `${(100 * q).toFixed(1)} ± ${(100 * e).toFixed(1)} %`; };
console.log(`${n} phrases, mean ${(res.reduce((s, r) => s + r.len, 0) / n).toFixed(1)} s`);
for (const th of [0.2, 0.3, 0.4, 0.5, 0.7]) console.log(`max ${th}: found right ${ci(res.filter(r => r.hit && r.c < th).length, n)}, wrong place ${ci(res.filter(r => !r.hit && r.c < th).length, n)}, impostor accepted ${ci(res.filter(r => r.ci < th).length, n)}`);
