// Breathiness, measured with the page's own code (trackTake, viterbiF0, trimEdges, ingest: the take path) in
// headless Chrome on VocalSet (Wilkins et al. 2018, CC BY 4.0, doi:10.5281/zenodo.1442513, not shipped): every
// singer's scales sung "breathy" and "straight" on five vowels (same singer, scale and vowel; only the technique
// changes). Per clip: median over voiced frames of CPP (cepstral peak prominence, dB), the CMND-based HNR, and the
// share of voiced frames the page's 'breathy' cue fires on. Reported: AUC (breathy vs straight over all clips),
// and the within-singer-and-vowel pair accuracy (breathy reads lower than straight).
// Usage: node check/breath-bench.mjs http://localhost:<port>/ <dir with VocalSet *_scales_{breathy,straight}_<v>.wav>
import { chromium } from 'playwright';
import { readdirSync, readFileSync } from 'fs';
const url = process.argv[2], dir = process.argv[3];
const files = readdirSync(dir).filter(f => /^[fm]\d+_scales_(breathy|straight)_[aeiou]\.wav$/.test(f));
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()); const p = await b.newPage();
await p.route('**/vs/*', r => r.fulfill({ body: readFileSync(dir + '/' + decodeURIComponent(r.request().url().split('/vs/')[1])), contentType: 'audio/wav' }));
await p.goto(url); await p.waitForTimeout(1000);
const rows = [];
for (const f of files) {
  rows.push(await p.evaluate(async f => {
    const ab = await (await fetch('vs/' + f)).arrayBuffer(), buf = await new OfflineAudioContext(1, 1, 44100).decodeAudioData(ab);
    const fs = await trackTake(buf); viterbiF0(fs); trimEdges(fs, buf); const S = new Stats(); for (const m of fs) ingest(S, m, 'take');
    const sn = S.rec.snaps, fr = S.rec.frames, c = [], h = [], bi = FLAWS.findIndex(x => x.id === 'breathy'); let br = 0, nv = 0;
    for (let i = 0; i < fr.length; i++) { if (!fr[i].voiced) continue; nv++; c.push(sn[i].cpp); h.push(sn[i].hnr); if (FLAWS[bi].test(sn[i])) br++; }
    const med = a => a.sort((x, y) => x - y)[a.length >> 1] || 0;
    return { f, cpp: med(c), hnr: med(h), cue: nv ? br / nv : 0, nv };
  }, f));
}
await b.close();
for (const r of rows) { const m = r.f.match(/^([fm]\d+)_scales_(\w+)_([aeiou])/); r.who = m[1]; r.breathy = m[2] === 'breathy'; r.v = m[3]; }
const auc = (k, sign) => { const B = rows.filter(r => r.breathy), S = rows.filter(r => !r.breathy); let w = 0; for (const x of B) for (const y of S) w += sign * (y[k] - x[k]) > 0 ? 1 : sign * (y[k] - x[k]) === 0 ? 0.5 : 0; return w / B.length / S.length; };
const pairs = (k, sign) => { let ok = 0, n = 0; for (const x of rows.filter(r => r.breathy)) { const y = rows.find(r => !r.breathy && r.who === x.who && r.v === x.v); if (!y) continue; n++; if (sign * (y[k] - x[k]) > 0) ok++; } const pr = ok / n; return `${(100 * pr).toFixed(1)} ± ${(196 * Math.sqrt(pr * (1 - pr) / n)).toFixed(1)} % of ${n}`; };
const ms = a => { const m = a.reduce((s, x) => s + x, 0) / a.length, sd = Math.sqrt(a.reduce((s, x) => s + (x - m) ** 2, 0) / (a.length - 1)); return `${m.toFixed(2)} ± ${(1.96 * sd / Math.sqrt(a.length)).toFixed(2)}`; };
console.log(`clips ${rows.length} (${rows.filter(r => r.breathy).length} breathy), singers ${new Set(rows.map(r => r.who)).size}`);
for (const [k, s, name] of [['cpp', 1, 'CPP (dB)'], ['hnr', 1, 'HNR from CMND (dB)'], ['cue', -1, "page 'breathy' cue share"]])
  console.log(`${name}: breathy ${ms(rows.filter(r => r.breathy).map(r => r[k]))}, straight ${ms(rows.filter(r => !r.breathy).map(r => r[k]))}; AUC ${auc(k, s).toFixed(3)}; pairs ${pairs(k, s)}`);
for (const g of ['f', 'm']) { const sub = rows.filter(r => r.who[0] === g); console.log(`  ${g === 'f' ? 'women' : 'men'}: CPP breathy ${ms(sub.filter(r => r.breathy).map(r => r.cpp))}, straight ${ms(sub.filter(r => !r.breathy).map(r => r.cpp))}`); }
if (process.env.DUMP) console.log(JSON.stringify(rows));
