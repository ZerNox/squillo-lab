// Vibrato evenness reference, measured with the page's own code (trackTake, viterbiF0, trimEdges, ingest,
// takeVibrato: the take path) in headless Chrome on every VocalSet vibrato clip (Wilkins et al. 2018, CC BY 4.0,
// doi:10.5281/zenodo.1442513, not shipped): scales, arpeggios (five vowels) and the three excerpts (caro, dona,
// row), 20 trained singers. Per clip: takeVibrato's rate, extent, rate CV and extent CV (means over vibrato notes).
// Reported per singer (mean of their clips), then across singers: median, p25-p75, p90 and mean ± 1.96 SE, by task.
// Usage: node check/vibeven-bench.mjs http://localhost:<port>/ <dir with VocalSet *_vibrato*.wav>
import { chromium } from 'playwright';
import { readdirSync, readFileSync } from 'fs';
const url = process.argv[2], dir = process.argv[3];
const files = readdirSync(dir).filter(f => /^[fm]\d+_(scales|arpeggios|caro|dona|row)_vibrato(_[aeiou])?\.wav$/.test(f));
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()); const p = await b.newPage();
await p.route('**/vs/*', r => r.fulfill({ body: readFileSync(dir + '/' + decodeURIComponent(r.request().url().split('/vs/')[1])), contentType: 'audio/wav' }));
await p.goto(url); await p.waitForTimeout(1000);
const rows = [];
for (const f of files) {
  const r = await p.evaluate(async f => { const ab = await (await fetch('vs/' + f)).arrayBuffer(), buf = await new OfflineAudioContext(1, 1, 44100).decodeAudioData(ab);
    const fs = await trackTake(buf); viterbiF0(fs); trimEdges(fs, buf); const S = new Stats(); for (const m of fs) ingest(S, m, 'take'); return takeVibrato(S); }, f);
  const [, s, task] = f.match(/^([fm]\d+)_([a-z]+)_/); rows.push({ f, s, task: ['caro', 'dona', 'row'].includes(task) ? 'excerpt' : task, ...r });
}
await b.close();
const q = (a, x) => { const s = [...a].sort((u, v) => u - v); return s[Math.min(s.length - 1, Math.floor(x * s.length))]; };
const ms = a => { const m = a.reduce((t, x) => t + x, 0) / a.length, sd = Math.sqrt(a.reduce((t, x) => t + (x - m) ** 2, 0) / Math.max(1, a.length - 1)); return [m, 1.96 * sd / Math.sqrt(a.length)]; };
for (const task of ['all', 'scales', 'arpeggios', 'excerpt']) {
  const R = rows.filter(r => (task === 'all' || r.task === task) && r.rcv), by = {};
  for (const r of R) (by[r.s] ||= []).push(r);
  const S = Object.values(by).map(a => ({ rcv: ms(a.map(r => r.rcv[0]))[0], ecv: ms(a.map(r => r.ecv[0]))[0], rate: ms(a.map(r => r.rate[0]))[0], ext: ms(a.map(r => r.ext[0]))[0] }));
  const line = k => { const a = S.map(x => x[k]); return `${k} median ${q(a, 0.5).toFixed(1)}, p25-p75 ${q(a, 0.25).toFixed(1)}-${q(a, 0.75).toFixed(1)}, p90 ${q(a, 0.9).toFixed(1)}, mean ${ms(a).map(v => v.toFixed(1)).join(' ± ')}`; };
  console.log(`${task}: ${R.length} of ${rows.filter(r => task === 'all' || r.task === task).length} clips with evenness, ${S.length} singers`);
  for (const k of ['rcv', 'ecv']) console.log('  ' + line(k));
  console.log(`  rate median ${q(S.map(x => x.rate), 0.5).toFixed(2)} Hz, extent median ${q(S.map(x => x.ext), 0.5).toFixed(2)} st`);
}
