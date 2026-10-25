// Slide style vs unwanted scoop, measured with the page's own code (scanTake, takeAspects) in headless Chrome.
// Synthetic phrases of 12 notes (0.9 s each, 0.15 s rests) at three voice ranges (bass 110 Hz, alto 196 Hz,
// soprano 330 Hz), 8 harmonics, light vibrato, jitter and noise. Classes: "style" slides into every note by
// one depth (1.5-4 st, ±10 %); "unwanted" scoops a random 2-5 notes by a random 1.5-4 st; "many" 6-9
// notes, random depth each (the hard case); "clean" none.
// Usage: node check/slide-bench.mjs http://localhost:<port>/ [trials per class and voice, default 10]
import { chromium } from 'playwright';
const url = process.argv[2], N = +(process.argv[3] || 10);
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()); const p = await b.newPage(); await p.goto(url); await p.waitForTimeout(1000);
const r = await p.evaluate(async N => {
  let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const out = { style: [0, 0], unwanted: [0, 0], clean: [0, 0], many: [0, 0] }, notes = { style: [0, 0], unwanted: [0, 0], many: [0, 0] };
  for (const F of [110, 196, 330]) for (const cls of ['style', 'unwanted', 'clean', 'many']) for (let t = 0; t < N; t++) {
    const sr = 48000, nd = 0.9, gap = 0.15, K = 12, n = Math.round(sr * K * (nd + gap)), x = new Float32Array(n);
    const deg = [0, 2, 4, 5, 7, 5, 4, 2, 0, 4, 7, 12], D = 1.5 + 2.5 * rnd(), sc = new Set();
    if (cls === 'style') for (let k = 0; k < K; k++) sc.add(k);
    if (cls === 'unwanted' || cls === 'many') { const m = cls === 'many' ? 6 + Math.floor(rnd() * 4) : 2 + Math.floor(rnd() * 4); while (sc.size < m) sc.add(Math.floor(rnd() * K)); }
    const dep = Array.from({ length: K }, () => cls === 'style' ? D * (0.9 + 0.2 * rnd()) : 1.5 + 2.5 * rnd());
    let ph = 0, jit = 0;
    for (let i = 0; i < n; i++) { const s = i / sr, k = Math.floor(s / (nd + gap)), u = s - k * (nd + gap);
      if (u > nd) { ph = 0; continue; }
      const sl = Math.min(1, u / 0.25), d = sc.has(k) ? -dep[k] * (1 - sl) * (1 - sl) : 0;
      if (i % 480 === 0) jit = 0.003 * (rnd() - 0.5);
      const f = F * Math.pow(2, (deg[k] + d + 0.15 * Math.sin(2 * Math.PI * 5.5 * s)) / 12) * (1 + jit);
      ph += 2 * Math.PI * f / sr; const env = Math.min(1, u / 0.03, (nd - u) / 0.03);
      let v = 0; for (let h = 1; h <= 8; h++) v += Math.sin(h * ph) / h; x[i] = env * (0.25 * v + 0.01 * (rnd() - 0.5)); }
    const buf = mkBuf(n, sr); buf.getChannelData(0).set(x);
    const a = (await scanTake(buf)).aspects;
    out[cls][0] += (cls === 'style') === a.slide.style ? 1 : 0; out[cls][1]++;
    if (cls !== 'clean') { notes[cls][0] += a.slide.n; notes[cls][1] += sc.size; }
  }
  return { out, notes };
}, N);
// Real trained voices that do not slide by style: the 14 VocalSet clips and the two public-domain references must not be called a style.
const real = await p.evaluate(async () => { const ids = ['f2', 'm2'].flatMap(v => ['belt', 'breathy', 'caro_straight', 'caro_vibrato', 'straight', 'vibrato', 'vocal_fry'].map(k => `demo/${v}_${k}.mp3`)).concat(['ref/polished.mp3', 'ref/rough.mp3']);
  const o = []; for (const u of ids) { const r = await fetch(u); if (!r.ok) continue; const buf = await new OfflineAudioContext(1, 1, 48000).decodeAudioData(await r.arrayBuffer());
    const a = (await scanTake(buf)).aspects; o.push([u, a.slide.style, a.slide.n, a.slide.of]); } return o; });
await b.close();
console.log('real voices called a style:', real.filter(x => x[1]).length, 'of', real.length, JSON.stringify(real));
const acc = ([k, n]) => `${k}/${n} (${(100 * k / n).toFixed(0)} %)`;
console.log(JSON.stringify(r));
for (const c of ['style', 'unwanted', 'clean', 'many']) console.log(c, 'classified right:', acc(r.out[c]));
for (const c of ['style', 'unwanted', 'many']) console.log(c, 'scoops detected / sung:', r.notes[c].join('/'));
