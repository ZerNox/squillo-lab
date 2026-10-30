// Note segmentation (segNotes, against the older takeNotes; the take path) in headless Chrome on vocadito (Bittner et al. 2021, CC BY 4.0,
// https://zenodo.org/records/5578807, not shipped: 40 clips, notes marked by two annotators, A1 and A2).
// Metrics as mir_eval.transcription: maximum one-to-one matching with onset within 50 ms (COn), plus pitch within 50 ¢ (COnP),
// plus offset within max(50 ms, 20 % of the true note) (COnPOff). F per clip, mean ± 1.96 SE over clips, A1 as truth;
// A2 against A1 is the human ceiling. Frames saved to FRAMES= for offline trials.
// Usage: node check/notes-bench.mjs http://localhost:<port>/ /path/to/vocadito
import { chromium } from 'playwright'; import fs from 'node:fs'; import path from 'node:path';
const [url, dir] = process.argv.slice(2);
const ids = fs.readFileSync(path.join(dir, 'vocadito_metadata.csv'), 'utf8').trim().split('\n').slice(1).map(l => l.split(',')[0]);
const notesOf = (id, a) => fs.readFileSync(path.join(dir, `Annotations/Notes/vocadito_${id}_notes${a}.csv`), 'utf8').trim().split('\n').map(l => { const [t, f, d] = l.split(',').map(Number); return { t0: t, t1: t + d, midi: 69 + 12 * Math.log2(f / 440) }; });
export const match = (R, E, mode) => { const ok = (r, e) => Math.abs(r.t0 - e.t0) <= 0.05 && (mode === 'on' || Math.abs(r.midi - e.midi) <= 0.5) && (mode !== 'off' || Math.abs(r.t1 - e.t1) <= Math.max(0.05, 0.2 * (r.t1 - r.t0)));
  const of = new Array(E.length).fill(-1); const tryR = (i, seen) => { for (let j = 0; j < E.length; j++) if (!seen[j] && ok(R[i], E[j])) { seen[j] = 1; if (of[j] < 0 || tryR(of[j], seen)) { of[j] = i; return true; } } return false; };
  let m = 0; for (let i = 0; i < R.length; i++) if (tryR(i, [])) m++; return { m, p: E.length ? m / E.length : 0, r: R.length ? m / R.length : 0, f: 2 * m / Math.max(1, R.length + E.length) }; };
const ms = v => { const m = v.reduce((s, x) => s + x, 0) / v.length, sd = Math.sqrt(v.reduce((s, x) => s + (x - m) ** 2, 0) / (v.length - 1)); return `${(100 * m).toFixed(1)} ± ${(196 * sd / Math.sqrt(v.length)).toFixed(1)}`; };
export const report = (name, rows) => { const line = ['on', 'p', 'off'].map(k => `${k === 'on' ? 'COn' : k === 'p' ? 'COnP' : 'COnPOff'} ${ms(rows.map(r => match(r.R, r.E, k).f))}`).join('; '); const pr = ['p', 'r'].map(q => ms(rows.map(r => match(r.R, r.E, 'p')[q]))); console.log(`${name}: ${line}; COnP precision ${pr[0]}, recall ${pr[1]}; notes ${rows.reduce((s, r) => s + r.E.length, 0)} vs ${rows.reduce((s, r) => s + r.R.length, 0)}`); };
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()), p = await b.newPage();
await p.route('**/vocadito/**', r => r.fulfill({ body: fs.readFileSync(path.join(dir, 'Audio', path.basename(new URL(r.request().url()).pathname))) }));
await p.goto(url); await p.waitForTimeout(1000);
const rows = [], dump = {};
for (const id of ids) { const r = await p.evaluate(async id => { const buf = await new OfflineAudioContext(1, 1, 44100).decodeAudioData(await (await fetch(`vocadito/vocadito_${id}.wav`)).arrayBuffer()); const F = await trackTake(buf); viterbiF0(F); trimEdges(F, buf); const S = new Stats(); for (const m of F) ingest(S, m, 'take'); const fr = S.rec.frames, g = n => n.map(x => ({ t0: x.t0, t1: x.t1, midi: x.med }));
    return { raw: g(takeNotes(fr).notes), smooth: g(takeNotes(smoothPitch(fr)).notes), seg: typeof segNotes === 'function' ? g(segNotes(fr)) : null, fr: fr.map(f => ({ t: f.t, midi: f.midi, voiced: f.voiced, ok: f.ok, lvl: f.rms ?? f.level ?? 0 })) }; }, id);
  dump[id] = r.fr; rows.push({ id, A1: notesOf(id, 'A1'), A2: notesOf(id, 'A2'), ...r }); }
await b.close();
if (process.env.FRAMES) fs.writeFileSync(process.env.FRAMES, JSON.stringify({ dump, rows: rows.map(({ id, A1, A2 }) => ({ id, A1, A2 })) }));
report('A2 vs A1 (ceiling)', rows.map(r => ({ R: r.A1, E: r.A2 })));
report('takeNotes raw', rows.map(r => ({ R: r.A1, E: r.raw })));
report('takeNotes smooth', rows.map(r => ({ R: r.A1, E: r.smooth })));
if (rows[0].seg) report('segNotes', rows.map(r => ({ R: r.A1, E: r.seg })));
