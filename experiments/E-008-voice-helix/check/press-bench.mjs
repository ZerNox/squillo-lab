// Pressed voice (belt as the labelled proxy) and breathiness, measured with the page's own code (trackTake, viterbiF0, trimEdges, ingest: the take path) in
// headless Chrome on VocalSet (Wilkins et al. 2018, CC BY 4.0, doi:10.5281/zenodo.1442513, not shipped): every
// singer's scales sung "breathy" and "straight" on five vowels (same singer, scale and vowel; only the technique
// changes). Per clip: median over voiced frames of CPP (cepstral peak prominence, dB), the CMND-based HNR, and the
// share of voiced frames the page's 'breathy' cue fires on. Reported: AUC (breathy vs straight over all clips),
// and the within-singer-and-vowel pair accuracy (breathy reads lower than straight).
// Usage: node check/breath-bench.mjs http://localhost:<port>/ <dir with VocalSet *_scales_{breathy,straight}_<v>.wav>
import { chromium } from 'playwright';
import { readdirSync, readFileSync } from 'fs';
const url = process.argv[2], dir = process.argv[3];
const files = readdirSync(dir).filter(f => /^[fm]\d+_scales_(belt|breathy|straight)_[aeiou]\.wav$/.test(f));
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()); const p = await b.newPage();
await p.route('**/vs/*', r => r.fulfill({ body: readFileSync(dir + '/' + decodeURIComponent(r.request().url().split('/vs/')[1])), contentType: 'audio/wav' }));
await p.goto(url); await p.waitForTimeout(1000);
const rows = [];
for (const f of files) {
  rows.push(await p.evaluate(async f => {
    const ab = await (await fetch('vs/' + f)).arrayBuffer(), buf = await new OfflineAudioContext(1, 1, 44100).decodeAudioData(ab);
    const fs = await trackTake(buf); viterbiF0(fs); trimEdges(fs, buf); const S = new Stats(); for (const m of fs) ingest(S, m, 'take');
    const sn = S.rec.snaps, fr = S.rec.frames, K = ['cpp', 'hnr', 'h12', 'tilt'], v = Object.fromEntries(K.map(k => [k, []])), pi = FLAWS.findIndex(x => x.id === 'pressed'); let pr = 0, nv = 0;
    for (let i = 0; i < fr.length; i++) { if (!fr[i].voiced) continue; nv++; for (const k of K) v[k].push(sn[i][k]); if (FLAWS[pi].test(sn[i])) pr++; }
    const med = a => a.sort((x, y) => x - y)[a.length >> 1] || 0;
    return { f, ...Object.fromEntries(K.map(k => [k, med(v[k])])), cue: nv ? pr / nv : 0, nv };
  }, f));
}
await b.close();
for (const r of rows) { const m = r.f.match(/^([fm]\d+)_scales_(\w+)_([aeiou])/); r.who = m[1]; r.tech = m[2]; r.v = m[3]; }
// a = the class expected to read higher on k (sign 1), b the other; AUC and same-singer-vowel pairs.
const cmp = (A, B, k) => { const X = rows.filter(r => r.tech === A), Y = rows.filter(r => r.tech === B); let w = 0; for (const x of X) for (const y of Y) w += x[k] > y[k] ? 1 : x[k] === y[k] ? 0.5 : 0;
  let ok = 0, n = 0; for (const x of X) { const y = Y.find(r => r.who === x.who && r.v === x.v); if (!y) continue; n++; if (x[k] > y[k]) ok++; } const pr = ok / n;
  return `AUC ${(w / X.length / Y.length).toFixed(3)}, pairs ${(100 * pr).toFixed(1)} ± ${(196 * Math.sqrt(pr * (1 - pr) / n)).toFixed(1)} % of ${n}`; };
const ms = a => { const m = a.reduce((s, x) => s + x, 0) / a.length, sd = Math.sqrt(a.reduce((s, x) => s + (x - m) ** 2, 0) / (a.length - 1)); return `${m.toFixed(2)} ± ${(1.96 * sd / Math.sqrt(a.length)).toFixed(2)}`; };
console.log(`clips ${rows.length}, singers ${new Set(rows.map(r => r.who)).size}`);
for (const k of ['h12', 'tilt', 'hnr', 'cpp', 'cue']) {
  console.log(`${k}: ` + ['belt', 'straight', 'breathy'].map(t => `${t} ${ms(rows.filter(r => r.tech === t).map(r => r[k]))}`).join(', '));
  console.log(`   straight > belt: ${cmp('straight', 'belt', k)};  belt > straight: ${cmp('belt', 'straight', k)}`); }
if (process.env.DUMP) console.log(JSON.stringify(rows));
