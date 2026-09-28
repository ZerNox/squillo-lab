// E-001 fold 2 (squillo iteration 43, F-043 k): run fold 1's WORLD WASM in the
// installed Chrome and Firefox, headless, through Playwright, and write every
// rung's samples to data/cache/f2/<browser>/p<pass>/. Crude experiment code.
// Usage: node f2_run.mjs [chrome|firefox ...]   -> results/f2/<browser>.json
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import pw from 'playwright';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const OUTDIR = path.join(HERE, 'data/cache/f2');
const browsers = process.argv.slice(2).filter((a) => a === 'chrome' || a === 'firefox');
if (!browsers.length) browsers.push('chrome', 'firefox');
fs.mkdirSync(path.join(HERE, 'results/f2'), { recursive: true });

function serve() {
  const types = { '.html': 'text/html', '.js': 'text/javascript', '.wasm': 'application/wasm' };
  const srv = http.createServer((req, res) => {
    const u = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    if (req.method === 'PUT' && u.startsWith('/out/')) {
      const p = path.join(OUTDIR, u.slice(5));
      if (!p.startsWith(OUTDIR + path.sep)) { res.writeHead(403); res.end(); return; }
      fs.mkdirSync(path.dirname(p), { recursive: true });
      const chunks = [];
      req.on('data', (c) => chunks.push(c));
      req.on('end', () => { fs.writeFileSync(p, Buffer.concat(chunks)); res.writeHead(204); res.end(); });
      return;
    }
    let f = u === '/' ? '/f2_page/index.html' : u;
    if (f.startsWith('/data/')) f = '/data/cache/' + f.slice(6);
    const p = path.join(HERE, f);
    if (!p.startsWith(HERE) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'content-type': types[path.extname(p)] || 'application/octet-stream',
      'cross-origin-opener-policy': 'same-origin', 'cross-origin-embedder-policy': 'require-corp' });
    fs.createReadStream(p).pipe(res);
  });
  return new Promise((r) => srv.listen(0, '127.0.0.1', () => r(srv)));
}

async function launch(browser) {
  // As f1_run.mjs: the snap Firefox sees neither /tmp nor hidden directories under home.
  process.env.TMPDIR = browser === 'chrome' ? '/tmp'
    : path.join(process.env.HOME, 'snap/firefox/common/e001-f2-tmp');
  fs.mkdirSync(process.env.TMPDIR, { recursive: true });
  if (browser === 'chrome') return pw.chromium.launch({ channel: 'chrome', headless: true });
  return pw.firefox.launch({ channel: 'moz-firefox', executablePath: '/snap/bin/firefox', headless: true });
}

const srv = await serve();
const base = `http://127.0.0.1:${srv.address().port}/`;
for (const browser of browsers) {
  fs.rmSync(path.join(OUTDIR, browser), { recursive: true, force: true });
  const b = await launch(browser);
  const p = await b.newPage();
  p.on('console', (m) => console.log(`  ${browser}:`, m.text()));
  await p.goto(base);
  await p.waitForFunction(() => window.e001ready);
  const t0 = Date.now();
  const out = await p.evaluate((cfg) => window.e001.run(cfg), { browser });
  out.browser = browser; out.version = b.version(); out.wall_s = (Date.now() - t0) / 1000;
  fs.writeFileSync(path.join(HERE, `results/f2/${browser}.json`), JSON.stringify(out, null, 1));
  console.log(browser, b.version(), 'done in', out.wall_s, 's');
  await b.close();
}
srv.close();
if (browsers.includes('firefox')) fs.rmSync(path.join(process.env.HOME, 'snap/firefox/common/e001-f2-tmp'), { recursive: true, force: true });
