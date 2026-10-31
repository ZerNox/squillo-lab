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
import { copyFileSync, existsSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
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
    if (!c.__mute) { c.__mute = c.createGain(); c.__mute.gain.value = 0; con.call(c.__mute, d); } con.call(this, c.__mute, ...r); return d; }
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
    const p = await c.newPage();
    if (headed) console.error(name, 'window', await p.evaluate(() => [outerWidth, outerHeight, screen.availWidth, screen.availHeight].join(' ')));
    p.on('pageerror', e => errs.push(String(e)));
    p.on('console', m => { if (m.type() === 'error' && !/favicon/.test(m.location().url)) errs.push(m.text()); });
    await p.goto(url, { waitUntil: 'load' }); await p.waitForTimeout(1500);
    await p.screenshot({ path: join(out, `${name}-start.png`) });
    const touch = !!ctxOpt.hasTouch, tap = l => touch ? l.tap() : l.click();
    // Screen lag: the demo voice runs live 3 s; the chip shows the measured audio-to-paint lag (median, p90).
    await tap(p.locator('#bDemo')); await p.waitForTimeout(3000);
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
    await tap(p.locator('#vHelix'));
    if (touch) { await tap(p.getByRole('button', { name: 'Recording' })); await p.waitForTimeout(300); await p.setInputFiles('#file', file); }
    else { const [fc] = await Promise.all([p.waitForEvent('filechooser'), p.getByRole('button', { name: 'Recording' }).click()]); await fc.setFiles(file); }
    await p.waitForFunction(() => !document.getElementById('bPlaySpot').disabled, null, { timeout: 120000 });
    // Phone: the scanned take comes into view by itself (play row and timeline on screen, no scrolling by hand).
    await p.waitForTimeout(900); const inView = await p.evaluate(() => { const r = document.getElementById('takebar').getBoundingClientRect(); return r.top >= 0 && r.bottom <= innerHeight; });
    await p.screenshot({ path: join(out, `${name}-take-first.png`) });
    const bar = p.locator('#takebar'); await bar.scrollIntoViewIfNeeded(); await bar.screenshot({ path: join(out, `${name}-timeline.png`) });
    await p.screenshot({ path: join(out, `${name}-take.png`) });
    const bb = await bar.boundingBox(); const pos = { position: { x: bb.width * 0.5, y: 10 } };
    touch ? await bar.tap(pos) : await bar.click(pos); await p.waitForTimeout(1200);
    const seek = await p.evaluate(() => AU.play ? (AU.ctx.currentTime - AU.play.t0) / AU.play.dur : -1);
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
    const vow = await p.evaluate(() => { const r = readVowel(693, 1233, 220), hi = readVowel(693, 1233, 700), ee = readVowel(355, 1963, 300); const n = TAKE.aspects.perf.find(x => x.vow && x.vow.sure), i = n ? TAKE.aspects.perf.indexOf(n) : -1; if (n) { TAKE.ni = i - 1; stepNote(1); TAKE.ni = -1; } const flat = envVowel(new Array(14).fill(0), 220), slope = envVowel(Array.from({ length: 14 }, (_, j) => 3 * (j - 6.5)), 220); return { ok: r.v === 'a' && r.sure && hi === null && ee.v === 'i' && flat && slope.v === flat.v && envVowel(new Array(14).fill(0), 700) === null, chip: !!document.getElementById('mVow'), said: !n || /sounds like “(ah|eh|ee|oh|oo)”/.test(document.getElementById('takeInfo').textContent) }; });
    if (!vow.ok || !vow.chip || !vow.said) throw new Error('vowel reading: ' + JSON.stringify(vow));
    if (seg.leg !== 4 || seg.vib !== 1 || !seg.perf) throw new Error('note segmentation: ' + JSON.stringify(seg));
    // Note by note: two taps on note ▶ then one on ◀ note land on the first note, play just it and say its numbers; → key goes to note 2.
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
    { const bt = p.locator('#rating [data-hear="far"]'); nn.farAb = await bt.count(); if (nn.farAb) { await tap(bt); await p.waitForTimeout(300); nn.farAb = await p.evaluate(() => AU.kind === 'ab' && AU.source.loop && /far/.test(AU.ab)); await p.evaluate(() => stopSource()); } if (!nn.farAb) throw new Error('far A/B: ' + nn.farAb); await tap(p.locator('#bPlaySpot')); await p.waitForTimeout(1000); }
    nn.vowels = await p.evaluate(() => { const l = vowelLine(TAKE.aspects.perf), few = vowelLine([{ vow: { v: 'a', sure: true } }]), many = vowelLine(Array.from({ length: 6 }, (_, i) => ({ vow: { v: i ? 'i' : 'a', sure: true } }))); return { n: l.length, shown: !l.length || $('rating').textContent.includes('Vowels heard'), ok: !few.length && /“ee” on 5 notes, “ah” on 1 note/.test(many[0]) }; });
    if (!nn.vowels.shown || !nn.vowels.ok) throw new Error('vowels line: ' + JSON.stringify(nn.vowels));
    nn.ring = await p.evaluate(() => ({ v: TAKE.aspects.ring, line: /Ring: singing power ratio/.test($('rating').textContent), row: Number.isFinite(loadHist().slice(-1)[0].ring) && !RATED.some(x => x.k === 'ring') }));
    if (!(nn.ring.v > -60 && nn.ring.v < 10 && nn.ring.line && nn.ring.row)) throw new Error('ring: ' + JSON.stringify(nn.ring));
    nn.room = await p.evaluate(() => { const c = (rms, v) => ({ rms, voiced: v, cs: v ? [[220, 0.1]] : [[300, 0.8]] }), fs = [...Array(30).fill(c(0.01, false)), ...Array(90).fill(c(0.1, true))]; return { snr: roomSnr(fs), lo: roomLine({ room: 5 })[0], hi: roomLine({ room: 25 })[0], none: roomFloor(Array(99).fill(c(0.1, true))) }; });
    if (!(Math.abs(nn.room.snr - 20) < 0.1 && /Noisy room/.test(nn.room.lo) && /Quiet room/.test(nn.room.hi) && nn.room.none === 0)) throw new Error('room: ' + JSON.stringify(nn.room));
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
    // Match and measure: step to Clean starts, five synthetic sung notes 10 ¢ sharp fed in place of the mic; the session is read and kept, a second one compares.
    r.match = await p.evaluate(async () => { stopSource(); const old = useMic; useMic = async () => { AU.kind = 'mic'; }; const oldS = MATCH_S; WARM.i = 1; renderWarm(); const hold = AU.kind; const run = async () => { document.getElementById('wMatch').click(); const W = WARM.plan, ms = warmNotes(W), sr = AU.sr || AU.ctx.sampleRate;
        for (const m of ms) { for (let i = 0; i < 200 && !DRILL.rec; i++) await new Promise(r => setTimeout(r, 25)); const n = sr * 2, x = new Float32Array(n); let ph = 0; for (let i = 0; i < n; i++) { ph += 2 * Math.PI * 440 * Math.pow(2, (m + 0.1 - 69) / 12) / sr; if (i > 0.2 * sr && i < 1.8 * sr) for (let h = 1; h <= 6; h++) x[i] += 0.15 * Math.sin(h * ph) / h; } DRILL.rec.push(x); while (DRILL.rec) await new Promise(r => setTimeout(r, 25)); }
        for (let i = 0; i < 200 && MATCH.busy; i++) await new Promise(r => setTimeout(r, 25)); }; await run(); const a = document.getElementById('matchBox').textContent; await run(); const b = document.getElementById('matchBox').textContent; useMic = old; const k = loadMatch(); stopSource(); return { a, b, n: k.length, off: k[0] && k[0].off, spark: !!document.querySelector('#matchBox svg'), hold, ok: /5 of 5 landed/.test(a) && /About the same/.test(b) && k.length === 2 && Math.abs(k[0].off - 10) < 3 }; });
    await p.locator('#warmup').screenshot({ path: join(out, `${name}-match.png`) }); if (!r.match.ok) throw new Error('match: ' + JSON.stringify(r.match));
    // High notes: a straight E5 and D6 must read on the note, not at a fraction of it (2026-10-31, check/high-bench.mjs).
    r.high = await p.evaluate(async () => { const o = []; for (const m of [76, 86]) { const sr = 48000, n = sr * 2, b = mkBuf(n, sr), x = b.getChannelData(0); for (let i = 0.2 * sr; i < 1.8 * sr; i++) for (let h = 1; h <= 8; h++) x[i] += 0.2 * Math.sin(2 * Math.PI * h * 440 * Math.pow(2, (m - 69) / 12) * i / sr) / (h * h); const fs = await trackTake(b); viterbiF0(fs); const v = fs.filter(f => f.voiced).map(f => 69 + 12 * Math.log2(f.f0 / 440) - m).sort((a, c) => a - c); o.push(v.length > 40 && Math.abs(v[v.length >> 1]) < 0.3); } return o; });
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
    r.sp = await p.evaluate(() => { const L = TAKE.lastSP; return { kind: AU.kind, said: /Same phrase:/.test(document.getElementById('takeInfo').textContent), nums: /Then vs today .*off [0-9]+ ± [0-9]+ → [0-9]+ ± [0-9]+ ¢ \(within the ±\)/.test(document.getElementById('takeInfo').textContent), dt: L && L.m ? +Math.abs(L.m.t0 - L.ph.t0).toFixed(2) : null, cost: L && L.m ? +L.m.cost.toFixed(2) : null }; });
    // All kept takes: a second copy stored two days earlier; with "all" picked the phrase is found in both, oldest first, then today.
    await p.evaluate(async () => { await storeAudio(Date.now() - 2 * 864e5, TAKE.buf); });
    await p.waitForFunction(() => [...document.querySelectorAll('#cmpSel option')].some(o => o.value === 'all'), null, { timeout: 10000 }).catch(() => {});
    await p.selectOption('#cmpSel', 'all'); await tap(p.locator('#bSamePh'));
    await p.waitForFunction(() => /kept takes, oldest|not found/.test(document.getElementById('takeInfo').textContent), null, { timeout: 30000 }).catch(() => {});
    r.spAll = await p.evaluate(() => ({ kind: AU.kind, said: /Same phrase in 2 of 2 kept takes, oldest first: .* then today [0-9]+ ± [0-9]+ ¢ off/.test(document.getElementById('takeInfo').textContent) }));
    // Range finder: the intro shows in the profile; three synthetic steps (lowest A2, highest A4) go through the page's analysis and show in the profile.
    r.rf = await p.evaluate(async () => { const intro = !!document.getElementById('rfGo'); const sr = 48000, mk = (T, m) => { const n = sr * T, b = mkBuf(n, sr), x = b.getChannelData(0); let ph = 0;
        for (let i = 0; i < n; i++) { ph += 2 * Math.PI * 440 * Math.pow(2, (m(i / sr) - 69) / 12) / sr; for (let h = 1; h <= 6; h++) x[i] += 0.2 * Math.sin(h * ph) / h; } return b; };
      const res = await rangeAnalyse([mk(3, s => s < 1.5 ? 52 - 7 * s / 1.5 : 45), mk(3, s => s < 1.5 ? 57 + 12 * s / 1.5 : 69), null]); renderProfile('x');
      const t = document.getElementById('profile').textContent; localStorage.removeItem(RANGE_KEY); return { intro, mn: res && Math.round(res.mn), mx: res && Math.round(res.mx), full: /Full range sung so far A2/.test(t), finds: /1 range find/.test(t) }; });
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
    // Personal bests: against 2 earlier takes (best 4.0 ¢, 2.0 s), a 2.5 ¢ / 3 s note is a new best; a 4.5 ¢ one only matches.
    r.pb = await p.evaluate(() => { const k = 'helix.takes.v1', keep = localStorage.getItem(k); localStorage.setItem(k, JSON.stringify([{ d: 1, lb: [4, 2] }, { d: 2, lb: [5, 1.5] }]));
      const P = w => [{ t0: 1, t1: 4, c: 3, wob: w }, { t0: 5, t1: 5.5, c: 2, wob: 0.5 }]; const a = pbLines(P(2.5), 9), b = pbLines(P(4.5), 9); localStorage.setItem(k, keep);
      return a.length === 2 && /^Personal best: your steadiest long note.*2\.5 ¢.*4\.0 ¢/.test(a[0]) && /3\.0 s at 0:01.*2\.0 s/.test(a[1]) && /matches your best/.test(b[0]); });
    // Last week: 2 takes from 2-3 days ago (best 4.0 ¢); last three long notes at 2.0-2.8 ¢ beat it, one at 3.5 ¢ does not; old takes (>7 d) ignored.
    r.wk = await p.evaluate(() => { const k = 'helix.takes.v1', keep = localStorage.getItem(k), now = Date.now(); localStorage.setItem(k, JSON.stringify([{ d: now - 2 * 864e5, lb: [4, 2] }, { d: now - 3 * 864e5, lb: [5, 1] }, { d: now - 20 * 864e5, lb: [1, 1] }]));
      const P = w => [{ t0: 0, t1: 2, c: 3, wob: 9 }, ...w.map((x, i) => ({ t0: 3 + 2 * i, t1: 4.5 + 2 * i, c: 3, wob: x }))]; const a = lastWeekLine(P([2, 2.4, 2.8]), now), b = lastWeekLine(P([2, 3.5, 2.8]), now); localStorage.setItem(k, keep);
      return /^Your last three long notes \(2\.0, 2\.4, 2\.8 ¢ wobble\).*your 2 takes.*best 4\.0 ¢/.test(a) && b === ''; });
    // Streak: 7 seeded daily takes + today's = 8 days in a row; without today it still counts 7 and asks to sing today.
    r.streak = await p.evaluate(() => { const t = document.querySelector('#rating p.streak'), now = Date.now(), H = [1, 2, 3].map(i => ({ d: now - i * 864e5, sung: 30 })), S = streakInfo(H, now);
      return !!t && /^8 days in a row · 8 days sung/.test(t.textContent) && S.n === 3 && !S.today && /sing today/.test(streakLine(H)); });
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
    // Key drift on the progress line: 12 seeded takes whose drift falls 70 to 15 ¢ (two without a drift) read 'better', the row exists, not rated.
    r.kdrift = await p.evaluate(() => { const H = Array.from({ length: 12 }, (_, i) => { const r = { d: Date.now() - (12 - i) * 36e5, score: 0.6, inton: 10, stab: 5, onset: 0.1, clar: 25, tone: -1 }; if (i !== 2 && i !== 9) r.kdrift = 70 - i * 5; return r; });
      const old = localStorage.getItem('helix.takes.v1'); localStorage.setItem('helix.takes.v1', JSON.stringify(H)); const d = document.createElement('div'); d.innerHTML = renderProgress(); localStorage.setItem('helix.takes.v1', old);
      const row = [...d.querySelectorAll('table.prog tr')].find(t => /key drift/.test(t.textContent)); return !!row && /better than the takes before/.test(row.textContent) && !RATED.some(x => x.k === 'kdrift'); });
    // Timing: 16 onsets on a 0.5 s pulse read about the jitter, a 12 % slowing is named with an exercise, free onsets find no pulse; rhythm row exists, not rated.
    r.timing = await p.evaluate(() => { let s = 5; const rnd = () => (s = (s * 16807) % 2147483647) / 2147483647, st = [1, 2, 1, 3, 2, 1, 2, 2, 1, 1, 3, 1, 2, 1, 2];
      const mk = (c, j) => { let g = 0; return [0, ...st.map((x, i) => { g += x * 0.5 * (1 + c * i / 14); return g + j * (rnd() - 0.5); })]; }, a = pulseFit(mk(0, 0.05)), b = pulseFit(mk(0.12, 0));
      let g = 0; const f = pulseFit(Array.from({ length: 16 }, () => g += 0.25 + 1.05 * rnd())), H = Array.from({ length: 8 }, (_, i) => ({ d: Date.now() - (8 - i) * 36e5, score: 0.6, inton: 10, stab: 5, onset: 0.1, clar: 25, tone: -1, rhythm: 90 - i * 8 }));
      const old = localStorage.getItem('helix.takes.v1'); localStorage.setItem('helix.takes.v1', JSON.stringify(H)); const d = document.createElement('div'); d.innerHTML = renderProgress(); localStorage.setItem('helix.takes.v1', old);
      const row = [...d.querySelectorAll('table.prog tr')].some(t => /rhythm spread/.test(t.textContent)); return a.pulse && a.sd < 30 && /^Steady rhythm/.test(timingLine(a, true)[0] || '') && b.pulse && /^tempo \(you slowed/.test(timingLine(b, false)[0] || '') && !f.pulse && /^Free timing/.test(timingLine(f, true)[0] || '') && !timingLine(f, false).length && row && !RATED.some(x => x.k === 'rhythm') && { sd: +a.sd.toFixed(0), change: +b.change.toFixed(0), r: +f.ratio.toFixed(2) }; });
    // Hear it with your pulse: a take with a found pulse gets the button; a tap plays the take with the click oscillator running, and stopping ends the clicks.
    r.pulse = await p.evaluate(async () => { const old = TAKE.aspects.tm; TAKE.aspects.tm = { ...pulseFit(Array.from({ length: 16 }, (_, i) => 1 + i * 0.6)) }; renderRating(); const b = document.querySelector('#rating [data-hear="pulse"]'); if (!b) return false; b.click(); await new Promise(r => setTimeout(r, 600));
      const ok = AU.kind === 'take' && !!AU.clicks && TAKE.aspects.tm.beats.length === 16; let ended = false; AU.clicks.addEventListener('ended', () => ended = true); stopSource(); await new Promise(r => setTimeout(r, 300)); TAKE.aspects.tm = old; renderRating(); return ok && ended; });
    r.errbox = await p.evaluate(() => typeof helixShowError === 'function' && !document.getElementById('errbox'));
    r.nn = nn; r.lat = lat; r.tone = tone; r.say = say; const ok = !!r.drift && r.kdrift && !!r.timing && r.pulse && tone && say.ok && !!lat && lat.chip && lat.med > 0 && lat.med < 200 && nn.i === 0 && nn.kind === 'take' && nn.until && nn.on === 1 && nn.said && nn.key === 1 && nn.mark && nn.markPlay && nn.loop && nn.loopStop && nn.hear.n >= 1 && nn.hear.ok && nn.hear.worst && r.acc && r.errbox && r.cmp.kind === 'cmp' && r.cmp.ctx === 'running' && r.cmp.opts === 1 && r.cmp.said && r.stored && r.sp.kind === 'cmp' && r.sp.said && r.sp.nums && r.sp.dt <= 0.15 && r.spAll.kind === 'cmp' && r.spAll.said && r.rf.intro && r.rf.mn === 45 && r.rf.mx === 69 && r.rf.full && r.rf.finds && r.prof.tenor && r.prof.key && r.prof.br && r.prof.toC && r.swell && r.dyn.n === 3 && r.dyn.mx > 14 && r.dyn.mx < 26 && Math.abs(r.dyn.span - 10) < 2 && r.dyn.line && r.dyn.flat && r.vib.line && r.vib.even && r.vib.tiers && r.pb && r.wk && r.streak && r.breath.f2_breathy.clar < 23 && r.breath.f2_breathy.work === 1 && r.breath.m2_straight.clar > r.breath.f2_breathy.clar + 2 && r.breath.m2_straight.work === 0 && r.breath.m2_straight.tl === 1 && r.breath.f2_breathy.tl === 1 && r.week && (!touch || r.inView) && r.pitch > 0.75 && !errs.length && r.ctx === 'running' && r.playing === 'spot' && r.notes > 10 && r.slide === false && ab && slow.cents < 3 && r.k === 0.5 && Math.abs(slow.ratio - 2) < 0.01 && r.summary && r.warm.steps === 'Lip trill or straw glides|Clean starts|Pitch matching|Siren' && r.warm.text && r.warm.osc && r.warm.ctx === 'running' && r.progress === 5 && r.takes === 8 && seek > 0.45 && seek < 0.65;
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
  for (let k = 1; !r.ok && br[0] === 'webkit-iphone' && k <= 2; k++) r = { ...(await run(br)), retried: k };  // first WebKit launch after a cold cache can time out
  console.log(JSON.stringify(r)); allOk &&= r.ok;
}
process.exit(allOk ? 0 : 1);
