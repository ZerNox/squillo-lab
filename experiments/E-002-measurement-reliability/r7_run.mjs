// E-002 round 7, step 3: run wasm/pkg and wasm/pkg-simd in the installed
// Chrome and Firefox, headless, through Playwright, as E-001 round 2's
// r2_run.mjs. Crude experiment code.
// Usage: node r7_run.mjs [chrome|firefox ...] [--pkg pkg|pkg-simd ...] [--list <file under data/cache/r7>]
// Writes data/cache/r7/out/<browser>-<pkg>/<variant>/<name>.f64 and timing.json.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import pw from 'playwright';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const CACHE = path.join(HERE, 'data/cache/r7');
const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const LIST = opt('--list', 'in/list.txt');
const browsers = args.filter((a) => a === 'chrome' || a === 'firefox');
if (!browsers.length) browsers.push('chrome', 'firefox');
const pkgs = args.flatMap((a, i) => (args[i - 1] === '--pkg' ? [a] : []));
if (!pkgs.length) pkgs.push('pkg', 'pkg-simd');

function serve() {
  const types = { '.html': 'text/html', '.js': 'text/javascript', '.wasm': 'application/wasm' };
  const srv = http.createServer((req, res) => {
    const u = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    if (req.method === 'POST' && u.startsWith('/put/')) {
      const [target, variant, name] = u.slice(5).split('/');
      const dir = path.join(CACHE, 'out', target, variant);
      fs.mkdirSync(dir, { recursive: true });
      const chunks = [];
      req.on('data', (c) => chunks.push(c));
      req.on('end', () => { fs.writeFileSync(path.join(dir, `${name}.f64`), Buffer.concat(chunks)); res.writeHead(200); res.end(); });
      return;
    }
    let p;
    if (u === '/') p = path.join(HERE, 'r7_page/index.html');
    else if (u.startsWith('/r7/')) p = path.join(CACHE, u.slice(4));
    else p = path.join(HERE, u);
    if (!p.startsWith(HERE) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'content-type': types[path.extname(p)] || 'application/octet-stream' });
    fs.createReadStream(p).pipe(res);
  });
  return new Promise((r) => srv.listen(0, '127.0.0.1', () => r(srv)));
}

async function launch(browser) {
  // The snap Firefox sees neither /tmp nor hidden directories under home
  // (squillo-lab README, Tooling); its profile goes in the snap's own cache.
  process.env.TMPDIR = browser === 'chrome' ? '/tmp'
    : path.join(process.env.HOME, 'snap/firefox/common/e002-tmp');
  fs.mkdirSync(process.env.TMPDIR, { recursive: true });
  if (browser === 'chrome') return pw.chromium.launch({ channel: 'chrome', headless: true });
  return pw.firefox.launch({ channel: 'moz-firefox', executablePath: '/snap/bin/firefox', headless: true });
}

const srv = await serve();
const base = `http://127.0.0.1:${srv.address().port}/`;
for (const browser of browsers) {
  for (const pkg of pkgs) {
    const target = `${browser}-${pkg}`;
    const b = await launch(browser);
    const p = await b.newPage();
    p.on('console', (m) => console.log(`  ${target}:`, m.text()));
    await p.goto(base);
    await p.waitForFunction(() => window.e002ready);
    const t0 = Date.now();
    const out = await p.evaluate((cfg) => window.e002.run(cfg), { pkg, target, list: `/r7/${LIST}` });
    out.browser = browser; out.version = b.version(); out.pkg = pkg; out.wall_s = (Date.now() - t0) / 1000;
    fs.mkdirSync(path.join(CACHE, 'out', target), { recursive: true });
    fs.writeFileSync(path.join(CACHE, 'out', target, 'timing.json'), JSON.stringify(out, null, 1));
    console.log(target, b.version(), 'done in', out.wall_s, 's');
    await b.close();
  }
}
srv.close();
if (browsers.includes('firefox')) fs.rmSync(path.join(process.env.HOME, 'snap/firefox/common/e002-tmp'), { recursive: true, force: true });
