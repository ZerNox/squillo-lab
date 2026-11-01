// Accessibility audit: axe-core (WCAG 2 A/AA rules) on the page's main states, in Chrome and WebKit at iPhone size.
// Usage: node a11y-audit.mjs <url>. Exit 0 = no violations. Automated rules find only part of what a screen-reader user meets.
import { chromium, webkit, devices } from 'playwright';
import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
const axe = readFileSync(createRequire(import.meta.url).resolve('axe-core/axe.min.js'), 'utf8');
const clip = join(dirname(fileURLToPath(import.meta.url)), '../page/ref', readdirSync(join(dirname(fileURLToPath(import.meta.url)), '../page/ref')).find(f => /\.(mp3|wav|ogg)$/.test(f)));
const url = process.argv[2] || 'http://localhost:8123/';
const tags = ['best-practice', 'wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'];
const scan = async (p, state, sum) => { await p.evaluate(axe);
  const r = await p.evaluate(t => window.axe.run(document, { runOnly: t }), tags);
  for (const v of r.violations) { console.log(`${state}: ${v.id} [${v.impact}] x${v.nodes.length}: ${v.help}`);
    for (const n of v.nodes.slice(0, 4)) console.log('   ', n.target.join(' '), (n.any[0]?.message || '').slice(0, 110));
    sum.n += v.nodes.length; } };
let bad = 0;
for (const [name, b, o] of [['chrome', { launch: o => chromium.launch({ ...o, channel: 'chrome' }).catch(() => chromium.launch(o)) }, { viewport: { width: 1440, height: 900 } }], ['webkit-iphone', webkit, devices['iPhone 15']]]) {
  const br = await b.launch({}), p = await (await br.newContext(o)).newPage(), sum = { n: 0 };
  await p.goto(url); await p.waitForTimeout(800); console.log('==', name);
  await scan(p, 'start', sum);
  const fc = p.waitForEvent('filechooser'); await p.getByRole('button', { name: 'Recording' }).click(); await (await fc).setFiles(clip);
  await p.waitForFunction(() => document.getElementById('sumHead') || /went well/i.test(document.body.innerText), null, { timeout: 120000 }); await p.waitForTimeout(1000);
  await scan(p, 'take', sum);
  for (const nm of [/warm-up/, /voice profile/, /my data/]) { await p.getByRole('button', { name: nm }).first().click(); await p.waitForTimeout(500); await scan(p, String(nm), sum); await p.keyboard.press('Escape'); await p.getByRole('button', { name: nm }).first().click().catch(() => {}); await p.waitForTimeout(200); }
  await br.close(); bad += sum.n; }
process.exit(bad ? 1 : 0);
