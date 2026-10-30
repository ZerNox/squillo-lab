// Singing power ratio (SPR, Omori et al. 1996: strongest peak 2-4 kHz minus strongest under 2 kHz, dB), the page's take path in headless Chrome on VocalSet (Wilkins et al. 2018, CC BY 4.0,
// doi:10.5281/zenodo.1442513, not shipped). Per clip the median over voiced frames, whole and in its first and second half in time, and with the clip at -12 dB (gain invariance).
// Reported: same-singer pairs and AUC, forte vs pp and straight vs breathy; split-half r; gain shift. No singer's-formant label exists in the set, so these contrasts are proxies.
// Usage: node check/ring-bench.mjs http://localhost:<port>/ <dir>
import { chromium } from 'playwright'; import { readdirSync, readFileSync } from 'fs';
const [url, dir] = process.argv.slice(2), files = readdirSync(dir).filter(f => /^[fm]\d+_(long_(forte|pp)_a|scales_(straight|breathy)_a)\.wav$/.test(f));
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()), p = await b.newPage();
await p.route('**/vs/*', r => r.fulfill({ body: readFileSync(dir + '/' + r.request().url().split('/vs/')[1]), contentType: 'audio/wav' }));
await p.goto(url); await p.waitForTimeout(1000);
const rows = [];
for (const f of files) { const r = await p.evaluate(async f => { const buf = await new OfflineAudioContext(1, 1, 44100).decodeAudioData(await (await fetch('vs/' + f)).arrayBuffer());
    const run = async B => { const F = await trackTake(B); viterbiF0(F); trimEdges(F, B); const S = new Stats(); for (const m of F) ingest(S, m, 'take'); const a = []; S.rec.frames.forEach((e, i) => { if (e.voiced && e.f0 < 1000 && S.rec.snaps[i].spr) a.push(S.rec.snaps[i].spr); }); return a; };
    const med = a => [...a].sort((x, y) => x - y)[a.length >> 1], a = await run(buf), q = new OfflineAudioContext(1, buf.length, buf.sampleRate).createBuffer(1, buf.length, buf.sampleRate); q.copyToChannel(buf.getChannelData(0).map(v => v / 4), 0); const c = await run(q);
    return { f, spr: med(a), h1: med(a.slice(0, a.length >> 1)), h2: med(a.slice(a.length >> 1)), quiet: med(c), n: a.length }; }, f); rows.push(r); }
await b.close();
for (const r of rows) { const m = r.f.match(/^([fm]\d+)_\w+?_(forte|pp|straight|breathy)_/); r.who = m[1]; r.t = m[2]; }
const cmp = (A, B) => { const X = rows.filter(r => r.t === A), Y = rows.filter(r => r.t === B); let w = 0, ok = 0, n = 0; for (const x of X) { for (const y of Y) w += x.spr > y.spr ? 1 : 0; const y = Y.find(r => r.who === x.who); if (y) { n++; if (x.spr > y.spr) ok++; } } const md = a => a.sort((p, q) => p - q)[a.length >> 1]; return `${A} vs ${B}: AUC ${(w / X.length / Y.length).toFixed(2)}, pairs ${ok}/${n}, median ${md(X.map(r => r.spr)).toFixed(1)} vs ${md(Y.map(r => r.spr)).toFixed(1)} dB`; };
console.log(cmp('forte', 'pp')); console.log(cmp('straight', 'breathy'));
const v = rows.filter(r => r.n > 40), mx = v.reduce((s, r) => s + r.h1, 0) / v.length, my = v.reduce((s, r) => s + r.h2, 0) / v.length; let xy = 0, xx = 0, yy = 0; for (const r of v) { xy += (r.h1 - mx) * (r.h2 - my); xx += (r.h1 - mx) ** 2; yy += (r.h2 - my) ** 2; }
console.log(`split-half r ${(xy / Math.sqrt(xx * yy)).toFixed(3)} (${v.length} clips); gain -12 dB shift max ${Math.max(...rows.filter(r => Number.isFinite(r.quiet)).map(r => Math.abs(r.spr - r.quiet))).toFixed(2)} dB`);
