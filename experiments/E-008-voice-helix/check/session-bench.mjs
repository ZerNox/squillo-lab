// Today's session: sessVerdict, the page's own code, on aspects from the page's own take path, headless Chrome.
// VocalSet (Wilkins et al. 2018, CC BY 4.0, doi:10.5281/zenodo.1442513, not shipped): f/m singers, scales, 5 vowels. Each singer's clips stand in for takes.
// Rest: straight clips dealt at random into today (2-3) and earlier days (rest): any 'better' or 'worse' is false; counted per aspect and per session.
// Change: clarity, breathy clips earlier, straight today (better), and the reverse (worse). Also the same draws from a normal, to see what clip order hides.
// Usage: node check/session-bench.mjs http://localhost:<port>/ <dir>
import { chromium } from 'playwright';
import { readdirSync, readFileSync } from 'fs';
const url = process.argv[2], dir = process.argv[3], files = readdirSync(dir).filter(f => /^[fm]\d+_scales_(straight|breathy)_[aeiou]\.wav$/.test(f));
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()), p = await b.newPage();
await p.route('**/vs/*', r => r.fulfill({ body: readFileSync(dir + '/' + decodeURIComponent(r.request().url().split('/vs/')[1])), contentType: 'audio/wav' }));
await p.goto(url); await p.waitForTimeout(1000);
const KS = await p.evaluate(() => SESS.map(x => x.k)), S = {};
for (const f of files) { const a = await p.evaluate(async ([f, KS]) => { const a = await window.helixAspects(await (await fetch('vs/' + f)).arrayBuffer()); let q = 0, w = 0; for (const n of a.perf || []) { const d = n.t1 - n.t0; q += n.q * d; w += d; } return { ok: a.ok, ...Object.fromEntries(KS.map(k => [k, a[k]])), score: w ? q / w : NaN }; }, [f, KS]);
  if (!a.ok) continue; const [, s, t] = f.match(/^([fm]\d+)_scales_(\w+?)_/); ((S[s] ??= {})[t] ??= []).push(a); }
const wil = (k, n) => { const c = k / n, z = 1.96, d = 1 + z * z / n, m = (c + z * z / 2 / n) / d, e = z * Math.sqrt(c * (1 - c) / n + z * z / 4 / n / n) / d; return `${k}/${n} = ${(100 * c).toFixed(1)} % (${(100 * (m - e)).toFixed(1)}-${(100 * (m + e)).toFixed(1)})`; };
let seed = 11; const rnd = () => (seed = seed * 16807 % 2147483647) / 2147483647, shuf = a => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
const V = (k, A, B) => p.evaluate(([k, A, B]) => { const v = sessVerdict(SESS.find(x => x.k === k), A, B); return v && v.v; }, [k, A, B]);
console.log('singers', Object.keys(S).length, 'clips', Object.values(S).flatMap(s => Object.values(s)).flat().length, 'aspects', KS.join(' '));
const cnt = Object.fromEntries(KS.map(k => [k, [0, 0, 0, 0]])); let ses = 0, anyF = 0, anyB = 0;
for (const s of Object.values(S)) { const C = s.straight || []; if (C.length < 5) continue;
  for (let r = 0; r < 40; r++) { const D = shuf(C), n = 2 + r % 2, A = D.slice(0, n), B = D.slice(n); let f = 0, g = 0;
    for (const k of KS) { const v = await V(k, A.map(a => a[k]), B.map(a => a[k])); if (!v) continue; cnt[k][0]++; if (v === 'better') { cnt[k][1]++; g++; } if (v === 'worse') cnt[k][2]++; if (v !== 'level') f++; }
    ses++; if (f) anyF++; if (g) anyB++; } }
for (const k of KS) console.log(k.padEnd(7), 'rest false', wil(cnt[k][1] + cnt[k][2], cnt[k][0]));
console.log('rest, sessions with any false change', wil(anyF, ses), 'any false better', wil(anyB, ses));
const r = { up: [0, 0, 0], down: [0, 0, 0] };
for (const s of Object.values(S)) { const A = (s.straight || []).map(a => a.clar).filter(Number.isFinite), B = (s.breathy || []).map(a => a.clar).filter(Number.isFinite); if (A.length < 5 || B.length < 5) continue;
  for (let i = 0; i < 20; i++) { const n = 2 + i % 2, v = await V('clar', shuf(A).slice(0, n), B); r.up[0]++; if (v === 'better') r.up[1]++; if (v === 'worse') r.up[2]++; const w = await V('clar', shuf(B).slice(0, n), A); r.down[0]++; if (w === 'worse') r.down[1]++; if (w === 'better') r.down[2]++; } }
console.log('clar breathy to straight better', wil(r.up[1], r.up[0]), 'wrong way', r.up[2]); console.log('clar straight to breathy worse', wil(r.down[1], r.down[0]), 'wrong way', r.down[2]);
const g = () => Math.sqrt(-2 * Math.log(rnd() || 1e-9)) * Math.cos(6.283185 * rnd()); let nf = 0, nt = 0; const N = await p.evaluate(() => 1);
for (let i = 0; i < 4000; i++) { const n = 2 + i % 2, m = 3 + i % 8, sd = 8, A = Array.from({ length: n }, () => 20 + sd * g()), B = Array.from({ length: m }, () => 20 + sd * g()); const v = await V('inton', A, B); nt++; if (v !== 'level') nf += N; }
console.log('normal draws, one aspect (SD 8, tol 3), false', wil(nf, nt));
await b.close();
