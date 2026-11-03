// Sung vowel on the live chip's 0.5 s window: spanVowel (page code) over the last 0.5 s of frames at three points in each note (middle, three quarters, end), on VocalSet vibrato scales and arpeggios (CC BY 4.0, not shipped), against whole notes on the same footing. The shipped table was fitted on these singers, so the figures are optimistic.
// Usage: node check/vowel-live-bench.mjs http://localhost:<port>/ <vocalset dir>
import { chromium } from 'playwright'; import { readdirSync, readFileSync } from 'fs';
const [url, dir] = process.argv.slice(2), files = readdirSync(dir).filter(f => /^[fm]\d+_(scales|arpeggios)_vibrato_[aeiou]\.wav$/.test(f));
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch());
const job = async part => { const p = await b.newPage(); await p.route('**/vs/*', r => r.fulfill({ body: readFileSync(dir + '/' + r.request().url().split('/vs/')[1]), contentType: 'audio/wav' })); await p.goto(url); await p.waitForTimeout(1000); const N = [];
 for (const f of part) { const r = await p.evaluate(async f => { const buf = await new OfflineAudioContext(1, 1, 44100).decodeAudioData(await (await fetch('vs/' + f)).arrayBuffer()); const F = await trackTake(buf); viterbiF0(F); trimEdges(F, buf); const S = new Stats(); for (const m of F) ingest(S, m, 'take'); const fr = S.rec.frames;
  return takeNotes(smoothPitch(fr)).notes.filter(n => n.t1 - n.t0 >= 0.5).map(n => { const w = spanVowel(fr, n.t0, n.t1); const L = [0.5, 0.75, 1].map(q => { const t = n.t0 + q * (n.t1 - n.t0); return t - 0.5 >= n.t0 - 1e-6 ? spanVowel(fr, t - 0.5, t) : null; }); return { w: w && [w.v, w.sure], L: L.map(x => x && [x.v, x.sure]) }; }); }, f);
  const m = f.match(/^([fm]\d+)_.*_([aeiou])\.wav/); for (const x of r) N.push({ ...x, who: m[1], t: m[2] }); } return N; };
const K = 6, parts = Array.from({ length: K }, (_, i) => files.filter((_, j) => j % K === i)); const N = (await Promise.all(parts.map(job))).flat(); await b.close();
const who = [...new Set(N.map(x => x.who))];
const pc = (get) => { const u = who.map(w => { let k = 0, n = 0, s = 0, ks = 0, all = 0; for (const x of N.filter(x => x.who === w)) for (const y of get(x)) { all++; if (!y) continue; n++; if (y[0] === x.t) k++; if (y[1]) { s++; if (y[0] === x.t) ks++; } } return { a: n ? k / n : NaN, s: s ? ks / s : NaN, cov: all ? s / all : 0 }; }).filter(u => Number.isFinite(u.a));
 const ms = k => { const v = u.map(x => x[k]).filter(Number.isFinite), me = v.reduce((s, x) => s + x, 0) / v.length, sd = Math.sqrt(v.reduce((s, x) => s + (x - me) ** 2, 0) / (v.length - 1)); return `${(100 * me).toFixed(1)} ± ${(196 * sd / Math.sqrt(v.length)).toFixed(1)}`; };
 return `all ${ms('a')} %, sure ${ms('s')} % on ${ms('cov')} % of windows`; };
console.log(N.length, 'notes of 0.5 s or more,', who.length, 'singers');
console.log('whole note:', pc(x => [x.w]));
console.log('0.5 s live window:', pc(x => x.L));
