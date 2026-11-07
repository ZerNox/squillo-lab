// Checks the Voice Helix page in Chrome (desktop), Firefox (desktop) and WebKit at an iPhone 15's
// size and touch: the page loads without errors, a public-domain reference clip loads as the take,
// the take is scanned (performance timeline, summary, progress lines over seeded earlier takes), a tap on the timeline plays from there, a tap on a spot loops it A/B with spotless, 0.5x playback keeps the pitch, the reference's scoops are not taken for a slide style, the take pitch tracker holds a breathy tone, the warm-up targets the seeded takes' weakest aspects and plays a guide tone, the voice profile reads the seeded range and suggests a key around the seeded register break, the range finder reads a synthetic A2-A4, an earlier take kept on the device plays for comparison, the summary states the real-voice pitch accuracy, and
// "spotless" plays. Screenshots go to the out directory; look at them.
// Usage: node check.mjs <url> [--wait <sha256 of page/index.html>] [--only chrome|firefox|webkit-iphone] [--out dir] [--headed] [--slow ms] [--hold s]
// --headed opens visible, maximized browser windows (menu bar and dock stay) on this machine's display (default headless, as
// the runner needs; WebKit keeps the iPhone 15 viewport, so its window stays phone-sized). Headless runs
// are muted (they used to play takes through the speakers); --sound unmutes, --mute mutes a headed run; --slow slows every action by ms; --hold keeps each browser open s seconds at the end to look.
// --wait polls the URL until it serves that index.html (a deploy from main takes 1-3 min).
// Prints one JSON line per browser; exit 0 = every browser passed. WebKit on Linux is not a real
// iPhone (no H.264/AAC, different audio stack): name any iOS-only risk separately.
import { chromium, firefox, webkit, devices } from 'playwright';
import { createHash } from 'node:crypto';
import { copyFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2), url = args[0];
const opt = k => { const i = args.indexOf(k); return i > 0 ? args[i + 1] : undefined; };
const headed = args.includes('--headed') || process.env.HEADED === '1', slowMo = +(opt('--slow') || 0), hold = +(opt('--hold') || 0);
const mute = args.includes('--mute') || (!headed && !args.includes('--sound'));
const L = o => ({ ...o, headless: !headed, slowMo });
// Headed Chrome and Firefox fill the screen: no fixed viewport, maximized (Chrome) or sized to the screen (Firefox has no maximize switch).
const FULL = headed ? { viewport: null } : {};
// Firefox has no maximize switch: headed, it runs on a fresh profile whose saved window state
// (xulstore.json) says maximized.
const fxMax = async (o) => { mkdirSync(fxDir, { recursive: true }); const dir = mkdtempSync(join(fxDir, 'profile-'));
  writeFileSync(join(dir, 'xulstore.json'), JSON.stringify({ 'chrome://browser/content/browser.xhtml': { 'main-window': { sizemode: 'maximized' } } }));
  const ctx = await firefox.launchPersistentContext(dir, { ...o, viewport: null });
  return { newContext: async () => ctx, close: async () => { await ctx.close(); rmSync(dir, { recursive: true, force: true }); } }; };
// Headed WebKit crashes this machine's GPU through its DMA-BUF renderer; the page is not at fault.
if (headed) process.env.WEBKIT_DISABLE_DMABUF_RENDERER ??= '1';
// Mute: every connection to the speakers goes through a gain of 0, so the audio graph runs as usual.
const MUTE = () => { const con = AudioNode.prototype.connect; AudioNode.prototype.connect = function (d, ...r) {
  if (typeof AudioDestinationNode !== 'undefined' && d instanceof AudioDestinationNode) { const c = d.context;
    if (c instanceof OfflineAudioContext) return con.call(this, d, ...r); if (!c.__mute) { c.__mute = c.createGain(); c.__mute.gain.value = 0; con.call(c.__mute, d); } con.call(this, c.__mute, ...r); return d; }
  return con.call(this, d, ...r); }; };
// Close every browser if the check is killed (a timeout), so none is left running and playing.
const open = new Set();
for (const sig of ['SIGTERM', 'SIGINT', 'SIGHUP']) process.on(sig, async () => { await Promise.all([...open].map(b => b.close().catch(() => {}))); process.exit(130); });
const out = opt('--out') || '/tmp/voice-helix-check', only = opt('--only'), want = opt('--wait');
mkdirSync(out, { recursive: true });
const wkLibs = join(process.env.HOME, '.local/share/squillo/webkit-libs/root/usr/lib/x86_64-linux-gnu');
if (existsSync(wkLibs)) { process.env.PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS ??= '1'; process.env.GST_PLUGIN_PATH ??= join(wkLibs, 'gstreamer-1.0'); }

if (want) {
  let got = '';
  for (let i = 0; i < 60 && got !== want; i++) {
    try { const r = await fetch(`${url}?nocache=${Date.now()}`, { cache: 'no-store' }); got = createHash('sha256').update(Buffer.from(await r.arrayBuffer())).digest('hex'); } catch {}
    if (got !== want) await new Promise(r => setTimeout(r, 10000));
  }
  if (got !== want) { console.log(JSON.stringify({ ok: false, reason: `site never served index.html ${want.slice(0, 12)} (got ${got.slice(0, 12)})` })); process.exit(1); }
}

const clip = join(here, '../page/ref/polished.mp3');
// Snap Firefox can only read files under ~/snap/firefox/common.
const snapFx = '/snap/bin/firefox', fxDir = join(process.env.HOME, 'snap/firefox/common/voice-helix-check');
const browsers = [
  ['chrome', () => chromium.launch(L({ channel: 'chrome', args: headed ? ['--start-maximized'] : [] })).catch(() => chromium.launch(L({ args: headed ? ['--start-maximized'] : [] }))), FULL, clip],
  ['firefox', () => {
    const prefs = { 'media.autoplay.default': 0, 'media.autoplay.block-webaudio': false };
    const o = existsSync(snapFx) ? L({ channel: 'moz-firefox', executablePath: snapFx, firefoxUserPrefs: prefs }) : L({ firefoxUserPrefs: prefs });
    if (existsSync(snapFx)) process.env.TMPDIR = fxDir;
    return headed ? fxMax(o) : firefox.launch(o);
  }, {}, existsSync(snapFx) ? join(fxDir, 'polished.mp3') : clip],
  ['webkit-iphone', () => { process.env.TMPDIR = '/tmp'; return webkit.launch(L({})); }, devices['iPhone 15'], clip],
].filter(b => !only || b[0] === only);
if (existsSync(snapFx)) { mkdirSync(fxDir, { recursive: true }); copyFileSync(clip, join(fxDir, 'polished.mp3')); }

async function run([name, launch, ctxOpt, file]) {
  const errs = []; let b;
  try {
    b = await launch(); open.add(b);
    const c = await b.newContext(ctxOpt);
    if (mute) await c.addInitScript(MUTE);
    // Seven earlier takes on the device, so the progress lines have a history to slide over.
    await c.addInitScript(() => { try { if (!localStorage.getItem('helix.takes.v1')) localStorage.setItem('helix.takes.v1', JSON.stringify(Array.from({ length: 7 }, (_, i) => ({ d: Date.now() - (7 - i) * 864e5, sung: 30, score: 0.6 + 0.02 * i, inton: 25 - i, stab: 5 - 0.2 * i, onset: 0.2, clar: 25, lo: 52, hi: 62, mn: 48, mx: 67, br: [60.2] })))); } catch (e) {} });
    const p = await c.newPage(), ext = []; p.on('request', q => { if (/^https?:/.test(q.url()) && new URL(q.url()).origin !== new URL(url).origin) ext.push(q.url()); });
    if (headed) console.error(name, 'window', await p.evaluate(() => [outerWidth, outerHeight, screen.availWidth, screen.availHeight].join(' ')));
    p.on('pageerror', e => errs.push(String(e)));
    if (process.env.TRACE) { const t0 = Date.now(); for (const m of ['evaluate', 'waitForFunction', 'goto', 'setInputFiles']) { const f = p[m].bind(p); p[m] = (...a) => { console.error(`[${((Date.now() - t0) / 1000).toFixed(1)}s] ${m} ${String(a[0]).slice(0, 70).replace(/\s+/g, ' ')}`); return f(...a); }; } }
    p.on('console', m => { if (m.type() === 'error' && !/favicon/.test(m.location().url)) errs.push(m.text()); });
    await p.goto(url, { waitUntil: 'load' }); await p.waitForTimeout(1500);
    await p.screenshot({ path: join(out, `${name}-start.png`) });
    const touch = !!ctxOpt.hasTouch, tap = l => touch ? l.tap() : l.click();
    // Screen lag: the demo voice runs live 3 s; the chip shows the measured audio-to-paint lag (median, p90).
    await tap(p.locator('#bDemo')); await p.waitForTimeout(3000);
    // Capture stays on the worklet in every browser (the fallback would hide a WebKit deadlock), and the context runs after its suspended setup.
    { const cap = await p.evaluate(() => [AU.capKind, AU.ctx.state]); if (cap[0] !== 'worklet' || cap[1] !== 'running') throw new Error('capture: ' + cap); }
    const lat = await p.evaluate(() => { const L = window.__lat(); return L && { med: Math.round(L.med), p90: Math.round(L.p90), n: L.n, chip: document.getElementById('mLat').textContent === String(L.med.toFixed(0)) || Math.abs(+document.getElementById('mLat').textContent - L.med) < 30 }; });
    // Tone colour: the tilt chip names a colour while the demo sings; the retired 'pressed' cue has no chip.
    const tone = await p.evaluate(() => /· (bright, belt-like|balanced|soft, airy)$/.test(document.getElementById('mTiltU').textContent) && ![...document.querySelectorAll('#flaws .flaw')].some(b => /pressed/.test(b.textContent)));
    // Say my note: N (tap on phone) turns it on; within 2 s of the steady demo the live region names a note and its cents; ? opens the key list, Esc closes it.
    if (touch) await tap(p.locator('#bSay')); else await p.keyboard.press('n');
    await p.waitForTimeout(2000);
    const say = await p.evaluate(() => ({ t: document.getElementById('say').textContent, on: document.getElementById('bSay').getAttribute('aria-pressed') === 'true' }));
    if (!touch) { await p.keyboard.press('?'); say.keys = await p.evaluate(() => !document.getElementById('keys').hidden); await p.keyboard.press('Escape'); say.keys = say.keys && await p.evaluate(() => document.getElementById('keys').hidden); } else say.keys = true;
    say.ok = say.on && /^[A-G]#?-?\d(, target [A-G]#?\d)?, (in tune|\d+ cents (sharp|flat))$/.test(say.t) && say.keys;
    await tap(p.locator('#bSay'));
    await p.locator('#rail').screenshot({ path: join(out, `${name}-lag.png`) }).catch(() => {});
    // Lane: the demo's steady note appears in big letters with cents and ±, the rail steps aside; a screenshot while it sings.
    await tap(p.locator('#vLane')); await p.waitForTimeout(1800);
    const lane = await p.evaluate(() => ({ note: document.getElementById('laneNote').textContent, c: document.getElementById('laneC').textContent, rail: getComputedStyle(document.getElementById('rail')).display, cv: getComputedStyle(document.getElementById('lane')).display, ink: (() => { const c = document.getElementById('lane'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let n = 0; for (let i = 0; i < d.length; i += 4) if (d[i + 1] > 180 && d[i] < 120) n++; return n; })() }));
    await p.screenshot({ path: join(out, `${name}-lane.png`) });
    // Drone: starts on the target note in the Lane's reach, follows a new target, stops.
    const roomGate = await p.evaluate(() => new Promise(res => { const sr = 44100, L = sr * 3, x = new Float32Array(L); let seed = 7; const R = () => (seed = seed * 16807 % 2147483647) / 2147483647 * 2 - 1; for (let i = 0; i < L; i++) x[i] = 0.03 * R() + (i > 2.2 * sr ? 0.04 * Math.sin(2 * Math.PI * 220 * i / sr) + 0.02 * Math.sin(4 * Math.PI * 220 * i / sr) : 0);
      const fs = [], d = makeDsp(m => { if (m.type === 'feat') fs.push(m); else if (m.type === 'pong') { d.kill(); const v = fs.filter(f => f.t > 2.4 && f.voiced && Math.abs(f.f0 - 220) < 5).length, n = fs.filter(f => f.t > 2.4).length; res({ v, n }); } }); d.post({ type: 'init', sr, hop: 0.02 }); d.post({ type: 'calib', seconds: 2 }); for (let i = 0; i < L; i += 441) { const c = x.slice(i, i + 441); d.post({ type: 'audio', buf: c }, [c.buffer]); } d.post({ type: 'ping' }); }));
    if (!(roomGate.n > 20 && roomGate.v > roomGate.n * 0.6)) throw new Error('live pitch in room noise: ' + JSON.stringify(roomGate));
    const drone = await p.evaluate(async () => { const B = document.getElementById('bDrone'), T = document.getElementById('tNote'), keep = T.value; T.value = '60'; T.dispatchEvent(new Event('change')); B.click(); await new Promise(r => setTimeout(r, 300)); const a = { on: DRONE.on, st: DRONE.ctx.state, f: DRONE.o[0].frequency.value, label: B.textContent }; T.value = '62'; T.dispatchEvent(new Event('change')); const m = DRONE.m; B.click(); const off = DRONE.on; T.value = keep; T.dispatchEvent(new Event('change')); return { ...a, m, off }; });
    if (!drone.on || drone.st !== 'running' || Math.abs(drone.f - 261.63) > 0.1 || drone.label !== '♪ C4' || drone.m !== 62 || drone.off) throw new Error('drone: ' + JSON.stringify(drone));
    if (!/^[A-G]♯?\d$/.test(lane.note) || !/±/.test(lane.c) || lane.rail !== 'none' || lane.cv !== 'block' || lane.ink < 100) throw new Error('lane: ' + JSON.stringify(lane));
    // Live note endings: a 1 s note whose last 0.2 s falls 80 ¢ is named as falling once it stops; a level one reads 'held'; nothing while it sounds.
    const lend = await p.evaluate(() => { const mk = D => { const h = []; for (let t = 0; t <= 1; t += 0.01) h.push({ t, voiced: true, ok: true, midi: 60 + D / 100 * Math.max(0, (t - 0.8) / 0.2) }); return h; };
      const f = laneEnd(mk(-80), 1.2), l = laneEnd(mk(0), 1.2); return { f: laneEndText(f), l: laneEndText(l), during: laneEnd(mk(-80), 1.0), el: !!document.querySelector('#laneRead #laneEnd') }; });
    if (!/^last note fell \d+ ¢ as you let go · ±\d+$/.test(lend.f) || lend.l !== 'last note held to the end' || lend.during !== null || !lend.el) throw new Error('lane note end: ' + JSON.stringify(lend));
    // Live note starts: a note that comes in 80 ¢ under and slides up over 0.25 s is named while it sounds; a level one 'landed'.
    const lst = await p.evaluate(() => { const mk = D => { const h = []; for (let t = 0; t <= 0.7; t += 0.01) h.push({ t, voiced: true, ok: true, midi: 60 + D / 100 * Math.max(0, 1 - t / 0.25) ** 2 }); return h; };
      return { u: laneStartText(laneStart(mk(-80), 0.7)), l: laneStartText(laneStart(mk(0), 0.7)), early: laneStart(mk(-80).filter(h => h.t <= 0.3), 0.3), el: !!document.querySelector('#laneRead #laneStart') }; });
    if (!/^came in \d+ ¢ under, then found it · ±\d+$/.test(lst.u) || lst.l !== 'landed right on the note' || lst.early !== null || !lst.el) throw new Error('lane note start: ' + JSON.stringify(lst));
    // Live vibrato: a 1.5 s note at 5.5 Hz, ±0.5 st is named with its rate once it stops; a straight one 'held straight'.
    const lvb = await p.evaluate(() => { const mk = w => { const h = []; for (let t = 0; t <= 1.5; t += 0.02) h.push({ t, voiced: true, ok: true, midi: 60 + w * Math.sin(2 * Math.PI * 5.5 * t) }); return h; };
      return { v: laneVibText(laneVib(mk(0.5), 1.7)), s: laneVibText(laneVib(mk(0), 1.7)), el: !!document.querySelector('#laneRead #laneVib') }; });
    if (!/^vibrato 5\.[45] Hz ±\d\.\d · 0\.\d\d st wide, even$/.test(lvb.v) || lvb.s !== 'held straight, no vibrato' || !lvb.el) throw new Error('lane vibrato: ' + JSON.stringify(lvb));
    // Live steadiness: a 1.5 s note's wobble (frames' fit residual) is named once it stops; after a 4 ¢ note a 1 ¢ one is 'your steadiest', a second 4 ¢ one is not.
    const lsd = await p.evaluate(() => { const mk = (r, t0) => { const h = []; for (let t = 0; t <= 1.5; t += 0.02) h.push({ t: t0 + t, voiced: true, ok: true, midi: 60, fit: true, res: r * (0.6 + 0.8 * ((t * 50) % 7) / 6) }); return h; };
      const w = laneSteady(mk(4, 0), 1.7), s = laneSteady(mk(1, 10), 11.7), w2 = laneSteady(mk(4, 10), 11.7);
      return { w: laneSteadyText(w, []).s, s: laneSteadyText(s, [w]), w2: laneSteadyText(w2, [w]).best, dv: laneSteadyText(s, [], { n: 3, bw: 4 }).s, dv1: laneSteadyText(s, [], { n: 1, bw: 4 }).best, dvN: laneSteadyText(w2, [], { n: 3, bw: 4 }).best, during: laneSteady(mk(4, 0), 1.5), el: !!document.querySelector('#laneRead #laneSteady') }; });
    if (!/^steadiness \d\.\d ¢ wobble · ±\d\.\d$/.test(lsd.w) || !lsd.s.best || !/your steadiest of 2 long notes$/.test(lsd.s.s) || lsd.w2 || !/steadier than any long note in your 3 kept takes \(best 4\.0 ¢\)$/.test(lsd.dv) || lsd.dv1 || lsd.dvN || lsd.during !== null || !lsd.el) throw new Error('lane steadiness: ' + JSON.stringify(lsd));
    // Live swell: a 1.5 s note swelling 20 dB soft-loud-soft is named a messa di voce with its peak near the middle; a level one 'held level'.
    const lsw = await p.evaluate(() => { const mk = D => { const h = []; for (let t = 0; t <= 1.5; t += 0.02) h.push({ t, voiced: true, ok: true, midi: 60, rms: 0.1 * 10 ** (D * (1 - Math.cos(2 * Math.PI * t / 1.5)) / 2 / 20) }); return h; };
      return { s: laneSwellText(laneSwell(mk(20), 1.7)), l: laneSwellText(laneSwell(mk(0), 1.7)).s, during: laneSwell(mk(20), 1.5), el: !!document.querySelector('#laneRead #laneSwell') }; });
    if (!/^swell 1\d dB ±\d, peak near the middle, a real messa di voce$/.test(lsw.s.s) || !lsw.s.real || !/^held level · 0 dB ±\d$/.test(lsw.l) || lsw.during !== null || !lsw.el) throw new Error('lane swell: ' + JSON.stringify(lsw));
    // After-note recap: a 1.5 s vibrato note with a 20 dB swell is read as one sentence 0.3 s after it stops, not while it sounds or at 0.1 s.
    const rcp = await p.evaluate(() => { const h = []; for (let t = 0; t <= 1.5; t += 0.02) h.push({ t, voiced: true, ok: true, midi: 60 + 0.5 * Math.sin(2 * Math.PI * 5.5 * t), rms: 0.1 * 10 ** (20 * (1 - Math.cos(2 * Math.PI * t / 1.5)) / 2 / 20) });
      return { r: noteRecap(h, 1.9, [], null), during: noteRecap(h, 1.5, [], null), early: noteRecap(h, 1.6, [], null) }; });
    if (!rcp.r || !/^Last note: .*vibrato 5\.[45] Hz.*; swell 1\d dB.*\.$/.test(rcp.r.s) || rcp.during !== null || rcp.early !== null) throw new Error('note recap: ' + JSON.stringify(rcp));
    // Long notes this sitting: the recap goes on the list beside the Lane once (same note twice is one line), with note name and length; visible in the Lane.
    const llog = await p.evaluate(() => { const h = []; for (let t = 0; t <= 1.5; t += 0.02) h.push({ t: 100 + t, voiced: true, ok: true, midi: 60 + 0.5 * Math.sin(2 * Math.PI * 5.5 * t), rms: 0.1 }); const r = noteRecap(h, 101.9, [], null); logRecap(r); logRecap(noteRecap(h, 102.2, [], null));
      const el = document.getElementById('laneLog'), li = el.querySelectorAll('li'); return { n: [...li].filter(x => x.textContent.startsWith('C4 1.5 s · ')).length, first: li[0] && li[0].textContent, vis: getComputedStyle(el).display }; });
    if (llog.n !== 1 || !/^C4 1\.5 s · .*vibrato 5\.[45] Hz/.test(llog.first) || llog.vis !== 'block') throw new Error('lane log: ' + JSON.stringify(llog));
    // Long notes across days: same wobble says level, half says steadier, under 3 notes a side says nothing; a recap with a steadiness reading is kept and the line shows.
    const ldays = await p.evaluate(() => { const now = new Date().setHours(12, 0, 0, 0), E = [1.9, 2.1, 2.0, 2.2, 1.8].map((w, i) => ({ d: now - 2 * 864e5 - i * 6e4, wob: w })), T = w => [0, 1, 2, 3].map(i => ({ d: now - i * 6e4, wob: w * (1 + 0.05 * (i % 2)) }));
      const lv = laneDays(E.concat(T(2)), now).v, st = laneDays(E.concat(T(1)), now).v, few = laneDays(E.concat(T(1).slice(0, 2)), now).s; const S = (a, b) => [a, a, b, b].map((c, i) => ({ d: now - (i < 2 ? 3 * 864e5 : 6e4) - i * 6e4, en: c })), held = laneDays(S(60, 5).concat(S(62, 4)), now, 'en'), flat = laneDays(S(30, 31).concat(S(32, 29)), now, 'en');
      localStorage.setItem(LN_KEY, JSON.stringify(E.concat(T(1).slice(0, 3)))); logRecap({ t: 500, s: 'x', n: 'A3', d: 1.4, p: ['steadiness 1.0 ¢ wobble · ±0.2'], w: { wob: 1.0, pm: 0.2 }, best: false });
      const kept = JSON.parse(localStorage.getItem(LN_KEY)).length, line = (document.querySelector('#laneLog .days') || {}).textContent || ''; localStorage.removeItem(LN_KEY); return { lv, st, few, kept, line, held: held.v + '|' + held.good, flat: flat.v }; });
    if (ldays.lv !== 'level with' || ldays.st !== 'steadier than' || ldays.few !== '' || ldays.held !== 'held better than|true' || ldays.flat !== 'endings level with' || ldays.kept !== 9 || !/^Today's 4 long notes steadier than your 5 from the last two weeks: wobble 1\.\d ¢/.test(ldays.line)) throw new Error('lane days: ' + JSON.stringify(ldays));
    // By note: C4 clearly steadier than the rest is named, all alike names nothing, one note name says nothing; the line shows in the Lane's list.
    const lbn = await p.evaluate(() => { const now = new Date().setHours(12, 0, 0, 0), mk = (n, ws) => ws.map((w, i) => ({ d: now - (i + 1) * 864e5, n, wob: w }));
      const A = mk('A3', [8, 9, 8.5, 7.5]), E = mk('E4', [8.2, 7.8, 9, 8.6]), C = mk('C4', [2, 2.2, 1.9, 2.1]), one = laneByNote(A, now).s, same = laneByNote(A.concat(E), now).s, q = laneByNote(A.concat(E, C), now);
      localStorage.setItem(LN_KEY, JSON.stringify(A.concat(E, C))); logRecap({ t: 520, s: 'x', n: 'A3', d: 1.4, p: ['steadiness 8.0 ¢ wobble · ±1'], w: { wob: 8, pm: 1 }, best: false });
      const line = (document.querySelector('#laneLog .bynote') || {}).textContent || ''; localStorage.removeItem(LN_KEY); return { one, same, lo: q.lo, hi: q.hi, line }; });
    if (lbn.one !== '' || lbn.same !== '' || lbn.lo !== 'C4' || !/^By note, last two weeks: steadiest on C4: wobble 2\.0 ¢/.test(lbn.line)) throw new Error('lane by note: ' + JSON.stringify(lbn));
    // Hear it again: mic audio kept 30 s in memory; a recapped note's ▶ cuts its own samples (padded 0.15 s), 'gone' once overwritten; notes heard back while ▶ plays are kept off the list.
    const lhr = await p.evaluate(() => { const k0 = AU.kind, sr0 = AU.sr, at0 = LIVE.at; AU.kind = 'mic'; AU.sr = 48000; LRING.b = null; LRING.mute = -1; const blk = n0 => { const b = new Float32Array(480); for (let i = 0; i < 480; i++) b[i] = (n0 + i) / 2e6; return b; };
      for (let j = 0; j < 1000; j++) liveTap(blk(j * 480)); LIVE.at = 10; LOG8.length = 0; logRecap({ t: 9, s: 'x', n: 'C4', d: 2, c: 40, p: ['held to the end'], best: false }); const q = LOG8[0], x = liveClip(q), first = Math.round(x[0] * 2e6), last = Math.round(x[x.length - 1] * 2e6);
      const btn = !!document.querySelector('#laneLog .hearln[data-i="0"]'); const tb = document.querySelector('#laneLog .tuneln[data-i="0"]'), tun = !!tb && /40 cents sharp/.test(tb.getAttribute('aria-label')) && /40 ¢ sharp/.test(document.querySelector('#laneLog li').textContent); let rate = null; if (AU.ctx) { hearLive(0, tb, true); rate = LRING.lastRate; } let slow = document.querySelector('#laneLog .slowln[data-i="0"]') ? 'btn' : null; if (slow && AU.ctx) { hearLive(0, document.querySelector('#laneLog .slowln'), 'slow'); slow = LRING.lastSlow; } let save = null; { const sb = document.querySelector('#laneLog .saveln[data-i="0"]'), x = liveClip(LOG8[0]); if (sb && x) { const c = mkBuf(x.length, LRING.sr); c.getChannelData(0).set(x); save = wavBlob(c).size === 44 + 2 * x.length; } } LRING.mute = 12; logRecap({ t: 11.5, s: 'x', n: 'D4', d: 1, p: ['held to the end'], best: false }); const muted = LOG8.length === 1; LRING.mute = -1; logRecap({ t: 9.6, s: 'x', n: 'E4', d: 0.3, c: 5, p: ['held to the end'], best: false }); const notun = !document.querySelector('#laneLog li .tuneln') || document.querySelectorAll('#laneLog .tuneln').length === 1 && !document.querySelector('#laneLog li:first-child .tuneln');
      Object.assign(LBEST, { x: null, t: -1, wob: Infinity }); LOG8.length = 0; LIVE.at = 20; logRecap({ t: 15, s: 'x', n: 'G4', d: 1.5, c: 0, w: { wob: 3, pm: 1 }, p: ['a'], best: false }); logRecap({ t: 18, s: 'x', n: 'A4', d: 1.5, c: 0, w: { wob: 9, pm: 1 }, p: ['b'], best: false }); const bb = document.querySelectorAll('#laneLog .bestln'), best1 = bb.length === 1 && bb[0].dataset.i === '0' && /G4 at 3.0 cents/.test(bb[0].getAttribute('aria-label')) && LBEST.n === 'G4'; let pair = null; if (AU.ctx) { hearLive(0, bb[0], 'best'); pair = LRING.lastPair; } LRING.mute = -1; logRecap({ t: 19.5, s: 'x', n: 'B4', d: 0.5, c: 0, w: { wob: 1, pm: 1 }, p: ['c'], best: false }); const best2 = LBEST.n === 'B4' && document.querySelectorAll('#laneLog .bestln').length === 2 && !document.querySelector('#laneLog li:first-child .bestln'); const ab = document.querySelector('#laneLog .hearall'); let all = ab ? 'btn' : null; if (ab && AU.ctx) { hearAll(ab); all = LRING.lastAll; } Object.assign(LBEST, { x: null, t: -1, wob: Infinity }); LOG8.length = 1; LOG8[0] = q;
      for (let j = 0; j < 3200; j++) liveTap(blk(0)); const gone = liveClip(q) === null; AU.kind = k0; AU.sr = sr0; LIVE.at = at0; LRING.b = null; LOG8.length = 0; localStorage.removeItem(LN_KEY); localStorage.removeItem(LNC_KEY); return { first, last, len: x.length, btn, muted, gone, tun, rate, notun, best1, best2, pair, all, slow, save }; });
    if (lhr.save === false || lhr.save == null && lhr.slow) throw new Error('lane save: ' + JSON.stringify(lhr.save)); if (Math.abs(lhr.first - 48000 * (9 - 2 - 0.15)) > 2 || Math.abs(lhr.last - (48000 * 9.15 - 1)) > 2 || !lhr.btn || !lhr.muted || !lhr.gone || !lhr.tun || !lhr.notun || !lhr.best1 || !lhr.best2 || !lhr.all || (Array.isArray(lhr.all) && lhr.all.join() !== '86400,86400,38400') || (lhr.pair && (lhr.pair[0] !== 86400 || lhr.pair[1] !== 86400)) || !lhr.slow || (Array.isArray(lhr.slow) && Math.abs(lhr.slow[1] - 2 * lhr.slow[0]) > 2) || (lhr.rate != null && Math.abs(lhr.rate - 2 ** (-40 / 1200)) > 1e-9)) throw new Error('lane hear again: ' + JSON.stringify(lhr));
    // Then held: a note whose ending fell 80 ¢ gets '▶ then held'; the ramped render, read back by zero crossings, ends within 15 ¢ of the body (was -80); a held ending gets no button.
    const lhd = await p.evaluate(async () => { const k0 = AU.kind, sr0 = AU.sr, at0 = LIVE.at; AU.kind = 'mic'; AU.sr = 48000; LRING.b = null; for (let j = 0; j < 4000; j++) liveTap(new Float32Array(480)); LIVE.at = 34; LOG8.length = 0; LRING.mute = -1; logRecap({ t: 30, s: 'x', n: 'A3', d: 1.5, c: 0, en: { c: -80, pm: 6, say: true }, p: ['fell 80 ¢'], best: false }); logRecap({ t: 33, s: 'x', n: 'B3', d: 1.5, c: 0, en: { c: 2, pm: 6, held: true, say: false }, p: ['held'], best: false });
      const btn = document.querySelectorAll('#laneLog .holdln'), one = btn.length === 1 && btn[0].dataset.i === '1' && /80 cents fallen/.test(btn[0].getAttribute('aria-label'));
      const sr = 48000, dur = 1.95, n = Math.round(dur * sr), z = dur - 0.15, f0 = 220, x = new Float32Array(n); let ph = 0; for (let i = 0; i < n; i++) { const t = i / sr, c = t < z - 0.3 ? 0 : -80 * Math.min(1, (t - (z - 0.3)) / 0.12); ph += 2 * Math.PI * f0 * 2 ** (c / 1200) / sr; x[i] = t < z ? Math.sin(ph) : 0; }
      const oc = new OfflineAudioContext(1, n + sr, sr), b = oc.createBuffer(1, n, sr); b.getChannelData(0).set(x); const s = oc.createBufferSource(); s.buffer = b; holdRamp(s.playbackRate, 0, dur, -80); s.connect(oc.destination);  s.start(0); const y = (await oc.startRendering()).getChannelData(0);
      const fq = (v, a, e) => { let k = 0, f = -1, l = -1; for (let i = Math.round(a * sr); i < Math.round(e * sr); i++) if (v[i - 1] < 0 && v[i] >= 0) { if (f < 0) f = i; l = i; k++; } return (k - 1) * sr / (l - f); };
      const zr = (() => { let i = y.length - 1; while (i > 0 && Math.abs(y[i]) < 1e-4) i--; return i / sr; })(), body = fq(y, 0.5, 1.2), end = fq(y, zr - 0.18, zr - 0.005), before = 1200 * Math.log2(fq(x, z - 0.18, z - 0.005) / fq(x, 0.5, 1.2));
      AU.kind = k0; AU.sr = sr0; LIVE.at = at0; LRING.b = null; LOG8.length = 0; return { one, before, after: 1200 * Math.log2(end / body), zr, body, end, ym: y.reduce((a, v) => Math.max(a, Math.abs(v)), 0), xm: x.reduce((a, v) => Math.max(a, Math.abs(v)), 0), yl: y.length }; });
    if (!lhd.one || lhd.before > -60 || !(Math.abs(lhd.after) <= 15)) throw new Error('lane then held: ' + JSON.stringify(lhd)); console.log('  lane then held: ending ' + lhd.before.toFixed(0) + ' → ' + lhd.after.toFixed(1) + ' ¢', JSON.stringify(lhd));
    // Then landed: a note that came in 80 ¢ under gets '▶ then landed'; the ramped render, read back by zero crossings, starts within 15 ¢ of the body (was -80); a clean start gets no button.
    const lld = await p.evaluate(async () => { const k0 = AU.kind, sr0 = AU.sr, at0 = LIVE.at; AU.kind = 'mic'; AU.sr = 48000; LRING.b = null; for (let j = 0; j < 4000; j++) liveTap(new Float32Array(480)); LIVE.at = 34; LOG8.length = 0; LRING.mute = -1; logRecap({ t: 30, s: 'x', n: 'A3', d: 1.5, c: 0, g: { c: -80, pm: 6, say: true }, p: ['came in 80 ¢ under'], best: false }); logRecap({ t: 33, s: 'x', n: 'B3', d: 1.5, c: 0, g: { c: 2, pm: 6, clean: true, say: false }, p: ['landed'], best: false });
      const btn = document.querySelectorAll('#laneLog .landln'), one = btn.length === 1 && btn[0].dataset.i === '1' && /80 cents under/.test(btn[0].getAttribute('aria-label'));
      const sr = 48000, dur = 1.95, n = Math.round(dur * sr), a = 0.15, f0 = 220, x = new Float32Array(n); let ph = 0; for (let i = 0; i < n; i++) { const t = i / sr, c = t < a + 0.1 ? -80 : t < a + 0.16 ? -80 * (1 - (t - a - 0.1) / 0.06) : 0; ph += 2 * Math.PI * f0 * 2 ** (c / 1200) / sr; x[i] = t >= a ? Math.sin(ph) : 0; }
      const oc = new OfflineAudioContext(1, n + sr, sr), b = oc.createBuffer(1, n, sr); b.getChannelData(0).set(x); const s = oc.createBufferSource(); s.buffer = b; landRamp(s.playbackRate, 0, -80); s.connect(oc.destination); s.start(0); const y = (await oc.startRendering()).getChannelData(0);
      const fq = (v, a, e) => { let k = 0, f = -1, l = -1; for (let i = Math.round(a * sr); i < Math.round(e * sr); i++) if (v[i - 1] < 0 && v[i] >= 0) { if (f < 0) f = i; l = i; k++; } return (k - 1) * sr / (l - f); };
      const za = (() => { let i = 1; while (i < y.length && Math.abs(y[i]) < 1e-4) i++; return i / sr; })(), body = fq(y, 0.6, 1.2), st = fq(y, za + 0.005, za + 0.09), before = 1200 * Math.log2(fq(x, a + 0.005, a + 0.09) / fq(x, 0.6, 1.2));
      AU.kind = k0; AU.sr = sr0; LIVE.at = at0; LRING.b = null; LOG8.length = 0; return { one, before, after: 1200 * Math.log2(st / body), za }; });
    if (!lld.one || lld.before > -60 || !(Math.abs(lld.after) <= 15)) throw new Error('lane then landed: ' + JSON.stringify(lld)); console.log('  lane then landed: start ' + lld.before.toFixed(0) + ' → ' + lld.after.toFixed(1) + ' ¢', JSON.stringify(lld));
    // All fixed: a note 30 ¢ sharp, coming in 80 ¢ under and falling 80 ¢ at the end gets '▶ all fixed' (one clean note gets none); the render, read back by zero crossings, has start, body and ending within 15 ¢ of A3.
    const lfx = await p.evaluate(async () => { const k0 = AU.kind, sr0 = AU.sr, at0 = LIVE.at; AU.kind = 'mic'; AU.sr = 48000; LRING.b = null; for (let j = 0; j < 4000; j++) liveTap(new Float32Array(480)); LIVE.at = 34; LOG8.length = 0; LRING.mute = -1; logRecap({ t: 30, s: 'x', n: 'A3', d: 1.5, c: 30, g: { c: -80, pm: 6, say: true }, en: { c: -80, pm: 6, say: true }, p: ['x'], best: false }); logRecap({ t: 33, s: 'x', n: 'B3', d: 1.5, c: 2, g: { c: -80, pm: 6, say: true }, p: ['y'], best: false });
      const btn = document.querySelectorAll('#laneLog .fixln'), one = btn.length === 1 && btn[0].dataset.i === '1' && /tuned and landed and held/.test(btn[0].getAttribute('aria-label')); let played = null; if (AU.ctx) { hearLive(1, btn[0], 'fix'); played = LRING.lastFix; }
      const sr = 48000, dur = 1.95, n = Math.round(dur * sr), a = 0.15, z = dur - 0.15, f0 = 220 * 2 ** (30 / 1200), x = new Float32Array(n); let ph = 0; for (let i = 0; i < n; i++) { const t = i / sr, c = t < a + 0.1 ? -80 : t < a + 0.16 ? -80 * (1 - (t - a - 0.1) / 0.06) : t < z - 0.3 ? 0 : -80 * Math.min(1, (t - (z - 0.3)) / 0.12); ph += 2 * Math.PI * f0 * 2 ** (c / 1200) / sr; x[i] = t >= a && t < z ? Math.sin(ph) : 0; }
      const oc = new OfflineAudioContext(1, n + sr, sr), b = oc.createBuffer(1, n, sr); b.getChannelData(0).set(x); const s = oc.createBufferSource(); s.buffer = b; fixRamp(s.playbackRate, 0, dur, fixParts(LOG8[1])); s.connect(oc.destination); s.start(0); const y = (await oc.startRendering()).getChannelData(0);
      const fq = (v, a, e) => { let k = 0, f = -1, l = -1; for (let i = Math.round(a * sr); i < Math.round(e * sr); i++) if (v[i - 1] < 0 && v[i] >= 0) { if (f < 0) f = i; l = i; k++; } return (k - 1) * sr / (l - f); }, ce = h => 1200 * Math.log2(h / 220);
      const za = (() => { let i = 1; while (i < y.length && Math.abs(y[i]) < 1e-4) i++; return i / sr; })(), zr = (() => { let i = y.length - 1; while (i > 0 && Math.abs(y[i]) < 1e-4) i--; return i / sr; })();
      const r = { one, played, st: ce(fq(y, za + 0.005, za + 0.09)), body: ce(fq(y, 0.6, 1.2)), end: ce(fq(y, zr - 0.18, zr - 0.005)), st0: ce(fq(x, a + 0.005, a + 0.09)), end0: ce(fq(x, z - 0.18, z - 0.005)), body0: ce(fq(x, 0.6, 1.2)) };
      AU.kind = k0; AU.sr = sr0; LIVE.at = at0; LRING.b = null; LOG8.length = 0; return r; });
    if (!lfx.one || lfx.st0 > -30 || lfx.end0 > -30 || ![lfx.st, lfx.body, lfx.end].every(v => Math.abs(v) <= 15) || (lfx.played && lfx.played.c !== 30)) throw new Error('lane all fixed: ' + JSON.stringify(lfx)); console.log('  lane all fixed: start ' + lfx.st0.toFixed(0) + ' → ' + lfx.st.toFixed(1) + ', body ' + lfx.body0.toFixed(0) + ' → ' + lfx.body.toFixed(1) + ', end ' + lfx.end0.toFixed(0) + ' → ' + lfx.end.toFixed(1) + ' ¢');
    // Then level: a 2 s A3 with 5 Hz vibrato (±20 ¢) that sags 40 ¢ in its middle gets '▶ then level' from laneDrift on its frames (a level note gets none); the levelRamp render, read back by zero crossings over 0.4 s, has its middle within 10 ¢ of its start and end (was about -35).
    const llv = await p.evaluate(async () => { const k0 = AU.kind, sr0 = AU.sr, at0 = LIVE.at; AU.kind = 'mic'; AU.sr = 48000; LRING.b = null; for (let j = 0; j < 4000; j++) liveTap(new Float32Array(480)); LIVE.at = 34; LOG8.length = 0; LRING.mute = -1;
      const sag = u => -40 * Math.max(0, Math.sin(Math.PI * (u - 0.5) / 1.0)) * (u > 0.5 && u < 1.5), vib = u => 20 * Math.sin(2 * Math.PI * 5 * u), H = (f) => Array.from({ length: 201 }, (_, i) => ({ t: 28 + i * 0.01, voiced: true, midi: 57 + f(i * 0.01) / 100 }));
      const h1 = H(u => sag(u) + vib(u)), h0 = H(vib), mm = h1.map(h => h.midi).sort((x, y) => x - y)[100], dr = laneDrift(h1, 0, 200, mm), none = laneDrift(h0, 0, 200, 57);
      logRecap({ t: 30, s: 'x', n: 'A3', d: 2, c: 0, dr, p: ['x'], best: false }); logRecap({ t: 33, s: 'x', n: 'B3', d: 2, c: 0, dr: none, p: ['y'], best: false });
      const btn = document.querySelectorAll('#laneLog .levelln'), one = btn.length === 1 && btn[0].dataset.i === '1' && /then held level/.test(btn[0].getAttribute('aria-label'));
      const sr = 48000, dur = 2.3, n = Math.round(dur * sr), a = 0.15, f0 = 220 * 2 ** ((mm - 57) * 100 / 1200) / 2 ** ((mm - 57) * 100 / 1200), x = new Float32Array(n); let ph = 0; for (let i = 0; i < n; i++) { const t = i / sr, u = t - a; ph += 2 * Math.PI * 220 * 2 ** ((sag(u) + vib(u)) / 1200) / sr; x[i] = u >= 0 && u < 2 ? Math.sin(ph) : 0; }
      const oc = new OfflineAudioContext(1, n + sr, sr), b = oc.createBuffer(1, n, sr); b.getChannelData(0).set(x); const s = oc.createBufferSource(); s.buffer = b; const d2 = levelRamp(s.playbackRate, 0, dur, dr); s.connect(oc.destination); s.start(0); const y = (await oc.startRendering()).getChannelData(0);
      const fq = (v, a, e) => { let k = 0, f = -1, l = -1; for (let i = Math.round(a * sr); i < Math.round(e * sr); i++) if (v[i - 1] < 0 && v[i] >= 0) { if (f < 0) f = i; l = i; k++; } return (k - 1) * sr / (l - f); }, ce = h => 1200 * Math.log2(h / 220);
      const zr = (() => { let i = y.length - 1; while (i > 0 && Math.abs(y[i]) < 1e-4) i--; return i / sr; })();
      const r = { one, none, mx: dr && dr.mx, mid0: ce(fq(x, a + 0.8, a + 1.2)), mid: ce(fq(y, a + 0.8, a + 1.2)), st: ce(fq(y, a + 0.05, a + 0.45)), end: ce(fq(y, a + 1.55, a + 1.95)), len: zr - a, d2 };
      AU.kind = k0; AU.sr = sr0; LIVE.at = at0; LRING.b = null; LOG8.length = 0; return r; });
    if (!llv.one || llv.none !== null || llv.mid0 > -30 || !(Math.abs(llv.mid - (llv.st + llv.end) / 2) <= 10)) throw new Error('lane then level: ' + JSON.stringify(llv)); console.log('  lane then level: middle ' + llv.mid0.toFixed(0) + ' → ' + llv.mid.toFixed(1) + ' ¢, start ' + llv.st.toFixed(1) + ', end ' + llv.end.toFixed(1), JSON.stringify(llv));
    // With vibrato: a straight 2 s A3 (vb.straight) gets '▶ with vibrato' (a note with vibrato gets none); the vibRamp render, pitch read every 10 ms by zero crossings over 20 ms and given to vibPiece (the take's estimator) over 0.8-1.6 s, has rate within 0.3 Hz of 5.8 and width within 0.1 st of 0.45; straight before (no rate).
    const vibq = await p.evaluate(async () => { const k0 = AU.kind, sr0 = AU.sr, at0 = LIVE.at; AU.kind = 'mic'; AU.sr = 48000; LRING.b = null; for (let j = 0; j < 4000; j++) liveTap(new Float32Array(480)); LIVE.at = 34; LOG8.length = 0; LRING.mute = -1;
      logRecap({ t: 30, s: 'x', n: 'A3', d: 2, c: 0, vb: { t: 28, straight: true }, p: ['x'], best: false }); logRecap({ t: 33, s: 'x', n: 'B3', d: 2, c: 0, vb: { t: 31, rate: 5.5, ext: 0.4 }, p: ['y'], best: false });
      const btn = document.querySelectorAll('#laneLog .vibln'), one = btn.length === 1 && btn[0].dataset.i === '1' && /gentle even vibrato/.test(btn[0].getAttribute('aria-label'));
      const sr = 48000, dur = 2.3, n = Math.round(dur * sr), a = 0.15, x = new Float32Array(n); for (let i = 0; i < n; i++) { const u = i / sr - a; x[i] = u >= 0 && u < 2 ? Math.sin(2 * Math.PI * 220 * u) : 0; }
      const oc = new OfflineAudioContext(1, n + sr, sr), b = oc.createBuffer(1, n, sr); b.getChannelData(0).set(x); const s = oc.createBufferSource(); s.buffer = b; vibRamp(s.playbackRate, 0, dur); s.connect(oc.destination); s.start(0); const y = (await oc.startRendering()).getChannelData(0);
      const fq = (v, a, e) => { let k = 0, f = -1, l = -1; for (let i = Math.max(1, Math.round(a * sr)); i < Math.round(e * sr); i++) if (v[i - 1] < 0 && v[i] >= 0) { if (f < 0) f = i; l = i; k++; } return (k - 1) * sr / (l - f); };
      const tr = v => { const m = []; for (let u = a + 0.8; u <= a + 1.6; u += 0.01) m.push(57 + 12 * Math.log2(fq(v, u - 0.01, u + 0.01) / 220)); return vibPiece(m, 0, 100); };
      const r1 = tr(y), r0 = tr(x), r = { one, rate: r1.rate, ext: r1.ext, rate0: r0.rate || 0 };
      AU.kind = k0; AU.sr = sr0; LIVE.at = at0; LRING.b = null; LOG8.length = 0; return r; });
    if (!vibq.one || vibq.rate0 || !(Math.abs(vibq.rate - 5.8) <= 0.3) || !(Math.abs(vibq.ext - 0.45) <= 0.1)) throw new Error('lane with vibrato: ' + JSON.stringify(vibq)); console.log('  lane with vibrato: straight → ' + vibq.rate.toFixed(2) + ' Hz, ' + vibq.ext.toFixed(3) + ' st (asked 5.8, 0.45)');
    // With a swell: a level 2 s A3 (sw within 6 dB) gets '▶ with a swell' (a swelled note gets none); the swellRamp render, level in 20 ms frames over the note, spreads 7-10 dB (5-95 %) with its peak in the middle third; the input is level (<0.5 dB).
    const swq = await p.evaluate(async () => { const k0 = AU.kind, sr0 = AU.sr, at0 = LIVE.at; AU.kind = 'mic'; AU.sr = 48000; LRING.b = null; for (let j = 0; j < 4000; j++) liveTap(new Float32Array(480)); LIVE.at = 34; LOG8.length = 0; LRING.mute = -1;
      logRecap({ t: 30, s: 'x', n: 'A3', d: 2, c: 0, sw: { w: 1, pm: 0.5, at: 0.5 }, p: ['x'], best: false }); logRecap({ t: 33, s: 'x', n: 'B3', d: 2, c: 0, sw: { w: 12, pm: 1, at: 0.5 }, p: ['y'], best: false });
      const btn = document.querySelectorAll('#laneLog .swellln'), one = btn.length === 1 && btn[0].dataset.i === '1' && /with a swell/.test(btn[0].getAttribute('aria-label'));
      const sr = 48000, dur = 2.3, n = Math.round(dur * sr), a = 0.15, x = new Float32Array(n); for (let i = 0; i < n; i++) { const u = i / sr - a; x[i] = u >= 0 && u < 2 ? Math.sin(2 * Math.PI * 220 * u) : 0; }
      const oc = new OfflineAudioContext(1, n + sr, sr), b = oc.createBuffer(1, n, sr); b.getChannelData(0).set(x); const s = oc.createBufferSource(), g = oc.createGain(); s.buffer = b; swellRamp(g.gain, 0, dur, 0.9); s.connect(g); g.connect(oc.destination); s.start(0); const y = (await oc.startRendering()).getChannelData(0);
      const lv = v => { const d = []; for (let u = a + 0.1; u + 0.02 <= a + 1.9; u += 0.02) { let e = 0; const i0 = Math.round(u * sr), i1 = Math.round((u + 0.02) * sr); for (let i = i0; i < i1; i++) e += v[i] * v[i]; d.push(10 * Math.log10(e / (i1 - i0) + 1e-12)); } const o = d.slice().sort((p, q) => p - q); return { w: o[Math.floor(o.length * 0.95)] - o[Math.floor(o.length * 0.05)], at: d.indexOf(Math.max(...d)) / (d.length - 1) }; };
      const r1 = lv(y), r0 = lv(x), r = { one, w: r1.w, at: r1.at, w0: r0.w };
      AU.kind = k0; AU.sr = sr0; LIVE.at = at0; LRING.b = null; LOG8.length = 0; return r; });
    if (!swq.one || !(swq.w0 < 0.5) || !(swq.w >= 7 && swq.w <= 10) || !(swq.at >= 0.33 && swq.at <= 0.67)) throw new Error('lane with a swell: ' + JSON.stringify(swq)); console.log('  lane with a swell: level ' + swq.w0.toFixed(2) + ' → ' + swq.w.toFixed(1) + ' dB, peak at ' + swq.at.toFixed(2));
    // Swell across days: wider today says 'wider swells' (good), same says level; a recap with a swell is kept with its width; the swell chart is drawn.
    const lswk = await p.evaluate(() => { const now = new Date().setHours(12, 0, 0, 0), S = (a, b) => [a, a + 1, b, b + 1].map((w, i) => ({ d: now - (i < 2 ? 3 * 864e5 : 6e4) - i * 6e4, sw: w })), E = [8, 9, 10].map((w, i) => ({ d: now - 864e5 - i * 6e4, sw: w }));
      const wide = laneDays(S(4, 16).concat(S(5, 15)), now, 'sw'), lv = laneDays(S(10, 10).concat(S(11, 10)), now, 'sw').v; localStorage.setItem(LN_KEY, JSON.stringify(E.concat(S(4, 16).slice(2))));
      logRecap({ t: 650, s: 'x', n: 'G3', d: 1.6, p: ['swell 16 dB ±2'], sw: { w: 16.04, pm: 2 }, best: false }); const L = JSON.parse(localStorage.getItem(LN_KEY)), svg = document.querySelector('#laneLog svg.trend[data-k="sw"]');
      localStorage.removeItem(LN_KEY); return { wide: wide.v + '|' + wide.good + '|' + /swell \d+\.?\d* dB \(/.test(wide.s), lv, kept: L[L.length - 1].sw, svg: !!svg && / dB /.test(svg.getAttribute('aria-label')) }; });
    if (lswk.wide !== 'wider swells than|true|true' || lswk.lv !== 'swells level with' || lswk.kept !== 16 || !lswk.svg) throw new Error('lane swell days: ' + JSON.stringify(lswk));
    // Vibrato across days: faster today is said but never 'good' (described, not rated); same rate level; a recap with vibrato keeps rate and width; both charts drawn.
    const lvib = await p.evaluate(() => { const now = new Date().setHours(12, 0, 0, 0), S = (k, a, b) => [a, a * 1.02, b, b * 1.02].map((w, i) => ({ d: now - (i < 2 ? 3 * 864e5 : 6e4) - i * 6e4, [k]: w })), E = [5, 5.1, 5.2].map((w, i) => ({ d: now - 864e5 - i * 6e4, vr: w, vx: 0.3 }));
      const fast = laneDays(S('vr', 5, 6).concat(S('vr', 5.1, 6.1)), now, 'vr'), lv = laneDays(S('vx', 0.3, 0.3).concat(S('vx', 0.31, 0.3)), now, 'vx').v; localStorage.setItem(LN_KEY, JSON.stringify(E.concat(E.map(q => ({ ...q, d: now - 6e4 })).slice(1))));
      logRecap({ t: 680, s: 'x', n: 'A3', d: 2.1, p: ['vibrato 5.6 Hz · 0.40 st wide'], vb: { rate: 5.613, ext: 0.4012 }, best: false }); const L = JSON.parse(localStorage.getItem(LN_KEY)), q = L[L.length - 1], ks = [...document.querySelectorAll('#laneLog svg.trend')].map(e => e.dataset.k).join(',');
      localStorage.removeItem(LN_KEY); return { fast: fast.v + '|' + fast.good + '|' + /vibrato \d\.\d Hz \(/.test(fast.s), lv, kept: q.vr + '/' + q.vx, ks }; });
    if (lvib.fast !== 'faster vibrato than|false|true' || lvib.lv !== 'vibrato width level with' || lvib.kept !== '5.61/0.401' || !/vr,vx/.test(lvib.ks)) throw new Error('lane vibrato days: ' + JSON.stringify(lvib));
    // Trend by day: days with 3+ notes get a dot and interval; under 2 such days no chart; the chart is drawn in the list.
    const ltr = await p.evaluate(() => { const now = new Date().setHours(12, 0, 0, 0), L = []; for (const [k, w] of [[0, 1], [2, 2], [5, 3], [9, 2]]) for (let i = 0; i < (k === 9 ? 2 : 4); i++) L.push({ d: now - k * 864e5 - i * 6e4, wob: w * (1 + 0.1 * (i % 2)), st: 10 * w + 4 * (i % 2), en: k === 2 ? undefined : 20 - 5 * w + 3 * (i % 2) });
      const T = laneTrend(L, now), one = laneTrendSvg(laneTrend(L.slice(0, 4), now)); localStorage.setItem(LN_KEY, JSON.stringify(L)); logRecap({ t: 700, s: 'x', n: 'B3', d: 1.2, p: ['steadiness 1.0 ¢ wobble · ±0.2'], w: { wob: 1.0, pm: 0.2 }, best: false });
      const svg = document.querySelector('#laneLog svg.trend'), kinds = [...document.querySelectorAll('#laneLog svg.trend')].map(e => e.dataset.k + e.querySelectorAll('circle').length).join(','), sl = (document.querySelector('#laneLog svg.trend[data-k=st]') || { getAttribute: () => '' }).getAttribute('aria-label'); localStorage.removeItem(LN_KEY); return { kinds, sl, ks: T.map(d => d.k).join(','), ok: T.every(d => d.lo < d.m && d.m < d.hi), one, dots: svg ? svg.querySelectorAll('circle').length : 0, lab: svg ? svg.getAttribute('aria-label') : '' }; });
    if (ltr.ks !== '5,2,0' || !ltr.ok || ltr.one !== '' || ltr.dots !== 3 || ltr.kinds !== 'wob3,st3,en2' || !/^Long-note starts by day.*today 1\d ¢/.test(ltr.sl) || !/^Long-note wobble by day.*today 1\.\d ¢/.test(ltr.lab)) throw new Error('lane trend: ' + JSON.stringify(ltr));
    await p.locator('#laneLog').screenshot({ path: join(out, `${name}-lanetrend.png`) });
    await p.screenshot({ path: join(out, `${name}-lanelog.png`) });
    await tap(p.locator('#vHelix'));
    if (touch) { await tap(p.getByRole('button', { name: 'Recording' })); await p.waitForTimeout(300); await p.setInputFiles('#file', file); }
    else { const [fc] = await Promise.all([p.waitForEvent('filechooser'), p.getByRole('button', { name: 'Recording' }).click()]); await fc.setFiles(file); }
    await p.waitForFunction(() => !document.getElementById('bPlaySpot').disabled, null, { timeout: 120000 });
    // Phone: the scanned take comes into view by itself (play row and timeline on screen, no scrolling by hand).
    await p.waitForTimeout(900); const inView = await p.evaluate(() => { const r = document.getElementById('takebar').getBoundingClientRect(); return r.top >= 0 && r.bottom <= innerHeight; });
    await p.screenshot({ path: join(out, `${name}-take-first.png`) });
    const bar = p.locator('#takebar'); await bar.scrollIntoViewIfNeeded(); await bar.screenshot({ path: join(out, `${name}-timeline.png`) });
    await p.evaluate(readFileSync(createRequire(import.meta.url).resolve('axe-core/axe.min.js'), 'utf8'));  // accessibility: no WCAG 2 A/AA violation on a scanned take (fuller states: a11y-audit.mjs)
    const axeBad = await p.evaluate(() => window.axe.run(document, { runOnly: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'] }).then(r => r.violations.map(v => v.id + ' ' + v.nodes[0].target)));
    if (axeBad.length) throw new Error('accessibility: ' + axeBad);
    await p.screenshot({ path: join(out, `${name}-take.png`) });
    const bb = await bar.boundingBox(); const pos = { position: { x: bb.width * 0.5, y: 10 } };
    touch ? await bar.tap(pos) : await bar.click(pos); await p.waitForTimeout(1200);
    const seek = await p.evaluate(() => AU.play ? (AU.ctx.currentTime - AU.play.t0) / AU.play.dur : -1);
    // Creak: read from 200 Hz up on 5 s sung, words only past the limit.
    // Focus across takes: three level earlier takes, today's focus on open, verdicts better/level/worse/too few, noise floor, slide style never a focus.
    const focus = await p.evaluate(() => { const x = aspectOf('stab'), P = [8, 8.5, 7.5], old = localStorage.getItem(HIST_KEY), now = Date.now(); localStorage.setItem(HIST_KEY, JSON.stringify([...P, 8].map((s, i) => ({ d: now - (4 - i) * 864e5, stab: s, f: ['stab'] })).concat({ d: now, stab: 4 })));
      const line = focusLines(now).join(), hasT = document.body.classList.contains('has-take'); document.body.classList.remove('has-take'); renderToday(); const t = document.getElementById('today'), today = !t.hidden && t.textContent; t.hidden = true; if (hasT) document.body.classList.add('has-take'); if (old === null) localStorage.removeItem(HIST_KEY); else localStorage.setItem(HIST_KEY, old);
      return { line, today, b: focusVerdict(x, 3, P).v, l: focusVerdict(x, 8.2, P).v, w: focusVerdict(x, 16, P).v, few: focusVerdict(x, 3, [8, 8]).v, floor: focusVerdict(x, 7, [8, 8, 8]).v, slide: focusKeys({ onset: 1, inton: 5, stab: 2, slide: { style: true }, tm: null }).length }; });
    if (!/steadiness.*Better/.test(focus.line) || !/Today's focus: steadiness/.test(focus.today) || focus.b !== 'better' || focus.l !== 'level' || focus.w !== 'worse' || focus.few !== 'few' || focus.floor !== 'level' || focus.slide) throw new Error('focus: ' + JSON.stringify(focus));
    const creak = await p.evaluate(() => { const fr = n => Array.from({ length: 300 }, () => ({ voiced: true, f0: n })), sn = (h, c) => Array.from({ length: 300 }, () => ({ h12: h, cpp: c })), on = takeCreak(fr(250), sn(0, 16)), off = takeCreak(fr(250), sn(8, 24)), low = takeCreak(fr(120), sn(0, 16)), short = takeCreak(fr(250).slice(0, 100), sn(0, 16)); return { on: on.on, words: creakLine({ creak: on }).length, off: off.on, quiet: creakLine({ creak: off }).length, low, short }; });
    if (!creak.on || creak.words !== 1 || creak.off || creak.quiet || creak.low !== null || creak.short !== null) throw new Error('creak: ' + JSON.stringify(creak));
    // Slow down: 0.5x must keep the pitch: three synthetic voices (110/220/440 Hz, steady, 8 harmonics) slowed, then scanned by the page; median and 90th percentile |cents| from the true pitch.
    const slow = await p.evaluate(async () => {
      const t = performance.now(), sb = wsola(TAKE.buf, 0.5), ms = performance.now() - t, sr = 48000, d = [], d1 = [];
      for (const F of [110, 220, 440]) { const n = sr * 3, x = new Float32Array(n); let ph = 0;
        const tru = s => F * Math.pow(2, 0 * Math.sin(2 * Math.PI * 5.5 * s) / 1200);
        for (let i = 0; i < n; i++) { ph += 2 * Math.PI * tru(i / sr) / sr; for (let h = 1; h <= 8; h++) x[i] += 0.3 * Math.sin(h * ph) / h; }
        const b = mkBuf(n, sr); b.getChannelData(0).set(x);
        for (const [k, out] of [[0.5, d], [1, d1]]) for (const f of (await scanTake(k === 1 ? b : wsola(b, k))).frames) { const s = (f.t - 0.02) * k; if (f.f0 > 0 && s > 0.2 && s < 2.8) out.push(Math.abs(1200 * Math.log2(f.f0 / tru(s)))); } }
      d.sort((x, y) => x - y); d1.sort((x, y) => x - y);
      return { at1: +d1[d1.length >> 1].toFixed(1), cents: +d[d.length >> 1].toFixed(1), p90: +d[Math.floor(d.length * 0.9)].toFixed(1), n: d.length, ratio: +(sb.duration / TAKE.buf.duration).toFixed(3), ms: Math.round(ms) }; });
    await tap(p.locator('#takebar i').first()); await p.waitForTimeout(800);
    const ab = await p.evaluate(() => AU.kind === 'ab' && AU.source && AU.source.loop && AU.ctx.state === 'running');
    const seg = await p.evaluate(() => { const mk = g => Array.from({ length: 200 }, (_, k) => ({ t: k * 0.02, voiced: true, ok: true, midi: g(k * 0.02) })), leg = segNotes(mk(t => 60 + Math.min(3, Math.floor(t)) * 2)).length, vib = segNotes(mk(t => 60 + 0.8 * Math.sin(2 * Math.PI * 5.2 * t))).length; return { leg, vib, perf: TAKE.aspects.perf.every(n => n.t1 > n.t0 && typeof n.q === 'number') }; }); 
    const vow = await p.evaluate(() => { const r = readVowel(693, 1233, 220), hi = readVowel(693, 1233, 700), ee = readVowel(355, 1963, 300); const n = TAKE.aspects.perf.find(x => x.vow && x.vow.sure), i = n ? TAKE.aspects.perf.indexOf(n) : -1; if (n) { TAKE.ni = i - 1; stepNote(1); TAKE.ni = -1; } const flat = envVowel(new Array(14).fill(0), 220), slope = envVowel(Array.from({ length: 14 }, (_, j) => 3 * (j - 6.5)), 220); return { ok: r.v === 'a' && r.sure && hi === null && ee.v === 'i' && flat && slope.v === flat.v && envVowel(new Array(14).fill(0), 700) === null && envVowel(Array.from({ length: 14 }, (_, j) => 3 * (j - 6.5)), 450).v === envVowel(new Array(14).fill(0), 450).v, chip: !!document.getElementById('mVow') && /7 in 8 right/.test(document.getElementById('mVow').nextElementSibling.textContent), said: !n || /sounds like “(ah|eh|ee|oh|oo)”/.test(document.getElementById('takeInfo').textContent) }; });
    if (!vow.ok || !vow.chip || !vow.said) throw new Error('vowel reading: ' + JSON.stringify(vow));
    const kl = await p.evaluate(() => { const G = [0, 2, 4, 5, 7, 9, 11, 12, 11, 9, 7, 5, 4, 2], N = Array.from({ length: 42 }, (_, i) => ({ m: 67 + G[i % 14], t0: i, t1: i + 0.6 })), k = takeKey(N, 0), few = takeKey(N.slice(0, 20), 0); return { sc: k && k.sc, sure: k && k.sure, few, line: keyLine(k)[0] || '' }; });
    if (kl.sc !== 7 || kl.sure < 0.9 || kl.few !== null || !kl.line.includes('G major / E minor')) throw new Error('scale line: ' + JSON.stringify(kl));
    if (seg.leg !== 4 || seg.vib !== 1 || !seg.perf) throw new Error('note segmentation: ' + JSON.stringify(seg));
    // Note by note: two taps on note ▶ then one on ◀ note land on the first note, play just it and say its numbers; → key goes to note 2.
    const spotKey = await p.evaluate(async () => { const K = () => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', shiftKey: true })); document.activeElement.blur(); TAKE.spotAt = null; K(); const a = [TAKE.spotAt, document.getElementById('say').textContent]; K(); await new Promise(r => setTimeout(r, 400)); const kind = AU.kind; stopSource(); return { a, b: TAKE.spotAt, n: TAKE.segs.length, kind }; });
    if (!(spotKey.n > 1 && spotKey.kind === 'ab' && spotKey.b > spotKey.a[0] && / spot 1 of /.test(spotKey.a[1]))) throw new Error('spot keys: ' + JSON.stringify(spotKey));
    await tap(p.locator('#bNextNote')); await tap(p.locator('#bNextNote')); await tap(p.locator('#bPrevNote')); await p.waitForTimeout(300);
    const nn = await p.evaluate(() => { const n = TAKE.aspects.perf[0]; return { i: TAKE.ni, kind: AU.kind, until: AU.play && Math.abs(AU.play.until - n.t1 - 0.15) < 0.01, on: document.querySelectorAll('#takebar u.on').length, said: /^Note 1 of \d+ at /.test(document.getElementById('takeInfo').textContent) }; });
    await p.keyboard.press('ArrowRight'); await p.waitForTimeout(200); nn.key = await p.evaluate(() => TAKE.ni);
    // Mark moments: ⚑ mark while note 2 plays drops a flag on it, kept per take in localStorage; tapping the flag plays from 1 s before.
    await tap(p.locator('#bMark')); await p.waitForTimeout(200);
    nn.mark = await p.evaluate(() => { const m = JSON.parse(localStorage.getItem('helix.marks.v1') || '{}')[TAKE.d] || []; const n = TAKE.aspects.perf[1]; return m.length === 1 && m[0] > n.t0 - 0.2 && m[0] < n.t1 + 0.2 && document.querySelectorAll('#takebar em').length === 1; });
    await p.locator('#takebar').screenshot({ path: join(out, `${name}-mark.png`) });
    await tap(p.locator('#takebar em').first()); await p.waitForTimeout(300);
    nn.markPlay = await p.evaluate(() => AU.kind === 'take' && /^Mark 1 at /.test(document.getElementById('takeInfo').textContent));
    // Loop a phrase: ⟲ while the take plays loops the phrase around the playhead (loopStart < loopEnd, at most 8.5 s), pressed; again stops.
    await tap(p.locator('#bLoopPh')); await p.waitForTimeout(300);
    nn.loop = await p.evaluate(() => { const s = AU.source; return AU.kind === 'loop' && s.loop && s.loopEnd > s.loopStart && s.loopEnd - s.loopStart < 8.6 && document.getElementById('bLoopPh').getAttribute('aria-pressed') === 'true' && /^Looping the phrase /.test(document.getElementById('takeInfo').textContent); });
    await tap(p.locator('#bLoopPh')); await p.waitForTimeout(200);
    nn.loopStop = await p.evaluate(() => AU.kind === null && document.getElementById('bLoopPh').getAttribute('aria-pressed') === 'false');
    // Save audio: the version last played saved as a WAV that decodes back to the same length and sample rate.
    nn.save = await p.evaluate(async () => { let blob = null, name = ''; const U = URL.createObjectURL; URL.createObjectURL = b => { blob = b; return U.call(URL, b); };
      const C = HTMLAnchorElement.prototype.click; HTMLAnchorElement.prototype.click = function () { name = this.download; }; document.getElementById('bSave').click(); URL.createObjectURL = U; HTMLAnchorElement.prototype.click = C;
      if (!blob) return false; const src = versionBuf(TAKE.nw || 'take'), b = await new OfflineAudioContext(1, 1, src.sampleRate).decodeAudioData(await blob.arrayBuffer());
      return /^voice-helix-.*\.wav$/.test(name) && b.length === src.length && b.sampleRate === src.sampleRate && /^Saved .* on this device only\.$/.test(document.getElementById('takeInfo').textContent); });
    // Save audio on a phone: the share sheet gets the same WAV as a file; closing it says not saved; a share error falls back to the download.
    nn.share = await p.evaluate(async () => { const M = window.matchMedia, CS = navigator.canShare, S = navigator.share, info = () => document.getElementById('takeInfo').textContent; let got = null, dl = 0, mode = 'ok';
      window.matchMedia = q => q === '(pointer:coarse)' ? { matches: true } : M.call(window, q); navigator.canShare = d => !!(d.files && d.files[0] instanceof File);
      navigator.share = d => { got = d.files[0]; return mode === 'ok' ? Promise.resolve() : Promise.reject(new DOMException('x', mode)); };
      const C = HTMLAnchorElement.prototype.click; HTMLAnchorElement.prototype.click = function () { dl++; }; const r = {};
      try { document.getElementById('bSave').click(); await new Promise(s => setTimeout(s, 50)); const src = versionBuf(TAKE.nw || 'take'), b = got && await new OfflineAudioContext(1, 1, src.sampleRate).decodeAudioData(await got.arrayBuffer());
        r.ok = !!b && b.length === src.length && /^voice-helix-.*\.wav$/.test(got.name) && dl === 0 && /^Shared /.test(info());
        mode = 'AbortError'; document.getElementById('bSave').click(); await new Promise(s => setTimeout(s, 50)); r.abort = dl === 0 && /^Not saved/.test(info());
        mode = 'NotAllowedError'; document.getElementById('bSave').click(); await new Promise(s => setTimeout(s, 50)); r.fall = dl === 1 && /^Saved /.test(info());
      } finally { window.matchMedia = M; navigator.canShare = CS; navigator.share = S; HTMLAnchorElement.prototype.click = C; }
      return r.ok && r.abort && r.fall; });
    // Hear it from the summary: each ▶ button by the words plays that note (best: the take from just before it; furthest-off: A/B with spotless). Needs at least one.
    nn.hear = { n: await p.locator('#rating [data-hear]').count(), ok: true };
    // Force one held note 40 ¢ off so the furthest-off button is exercised too, then the summary is re-rendered.
    await p.evaluate(() => { const n = TAKE.aspects.perf.find(n => n.t1 - n.t0 >= 0.4); n.c = 40; renderRating(); }); nn.hear.n = await p.locator('#rating [data-hear]').count();
    for (const m of ['best', 'worst']) { const bt = p.locator(`#rating [data-hear="${m}"]`); if (!(await bt.count())) continue; await tap(bt); await p.waitForTimeout(300);
      nn.hear[m] = await p.evaluate(m => m === 'worst' ? AU.kind === 'ab' && AU.source.loop : AU.kind === 'take' && AU.play && AU.play.until > 0, m); nn.hear.ok = nn.hear.ok && nn.hear[m]; }
    await tap(p.locator('#bPlaySpot')); await p.waitForTimeout(1200);
    // Far vision: a fourth version; a version button carries on from the same moment; the render differs from spotless only where a long note exists.
    // Sing it again: tuned note, 4 s capture (the mic stubbed, synthetic note 10 ¢ sharp of the target fed in), a reading with ± in the box.
    nn.drill = await p.evaluate(async () => { const b = document.getElementById('bTry'); if (!b) return { ok: false, why: 'no button' }; const m = +b.dataset.m, sr = AU.sr || AU.ctx.sampleRate, old = useMic; useMic = async () => { AU.kind = 'mic'; }; b.click();
      for (let i = 0; i < 100 && !DRILL.rec; i++) await new Promise(r => setTimeout(r, 50)); const live = !!DRILL.rec, n = sr * 3, x = new Float32Array(n); let ph = 0; for (let i = 0; i < n; i++) { ph += 2 * Math.PI * 440 * Math.pow(2, (m + 0.1 - 69) / 12) / sr; for (let h = 1; h <= 6; h++) x[i] += 0.15 * Math.sin(h * ph) / h; } DRILL.rec && DRILL.rec.push(x);
      for (let i = 0; i < 300 && DRILL.busy; i++) await new Promise(r => setTimeout(r, 100)); useMic = old; const t = document.getElementById('tryBox').textContent; stopSource(); return { live, t, ok: live && /Try 1: on the note, 1?[0-9] ¢ sharp ± [0-9]+/.test(t) && !/Further off/.test(t) }; });
    if (!nn.drill.ok) throw new Error('sing it again: ' + JSON.stringify(nn.drill));
    await p.locator('#tryBox').scrollIntoViewIfNeeded(); await p.locator('#tryBox').locator('xpath=..').screenshot({ path: join(out, `${name}-drill.png`) });
    // Sing the phrase: tuned phrase, capture (mic stubbed), the phrase's own notes fed back 10 ¢ sharp, 10 % slower: read note by note; a wrong melody is refused.
    nn.phr = await p.evaluate(async () => { const P = TAKE.aspects.perf, syn = (T, st) => { const sr = AU.sr || 48000, S = 0.3, n = Math.round(sr * (T.reduce((a, q) => a + S, 0) + 0.2 * T.length + 1)), b = mkBuf(n, sr), x = b.getChannelData(0); let ph = 0, u = 0.2 * sr; for (const q of T) { const e = u + sr * Math.max(0.5, S); for (; u < e; u++) { const i = Math.floor(u); ph += 2 * Math.PI * 440 * Math.pow(2, (q.m + st - 69) / 12) / sr; let v = 0; for (let h = 1; h <= 6; h++) v += 0.15 * Math.sin(h * ph) / h; x[i] = v; } u += 0.05 * sr; } return b; };
      const T0 = [{ m: 60, t0: 0, t1: 0.5, d: 30 }, { m: 64, t0: 0.55, t1: 1.05, d: -20 }, { m: 62, t0: 1.1, t1: 1.6, d: 25 }, { m: 67, t0: 1.65, t1: 2.15, d: 30 }], r = await phraseRead(syn(T0, 0.1), T0), bad = await phraseRead(syn([{ m: 71 }, { m: 60 }, { m: 72 }, { m: 57 }], 0), T0);
      TAKE.ni = P.findIndex(n => n.m !== undefined); const old = useMic; useMic = async () => { AU.kind = 'mic'; }; const b = $('bSingPh'); b.click(); await new Promise(r => setTimeout(r, 300)); const flow = PHR.busy ? 1 : 0, msg = $('phrBox').textContent; for (let i = 0; i < 300 && PHR.busy; i++) { if (DRILL.rec && !DRILL.rec.length) DRILL.rec.push(syn(PHR.T, 0.1).getChannelData(0)); await new Promise(r => setTimeout(r, 100)); } useMic = old; const t = $('phrBox').textContent; stopSource();
      return { r: r && r.same && r.notes.map(n => n.c), bad: bad && bad.same, msg, t, ok: !!r && r.same && r.heard === 4 && r.notes.every(n => Math.abs(n.c - 10) < 8) && !(bad && bad.same) && (flow ? /Try 1:/.test(t) : /two notes/.test(msg)) }; });
    nn.phrT = await p.evaluate(() => { const T = [0, 1, 2, 3, 4].map(i => ({ m: 60 + i, t0: i * 0.5 })), N = o => T.map((q, i) => ({ i, heard: true, at: 0.2 + q.t0 * 1.1 + (i === 2 ? o : 0) })), R = T.map((q, i) => ({ i, heard: true, at: q.t0 })), a = phraseTime(N(0.3), R), b = phraseTime(N(0), R); return { a, b, ok: a.out && a.i === 2 && Math.abs(a.ms - 300) < 1 && !b.out }; }); if (!nn.phrT.ok) throw new Error('phrase timing: ' + JSON.stringify(nn.phrT));
    if (!nn.phr.ok) throw new Error('sing the phrase: ' + JSON.stringify(nn.phr));
    // Tries kept across days: closer / level / further against an earlier day, today ignored, and the store is part of my data.
    nn.phrDays = await p.evaluate(() => { const D = 864e5, now = 40 * D + 5e6, r = m => ({ mean: m, me: 4 }), h = [{ d: now - 3 * D, id: 'a', mean: 20, e: 4 }, { d: now - 1000, id: 'a', mean: 1, e: 1 }, { d: now - D, id: 'b', mean: 9, e: 4 }], s = m => phraseSince(h, 'a', r(m), now); return { a: s(9).says, b: s(19).says, c: s(35).says, none: phraseSince(h, 'z', r(9), now), line: phraseBack(s(9)), kept: DATA_KEYS.some(([k]) => k === PHR_KEY), id: phraseId([{ m: 60 }, { m: 64 }, { m: 62 }]) }; });
    if (nn.phrDays.a !== 'closer' || nn.phrDays.b !== 'level' || nn.phrDays.c !== 'further' || nn.phrDays.none || !/3 days ago/.test(nn.phrDays.line) || !nn.phrDays.kept || nn.phrDays.id !== '4 -2') throw new Error('phrase across days: ' + JSON.stringify(nn.phrDays));
    if (await p.locator('#phrBox ul').count()) { await p.locator('#phrBox').scrollIntoViewIfNeeded(); await p.locator('#phrBox').screenshot({ path: join(out, `${name}-phrase.png`) }); }
    { const bt = p.locator('#rating [data-hear="far"]'); nn.farAb = await bt.count(); if (nn.farAb) { await tap(bt); await p.waitForTimeout(300); nn.farAb = await p.evaluate(() => AU.kind === 'ab' && AU.source.loop && /far/.test(AU.ab)); await p.evaluate(() => stopSource()); } if (!nn.farAb) throw new Error('far A/B: ' + nn.farAb); await tap(p.locator('#bPlaySpot')); await p.waitForTimeout(1000); }
    nn.vowels = await p.evaluate(() => { const l = vowelLine(TAKE.aspects.perf), few = vowelLine([{ vow: { v: 'a', sure: true } }]), many = vowelLine(Array.from({ length: 6 }, (_, i) => ({ vow: { v: i ? 'i' : 'a', sure: true } }))); return { n: l.length, shown: !l.length || $('rating').textContent.includes('Vowels heard'), ok: !few.length && /“ee” on 5 notes, “ah” on 1 note/.test(many[0]) }; });
    if (!nn.vowels.shown || !nn.vowels.ok) throw new Error('vowels line: ' + JSON.stringify(nn.vowels));
    nn.ring = await p.evaluate(() => ({ v: TAKE.aspects.ring, line: /Ring: singing power ratio/.test($('rating').textContent), row: Number.isFinite(loadHist().slice(-1)[0].ring) && !RATED.some(x => x.k === 'ring') }));
    if (!(nn.ring.v > -60 && nn.ring.v < 10 && nn.ring.line && nn.ring.row)) throw new Error('ring: ' + JSON.stringify(nn.ring));
    nn.room = await p.evaluate(() => { const c = (rms, v) => ({ rms, voiced: v, cs: v ? [[220, 0.1]] : [[300, 0.8]] }), fs = [...Array(30).fill(c(0.01, false)), ...Array(90).fill(c(0.1, true))]; return { snr: roomSnr(fs), lo: roomLine({ room: 5 })[0], hi: roomLine({ room: 25 })[0], none: roomFloor(Array(99).fill(c(0.1, true))) }; });
    if (!(Math.abs(nn.room.snr - 20) < 0.1 && /Noisy room/.test(nn.room.lo) && /Quiet room/.test(nn.room.hi) && nn.room.none === 0)) throw new Error('room: ' + JSON.stringify(nn.room));
    // Next step: tuning moved half way, its A/B loops, its version plays.
    { const bt = p.locator('#rating [data-hear="next"]'); nn.next = await bt.count(); if (nn.next) { await tap(bt); await p.waitForTimeout(300); nn.next = await p.evaluate(() => AU.kind === 'ab' && AU.source.loop && /next/.test(AU.ab)); await p.evaluate(() => stopSource()); }
      await tap(p.locator('#bPlayNext')); await p.waitForTimeout(300); const v = await p.evaluate(() => { const a = TAKE.buf.getChannelData(0), b = TAKE.next.getChannelData(0); let d = 0; for (let i = 0; i < a.length; i += 7) d = Math.max(d, Math.abs(a[i] - b[i])); return { d, which: AU.play && AU.play.which, status: /^Next step:/.test($('status').textContent) }; }); if (nn.next === false || !(v.d > 0.001 && v.which === 'next' && v.status)) throw new Error('next step: ' + JSON.stringify({ a: nn.next, v })); nn.next = v.d; await tap(p.locator('#bPlaySpot')); await p.waitForTimeout(300); }
    // Next step for starts: a synthetic take with 3 st scoops on every other note reads fewer scoops after the 'starts' render; the rule picks it.
    nn.nst = await p.evaluate(async () => { const sr = 44100, nd = 0.8, n = Math.round(8 * nd * sr), x = new Float32Array(n); let ph = 0; const st = [0, 2, 4, 5, 7, 5, 4, 2];
      for (let i = 0; i < n; i++) { const t = i / sr, N = Math.floor(t / nd), u = t - N * nd, sc = N % 2 && u < 0.3 ? -3 * (1 - u / 0.3) : 0, f = 220 * 2 ** ((st[N] + sc) / 12); ph += 2 * Math.PI * f / sr; let v = 0; for (let h = 1; h <= 20 && h * f < 16000; h++) v += Math.sin(h * ph) / h ** 1.2; x[i] = 0.25 * v * Math.min(1, Math.max(0, Math.min(u, nd - 0.1 - u)) / 0.02); }
      const b = new AudioBuffer({ length: n, sampleRate: sr }); b.getChannelData(0).set(x); const A = await scanTake(b), B = await scanTake(improveTake(b, A.frames, 0.5, A.aspects.off, null, 'starts'));
      return { a: A.aspects.onsetRaw, b: B.aspects.onsetRaw, kind: nextKindOf(A.aspects), clean: nextKindOf({ onset: 0, notes: 9, inton: 10 }), off: nextKindOf({ onset: 0.5, notes: 9, inton: 30 }) }; });
    if (!(nn.nst.a >= 0.25 && nn.nst.b < nn.nst.a && nn.nst.kind === 'starts' && nn.nst.clean === 'tuning' && nn.nst.off === 'tuning')) throw new Error('next starts: ' + JSON.stringify(nn.nst));
    // Next step for endings: a synthetic take whose long notes fall 80 ¢ over their last 0.2 s reads a smaller fall after the 'endings' render; the rule picks it.
    nn.nen = await p.evaluate(async () => { const sr = 44100, nd = 0.9, K = 10, n = Math.round(K * nd * sr), x = new Float32Array(n); let ph = 0; const st = [0, 2, 4, 5, 7, 5, 4, 2, 0, 4];
      for (let i = 0; i < n; i++) { const t = i / sr, N = Math.floor(t / nd), u = t - N * nd, L = nd - 0.1, fl = u > L - 0.2 ? -0.8 * (u - L + 0.2) / 0.2 : 0, f = 220 * 2 ** ((st[N] + fl) / 12); ph += 2 * Math.PI * f / sr; let v = 0; for (let h = 1; h <= 20 && h * f < 16000; h++) v += Math.sin(h * ph) / h ** 1.2; x[i] = 0.25 * v * Math.min(1, Math.max(0, Math.min(u, L - u)) / 0.02); }
      const b = new AudioBuffer({ length: n, sampleRate: sr }); b.getChannelData(0).set(x); const A = await scanTake(b), B = await scanTake(improveTake(b, A.frames, 0.5, A.aspects.off, null, 'endings'));
      return { a: A.aspects.tail && A.aspects.tail.cents, b: B.aspects.tail && B.aspects.tail.cents, kind: nextKindOf(A.aspects) }; });
    if (!(nn.nen.a < -20 && nn.nen.b > nn.nen.a + 10 && nn.nen.kind === 'endings')) throw new Error('next endings: ' + JSON.stringify(nn.nen));
    nn.far = await p.evaluate(() => { const f = TAKE.far && TAKE.far.getChannelData(0), t = AU.play && (AU.ctx.currentTime - AU.play.t0) * AU.play.k; return { len: !!f && f.length === TAKE.buf.length, peak: f ? f.reduce((m, v) => Math.max(m, Math.abs(v)), 0) : 0, t, status: /^Far vision/.test(VERSION.far.status) && VERSION.far.status.length > 20 }; });
    await tap(p.locator('#bPlayFar')); await p.waitForTimeout(300);
    nn.far.ok = nn.far.len && nn.far.peak > 0.01 && nn.far.peak <= 1 && nn.far.status && await p.evaluate(t => AU.play && AU.play.which === 'far' && (AU.ctx.currentTime - AU.play.t0) * AU.play.k >= t, nn.far.t);
    if (!nn.far.ok) throw new Error('far vision: ' + JSON.stringify(nn.far));
    await tap(p.locator('#bPlaySpot')); await p.waitForTimeout(300);
    await p.selectOption('#speed', '0.5'); await p.waitForTimeout(1500);
    const r = await p.evaluate(() => ({ k: AU.play && AU.play.k, ctx: AU.ctx && AU.ctx.state, playing: AU.play && AU.play.which, notes: TAKE.aspects.perf.length, slide: TAKE.aspects.slide && TAKE.aspects.slide.style, spots: TAKE.segs.length, summary: !document.getElementById('rating').hidden, acc: /97.4 ± 0.8 %/.test((document.getElementById('pitchAcc') || {}).textContent || ''), progress: document.querySelectorAll('#rating table.prog tr').length, takes: JSON.parse(localStorage.getItem('helix.takes.v1')).length }));
    await p.locator('table.prog').screenshot({ path: join(out, `${name}-progress.png`) });
    // Take pitch tracker: a breathy 600 Hz tone (noise at about -10 dB) must come out at 600 Hz on most frames
    // (live tracker: 0 % at this noise, it locks on 75 Hz; take tracker 81 %, LOG 2026-10-25).
    const pitch = await p.evaluate(async () => { const sr = 48000, n = sr * 2, b = mkBuf(n, sr), x = b.getChannelData(0); let s = 5;
      for (let i = 0; i < n; i++) { s = (s * 16807) % 2147483647; const ph = 2 * Math.PI * 600 * i / sr; x[i] = 0.2 * (Math.sin(ph) + 0.5 * Math.sin(2 * ph) + 0.3 * Math.sin(3 * ph)) + 0.25 * (s / 2147483647 - 0.5); }
      const fs = await trackTake(b); viterbiF0(fs); const v = fs.filter(m => m.t > 0.2 && m.voiced); return v.filter(m => Math.abs(1200 * Math.log2(m.f0 / 600)) < 50).length / Math.max(1, fs.filter(m => m.t > 0.2).length); });
    r.pitch = +pitch.toFixed(3); r.inView = inView;
    // Breathiness from CPP (check/breath-bench.mjs): the same singer's breathy scale reads below the cue's
    // threshold and below their straight scale; the take summary turns the breathy one into a point to work on.
    r.breath = await p.evaluate(async () => { const o = {}; for (const id of ['f2_breathy', 'm2_straight']) { const ab = await (await fetch(`demo/${id}.mp3`)).arrayBuffer(), buf = await new OfflineAudioContext(1, 1, 44100).decodeAudioData(ab);
      const fs = await trackTake(buf); viterbiF0(fs); trimEdges(fs, buf); const S = new Stats(); for (const m of fs) ingest(S, m, 'take'); const a = takeAspects(S); o[id] = { clar: +a.clar.toFixed(1), work: clarLine(a, false).length, good: clarLine(a, true).length, tone: +a.tone.toFixed(2), tl: toneLine(a).length }; }
      return o; });
    // Warm-up from the seeded takes: onsets (0.2 scoops/note) and intonation (~21 ¢) are furthest from the trained median, so they are the targeted steps; guide tone plays.
    await tap(p.locator('#bWarm')); await p.waitForTimeout(600); await p.locator('#warmup').screenshot({ path: join(out, `${name}-warmup.png`) });
    await tap(p.locator('#wNext')); await p.waitForTimeout(400);
    r.warm = await p.evaluate(() => ({ steps: WARM.plan.steps.map(s => s.name).join('|'), why: WARM.plan.why.length, osc: !!WARM.osc, ctx: (AU.ctx || WARM.ctx).state, text: /Clean starts/.test(document.getElementById('warmup').textContent) }));
    r.warmDesc = await p.evaluate(() => { const base = { inton: 10, stab: 2, onset: 0, clar: 30, lo: 55, hi: 64 }, h = [['tsag'], ['tsag', 'rhythm'], [], ['tsag'], ['rhythm']].map((f, i) => ({ ...base, d: i, f })), P = planWarmup(h), one = planWarmup([{ ...base, d: 1, f: ['kdrift'] }]), none = planWarmup(h.map(x => ({ ...x, f: [] })));
      return { steps: P.steps.map(s => s.name).join('|'), why: /note endings \(named in 3 of your last 5 takes\)/.test(P.why.join()), one: one.steps.map(s => s.name).join('|'), none: none.steps.some(s => /Hold|Clap/.test(s.name)) }; });
    // Live long notes steer the warm-up: yesterday's wobble 3x the earlier fortnight adds messa di voce; level adds nothing; already in, not twice.
    r.warmLane = await p.evaluate(() => { const now = Date.now(), L = (w, n, d) => Array.from({ length: n }, (_, i) => ({ d: now - d * 864e5 - i * 6e4, wob: w * (1 + 0.1 * (i % 3)), st: 10 + i % 4, en: 8 + i % 3 }));
      const base = { inton: 10, stab: 2, onset: 0, clar: 30, lo: 55, hi: 64, f: [] }, worse = [...L(2, 8, 6), ...L(6, 5, 1)], P = planWarmup([base], worse), Q = planWarmup([base], [...L(2, 8, 6), ...L(2, 5, 1)]), E = planWarmup([], [...L(2, 8, 6), ...L(2, 5, 1).map(q => ({ ...q, en: q.en + 70 }))]);
      const keep = [WARM.plan, WARM.i]; WARM.plan = E; WARM.i = 0; renderWarm(); const txt = document.getElementById('warmup').textContent; [WARM.plan, WARM.i] = keep; renderWarm();
      return { add: P.lane === 'wob' && P.steps.filter(s => s.name === 'Messa di voce').length === 1 && /long-note steadiness \(live: less steady than/.test(P.why.join()), level: Q.lane === null, empty: E.lane === 'en' && E.steps.some(s => s.name === 'Hold to the end') && /your live long notes say/.test(txt) }; });
    if (!r.warmLane.add || !r.warmLane.level || !r.warmLane.empty) throw new Error('warm-up lane: ' + JSON.stringify(r.warmLane));
    if (r.warmDesc.steps !== 'Lip trill or straw glides|Hold to the end|Clap, then sing|Siren' || !r.warmDesc.why || r.warmDesc.one !== 'Lip trill or straw glides|Keep the key|Siren' || r.warmDesc.none) throw new Error('warm-up described: ' + JSON.stringify(r.warmDesc));
    // Match and measure: step to Clean starts, five synthetic sung notes 10 ¢ sharp fed in place of the mic; the session is read and kept, a second one compares.
    r.match = await p.evaluate(async () => { stopSource(); const old = useMic; useMic = async () => { AU.kind = 'mic'; }; const oldS = MATCH_S; WARM.i = 1; renderWarm(); const hold = AU.kind; const run = async () => { document.getElementById('wMatch').click(); const W = WARM.plan, ms = warmNotes(W), sr = AU.sr || AU.ctx.sampleRate;
        for (const m of ms) { for (let i = 0; i < 200 && !DRILL.rec; i++) await new Promise(r => setTimeout(r, 25)); const n = sr * 2, x = new Float32Array(n); let ph = 0; for (let i = 0; i < n; i++) { ph += 2 * Math.PI * 440 * Math.pow(2, (m + 0.1 - 69) / 12) / sr; if (i > 0.2 * sr && i < 1.8 * sr) for (let h = 1; h <= 6; h++) x[i] += 0.15 * Math.sin(h * ph) / h; } DRILL.rec.push(x); while (DRILL.rec) await new Promise(r => setTimeout(r, 25)); }
        for (let i = 0; i < 200 && MATCH.busy; i++) await new Promise(r => setTimeout(r, 25)); }; await run(); const a = document.getElementById('matchBox').textContent; await run(); const b = document.getElementById('matchBox').textContent; useMic = old; const k = loadMatch(); stopSource(); return { a, b, n: k.length, off: k[0] && k[0].off, spark: !!document.querySelector('#matchBox svg'), hold, ok: /5 of 5 landed/.test(a) && /About the same/.test(b) && k.length === 2 && Math.abs(k[0].off - 10) < 3 }; });
    await p.locator('#warmup').screenshot({ path: join(out, `${name}-match.png`) }); if (!r.match.ok) throw new Error('match: ' + JSON.stringify(r.match));
    // High notes: a straight E5 and D6 must read on the note, not at a fraction of it (2026-10-31, check/high-bench.mjs).
    r.high = await p.evaluate(async () => { const o = []; for (const m of [33, 76, 86]) { const sr = 48000, n = sr * 2, b = mkBuf(n, sr), x = b.getChannelData(0); for (let i = 0.2 * sr; i < 1.8 * sr; i++) for (let h = 1; h <= 8; h++) x[i] += 0.2 * Math.sin(2 * Math.PI * h * 440 * Math.pow(2, (m - 69) / 12) * i / sr) / (h * h); const fs = await trackTake(b); viterbiF0(fs); const v = fs.filter(f => f.voiced).map(f => 69 + 12 * Math.log2(f.f0 / 440) - m).sort((a, c) => a - c); o.push(v.length > 40 && Math.abs(v[v.length >> 1]) < 0.3); } return o; });
    if (!r.high.every(Boolean)) throw new Error('high notes: ' + r.high);
    // Voice profile from the seeded takes (comfortable E3-D4, centre 57: tenor); a G3-D5 melody in G moves down 7 to C.
    await tap(p.locator('#bProf')); await p.waitForTimeout(400); await p.locator('#profile').screenshot({ path: join(out, `${name}-profile.png`) });
    r.prof = await p.evaluate(() => { const t = document.getElementById('profile').textContent; return { tenor: /fits a tenor/.test(t), key: /down 7 semitones/.test(t), br: /around C4/.test(t) && /crosses your break/.test(t) }; });
    await p.fill('#pKey', 'G'); await tap(p.locator('#pGo')); r.prof.toC = await p.evaluate(() => /key of C/.test(document.getElementById('pOut').textContent));
    // Compare: the scanned take's audio is kept (IndexedDB); one more stored a day earlier shows in the picker and plays.
    r.stored = await p.evaluate(async () => { const k = Date.now() - 864e5; await storeAudio(k, TAKE.buf); const a = await adbDo('readonly', st => st.get(k)); let m = 0; for (const v of a.pcm) m = Math.max(m, Math.abs(v)); return m > 1000; });
    await p.waitForFunction(() => !document.getElementById('bPlayCmp').hidden, null, { timeout: 10000 }).catch(() => {});
    await tap(p.locator('#bPlayCmp')); await p.waitForTimeout(800);
    r.cmp = await p.evaluate(() => ({ kind: AU.kind, ctx: AU.ctx.state, opts: document.querySelectorAll('#cmpSel option').length, said: /Playing your take from/.test(document.getElementById('takeInfo').textContent) }));
    // Same phrase: the earlier take is this take's own audio, so the phrase around the current note is found at the same time and plays.
    await tap(p.locator('#bSamePh')); await p.waitForFunction(() => /Same phrase:|not found/.test(document.getElementById('takeInfo').textContent), null, { timeout: 20000 }).catch(() => {});
    await p.locator('#takeRow').screenshot({ path: join(out, `${name}-samephrase.png`) });
    // Phone: two swipeable rows of take controls keep the score line on the first screen, every control still reachable.
    if (name.includes('iphone')) { r.rowFit = await p.evaluate(() => { const t = document.getElementById('takeRow'), b = document.getElementById('takebar'), h = t.getBoundingClientRect().height; return { h, gap: b.getBoundingClientRect().top - t.getBoundingClientRect().top, sw: t.scrollWidth, cw: t.clientWidth }; }); if (r.rowFit.gap > 300 || r.rowFit.sw <= r.rowFit.cw) throw new Error('take row: ' + JSON.stringify(r.rowFit)); console.log('rowFit', JSON.stringify(r.rowFit)); }
    r.sp = await p.evaluate(() => { const L = TAKE.lastSP; return { kind: AU.kind, said: /Same phrase:/.test(document.getElementById('takeInfo').textContent), nums: /Then vs today .*off [0-9]+ ± [0-9]+ → [0-9]+ ± [0-9]+ ¢ \(within the ±\)/.test(document.getElementById('takeInfo').textContent), dt: L && L.m ? +Math.abs(L.m.t0 - L.ph.t0).toFixed(2) : null, cost: L && L.m ? +L.m.cost.toFixed(2) : null }; });
    // All kept takes: a second copy stored two days earlier; with "all" picked the phrase is found in both, oldest first, then today.
    await p.evaluate(async () => { await storeAudio(Date.now() - 2 * 864e5, TAKE.buf); });
    await p.waitForFunction(() => [...document.querySelectorAll('#cmpSel option')].some(o => o.value === 'all'), null, { timeout: 10000 }).catch(() => {});
    await p.selectOption('#cmpSel', 'all'); await tap(p.locator('#bSamePh'));
    await p.waitForFunction(() => /kept takes, oldest|not found/.test(document.getElementById('takeInfo').textContent), null, { timeout: 30000 }).catch(() => {});
    r.spAll = await p.evaluate(() => ({ kind: AU.kind, said: /Same phrase in 2 of 2 kept takes, oldest first: .* then today [0-9]+ ± [0-9]+ ¢ off/.test(document.getElementById('takeInfo').textContent) }));
    // Same phrase drawn: versions over each other in today's key; a copy moved up 2 st comes back onto today's line, a line was painted.
    r.spFig = await p.evaluate(() => { const c = document.getElementById('cmpFig'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let ink = 0; for (let i = 3; i < d.length; i += 4) if (d[i]) ink++; const L = TAKE.lastSP, F = TAKE.frames, up = F.map(f => ({ t: f.t, f0: f.f0 * 2 ** (2 / 12) })), m = samePhrase(F, L.ph.t0, L.ph.t1, up); return { shown: !c.hidden, h: c.clientHeight, ink, lines: CMPV.lines.length, say: c.getAttribute('aria-label'), shift: m.shift, gap: cmpGap(cmpLine(up, m.t0, m.t1, m.shift), cmpLine(F, L.ph.t0, L.ph.t1, 0)) }; });
    console.log('spFig', JSON.stringify(r.spFig)); if (!r.spFig.shown || r.spFig.ink < 200 || r.spFig.lines !== 3 || r.spFig.shift !== -2 || !(r.spFig.gap < 0.3)) throw new Error('phrase figure: ' + JSON.stringify(r.spFig));
    await p.locator('#cmpFig').screenshot({ path: join(out, `${name}-cmpfig.png`) });
    // Range finder: the intro shows in the profile; three synthetic steps (lowest A2, highest A4) go through the page's analysis and show in the profile.
    r.rf = await p.evaluate(async () => { const intro = !!document.getElementById('rfGo'); const sr = 48000, mk = (T, m) => { const n = sr * T, b = mkBuf(n, sr), x = b.getChannelData(0); let ph = 0;
        for (let i = 0; i < n; i++) { ph += 2 * Math.PI * 440 * Math.pow(2, (m(i / sr) - 69) / 12) / sr; for (let h = 1; h <= 6; h++) x[i] += 0.2 * Math.sin(h * ph) / h; } return b; };
      const res = await rangeAnalyse([mk(3, s => s < 1.5 ? 52 - 7 * s / 1.5 : 45), mk(3, s => s < 1.5 ? 57 + 12 * s / 1.5 : 69), null]); renderProfile('x');
      const t = document.getElementById('profile').textContent; localStorage.removeItem(RANGE_KEY); return { intro, mn: res && Math.round(res.mn), mx: res && Math.round(res.mx), full: /Full range sung so far A2/.test(t), finds: /1 range find/.test(t) }; });
    // Range by week: weekly spans from takes and range finds; the last two weeks named only a semitone or more past before; a quieter fortnight never shrinks it.
    r.rwk = await p.evaluate(() => { const D = 864e5, now = new Date(); now.setHours(12, 0, 0, 0); const t = +now, H = [{ d: t - 30 * D, lo: 50, hi: 62, mn: 47, mx: 66 }, { d: t - 20 * D, lo: 51, hi: 63, mn: 47.2, mx: 66.4 }], G = [{ d: t - 2 * D, mn: 46.8, mx: 69.2 }];
      const up = rangeWeeks(H, G, t), lvl = rangeWeeks(H, [{ d: t - 2 * D, mn: 47.3, mx: 66.6 }], t), dn = rangeWeeks(H, [{ d: t - 2 * D, mn: 50, mx: 60 }], t), one = rangeWeeks([H[0]], [], t), svg = rangeWeeksSvg(up);
      const old = localStorage.getItem(RANGE_KEY); localStorage.setItem(RANGE_KEY, JSON.stringify(G)); renderProfile(); const sh = document.getElementById('profile').innerHTML; if (old === null) localStorage.removeItem(RANGE_KEY); else localStorage.setItem(RANGE_KEY, old);
      return up.wk.length === 3 && /highest held note, <b>A4<\/b>, is 3 semitones above/.test(up.say) && !/lowest/.test(up.say) && /stayed within a semitone/.test(lvl.say) && !/shrink/.test(lvl.say) && /does not shrink/.test(dn.say) && one.say === '' && /<rect class="full"/.test(svg) && /aria-label="Range by week, 3 weeks/.test(svg) && /Range by week/.test(sh); });
    // My data: a saved copy round-trips through a real download and file input after a wipe, merges without doubles, refuses markup, and delete takes the audio too.
    r.data = await p.evaluate(() => { const k = Date.now(), o = {}; o.old = localStorage.getItem(HIST_KEY); localStorage.setItem(HIST_KEY, JSON.stringify([{ d: k, sung: 9, score: 0.7 }])); localStorage.setItem(RANGE_KEY, JSON.stringify([{ d: k, mn: 45, mx: 69 }])); localStorage.setItem(MARK_KEY, JSON.stringify({ [k]: [3.5] })); window.__dk = k; window.__do = o.old; document.getElementById('bData').click(); return true; });
    await p.locator('#data').screenshot({ path: join(out, `${name}-data.png`) }); await p.locator('#dSave').scrollIntoViewIfNeeded(); const [dl] = await Promise.all([p.waitForEvent('download'), p.locator('#dSave').click()]); const dlp = join(out, `${name}-copy.json`); await dl.saveAs(dlp);
    await p.locator('#dForget').click(); await p.locator('#dForget').click(); await p.waitForFunction(() => /^Deleted/.test(document.getElementById('dataMsg')?.textContent || ''));
    const dgone = await p.evaluate(async () => [loadHist().length, loadRange().length, ((await adbDo('readonly', st => st.getAllKeys())) || []).length]);
    await p.setInputFiles('#dataFile', { name: 'copy.json', mimeType: 'application/json', buffer: readFileSync(dlp) }); await p.waitForFunction(() => /^Brought back \d+ records?, 1 of them take/.test(document.getElementById('dataMsg')?.textContent || ''));
    r.data = await p.evaluate(() => { const k = window.__dk, t = backupText(1), again = restoreText(t), bad = restoreText(JSON.stringify({ app: 'voice-helix', v: 1, data: { [HIST_KEY]: [{ d: 5, x: '<img src=x>' }, { d: 6, score: 1 }] } })), junk = restoreText('{"a":1}'), h = loadHist(), ok = h.length === 2 && h[0].d === 6 && h[1].d === k && loadRange().length === 1 && loadMarks()[k]?.[0] === 3.5 && again.n === 0 && bad.n === 1 && junk === null;
      if (window.__do === null) localStorage.removeItem(HIST_KEY); else localStorage.setItem(HIST_KEY, window.__do); localStorage.removeItem(RANGE_KEY); localStorage.removeItem(MARK_KEY); localStorage.removeItem(SAVED_KEY); document.getElementById('data').hidden = true; renderRating(); return { ok, n: h.length }; });
    if (!r.data.ok || dgone.join() !== '0,0,0') throw new Error('data: ' + JSON.stringify([r.data, dgone])); r.data = true;
    // The on-page error box (for phones, which have no console) is armed and empty.
    // Vibrato in the take summary: 5 notes of 2 s at 6 Hz, ±0.5 st must read 6.0 ± 0.3 Hz on 5 of 5 long notes (check/vibrato-bench.mjs).
    r.vib = await p.evaluate(async () => { const sr = 44100, n = sr * 12, b = mkBuf(n, sr), x = b.getChannelData(0); let ph = 0;
      for (let i = 0; i < n; i++) { const s = i / sr, k = Math.floor(s / 2.4), u = s - k * 2.4; if (u > 2) { ph = 0; continue; } const f = 220 * Math.pow(2, (k * 2 + 0.5 * Math.sin(2 * Math.PI * 6 * u)) / 12); ph += 2 * Math.PI * f / sr;
        x[i] = 0.2 * Math.min(1, u / 0.04, (2 - u) / 0.04) * (Math.sin(ph) + 0.5 * Math.sin(2 * ph) + 0.3 * Math.sin(3 * ph)); }
      const fs = await trackTake(b); viterbiF0(fs); trimEdges(fs, b); const S = new Stats(); for (const m of fs) ingest(S, m, 'take'); const v = takeVibrato(S);
      return { n: v.n, long: v.long, rate: v.rate && +v.rate[0].toFixed(2), line: /^Vibrato on 5 of 5 long notes: 6\.0 ± 0\.[0-9] Hz, ±0\.[45][0-9]/.test(vibLine(v)[0] || ''), even: !!v.rcv && v.rcv[0] < 6 && /^Vibrato evenness: rate varies .*as even as/.test(vibLine(v)[1] || ''),
        tiers: [[16, 25, /within the range of 20/], [22, 20, /under 18 %\)\. Slow sirens/], [12, 35, /under 29 %\)\. Messa di voce/]].every(([a, e, re]) => re.test(vibLine({ ...v, rcv: [a, 2], ecv: [e, 3] })[1] || '')) }; });
    // Dynamics: two 3 s tones, one swelled soft-loud-soft by 24 dB, one level, then a level one 10 dB softer: the swell reads about 18 dB (p95-p5 of a sine swell) and is named, the span about 10 dB.
    r.dyn = await p.evaluate(async () => { const sr = 44100, n = sr * 10, b = mkBuf(n, sr), x = b.getChannelData(0); let ph = 0;
      for (let i = 0; i < n; i++) { const s = i / sr, k = Math.floor(s / 3.4), u = s - k * 3.4; if (u > 3) { ph = 0; continue; } ph += 2 * Math.PI * 220 / sr;
        const g = k === 0 ? Math.pow(10, (-24 + 24 * Math.sin(Math.PI * u / 3)) / 20) : k === 1 ? 1 : Math.pow(10, -10 / 20);
        x[i] = 0.25 * g * Math.min(1, u / 0.04, (3 - u) / 0.04) * (Math.sin(ph) + 0.5 * Math.sin(2 * ph) + 0.3 * Math.sin(3 * ph)); }
      const fs = await trackTake(b); viterbiF0(fs); trimEdges(fs, b); const S = new Stats(); for (const m of fs) ingest(S, m, 'take'); const d = takeDynamics(S), l = dynLine(d)[0] || '';
      return { n: d && d.n, mx: d && +d.maxSwell.toFixed(1), span: d && +d.span.toFixed(1), line: /^Dynamics: on 3 long notes/.test(l) && /A real swell/.test(l), flat: /Held fairly level/.test(dynLine({ ...d, maxSwell: 6 })[0] || '') }; });
    // Swell and measure: a synthetic 10 s messa di voce, 18 dB, pitch tied to level by 2 ¢/dB, fed in place of the mic; read, kept, a second one compares.
    r.swell = await p.evaluate(async () => { stopSource(); const old = useMic; useMic = async () => { AU.kind = 'mic'; }; const pl = WARM.plan.steps, oi = WARM.i; WARM.plan.steps = [WARM_STEP.start, WARM_STEP.stab]; WARM.i = 1; renderWarm(); const sr = AU.sr || AU.ctx.sampleRate;
      const run = async () => { document.getElementById('wSwell').click(); for (let i = 0; i < 400 && !DRILL.rec; i++) await new Promise(r => setTimeout(r, 25)); const n = sr * 9, x = new Float32Array(n); let ph = 0; for (let i = 0; i < n; i++) { const u = i / n, db = 18 * (1 - Math.abs(2 * u - 1)) - 9; ph += 2 * Math.PI * 440 * Math.pow(2, (57 + 2 * db / 100 - 69) / 12) / sr; for (let h = 1; h <= 6; h++) x[i] += 0.1 * Math.pow(10, db / 20) * Math.sin(h * ph) / h; } DRILL.rec.push(x); for (let i = 0; i < 800 && SWELL.busy; i++) await new Promise(r => setTimeout(r, 25)); return document.getElementById('swellBox').textContent; };
      const a = await run(), b = await run(), k = loadSwell(); useMic = old; stopSource(); const shown = !!document.getElementById('swellBox'); window.__sw = () => { WARM.plan.steps = pl; WARM.i = oi; renderWarm(); }; return { a, b, n: k.length, shown, ok: /1[5-9] dB from soft to loud/.test(a) && /went up with the volume/.test(a) && /As still as your last swell/.test(b) && k.length === 2 && Math.abs(k[0].slope - 2) < 0.5 }; });
    await p.locator('#warmup').screenshot({ path: join(out, `${name}-swell.png`) }); await p.evaluate(() => window.__sw()); console.log('swell', name, r.swell.b); r.swell = r.swell.ok ? true : r.swell;
    if (r.swell !== true) throw new Error('swell: ' + JSON.stringify(r.swell));
    // Siren and measure: a synthetic 12 s siren A2-A4 fed in place of the mic; span read and kept.
    r.siren = await p.evaluate(async () => { stopSource(); const old = useMic; useMic = async () => { AU.kind = 'mic'; }; const pl = WARM.plan.steps, oi = WARM.i; WARM.plan.steps = [WARM_STEP.start, WARM_STEP.end]; WARM.i = 1; renderWarm(); const sr = AU.sr || AU.ctx.sampleRate; document.getElementById('wSiren').click(); for (let i = 0; i < 400 && !DRILL.rec; i++) await new Promise(r => setTimeout(r, 25)); const n = sr * 10, x = new Float32Array(n); let ph = 0; for (let i = 0; i < n; i++) { const u = i / n, m = 45 + 24 * (1 - Math.abs(2 * u - 1)); ph += 2 * Math.PI * 440 * Math.pow(2, (m - 69) / 12) / sr; for (let h = 1; h <= 6; h++) x[i] += 0.1 * Math.sin(h * ph) / h; } DRILL.rec.push(x); for (let i = 0; i < 800 && SIREN.busy; i++) await new Promise(r => setTimeout(r, 25)); const a = document.getElementById('sirenBox').textContent, k = loadSiren(); useMic = old; stopSource(); WARM.plan.steps = pl; WARM.i = oi; renderWarm(); return { a, ok: /^2[34] semitones/.test(a) && /No register jump/.test(a) && k.length === 1 }; });
    if (!r.siren.ok) throw new Error('siren: ' + JSON.stringify(r.siren));
    // Personal bests: against 2 earlier takes (best 4.0 ¢, 2.0 s), a 2.5 ¢ / 3 s note is a new best; a 4.5 ¢ one only matches.
    r.pb = await p.evaluate(() => { const k = 'helix.takes.v1', keep = localStorage.getItem(k); localStorage.setItem(k, JSON.stringify([{ d: 1, lb: [4, 2] }, { d: 2, lb: [5, 1.5] }]));
      const P = w => [{ t0: 1, t1: 4, c: 3, wob: w }, { t0: 5, t1: 5.5, c: 2, wob: 0.5 }]; const a = pbLines(P(2.5), 9), b = pbLines(P(4.5), 9); localStorage.setItem(k, keep);
      return a.length === 2 && /^Personal best: your steadiest long note.*2\.5 ¢.*4\.0 ¢/.test(a[0]) && /3\.0 s at 0:01.*2\.0 s/.test(a[1]) && /matches your best/.test(b[0]); });
    // Last week: 2 takes from 2-3 days ago (best 4.0 ¢); last three long notes at 2.0-2.8 ¢ beat it, one at 3.5 ¢ does not; old takes (>7 d) ignored.
    r.wk = await p.evaluate(() => { const k = 'helix.takes.v1', keep = localStorage.getItem(k), now = Date.now(); localStorage.setItem(k, JSON.stringify([{ d: now - 2 * 864e5, lb: [4, 2] }, { d: now - 3 * 864e5, lb: [5, 1] }, { d: now - 20 * 864e5, lb: [1, 1] }]));
      const P = w => [{ t0: 0, t1: 2, c: 3, wob: 9 }, ...w.map((x, i) => ({ t0: 3 + 2 * i, t1: 4.5 + 2 * i, c: 3, wob: x }))]; const a = lastWeekLine(P([2, 2.4, 2.8]), now), b = lastWeekLine(P([2, 3.5, 2.8]), now); localStorage.setItem(k, keep);
      return /^Your last three long notes \(2\.0, 2\.4, 2\.8 ¢ wobble\).*your 2 takes.*best 4\.0 ¢/.test(a) && b === ''; });
    // Streak: 7 seeded daily takes + today's = 8 days in a row; without today it still counts 7 and asks to sing today.
    r.streak = await p.evaluate(() => { const t = document.querySelector('#rating p.streak'), now = Date.now(), H = [1, 2, 3].map(i => ({ d: now - i * 864e5, sung: 30 })), S = streakInfo(H, now), lk = localStorage.getItem(LN_KEY); localStorage.removeItem(LN_KEY); const said = streakLine(H); if (lk) localStorage.setItem(LN_KEY, lk);
      return !!t && /^8 days in a row · 8 days sung/.test(t.textContent) && S.n === 3 && !S.today && /sing today/.test(said)
        && (() => { const L = [0, 1, 2, 3].map(i => ({ d: now - i * 864e5, len: 6 })), Q = streakInfo(H, now, L); return Q.n === 4 && Q.today && Q.days === 4 && Q.ln === 4 && Math.abs(Q.lmin - 0.4) < 1e-9 && Math.abs(Q.min - 1.5) < 1e-9 && streakInfo([], now, L).n === 4; })()
        && (() => { const Q = streakInfo(H, now, [{ d: now, len: 5 }], 120); return Q.ln === 120 && Q.ml === 100 && Q.nextL === 250; })()
        && (() => { const lk2 = localStorage.getItem(LN_KEY), lc = localStorage.getItem(LNC_KEY); localStorage.setItem(LN_KEY, JSON.stringify(Array.from({ length: 9 }, (_, i) => ({ d: now - i * 1e3, wob: 3 })))); localStorage.removeItem(LNC_KEY);
          const m = laneKeep({ n: 'A4', d: 2, w: { wob: 3 } }), m2 = laneKeep({ n: 'A4', d: 2, w: { wob: 3 } }), c = laneCount(), b = JSON.parse(backupText(now)).data[LNC_KEY], said = streakLine([]);
          if (lk2) localStorage.setItem(LN_KEY, lk2); else localStorage.removeItem(LN_KEY); if (lc) localStorage.setItem(LNC_KEY, lc); else localStorage.removeItem(LNC_KEY);
          return m === 10 && m2 === 0 && c === 11 && b === 11 && /11 long notes held live \(milestone: 10\), next: 50/.test(said); })(); });
    // Today's session: three takes today, overall clearly up on earlier days, a kept note plays, the second take alone says nothing of the sort.
    r.session = await p.evaluate(async () => { const now = Date.now(), t0 = new Date(now); t0.setHours(0, 0, 0, 0); const d = +t0, H = [40, 41, 42, 43].map((i, j) => ({ d: d - i * 864e5, sung: 30, score: 0.50 + j * 0.01, inton: 20 + j % 2 })).concat([1, 2, 3].map(j => ({ d: d + j * 6e4, sung: 40, score: 0.8 + j * 0.01, inton: 20 + j % 2, lb: [3 + j, 1 + j / 10], lt: [[1, 2], [1, 2]], f: ['inton'] })));
      const S = sessInfo(H, d + 18e4), v = k => S.V.find(o => o.x.k === k).v, one = sessInfo(H, d + 6e4), key = H[6].d; const pcm = new Int16Array(22050); for (let i = 0; i < pcm.length; i++) pcm[i] = 8000 * Math.sin(i * 0.05); await adbDo('readwrite', st => { st.put({ sr: 22050, pcm }, key); });
      const prev = localStorage.getItem(HIST_KEY); localStorage.setItem(HIST_KEY, JSON.stringify(H)); const b = sessBlock(d + 18e4); localStorage.setItem(HIST_KEY, prev); await playKept(key, 0, 0.5); const played = AU.kind === 'cmp' && !!AU.source; stopSource(); await adbDo('readwrite', st => { st.delete(key); });
      const rest = sessVerdict(aspectOf('inton'), [20, 21], [20, 21, 20]), flat = sessVerdict(SESS[0], [0.6, 0.61], [0.6, 0.61, 0.6]); return flat.v === 'level' && Number.isFinite(flat.half) && !/NaN/.test(b) && S.n === 3 && one === null && v('score') === 'better' && v('inton') === 'level' && S.st.d === H[4].d && S.tn.d === H[6].d && rest.v === 'level' && /Today's session/.test(b) && /Better today: overall/.test(b) && /For next time: intonation/.test(b) && /data-kept/.test(b) && played; });
    // Moments marked earlier: a mark on a kept take lists, plays, and ✕ removes it; a mark without kept audio stays out.
    r.oldMarks = await p.evaluate(async () => { const k = TAKE.d - 5e3, gone = TAKE.d - 9e3, pcm = new Int16Array(66150); for (let i = 0; i < pcm.length; i++) pcm[i] = 8000 * Math.sin(i * 0.05); await adbDo('readwrite', st => { st.put({ sr: 22050, pcm }, k); });
      const old = localStorage.getItem(MARK_KEY); const m = loadMarks(); m[k] = [1.5]; m[gone] = [2]; localStorage.setItem(MARK_KEY, JSON.stringify(m)); await fillOldMarks(); const el = document.getElementById('oldMarks'), n = el.querySelectorAll('li').length; el.querySelector('[data-oldp]').click(); await new Promise(r => setTimeout(r, 400)); const played = AU.kind === 'cmp' && !!AU.source; stopSource(); el.querySelector('[data-oldx]').click(); await new Promise(r => setTimeout(r, 300)); const left = el.querySelectorAll('li').length, kept = !loadMarks()[k];
      if (old === null) localStorage.removeItem(MARK_KEY); else localStorage.setItem(MARK_KEY, old); await adbDo('readwrite', st => { st.delete(k); }); await fillOldMarks(); return n === 1 && played && left === 0 && kept; });
    // This week vs last week: 3 takes per week, overall clearly up, one aspect level.
    r.week = await p.evaluate(() => { const now = Date.now(), H = [1, 2, 3, 8, 9, 10].map((i, j) => { const r = { d: now - i * 864e5 + 6e4, score: j < 3 ? 0.8 + j * 0.01 : 0.5 + j * 0.01 }; for (const x of ASPECTS) r[x.k] = 5 + (j % 2); return r; });
      const W = weekLines(H, now), t = weekLine(H);
      return !!W && W.na === 3 && W.nb === 3 && W.out[0].v === 'better' && W.out.slice(1).every(o => o.v === 'level') && weekLines(H.slice(0, 4), now) === null && /overall better than last week/.test(t); });
    // Swell on the progress line: 12 seeded takes whose swell rises 6 to 20 dB (two without long notes, no swell stored) read 'more swell', described not rated; the take table shows '—' without long notes.
    r.swell = await p.evaluate(() => { const H = Array.from({ length: 12 }, (_, i) => { const r = { d: Date.now() - (12 - i) * 36e5, score: 0.6, inton: 10, stab: 5, onset: 0.1, clar: 25, tone: -1 }; if (i !== 3 && i !== 7) r.swell = 6 + i * 1.3; return r; });
      const old = localStorage.getItem('helix.takes.v1'); localStorage.setItem('helix.takes.v1', JSON.stringify(H)); const d = document.createElement('div'); d.innerHTML = renderProgress(); localStorage.setItem('helix.takes.v1', old);
      const row = [...d.querySelectorAll('table.prog tr')].find(t => /swell/.test(t.textContent)); return !!row && /more swell than the takes before/.test(row.textContent) && !/better|worse/.test(row.textContent) && !RATED.some(x => x.k === 'swell'); });
    // Key drift: 12 one-second notes on a scale sinking 60 ¢ over the take read as a sink beyond the ± with a point to work on; the same notes level read 'held your key'.
    r.drift = await p.evaluate(async () => { const mk = async D => { const sr = 44100, n = sr * 14, b = mkBuf(n, sr), x = b.getChannelData(0), sc = [0, 2, 4, 5, 7, 5, 4, 2, 0, 4, 7, 12]; let ph = 0;
        for (let i = 0; i < n; i++) { const s = i / sr, k = Math.floor(s / 1.15), u = s - k * 1.15; if (k >= 12 || u > 1) { ph = 0; continue; } const f = 220 * Math.pow(2, (sc[k] + D / 100 * s / 14) / 12); ph += 2 * Math.PI * f / sr;
          x[i] = 0.25 * Math.min(1, u / 0.04, (1 - u) / 0.04) * (Math.sin(ph) + 0.5 * Math.sin(2 * ph) + 0.3 * Math.sin(3 * ph)); }
        const fs = await trackTake(b); viterbiF0(fs); trimEdges(fs, b); const S = new Stats(); for (const m of fs) ingest(S, m, 'take'); return takeDrift(S.rec.frames); };
      const a = await mk(-60), z = await mk(0);
      return !!a && !!z && a.cents < -40 && a.cents > -80 && /^key drift \(your tuning sank/.test(driftLine(a, false)[0] || '') && !driftLine(z, false).length && /^You held your key/.test(driftLine(z, true)[0] || '') && { a: +a.cents.toFixed(0), ci: +a.ci.toFixed(0), z: +z.cents.toFixed(0) }; });
    // Register lean: a seeded lean says 'under' with its ±, a level one praises, an ambiguous one (alt) stays silent.
    // Note endings: 10 one-second notes whose last 0.2 s fall 80 ¢ while fading read as 'sits … under' with a point; the same notes held read 'held their pitch to the end'.
    r.tail = await p.evaluate(async () => { const mk = async D => { const sr = 44100, n = sr * 12, b = mkBuf(n, sr), x = b.getChannelData(0), sc = [0, 2, 4, 5, 7, 5, 4, 2, 0, 4]; let ph = 0;
        for (let i = 0; i < n; i++) { const s = i / sr, k = Math.floor(s / 1.15), u = s - k * 1.15; if (k >= 10 || u > 1) { ph = 0; continue; } const rel = Math.max(0, (u - 0.8) / 0.2), f = 220 * Math.pow(2, (sc[k] + D / 100 * rel) / 12); ph += 2 * Math.PI * f / sr;
          x[i] = 0.25 * Math.min(1, u / 0.04, (1 - u) / 0.03) * (1 - 0.5 * rel) * (Math.sin(ph) + 0.5 * Math.sin(2 * ph) + 0.3 * Math.sin(3 * ph)); }
        const fs = await trackTake(b); viterbiF0(fs); trimEdges(fs, b); const S = new Stats(); for (const m of fs) ingest(S, m, 'take'); mk.last = mk.last || b; return takeTail(S.rec.frames); };
      const a = await mk(-80), z = await mk(0);
      // held ending, heard: the furthest-falling note is picked, and spotless holds it (check/tailfix-bench.mjs)
      const rd = async b => { const fs = await trackTake(b); viterbiF0(fs); trimEdges(fs, b); const S = new Stats(); for (const m of fs) ingest(S, m, 'take'); return takeTail(S.rec.frames); };
      const sc = await scanTake(mk.last), held = await rd(improveTake(mk.last, sc.frames, 1, sc.aspects.off));
      if (!a || !a.worst || a.worst.c > -20 || a.worst.t1 - a.worst.t0 < 0.5 || !held || Math.abs(held.cents) > 10) return false;
      return !!a && !!z && a.cents < -20 && /^Note endings: .* ¢ under the rest/.test(tailLine(a, false)[0] || '') && !tailLine(z, false).length && /^Your long notes held their pitch/.test(tailLine(z, true)[0] || '') && { a: +a.cents.toFixed(0), ci: +a.ci.toFixed(0), z: +z.cents.toFixed(0), held: +held.cents.toFixed(0) }; });
    r.lean = await p.evaluate(() => { const L = { cents: -30, ci: 12, hi: 69, lo: 57, R: 0.7, alt: 0.6 }; return /sit 30 ± 12 ¢ under your low ones/.test(leanLine(L, false)[0] || '') && !leanLine({ ...L, alt: 0.95 }, false).length && /^High and low notes sit together/.test(leanLine({ ...L, cents: 3 }, true)[0] || '') && !leanLine({ ...L, cents: 3 }, false).length; });
    // Key drift on the progress line: 12 seeded takes whose drift falls 70 to 15 ¢ (two without a drift) read 'better', the row exists, not rated.
    r.kdrift = await p.evaluate(() => { const H = Array.from({ length: 12 }, (_, i) => { const r = { d: Date.now() - (12 - i) * 36e5, score: 0.6, inton: 10, stab: 5, onset: 0.1, clar: 25, tone: -1 }; if (i !== 2 && i !== 9) r.kdrift = 70 - i * 5; return r; });
      const old = localStorage.getItem('helix.takes.v1'); localStorage.setItem('helix.takes.v1', JSON.stringify(H)); const d = document.createElement('div'); d.innerHTML = renderProgress(); localStorage.setItem('helix.takes.v1', old);
      const row = [...d.querySelectorAll('table.prog tr')].find(t => /key drift/.test(t.textContent)); return !!row && /better than the takes before/.test(row.textContent) && !RATED.some(x => x.k === 'kdrift'); });
    // Note endings on the progress line: 12 seeded takes whose end sag falls 40 to 7 ¢ (two without one) read 'better', the row exists, not rated.
    r.tsag = await p.evaluate(() => { const H = Array.from({ length: 12 }, (_, i) => { const r = { d: Date.now() - (12 - i) * 36e5, score: 0.6, inton: 10, stab: 5, onset: 0.1, clar: 25, tone: -1 }; if (i !== 2 && i !== 9) r.tsag = 40 - i * 3; return r; });
      const old = localStorage.getItem('helix.takes.v1'); localStorage.setItem('helix.takes.v1', JSON.stringify(H)); const d = document.createElement('div'); d.innerHTML = renderProgress(); localStorage.setItem('helix.takes.v1', old);
      const row = [...d.querySelectorAll('table.prog tr')].find(t => /note endings/.test(t.textContent)); return !!row && /better than the takes before/.test(row.textContent) && !RATED.some(x => x.k === 'tsag'); });
    // Timing: 16 onsets on a 0.5 s pulse read about the jitter, a 12 % slowing is named with an exercise, free onsets find no pulse; rhythm row exists, not rated.
    r.timing = await p.evaluate(() => { let s = 5; const rnd = () => (s = (s * 16807) % 2147483647) / 2147483647, st = [1, 2, 1, 3, 2, 1, 2, 2, 1, 1, 3, 1, 2, 1, 2];
      const mk = (c, j) => { let g = 0; return [0, ...st.map((x, i) => { g += x * 0.5 * (1 + c * i / 14); return g + j * (rnd() - 0.5); })]; }, a = pulseFit(mk(0, 0.05)), b = pulseFit(mk(0.12, 0));
      let g = 0; const f = pulseFit(Array.from({ length: 16 }, () => g += 0.25 + 1.05 * rnd())), H = Array.from({ length: 8 }, (_, i) => ({ d: Date.now() - (8 - i) * 36e5, score: 0.6, inton: 10, stab: 5, onset: 0.1, clar: 25, tone: -1, rhythm: 90 - i * 8 }));
      const old = localStorage.getItem('helix.takes.v1'); localStorage.setItem('helix.takes.v1', JSON.stringify(H)); const d = document.createElement('div'); d.innerHTML = renderProgress(); localStorage.setItem('helix.takes.v1', old);
      const row = [...d.querySelectorAll('table.prog tr')].some(t => /rhythm spread/.test(t.textContent)); return a.pulse && a.sd < 30 && /^Steady rhythm/.test(timingLine(a, true)[0] || '') && b.pulse && /^tempo \(you slowed/.test(timingLine(b, false)[0] || '') && !f.pulse && /^Free timing/.test(timingLine(f, true)[0] || '') && !timingLine(f, false).length && row && !RATED.some(x => x.k === 'rhythm') && { sd: +a.sd.toFixed(0), change: +b.change.toFixed(0), r: +f.ratio.toFixed(2) }; });
    // A stray onset no longer hides a pulse: 20 onsets on a 0.5 s step with 12 ms spread and two between beats (the half step is a fair reading).
    r.stray = await p.evaluate(() => { const on = Array.from({ length: 20 }, (_, i) => 1 + i * 0.5 + (i % 2 ? 0.012 : -0.012)); on.push(3.2, 7.3); const f = pulseFit(on); return !!f?.pulse && [0.25, 0.5].some(s => Math.abs(f.step - s) < 0.03); });
    if (!r.stray) throw new Error('stray onset hid the pulse');
    // No pulse is said in words in the summary, not as a bare dash.
    r.noPulse = await p.evaluate(() => { const A = TAKE.aspects, o = A.tm, v = A.rhythm; A.rhythm = NaN; A.tm = { pulse: false, n: 14 }; renderRating(); const f = /free timing, no steady pulse/.test(document.getElementById('rating').textContent); A.tm = null; renderRating(); const s = /too few notes to find a pulse/.test(document.getElementById('rating').textContent); A.tm = o; A.rhythm = v; renderRating(); return f && s; });
    if (!r.noPulse) throw new Error('no-pulse words missing');
    // Hear it with your pulse: a take with a found pulse gets the button; a tap plays the take with the click oscillator running, and stopping ends the clicks.
    r.pulse = await p.evaluate(async () => { const old = TAKE.aspects.tm; TAKE.aspects.tm = { ...pulseFit(Array.from({ length: 16 }, (_, i) => 1 + i * 0.6)) }; renderRating(); const b = document.querySelector('#rating [data-hear="pulse"]'); if (!b) return false; b.click(); await new Promise(r => setTimeout(r, 600));
      const ok = AU.kind === 'take' && !!AU.clicks && TAKE.aspects.tm.beats.length === 16; let ended = false; AU.clicks.addEventListener('ended', () => ended = true); stopSource(); await new Promise(r => setTimeout(r, 300)); TAKE.aspects.tm = old; renderRating(); return ok && ended; });
    r.errbox = await p.evaluate(() => typeof helixShowError === 'function' && !document.getElementById('errbox'));
    // On the device: no request leaves the site; the manifest and icon load, the Plex font is ours; the service worker keeps the files (a real outage: check/offline-check.mjs).
    if (ext.length) throw new Error('third-party requests: ' + ext.slice(0, 3));
    r.app = await p.evaluate(async () => { const m = await (await fetch('manifest.webmanifest')).json(), i = await fetch(m.icons[1].src); await document.fonts.load('16px "IBM Plex Sans"'); const auto = (await navigator.serviceWorker.getRegistrations()).length; await Promise.race([keepOffline(), new Promise(r => setTimeout(r, 15000))]); for (let k = 0; k < 150 && !(await (await caches.open('helix-1')).match('ref/rough.mp3')); k++) await new Promise(r => setTimeout(r, 100)); return { name: m.name, icon: i.ok, font: document.fonts.check('16px "IBM Plex Sans"'), kept: auto === 0 && !!(await (await caches.open('helix-1')).match('ref/rough.mp3')) && (await dropOffline(), true) }; }).catch(e => ({ err: String(e) }));
    if (r.app.name !== 'Voice Helix' || !r.app.icon || !r.app.font || !r.app.kept) throw new Error('on the device: ' + JSON.stringify(r.app)); r.app = true;
    // Live on a breathy high note (523 Hz, HNR 5 dB): no lock onto a subharmonic (check/breathy-live-bench.mjs).
    r.breathyLive = await p.evaluate(async () => { const sr = 44100, f = 523, L = sr * 2, x = new Float32Array(L); let e = 0, seed = 3; const R = () => (seed = seed * 16807 % 2147483647) / 2147483647 * 2 - 1; for (let i = 0; i < L; i++) { for (let h = 1; h <= 8; h++) x[i] += Math.sin(2 * Math.PI * f * h * i / sr) / (h * h); e += x[i] * x[i]; } const g = Math.sqrt(e / L * 3) * 10 ** (-5 / 20); for (let i = 0; i < L; i++) x[i] = 0.1 * (x[i] + g * R());
      const fs = await new Promise(res => { const a = [], d = makeDsp(m => { if (m.type === 'feat') a.push(m); else if (m.type === 'pong') { d.kill(); res(a); } }); d.post({ type: 'init', sr, hop: 0.02 }); for (let i = 0; i < L; i += 441) { const c = x.slice(i, i + 441); d.post({ type: 'audio', buf: c }, [c.buffer]); } d.post({ type: 'ping' }); }); const q = fs.filter(m => m.t > 0.3); return q.filter(m => m.voiced && Math.abs(1200 * Math.log2(m.f0 / f)) < 50).length / q.length; });
    if (r.breathyLive < 0.9) throw new Error('breathy live: ' + r.breathyLive);
    // Live Viterbi with one frame's lag: a note after silence shows within 90 ms, timed at its own frame, and a lone click stays unvoiced.
    r.lagLive = await p.evaluate(async () => { const sr = 44100, L = sr * 2, x = new Float32Array(L); for (let i = sr; i < L; i++) x[i] = 0.2 * Math.sin(2 * Math.PI * 220 * i / sr); x[sr / 2] = 0.9;
      const fs = await new Promise(res => { const a = [], d = makeDsp(m => { if (m.type === 'feat') a.push(m); else if (m.type === 'pong') { d.kill(); res(a); } }); d.post({ type: 'init', sr, hop: 0.02 }); for (let i = 0; i < L; i += 441) { const c = x.slice(i, i + 441); d.post({ type: 'audio', buf: c }, [c.buffer]); } d.post({ type: 'ping' }); }); const v = fs.filter(m => m.voiced); return { first: v[0]?.t, early: v.filter(m => m.t < 0.95).length }; });
    if (!(r.lagLive.first < 1.09 && r.lagLive.first > 1) || r.lagLive.early) throw new Error('lag live: ' + JSON.stringify(r.lagLive));
    r.nn = nn; r.lat = lat; r.tone = tone; r.say = say; const ok = !!r.session && !!r.oldMarks && !!r.drift && r.lean && !!r.tail && r.tsag && r.kdrift && !!r.timing && r.pulse && tone && say.ok && !!lat && lat.chip && lat.med > 0 && lat.med < 200 && nn.i === 0 && nn.kind === 'take' && nn.until && nn.on === 1 && nn.said && nn.key === 1 && nn.mark && nn.markPlay && nn.loop && nn.loopStop && nn.save && nn.share && nn.hear.n >= 1 && nn.hear.ok && nn.hear.worst && r.acc && r.errbox && r.cmp.kind === 'cmp' && r.cmp.ctx === 'running' && r.cmp.opts === 1 && r.cmp.said && r.stored && r.sp.kind === 'cmp' && r.sp.said && r.sp.nums && r.sp.dt <= 0.15 && r.spAll.kind === 'cmp' && r.spAll.said && r.rf.intro && r.rf.mn === 45 && r.rf.mx === 69 && r.rf.full && r.rf.finds && r.rwk && r.prof.tenor && r.prof.key && r.prof.br && r.prof.toC && r.swell && r.dyn.n === 3 && r.dyn.mx > 14 && r.dyn.mx < 26 && Math.abs(r.dyn.span - 10) < 2 && r.dyn.line && r.dyn.flat && r.vib.line && r.vib.even && r.vib.tiers && r.pb && r.wk && r.streak && r.breath.f2_breathy.clar < 23 && r.breath.f2_breathy.work === 1 && r.breath.m2_straight.clar > r.breath.f2_breathy.clar + 2 && r.breath.m2_straight.work === 0 && r.breath.m2_straight.tl === 1 && r.breath.f2_breathy.tl === 1 && r.week && (!touch || r.inView) && r.pitch > 0.75 && !errs.length && r.ctx === 'running' && r.playing === 'spot' && r.notes > 10 && r.slide === false && ab && slow.cents < 3 && r.k === 0.5 && Math.abs(slow.ratio - 2) < 0.01 && r.summary && r.warm.steps === 'Lip trill or straw glides|Clean starts|Pitch matching|Siren' && r.warm.text && r.warm.osc && r.warm.ctx === 'running' && r.progress === 5 && r.takes === 8 && seek > 0.45 && seek < 0.65;
    return { browser: name, ok, seek: +seek.toFixed(2), ab, slow, ...r, errs };
  } catch (e) { return { browser: name, ok: false, errs: [...errs, String(e).split('\n')[0]] }; }
  finally { if (b) { if (hold) await new Promise(r => setTimeout(r, hold * 1000)); await b.close(); open.delete(b); } }
}

let allOk = true;
// Without --only, each browser runs in its own node process: WebKit launched after Chrome and Firefox in one process
// hung at its first page on 2026-10-27 (alone it passes in ~40 s).
if (!only) {
  const { spawnSync } = await import('node:child_process');
  const rest = args.slice(1).filter((a, i, A) => a !== '--wait' && A[i - 1] !== '--wait');
  // WebKit also hangs now and then alone: a run killed by the timeout gets one retry; a failed check does not.
  for (const br of browsers) { const go = () => spawnSync(process.execPath, [fileURLToPath(import.meta.url), url, ...rest, '--only', br[0]], { stdio: 'inherit', timeout: 240000 }); let c = go(); if (c.signal) { console.log(`${br[0]} hung, retrying once`); c = go(); } allOk &&= c.status === 0; }
  process.exit(allOk ? 0 : 1);
}
for (const br of browsers) {
  let r = await run(br);
  for (let k = 1; !r.ok && br[0] === 'webkit-iphone' && k <= 2; k++) { console.error('webkit retry', k, r.errs); r = { ...(await run(br)), retried: k }; }  // first WebKit launch after a cold cache can time out
  console.log(JSON.stringify(r)); allOk &&= r.ok;
}
process.exit(allOk ? 0 : 1);
