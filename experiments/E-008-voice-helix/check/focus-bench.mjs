// Focus verdict: focusVerdict, the page's own code, on aspects from the page's own take path, headless Chrome.
// VocalSet (Wilkins et al. 2018, CC BY 4.0, doi:10.5281/zenodo.1442513, not shipped): f/m singers, scales, 5 vowels. Each singer's clips stand in for takes.
// Rest: straight clips, each left out against up to 5 others of that singer: any 'better' or 'worse' is false.
// Change: clarity and steadiness, the mean of a singer's breathy clips as earlier takes, a straight clip now (should read better), and the reverse (worse).
// Usage: node check/focus-bench.mjs http://localhost:<port>/ <dir>
import { chromium } from 'playwright';
import { readdirSync, readFileSync } from 'fs';
const url = process.argv[2], dir = process.argv[3], files = readdirSync(dir).filter(f => /^[fm]\d+_scales_(straight|breathy)_[aeiou]\.wav$/.test(f));
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()), p = await b.newPage();
await p.route('**/vs/*', r => r.fulfill({ body: readFileSync(dir + '/' + decodeURIComponent(r.request().url().split('/vs/')[1])), contentType: 'audio/wav' }));
await p.goto(url); await p.waitForTimeout(1000);
const S = {};
for (const f of files) { const a = await p.evaluate(async f => { const a = await window.helixAspects(await (await fetch('vs/' + f)).arrayBuffer()); return { ok: a.ok, inton: a.inton, stab: a.stab, onset: a.onset, clar: a.clar }; }, f);
  if (!a.ok) continue; const [, s, t] = f.match(/^([fm]\d+)_scales_(\w+?)_/); ((S[s] ??= {})[t] ??= []).push(a); }
const wil = (k, n) => { const c = k / n, z = 1.96, d = 1 + z * z / n, m = (c + z * z / 2 / n) / d, e = z * Math.sqrt(c * (1 - c) / n + z * z / 4 / n / n) / d; return `${k}/${n} = ${(100 * c).toFixed(1)} % (${(100 * (m - e)).toFixed(1)}-${(100 * (m + e)).toFixed(1)})`; };
const V = async (k, now, prev) => p.evaluate(([k, now, prev]) => focusVerdict(aspectOf(k), now, prev).v, [k, now, prev]);
console.log('singers', Object.keys(S).length, 'clips', Object.values(S).flatMap(s => Object.values(s)).flat().length);
for (const k of ['inton', 'stab', 'onset', 'clar']) { let n = 0, bad = 0;
  for (const s of Object.values(S)) { const A = (s.straight || []).map(a => a[k]).filter(Number.isFinite); if (A.length < 4) continue;
    for (let i = 0; i < A.length; i++) { const v = await V(k, A[i], A.filter((_, j) => j !== i)); n++; if (v !== 'level') bad++; } }
  console.log(k.padEnd(6), 'rest, false change', wil(bad, n)); }
for (const k of ['clar']) { const r = { up: [0, 0, 0], down: [0, 0, 0] };
  for (const s of Object.values(S)) { const A = (s.straight || []).map(a => a[k]).filter(Number.isFinite), B = (s.breathy || []).map(a => a[k]).filter(Number.isFinite); if (A.length < 3 || B.length < 3) continue;
    for (const q of A) { const v = await V(k, q, B); r.up[0]++; if (v === 'better') r.up[1]++; if (v === 'worse') r.up[2]++; }
    for (const q of B) { const v = await V(k, q, A); r.down[0]++; if (v === 'worse') r.down[1]++; if (v === 'better') r.down[2]++; } }
  console.log(k, 'breathy to straight reads better', wil(r.up[1], r.up[0]), 'wrong way', r.up[2]); console.log(k, 'straight to breathy reads worse', wil(r.down[1], r.down[0]), 'wrong way', r.down[2]); }
await b.close();
