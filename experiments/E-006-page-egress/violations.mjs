// E-006 re-read for squillo F-059 (iteration 56): which governed probes the
// browser reported as a violation of the page's policy, in the context that
// fired them, in the configuration squillo ships (ADR 0021: the worker from a
// blob: URL), under 'meta' and 'header'. Reads data/cache/runs only; writes
// results/violations.json. Refuses to run on an uncommitted edit of itself
// (squillo S15, L-047).
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { execSync } from 'node:child_process';
import * as R from './rules.mjs';

const HERE = path.dirname(new URL(import.meta.url).pathname);
for (const f of ['violations.mjs', 'rules.mjs']) {
  try { execSync(`git ls-files --error-unmatch -- ${f}`, { cwd: HERE, stdio: 'ignore' }); execSync(`git diff --quiet HEAD -- ${f}`, { cwd: HERE }); }
  catch { throw new Error(`${f} has uncommitted edits: commit it first (S15, L-047)`); }
}

// Rules, before the read: the shipped configuration only; a probe counts as
// reported in a run when the context that fired it recorded a violation whose
// blocked URI is the probe's own URL. Chrome and Firefox report a blocked
// frame by its origin only (seen in R-11's re-read), so the iframe probe is
// matched by the logger's origin, and said so in the output.
const CONDS = ['meta', 'header'];
const MODE = 'blob';
const JUDGED_OUT = { firefox: ['doc/prefetch'] };  // E-006 K1: not judged in Firefox
const DOC = R.DOC_PROBES.filter((p) => p !== 'webrtc');  // webrtc is not governed

function originOf(u) { try { return new URL(u).origin; } catch { return null; } }
// The matcher: does this context's violation list name this probe?
function reported(run, ctx, probe, list) {
  const urls = list.map(([, u]) => u);
  if (ctx === 'doc' && probe === 'iframe') {
    const logger = urls.map(originOf).find((o) => o && !o.startsWith('null'));
    return { hit: urls.some((u) => u === logger && !u.includes(`/${run.name}/`)), by: 'origin' };
  }
  return { hit: urls.some((u) => u.split('?')[0].endsWith(`/${run.name}/${ctx}/${probe}`)), by: 'url' };
}

// Check of the matcher (S15): a must-pass and a must-fail input, differing in
// the list the matcher reads.
{
  const run = { name: 'x-r0' };
  assert.equal(reported(run, 'worker', 'fetch', [['connect-src', 'http://127.0.0.1:1/x-r0/worker/fetch']]).hit, true, 'matcher must-pass');
  assert.equal(reported(run, 'worker', 'fetch', [['connect-src', 'http://127.0.0.1:1/x-r0/doc/fetch']]).hit, false, 'matcher must-fail: another context');
  assert.equal(reported(run, 'worker', 'fetch', [['connect-src', 'http://127.0.0.1:1/y-r0/worker/fetch']]).hit, false, 'matcher must-fail: another run');
  assert.equal(reported(run, 'doc', 'iframe', [['frame-src', 'http://127.0.0.1:1']]).hit, true, 'iframe must-pass');
  assert.equal(reported(run, 'doc', 'iframe', []).hit, false, 'iframe must-fail: no report');
}

const DIR = path.join(HERE, 'data/cache/runs');
const runs = fs.readdirSync(DIR).filter((f) => f.endsWith('.json')).map((f) => JSON.parse(fs.readFileSync(path.join(DIR, f))))
  .filter((r) => CONDS.includes(r.cond) && r.mode === MODE);
assert.equal(runs.length, R.BROWSERS.length * CONDS.length * R.REPS, 'every shipped-configuration run present');
for (const r of runs) assert.ok(!r.error && r.page && r.page.worker && !r.page.worker.error, `run complete: ${r.name}`);

const out = { source: 'data/cache/runs (E-006 round 1, results commit 7a2e669)', conds: CONDS, mode: MODE, runs: runs.length, cells: {}, unmatched: 0 };
for (const b of R.BROWSERS) for (const c of CONDS) {
  const rs = runs.filter((r) => r.browser === b && r.cond === c);
  const cell = { runs: rs.length, reported: {}, not_reported: [], not_judged: JUDGED_OUT[b] ?? [], iframe_by: 'origin' };
  for (const [ctx, list, names] of [['doc', 'violations', DOC], ['worker', null, R.WORKER_PROBES]]) {
    for (const p of names) {
      const n = rs.filter((r) => reported(r, ctx, p, ctx === 'doc' ? r.page.violations : r.page.worker.violations).hit).length;
      cell.reported[`${ctx}/${p}`] = n;
      if (n === 0) cell.not_reported.push(`${ctx}/${p}`);
      else assert.equal(n, rs.length, `reps agree on ${b}|${c} ${ctx}/${p}`);
    }
  }
  // every recorded violation is some probe's
  for (const r of rs) for (const [ctx, list] of [['doc', r.page.violations], ['worker', r.page.worker.violations]]) {
    for (const v of list) {
      const names = ctx === 'doc' ? DOC : R.WORKER_PROBES;
      if (!names.some((p) => reported(r, ctx, p, [v]).hit)) { out.unmatched++; }
    }
  }
  out.cells[`${b}|${c}`] = cell;
}
assert.equal(out.unmatched, 0, 'every recorded violation matched to a probe');
fs.mkdirSync(path.join(HERE, 'results'), { recursive: true });
fs.writeFileSync(path.join(HERE, 'results/violations.json'), JSON.stringify(out, null, 1) + '\n');
for (const [k, v] of Object.entries(out.cells)) console.log(k, 'not reported:', v.not_reported.join(', ') || 'none', '| not judged:', v.not_judged.join(', ') || 'none');
