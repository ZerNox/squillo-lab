"""E-005 fold 2 (squillo iteration 38): round 2 under squillo MT-003's refusal.

Crude experiment code. Round 1, the fold and round 2 stay unchanged; this
file adds, never replaces. It imports round 2's generator and estimators.

    uv run python fold_refusal.py check      # the checks, each checked (S15) -> results/fold_refusal_checks.json
    uv run python fold_refusal.py time       # S19: one phrase of the slowest condition, timed
    uv run python fold_refusal.py synth      # round 2's 5040 phrases, both ways -> data/cache/fr_synth.pkl
    uv run python fold_refusal.py real       # 77 VocalSet originals, 40 E-002 re-syntheses -> data/cache/fr_real.pkl
    uv run python fold_refusal.py fixtures <dir>   # squillo's fixtures/metrics/ takes, checked -> results/fold_refusal_fixtures.json
    uv run python fold_refusal.py report     # -> results/fold_refusal.json

Question (squillo F-033 (e), R-07): squillo `metrics` MT-003 makes a frame
unmeasurable when its aperiodicity (YIN's d' at the chosen lag, squillo
SG-008) is 0.02 or more. Round 2 measured with every frame YIN gave. Does
round 2's rule still hold with the refusal: sigma-hat shown measured, +- 2 u_B,
when its upper end is at most 25 cents (U25), its lower end otherwise, with
the note centre over whole vibrato cycles (`cyc`)? And does the improvement
test (MT-008's form where both are measured, the one-sided form on honest
ends otherwise) still call no change that is not there?

Bar, written before the run (S15, L-036): in every cell of round 2's design
(length x vibrato x sigma), the shown statement excludes the singer's spread
(the population sigma, round 2's R3 truth) in at most 5 % of phrases, the
share a k = 2 interval claims (GUM 6.3.3). It is itself checked first: on
round 2's cached values (no refusal) U25 must pass it and U35 must fail it.
"""

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import hashlib
import json
import math
import pickle
import struct
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

import run
import infer
import round2 as R2

HERE = Path(__file__).parent
CACHE = HERE / "data" / "cache"
OUT = HERE / "results"
SQ = HERE.parents[2] / "squillo"
REFUSE = 0.02  # squillo MT-003: a frame with aperiodicity >= 0.02 is unmeasurable
UPPER = 25.0   # round 2's U25
BAR = 5.0      # per cent, the bar above
SR, HOP = 48_000, 384


# ------------------------------------------------------------ the pipeline

def track(x, refuse=True):
    """run.track, then MT-003's refusal on YIN's d' at the chosen lag."""
    t, cents, dmin = run.track(x)
    cents = cents.copy()
    n_ref = 0
    if refuse:
        bad = ~np.isnan(cents) & (dmin >= REFUSE)
        n_ref = int(bad.sum())
        cents[bad] = np.nan
    return t, cents, dmin, n_ref


def measure(cents, t, settle_fn=R2.settle_cycles):
    """Round 2's take measure without its Neyman interval: segments, settle, global tuning, spread_all."""
    segs = R2.est_segments(cents)
    if not segs:
        return dict(s=np.inf, n=0.0, uA=np.nan, uB=np.nan, uD=np.nan, us=np.nan), None, None
    o = R2.infer_global(cents, t, segs, settle_fn)
    keep = o["dur"] >= R2.TRANS_S
    if keep.sum() < 2:
        return dict(s=np.inf, n=0.0, uA=np.nan, uB=np.nan, uD=np.nan, us=np.nan), o, keep
    return R2.spread_all(o["dev"][keep], o["dur"][keep], o["u_settle"][keep]), o, keep


def state(sp, upper=UPPER):
    if not np.isfinite(sp["s"]):
        return "uncertain"
    return "measured" if sp["s"] + 2 * sp["uB"] <= upper else "at least"


def miss(sp, truth, upper=UPPER):
    st = state(sp, upper)
    if st == "uncertain":
        return False
    if st == "measured":
        return abs(sp["s"] - truth) > 2 * sp["uB"]
    return sp["s"] - 2 * sp["uB"] > truth


def compare(a, b, upper=UPPER):
    """+1 b (the later) better, -1 worse, 0 no change shown: MT-008's form where both are
    measured; else the later measured with its upper end below the earlier's lower end, or
    the reverse."""
    sa, sb = state(a, upper), state(b, upper)
    if sa == "measured" and sb == "measured":
        d = a["s"] - b["s"]
        return int(np.sign(d)) if abs(d) > 2 * math.hypot(a["uB"], b["uB"]) else 0
    if sb == "measured" and sa == "at least" and b["s"] + 2 * b["uB"] < a["s"] - 2 * a["uB"]:
        return 1
    if sa == "measured" and sb == "at least" and a["s"] + 2 * a["uB"] < b["s"] - 2 * b["uB"]:
        return -1
    return 0


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None, None, 0]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(100 * p, 1), round(100 * (c - h), 1), round(100 * (c + h), 1), n]


# ------------------------------------------------------------ synthetic

def one(args):
    voice_name, scale, sigma, vib, n_notes, seed = args
    x, tr = R2.phrase(voice_name, scale, sigma, vib, n_notes, seed)
    row = dict(voice=voice_name, scale=scale, sigma=sigma, vib=vib, n_notes=n_notes, seed=seed)
    t, c0, dmin, _ = track(x, refuse=False)
    voiced = ~np.isnan(c0)
    row["frames_measured"] = int(voiced.sum())
    row["frames_refused"] = int((voiced & (dmin >= REFUSE)).sum())
    row["off"] = measure(c0, t)[0]
    c1 = c0.copy()
    c1[voiced & (dmin >= REFUSE)] = np.nan
    row["on"] = measure(c1, t)[0]
    return row


def time_one():
    """S19: the slowest condition, 56 notes with vibrato, one process."""
    jobs = [j for j in R2.jobs_synth() if j[4] == 56 and j[3] == 1][:3]
    ts = []
    for j in jobs:
        t0 = time.time()
        one(j)
        ts.append(time.time() - t0)
    print("56 notes, vibrato, s per phrase:", [round(v, 1) for v in ts])


def jobs_cut(per_cell):
    """Round 2's jobs, the first per_cell phrases of each cell (round 2's own seeds)."""
    jobs = R2.jobs_synth()
    assert len(jobs) == 5040
    return [j for i, j in enumerate(jobs) if i % R2.PER_CELL < per_cell]


def run_synth(per_cell="60", procs="18"):
    """S19 (L-037): throughput is timed under the pool itself (`time_pool`), and rows are
    saved every 100 phrases so a stopped run keeps its work and resumes."""
    per_cell, procs = int(per_cell), int(procs)
    jobs = jobs_cut(per_cell)
    path = CACHE / "fr_synth.pkl"
    rows = pickle.load(open(path, "rb")) if path.exists() else []
    done = {r["seed"] for r in rows}
    todo = [j for j in jobs if j[5] not in done]
    t0 = time.time()
    with Pool(procs) as p:
        for k, r in enumerate(p.imap_unordered(one, todo, chunksize=2), 1):
            rows.append(r)
            if k % 100 == 0 or k == len(todo):
                pickle.dump(rows, open(path, "wb"))
                print(f"{len(rows)} of {len(jobs)} phrases, {round((time.time() - t0) / 60, 1)} min", flush=True)


def time_pool(n="72", procs="18"):
    """S19 under load: n phrases, spread over lengths and vibrato, on the pool."""
    n, procs = int(n), int(procs)
    jobs = jobs_cut(R2.PER_CELL)
    pick = jobs[::len(jobs) // n][:n]
    t0 = time.time()
    with Pool(procs) as p:
        p.map(one, pick, chunksize=1)
    dt = time.time() - t0
    print(f"{n} phrases on {procs} processes: {dt:.1f} s, {dt / n:.3f} s per phrase of wall time")


# ------------------------------------------------------------ real voices

def one_real(args):
    kind, path = args
    import soundfile as sf
    from scipy.signal import resample_poly
    if kind == "resynth":
        z = np.load(path)
        x = z["y"].astype(np.float32)
    else:
        x, sr = sf.read(path, dtype="float64")
        if x.ndim > 1:
            x = x.mean(axis=1)
        g = math.gcd(SR, sr)
        x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    t, c0, dmin, _ = track(x, refuse=False)
    voiced = ~np.isnan(c0)
    c1 = c0.copy()
    c1[voiced & (dmin >= REFUSE)] = np.nan
    row = dict(kind=kind, name=Path(path).stem, frames_measured=int(voiced.sum()),
               frames_refused=int((voiced & (dmin >= REFUSE)).sum()))
    for key, c in (("off", c0), ("on", c1)):
        sp, o, keep = measure(c, t)
        row[key] = sp
        # halves of the take's notes, for a false change between them (round 2's R6)
        hv = []
        if keep is not None:
            idx = np.flatnonzero(keep)
            h = len(idx) // 2
            for part in (idx[:h], idx[h:]):
                hv.append(R2.spread_all(o["dev"][part], o["dur"][part], o["u_settle"][part]) if len(part) >= 2
                          else dict(s=np.inf, uB=np.nan))
        row[key + "_halves"] = hv
    return row


def run_real():
    names = [Path(l.strip()).name for l in (HERE / "data" / "vocalset-files.txt").read_text().splitlines() if l.strip()]
    originals = [("original", CACHE / n) for n in names]
    assert all(p.exists() for _, p in originals)
    r2 = sorted(p for p in (R2.E002 / "data" / "cache" / "r2").glob("*.npz")
                if "scales_straight" in p.stem or "row_vibrato" in p.stem)
    assert len(r2) == 40, len(r2)
    with Pool(18) as p:
        rows = p.map(one_real, originals + [("resynth", q) for q in r2])
    pickle.dump(rows, open(CACHE / "fr_real.pkl", "wb"))
    print(len(rows), "real takes")


# ------------------------------------------------------------ checks (S15)

def check():
    out = {}
    # 1. The pipeline without the refusal reproduces round 2's cached cyc values (must pass),
    #    and not those of another phrase (must fail): one phrase per cell of 14 notes, and 56.
    cached = {r["seed"]: r for r in pickle.load(open(CACHE / "r2_synth.pkl", "rb"))}
    jobs = [j for j in R2.jobs_synth() if j[4] in (14, 56)]
    pick = [jobs[k] for k in range(0, len(jobs), R2.PER_CELL)]
    with Pool(18) as p:
        rows = p.map(one, pick)
    same, other = [], []
    seeds = [j[5] for j in pick]
    for r, s_next in zip(rows, seeds[1:] + seeds[:1]):
        c, o = cached[r["seed"]]["cyc"], cached[s_next]["cyc"]
        same.append(abs(r["off"]["s"] - c["s"]) <= 1e-9 and abs(r["off"]["uB"] - c["uB"]) <= 1e-9
                    if np.isfinite(c["s"]) else not np.isfinite(r["off"]["s"]))
        other.append(bool(np.isfinite(o["s"]) and np.isfinite(r["off"]["s"]) and abs(r["off"]["s"] - o["s"]) <= 1e-9))
    out["reproduces_round2"] = dict(phrases=len(rows), same=int(sum(same)), matches_another_phrase=int(sum(other)))
    assert all(same), out
    assert not any(other), out
    # 2. The refusal: on squillo's tone-aperiodic.wav (MT-003's scenario) at least one frame
    #    refused, every refused frame at d' >= 0.02, none below (must pass); on sine-220hz.wav none
    #    refused (must pass); with the threshold mistyped as 0.2 none refused on tone-aperiodic
    #    (must fail the first criterion).
    import soundfile as sf
    xa, _ = sf.read(SQ / "fixtures" / "metrics" / "tone-aperiodic.wav", dtype="float32")
    xs, _ = sf.read(SQ / "fixtures" / "signal" / "sine-220hz.wav", dtype="float32")
    t, c0, dmin = run.track(xa)
    _, c1, _, n_ref = track(xa)
    refused = ~np.isnan(c0) & np.isnan(c1)
    ok_a = n_ref > 0 and bool(np.all(dmin[refused] >= REFUSE)) and bool(np.all(dmin[~np.isnan(c1)] < REFUSE))
    _, _, _, n_s = track(xs)
    wrong = int(np.sum(~np.isnan(c0) & (dmin >= 0.2)))
    out["refusal"] = dict(tone_aperiodic_refused=n_ref, tone_aperiodic_measured=int(np.sum(~np.isnan(c1))),
                          dmin_range=[float(np.nanmin(dmin)), float(np.nanmax(dmin))], ok=ok_a,
                          sine_refused=n_s, mistyped_0_2_refused=wrong)
    assert ok_a and n_s == 0 and wrong == 0, out
    # 3. The bar, on round 2's cached values (no refusal): U25 must pass, U35 must fail.
    rows2 = list(cached.values())
    for upper, must in ((25.0, True), (35.0, False)):
        worst = worst_cell(rows2, "cyc", upper)
        out[f"bar_on_round2_U{int(upper)}"] = dict(worst=worst, passes=worst[0] <= BAR)
        assert (worst[0] <= BAR) == must, out
    json.dump(out, open(OUT / "fold_refusal_checks.json", "w"), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float))


def cells(rows):
    c = {}
    for r in rows:
        c.setdefault((r["n_notes"], r["vib"], r["sigma"]), []).append(r)
    for v in c.values():
        v.sort(key=lambda r: r["seed"])  # imap_unordered: pairs and power match phrases by seed order
    return c


def worst_cell(rows, key, upper):
    worst = None
    for (L, vib, sg), rs in sorted(cells(rows).items()):
        w = wilson(sum(miss(r[key], float(sg), upper) for r in rs), len(rs)) + [f"L={L} vib={vib} sigma={sg}"]
        if worst is None or w[0] > worst[0]:
            worst = w
    return worst


# ------------------------------------------------------------ report

def report():
    rows = pickle.load(open(CACHE / "fr_synth.pkl", "rb"))
    real = pickle.load(open(CACHE / "fr_real.pkl", "rb"))
    r2real = pickle.load(open(CACHE / "r2_real.pkl", "rb"))
    out = dict(conditions=dict(refuse_at=REFUSE, upper=UPPER, bar_percent=BAR, phrases=len(rows)))
    cached = {r["seed"]: r["cyc"] for r in pickle.load(open(CACHE / "r2_synth.pkl", "rb"))}
    same = sum((abs(r["off"]["s"] - cached[r["seed"]]["s"]) <= 1e-9 and abs(r["off"]["uB"] - cached[r["seed"]]["uB"]) <= 1e-9)
               if np.isfinite(cached[r["seed"]]["s"]) else not np.isfinite(r["off"]["s"]) for r in rows)
    out["off_reproduces_round2"] = [int(same), len(rows)]
    fm = sum(r["frames_measured"] for r in rows)
    fr = sum(r["frames_refused"] for r in rows)
    out["synthetic_frames"] = dict(measured_by_yin=fm, refused=fr, refused_percent=round(100 * fr / fm, 2),
                                   refused_percent_vib0=round(100 * sum(r["frames_refused"] for r in rows if not r["vib"]) /
                                                              sum(r["frames_measured"] for r in rows if not r["vib"]), 2),
                                   refused_percent_vib1=round(100 * sum(r["frames_refused"] for r in rows if r["vib"]) /
                                                              sum(r["frames_measured"] for r in rows if r["vib"]), 2))
    per = {}
    for (L, vib, sg), rs in sorted(cells(rows).items()):
        per[f"L={L} vib={vib} sigma={sg}"] = {
            k: dict(miss=wilson(sum(miss(r[k], float(sg)) for r in rs), len(rs)),
                    measured=sum(state(r[k]) == "measured" for r in rs),
                    at_least=sum(state(r[k]) == "at least" for r in rs),
                    uncertain=sum(state(r[k]) == "uncertain" for r in rs),
                    uB_median=round(float(np.median([r[k]["uB"] for r in rs if np.isfinite(r[k]["uB"])] or [np.nan])), 2))
            for k in ("off", "on")}
    out["cells"] = per
    out["worst_cell"] = {k: worst_cell(rows, k, UPPER) for k in ("off", "on")}
    out["bar_passes_with_refusal"] = out["worst_cell"]["on"][0] <= BAR
    # lower ends over all reported phrases
    for k in ("off", "on"):
        lo = [r for r in rows if state(r[k]) != "uncertain"]
        out[f"lower_end_holds_{k}"] = wilson(sum(r[k]["s"] - 2 * r[k]["uB"] <= r["sigma"] for r in lo), len(lo))
        meas = [r for r in rows if state(r[k]) == "measured"]
        out[f"measured_{k}"] = dict(n=len(meas), max_value=round(max(r[k]["s"] for r in meas), 2),
                                    above_10=sum(r[k]["s"] > 10 for r in meas),
                                    covers=wilson(sum(abs(r[k]["s"] - r["sigma"]) <= 2 * r[k]["uB"] for r in meas), len(meas)))
    # false change on pairs from one cell (round 2's R6: phrases 2i, 2i+1), and power 20 -> 0, 40 -> 10
    cl = cells(rows)
    fc, pw = {}, {}
    for L in R2.LENGTHS:
        for vib in (0, 1):
            for k in ("off", "on"):
                calls = [compare(rs[2 * i][k], rs[2 * i + 1][k]) != 0
                         for sg in R2.SIGMAS for rs in [cl[(L, vib, sg)]] for i in range(len(rs) // 2)]
                fc[f"L={L} vib={vib} {k}"] = wilson(sum(calls), len(calls))
                for a, b in ((20, 0), (40, 10)):
                    A, B = cl[(L, vib, a)], cl[(L, vib, b)]
                    res = [compare(x[k], y[k]) for x, y in zip(A, B)]
                    pw[f"L={L} vib={vib} {a}->{b} {k}"] = dict(improved=wilson(sum(v == 1 for v in res), len(res)),
                                                               worse=sum(v == -1 for v in res))
    out["false_change_same_cell"] = fc
    out["power"] = pw
    # real takes
    truth = {r["name"]: r["truth"] for r in r2real["resynth"]}
    rr = {}
    for kind, sets in (("resynth", ("scales_straight", "row_vibrato")),
                       ("original", ("scales_straight", "row_straight", "scales_vibrato", "row_vibrato"))):
        for S in sets:
            b = [r for r in real if r["kind"] == kind and S in r["name"]]
            d = dict(takes=len(b),
                     frames_refused_percent=round(100 * sum(r["frames_refused"] for r in b) / max(1, sum(r["frames_measured"] for r in b)), 2))
            for k in ("off", "on"):
                d[k] = dict(uB_median=round(float(np.median([r[k]["uB"] for r in b if np.isfinite(r[k]["uB"])])), 2),
                            s_median=round(float(np.median([r[k]["s"] for r in b if np.isfinite(r[k]["s"])])), 2),
                            measured=sum(state(r[k]) == "measured" for r in b),
                            at_least=sum(state(r[k]) == "at least" for r in b),
                            uncertain=sum(state(r[k]) == "uncertain" for r in b))
                if kind == "resynth":
                    full = [r for r in b if truth[r["name"]]["found"] == truth[r["name"]]["states"]]
                    d[k]["truth_every_state_found"] = len(full)
                    d[k]["miss_on_full_truth"] = wilson(sum(miss(r[k], truth[r["name"]]["sd"]) for r in full), len(full))
                    d[k]["lower_end_holds_all"] = wilson(sum(r[k]["s"] - 2 * r[k]["uB"] <= truth[r["name"]]["sd"]
                                                             for r in b if np.isfinite(r[k]["s"])),
                                                         sum(np.isfinite(r[k]["s"]) for r in b))
                if kind == "original":
                    hv = [compare(r[k + "_halves"][0], r[k + "_halves"][1]) != 0 for r in b if len(r[k + "_halves"]) == 2]
                    d[k]["halves_false_change"] = [int(sum(hv)), len(hv)]
            rr[f"{kind} {S}"] = d
    out["real"] = rr
    json.dump(out, open(OUT / "fold_refusal.json", "w"), indent=1, default=float)
    print(json.dumps({k: v for k, v in out.items() if k not in ("cells", "power", "false_change_same_cell")}, indent=1, default=float))


# ------------------------------------------------------------ fixtures for squillo

MELODY = [-12, -10, -8, -7, -5, -3, -1, 0, -1, -3, -5, -7, -8, -10]
TUNING = 23.0
GAP, RAMP = 4_800, 480
pi = math.pi
DEV5 = [-7.5, 2.5, 5, -2.5, 0, 7.5, -5, 7.5, -7.5, 2.5, -2.5, 5, -5, 0]
# take-spread-15c: the fold's 5-cent deviations times three (population sd exactly 15)
DEV15 = [3 * d for d in DEV5]
VIB_BETA, VIB_RATE = 0.0204, 5.5  # f(t) = f_j (1 + beta sin(2 pi r t)): +34.96 / -35.69 cents at 5.5 Hz
# (inside E-002 result 21, VocalSet extent p5 6.0 to p95 110.5 cents; under 38.3 cents, where the mean of
# exp(i pi A sin / 50) over a cycle, J0(pi A / 50), is still positive: at +-50 it is J0(pi) = -0.30, and the
# provisional tuning of infer.segment turns half a semitone, which splits every note (found at iteration 38)


def note_freq(j, dev):
    return 440 * 2 ** ((100 * MELODY[j] + TUNING + dev) / 1200)


def take_sample(n, devs, note, vib):
    if n < GAP:
        return 0.0
    j, m = divmod(n - GAP, note + GAP)
    if m >= note:
        return 0.0
    f = note_freq(j, devs[j])
    g = 1.0
    if m < RAMP:
        g = 0.5 - 0.5 * math.cos(pi * m / RAMP)
    elif m >= note - RAMP:
        g = 0.5 - 0.5 * math.cos(pi * (note - m) / RAMP)
    ph = 2 * pi * f * m / 48000
    if vib:
        ph += f * VIB_BETA / VIB_RATE * (1 - math.cos(2 * pi * VIB_RATE * m / 48000))
    return 0.5 * g * math.sin(ph)


def weak_odd_amps():
    """E-002 round 3's must-fail tone (r3_octave.py check(), from run.py spectrum('saw12')):
    350 Hz, harmonic k at 1/k^2 up to 20 kHz, the first 26 dB under the second, every other odd
    harmonic 10 dB under its 1/k^2 level; sine phase 0; scaled by 0.5 / (sum of amplitudes)."""
    K = int(20_000 // 350.0)
    k = np.arange(1, K + 1, dtype=float)
    s = 1 / k ** 2
    s[0] = s[1] * 10 ** (-26 / 20)
    s[2::2] *= 10 ** (-10 / 20)
    return s


def weak_odd_sample(n, s, scale):
    return scale * sum(a * math.sin(2 * pi * (k + 1) * 350.0 * n / 48000) for k, a in enumerate(s))


def wav(samples):
    data = b"".join(struct.pack("<f", x) for x in samples)
    fmt = struct.pack("<HHIIHHH", 3, 1, SR, SR * 4, 4, 32, 0)
    body = (b"WAVE" + b"fmt " + struct.pack("<I", 18) + fmt
            + b"fact" + struct.pack("<I", 4) + struct.pack("<I", len(samples))
            + b"data" + struct.pack("<I", len(data)) + data)
    return b"RIFF" + struct.pack("<I", len(body)) + body


def fixtures(outdir="/tmp/e005-fold-refusal"):
    import soundfile as sf
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    E2, C6 = 440 * 2 ** (R2.E2_CENTS / 1200), 440 * 2 ** (R2.C6_CENTS / 1200)
    rep = {}
    new = {"take-spread-15c.wav": (DEV15, 19_200, False), "take-vibrato-in-tune.wav": ([0.0] * 14, 38_400, True)}
    for name, (devs, note, vib) in new.items():
        # conditions, asserted on the formula's exact values (S15)
        fr = [note_freq(j, d) for j, d in enumerate(devs)]
        lo_f = min(fr) * (1 - VIB_BETA if vib else 1)
        hi_f = max(fr) * (1 + VIB_BETA if vib else 1)
        assert E2 <= lo_f and hi_f <= C6, (name, lo_f, hi_f)
        assert abs(np.mean(devs)) < 1e-9 and all(-50 < d < 50 for d in devs), name
        N = GAP + 14 * (note + GAP)
        xs = [take_sample(n, devs, note, vib) for n in range(N)]
        f32 = np.array(xs, dtype=np.float32)
        assert float(np.abs(f32).max()) <= 0.5
        for j in range(15):
            a = j * (note + GAP)
            assert not f32[a:a + GAP].any(), (name, j)
        blob = wav(xs)
        (out / name).write_bytes(blob)
        rep[name] = dict(sha256=hashlib.sha256(blob).hexdigest(), bytes=len(blob), samples=N,
                         deviation_sd=round(float(np.sqrt(np.mean(np.square(devs)))), 4),
                         f_min=round(lo_f, 3), f_max=round(hi_f, 3))
    s = weak_odd_amps()
    scale = 0.5 / float(s.sum())
    xs = [weak_odd_sample(n, s, scale) for n in range(48_000)]
    assert max(abs(v) for v in xs) <= 0.5
    blob = wav(xs)
    (out / "tone-weak-odd.wav").write_bytes(blob)
    rep["tone-weak-odd.wav"] = dict(sha256=hashlib.sha256(blob).hexdigest(), bytes=len(blob), samples=48_000,
                                    harmonics=len(s), h1_under_h2_db=26, odd_under_db=10, scale=scale)
    # the new pipeline on every take fixture: refusal, cyc centre, U25; and round 1's median for contrast
    takes = {n: out / n for n in new}
    for n in ("take-in-tune.wav", "take-spread-5c.wav", "take-drift-60c.wav", "take-uncertain.wav"):
        takes[n] = SQ / "fixtures" / "metrics" / n
    R = {}
    for n, p in sorted(takes.items()):
        x, sr = sf.read(p, dtype="float32")
        assert sr == SR
        t, c, dmin, n_ref = track(x)
        sp = measure(c, t)[0]
        spm = measure(c, t, R2.settle_median)[0]
        R[n] = sp
        rep.setdefault(n, {}).update(
            refused=n_ref, state=state(sp), s=round(sp["s"], 3) if np.isfinite(sp["s"]) else None,
            uB=round(sp["uB"], 3) if np.isfinite(sp["uB"]) else None,
            upper=round(sp["s"] + 2 * sp["uB"], 3) if np.isfinite(sp["s"]) else None,
            lower=round(sp["s"] - 2 * sp["uB"], 3) if np.isfinite(sp["s"]) else None,
            state_under_S10=("uncertain" if not np.isfinite(sp["s"]) else "measured" if sp["s"] <= 10 else "at least"),
            median_centre=dict(state=state(spm), s=round(spm["s"], 3) if np.isfinite(spm["s"]) else None,
                               uB=round(spm["uB"], 3) if np.isfinite(spm["uB"]) else None))
    # the weak-odd tone through MT-003
    x, _ = sf.read(out / "tone-weak-odd.wav", dtype="float32")
    t, c0, dmin = run.track(x)
    e = 1200 * np.log2(440 * 2 ** (c0 / 1200) / 350.0)
    meas = ~np.isnan(c0)
    rep["tone-weak-odd.wav"].update(frames=len(c0), measured_by_yin=int(meas.sum()),
                                    octave_high=int(np.sum(meas & (np.abs(e - 1200) < 100))),
                                    within_50_of_350=int(np.sum(meas & (np.abs(e) <= 50))),
                                    dmin_min_measured=round(float(np.nanmin(dmin[meas])), 5) if meas.any() else None,
                                    refused_by_mt003=int(np.sum(meas & (dmin >= REFUSE))),
                                    accepted=int(np.sum(meas & (dmin < REFUSE))))

    def contains(n, v):
        return R[n]["s"] - 2 * R[n]["uB"] <= v <= R[n]["s"] + 2 * R[n]["uB"]
    checks = {
        "in-tune measured, contains 0": state(R["take-in-tune.wav"]) == "measured" and contains("take-in-tune.wav", 0),
        "spread-5 measured, contains 5, excludes 0": state(R["take-spread-5c.wav"]) == "measured"
        and contains("take-spread-5c.wav", 5) and not contains("take-spread-5c.wav", 0),
        "spread-15 measured, contains 15, excludes 5": state(R["take-spread-15c.wav"]) == "measured"
        and contains("take-spread-15c.wav", 15) and not contains("take-spread-15c.wav", 5),
        "spread-15 above 10 (at least under S10)": R["take-spread-15c.wav"]["s"] > 10,
        "vibrato in tune measured, contains 0": state(R["take-vibrato-in-tune.wav"]) == "measured"
        and contains("take-vibrato-in-tune.wav", 0),
        "drift at least, lower end in (0, 18.6052]": state(R["take-drift-60c.wav"]) == "at least"
        and 0 < R["take-drift-60c.wav"]["s"] - 2 * R["take-drift-60c.wav"]["uB"] <= 18.6052,
        "uncertain": state(R["take-uncertain.wav"]) == "uncertain",
        "15 -> 5 improved": compare(R["take-spread-15c.wav"], R["take-spread-5c.wav"]) == 1,
        "5 -> in-tune improved": compare(R["take-spread-5c.wav"], R["take-in-tune.wav"]) == 1,
        "5 -> 5 no change": compare(R["take-spread-5c.wav"], R["take-spread-5c.wav"]) == 0,
        "drift -> in-tune improved (one-sided)": compare(R["take-drift-60c.wav"], R["take-in-tune.wav"]) == 1,
        "in-tune -> drift worse (one-sided)": compare(R["take-in-tune.wav"], R["take-drift-60c.wav"]) == -1,
        "drift -> drift no change (two lower ends)": compare(R["take-drift-60c.wav"], R["take-drift-60c.wav"]) == 0,
        "weak-odd: every frame YIN measures is octave high and refused": (
            rep["tone-weak-odd.wav"]["measured_by_yin"] > 0
            and rep["tone-weak-odd.wav"]["octave_high"] == rep["tone-weak-odd.wav"]["measured_by_yin"]
            and rep["tone-weak-odd.wav"]["accepted"] == 0),
    }
    # the must-fail cases of the checks: the old rule and the old centre
    must_fail = {
        "spread-15 under S10 is not measured": rep["take-spread-15c.wav"]["state_under_S10"] != "measured",
        "vibrato in tune with round 1's median centre is not measured": rep["take-vibrato-in-tune.wav"]["median_centre"]["state"] != "measured",
    }
    res = dict(fixtures=rep, checks=checks, must_fail=must_fail)
    json.dump(res, open(OUT / "fold_refusal_fixtures.json", "w"), indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))
    assert all(checks.values()), checks


if __name__ == "__main__":
    {"check": check, "time": time_one, "time_pool": time_pool, "synth": run_synth, "real": run_real,
     "report": report, "fixtures": fixtures}[sys.argv[1]](*sys.argv[2:])
