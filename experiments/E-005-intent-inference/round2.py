"""E-005 round 2 (squillo iteration 31): an honest +- where takes are.

Crude experiment code. Round 1 (run.py, infer.py) and the fold (fold.py)
stay unchanged; this file adds, never replaces.

    uv run python round2.py check    # checks of the checks (S15) -> results/round2_checks.json
    uv run python round2.py synth    # synthetic phrases, 14/28/56 notes -> data/cache/r2_synth.pkl
    uv run python round2.py real     # VocalSet: 77 originals, 40 E-002 re-syntheses -> data/cache/r2_real.pkl
    uv run python round2.py report   # -> results/round2.json

Questions (squillo R-06, iteration 31; F-032):
  Q1 a note centre over whole vibrato cycles: least squares, constant plus
     one sinusoid at the best rate in 3.5..8 Hz, on the settle window;
  Q2 an honest +- for the take's spread sigma-hat above 10 cents: B (the
     fold's: GUM E.4.3 (+) settle), D (a delta-method u for the circular
     estimator (+) settle), N (a Neyman interval by simulation, asymmetric,
     its upper end unbounded when the take cannot bound it); takes of 14, 28
     and 56 notes;
  Q3 improvement between two takes: its false-change rate on pairs at the
     same spread, and its power;
  Q4 a library phrase's known melody: attribution by aligning to the notes,
     spread as a linear standard deviation, no 50-cent wrap;
  Q5 the per-note +- (reference term from the circular estimate) and a
     heavier-tailed per-note flag (a uniform outlier share fitted on half the
     VocalSet singers, checked on the other half).
"""

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")  # one thread per process: the runs use a process pool

import itertools
import json
import math
import pickle
import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

import run  # before synth: synth puts E-001 on sys.path, which has its own run.py
import infer
import synth  # noqa: E402

HERE = Path(__file__).parent
CACHE = HERE / "data" / "cache"
OUT = HERE / "results"
E002 = HERE.parent / "E-002-measurement-reliability"
SR, HOP = 48_000, 384
HOP_S = HOP / SR
P = 100.0  # cents per semitone: the circle
E2_CENTS, C6_CENTS = 100 * -29, 100 * 15  # ADR 0007's range, semitones re A4
TRANS_S = 0.1
TAU = infer.TAU
RATES = np.arange(3.5, 8.0001, 0.05)  # Hz, vibrato rates searched (E-002 result 22: VocalSet p5 4.17, median 4.99, p95 6.20 Hz)
GRID = np.arange(0.0, 80.01, 1.0)  # cents, Neyman grid
M_SIM = 400
VOICED_MIN = 0.8  # share of the settle window voiced for the cycle fit
WRONG_NOTE = 150.0  # cents: with a known melody, a note this far from its aim is a wrong note, counted apart
A_VIB = 25.0  # cents: fitted vibrato amplitude gating the cycle mean (round2_amp.py: VocalSet straight p75 22.8, vibrato p25 41.8)
GLITCH = 200.0  # cents from the span median: an f0 glitch, not vibrato (E-002 result 21: extent p95 110.5 cents)
BIG = 1e9  # stands for "not above chance" inside quantiles
SIGMAS = (0, 10, 15, 20, 25, 30, 40)
LENGTHS = (14, 28, 56)
PER_CELL = 120
SPLIT = 10.0  # the fold's measured / at-least split (squillo MT-007)


# ------------------------------------------------------------ inputs (S15)
#
# Conditions written before generating (S15):
#  - every sample of the sung contour (note centre, scoop, vibrato, wobble)
#    inside ADR 0007's E2..C6, computed from the generated contour itself;
#  - every note inside the voice's own range (E-001's base + 17 semitones);
#  - note-to-note spread: normal per-note error of sd sigma; no drift in
#    round 2 (the fold covered drift);
#  - vibrato: 5.5 Hz +-50 cents, inside VocalSet's measured range (E-002
#    round 2, result 22: rate median 4.99 Hz, extent median 47 cents); the
#    real side is checked on E-002's re-synthesized VocalSet takes (`real`).

def melody(scale, base, rng, n_notes):
    """synth.melody with a lower floor: the lowest note at least A4 - 25
    semitones, so that a note -50 (tuning) - 3 sigma - 100 (scoop) - 50
    (vibrato) - wobble cents off stays above E2 (A4 - 29)."""
    degs = synth.SCALES[scale]
    tonic = base + int(rng.integers(0, 12)) - 5
    span = len(degs) + len(degs) // 2 + 1
    pos = int(rng.integers(len(degs) // 2, len(degs)))
    notes = []
    for _ in range(n_notes):
        octv, k = divmod(pos, len(degs))
        n = tonic + 12 * octv + degs[k]
        if scale == "blue" and degs[k] in (4, 11) and rng.random() < 0.3:
            n -= 1
        notes.append(n)
        step = rng.choice([-3, -2, -1, -1, 0, 1, 1, 2, 3])
        pos = int(np.clip(pos + step, 0, span - 1))
    notes = np.array(notes)
    hi, lo = min(12, base + 17), -25
    k = (hi - notes.max()) // 12  # the highest octave shift that keeps the top in range
    if notes.min() + 12 * k < lo:
        return None  # no octave shift fits both bounds: the caller draws again
    notes = notes + 12 * k
    durs = rng.uniform(0.25, 0.8, n_notes)
    return notes, durs


def contour_ok(sung, amp):
    """Every sounding sample of the contour inside E2..C6 (bounds from ADR 0007's semitones)."""
    on = amp > 1e-3
    return bool(sung[on].min() >= E2_CENTS and sung[on].max() <= C6_CENTS), float(sung[on].min()), float(sung[on].max())


def phrase(voice_name, scale, sigma, vib, n_notes, seed, shift=0.0):
    """synth.phrase with n_notes and the contour asserted (S15). shift: the check's must-fail case."""
    import voice
    from scipy.signal import butter, sosfiltfilt
    sex, base = voice.VOICES[voice_name]
    rng = np.random.default_rng(seed)
    for _ in range(100):
        m = melody(scale, base, rng, n_notes)
        if m is not None:
            break
    notes, durs = m
    assert notes.max() <= min(12, base + 17) and notes.min() >= -25, (notes.min(), notes.max(), base)
    starts = np.concatenate([[0.0], np.cumsum(durs)[:-1]]) + 0.1
    T = starts[-1] + durs[-1] + 0.1
    n = int(round(T * SR))
    t = np.arange(n) / SR
    G = rng.uniform(-50, 50)
    e = rng.normal(0, sigma, len(notes))
    sung = synth.contour(100.0 * notes + e, starts, n) + G + shift
    idx = np.clip(np.searchsorted(starts, t, "right") - 1, 0, None)
    since = t - starts[idx]
    scoop_on = rng.random(len(notes)) < 0.5
    depth = rng.uniform(30, 100, len(notes)) * scoop_on
    sung -= depth[idx] * np.exp(-np.maximum(since, 0) / 0.06)
    if vib:
        fade = np.clip((since - 0.15) / 0.1, 0, 1)
        sung += 50.0 * fade * np.sin(2 * np.pi * 5.5 * t)
    sos = butter(2, [1.0, 6.0], btype="band", fs=SR, output="sos")
    w = sosfiltfilt(sos, rng.standard_normal(n))
    sung += 10.0 * w / np.sqrt(np.mean(w ** 2))
    amp = np.ones(n)
    amp[t < 0.1] = 0
    amp[t > T - 0.1] = 0
    amp = np.convolve(amp, np.ones(960) / 960, mode="same")
    ok, lo, hi = contour_ok(sung, amp)
    if not ok:
        raise AssertionError(f"contour outside E2..C6: {lo:.1f} .. {hi:.1f} cents ({voice_name}, seed {seed})")
    x = voice.render(dict(sex=sex, n=n, amp=amp, noise_seed=seed + 1000), sung)
    truth = dict(notes=notes, starts=starts, durs=durs, G=G, e=e, T=T, lo=lo, hi=hi, sung=sung, amp=amp)
    return x.astype(np.float32), truth


# ------------------------------------------------------------ estimators

def settle_median(cents, t, segs):
    """Round 1's settle (infer.settle): median of 30..90 %, u = 1.2533 sd / sqrt(n_eff) (+) 1 cent."""
    return infer.settle(cents, segs)


def fit_rate(x, tt):
    """The vibrato rate: constant plus one sinusoid, least squares, best rate in RATES
    spanning at least one cycle. Returns (rate, residual sd) or None."""
    n = len(x)
    span = tt[-1] - tt[0] + HOP_S if n else 0.0
    rates = RATES[RATES * span >= 1.0]
    if len(rates) == 0 or n < 6:
        return None
    best = None
    for f in rates:
        X = np.column_stack([np.ones(n), np.sin(2 * np.pi * f * tt), np.cos(2 * np.pi * f * tt)])
        coef, _, rank, _ = np.linalg.lstsq(X, x, rcond=None)
        rss = float(np.sum((x - X @ coef) ** 2))
        if rank == 3 and (best is None or rss < best[0]):
            best = (rss, f)
    if best is None:
        return None
    return best[1], math.sqrt(best[0] / (n - 3))


def fit_centre(x, tt):
    """Q1: the mean of the pitch over the largest whole number of cycles of the
    fitted vibrato rate that the window holds, centred in it; u = sd / sqrt(n_eff)
    with sd the residual about the fitted sinusoid and n_eff round 1's (one per
    TAU), (+) the tracker. Returns (centre, u, rate, amplitude) or None when the
    window holds no whole cycle."""
    r = fit_rate(x, tt)
    if r is None:
        return None
    f, sd_r = r
    X = np.column_stack([np.ones(len(x)), np.sin(2 * np.pi * f * tt), np.cos(2 * np.pi * f * tt)])
    coef = np.linalg.lstsq(X, x, rcond=None)[0]
    amp = float(math.hypot(coef[1], coef[2]))
    span = tt[-1] - tt[0] + HOP_S
    k = int(math.floor(span * f + 1e-9))
    L = k / f
    mid = 0.5 * (tt[0] + tt[-1])
    sel = (tt >= mid - L / 2 - 1e-9) & (tt < mid + L / 2 - 1e-9)
    if sel.sum() < 3:
        return None
    n_e = max(1.0, sel.sum() * HOP_S / TAU)
    return float(np.mean(x[sel])), float(np.hypot(sd_r / math.sqrt(n_e), infer.U_TRACK)), float(f), amp


def settle_cycles(cents, t, segs):
    """Q1: each note's centre. The settle window (30..90 %, round 1's) must be at
    least VOICED_MIN voiced, else round 1's settle. Frames more than GLITCH cents
    from the window's median are dropped (f0 glitches: a real take's octave jumps
    otherwise dominate u). Where the fitted vibrato amplitude is at least A_VIB and
    the window holds a whole cycle: the mean over whole cycles (fit_centre).
    Otherwise: the median, u = 1.2533 sd / sqrt(n_eff) (+) the tracker, as round 1
    but on the kept frames.

    Iteration 31's first two forms, a free-rate sinusoid's constant and the median
    over whole cycles, failed: the first overfits one-cycle windows of real vibrato,
    the second is coarse on a sampled sinusoid (3.8 cents off). The third, the
    cycle mean on every note, took scoop tails into straight notes' centres and
    kept glitches in u; the gate and the guard are this form's changes."""
    med = infer.settle(cents, segs)
    out = []
    for (a, b), m in zip(segs, med):
        L = b - a
        lo, hi = a + int(0.3 * L), a + max(int(0.9 * L), int(0.3 * L) + 1)
        x, tt = cents[lo:hi], t[lo:hi]
        ok = ~np.isnan(x)
        if len(x) == 0 or ok.mean() < VOICED_MIN:
            out.append((m[0], m[1], m[2]))
            continue
        x, tt = x[ok], tt[ok]
        g = np.abs(x - np.median(x)) <= GLITCH
        if g.sum() < 3:
            out.append((m[0], m[1], m[2]))  # a window split between two registers
            continue
        x, tt = x[g], tt[g]
        r = fit_centre(x, tt)
        if r is not None and r[3] >= A_VIB:
            out.append((r[0], m[1], r[1]))
            continue
        n_e = max(1.0, len(x) * HOP_S / TAU)
        sd = float(np.std(x)) if len(x) > 1 else 0.0
        out.append((float(np.median(x)), m[1], float(np.hypot(1.2533 * sd / math.sqrt(n_e), infer.U_TRACK))))
    return np.array(out).reshape(-1, 3)


def infer_global(cents, t, segs, settle_fn):
    """infer.infer's global / chromatic path with a chosen settle."""
    st = settle_fn(cents, t, segs)
    s, dur, u_s = st[:, 0], st[:, 1], st[:, 2]
    r = infer.circ_mean(s, dur)
    rel = s - r
    target = np.round(rel / P)
    dev = rel - P * target
    return dict(settle=s, dur=dur, u_settle=u_s, ref=r, target=target, dev=dev)


def n_eff(w):
    w = np.asarray(w, float)
    return w.sum() ** 2 / np.sum(w ** 2)


def spread_all(dev, w, us):
    """sigma-hat and its u's: A (GUM E.4.3), B = A (+) settle rms, D = circular delta method (+) settle rms."""
    s = infer.circ_sigma(dev, w)
    n = n_eff(w)
    us_rms = float(np.sqrt(np.average(us ** 2, weights=w)))
    if not np.isfinite(s) or n <= 1:
        return dict(s=float(s), n=float(n), uA=np.nan, uB=np.nan, uD=np.nan, us=us_rms)
    a = s / np.sqrt(2 * (n - 1))
    rho = math.exp(-0.5 * (2 * math.pi * s / P) ** 2)  # corrected resultant length, as circ_sigma inverts it
    var_r = max((1 + rho ** 4) / 2 - rho ** 2, 0.0) / n
    d_samp = (P / (2 * math.pi)) * math.sqrt(var_r) / (rho * math.sqrt(max(-2 * math.log(rho), 1e-300)))
    d_samp = min(d_samp, 1e6)
    return dict(s=float(s), n=float(n), uA=float(a), uB=float(np.hypot(a, us_rms)),
                uD=float(np.hypot(d_samp, us_rms)), us=us_rms)


def circ_sigma_batch(d, w):
    """infer.circ_sigma over rows of d (sims x notes); inf where not above chance."""
    w = np.asarray(w, float)
    z = (np.exp(2j * np.pi * d / P) @ w) / w.sum()
    n = n_eff(w)
    r2 = (n * np.abs(z) ** 2 - 1) / (n - 1)
    out = np.full(len(d), np.inf)
    ok = r2 > 0
    out[ok] = P / (2 * np.pi) * np.sqrt(-np.log(np.minimum(r2[ok], 1 - 1e-12)))
    return out


def neyman(s_obs, w, us, seed, grid=GRID, m=M_SIM, level=0.95):
    """Q2 N: a central confidence interval for the singer's spread sigma, by
    inverting the simulated distribution of sigma-hat under the model
    d_i = sigma Z_i + u_i Z'_i, wrapped on the 100-cent circle, with the
    take's own duration weights and settle u's. Common random numbers across
    the grid. Upper end inf: the take cannot bound it."""
    rng = np.random.default_rng(seed)
    k = len(w)
    z1, z2 = rng.standard_normal((m, k)), rng.standard_normal((m, k))
    a = (1 - level) / 2
    q_lo, q_hi = [], []
    for sg in grid:
        sims = np.minimum(circ_sigma_batch(sg * z1 + us[None, :] * z2, w), BIG)  # inf - inf is nan in np.quantile
        q_lo.append(np.quantile(sims, a))
        q_hi.append(np.quantile(sims, 1 - a))
    q_lo, q_hi = np.array(q_lo), np.array(q_hi)
    q_hi[q_hi >= BIG] = np.inf
    q_lo[q_lo >= BIG] = np.inf
    ok = (q_hi >= s_obs) & (q_lo <= s_obs)
    if not ok.any():
        return float("nan"), float("nan")
    lo = float(grid[np.argmax(ok)])
    hi_i = len(grid) - 1 - int(np.argmax(ok[::-1]))
    hi = float("inf") if hi_i == len(grid) - 1 else float(grid[hi_i])
    return lo, hi


def ref_u_circ(dev, w):
    """Q5: the reference's standard uncertainty from the circular estimate: the
    large-sample standard error of a mean direction by the delta method,
    (P / 2 pi) sqrt((1 - R2) / (2 n R^2)), R the mean resultant length and R2
    that of the doubled angles; sigma / sqrt(n) for small spreads."""
    w = np.asarray(w, float)
    th = 2 * np.pi * np.asarray(dev) / P
    R = abs(np.sum(w * np.exp(1j * th))) / w.sum()
    R2 = abs(np.sum(w * np.exp(2j * th))) / w.sum()
    n = n_eff(w)
    if R <= 0:
        return np.inf
    return float(P / (2 * np.pi) * np.sqrt(max(1 - R2, 0.0) / (2 * n * R ** 2)))


def ref_u_round1(dev, w):
    w = np.asarray(w, float)
    return float(np.sqrt(np.sum(w * (dev - np.average(dev, weights=w)) ** 2) / w.sum()) / np.sqrt(n_eff(w)))


def dtw_T(x, p, Ts):
    """run.dtw with the transposition searched over Ts only, all Ts at once."""
    Ts = np.asarray(Ts, float)
    J = len(p)
    D = np.full((len(Ts), J), np.inf)
    D[:, 0] = np.minimum(np.abs(x[0] - p[0] - Ts), 300.0)
    for i in range(1, len(x)):
        c = np.minimum(np.abs(x[i] - p[None, :] - Ts[:, None]), 300.0)
        move = np.concatenate([np.full((len(Ts), 1), np.inf), D[:, :-1]], axis=1)
        D = c + np.minimum(D, move)
    T = float(Ts[int(np.argmin(D[:, -1]))])  # first minimum, as run.dtw's strict <
    c = np.minimum(np.abs(x[:, None] - p[None, :] - T), 300.0)
    D = np.full((len(x), J), np.inf)
    D[0, 0] = c[0, 0]
    back = np.zeros((len(x), J), np.int8)
    for i in range(1, len(x)):
        move = np.concatenate([[np.inf], D[i - 1, :-1]])
        back[i] = move < D[i - 1]
        D[i] = c[i] + np.minimum(D[i - 1], move)
    path = np.zeros(len(x), int)
    j = J - 1
    for i in range(len(x) - 1, -1, -1):
        path[i] = j
        if i > 0 and back[i, j]:
            j -= 1
    return path, T, float(np.mean(c[np.arange(len(x)), path] > 100))


def merge_repeats(notes):
    notes = np.asarray(notes)
    keep = np.concatenate([[True], np.diff(notes) != 0])
    return notes[keep], np.cumsum(keep) - 1  # states, state of each note


def align(cents, states):
    """Frames -> score state, by DTW of the 200 ms running median of voiced frames.
    Transposition: semitone steps on the take's own circular reference."""
    v = np.flatnonzero(~np.isnan(cents))
    x = infer.running_median(cents[v], 25)
    r0 = infer.circ_mean(x, np.ones(len(x)))
    Ts = r0 + P * np.arange(-45, 46)
    pth, T, bad = dtw_T(x, P * np.asarray(states, float), Ts)
    segs = []
    for j in range(len(states)):
        fr = v[pth == j]
        segs.append((int(fr.min()), int(fr.max()) + 1) if len(fr) else None)
    return segs, T, bad


def known_melody(cents, t, states, settle_fn, al=None):
    """Q4: deviations against the known notes on the singer's own tuning (a
    weighted linear mean), spread as a linear standard deviation, u = GUM
    E.4.3 (+) settle rms. No wrap: a note 60 cents off stays 60 cents off."""
    segs, T, bad = al if al is not None else align(cents, states)
    ok = [i for i, s in enumerate(segs) if s is not None and s[1] - s[0] >= 1
          and np.sum(~np.isnan(cents[s[0]:s[1]])) > 0]
    st = settle_fn(cents, t, [segs[i] for i in ok])
    keep = st[:, 1] >= TRANS_S
    c, w, us = st[keep, 0], st[keep, 1], st[keep, 2]
    dev = c - P * np.asarray(states, float)[np.array(ok)[keep]]
    dev, w, us, wrong = drop_wrong(dev, w, us)
    tun = np.average(dev, weights=w)
    d = dev - tun
    n = n_eff(w)
    if n <= 1:
        return dict(s=np.nan, n=n, uA=np.nan, uB=np.nan, states=len(states), found=int(keep.sum()), bad=bad, wrong=wrong)
    s = math.sqrt(np.average(d ** 2, weights=w) * n / (n - 1))
    a = s / math.sqrt(2 * (n - 1))
    us_rms = float(np.sqrt(np.average(us ** 2, weights=w)))
    return dict(s=float(s), n=float(n), uA=float(a), uB=float(np.hypot(a, us_rms)), us=us_rms,
                states=len(states), found=int(keep.sum()), bad=bad, wrong=wrong, tuning=float(tun), max_abs_dev=float(np.abs(d).max()))


def wmedian(x, w):
    o = np.argsort(x)
    c = np.cumsum(w[o])
    return float(x[o][np.searchsorted(c, 0.5 * c[-1])])


def drop_wrong(dev, w, us):
    """Notes more than WRONG_NOTE cents from their aim on the take's (weighted-median) tuning are wrong notes."""
    bad = np.abs(dev - wmedian(dev, w)) > WRONG_NOTE
    return dev[~bad], w[~bad], us[~bad], int(bad.sum())


def est_segments(cents):
    segs = infer.segment(cents)
    return [s for s in segs if np.sum(~np.isnan(cents[s[0]:s[1]])) > 0]


def take_measures(cents, t, segs, settle_fn, seed):
    o = infer_global(cents, t, segs, settle_fn)
    keep = o["dur"] >= TRANS_S
    if keep.sum() < 2:
        return o, keep, dict(s=np.inf, n=0.0, uA=np.nan, uB=np.nan, uD=np.nan, us=np.nan, N=(np.nan, np.nan))
    sp = spread_all(o["dev"][keep], o["dur"][keep], o["u_settle"][keep])
    sp["N"] = neyman(sp["s"], o["dur"][keep], o["u_settle"][keep], seed)
    return o, keep, sp


def halves(o, keep, seed):
    """Q3 on real takes: the take's notes split into first and second half, each measured."""
    idx = np.flatnonzero(keep)
    h = len(idx) // 2
    res = []
    for part in (idx[:h], idx[h:]):
        if len(part) < 2:
            res.append(None)
            continue
        sp = spread_all(o["dev"][part], o["dur"][part], o["u_settle"][part])
        sp["N"] = neyman(sp["s"], o["dur"][part], o["u_settle"][part], seed)
        res.append(sp)
    return res


# ------------------------------------------------------------ per-note (Q5)

def note_calls(nof, mid, segs, out, keep):
    """Per true note: the kept segment holding most of its settle-window frames (round 1's rule)."""
    sof = np.full(len(nof), -1)
    for k, (a, b) in enumerate(segs):
        if keep[k]:
            sof[a:b] = k
    calls = []
    for k in range(int(nof.max()) + 1):
        s = sof[(nof == k) & mid]
        s = s[s >= 0]
        calls.append(Counter(s.tolist()).most_common(1)[0][0] if len(s) else None)
    return calls


def per_note(nof, mid, segs, o, keep, true_notes):
    calls = note_calls(nof, mid, segs, o, keep)
    offs = [int(o["target"][c]) - int(n) for c, n in zip(calls, true_notes) if c is not None]
    modal = Counter(offs).most_common(1)[0][0] if offs else 0
    right = np.array([c is not None and int(o["target"][c]) - int(n) == modal for c, n in zip(calls, true_notes)])
    found = np.array([c is not None for c in calls])
    return calls, right, found


def p_attrib_mix(dev, sigma, pi_out):
    """Posterior that the attributed semitone is the aimed one: a wrapped normal
    of spread sigma plus a share pi_out spread evenly over the seven semitones
    considered (round 1's p_attrib at pi_out = 0)."""
    dev = np.asarray(dev, float)
    if not np.isfinite(sigma):
        return np.zeros_like(dev)
    sigma = max(sigma, 1.0)
    k = np.arange(-3, 4)
    g = np.exp(-0.5 * ((dev[:, None] + P * k[None, :]) / sigma) ** 2) / (sigma * math.sqrt(2 * math.pi))
    lik = (1 - pi_out) * g + pi_out / (7 * P)
    return lik[:, 3] / lik.sum(axis=1)


# ------------------------------------------------------------ synthetic run

def one_synth(args):
    voice_name, scale, sigma, vib, n_notes, seed = args
    x, tr = phrase(voice_name, scale, sigma, vib, n_notes, seed)
    t, cents, _ = run.track(x)
    segs = est_segments(cents)
    nof, mid = run.note_frames(t, tr["starts"], tr["durs"])
    w_true = tr["durs"]
    e = tr["e"]
    pop = float(sigma)
    realised = float(np.sqrt(np.average((e - np.average(e, weights=w_true)) ** 2, weights=w_true)))
    row = dict(voice=voice_name, scale=scale, sigma=sigma, vib=vib, n_notes=n_notes, seed=seed,
               pop=pop, realised=realised, lo=tr["lo"], hi=tr["hi"])
    for name, fn in (("med", settle_median), ("cyc", settle_cycles)):
        o, keep, sp = take_measures(cents, t, segs, fn, seed)
        row[name] = sp
        if True:  # per-note measures for both settles
            calls, right, found = per_note(nof, mid, segs, o, keep, tr["notes"])
            kd, kw = o["dev"][keep], o["dur"][keep]
            u_rc = ref_u_circ(kd, kw) if keep.sum() >= 2 else np.inf
            u_r1 = ref_u_round1(kd, kw) if keep.sum() >= 2 else np.inf
            ebar = np.average(e, weights=w_true)
            notes = []
            for k, c in enumerate(calls):
                if c is None:
                    notes.append((0, 0, np.nan, np.nan, np.nan, np.nan))
                    continue
                notes.append((1, int(right[k]), float(o["dev"][c]), float(e[k] - ebar),
                              float(o["u_settle"][c]), float(o["dur"][c])))
            row[name + "_notes"] = np.array(notes)
            row[name + "_uref"] = (u_rc, u_r1)
    # the realised truth, as for real voices: the sung contour at each frame's instant
    # (where the voice is at full level), each note's centre by settle_cycles over its
    # true boundaries, deviations from the notes on the weighted-mean tuning, weighted SD
    pos = np.clip(np.round(t * SR).astype(int), 0, len(tr["sung"]) - 1)
    tc = np.where(tr["amp"][pos] >= 0.999, tr["sung"][pos], np.nan)
    tsegs = run.oracle_from(nof)
    stc = settle_cycles(tc, t, tsegs)
    note_of = [int(nof[a]) for a, b in tsegs]
    dv = stc[:, 0] - P * tr["notes"][note_of]
    wv = stc[:, 1]
    row["realised_c"] = float(np.sqrt(np.average((dv - np.average(dv, weights=wv)) ** 2, weights=wv)))
    del tr["sung"], tr["amp"]
    states, _ = merge_repeats(tr["notes"])
    al = align(cents, states)
    row["known"] = known_melody(cents, t, states, settle_cycles, al)
    row["known_med"] = known_melody(cents, t, states, settle_median, al)
    return row


def jobs_synth():
    jobs = []
    seed = 20260927 * 10
    for n_notes, sigma, vib in itertools.product(LENGTHS, SIGMAS, (0, 1)):
        for k in range(PER_CELL):
            seed += 1
            v = run.VOICES[k % len(run.VOICES)]
            sc = run.SCALE_NAMES[(k // len(run.VOICES)) % len(run.SCALE_NAMES)]
            jobs.append((v, sc, sigma, vib, n_notes, seed))
    return jobs


def run_synth():
    jobs = jobs_synth()
    CACHE.mkdir(parents=True, exist_ok=True)
    with Pool(18) as p:
        rows = p.map(one_synth, jobs, chunksize=4)
    pickle.dump(rows, open(CACHE / "r2_synth.pkl", "wb"))
    print(len(rows), "phrases")


# ------------------------------------------------------------ real voices

def truth_per_sample(f0, n, fp_ms=1.0):
    """E-002 r2_truth.truth_per_sample (squillo-lab E-002 @ e7d2bf4), copied: E-002's
    module imports pyworld, which this experiment does not install."""
    tk = np.arange(len(f0)) * fp_ms / 1000 * SR
    ts = np.arange(n)
    f = np.interp(ts, tk, f0)
    k = np.minimum((ts / (fp_ms / 1000 * SR)).astype(int), len(f0) - 2)
    voiced = (f0[k] > 0) & (f0[k + 1] > 0)
    return np.where(voiced, f, 0.0)


def frame_truth_cents(ft, t):
    """The known f0 at each frame's instant (run.track's t: YIN's lag centre, 20 ms
    before the frame's end), matched by the frame index YIN returns (t carries it)."""
    pos = np.clip(np.round(t * SR).astype(int), 0, len(ft) - 1)
    f = ft[pos]
    c = np.full(len(f), np.nan)
    ok = (f >= 440 * 2 ** (E2_CENTS / 1200)) & (f <= 440 * 2 ** (C6_CENTS / 1200))
    c[ok] = 1200 * np.log2(f[ok] / 440.0)
    return c


def truth_spread(tc, t, states):
    """The singer's spread on the known f0: align the true pitch to the score,
    each note's centre by the same cycle fit on the true pitch (no tracker),
    deviations from the notes on the singer's weighted-mean tuning, weighted SD."""
    segs, T, bad = align(tc, states)
    ok = [i for i, s in enumerate(segs) if s is not None and s[1] - s[0] >= 1]
    st = settle_cycles(tc, t, [segs[i] for i in ok])
    stm = settle_median(tc, t, [segs[i] for i in ok])
    keep = st[:, 1] >= TRANS_S
    dev = st[keep, 0] - P * np.asarray(states, float)[np.array(ok)[keep]]
    devm = stm[keep, 0] - P * np.asarray(states, float)[np.array(ok)[keep]]
    w = st[keep, 1]
    good = np.abs(dev - wmedian(dev, w)) <= WRONG_NOTE
    goodm = np.abs(devm - wmedian(devm, w)) <= WRONG_NOTE
    d = dev[good] - np.average(dev[good], weights=w[good])
    dm = devm[goodm] - np.average(devm[goodm], weights=w[goodm])
    return dict(sd=float(np.sqrt(np.average(d ** 2, weights=w[good]))),
                sd_median_centre=float(np.sqrt(np.average(dm ** 2, weights=w[goodm]))),
                max_abs=float(np.abs(d).max()), states=len(states), found=int(keep.sum()), wrong=int((~good).sum()),
                bad=bad, T=float(T), segs=segs)


def score_of(name):
    return run.SCORES["scales" if "scales" in name else "row"]


def one_resynth(path):
    """E-002's WORLD re-synthesis of a VocalSet take (known f0): truth and measures."""
    z = np.load(path)
    y, f0 = z["y"].astype(np.float32), z["f0"]
    ft = truth_per_sample(f0, len(y))
    t, cents, _ = run.track(y)
    tc = frame_truth_cents(ft, t)
    states, _ = merge_repeats(score_of(path.stem))
    tr = truth_spread(tc, t, states)
    del tr["segs"]
    segs = est_segments(cents)
    singer = {Path(l).stem: l.split("/")[1] for l in (E002 / "data" / "vocalset-files.txt").read_text().split()}[path.stem]
    row = dict(name=path.stem, singer=singer, set="SC-straight" if "scales_straight" in path.stem else "VIB-row",
               truth=tr)
    seed = int.from_bytes(path.stem.encode()[:4].ljust(4, b"_"), "little")
    for name, fn in (("med", settle_median), ("cyc", settle_cycles)):
        o, keep, sp = take_measures(cents, t, segs, fn, seed)
        row[name] = sp
    row["known"] = known_melody(cents, t, states, settle_cycles)
    return row


def one_original(path):
    """A VocalSet original (77 takes of E-005 round 1): per-note attribution against the
    score (round 1's DTW truth), deviations with the cycle settle, halves for Q3."""
    name = path.stem
    x, sr = sf.read(path, dtype="float64")
    if x.ndim > 1:
        x = x.mean(axis=1)
    g = math.gcd(SR, sr)
    x = resample_poly(x, SR // g, sr // g)
    t, cents, _ = run.track(x.astype(np.float32))
    score = np.array(score_of(name))
    states, _ = merge_repeats(score)
    v = np.flatnonzero(~np.isnan(cents))
    pth, T, bad = run.dtw(infer.running_median(cents[v], 25), P * states)
    nof = np.full(len(cents), -1)
    nof[v] = pth
    mid = np.zeros(len(cents), bool)
    for j in range(len(states)):
        fr = v[pth == j]
        if len(fr) == 0:
            continue
        a, b = fr.min(), fr.max() + 1
        nof[a:b][nof[a:b] < 0] = j
        L = b - a
        mid[a + int(0.25 * L):a + int(0.75 * L)] = True
    mid &= nof >= 0
    segs = est_segments(cents)
    seed = sum(name.encode())
    row = dict(name=name, singer=name.split("_")[0], kind="scales" if "_scales_" in name else "row",
               style="vibrato" if "vibrato" in name else "straight", dtw_bad=bad)
    for sname, fn in (("med", settle_median), ("cyc", settle_cycles)):
        o, keep, sp = take_measures(cents, t, segs, fn, seed)
        calls, right, found = per_note(nof, mid, segs, o, keep, states)
        s_take = sp["s"]
        row[sname] = dict(sp=sp, dev=np.array([o["dev"][c] if c is not None else np.nan for c in calls]),
                          right=right, found=found, halves=halves(o, keep, seed))
        row[sname]["s_take"] = s_take
    row["known"] = known_melody(cents, t, states, settle_cycles)
    return row


def run_real():
    names = [Path(l.strip()).name for l in (HERE / "data" / "vocalset-files.txt").read_text().splitlines() if l.strip()]
    originals = [CACHE / n for n in names]
    missing = [p for p in originals if not p.exists()]
    assert not missing, missing[:3]
    r2 = sorted(p for p in (E002 / "data" / "cache" / "r2").glob("*.npz")
                if "scales_straight" in p.stem or "row_vibrato" in p.stem)
    assert len(r2) == 40, len(r2)
    with Pool(18) as p:
        orig = p.map(one_original, originals)
        res = p.map(one_resynth, r2)
    pickle.dump(dict(originals=orig, resynth=res), open(CACHE / "r2_real.pkl", "wb"))
    print(len(orig), "originals,", len(res), "re-syntheses")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "synth":
        run_synth()
    elif cmd == "real":
        run_real()
    elif cmd == "check":
        import round2_check
        round2_check.main()
    elif cmd == "report":
        import round2_report
        round2_report.main()
