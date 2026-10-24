// Builds page/rating/anchors.json: the reference pool for the take rating.
// Each clip is measured by the page itself (window.helixAspects, the same code that measures a take)
// in headless Chrome, then the pool plays a round robin (aspectGame) and Elo ratings are fitted so the
// median conservatory-trained singer (VocalSet) is 2000.
// Usage: node build-anchors.mjs <page-url> <vocalset-dir> <out.json> [label=file ...]
//   PLAYWRIGHT=/path/to/node_modules/playwright (default: ~/.local/share/squillo/verify)
import { readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { join, basename } from 'node:path';
const pw = await import(process.env.PLAYWRIGHT || join(process.env.HOME, '.local/share/squillo/verify/node_modules/playwright/index.mjs'));
const [url, vsDir, out, ...extra] = process.argv.slice(2);
const clips = readdirSync(vsDir).filter(f => /\.(wav|mp3)$/.test(f)).sort().map(f => ({ id: 'vocalset/' + f.replace(/\.\w+$/, ''), group: 'trained', file: join(vsDir, f) }));
for (const e of extra) { const [label, file] = e.split('='); clips.push({ id: label, group: 'other', file }); }
const b = await pw.chromium.launch({ channel: 'chrome' }); const p = await b.newPage();
await p.goto(url, { waitUntil: 'load' });
const ASP = await p.evaluate(() => RATED.map(x => ({ k: x.k, lower: x.lower, tol: x.tol })));
const rows = [];
for (const c of clips) {
  const b64 = readFileSync(c.file).toString('base64');
  const a = await p.evaluate(async s => { const bin = atob(s), u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i); return helixAspects(u.buffer); }, b64);
  if (!a.ok) { console.error('skip (too few notes)', c.id); continue; }
  rows.push({ ...c, a }); console.error(c.id, ASP.map(x => x.k + '=' + a[x.k].toFixed(2)).join(' '));
}
await b.close();
const game = (a, b) => { let s = 0; for (const x of ASP) { const d = a[x.k] - b[x.k]; s += Math.abs(d) <= x.tol ? 0.5 : (x.lower ? d < 0 : d > 0) ? 1 : 0; } return s / ASP.length; };
const n = rows.length, R = new Array(n).fill(1500);
for (let it = 0; it < 4000; it++) for (let i = 0; i < n; i++) { let g = 0; for (let j = 0; j < n; j++) if (i !== j) g += game(rows[i].a, rows[j].a) - 1 / (1 + 10 ** ((R[j] - R[i]) / 400)); R[i] += 2 * g / n * 4; }
const tr = rows.map((r, i) => r.group === 'trained' ? R[i] : null).filter(x => x !== null).sort((a, b) => a - b), shift = 2000 - tr[tr.length >> 1];
const anchors = rows.map((r, i) => ({ id: r.id, group: r.group, r: Math.round(R[i] + shift), a: Object.fromEntries(ASP.map(x => [x.k, +r.a[x.k].toFixed(3)])) })).sort((a, b) => b.r - a.r);
const json = { pool: `${tr.length} VocalSet song excerpts by 20 conservatory-trained singers (Wilkins et al. 2018, CC BY 4.0)` + (extra.length ? ` and ${extra.length} other recordings` : ''), built: new Date().toISOString().slice(0, 10), anchors };
writeFileSync(out, JSON.stringify(json, null, 1));
for (const a of anchors.filter(a => a.group !== 'trained')) console.error('other:', a.id, a.r);
console.error('trained range', anchors.filter(a => a.group === 'trained').at(-1).r, '..', anchors.filter(a => a.group === 'trained')[0].r);
