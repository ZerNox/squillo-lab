"""E-001 round 3, levelling step (squillo iteration 67, F-063's fold): does one gain per rung,
repeated, bring every rung to its take's integrated loudness, and what does it leave?

Crude experiment code. Round 3 (r3_loudness.py, results/r3/loudness.json) found every rung
louder than its take, by 1.08-4.84 LU on real voices, and its rule R1 said: levelling needed.
squillo's fold specifies the levelling in `synthesis`. This step applies the levelling the fold
will name to round 3's own rungs and measures what it achieves, so the spec's numbers come from a
result and not from listen.py's one take.

    uv run python r3_loudness.py     # only if data/cache/r3/out or data/cache/f1/out is missing
    uv run python r3_level.py        # -> results/r3/level.json

Estimate (S19, written before any run): round 3's whole run, WORLD included, took 54 s; this step
reads its 134 rungs and runs at most 2 + 2 * STEPS loudness readings per rung on about 1700 s of
audio (round 3 ran 4 per rung, the meters in well under a minute), plus squillo's tracker on 3
fixture rungs of 5 s each (fold 1). Under 3 minutes, one process, no pool.

Inputs: round 3's rungs as they are cached (data/cache/r3/out, data/cache/f1/out), each rounded to
f32 as it crosses squillo's boundary (ADR 0006), and their takes; the same 57 real (19 VocalSet
singers x id, c100, s100), 72 synthetic and 5 fixture rungs, asserted by count.

The levelling, as squillo's fold will state it (written before the run):
  g = 10 ** ((L_take - L_rung) / 20), L by ITU-R BS.1770-4 (round 3's `bs1770`, the standard's
  48 kHz K-weighting, 400 ms blocks at 75 % overlap, gates -70 LKFS and -10 LU), applied to the
  rung in f64, the rung re-measured, and repeated while |L_rung - L_take| >= EPS, at most STEPS
  times; then rounded to f32. EPS = 0.001 LU and STEPS = 4 are listen.py's (round 3, iteration 66),
  where one step left a clip 0.045 LU loud because the absolute gate does not move with the gain.

Rules (written and committed before the run):
  V1  On every rung of the three kinds, the levelled rung, read after rounding to f32 by this
      meter, lies within EPS of its take within STEPS steps. If so, a spec may state the
      levelled rung within round 3's bar (0.50 LU, `loudness.json` `bar.bar`) with this method
      as its evidence; otherwise the fold states the rungs where it did not.
  V2  SY-003's delivered-change rule (f1_fold.delivered), run on the three levelled `voice`
      fixture rungs, passes each as it passes the unlevelled ones (fold 1: 621 of 622 frames
      each, at least 591 needed). If it does, levelling does not change what SY-003's
      scenarios state; otherwise the fold revises them.
Recorded, not rules: steps used; the residual after one step; pyloudnorm's |dL| on the levelled
rung (the other meter, compared with the bar, not with EPS: their framing differs, L-054); the
gain in dB; the levelled rung's peak against its take's peak, in dB (if above 0 dB anywhere, a
take peaking within that much of full scale gives a levelled rung that clips at playback).

Checks of the checks (S15; each must-fail differs from its must-pass in the input it reads):
  level_check: V1's test passes the m1 take scaled by 10 ** (-2/20) and levelled (must pass),
      and fails the same scaled take not levelled (must fail: 2 LU off).
  delivered_check: V2's rule passes the levelled `zero` rung against the `zero` request (must
      pass) and fails the levelled `zero` rung against the `up-50c` request (must fail; fold 1's
      own must-fail case, levelled).
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

import f1_fold
from r3_loudness import CACHE, FOLD1, MODS, VOCALSET, bs1770, pyln_l

HERE = Path(__file__).parent
OUT = HERE / "results" / "r3"
EPS = 0.001
STEPS = 4


def committed_first():
    """squillo L-047 (S15): this script holds the rules; it refuses to run on an uncommitted edit
    of itself, or before it is committed at all."""
    here = Path(__file__).resolve()
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", here.name], cwd=here.parent,
                             capture_output=True).returncode == 0
    r = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", here.name], cwd=here.parent)
    if not tracked or r.returncode != 0:
        raise SystemExit(f"{here.name} has uncommitted edits: commit its rules first (S15, L-047)")


def level(x, y):
    """The fold's levelling: returns the levelled rung (f32-rounded, as f64), steps, residuals."""
    lx = bs1770(x)
    res = [bs1770(y) - lx]
    steps = 0
    while abs(res[-1]) >= EPS and steps < STEPS:
        y = y * 10 ** (-res[-1] / 20)
        steps += 1
        res.append(bs1770(y) - lx)
    yf = y.astype(np.float32).astype(np.float64)
    return yf, steps, res, bs1770(yf) - lx


def within(x, y):
    return abs(bs1770(y) - bs1770(x)) < EPS


def check_the_checks():
    out = {}
    x = np.fromfile(CACHE / "r2" / "m1.x.f64", dtype="<f8")
    s = x * 10 ** (-2 / 20)
    lev, _, _, _ = level(x, s)
    out["level_check_must_pass"] = bs1770(lev) - bs1770(x)
    out["level_check_must_fail"] = bs1770(s) - bs1770(x)
    assert within(x, lev), out
    assert not within(x, s), out
    return out


def main():
    committed_first()
    loud = json.loads((OUT / "loudness.json").read_text())
    report = dict(eps=EPS, steps_max=STEPS, bar=loud["bar"]["bar"], checks=check_the_checks(), items=[])
    names = [l.split()[0] for l in (CACHE / "r2" / "list.txt").read_text().splitlines()]
    assert set(VOCALSET) <= set(names) and len(names) == 43, names
    sets = [("vocalset" if n in VOCALSET else "synthetic", CACHE / "r3", n, MODS) for n in names]
    sets += [("fixture", CACHE / "f1", n, r) for n, r in FOLD1.items()]
    levelled = {}
    for kind, d, n, reqs in sets:
        x = np.fromfile(d / f"{n}.x.f64", dtype="<f8")
        assert len(x) and np.isfinite(x).all() and np.abs(x).max() <= 1.0, n
        for q in reqs:
            y = np.fromfile(d / "out" / f"{n}.{q}.native.f64", dtype="<f8").astype(np.float32).astype(np.float64)
            assert len(y) == len(x) and np.isfinite(y).all(), (n, q)
            yl, steps, res, final = level(x, y)
            if kind == "fixture" and n == "voice":
                levelled[q] = yl
            report["items"].append(dict(
                kind=kind, input=n, request=q, dL_before=res[0], steps=steps, after_one_step=res[1] if len(res) > 1 else res[0],
                dL_after=final, dL_after_pyln=pyln_l(yl) - pyln_l(x), gain_db=float(20 * np.log10(np.abs(yl).max() / np.abs(y).max())),
                peak_vs_take_db=float(20 * np.log10(np.abs(yl).max() / np.abs(x).max())),
                levelled=bool(abs(final) < EPS)))
    counts = {k: sum(i["kind"] == k for i in report["items"]) for k in ("vocalset", "synthetic", "fixture")}
    assert counts == dict(vocalset=57, synthetic=72, fixture=5), counts
    # V2: SY-003 on the levelled voice rungs, with fold 1's own measure and rule
    fx = f1_fold.read_wav(Path(sys.argv[1]) / "synthesis" / "voice-220hz-wobble.wav") if len(sys.argv) > 1 else None
    assert fx is not None, "usage: r3_level.py <squillo>/fixtures"
    c_in, u_in, _, _ = f1_fold.measure(fx)
    req = {k: json.loads((Path(sys.argv[1]) / "synthesis" / f"request-{k}.json").read_text())["change_cents"]
           for k in ("zero", "up-50c", "steady")}
    meas = {k: f1_fold.measure(levelled[k]) for k in req}
    report["V2"] = {k: f1_fold.delivered(c_in, u_in, meas[k][0], meas[k][1], req[k]) for k in req}
    report["checks"]["delivered_check_must_pass"] = report["V2"]["zero"]["passes"]
    report["checks"]["delivered_check_must_fail"] = f1_fold.delivered(c_in, u_in, meas["zero"][0], meas["zero"][1], req["up-50c"])["passes"]
    assert report["checks"]["delivered_check_must_pass"] and not report["checks"]["delivered_check_must_fail"], report["checks"]
    unlev = json.loads((HERE / "results" / "f1" / "fold.json").read_text())["rule"]
    report["V2_unlevelled_within"] = {k: unlev[k]["within"] for k in req}
    report["V2_outcome"] = all(report["V2"][k]["passes"] == unlev[k]["passes"] for k in req)
    report["V1_outcome"] = all(i["levelled"] for i in report["items"])
    summ = {}
    for kind in counts:
        its = [i for i in report["items"] if i["kind"] == kind]
        summ[kind] = dict(
            n=len(its), levelled=sum(i["levelled"] for i in its),
            steps=[min(i["steps"] for i in its), max(i["steps"] for i in its)],
            steps_hist={s: sum(i["steps"] == s for i in its) for s in range(STEPS + 1)},
            abs_after_one_step_max=max(abs(i["after_one_step"]) for i in its),
            abs_dL_after_max=max(abs(i["dL_after"]) for i in its),
            abs_dL_after_pyln_max=max(abs(i["dL_after_pyln"]) for i in its),
            gain_db=[min(i["gain_db"] for i in its), max(i["gain_db"] for i in its)],
            peak_vs_take_db=[min(i["peak_vs_take_db"] for i in its), max(i["peak_vs_take_db"] for i in its)])
    report["summary"] = summ
    (OUT / "level.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(dict(V1=report["V1_outcome"], V2=report["V2_outcome"], checks=report["checks"],
                          V2_within={k: v["within"] for k, v in report["V2"].items()}, summary=summ), indent=1))


if __name__ == "__main__":
    sys.exit(main())
