// E-001 fold 1 (squillo iteration 37): run WORLD in WASM in the installed Chrome and
// Firefox, headless, through Playwright. Crude experiment code.
// Usage: node r2_run.mjs [chrome|firefox ...] [--pkg pkg|pkg-simd ...] [--reps N]
// Writes results/f1/<browser>.json (plain WASM only; f1_page loads /wasm/pkg).
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import pw from 'playwright';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const REPS = Number(opt('--reps', 3));
const browsers = args.filter((a) => a === 'chrome' || a === 'firefox');
if (!browsers.length) browsers.push('chrome', 'firefox');
const pkgs = args.flatMap((a, i) => (args[i - 1] === '--pkg' ? [a] : []));
if (!pkgs.length) pkgs.push('pkg');
fs.mkdirSync(path.join(HERE, 'results/f1'), { recursive: true });

function serve() {
  const types = { '.html': 'text/html', '.js': 'text/javascript', '.wasm': 'application/wasm' };
  const srv = http.createServer((req, res) => {
    const u = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    let f = u === '/' ? '/f1_page/index.html' : u;
    if (f.startsWith('/data/')) f = '/data/cache/' + f.slice(6);
    const p = path.join(HERE, f);
    if (!p.startsWith(HERE) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
    // cross-origin isolated, for the finest performance.now() both browsers give
    res.writeHead(200, { 'content-type': types[path.extname(p)] || 'application/octet-stream',
      'cross-origin-opener-policy': 'same-origin', 'cross-origin-embedder-policy': 'require-corp' });
    fs.createReadStream(p).pipe(res);
  });
  return new Promise((r) => srv.listen(0, '127.0.0.1', () => r(srv)));
}

async function launch(browser) {
  // The snap Firefox sees neither /tmp nor hidden directories under home
  // (squillo-lab README, Browsers); its profile goes in the snap's own cache.
  process.env.TMPDIR = browser === 'chrome' ? '/tmp'
    : path.join(process.env.HOME, 'snap/firefox/common/e001-f1-tmp');
  fs.mkdirSync(process.env.TMPDIR, { recursive: true });
  if (browser === 'chrome') return pw.chromium.launch({ channel: 'chrome', headless: true });
  return pw.firefox.launch({ channel: 'moz-firefox', executablePath: '/snap/bin/firefox', headless: true });
}

const srv = await serve();
const base = `http://127.0.0.1:${srv.address().port}/`;
for (const browser of browsers) {
  for (const pkg of pkgs) {
    const b = await launch(browser);
    const p = await b.newPage();
    p.on('console', (m) => console.log(`  ${browser} ${pkg}:`, m.text()));
    await p.goto(base);
    await p.waitForFunction(() => window.e001ready);
    const t0 = Date.now();
    const out = await p.evaluate((cfg) => window.e001.run(cfg), { pkg });
    out.browser = browser; out.version = b.version(); out.pkg = pkg; 
    out.wall_s = (Date.now() - t0) / 1000;
    fs.writeFileSync(path.join(HERE, `results/f1/${browser}.json`), JSON.stringify(out, null, 1));
    console.log(browser, b.version(), pkg, 'done in', out.wall_s, 's; isolated', out.crossOriginIsolated);
    await b.close();
  }
}
srv.close();
if (browsers.includes('firefox')) fs.rmSync(path.join(process.env.HOME, 'snap/firefox/common/e001-f1-tmp'), { recursive: true, force: true });
