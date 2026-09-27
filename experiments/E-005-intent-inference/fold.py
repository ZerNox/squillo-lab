"""E-005, fold into squillo `metrics` (squillo iteration 27). Crude experiment code.

    uv run python fold.py coverage          # -> data/cache/fold_synth.pkl, results/fold.json
    uv run python fold.py fixtures <dir>    # -> <dir>/*.wav, results/fold_fixtures.json

1. coverage: does the take's spread sigma-hat (infer.circ_sigma, est
   segmentation, global reference, chromatic target) carry an honest +- ?
   The measurand is the singer's intonation spread, the standard deviation
   of their note-centre errors relative to their own tuning: sqrt(sigma^2 +
   var(D)) for the generating per-note sd sigma and the drift D of their
   tuning at the notes (a global reference counts drift). Candidate standard
   uncertainties, each checked for coverage at k = 2 among the phrases whose
   spread is above chance:
     A  sampling only, GUM (JCGM 100:2008) E.4.3: s / sqrt(2 (n_eff - 1))
     B  A combined with the notes' mean reading variance, mean(u_settle^2)
     C  A combined with sqrt(3) cents, SG-005's +-3 cents as a rectangular
        bound (GUM 4.3.7), in place of E-005's settle estimate
   Also checked against the take's realised spread (round 1's `true`).
   Four seed sets of round 1's 600-phrase design, 2400 phrases.

2. fixtures: squillo's four `fixtures/metrics/` takes, generated in pure
   Python binary64 (math.sin, math.cos) and rounded to f32, by the formula
   the squillo MANIFEST records; every condition asserted on the output;
   then run through E-002's YIN and this experiment's inference, checking
   the scenarios squillo iteration 27 writes.
"""
import hashlib
import itertools
import json
import math
import pickle
import struct
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

import infer
import run

HERE = Path(__file__).parent
CACHE = HERE / "data" / "cache"
SR = 48_000
TRANS_S = 0.1
E2_CENTS, C6_CENTS = 100 * -29, 100 * 15  # ADR 0007's range: semitones re A4 (E2 = A4 - 29, C6 = A4 + 15)
SQRT3 = math.sqrt(3)


# ---------------------------------------------------------------- 1. coverage

def n_eff(w):
    w = np.asarray(w, float)
    return w.sum() ** 2 / np.sum(w ** 2)


def spread_u(out, keep):
    dev, w, us = out["dev"][keep], out["dur"][keep], out["u_settle"][keep]
    s = infer.circ_sigma(dev, w)
    n = n_eff(w)
    if not np.isfinite(s) or n <= 1:
        return s, n, np.nan, np.nan, np.nan
    a = s / np.sqrt(2 * (n - 1))
    b = np.hypot(a, np.sqrt(np.average(us ** 2, weights=w)))
    c = np.hypot(a, SQRT3)
    return s, n, a, b, c


def one(args):
    import synth
    voice, scale, sigma, drift, vib, seed = args
    x, truth = synth.phrase(voice, scale, sigma, drift, vib, seed)
    t, cents, _ = run.track(x)
    segs = infer.segment(cents)
    segs = [s for s in segs if np.sum(~np.isnan(cents[s[0]:s[1]])) > 0]
    out = infer.infer(cents, segs, "global", "chromatic")
    keep = out["dur"] >= TRANS_S
    tc = truth["starts"] + 0.6 * truth["durs"]
    D = truth["drift"] * (tc / truth["T"] - 0.5)
    w = truth["durs"]
    E = truth["e"] + D
    realised = float(np.sqrt(np.average((E - np.average(E, weights=w)) ** 2, weights=w)))
    pop = float(np.sqrt(sigma ** 2 + np.average((D - np.average(D, weights=w)) ** 2, weights=w)))
    if keep.sum() >= 1:
        s, n, a, b, c = spread_u(out, keep)
    else:
        s, n, a, b, c = np.inf, 0.0, np.nan, np.nan, np.nan
    # S15: every note centre inside ADR 0007's E2..C6 (-2900..+1500 cents re A4)
    centre = 100.0 * truth["notes"] + truth["G"] + E
    return dict(voice=voice, scale=scale, sigma=sigma, drift=drift, vib=vib, seed=seed,
                centre_min=float(centre.min()), centre_max=float(centre.max()),
                notes=int(keep.sum()), s=float(s), n_eff=float(n), uA=float(a), uB=float(b), uC=float(c),
                pop=pop, realised=realised)


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(100 * p, 1), round(100 * (c - h), 1), round(100 * (c + h), 1)]


def coverage():
    jobs = []
    for rep in range(4):
        seed = 20260926 + 100_000 * (rep + 1)  # round 1 used 20260926 + 1..600
        for scale, sigma, drift, vib in itertools.product(run.SCALE_NAMES, run.SIGMAS, (0, 60), (0, 1)):
            for v in run.VOICES:
                seed += 1
                jobs.append((v, scale, sigma, drift, vib, seed))
    CACHE.mkdir(parents=True, exist_ok=True)
    with Pool(18) as p:
        rows = p.map(one, jobs, chunksize=8)
    pickle.dump(rows, open(CACHE / "fold_synth.pkl", "wb"))
    summarize(rows)


SPLIT = 10.0  # cents: the spread is measured, value +- 2 u_B, while s <= SPLIT; above, only s - 2 u_B
UPPER = 25.0  # cents: report the spread only while s + 2 u_B <= UPPER (by_upper, below)


def summarize(rows=None):
    if rows is None:
        rows = pickle.load(open(CACHE / "fold_synth.pkl", "rb"))
    summary = {}
    for sigma, drift, vib in itertools.product(run.SIGMAS, (0, 60), (0, 1)):
        R = [r for r in rows if (r["sigma"], r["drift"], r["vib"]) == (sigma, drift, vib)]
        rep = [r for r in R if np.isfinite(r["s"])]
        cell = dict(n=len(R), reported=len(rep),
                    pop_median=round(float(np.median([r["pop"] for r in R])), 2),
                    s_median=round(float(np.median([r["s"] for r in rep])), 2) if rep else None,
                    notes_median=float(np.median([r["notes"] for r in R])))
        for u in ("uA", "uB", "uC"):
            for truth in ("pop", "realised"):
                k = sum(abs(r["s"] - r[truth]) <= 2 * r[u] for r in rep)
                cell[f"{u}_{truth}"] = wilson(k, len(rep))
            cell[f"{u}_median"] = round(float(np.median([r[u] for r in rep])), 2) if rep else None
        # which side the misses fall on, for B against pop
        cell["uB_pop_miss_low"] = sum(r["s"] + 2 * r["uB"] < r["pop"] for r in rep)
        cell["uB_pop_miss_high"] = sum(r["s"] - 2 * r["uB"] > r["pop"] for r in rep)
        ok = [r for r in rep if r["s"] + 2 * r["uB"] <= UPPER]
        cell["rule_reported"] = len(ok)
        cell["rule_uB_pop"] = wilson(sum(abs(r["s"] - r["pop"]) <= 2 * r["uB"] for r in ok), len(ok))
        cell["rule_uB_realised"] = wilson(sum(abs(r["s"] - r["realised"]) <= 2 * r["uB"] for r in ok), len(ok))
        cell["rule_misses_low"] = sum(r["s"] + 2 * r["uB"] < r["pop"] for r in ok)
        summary[f"sigma={sigma},drift={drift},vib={vib}"] = cell
    # coverage by the reported interval's upper end, pooled over conditions
    by_upper = {}
    for lo, hi in ((0, 10), (10, 20), (20, 25), (25, 30), (30, 40), (40, 1e9)):
        for u in ("uA", "uB", "uC"):
            rep = [r for r in rows if np.isfinite(r["s"]) and lo <= r["s"] + 2 * r[u] < hi]
            k = sum(abs(r["s"] - r["pop"]) <= 2 * r[u] for r in rep)
            by_upper[f"{u} upper in [{lo},{hi})"] = wilson(k, len(rep)) + [len(rep)]
    out_of_range = sum(r["centre_min"] < E2_CENTS or r["centre_max"] > C6_CENTS for r in rows)
    assert out_of_range == 0, out_of_range  # every input inside E2-C6 (S15; asserted since R-06)
    ok = [r for r in rows if np.isfinite(r["s"]) and r["s"] + 2 * r["uB"] <= UPPER]
    rule = dict(upper=UPPER, reported=len(ok),
                coverage_pop=wilson(sum(abs(r["s"] - r["pop"]) <= 2 * r["uB"] for r in ok), len(ok)),
                coverage_realised=wilson(sum(abs(r["s"] - r["realised"]) <= 2 * r["uB"] for r in ok), len(ok)),
                misses_low=sum(r["s"] + 2 * r["uB"] < r["pop"] for r in ok),
                misses_high=sum(r["s"] - 2 * r["uB"] > r["pop"] for r in ok),
                max_pop_reported=round(max(r["pop"] for r in ok), 2),
                uB_median=round(float(np.median([r["uB"] for r in ok])), 2))
    rep = [r for r in rows if np.isfinite(r["s"])]
    m = [r for r in rep if r["s"] <= SPLIT]
    w = [r for r in rep if r["s"] > SPLIT]
    split = dict(split=SPLIT, measured=len(m), at_least=len(w), uncertain=len(rows) - len(rep),
                 measured_coverage_pop=wilson(sum(abs(r["s"] - r["pop"]) <= 2 * r["uB"] for r in m), len(m)),
                 measured_coverage_realised=wilson(sum(abs(r["s"] - r["realised"]) <= 2 * r["uB"] for r in m), len(m)),
                 measured_coverage_pop_vib0=wilson(sum(abs(r["s"] - r["pop"]) <= 2 * r["uB"] for r in m if not r["vib"]), sum(not r["vib"] for r in m)),
                 measured_coverage_pop_vib1=wilson(sum(abs(r["s"] - r["pop"]) <= 2 * r["uB"] for r in m if r["vib"]), sum(r["vib"] for r in m)),
                 measured_uB_median_vib0=round(float(np.median([r["uB"] for r in m if not r["vib"]])), 2),
                 measured_uB_median_vib1=round(float(np.median([r["uB"] for r in m if r["vib"]])), 2),
                 at_least_lower_end_honest=wilson(sum(r["s"] - 2 * r["uB"] <= r["pop"] for r in w), len(w)),
                 lower_end_honest_all=wilson(sum(r["s"] - 2 * r["uB"] <= r["pop"] for r in rep), len(rep)),
                 by_sigma={sg: dict(measured=sum(r["sigma"] == sg for r in m), at_least=sum(r["sigma"] == sg for r in w),
                                    uncertain=sum(r["sigma"] == sg and not np.isfinite(r["s"]) for r in rows))
                           for sg in run.SIGMAS},
                 coverage_by_s_bin_uB={})
    for lo, hi in ((0, 5), (5, 10), (10, 12.5), (12.5, 15), (15, 20), (20, 25), (25, 1e9)):
        for vib in (0, 1):
            b = [r for r in rep if lo <= r["s"] < hi and r["vib"] == vib]
            split["coverage_by_s_bin_uB"][f"[{lo},{hi}) vib={vib}"] = wilson(
                sum(abs(r["s"] - r["pop"]) <= 2 * r["uB"] for r in b), len(b)) + [len(b)]
    res = dict(phrases=len(rows), split=split, rule=rule, note_centres_outside_E2_C6=out_of_range,
               centre_min=round(min(r["centre_min"] for r in rows), 1),
               centre_max=round(max(r["centre_max"] for r in rows), 1), conditions=summary, by_upper=by_upper)
    path = HERE / "results" / "fold.json"
    old = json.load(open(path)) if path.exists() else {}
    old["coverage"] = res
    json.dump(old, open(path, "w"), indent=1)
    print(json.dumps(res, indent=1))


# ---------------------------------------------------------------- 2. fixtures

# 14 notes of the A major scale from A3 up to A4 and back (semitones re A4),
# a scale exercise, taken from no work; the singer's own tuning 23 cents
# above A4 = 440 Hz; each note 0.4 s, after 0.1 s of silence; 0.1 s of
# silence at the end. 7.1 s, 340 800 samples.
MELODY = [-12, -10, -8, -7, -5, -3, -1, 0, -1, -3, -5, -7, -8, -10]
TUNING = 23.0
NOTE, GAP, RAMP = 19_200, 4_800, 480
N_TOTAL = GAP + len(MELODY) * (NOTE + GAP)
pi = math.pi

DEVS = {
    # no error: every note on a semitone of the singer's own tuning
    "take-in-tune.wav": [0.0] * 14,
    # deviations, mean 0, population standard deviation exactly 5
    "take-spread-5c.wav": [-7.5, 2.5, 5, -2.5, 0, 7.5, -5, 7.5, -7.5, 2.5, -2.5, 5, -5, 0],
    # in tune, but the tuning drifts linearly by 60 cents, -30 to +30
    "take-drift-60c.wav": [60 * (j / 13 - 0.5) for j in range(14)],
    # deviations evenly spaced around the 100-cent circle, in the order 5 j mod 14
    "take-uncertain.wav": [-50 + 100 * (((5 * j) % 14) + 0.5) / 14 for j in range(14)],
}


def note_freq(j, dev):
    return 440 * 2 ** ((100 * MELODY[j] + TUNING + dev) / 1200)


def sample(n, devs):
    """Sample n of a take: silence, or note j's sine with 10 ms raised-cosine ramps."""
    if n < GAP:
        return 0.0
    j, m = divmod(n - GAP, NOTE + GAP)
    if m >= NOTE:
        return 0.0
    f = note_freq(j, devs[j])
    g = 1.0
    if m < RAMP:
        g = 0.5 - 0.5 * math.cos(pi * m / RAMP)
    elif m >= NOTE - RAMP:
        g = 0.5 - 0.5 * math.cos(pi * (NOTE - m) / RAMP)
    return 0.5 * g * math.sin(2 * pi * f * m / 48000)


def wav(samples):
    data = b"".join(struct.pack("<f", x) for x in samples)
    fmt = struct.pack("<HHIIHHH", 3, 1, SR, SR * 4, 4, 32, 0)
    body = (b"WAVE" + b"fmt " + struct.pack("<I", 18) + fmt
            + b"fact" + struct.pack("<I", 4) + struct.pack("<I", len(samples))
            + b"data" + struct.pack("<I", len(data)) + data)
    return b"RIFF" + struct.pack("<I", len(body)) + body


def pop_sd(x):
    x = np.asarray(x, float)
    return float(np.sqrt(np.mean((x - x.mean()) ** 2)))


def fixtures(outdir="/tmp/e005-fold"):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    E2, C6 = 440 * 2 ** (E2_CENTS / 1200), 440 * 2 ** (C6_CENTS / 1200)
    report = {}
    for name, devs in DEVS.items():
        # conditions, asserted on the formula's exact values (S15)
        fr = [note_freq(j, d) for j, d in enumerate(devs)]
        assert E2 <= min(fr) and max(fr) <= C6, (name, min(fr), max(fr))
        assert abs(np.mean(devs)) < 1e-9, name
        assert all(-50 < d < 50 for d in devs), name
        xs = [sample(n, devs) for n in range(N_TOTAL)]
        f32 = np.array(xs, dtype=np.float32)
        assert len(f32) == N_TOTAL == 340_800
        assert float(np.abs(f32).max()) <= 0.5
        for j in range(15):  # every gap exactly zero
            a = j * (NOTE + GAP)
            assert not f32[a:a + GAP].any(), (name, j)
        blob = wav(xs)
        (out / name).write_bytes(blob)
        x = f32.astype(np.float32)
        t, cents, _ = run.track(x)
        segs = infer.segment(cents)
        segs = [s for s in segs if np.sum(~np.isnan(cents[s[0]:s[1]])) > 0]
        o = infer.infer(cents, segs, "global", "chromatic")
        keep = o["dur"] >= TRANS_S
        s, n, a, b, c = spread_u(o, keep)
        # each note's settle pitch against its true frequency
        true_c = np.array([1200 * math.log2(f / 440) for f in fr])
        err = o["settle"][keep] - true_c if keep.sum() == 14 else None
        # the frames wholly within each note: every one within +-3 cents (SG-005)
        frame_err = []
        # frames matched by the index YIN returns, never by position (S15, L-030;
        # R-06 found the position form left here)
        idx = np.asarray(run.yin.yin(x)[0])
        assert len(idx) == len(cents)
        first = run.HOP * (idx - 3)  # first sample of frame idx's four-frame window
        last = run.HOP * (idx + 1) - 1  # last sample of frame idx (ADR 0007)
        for j in range(14):
            a0 = GAP + j * (NOTE + GAP)
            inside = (first >= a0 + RAMP) & (last < a0 + NOTE - RAMP)
            frame_err.append(float(np.nanmax(np.abs(cents[inside] - true_c[j]))))
        report[name] = dict(
            sha256=hashlib.sha256(blob).hexdigest(), bytes=len(blob),
            deviations=[round(d, 4) for d in devs], deviation_sd=round(pop_sd(devs), 4),
            f_min=round(min(fr), 4), f_max=round(max(fr), 4),
            notes_found=int(keep.sum()),
            settle_max_abs_err=None if err is None else round(float(np.abs(err).max()), 3),
            frame_max_abs_err_inside=round(max(frame_err), 3),
            spread=None if not np.isfinite(s) else round(float(s), 3), n_eff=round(float(n), 3),
            uA=None if np.isnan(a) else round(float(a), 3),
            uB=None if np.isnan(b) else round(float(b), 3),
            uC=None if np.isnan(c) else round(float(c), 3))
        report[name]["_raw"] = dict(s=float(s), uB=float(b), uC=float(c))
    # scenario checks: the states squillo's metrics spec gives, with u_B
    R = {k: v["_raw"] for k, v in report.items()}

    def state(k):
        x = R[k]
        if not np.isfinite(x["s"]):
            return "intent uncertain"
        return "measured" if x["s"] <= SPLIT else "at least"

    def contains(k, x):
        return R[k]["s"] - 2 * R[k]["uB"] <= x <= R[k]["s"] + 2 * R[k]["uB"]
    s5, s0 = R["take-spread-5c.wav"], R["take-in-tune.wav"]
    d = s5["s"] - s0["s"]
    drift_sd = report["take-drift-60c.wav"]["deviation_sd"]
    lo_drift = R["take-drift-60c.wav"]["s"] - 2 * R["take-drift-60c.wav"]["uB"]
    checks = {
        "states": {k: state(k) for k in R},
        "in-tune measured, contains 0": state("take-in-tune.wav") == "measured" and contains("take-in-tune.wav", 0.0),
        "spread-5 measured, contains 5": state("take-spread-5c.wav") == "measured" and contains("take-spread-5c.wav", 5.0),
        "spread-5 excludes 0": not contains("take-spread-5c.wav", 0.0),
        "drift at least, lower end": round(lo_drift, 3),
        "drift lower end in (0, deviation sd]": state("take-drift-60c.wav") == "at least" and 0 < lo_drift <= drift_sd,
        "uncertain not above chance": state("take-uncertain.wav") == "intent uncertain",
        "spread-5 -> in-tune improved": bool(d > 2 * math.hypot(s5["uB"], s0["uB"])),
        "improvement margin (d, U)": [round(d, 3), round(2 * math.hypot(s5["uB"], s0["uB"]), 3)],
    }
    for v in report.values():
        del v["_raw"]
    res = dict(fixtures=report, checks=checks)
    path = HERE / "results" / "fold.json"
    old = json.load(open(path)) if path.exists() else {}
    old["fixtures"] = res
    json.dump(old, open(path, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    {"coverage": coverage, "summary": summarize, "fixtures": fixtures}[sys.argv[1]](*sys.argv[2:])
