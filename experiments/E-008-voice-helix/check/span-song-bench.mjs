// Key from a recording: the page's songSpan (take path, segNotes, lowest/highest semitone held SPAN_MIN s in total)
// against the same rule on vocadito's hand-annotated notes (Bittner et al. 2021, 40 a cappella excerpts, CC BY 4.0,
// https://zenodo.org/records/5578807, not shipped), annotator A1, and A1 against A2 as the human floor.
// Reports exact-semitone and within-1 agreement for lowest, highest and the key shift (centre of span, rounded).
// Usage: node check/span-song-bench.mjs http://localhost:<port>/ /path/to/vocadito
import { chromium } from 'playwright'; import fs from 'node:fs'; import path from 'node:path';
const [url, dir] = process.argv.slice(2);
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()); const p = await b.newPage();
await p.route('**/vocadito/**', r => r.fulfill({ body: fs.readFileSync(path.join(dir, 'Audio', path.basename(new URL(r.request().url()).pathname))) }));
await p.goto(url); await p.waitForTimeout(1000);
const span = (f) => { if (!fs.existsSync(f)) return null; const T = new Map();
  for (const l of fs.readFileSync(f, 'utf8').trim().split('\n')) { const [t, hz, d] = l.split(',').map(Number); const k = Math.round(69 + 12 * Math.log2(hz / 440)); T.set(k, (T.get(k) || 0) + d); }
  const ks = [...T].filter(x => x[1] >= 0.25).map(x => x[0]).sort((a, c) => a - c); return ks.length >= 2 ? { lo: ks[0], hi: ks.at(-1) } : null; };
const R = [];
for (let i = 1; i <= 40; i++) {
  const pg = await p.evaluate(async i => { const ab = await (await fetch(`vocadito/vocadito_${i}.wav`)).arrayBuffer(); const buf = await new OfflineAudioContext(1, 1, 44100).decodeAudioData(ab); return songSpan(buf); }, i);
  const a1 = span(path.join(dir, 'Annotations/Notes', `vocadito_${i}_notesA1.csv`)), a2 = span(path.join(dir, 'Annotations/Notes', `vocadito_${i}_notesA2.csv`));
  R.push({ i, pg, a1, a2 }); console.log(i, JSON.stringify(pg), JSON.stringify(a1), JSON.stringify(a2));
}
await b.close();
const cmp = (X, Y) => { const P = R.filter(r => r[X] && r[Y]); const c = r => (r.lo + r.hi) / 2; const s = (f, tol) => { const k = P.filter(r => Math.abs(f(r)) <= tol).length, q = k / P.length; return `${k}/${P.length} (${(100 * q).toFixed(0)} ± ${(196 * Math.sqrt(q * (1 - q) / P.length)).toFixed(0)} %)`; };
  return `n ${P.length}; lowest exact ${s(r => r[X].lo - r[Y].lo, 0)}, ±1 ${s(r => r[X].lo - r[Y].lo, 1)}; highest exact ${s(r => r[X].hi - r[Y].hi, 0)}, ±1 ${s(r => r[X].hi - r[Y].hi, 1)}; key shift exact ${s(r => Math.round(c(r[X])) - Math.round(c(r[Y])), 0)}, ±1 ${s(r => Math.round(c(r[X])) - Math.round(c(r[Y])), 1)}`; };
console.log('page vs A1:', cmp('pg', 'a1')); console.log('A2 vs A1:', cmp('a2', 'a1'));
