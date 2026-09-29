// E-006 analysis: applies rules.mjs's checks and hypotheses to data/cache/runs
// (or data/cache/sample with --sample) and writes results/summary.json.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { execSync } from 'node:child_process';
import * as R from './rules.mjs';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const SAMPLE = process.argv.includes('--sample');
if (!SAMPLE) for (const f of ['rules.mjs', 'analyze.mjs']) {
  try { execSync(`git diff --quiet HEAD -- ${f}`, { cwd: HERE }); }
  catch { throw new Error(`${f} has uncommitted edits: commit the rules first (S15, L-047)`); }
}
const DIR = path.join(HERE, 'data/cache', SAMPLE ? 'sample' : 'runs');
const runs = fs.readdirSync(DIR).filter((f) => f.endsWith('.json')).map((f) => JSON.parse(fs.readFileSync(path.join(DIR, f))));
const reps = SAMPLE ? 1 : R.REPS;
assert.equal(runs.length, R.BROWSERS.length * Object.keys(R.CONDITIONS).length * R.WORKER_MODES.length * reps, 'every run present');

// The logger check: a path reached is one the logger logged exactly.
const reached = (run, p, list = run.hits) => list.includes(`/${run.name}/${p}`);

// K0, checked on its own must-pass and must-fail inputs, in every run.
const k0 = { runs: runs.length, pass_seen: 0, fail_unseen: 0 };
for (const r of runs) {
  assert.ok(reached(r, 'control/node'), `K0 must-pass: ${r.name}`); k0.pass_seen++;
  assert.ok(!reached(r, 'control/never'), `K0 must-fail: ${r.name}`); k0.fail_unseen++;
  // the UDP port's must-fail input: nothing has fired WebRTC before the page loads
  assert.equal(r.udpBeforePage, 0, `K0 UDP must-fail: ${r.name}`); k0.udp_silent_before_page = (k0.udp_silent_before_page ?? 0) + 1;
}
// K2: every run complete.
for (const r of runs) {
  assert.ok(!r.error, `K2 harness error: ${r.name} ${r.error}`);
  for (const p of R.DOC_PROBES) assert.ok(p in r.page.doc, `K2 doc ${p}: ${r.name}`);
  assert.ok(r.page.worker && !r.page.worker.error, `K2 worker: ${r.name} ${JSON.stringify(r.page.worker)}`);
  for (const p of R.WORKER_PROBES) assert.ok(p in r.page.worker.probes, `K2 worker ${p}: ${r.name}`);
  assert.ok(r.page.worklet && r.page.worklet.has, `K2 worklet: ${r.name}`);
}
const k2 = { complete: runs.length };

// Each run's outcome per probe: reached the logger (before navigation; webrtc by the UDP port).
const probes = [...R.DOC_PROBES.map((p) => `doc/${p}`), ...R.WORKER_PROBES.map((p) => `worker/${p}`), `doc/${R.NAV_PROBE}`];
function outcome(r, p) {
  if (p === 'doc/webrtc') return r.udpBeforeNav > 0;
  if (p === `doc/${R.NAV_PROBE}`) return reached(r, p);
  return reached(r, p, r.hitsBeforeNav);
}
const cell = {};  // browser|cond|mode -> probe -> [bool per rep]
for (const r of runs) {
  const k = `${r.browser}|${r.cond}|${r.mode}`; cell[k] ??= { probes: {}, wasm_doc: [], wasm_worker: [], violations: [], own: new Set(), udp_from: new Set(), version: r.version };
  for (const p of probes) (cell[k].probes[p] ??= []).push(outcome(r, p));
  cell[k].wasm_doc.push(r.page.wasm); cell[k].wasm_worker.push(r.page.worker.wasm);
  cell[k].violations.push(r.page.violations.length + r.page.worker.violations.length);
  r.own.forEach((o) => cell[k].own.add(o)); r.udp.forEach((u) => cell[k].udp_from.add(u.from));
}
// K1: judged where every rep of 'none' reached, per browser and worker mode.
const judged = {};
for (const b of R.BROWSERS) for (const m of R.WORKER_MODES) {
  judged[`${b}|${m}`] = probes.filter((p) => cell[`${b}|none|${m}`].probes[p].every(Boolean));
}
let disagree = 0;
const table = {};
for (const [k, c] of Object.entries(cell)) {
  const [b, , m] = k.split('|');
  const reachedJudged = {}, notJudged = [];
  for (const p of probes) {
    const v = c.probes[p];
    if (!v.every((x) => x === v[0])) disagree++;
    if (!judged[`${b}|${m}`].includes(p)) { notJudged.push(p); continue; }
    reachedJudged[p] = `${v.filter(Boolean).length}/${v.length}`;
  }
  table[k] = { version: c.version, reached: Object.fromEntries(Object.entries(reachedJudged).filter(([, s]) => !s.startsWith('0/'))),
    blocked: Object.entries(reachedJudged).filter(([, s]) => s.startsWith('0/')).map(([p]) => p),
    not_judged: notJudged, wasm_doc: [...new Set(c.wasm_doc)], wasm_worker: [...new Set(c.wasm_worker)],
    violations: c.violations, own_origin_requests: [...c.own].sort(), udp_from: [...c.udp_from].sort() };
}
const T = (b, c, m) => table[`${b}|${c}|${m}`];
const inT = (t, p) => p in t.reached;
const all = (f) => R.BROWSERS.every((b) => R.WORKER_MODES.every((m) => f(b, m)));
const docJ = (b, m) => judged[`${b}|${m}`].filter((p) => p.startsWith('doc/') && p !== 'doc/webrtc' && p !== `doc/${R.NAV_PROBE}`);
const wJ = (b, m) => judged[`${b}|${m}`].filter((p) => p.startsWith('worker/'));
const H = {
  H1: all((b, m) => ['meta', 'header'].every((c) => docJ(b, m).every((p) => !inT(T(b, c, m), p)))),
  H2: all((b, m) => wJ(b, m).every((p) => (m === 'url' ? inT(T(b, 'meta', m), p) : !inT(T(b, 'meta', m), p)) && !inT(T(b, 'header', m), p))),
  H3: all((b, m) => !judged[`${b}|${m}`].includes('doc/webrtc') || Object.keys(R.CONDITIONS).every((c) => inT(T(b, c, m), 'doc/webrtc'))),
  H4: all((b, m) => ['meta', 'header'].every((c) => T(b, c, m).wasm_doc.join() === 'ok' && T(b, c, m).wasm_worker.join() === 'ok')
    && ['meta-nowasm', 'header-nowasm'].every((c) => T(b, c, m).wasm_doc.every((w) => w.startsWith('throw'))
      && (c === 'meta-nowasm' && m === 'url' ? true : T(b, c, m).wasm_worker.every((w) => w.startsWith('throw'))))),
  H5: all((b, m) => judged[`${b}|${m}`].includes(`doc/${R.NAV_PROBE}`) && Object.keys(R.CONDITIONS).every((c) => inT(T(b, c, m), `doc/${R.NAV_PROBE}`))),
};
const worklet = [...new Set(runs.map((r) => JSON.stringify(r.page.worklet.has)))];
const summary = { sample: SAMPLE, runs: runs.length, checks: { K0: k0, K1_judged: judged, K2: k2 }, reps_disagree_recorded: disagree,
  hypotheses: Object.fromEntries(Object.entries(R.HYPOTHESES).map(([h, s]) => [h, { statement: s, held: H[h] }])),
  worklet_apis: worklet.map((s) => JSON.parse(s)), policy: R.POLICY, cells: table };
const out = path.join(HERE, SAMPLE ? 'data/cache/sample-summary.json' : 'results/summary.json');
fs.writeFileSync(out, JSON.stringify(summary, null, 1) + '\n');
console.log(JSON.stringify({ hypotheses: summary.hypotheses, disagree, judged }, null, 1));
for (const [k, t] of Object.entries(table)) console.log(k.padEnd(28), 'reached:', JSON.stringify(t.reached), '| wasm', t.wasm_doc.join(), t.wasm_worker.join());
