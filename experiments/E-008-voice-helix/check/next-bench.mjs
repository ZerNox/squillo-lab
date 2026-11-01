// Next step (improveTake with one point, the page's own code) in headless Chrome on VocalSet (Wilkins et al. 2018, CC BY 4.0, doi:10.5281/zenodo.1442513, not shipped).
// Each clip is scanned, each point rendered alone at 0.5 and rescanned; intonation, steadiness and scoop share read back, median change [min-max] of the three. The moved point should fall, the others stay.
// Also, spectrum change in dB (as far-bench). Usage: node check/next-bench.mjs http://localhost:<port>/ <dir> [max files]
import { chromium } from 'playwright'; import { readdirSync, readFileSync } from 'fs';
const [url, dir, max] = process.argv.slice(2), all = readdirSync(dir).filter(f => /^[fm]\d+_.*\.wav$/.test(f)).sort(), step = Math.max(1, Math.floor(all.length / +(max || 40))), files = all.filter((_, i) => i % step === 0).slice(0, +(max || 40));
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()), p = await b.newPage();
await p.route('**/vs/*', r => r.fulfill({ body: readFileSync(dir + '/' + r.request().url().split('/vs/')[1]), contentType: 'audio/wav' }));
await p.goto(url); await p.waitForTimeout(1000);
// Synthetic: 12 notes of 0.8 s on five voices, 6 seeds, all three faults at once: each note ±30 ¢ off, 12 ¢ RMS slow random wobble, a 3 st scoop of 300 ms on every other note. Floor: amount 0, the render itself.
const syn = await p.evaluate(async () => { const out = []; for (const base of [41, 48, 55, 62, 69]) for (let seed = 0; seed < 6; seed++) { let R = 1 + seed * 7 + base; const rnd = () => (R = (R * 16807) % 2147483647) / 2147483647, sr = 44100, nN = 12, nd = 0.8, n = Math.round(nN * nd * sr), x = new Float32Array(n); let ph = 0, w = 0, lp = 0;
    const steps = [0, 2, 4, 5, 7, 5, 4, 2, 0, 4, 7, 2], offs = steps.map(() => (rnd() < 0.5 ? -1 : 1) * 0.3 * (0.6 + 0.8 * rnd()));
    for (let i = 0; i < n; i++) { const t = i / sr, N = Math.floor(t / nd), u = t - N * nd; if (i % 441 === 0) { const g = (rnd() - 0.5); w += (g - w) * 0.25; } lp += (w * 1.1 - lp) * 0.002; const sc = N % 2 && u < 0.3 ? -3 * (1 - u / 0.3) : 0, f = 440 * 2 ** ((base + steps[N] + offs[N] + sc + lp * 1 - 69) / 12); ph += 2 * Math.PI * f / sr; let v = 0; for (let h = 1; h <= 20 && h * f < 16000; h++) v += Math.sin(h * ph) / h ** 1.2; x[i] = 0.25 * v * Math.min(1, Math.min(u, nd - u) / 0.02); }
    const b = new AudioBuffer({ length: n, sampleRate: sr }); b.getChannelData(0).set(x); const scan = async buf => { const F = await trackTake(buf); viterbiF0(F); trimEdges(F, buf); const S = new Stats(); for (const m of F) ingest(S, m, 'take'); const sc = takeSpots(S); return { fr: sc.frames, a: sc.aspects, off: sc.aspects.off }; };
    const A = await scan(b), g = a => ({ inton: a.inton, stab: a.stab, onset: a.onsetRaw }), r = { base: g(A.a), moved: {} }; for (const k of ['inton']) r.moved[k] = g((await scan(improveTake(b, A.fr, 0.5, A.off, null, true))).a); r.moved.floor = g((await scan(improveTake(b, A.fr, 0, A.off, null, true))).a); out.push(r); } return out; });
const rows = [];
for (const f of files) rows.push(await p.evaluate(async f => {
  const scan = async buf => { const F = await trackTake(buf); viterbiF0(F); trimEdges(F, buf); const S = new Stats(); for (const m of F) ingest(S, m, 'take'); const sc = takeSpots(S); return { fr: sc.frames, a: sc.aspects, off: sc.aspects.off }; };
  const buf = await new OfflineAudioContext(1, 1, 44100).decodeAudioData(await (await fetch('vs/' + f)).arrayBuffer()), A = await scan(buf); if (!A.a.ok) return { f, skip: 1 };
  const r = { f, base: { inton: A.a.inton, stab: A.a.stab, onset: A.a.onsetRaw }, moved: {} };
  for (const k of ['inton']) { const B = await scan(improveTake(buf, A.fr, 0.5, A.off, null, true)); r.moved[k] = { inton: B.a.inton, stab: B.a.stab, onset: B.a.onsetRaw }; }
  { const B = await scan(improveTake(buf, A.fr, 0, A.off, null, true)); r.moved.floor = { inton: B.a.inton, stab: B.a.stab, onset: B.a.onsetRaw }; }
  return r; }, f));
await b.close();
const ok = rows.filter(r => !r.skip), med = a => { const s = a.filter(Number.isFinite).sort((x, y) => x - y); return s.length ? `${s[s.length >> 1].toFixed(2)} [${s[0].toFixed(2)}, ${s[s.length - 1].toFixed(2)}]` : 'none'; };
const rep = (tag, ok) => { console.log(`${tag}: n ${ok.length}; base ${['inton', 'stab', 'onset'].map(q => q + ' ' + med(ok.map(r => r.base[q]))).join('; ')}`);
  for (const k of ['floor', 'inton']) console.log(`  move ${k}: ` + ['inton', 'stab', 'onset'].map(q => q + ' ' + med(ok.map(r => r.moved[k][q]))).join('; ')); };
rep('synthetic', syn); rep('VocalSet', ok);
