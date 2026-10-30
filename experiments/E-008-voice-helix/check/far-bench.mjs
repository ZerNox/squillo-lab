// Far vision (improveTake with farVib, the page's own code) in headless Chrome on VocalSet (Wilkins et al. 2018, CC BY 4.0, doi:10.5281/zenodo.1442513, not shipped): *_scales_straight_a.wav and *_long_straight_a.wav.
// Each clip goes through the take path, is rendered spotless and far, and the far render goes through the take path again. Reported per file, then median [min-max]:
// vibrato asked vs read back (rate, peak extent); notes off the grid; 'still your voice' proxy: RMS difference in dB of the long-term 1/3-octave spectrum (500 Hz-8 kHz; bands below f0 hold only room noise), take vs far, take vs spotless (level matched). A proxy, not a listener.
// Usage: node check/far-bench.mjs http://localhost:<port>/ <dir> [max files]
import { chromium } from 'playwright'; import { readdirSync, readFileSync } from 'fs';
const [url, dir, max] = process.argv.slice(2), files = readdirSync(dir).filter(f => /^[fm]\d+_(scales|long)_straight_a\.wav$/.test(f)).slice(0, +(max || 40));
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()), p = await b.newPage();
await p.route('**/vs/*', r => r.fulfill({ body: readFileSync(dir + '/' + r.request().url().split('/vs/')[1]), contentType: 'audio/wav' }));
await p.goto(url); await p.waitForTimeout(1000);
const rows = [];
for (const f of files) rows.push(await p.evaluate(async f => {
  const scan = async buf => { const F = await trackTake(buf); viterbiF0(F); trimEdges(F, buf); const S = new Stats(); for (const m of F) ingest(S, m, 'take'); const sc = takeSpots(S); return { S, fr: sc.frames, off: sc.aspects.off }; };
  const lts = buf => { const x = buf.getChannelData(0), sr = buf.sampleRate, N = 4096, B = []; for (let c = 500; c < 8000; c *= 2 ** (1 / 3)) B.push([c / 2 ** (1 / 6), c * 2 ** (1 / 6), 0]);
    const re = new Float64Array(N), im = new Float64Array(N), fft = () => { for (let i = 1, j = 0; i < N; i++) { let b = N >> 1; for (; j & b; b >>= 1) j ^= b; j ^= b; if (i < j) { [re[i], re[j]] = [re[j], re[i]]; [im[i], im[j]] = [im[j], im[i]]; } } for (let L = 2; L <= N; L <<= 1) { const w = -2 * Math.PI / L; for (let i = 0; i < N; i += L) for (let k = 0; k < L / 2; k++) { const c = Math.cos(w * k), s = Math.sin(w * k), a = i + k, d = a + L / 2, tr = re[d] * c - im[d] * s, ti = re[d] * s + im[d] * c; re[d] = re[a] - tr; im[d] = im[a] - ti; re[a] += tr; im[a] += ti; } } };
    for (let o = 0; o + N < x.length; o += N >> 1) { for (let i = 0; i < N; i++) { re[i] = x[o + i] * (0.5 - 0.5 * Math.cos(2 * Math.PI * i / N)); im[i] = 0; } fft(); for (const q of B) for (let k = Math.ceil(q[0] * N / sr); k < q[1] * N / sr; k++) q[2] += re[k] ** 2 + im[k] ** 2; }
    return B.map(q => 10 * Math.log10(q[2] + 1e-12)); };
  const dist = (a, c) => { const d = a.map((v, i) => v - c[i]), m = d.reduce((s, v) => s + v, 0) / d.length; return Math.sqrt(d.reduce((s, v) => s + (v - m) ** 2, 0) / d.length); };
  const buf = await new OfflineAudioContext(1, 1, 44100).decodeAudioData(await (await fetch('vs/' + f)).arrayBuffer());
  const A = await scan(buf), fv = { rate: 5.8, ext: 0.45, notes: 0 }, spot = improveTake(buf, A.fr, 1, A.off), far = improveTake(buf, A.fr, 1, A.off, fv), B = await scan(far), v = takeVibrato(B.S);
  const L = lts(buf); return { f, notes: fv.notes, n: v.n, long: v.long, rate: v.rate && v.rate[0], ext: v.ext && v.ext[0], far: dist(L, lts(far)), spot: dist(L, lts(spot)) };
}, f));
await b.close();
const med = k => { const a = rows.map(r => r[k]).filter(v => v !== null && v !== undefined).sort((x, y) => x - y); if (!a.length) return 'none'; return `${a[a.length >> 1].toFixed(2)} [${a[0].toFixed(2)}-${a[a.length - 1].toFixed(2)}] n ${a.length}`; };
for (const r of rows) console.log(r.f, r.notes, r.n + '/' + r.long, r.rate && r.rate.toFixed(2), r.ext && r.ext.toFixed(2), r.far.toFixed(2), r.spot.toFixed(2));
console.log(`files ${rows.length}, far notes ${rows.reduce((s, r) => s + r.notes, 0)}; read back rate ${med('rate')} Hz (asked 5.8), extent ${med('ext')} st (asked 0.45); spectrum dB far ${med('far')}, spotless ${med('spot')}`);
