"""E-005 round 2: every check checked before it is trusted (squillo S15).

Each check runs once on a case it must pass and once on a case it must
fail, each known independently of the check. Writes results/round2_checks.json.
Crude experiment code.
"""

import json
import math

import numpy as np

import round2 as R
import run

rng = np.random.default_rng(31)


def c1_contour():
    """The generator's E2..C6 contour assertion (S15): a real phrase passes, the same shifted by +1500 cents fails."""
    x, tr = R.phrase("soprano_high", "major", 40, 1, 56, 1)
    passed = True
    try:
        R.phrase("soprano_high", "major", 40, 1, 56, 1, shift=1500.0)
        failed = False
    except AssertionError:
        failed = True
    return dict(pass_case=dict(ok=passed, lo=round(tr["lo"], 1), hi=round(tr["hi"], 1)), fail_case_raised=failed)


def c2_frame_truth():
    """Known f0 matched to frames by YIN's own index: an exponential glide of 1200
    cents/s. Criterion, from the definition: a truth matched to the right frame
    is nearer YIN than half a frame's glide, rate * HOP_S / 2 = 4.8 cents; one
    frame off moves it by a whole frame's glide, 9.6 cents. (Iteration 31's
    first criterion, 3 cents, was typed, not derived; it failed at 3.2.)
    Must fail: the same with the instants shifted by one frame."""
    rate = 1200.0  # cents/s
    n = 2 * R.SR
    ts = np.arange(n) / R.SR
    f = 200.0 * 2 ** (ts * rate / 1200)  # 200 -> 400 Hz
    ph = 2 * np.pi * np.cumsum(f) / R.SR
    x = (0.5 * np.sin(ph)).astype(np.float32)
    t, cents, _ = run.track(x)
    tc = R.frame_truth_cents(f, t)
    ok = ~np.isnan(cents) & ~np.isnan(tc) & (t > 0.1) & (t < 1.9)
    med = float(np.median(np.abs(cents[ok] - tc[ok])))
    tc2 = R.frame_truth_cents(f, t + R.HOP_S)
    med2 = float(np.median(np.abs(cents[ok] - tc2[ok])))
    crit = rate * R.HOP_S / 2
    return dict(criterion_cents=crit, pass_case=round(med, 3), passes=med <= crit,
                fail_case_shifted_one_frame=round(med2, 3), fails=med2 > crit)


def c3_centre():
    """The whole-cycle centre on known contours: c0 + A sin(2 pi f t + phi), no noise, windows
    0.2..0.6 s. Criterion, from the definition: whole cycles are cut from 8 ms frames, so at
    most half a frame's phase at each end is left over; the leftover shifts a median of a
    sinusoid by at most A sin(pi f h) / (pi k) for k whole cycles (k = 1 the worst case).
    (Iteration 31's first criterion, 0.5 cent, was typed, not derived; it failed at 0.59.)
    Round 1's median must fail the same criterion on some window (a partial cycle biases it)."""
    A, f = 50.0, 5.5
    bound = A * math.sin(math.pi * f * R.HOP_S) / math.pi
    errs_fit, errs_med = [], []
    for L in (0.2, 0.25, 0.3, 0.4, 0.5, 0.6):
        for phi in np.linspace(0, 2 * np.pi, 8, endpoint=False):
            tt = np.arange(int(L / R.HOP_S)) * R.HOP_S
            x = 17.0 + A * np.sin(2 * np.pi * f * tt + phi)
            c, u, fr, amp = R.fit_centre(x, tt)
            errs_fit.append(abs(c - 17.0))
            errs_med.append(abs(np.median(x) - 17.0))
    return dict(criterion_cents=round(bound, 3), fit_max_err=round(max(errs_fit), 4), passes=max(errs_fit) <= bound,
                median_max_err=round(float(max(errs_med)), 2), median_fails=bool(max(errs_med) > bound))


def c4_interval():
    """The coverage machinery on the model itself (no audio): wrapped deviations
    sigma Z + u Z', with durations 0.25..0.8 s. N and D should cover sigma about 95 %.
    Must fail: N told u = 0 when the settle noise is 15 cents, at sigma = 0."""
    res = {}
    for n_notes in (14, 56):
        for sg in (0, 10, 20, 30):
            kN = kD = kB = rep = 0
            m = 200
            for i in range(m):
                w = rng.uniform(0.25, 0.8, n_notes)
                us = np.full(n_notes, 2.0)
                d = sg * rng.standard_normal(n_notes) + us * rng.standard_normal(n_notes)
                d = (d + 50) % 100 - 50
                sp = R.spread_all(d, w, us)
                lo, hi = R.neyman(sp["s"], w, us, seed=i)
                kN += lo <= sg <= hi
                if np.isfinite(sp["s"]):
                    rep += 1
                    kD += abs(sp["s"] - sg) <= 2 * sp["uD"]
                    kB += abs(sp["s"] - sg) <= 2 * sp["uB"]
            res[f"n={n_notes},sigma={sg}"] = dict(N=round(100 * kN / m, 1), D_reported=round(100 * kD / max(rep, 1), 1),
                                                   B_reported=round(100 * kB / max(rep, 1), 1), reported=rep)
    # must fail
    k = 0
    m = 200
    for i in range(m):
        w = rng.uniform(0.25, 0.8, 14)
        d = 15.0 * rng.standard_normal(14)
        sp = R.spread_all(d, w, np.full(14, 15.0))
        lo, hi = R.neyman(sp["s"], w, np.zeros(14), seed=i)
        k += lo <= 0.0 <= hi
    res["fail_case: sigma=0, noise 15, told u=0"] = dict(N=round(100 * k / m, 1))
    Ns = [v["N"] for kk, v in res.items() if not kk.startswith("fail")]
    return dict(cells=res, N_min=min(Ns), passes=min(Ns) >= 92.0, fails=res["fail_case: sigma=0, noise 15, told u=0"]["N"] < 80)


def c5_truth_procedures():
    """Truth-making procedures on one input of every condition (S15): the known-melody
    alignment finds every score state on one synthetic phrase per length and vibrato;
    per-note attribution at sigma = 0 finds every note; the real truth (E-002 re-synthesis)
    finds every state on one take of each set."""
    out = {}
    for n_notes in R.LENGTHS:
        for vib in (0, 1):
            x, tr = R.phrase("tenor", "major", 0, vib, n_notes, 7 + n_notes + vib)
            t, cents, _ = run.track(x)
            states, _ = R.merge_repeats(tr["notes"])
            km = R.known_melody(cents, t, states, R.settle_cycles)
            segs = R.est_segments(cents)
            nof, mid = run.note_frames(t, tr["starts"], tr["durs"])
            o = R.infer_global(cents, t, segs, R.settle_cycles)
            keep = o["dur"] >= R.TRANS_S
            calls, right, found = R.per_note(nof, mid, segs, o, keep, tr["notes"])
            row = R.one_synth(("tenor", "major", 0, vib, n_notes, 7 + n_notes + vib))
            out[f"synth n={n_notes} vib={vib}"] = dict(realised_truth_sigma0=round(row["realised_c"], 2),states=km["states"], found=km["found"], dtw_bad=round(km["bad"], 4),
                                                      known_s=round(km["s"], 2), notes=len(right), right=int(right.sum()))
    for stem in ("f1_scales_straight_a", "f1_row_vibrato"):
        z = np.load(R.E002 / "data" / "cache" / "r2" / (stem + ".npz"))
        ft = R.truth_per_sample(z["f0"], len(z["y"]))
        t, cents, _ = run.track(z["y"].astype(np.float32))
        tc = R.frame_truth_cents(ft, t)
        states, _ = R.merge_repeats(R.score_of(stem))
        tr = R.truth_spread(tc, t, states)
        out[stem] = dict(states=tr["states"], found=tr["found"], dtw_bad=round(tr["bad"], 4),
                         truth_sd=round(tr["sd"], 2), truth_sd_median_centre=round(tr["sd_median_centre"], 2))
    return out


def main():
    res = dict(c1_contour=c1_contour(), c2_frame_truth=c2_frame_truth(), c3_centre=c3_centre(),
               c4_interval=c4_interval(), c5_truth_procedures=c5_truth_procedures())
    json.dump(res, open(R.OUT / "round2_checks.json", "w"), indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
