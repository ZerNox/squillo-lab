// Creak (VocalSet's 'vocal_fry', pitched near 250 Hz, not low pulses) against other techniques: takeCreak, the page's own code on the take path, headless Chrome.
// VocalSet (Wilkins et al. 2018, CC BY 4.0, doi:10.5281/zenodo.1442513, not shipped): *_{scales,arpeggios}_vocal_fry_{a,i,u}, and straight, breathy, belt, vibrato controls. Any other wav (vocadito) is listed as unlabelled.
// Usage: node check/fry-bench.mjs http://localhost:<port>/ <dir>
import { chromium } from 'playwright';
import { readdirSync, readFileSync } from 'fs';
const url = process.argv[2], dir = process.argv[3], files = readdirSync(dir).filter(f => f.endsWith('.wav'));
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()), p = await b.newPage();
await p.route('**/vs/*', r => r.fulfill({ body: readFileSync(dir + '/' + decodeURIComponent(r.request().url().split('/vs/')[1])), contentType: 'audio/wav' }));
await p.goto(url); await p.waitForTimeout(1000);
const rows = [];
for (const f of files) rows.push(await p.evaluate(async f => {
  const ab = await (await fetch('vs/' + f)).arrayBuffer(), buf = await new OfflineAudioContext(1, 1, 44100).decodeAudioData(ab);
  const fs = await trackTake(buf); viterbiF0(fs); trimEdges(fs, buf); const S = new Stats(); for (const m of fs) ingest(S, m, 'take');
  return { f, c: takeCreak(S.rec.frames, S.rec.snaps) };
}, f));
await b.close();
const wil = (k, n) => { const c = k / n, z = 1.96, d = 1 + z * z / n, m = (c + z * z / 2 / n) / d, e = z * Math.sqrt(c * (1 - c) / n + z * z / 4 / n / n) / d; return `${k}/${n} = ${(100 * c).toFixed(1)} % (${(100 * (m - e)).toFixed(1)}-${(100 * (m + e)).toFixed(1)})`; };
const rep = (name, a) => { const r = a.filter(x => x.c); console.log(name.padEnd(20), `read ${r.length} of ${a.length}, creak ${wil(r.filter(x => x.c.on).length, r.length || 1)}`); };
const vs = rows.filter(r => /^[fm]\d+_/.test(r.f));
rep('vocal fry', vs.filter(r => /vocal_fry/.test(r.f))); rep('controls', vs.filter(r => !/vocal_fry/.test(r.f)));
for (const k of ['straight', 'breathy', 'belt', 'vibrato']) rep('  ' + k, vs.filter(r => r.f.includes(k)));
if (vs.length < rows.length) rep('unlabelled', rows.filter(r => !vs.includes(r)));
