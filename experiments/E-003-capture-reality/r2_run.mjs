// E-003 round 2 runner (squillo iteration 47): each input WAV of r2_gen.py
// as Chrome's fake microphone, captured through page/r2.js under each
// request of the README's rule 2. Resumes: a capture whose .json exists is
// skipped. Usage: node r2_run.mjs [--jobs N] [--only N] [--sample]
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import pw from 'playwright';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const IN = path.join(HERE, 'data/cache/r2/in');
const CAP = path.join(HERE, 'data/cache/r2/cap');
fs.mkdirSync(CAP, { recursive: true });
const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? Number(args[i + 1]) : d; };
const JOBS = opt('--jobs', 4);
const ONLY = opt('--only', Infinity);

const rows = fs.readFileSync(path.join(IN, 'list.txt'), 'utf8').trim().split('\n').map((l) => {
  const [stem, cond, set, seconds] = l.split(' ');
  return { stem, cond, set, seconds: Number(seconds) };
});
let jobs = [];
for (const r of rows) {
  const reqs = ['raw', 'default'].concat(r.set === 'LT-straight' ? ['ec', 'ns', 'agc'] : []);
  for (const q of reqs) jobs.push({ ...r, request: q });
}
// --sample: two takes of each set, both conditions, raw and default (S19's timing)
if (args.includes('--sample')) {
  const pick = new Set();
  for (const s of ['LT-straight', 'LT-forte', 'LT-pp', 'LT-messa'])
    rows.filter((r) => r.set === s).slice(0, 2).forEach((r) => pick.add(r.stem));
  jobs = jobs.filter((j) => pick.has(j.stem) && (j.request === 'raw' || j.request === 'default'));
}
jobs = jobs.slice(0, ONLY);

const srv = http.createServer((req, res) => {
  const u = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  const p = path.join(HERE, u);
  if (!p.startsWith(path.join(HERE, 'page')) || !fs.existsSync(p)) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'content-type': p.endsWith('.html') ? 'text/html' : 'text/javascript' });
  fs.createReadStream(p).pipe(res);
});
await new Promise((r) => srv.listen(0, '127.0.0.1', r));
const base = `http://127.0.0.1:${srv.address().port}/page/r2.html`;
process.env.TMPDIR = '/tmp';

async function one(j) {
  const name = `${j.stem}.${j.cond}.${j.request}`;
  const jf = path.join(CAP, `${name}.json`);
  if (fs.existsSync(jf)) return 'skip';
  const wav = path.join(IN, `${j.stem}.${j.cond}.wav`);
  const b = await pw.chromium.launch({ channel: 'chrome', headless: true, args: [
    '--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream',
    `--use-file-for-fake-audio-capture=${wav}`, '--autoplay-policy=no-user-gesture-required'] });
  try {
    const p = await b.newPage();
    await p.goto(base);
    const out = await p.evaluate((c) => window.e003r2.capture(c), { request: j.request, seconds: j.seconds + 0.5 });
    out.version = b.version(); out.job = j;
    if (out.samples) {
      fs.writeFileSync(path.join(CAP, `${name}.f32`), Buffer.from(out.samples, 'base64'));
      delete out.samples;
    }
    fs.writeFileSync(jf, JSON.stringify(out));
    return 'ok';
  } finally { await b.close(); }
}

const t0 = Date.now();
let next = 0, done = 0;
async function worker() {
  while (next < jobs.length) {
    const j = jobs[next++];
    let r;
    try { r = await one(j); } catch (e) { r = 'error ' + e; }
    done++;
    if (r !== 'skip') console.log(`${done}/${jobs.length} ${j.stem}.${j.cond}.${j.request} ${r} ${((Date.now() - t0) / 1000).toFixed(0)} s`);
  }
}
await Promise.all(Array.from({ length: JOBS }, worker));
console.log('jobs', jobs.length, 'wall s', ((Date.now() - t0) / 1000).toFixed(1));
srv.close();
