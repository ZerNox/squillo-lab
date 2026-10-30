// Sung vowel per note (takeNotes, spanVowel: the take path) in headless Chrome on VocalSet (Wilkins et al. 2018, CC BY 4.0,
// doi:10.5281/zenodo.1442513, not shipped): *_{scales,arpeggios}_vibrato_<v>.wav, five vowels, the label from the file name.
// Reported: 5-way accuracy per f0 band shipped (spanVowel, table fitted on these notes, so optimistic: the honest figure is check/vowel-fit.mjs), speech VOWELS, formant centres left-out-singer, 'sure', 0.5 s live window; ± 1.96 SE over singers.
// Usage: node check/vowel-bench.mjs http://localhost:<port>/ <dir>
import { chromium } from 'playwright'; import { readdirSync, readFileSync } from 'fs';
const [url, dir] = process.argv.slice(2), files = readdirSync(dir).filter(f => /^[fm]\d+_(scales|arpeggios)_vibrato_[aeiou]\.wav$/.test(f));
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()), p = await b.newPage();
await p.route('**/vs/*', r => r.fulfill({ body: readFileSync(dir + '/' + r.request().url().split('/vs/')[1]), contentType: 'audio/wav' }));
await p.goto(url); await p.waitForTimeout(1000);
const N = [];
for (const f of files) { const r = await p.evaluate(async f => { const buf = await new OfflineAudioContext(1, 1, 44100).decodeAudioData(await (await fetch('vs/' + f)).arrayBuffer()); const F = await trackTake(buf); viterbiF0(F); trimEdges(F, buf); const S = new Stats(); for (const m of F) ingest(S, m, 'take'); const fr = S.rec.frames;
    return takeNotes(smoothPitch(fr)).notes.map(n => { const a = fr.filter(e => e.voiced && e.F1 && e.F2 && e.t >= n.t0 && e.t <= n.t1); if (a.length < 8) return null; const med = k => a.map(e => e[k]).sort((x, y) => x - y)[a.length >> 1]; const R = spanVowel(fr, n.t0, n.t1), s = readVowel(med('F1'), med('F2'), Math.min(med('f0'), 599), VOWELS); const mid = (n.t0 + n.t1) / 2, W = n.t1 - n.t0 >= 0.5 ? spanVowel(fr, mid - 0.25, mid + 0.25) : null; return { win: W && W.v, winSure: W && W.sure, f0: med('f0'), F1: med('F1'), F2: med('F2'), v: R && R.v, sure: R && R.sure, sp: s && s.v }; }).filter(Boolean); }, f);
  const m = f.match(/^([fm]\d+)_.*_([aeiou])\.wav/); for (const x of r) N.push({ ...x, who: m[1], t: m[2] }); }
await b.close();
const who = [...new Set(N.map(x => x.who))], L = Math.log, near = (x, C) => Object.keys(C).sort((a, c) => Math.hypot(L(x.F1 / C[a][0]), L(x.F2 / C[a][1])) - Math.hypot(L(x.F1 / C[c][0]), L(x.F2 / C[c][1])))[0];
for (const x of N) { const C = {}; for (const v of 'aeiou') { const a = N.filter(y => y.who !== x.who && y.t === v && y.f0 < 400); C[v] = [Math.exp(a.reduce((s, y) => s + L(y.F1), 0) / a.length), Math.exp(a.reduce((s, y) => s + L(y.F2), 0) / a.length)]; } x.lo = near(x, C); }
const pc = (a, k) => { const u = who.map(w => a.filter(x => x.who === w)).filter(g => g.length).map(g => g.filter(x => x[k] === x.t).length / g.length), m = u.reduce((s, x) => s + x, 0) / u.length, sd = Math.sqrt(u.reduce((s, x) => s + (x - m) ** 2, 0) / Math.max(1, u.length - 1)); return `${(100 * m).toFixed(1)} ± ${(196 * sd / Math.sqrt(u.length)).toFixed(1)} %`; };
console.log(`notes ${N.length}, singers ${who.length}`);
for (const [lo, hi] of [[0, 200], [200, 300], [300, 400], [400, 600], [600, 9999], [0, 600]]) { const a = N.filter(x => x.f0 >= lo && x.f0 < hi), s = a.filter(x => x.sure); console.log(`${lo}-${hi} Hz: n ${a.length}; shipped ${pc(a, 'v')}; speech ${pc(a, 'sp')}; left-out-singer ${pc(a, 'lo')}; sure ${s.length ? pc(s, 'v') : '-'} on ${(100 * s.length / a.length).toFixed(0)} %`); }
const W = N.filter(x => x.win && x.f0 < 600); console.log(`0.5 s live window: n ${W.length}; ${pc(W, 'win')}; sure ${pc(W.filter(x => x.winSure), 'win')} on ${(100 * W.filter(x => x.winSure).length / W.length).toFixed(0)} %`);
