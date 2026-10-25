// Checks the Voice Helix page in Chrome (desktop), Firefox (desktop) and WebKit at an iPhone 15's
// size and touch: the page loads without errors, a public-domain reference clip loads as the take,
// the take is scanned (performance timeline, summary, progress lines over seeded earlier takes), a tap on the timeline plays from there, a tap on a spot loops it A/B with spotless, 0.5x playback keeps the pitch, the reference's scoops are not taken for a slide style, the take pitch tracker holds a breathy tone, the warm-up targets the seeded takes' weakest aspects and plays a guide tone, the voice profile reads the seeded range and suggests a key around the seeded register break, and
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
    await c.addInitScript(() => { try { if (!localStorage.getItem('helix.takes.v1')) localStorage.setItem('helix.takes.v1', JSON.stringify(Array.from({ length: 7 }, (_, i) => ({ d: Date.now() - (7 - i) * 864e5, sung: 30, score: 0.6 + 0.02 * i, inton: 25 - i, stab: 5 - 0.2 * i, onset: 0.2, tone: 12, lo: 52, hi: 62, mn: 48, mx: 67, br: [60.2] })))); } catch (e) {} });
    const p = await c.newPage();
    if (headed) console.error(name, 'window', await p.evaluate(() => [outerWidth, outerHeight, screen.availWidth, screen.availHeight].join(' ')));
    p.on('pageerror', e => errs.push(String(e)));
    p.on('console', m => { if (m.type() === 'error' && !/favicon/.test(m.location().url)) errs.push(m.text()); });
    await p.goto(url, { waitUntil: 'load' }); await p.waitForTimeout(1500);
    await p.screenshot({ path: join(out, `${name}-start.png`) });
    const touch = !!ctxOpt.hasTouch, tap = l => touch ? l.tap() : l.click();
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
    await tap(p.locator('#bPlaySpot')); await p.waitForTimeout(1200);
    await p.selectOption('#speed', '0.5'); await p.waitForTimeout(1500);
    const r = await p.evaluate(() => ({ k: AU.play && AU.play.k, ctx: AU.ctx && AU.ctx.state, playing: AU.play && AU.play.which, notes: TAKE.aspects.perf.length, slide: TAKE.aspects.slide && TAKE.aspects.slide.style, spots: TAKE.segs.length, summary: !document.getElementById('rating').hidden, progress: document.querySelectorAll('#rating table.prog tr').length, takes: JSON.parse(localStorage.getItem('helix.takes.v1')).length }));
    await p.locator('table.prog').screenshot({ path: join(out, `${name}-progress.png`) });
    // Take pitch tracker: a breathy 600 Hz tone (noise at about -10 dB) must come out at 600 Hz on most frames
    // (live tracker: 0 % at this noise, it locks on 75 Hz; take tracker 81 %, LOG 2026-10-25).
    const pitch = await p.evaluate(async () => { const sr = 48000, n = sr * 2, b = mkBuf(n, sr), x = b.getChannelData(0); let s = 5;
      for (let i = 0; i < n; i++) { s = (s * 16807) % 2147483647; const ph = 2 * Math.PI * 600 * i / sr; x[i] = 0.2 * (Math.sin(ph) + 0.5 * Math.sin(2 * ph) + 0.3 * Math.sin(3 * ph)) + 0.25 * (s / 2147483647 - 0.5); }
      const fs = await trackTake(b); viterbiF0(fs); const v = fs.filter(m => m.t > 0.2 && m.voiced); return v.filter(m => Math.abs(1200 * Math.log2(m.f0 / 600)) < 50).length / Math.max(1, fs.filter(m => m.t > 0.2).length); });
    r.pitch = +pitch.toFixed(3); r.inView = inView;
    // Warm-up from the seeded takes: onsets (0.2 scoops/note) and intonation (~21 ¢) are furthest from the trained median, so they are the targeted steps; guide tone plays.
    await tap(p.locator('#bWarm')); await p.waitForTimeout(600); await p.locator('#warmup').screenshot({ path: join(out, `${name}-warmup.png`) });
    await tap(p.locator('#wNext')); await p.waitForTimeout(400);
    r.warm = await p.evaluate(() => ({ steps: WARM.plan.steps.map(s => s.name).join('|'), why: WARM.plan.why.length, osc: !!WARM.osc, ctx: (AU.ctx || WARM.ctx).state, text: /Clean starts/.test(document.getElementById('warmup').textContent) }));
    // Voice profile from the seeded takes (comfortable E3-D4, centre 57: tenor); a G3-D5 melody in G moves down 7 to C.
    await tap(p.locator('#bProf')); await p.waitForTimeout(400); await p.locator('#profile').screenshot({ path: join(out, `${name}-profile.png`) });
    r.prof = await p.evaluate(() => { const t = document.getElementById('profile').textContent; return { tenor: /fits a tenor/.test(t), key: /down 7 semitones/.test(t), br: /around C4/.test(t) && /crosses your break/.test(t) }; });
    await p.fill('#pKey', 'G'); await tap(p.locator('#pGo')); r.prof.toC = await p.evaluate(() => /key of C/.test(document.getElementById('pOut').textContent));
    const ok = r.prof.tenor && r.prof.key && r.prof.br && r.prof.toC && (!touch || r.inView) && r.pitch > 0.75 && !errs.length && r.ctx === 'running' && r.playing === 'spot' && r.notes > 10 && r.slide === false && ab && slow.cents < 3 && r.k === 0.5 && Math.abs(slow.ratio - 2) < 0.01 && r.summary && r.warm.steps === 'Lip trill or straw glides|Clean starts|Pitch matching|Siren' && r.warm.text && r.warm.osc && r.warm.ctx === 'running' && r.progress === 5 && r.takes === 8 && seek > 0.45 && seek < 0.65;
    return { browser: name, ok, seek: +seek.toFixed(2), ab, slow, ...r, errs };
  } catch (e) { return { browser: name, ok: false, errs: [...errs, String(e).split('\n')[0]] }; }
  finally { if (b) { if (hold) await new Promise(r => setTimeout(r, hold * 1000)); await b.close(); open.delete(b); } }
}

let allOk = true;
for (const br of browsers) {
  let r = await run(br);
  for (let k = 1; !r.ok && br[0] === 'webkit-iphone' && k <= 2; k++) r = { ...(await run(br)), retried: k };  // first WebKit launch after a cold cache can time out
  console.log(JSON.stringify(r)); allOk &&= r.ok;
}
process.exit(allOk ? 0 : 1);
