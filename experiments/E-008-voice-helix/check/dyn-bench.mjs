// Dynamics (takeDynamics: the take path, trackTake, viterbiF0, trimEdges, ingest) in headless Chrome on VocalSet
// (Wilkins et al. 2018, CC BY 4.0, doi:10.5281/zenodo.1442513, not shipped): every singer's long tones on "a" sung
// messa di voce, straight, pp and forte. Per clip: swell (p95 - p5 of the smoothed level over the held tone, dB) and
// median level. Reported: swell per technique, messa vs straight AUC and same-singer pairs, forte - pp level per singer.
// Usage: node check/dyn-bench.mjs http://localhost:<port>/ <dir with VocalSet *_long_{messa,straight,pp,forte}_a.wav>
import { chromium } from 'playwright';
import { readdirSync, readFileSync } from 'fs';
const url = process.argv[2], dir = process.argv[3];
const files = readdirSync(dir).filter(f => /^[fm]\d+_long_(messa|straight|pp|forte)_a\.wav$/.test(f));
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()); const p = await b.newPage();
await p.route('**/vs/*', r => r.fulfill({ body: readFileSync(dir + '/' + decodeURIComponent(r.request().url().split('/vs/')[1])), contentType: 'audio/wav' }));
await p.goto(url); await p.waitForTimeout(1000);
const rows = [];
for (const f of files) rows.push(await p.evaluate(async f => {
  const ab = await (await fetch('vs/' + f)).arrayBuffer(), buf = await new OfflineAudioContext(1, 1, 44100).decodeAudioData(ab);
  const fs = await trackTake(buf); viterbiF0(fs); trimEdges(fs, buf); const S = new Stats(); for (const m of fs) ingest(S, m, 'take');
  const d = takeDynamics(S); if (!d) return { f, swell: null };
  const L = d.runs.reduce((a, r) => (r.swell > a.swell ? r : a)); return { f, swell: d.maxSwell, med: L.med, n: d.n };
}, f));
await b.close();
for (const r of rows) { const m = r.f.match(/^([fm]\d+)_long_(\w+)_a/); r.who = m[1]; r.tech = m[2]; }
const ok = rows.filter(r => r.swell !== null), q = (a, p) => a.slice().sort((x, y) => x - y)[Math.floor(p * (a.length - 1))];
const ms = a => { const m = a.reduce((s, x) => s + x, 0) / a.length, sd = Math.sqrt(a.reduce((s, x) => s + (x - m) ** 2, 0) / (a.length - 1)); return `${m.toFixed(1)} ± ${(1.96 * sd / Math.sqrt(a.length)).toFixed(1)} (median ${q(a, 0.5).toFixed(1)}, p10 ${q(a, 0.1).toFixed(1)}, p90 ${q(a, 0.9).toFixed(1)}, n ${a.length})`; };
console.log(`clips ${rows.length}, with a held tone ${ok.length}`);
for (const t of ['messa', 'straight', 'pp', 'forte']) console.log(`swell ${t}: ${ms(ok.filter(r => r.tech === t).map(r => r.swell))} dB`);
const X = ok.filter(r => r.tech === 'messa'), Y = ok.filter(r => r.tech === 'straight'); let w = 0; for (const x of X) for (const y of Y) w += x.swell > y.swell ? 1 : x.swell === y.swell ? 0.5 : 0;
let pr = 0, n = 0; for (const x of X) { const y = Y.find(r => r.who === x.who); if (!y) continue; n++; if (x.swell > y.swell) pr++; }
console.log(`messa > straight: AUC ${(w / X.length / Y.length).toFixed(3)}, pairs ${pr}/${n}`);
for (const th of [6, 8, 10, 12]) console.log(`swell >= ${th} dB: messa ${X.filter(r => r.swell >= th).length}/${X.length}, straight ${Y.filter(r => r.swell >= th).length}/${Y.length}`);
const fp = []; for (const x of ok.filter(r => r.tech === 'forte')) { const y = ok.find(r => r.tech === 'pp' && r.who === x.who); if (y) fp.push(x.med - y.med); }
console.log(`forte - pp level: ${ms(fp)} dB, louder in ${fp.filter(v => v > 0).length}/${fp.length}`);
