// A real outage in all three browsers (Playwright's setOffline breaks WebKit navigation): serves page/ itself, loads the page so the service worker
// keeps it, shuts the server, then a new tab must open the page, run its script, and fetch a clip and a font. Usage: node check/offline-check.mjs
import { chromium, firefox, webkit, devices } from 'playwright';
import { createServer } from 'node:http';
import { existsSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, extname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
const here = dirname(fileURLToPath(import.meta.url)), root = join(here, '../page'), wk = join(process.env.HOME, '.local/share/squillo/webkit-libs/root/usr/lib/x86_64-linux-gnu');
if (existsSync(wk)) { process.env.PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS ??= '1'; process.env.GST_PLUGIN_PATH ??= join(wk, 'gstreamer-1.0'); }
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.webmanifest': 'application/manifest+json', '.png': 'image/png', '.mp3': 'audio/mpeg', '.woff2': 'font/woff2' };
if (existsSync('/snap/bin/firefox')) { process.env.TMPDIR = join(process.env.HOME, 'snap/firefox/common/voice-helix-check'); mkdirSync(process.env.TMPDIR, { recursive: true }); }
let bad = 0;
for (const [name, type, opt, how] of [['chrome', chromium, {}, { channel: 'chrome' }], ['firefox', firefox, {}, existsSync('/snap/bin/firefox') ? { channel: 'moz-firefox', executablePath: '/snap/bin/firefox' } : {}], ['webkit-iphone', webkit, devices['iPhone 15'], {}]]) {
  const srv = createServer((q, s) => { const u = decodeURIComponent(q.url.split('?')[0]), f = join(root, u.endsWith('/') ? 'index.html' : u); if (u.includes('..') || !existsSync(f)) { s.writeHead(404); s.end(); return; } s.writeHead(200, { 'Content-Type': MIME[extname(f)] || 'text/plain', Connection: 'close' }); s.end(readFileSync(f)); });
  await new Promise(r => srv.listen(0, '127.0.0.1', r)); const url = `http://localhost:${srv.address().port}/`, b = await type.launch(how), c = await b.newContext(opt); let r = { browser: name, ok: false };
  try { const p = await c.newPage(); await p.goto(url); await p.evaluate(() => navigator.serviceWorker.ready); await p.waitForFunction(() => navigator.serviceWorker.controller, null, { timeout: 15000 });
    r.kept = await p.evaluate(async () => { const c = await caches.open('helix-1'); for (let k = 0; k < 100; k++) { const n = (await c.keys()).length; if (n >= 26) return n; await new Promise(r => setTimeout(r, 100)); } return (await c.keys()).length; });
    srv.closeAllConnections(); await new Promise(r => srv.close(r));
    const o = await c.newPage(), t0 = Date.now(); await o.goto(url); await o.waitForSelector('#bData', { state: 'attached' }); r.ms = Date.now() - t0;
    r.run = await o.evaluate(async () => { const a = await fetch('ref/rough.mp3'), f = await fetch('font/syne.woff2'); return typeof renderData === 'function' && a.ok && f.ok; }); r.ok = r.kept >= 26 && r.run; }
  catch (e) { r.err = String(e).slice(0, 200); }
  await b.close(); srv.close(); console.log(JSON.stringify(r)); if (!r.ok) bad++; }
process.exit(bad ? 1 : 0);
