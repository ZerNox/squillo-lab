// Next step for starts (improveTake 'starts', the page's own code) in headless Chrome, synthetic: 12 notes of 0.8 s on five voices, 6 seeds,
// a scoop of D st over 300 ms on every other note (D 1.5-3), notes ±30 ¢ off. Rendered at 0.5 (and 0, the render's floor) and rescanned:
// scoops per note, mean scoop depth (st) of what the scan still calls a scoop, tuning (¢). Usage: node check/next-start-bench.mjs http://localhost:<port>/
import { chromium } from 'playwright';
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()), p = await b.newPage();
await p.goto(process.argv[2]); await p.waitForTimeout(1000);
const out = await p.evaluate(async () => { const out = []; for (const D of [1.8, 3]) for (const base of [41, 48, 55, 62, 69]) for (let seed = 0; seed < +(window.NSEED || 6); seed++) { let R = 1 + seed * 7 + base; const rnd = () => (R = (R * 16807) % 2147483647) / 2147483647, sr = 44100, nN = 12, nd = 0.8, n = Math.round(nN * nd * sr), x = new Float32Array(n); let ph = 0;
    const steps = [0, 2, 4, 5, 7, 5, 4, 2, 0, 4, 7, 2], offs = steps.map(() => (rnd() < 0.5 ? -1 : 1) * 0.3 * (0.6 + 0.8 * rnd()));
    for (let i = 0; i < n; i++) { const t = i / sr, N = Math.floor(t / nd), u = t - N * nd, sc = N % 2 && u < 0.3 ? -D * (1 - u / 0.3) : 0, f = 440 * 2 ** ((base + steps[N] + offs[N] + sc - 69) / 12); ph += 2 * Math.PI * f / sr; let v = 0; for (let h = 1; h <= 20 && h * f < 16000; h++) v += Math.sin(h * ph) / h ** 1.2; x[i] = 0.25 * v * Math.min(1, Math.max(0, Math.min(u, nd - 0.1 - u)) / 0.02); }
    const bf = new AudioBuffer({ length: n, sampleRate: sr }); bf.getChannelData(0).set(x);
    const scan = async buf => { const F = await trackTake(buf); viterbiF0(F); trimEdges(F, buf); const S = new Stats(); for (const m of F) ingest(S, m, 'take'); const sc = takeSpots(S), ev = S.rec.events.filter(e => e.type === 'scoop'); return { fr: sc.frames, a: sc.aspects, dep: ev.length ? ev.reduce((s, e) => s + e.depth, 0) / ev.length : 0 }; };
    const A = await scan(bf), g = r => ({ on: r.a.onsetRaw, dep: r.dep, inton: r.a.inton });
    out.push({ D, base: g(A), half: g(await scan(improveTake(bf, A.fr, 0.5, A.a.off, null, 'starts'))), floor: g(await scan(improveTake(bf, A.fr, 0, A.a.off, null, 'starts'))) }); } return out; });
await b.close();
const med = a => { const s = a.filter(Number.isFinite).sort((x, y) => x - y); return `${s[s.length >> 1].toFixed(2)} [${s[0].toFixed(2)}, ${s[s.length - 1].toFixed(2)}]`; };
for (const D of [1.8, 3]) { const r = out.filter(o => o.D === D); console.log(`scoop ${D} st, n ${r.length}`); for (const k of ['base', 'floor', 'half']) console.log(`  ${k}: scoops/note ${med(r.map(o => o[k].on))}; depth ${med(r.map(o => o[k].dep))} st; tuning ${med(r.map(o => o[k].inton))} ¢`); }
