// E-003 round 1 runner: drives the installed Chrome (Playwright, channel
// "chrome") and the installed Firefox (Playwright over WebDriver BiDi,
// channel "moz-firefox") through page/probe.js.
// Usage: node run.mjs [chrome|firefox ...] [--reps N] [--seconds S]
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import pw from 'playwright';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const RAW_DIR = path.join(HERE, 'data/cache/raw');
const OUT_DIR = path.join(HERE, 'results/raw');
fs.mkdirSync(RAW_DIR, { recursive: true });
fs.mkdirSync(OUT_DIR, { recursive: true });

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? Number(args[i + 1]) : d; };
const REPS = opt('--reps', 3);
const SECONDS = opt('--seconds', 12);
const READBACK_ONLY = args.includes('--readback-only');
// --fake R: only the Chrome conditions whose fake capture file is at R Hz
// (splits a run into steps; the readback runs whatever the filter)
const FAKE = opt('--fake', null);
const browsers = args.filter((a) => a === 'chrome' || a === 'firefox');
if (!browsers.length) browsers.push('chrome', 'firefox');

// Block period at 48 kHz is 128 / 48000 s = 2.667 ms; loads are fractions of it.
const PERIOD_MS = 128 / 48000 * 1000;
const LOADS = [0, 0.5, 0.75, 0.9, 1.5];

function conditions(browser) {
  const c = [];
  const fakeRates = browser === 'chrome' ? [48000, 44100] : [null];
  for (const fr of fakeRates) {
    // mic path: the fake capture device into a 48 kHz context, every load
    for (const l of LOADS) c.push({ path: 'mic', fakeRate: fr, ctxRate: 48000, load: l });
    // mic path into a 44.1 kHz context (the other side of a rate mismatch)
    c.push({ path: 'mic', fakeRate: fr, ctxRate: 44100, load: 0 });
  }
  // stream path: a track made at srcRate, read by a context at ctxRate
  for (const [s, r] of [[48000, 48000], [44100, 48000], [48000, 44100]])
    c.push({ path: 'stream', fakeRate: browser === 'chrome' ? 48000 : null, srcRate: s, ctxRate: r, load: 0 });
  return c;
}

function serve() {
  const types = { '.html': 'text/html', '.js': 'text/javascript', '.f32': 'application/octet-stream' };
  const srv = http.createServer((req, res) => {
    const u = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    let f = u === '/' ? '/page/index.html' : u;
    if (f.startsWith('/data/')) f = '/data/cache/' + f.slice(6);
    const p = path.join(HERE, f);
    if (!p.startsWith(HERE) || !fs.existsSync(p)) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'content-type': types[path.extname(p)] || 'application/octet-stream' });
    fs.createReadStream(p).pipe(res);
  });
  return new Promise((r) => srv.listen(0, '127.0.0.1', () => r(srv)));
}

async function launch(browser, fakeRate) {
  // The snap Firefox sees neither /tmp nor hidden directories under home
  // (this worktree may live under ~/.local); its temporary profile goes in
  // the snap's own cache directory, removed after each run by Playwright.
  process.env.TMPDIR = browser === 'chrome' ? '/tmp'
    : path.join(process.env.HOME, 'snap/firefox/common/e003-tmp');
  fs.mkdirSync(process.env.TMPDIR, { recursive: true });
  if (browser === 'chrome') {
    return pw.chromium.launch({ channel: 'chrome', headless: true, args: [
      '--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream',
      `--use-file-for-fake-audio-capture=${path.join(HERE, `data/cache/probe${fakeRate}.wav`)}`,
      '--autoplay-policy=no-user-gesture-required'] });
  }
  return pw.firefox.launch({ channel: 'moz-firefox', executablePath: '/snap/bin/firefox',
    headless: true, firefoxUserPrefs: {
      'media.navigator.streams.fake': true,
      'media.navigator.permission.disabled': true,
      'media.autoplay.default': 0,
      'media.autoplay.block-webaudio': false } });
}

const srv = await serve();
const base = `http://127.0.0.1:${srv.address().port}/`;
// merged with earlier steps' versions, so a split run keeps them all
const VFILE = path.join(OUT_DIR, 'versions.json');
const version = fs.existsSync(VFILE) ? JSON.parse(fs.readFileSync(VFILE)) : {};
for (const browser of browsers) {
  // readback, raw request and default request, per fake rate
  const rates = browser === 'chrome' ? [48000, 44100] : [null];
  for (const fr of rates) {
    const b = await launch(browser, fr);
    version[browser] = b.version();
    const p = await b.newPage();
    await p.goto(base);
    const rb = { browser, version: b.version(), fakeRate: fr,
      raw: await p.evaluate(() => window.e003.readback('raw')),
      default: await p.evaluate(() => window.e003.readback('default')) };
    fs.writeFileSync(path.join(OUT_DIR, `${browser}-readback${fr ? '-' + fr : ''}.json`), JSON.stringify(rb, null, 1));
    console.log(browser, fr, 'readback', JSON.stringify(rb.raw.settings));
    await b.close();
  }
  if (READBACK_ONLY) continue;
  for (const c of conditions(browser).filter((c) => FAKE === null || c.fakeRate === FAKE || c.fakeRate === null)) {
    for (let rep = 0; rep < REPS; rep++) {
      const name = [browser, c.path, c.fakeRate ? `fake${c.fakeRate}` : 'fake',
        c.srcRate ? `src${c.srcRate}` : null, `ctx${c.ctxRate}`, `load${c.load}`, `r${rep}`].filter(Boolean).join('-');
      const b = await launch(browser, c.fakeRate);
      const p = await b.newPage();
      p.on('console', (m) => { if (m.type() === 'error') console.log('  page:', m.text()); });
      await p.goto(base);
      const cfg = { path: c.path, srcRate: c.srcRate, ctxRate: c.ctxRate,
                    loadMs: c.load * PERIOD_MS, seconds: SECONDS };
      let out;
      try { out = await p.evaluate((cfg) => window.e003.capture(cfg), cfg); }
      catch (e) { out = { cfg, error: String(e) }; }
      out.browser = browser; out.version = b.version(); out.condition = c; out.rep = rep;
      if (out.samples) {
        fs.writeFileSync(path.join(RAW_DIR, `${name}.f32`), Buffer.from(out.samples, 'base64'));
        delete out.samples;
      }
      fs.writeFileSync(path.join(RAW_DIR, `${name}.json`), JSON.stringify(out));
      console.log(name, out.error || out.ctxError || out.sourceError || '',
        out.worker ? JSON.stringify(out.worker) : '', out.tap ? JSON.stringify({ calls: out.tap.stats.calls, ch: out.tap.stats.maxChannels, empty: out.tap.stats.emptyInputs }) : '',
        out.ctxRate || '');
      await b.close();
    }
  }
}
fs.writeFileSync(VFILE, JSON.stringify(version, null, 1));
srv.close();
