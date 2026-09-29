// E-003 round 4 runner (squillo iteration 53, F-042): drives the installed
// Chrome and Firefox through page/r4.js, as run.mjs does round 1.
// Usage: node r4_run.mjs [chrome|firefox ...] [--reps N] [--seconds S] [--only NAME-PREFIX]
// Writes data/cache/r4/<name>.json (per-frame times; uncommitted, analysed by r4_analyze.py).
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import pw from 'playwright';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const OUT = path.join(HERE, 'data/cache/r4');
fs.mkdirSync(OUT, { recursive: true });
const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const REPS = Number(opt('--reps', 3));
const SECONDS = Number(opt('--seconds', 12));
const ONLY = opt('--only', '');
const browsers = args.filter((a) => a === 'chrome' || a === 'firefox');
if (!browsers.length) browsers.push('chrome', 'firefox');

// R1 (README round 4): block period 128/48000 s; frame period 384/48000 s (squillo SG-002)
const BLOCK_MS = 128 / 48000 * 1000, FRAME_MS = 384 / 48000 * 1000;
const WORKER_LOADS = [0, 0.75];      // fractions of the block period, from round 1's LOADS
const PAGE_LOADS = [0, 0.5, 1.5];    // fractions of the frame period; 1.5 is the must-fail overload

function serve() {
  const types = { '.html': 'text/html', '.js': 'text/javascript' };
  const srv = http.createServer((req, res) => {
    const u = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    const f = u === '/' ? '/page/r4.html' : u;
    const p = path.join(HERE, f);
    if (!p.startsWith(HERE) || !fs.existsSync(p)) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'content-type': types[path.extname(p)] || 'application/octet-stream' });
    fs.createReadStream(p).pipe(res);
  });
  return new Promise((r) => srv.listen(0, '127.0.0.1', () => r(srv)));
}
async function launch(browser) {
  process.env.TMPDIR = browser === 'chrome' ? '/tmp' : path.join(process.env.HOME, 'snap/firefox/common/e003-tmp');
  fs.mkdirSync(process.env.TMPDIR, { recursive: true });
  if (browser === 'chrome') {
    return pw.chromium.launch({ channel: 'chrome', headless: true, args: [
      '--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream',
      `--use-file-for-fake-audio-capture=${path.join(HERE, 'data/cache/probe48000.wav')}`,
      '--autoplay-policy=no-user-gesture-required'] });
  }
  return pw.firefox.launch({ channel: 'moz-firefox', executablePath: '/snap/bin/firefox', headless: true,
    firefoxUserPrefs: { 'media.navigator.streams.fake': true, 'media.navigator.permission.disabled': true,
      'media.autoplay.default': 0, 'media.autoplay.block-webaudio': false } });
}
const srv = await serve();
const base = `http://127.0.0.1:${srv.address().port}/`;
for (const browser of browsers) {
  for (const wl of WORKER_LOADS) for (const pl of PAGE_LOADS) for (let rep = 0; rep < REPS; rep++) {
    const name = `${browser}-wload${wl}-pload${pl}-r${rep}`;
    if (ONLY && !name.startsWith(ONLY)) continue;
    const t0 = Date.now();
    const b = await launch(browser);
    const p = await b.newPage();
    p.on('console', (m) => { if (m.type() === 'error') console.log('  page:', m.text()); });
    await p.goto(base);
    const cfg = { workerLoadMs: wl * BLOCK_MS, pageLoadMs: pl * FRAME_MS, seconds: SECONDS };
    let out;
    try { out = await p.evaluate((cfg) => window.e003r4.capture(cfg), cfg); }
    catch (e) { out = { cfg, error: String(e) }; }
    Object.assign(out, { browser, version: b.version(), workerLoad: wl, pageLoad: pl, rep, wallS: (Date.now() - t0) / 1000 });
    fs.writeFileSync(path.join(OUT, `${name}.json`), JSON.stringify(out));
    console.log(name, out.error || '', out.worker ? JSON.stringify(out.worker) : '', 'frames at page', out.fRecv ? out.fRecv.length : '-', `${out.wallS}s`);
    await b.close();
  }
}
srv.close();
