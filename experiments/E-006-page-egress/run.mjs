// E-006 runner: serves the probe page under each condition from rules.mjs,
// with a logger on a second origin, and drives the installed Chrome and Firefox.
// Usage: node run.mjs [--sample]   (--sample: rep 0 of every cell, to
// data/cache/sample, allowed before the rules are committed, for timing only)
import http from 'node:http';
import dgram from 'node:dgram';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execSync } from 'node:child_process';
import pw from 'playwright';
import * as R from './rules.mjs';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const SAMPLE = process.argv.includes('--sample');
if (!SAMPLE) {
  for (const f of ['rules.mjs', 'run.mjs', 'analyze.mjs', 'page']) {
    try { execSync(`git diff --quiet HEAD -- ${f}`, { cwd: HERE }); }
    catch { throw new Error(`${f} has uncommitted edits: commit the rules first (S15, L-047)`); }
  }
}
const OUT = path.join(HERE, 'data/cache', SAMPLE ? 'sample' : 'runs');
fs.mkdirSync(OUT, { recursive: true });
const LAN = Object.values(os.networkInterfaces()).flat().find((i) => i.family === 'IPv4' && !i.internal)?.address;
const listen = (s, host) => new Promise((r) => s.listen(0, host, () => r(s.address().port)));

function pageServer(cond, log) {
  const c = R.CONDITIONS[cond];
  const engine = fs.readFileSync(path.join(HERE, 'page/engine.js'), 'utf8');
  const files = {
    '/': ['text/html', `<!doctype html><html><head>${c.meta ? `<meta http-equiv="Content-Security-Policy" content="${c.meta}">` : ''}`
      + '<title>E-006</title><script src="/app.js"></script></head><body></body></html>'],
    '/app.js': ['text/javascript', `const ENGINE_SRC = ${JSON.stringify(engine)};\n` + fs.readFileSync(path.join(HERE, 'page/app.js'), 'utf8')],
    '/engine.js': ['text/javascript', engine],
    '/worklet.js': ['text/javascript', fs.readFileSync(path.join(HERE, 'page/worklet.js'), 'utf8')],
  };
  return http.createServer((req, res) => {
    const p = new URL(req.url, 'http://x').pathname;
    log.push(p);
    const f = files[p];
    if (!f) { res.writeHead(404); res.end(); return; }
    const h = { 'content-type': f[0] };
    if (c.header) h['content-security-policy'] = c.header;
    res.writeHead(200, h); res.end(f[1]);
  });
}
function logger(log) {
  const s = http.createServer((req, res) => {
    log.push(new URL(req.url, 'http://x').pathname);
    if (req.headers.accept === 'text/event-stream') { res.writeHead(200, { 'content-type': 'text/event-stream' }); res.end(); return; }
    res.writeHead(200, { 'content-type': 'text/plain', 'access-control-allow-origin': '*' }); res.end('');
  });
  s.on('upgrade', (req, sock) => { log.push(new URL(req.url, 'http://x').pathname); sock.destroy(); });
  return s;
}
async function launch(browser) {
  process.env.TMPDIR = browser === 'chrome' ? '/tmp' : path.join(process.env.HOME, 'snap/firefox/common/e006-tmp');
  fs.mkdirSync(process.env.TMPDIR, { recursive: true });
  if (browser === 'chrome') {
    return pw.chromium.launch({ channel: 'chrome', headless: true, args: ['--autoplay-policy=no-user-gesture-required'] });
  }
  return pw.firefox.launch({ channel: 'moz-firefox', executablePath: '/snap/bin/firefox', headless: true,
    firefoxUserPrefs: { 'media.autoplay.default': 0, 'media.autoplay.block-webaudio': false } });
}
const get = (u) => new Promise((r) => http.get(u, (res) => { res.resume(); res.on('end', r); }).on('error', r));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

for (const browser of R.BROWSERS) for (const cond of Object.keys(R.CONDITIONS)) for (const mode of R.WORKER_MODES)
  for (let rep = 0; rep < (SAMPLE ? 1 : R.REPS); rep++) {
    const name = `${browser}-${cond}-${mode}-r${rep}`;
    const t0 = Date.now();
    const own = [], hits = [], udp = [];
    const ps = pageServer(cond, own), ls = logger(hits), us = dgram.createSocket('udp4');
    us.on('message', (m, rinfo) => udp.push({ from: rinfo.address, bytes: m.length }));
    const pport = await listen(ps, '127.0.0.1'), lport = await listen(ls, '0.0.0.0');
    const uport = await new Promise((r) => us.bind(0, '0.0.0.0', () => r(us.address().port)));
    const LOG = `http://127.0.0.1:${lport}`;
    // K0: the logger check, checked
    await get(`${LOG}/${name}/control/node`);
    const b = await launch(browser);
    const out = { name, browser, version: b.version(), cond, mode, rep, udpBeforePage: udp.length };
    try {
      const p = await b.newPage();
      const stun = [`127.0.0.1:${uport}`, `${LAN}:${uport}`].join(',');
      await p.goto(`http://127.0.0.1:${pport}/?logger=${encodeURIComponent(LOG)}&run=${name}&mode=${mode}&stun=${stun}&ice=${R.ICE_WAIT_MS}`);
      out.page = await p.evaluate(([d, w]) => window.e006(d, w), [R.DOC_PROBES, R.WORKER_PROBES]);
      await sleep(R.SETTLE_MS);
      out.hitsBeforeNav = [...hits];
      out.udpBeforeNav = udp.length;
      await p.evaluate(() => window.e006nav()).catch(() => {});
      await sleep(R.NAV_SETTLE_MS);
    } catch (e) { out.error = String(e); }
    await b.close();
    Object.assign(out, { own, hits, udp, lan: LAN, wallS: (Date.now() - t0) / 1000 });
    fs.writeFileSync(path.join(OUT, `${name}.json`), JSON.stringify(out, null, 1));
    console.log(name, out.error || '', `hits ${hits.length} udp ${udp.length}`, `${out.wallS}s`);
    ps.close(); ls.close(); us.close();
  }
