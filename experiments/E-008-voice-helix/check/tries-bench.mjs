// Tries of one note (the Lane's 'tries of G4'): runs the page's own triesTrend on synthetic series of a note's live
// wobble. Each try reads true + N(0, SE), SE = ± / 1.96 with ± drawn 0.5-3 ¢ (the Lane's range), plus, in the 'scatter'
// rows, an extra try-to-try spread of 1.5 ¢ the ± does not know about. Counts 'steadier'/'less steady' calls per 400.
// Usage: node check/tries-bench.mjs http://localhost:<port>/
import { chromium } from 'playwright';
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()); const p = await b.newPage(); await p.goto(process.argv[2]); await p.waitForTimeout(800);
const out = await p.evaluate(() => { let s = 7; const rnd = () => (s = (s * 16807) % 2147483647) / 2147483647, gs = () => Math.sqrt(-2 * Math.log(rnd())) * Math.cos(2 * Math.PI * rnd());
  const rows = []; for (const n of [3, 4, 6]) for (const [name, drop, sc] of [['level', 0, 0], ['level+scatter', 0, 1.5], ['−30 %', 0.3, 0], ['halved', 0.5, 0], ['halved+scatter', 0.5, 1.5], ['+50 %', -0.5, 0]]) {
    const c = { steadier: 0, 'less steady': 0, level: 0 }; for (let r = 0; r < 400; r++) { const w0 = 4 + 10 * rnd(), T = [];
      for (let i = 0; i < n; i++) { const tru = w0 * (1 - drop * i / (n - 1)), pm = 0.5 + 2.5 * rnd(); T.push({ t: i, wob: Math.max(0.3, tru + gs() * pm / 1.96 + sc * gs()), pm }); }
      c[triesTrend(T).w]++; } rows.push(`${n} tries  ${name.padEnd(15)} steadier ${c.steadier}/400  less steady ${c['less steady']}/400  level ${c.level}/400`); } return rows; });
console.log(out.join('\n')); await b.close();
