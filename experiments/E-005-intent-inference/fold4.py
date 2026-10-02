"""E-005 fold 4 (squillo iteration 72): round 4's provisional tuning (PM) into squillo
`metrics` MT-006, and a fixture that shows it. Crude experiment code; adds to
round4.py and fold_refusal.py, never replaces them.

    uv run python fold4.py run <dir>   # writes the fixture to <dir>, measures every squillo
                                       # wav fixture under P0 and PM -> results/fold4.json

Question: squillo's fold of round 4 (F-040) replaces ADR 0015 step 1's provisional
tuning, the circular mean of all measured frames (P0), with the circular mean of each
bridged voiced run's 200 ms running median (PM, round4.provisional). Does a fixture
exist that the old rule fails and the new one passes, and does every pitch-spread
scenario squillo already has still hold under PM?

The fixture, conditions written before generating (S15):
  take-vibrato-onset-50c.wav: fold_refusal's take (fold_refusal.py:393-426: MELODY,
  TUNING 23 cents above A4 = 440 Hz, notes of 38 400 samples, gaps of 4 800, 480-sample
  raised-cosine ramps, peak 0.5, 48 kHz float32 WAV) with every deviation 0 and the
  vibrato of take-vibrato-in-tune.wav widened: f(t) = f_j (1 + BETA sin(2 pi 5.5 t)),
  BETA = 2^(50/1200) - 1, full extent from each note's first sample (no fade), so the
  upper extreme is 50 cents and the lower 1200 log2(1 - BETA). 50 cents is round 4's
  onset condition at which P0 measured 0 of 100 takes in every cell (results/round4.json)
  and lies inside VocalSet's extents (E-002 result 21: p5 6.0, p95 110.5 cents), above the
  38.3 cents at which P0 turns (F-040). Asserted on the exact formula on the sample grid:
  every instantaneous frequency inside E2..C6, the extremes, every gap silent, the peak.

Rules, written and committed before the run:
  F1 (the fixture shows the change; must pass) under PM, MT-003's refusal on, the new
     fixture's pitch-spread is measured (upper end <= 25 cents, MT-007) and 0 lies within
     its value +- 2u (MT-006's scenario form: value minus expanded uncertainty <= 0), with
     14 segments, one per note.
  F2 (the fixture fails the old rule; must fail under P0): under P0 it is not measured.
  F3 (no scenario moves): on every other wav fixture in squillo's fixtures/, PM gives the
     same state as P0; and under PM each MT-006/MT-007 scenario check fold_refusal.fixtures
     makes holds (in-tune and vibrato-in-tune measured containing 0; spread-5c measured
     containing 5, excluding 0; spread-15c measured containing 15, excluding 5; drift at
     least with its lower end in (0, 18.6052]; uncertain), and MT-008's compare checks.
  Checks of the checks, each with an input that must fail them: "measured and contains 0"
     on take-spread-5c.wav under PM (its interval excludes 0); "not measured" on
     take-vibrato-in-tune.wav under P0 (measured, fold_refusal_fixtures.json).
"""

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

import run  # before synth (round2's note)
import round2 as R2
import fold_refusal as FR
import round4 as R4

HERE = Path(__file__).parent
OUT = HERE / "results"
SQ = HERE.parents[2] / "squillo"
NAME = "take-vibrato-onset-50c.wav"
EXTENT = 50.0  # cents, round 4's onset condition (round4.py VIBS)
BETA = 2 ** (EXTENT / 1200) - 1  # f_j (1 + BETA) is EXTENT cents above f_j
NOTE = 38_400  # samples, take-vibrato-in-tune.wav's (fold_refusal.py:459)
N_NOTES = len(FR.MELODY)
UPPER = FR.UPPER  # 25 cents, MT-007
DRIFT_SD = 18.6052  # take-drift-60c.wav's deviation sd, squillo MT-007's scenario


def committed_first():
    """S15: refuse to run on an uncommitted edit of this file, or before it is committed."""
    me = Path(__file__).name
    a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
    b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", me], cwd=HERE)
    if a.returncode or b.returncode:
        sys.exit(f"{me} is not committed as it stands: commit the rules before running")


def sample(n):
    if n < FR.GAP:
        return 0.0
    j, m = divmod(n - FR.GAP, NOTE + FR.GAP)
    if m >= NOTE:
        return 0.0
    f = FR.note_freq(j, 0.0)
    g = 1.0
    if m < FR.RAMP:
        g = 0.5 - 0.5 * math.cos(math.pi * m / FR.RAMP)
    elif m >= NOTE - FR.RAMP:
        g = 0.5 - 0.5 * math.cos(math.pi * (NOTE - m) / FR.RAMP)
    ph = 2 * math.pi * f * m / 48000 + f * BETA / FR.VIB_RATE * (1 - math.cos(2 * math.pi * FR.VIB_RATE * m / 48000))
    return 0.5 * g * math.sin(ph)


def generate(out):
    E2, C6 = 440 * 2 ** (R2.E2_CENTS / 1200), 440 * 2 ** (R2.C6_CENTS / 1200)
    m = np.arange(NOTE)
    dev = 1200 * np.log2(1 + BETA * np.sin(2 * math.pi * FR.VIB_RATE * m / 48000))  # cents from f_j, exact
    fr = [FR.note_freq(j, 0.0) for j in range(N_NOTES)]
    lo_f, hi_f = min(fr) * 2 ** (dev.min() / 1200), max(fr) * 2 ** (dev.max() / 1200)
    assert E2 <= lo_f and hi_f <= C6, (lo_f, hi_f)
    assert abs(dev.max() - EXTENT) < 1e-3, dev.max()  # the extreme the grid reaches
    # full extent within the first cycle of every note: no fade (round4.assert_vib's 0.99 A)
    first = dev[: int(48000 / FR.VIB_RATE) + 1]
    assert first.max() >= 0.99 * EXTENT, first.max()
    N = FR.GAP + N_NOTES * (NOTE + FR.GAP)
    xs = [sample(n) for n in range(N)]
    f32 = np.array(xs, dtype=np.float32)
    assert float(np.abs(f32).max()) <= 0.5
    for j in range(N_NOTES + 1):
        a = j * (NOTE + FR.GAP)
        assert not f32[a:a + FR.GAP].any(), j
    blob = FR.wav(xs)
    (out / NAME).write_bytes(blob)
    return dict(sha256=hashlib.sha256(blob).hexdigest(), bytes=len(blob), samples=N, beta=BETA,
                extent_up=round(float(dev.max()), 4), extent_down=round(float(dev.min()), 4),
                f_min=round(lo_f, 3), f_max=round(hi_f, 3))


def measure(path, rule):
    import soundfile as sf
    x, sr = sf.read(path, dtype="float32")
    assert sr == FR.SR, (path, sr)
    if x.ndim > 1:
        x = x[:, 0]
    t, c, _, n_ref = FR.track(x)
    sp, tun, nseg, r0 = R4.measure(c, t, rule)
    st = FR.state(sp)
    fin = np.isfinite(sp["s"])
    return dict(state=st, s=float(sp["s"]) if fin else None, uB=float(sp["uB"]) if fin else None,
                lower=float(sp["s"] - 2 * sp["uB"]) if fin else None,
                upper=float(sp["s"] + 2 * sp["uB"]) if fin else None,
                nseg=nseg, r0=r0, refused=n_ref), sp


def main(outdir="/tmp/e005-fold4"):
    committed_first()
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    fx = generate(out)
    paths = {str(p.relative_to(SQ)): p for p in sorted((SQ / "fixtures").rglob("*.wav"))}
    paths["fixtures/metrics/" + NAME] = out / NAME
    rows, SP = {}, {}
    for name, p in paths.items():
        rows[name] = {}
        for rule in ("P0", "PM"):
            rows[name][rule], SP[(name, rule)] = measure(p, rule)
    new = "fixtures/metrics/" + NAME

    def contains(name, rule, v):
        r = rows[name][rule]
        return r["state"] == "measured" and r["lower"] <= v <= r["upper"]

    def sp(n):
        return SP[("fixtures/metrics/" + n, "PM")]

    moved = [n for n in rows if n != new and rows[n]["P0"]["state"] != rows[n]["PM"]["state"]]
    drift = rows["fixtures/metrics/take-drift-60c.wav"]["PM"]
    checks = {
        "F1_new_measured_contains_0": contains(new, "PM", 0.0),
        "F1_new_14_segments": rows[new]["PM"]["nseg"] == N_NOTES,
        "F3_no_state_moved": not moved,
        "F3_in_tune": contains("fixtures/metrics/take-in-tune.wav", "PM", 0.0),
        "F3_vibrato_in_tune": contains("fixtures/metrics/take-vibrato-in-tune.wav", "PM", 0.0),
        "F3_spread_5": contains("fixtures/metrics/take-spread-5c.wav", "PM", 5.0)
        and not contains("fixtures/metrics/take-spread-5c.wav", "PM", 0.0),
        "F3_spread_15": contains("fixtures/metrics/take-spread-15c.wav", "PM", 15.0)
        and not contains("fixtures/metrics/take-spread-15c.wav", "PM", 5.0),
        "F3_drift": drift["state"] == "at least" and 0 < drift["lower"] <= DRIFT_SD,
        "F3_uncertain": rows["fixtures/metrics/take-uncertain.wav"]["PM"]["state"] == "uncertain",
        "F3_15_to_5_improved": FR.compare(sp("take-spread-15c.wav"), sp("take-spread-5c.wav")) == 1,
        "F3_5_to_in_tune_improved": FR.compare(sp("take-spread-5c.wav"), sp("take-in-tune.wav")) == 1,
        "F3_5_to_5_no_change": FR.compare(sp("take-spread-5c.wav"), sp("take-spread-5c.wav")) == 0,
        "F3_drift_to_in_tune_improved": FR.compare(sp("take-drift-60c.wav"), sp("take-in-tune.wav")) == 1,
        "F3_in_tune_to_drift_worse": FR.compare(sp("take-in-tune.wav"), sp("take-drift-60c.wav")) == -1,
        "F3_drift_to_drift_no_change": FR.compare(sp("take-drift-60c.wav"), sp("take-drift-60c.wav")) == 0,
    }
    must_fail = {
        "F2_new_not_measured_under_P0": rows[new]["P0"]["state"] != "measured",
        "contains_0_fails_on_spread_5c": not contains("fixtures/metrics/take-spread-5c.wav", "PM", 0.0),
        "not_measured_fails_on_vibrato_in_tune_P0": rows["fixtures/metrics/take-vibrato-in-tune.wav"]["P0"]["state"] == "measured",
    }
    res = dict(fixture=fx, rows=rows, moved=moved, checks=checks, must_fail=must_fail)
    json.dump(res, open(OUT / "fold4.json", "w"), indent=1, default=float)
    print(json.dumps(dict(fixture=fx, new=rows[new], moved=moved, checks=checks, must_fail=must_fail), indent=1, default=float))
    for k in ("F1_new_measured_contains_0", "F1_new_14_segments", "F3_no_state_moved", "F3_in_tune",
              "F3_vibrato_in_tune", "F3_spread_5", "F3_spread_15", "F3_drift", "F3_uncertain",
              "F3_15_to_5_improved", "F3_5_to_in_tune_improved", "F3_5_to_5_no_change",
              "F3_drift_to_in_tune_improved", "F3_in_tune_to_drift_worse", "F3_drift_to_drift_no_change"):
        assert checks[k], k
    for k in ("F2_new_not_measured_under_P0", "contains_0_fails_on_spread_5c",
              "not_measured_fails_on_vibrato_in_tune_P0"):
        assert must_fail[k], k


if __name__ == "__main__":
    {"run": main}[sys.argv[1]](*sys.argv[2:])
