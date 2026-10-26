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
    await tap(p.locator('#bPlaySpot')); await p.waitForTimeout(1200);
    await p.selectOption('#speed', '0.5'); await p.waitForTimeout(1500);
    const r = await p.evaluate(() => ({ k: AU.play && AU.play.k, ctx: AU.ctx && AU.ctx.state, playing: AU.play && AU.play.which, notes: TAKE.aspects.perf.length, slide: TAKE.aspects.slide && TAKE.aspects.slide.style, spots: TAKE.segs.length, summary: !document.getElementById('rating').hidden, acc: /97\.6 ± 0\.7 %/.test((document.getElementById('pitchAcc') || {}).textContent || ''), progress: document.querySelectorAll('#rating table.prog tr').length, takes: JSON.parse(localStorage.getItem('helix.takes.v1')).length }));
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
      return { n: v.n, long: v.long, rate: v.rate && +v.rate[0].toFixed(2), line: /^Vibrato on 5 of 5 long notes: 6\.0 ± 0\.[0-9] Hz, ±0\.[45][0-9]/.test(vibLine(v)[0] || ''), even: !!v.rcv && v.rcv[0] < 6 && /^Vibrato evenness: rate varies .*as even as/.test(vibLine(v)[1] || '') }; });
    // Personal bests: against 2 earlier takes (best 4.0 ¢, 2.0 s), a 2.5 ¢ / 3 s note is a new best; a 4.5 ¢ one only matches.
    r.pb = await p.evaluate(() => { const k = 'helix.takes.v1', keep = localStorage.getItem(k); localStorage.setItem(k, JSON.stringify([{ d: 1, lb: [4, 2] }, { d: 2, lb: [5, 1.5] }]));
      const P = w => [{ t0: 1, t1: 4, c: 3, wob: w }, { t0: 5, t1: 5.5, c: 2, wob: 0.5 }]; const a = pbLines(P(2.5), 9), b = pbLines(P(4.5), 9); localStorage.setItem(k, keep);
      return a.length === 2 && /^Personal best: your steadiest long note.*2\.5 ¢.*4\.0 ¢/.test(a[0]) && /3\.0 s at 0:01.*2\.0 s/.test(a[1]) && /matches your best/.test(b[0]); });
    // Streak: 7 seeded daily takes + today's = 8 days in a row; without today it still counts 7 and asks to sing today.
    r.streak = await p.evaluate(() => { const t = document.querySelector('#rating p.streak'), now = Date.now(), H = [1, 2, 3].map(i => ({ d: now - i * 864e5, sung: 30 })), S = streakInfo(H, now);
      return !!t && /^8 days in a row · 8 days sung/.test(t.textContent) && S.n === 3 && !S.today && /sing today/.test(streakLine(H)); });
    r.errbox = await p.evaluate(() => typeof helixShowError === 'function' && !document.getElementById('errbox'));
    r.nn = nn; const ok = nn.i === 0 && nn.kind === 'take' && nn.until && nn.on === 1 && nn.said && nn.key === 1 && nn.mark && nn.markPlay && r.acc && r.errbox && r.cmp.kind === 'cmp' && r.cmp.ctx === 'running' && r.cmp.opts === 1 && r.cmp.said && r.stored && r.sp.kind === 'cmp' && r.sp.said && r.sp.nums && r.sp.dt <= 0.15 && r.spAll.kind === 'cmp' && r.spAll.said && r.rf.intro && r.rf.mn === 45 && r.rf.mx === 69 && r.rf.full && r.rf.finds && r.prof.tenor && r.prof.key && r.prof.br && r.prof.toC && r.vib.line && r.vib.even && r.pb && r.streak && (!touch || r.inView) && r.pitch > 0.75 && !errs.length && r.ctx === 'running' && r.playing === 'spot' && r.notes > 10 && r.slide === false && ab && slow.cents < 3 && r.k === 0.5 && Math.abs(slow.ratio - 2) < 0.01 && r.summary && r.warm.steps === 'Lip trill or straw glides|Clean starts|Pitch matching|Siren' && r.warm.text && r.warm.osc && r.warm.ctx === 'running' && r.progress === 5 && r.takes === 8 && seek > 0.45 && seek < 0.65;
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
