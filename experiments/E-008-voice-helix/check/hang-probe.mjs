// WebKit hang probe: starts the demo, tests whether the page still answers, and on a stall dumps every thread of the web process.
// Usage: node hang-probe.mjs <url> [runs] [init-js]
import { webkit, devices } from 'playwright';
import { execSync } from 'node:child_process';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
const url = process.argv[2], runs = +(process.argv[3] || 10), init = process.argv[4] || '';
const wkLibs = join(process.env.HOME, '.local/share/squillo/webkit-libs/root/usr/lib/x86_64-linux-gnu');
if (existsSync(wkLibs)) { process.env.PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS ??= '1'; process.env.GST_PLUGIN_PATH ??= join(wkLibs, 'gstreamer-1.0'); }
process.env.TMPDIR = '/tmp';
const MUTE = () => { const con = AudioNode.prototype.connect; AudioNode.prototype.connect = function (d, ...r) {
  if (typeof AudioDestinationNode !== 'undefined' && d instanceof AudioDestinationNode) { const c = d.context;
    if (!c.__mute) { c.__mute = c.createGain(); c.__mute.gain.value = 0; con.call(c.__mute, d); } con.call(this, c.__mute, ...r); return d; }
  return con.call(this, d, ...r); }; };
const kids = pid => { const o = execSync(`ps --ppid ${pid} -o pid=,comm= || true`).toString().trim().split('\n').filter(Boolean).map(l => l.trim().split(/\s+/)); return o.flatMap(([p, c]) => [[p, c], ...kids(p)]); };
let hung = 0;
for (let i = 0; i < runs; i++) {
  const b = await webkit.launch({ headless: true }), c = await b.newContext(devices['iPhone 15']);
  await c.addInitScript(MUTE); if (init) await c.addInitScript(init);
  const p = await c.newPage(); const t0 = Date.now();
  await p.goto(url, { waitUntil: 'load' }); await p.waitForTimeout(1500);
  await p.locator('#bDemo').tap(); await p.waitForTimeout(3000);
  let ok = true; const kind = await Promise.race([p.evaluate(() => AU.capKind + ' ' + AU.ctx.state + ' ' + LAT.n), new Promise(r => setTimeout(() => r('no answer'), 15000))]);
  for (let k = 0; k < 8 && ok; k++) { ok = await Promise.race([p.evaluate(() => 1).then(() => true), new Promise(r => setTimeout(() => r(false), 15000))]); await new Promise(r => setTimeout(r, 400)); }
  console.log(`run ${i}: ${ok ? 'ok' : 'HUNG'} ${kind} ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  if (!ok) { hung++; const ps = execSync('ps -eo pid=,comm=,args=', { maxBuffer: 1 << 26 }).toString().split('\n').filter(l => /WebKit|pw_run|minibrowser/i.test(l) && !/ (bash|node|claude|timeout|gdb|ps) /.test(l.slice(0, 40))); const all = ps.map(l => l.trim().split(/\s+/)[0]); const web = ps.filter(l => /WPEWebProcess/.test(l)).map(l => l.trim().split(/\s+/)[0]);
    const snap = pid => Object.fromEntries(readdirSync(`/proc/${pid}/task`).map(t => { const f = readFileSync(`/proc/${pid}/task/${t}/stat`, 'utf8'), r = f.slice(f.lastIndexOf(')') + 2).split(' '); let w = ''; try { w = readFileSync(`/proc/${pid}/task/${t}/wchan`, 'utf8'); } catch {} return [t, { comm: readFileSync(`/proc/${pid}/task/${t}/comm`, 'utf8').trim(), st: r[0], cpu: +r[11] + +r[12], w }]; }));
    if (process.env.THREADS) for (const pid of web) { const A = snap(pid); await new Promise(r => setTimeout(r, 3000)); const B = snap(pid); for (const t in B) console.log(pid, t, B[t].comm.padEnd(16), B[t].st, 'cpu+', A[t] ? B[t].cpu - A[t].cpu : '?', B[t].w); }
    await Promise.race([b.close(), new Promise(r => setTimeout(r, 5000))]); for (const pid of all) try { process.kill(+pid, 'SIGKILL'); } catch {} continue; }
  await Promise.race([b.close(), new Promise(r => setTimeout(r, 5000))]);
}
process.exit(0);
console.log(`hung ${hung} of ${runs}`);
