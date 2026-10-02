"""E-005 round 4 (squillo iteration 71): the provisional tuning (F-040) and a
tuning fitted to a take's first seconds (F-056). Crude experiment code; adds
to round2.py and fold_refusal.py, never replaces them.

    uv run python round4.py check    # checks of the checks (S15)  -> results/round4_checks.json
    uv run python round4.py time     # S19 timing sample on the pool -> printed, written in the README
    uv run python round4.py run      # synthetic and real takes     -> data/cache/r4/*.pkl (resumes)
    uv run python round4.py report   # rules applied                 -> results/round4.json

Questions (squillo R-14 section 8, iteration 71):
  A (F-040) infer.segment quantises each voiced run against a provisional
    tuning r0, the circular mean of all voiced frames (infer.py:70-71). Under
    a vibrato of extent A cents from each note's first frame, that mean
    shrinks by J0(pi A / 50), turning negative above 38.3 cents, and notes
    split (f040_wide_vibrato.py: from +41 cents on one take). Candidates:
      P0  the present rule (the reference; must reproduce infer.segment);
      PM  the circular mean of each run's 200 ms running median, the same
          smoothing infer.segment already applies to each run (infer.py:76,
          med=25 frames);
      PL  the circular mean of each run's contour filled across its gaps and
          low-passed at 2 Hz, order-2 Butterworth forward and backward, MT-009's
          contour (E-002 fold2.py:124-126, read from the code; at the frame
          rate 125 Hz; a run too short for filtfilt's padding, 9 frames, gives
          its median).
  B (F-056) a tuning fitted to the take's first t seconds and then frozen: the
    same pipeline (provisional tuning, segments, settle_cycles, the circular
    mean of note centres weighted by duration, notes of at least 0.1 s) on the
    frames whose instant is at most t, against the whole take's tuning; its
    own standard uncertainty u_e = ref_u_circ (+) rms settle u / sqrt(n_eff).

Conditions, written before generating (S15):
  - Synthetic phrases: round2.phrase's generator (round2.py:119-160), copied as
    phrase4 with the vibrato's extent and onset as parameters; everything else
    read from that code: notes inside the voice's range, tuning G uniform in
    +-50 cents, per-note error normal of sd sigma, scoops on half the notes
    (30-100 cents, 60 ms), a 1-6 Hz wobble of rms 10 cents, 5.5 Hz vibrato.
    Round 2's vibrato fades in from 0.15 to 0.25 s after each onset
    (round2.py:146); "onset" here means full extent from each note's first
    sample (fade = 1).
  - Vibrato conditions: none; 40, 50, 60 cents from the onset; 50 cents faded
    in (round 2's own). Extent is the sinusoid's amplitude, E-002's definition
    (r2_analyse.py:197: sqrt 2 x rms of the band-passed contour). Real extents
    span p5 6.0 to p95 110.5 cents pooled over blocks (E-002 result 21); 60 is
    inside it and is the widest whose contour stays in E2..C6 under round 2's
    melody floor with sigma <= 20 (asserted on every phrase by contour_ok).
  - sigma in {0, 10, 20} cents; 14 and 28 notes; PER_CELL phrases per cell,
    round 2's voices and scales in turn, new seeds.
  - phrase4 asserts on its own output: the contour inside E2..C6 (round 2's
    contour_ok), and the vibrato it added (the contour minus the same phrase
    rendered with no vibrato) within +-A everywhere, and for "onset" reaching
    at least 0.99 A within the first vibrato cycle (1 / 5.5 s) of every note;
    for "fade" exactly 0 in every note's first 0.15 s.
  - Real takes: round 2's 40 E-002 WORLD re-syntheses (20 straight scales, 20
    vibrato rows; known f0) and its 77 VocalSet originals, tracked with
    MT-003's refusal (fold_refusal.track).
  - B: t in T_GRID seconds after the take's first sample; a take enters a t
    only when it is longer than t + 1 s.

Rules and bars, written and committed before any run:
  A1 honesty: a candidate's MT-007 statement (U25, k = 2, the population sigma
     as truth, fold_refusal.miss) misses in at most BAR % of the phrases of
     every synthetic cell, or in no more phrases than P0's in that cell.
  A2 informative: over the "onset" cells at 50 and 60 cents (both above
     38.3), the candidate gives more takes in the state measured than P0, by
     the exact McNemar test on the paired takes, two-sided p < 0.05.
  A3 no harm: on the cells without vibrato, the candidate gives fewer takes
     measured than P0 in no cell by McNemar p < 0.05; and on the 40
     re-syntheses (truth: round 2's truth_spread sd on the known f0) it
     misses no more takes than P0.
  A candidate passing A1-A3 replaces P0; if both pass, the one with more
  takes measured over A2's cells; a tie goes to PM (infer.segment already
  computes it). None passing: P0 stays and F-040 says why.
  B1 for each rule kept (P0, and the A winner if any), the settling time t* is
     the smallest t in T_GRID at which, in every synthetic cell with at least
     MIN_B takes entering t, and on the re-syntheses and on the originals,
     |wrap(r_t - r_whole)| <= 2 u_e in at least 100 - BAR % of the takes that
     have a tuning at t (at least two notes kept). Recorded beside it: the
     share of takes with a tuning at t, and the median and p95 of 2 u_e and of
     |wrap(r_t - r_whole)| in cents. No t passing: none settles within 6 s.
"""

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import itertools
import json
import math
import pickle
import subprocess
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from scipy.signal import butter, filtfilt, sosfiltfilt
from scipy.stats import binomtest

import run  # before synth (round2's note)
import infer
import round2 as R2
import fold_refusal as FR

HERE = Path(__file__).parent
OUT = HERE / "results"
CACHE = HERE / "data" / "cache" / "r4"
SR, HOP = 48_000, 384
FR_HZ = SR / HOP  # 125 frames per second
P = 100.0
BAR = FR.BAR  # 5 per cent
UPPER = FR.UPPER  # 25 cents, MT-007
VIBS = (("none", 0.0), ("onset", 40.0), ("onset", 50.0), ("onset", 60.0), ("fade", 50.0))
SIGMAS = (0, 10, 20)
LENGTHS = (14, 28)
PER_CELL = 100
T_GRID = (1.0, 2.0, 3.0, 4.0, 6.0)
MIN_B = 20
RULES = ("P0", "PM", "PL")
LP = butter(2, 2.0, "low", fs=FR_HZ)  # MT-009's contour filter (E-002 fold2.py:124-126)
VIB_RATE = 5.5  # round2.py:146
HALF_MARGIN = P / 4  # cents: half of the 50 cents segment_r leaves between a correct tuning's notes and a cut


def committed_first():
    """S15: refuse to run on an uncommitted edit of this file, or before it is committed."""
    me = Path(__file__).name
    a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
    b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", me], cwd=HERE)
    if a.returncode or b.returncode:
        sys.exit(f"{me} is not committed as it stands: commit the rules before running")


def wrap(x):
    return (np.asarray(x, float) + P / 2) % P - P / 2


# ------------------------------------------------------------ inputs

def contour4(voice_name, scale, sigma, ext, onset, n_notes, seed):
    """round2.phrase's contour (round2.py:119-160) with the vibrato's extent and onset
    as parameters. onset: 'fade' (round 2's), 'onset' (full from each note's first
    sample) or 'none'. Returns (sung, amp, truth, vib_added)."""
    import voice  # round2.phrase's import; synth puts E-001 on the path
    sex, base = voice.VOICES[voice_name]
    rng = np.random.default_rng(seed)
    for _ in range(100):
        m = R2.melody(scale, base, rng, n_notes)
        if m is not None:
            break
    notes, durs = m
    assert notes.max() <= min(12, base + 17) and notes.min() >= -25
    starts = np.concatenate([[0.0], np.cumsum(durs)[:-1]]) + 0.1
    T = starts[-1] + durs[-1] + 0.1
    n = int(round(T * SR))
    t = np.arange(n) / SR
    G = rng.uniform(-50, 50)
    e = rng.normal(0, sigma, len(notes))
    sung = R2.synth.contour(100.0 * notes + e, starts, n) + G
    idx = np.clip(np.searchsorted(starts, t, "right") - 1, 0, None)
    since = t - starts[idx]
    scoop_on = rng.random(len(notes)) < 0.5
    depth = rng.uniform(30, 100, len(notes)) * scoop_on
    sung -= depth[idx] * np.exp(-np.maximum(since, 0) / 0.06)
    if onset == "fade":
        fade = np.clip((since - 0.15) / 0.1, 0, 1)
    elif onset == "onset":
        fade = np.ones(n)
    else:
        fade = np.zeros(n)
    vib = ext * fade * np.sin(2 * np.pi * VIB_RATE * t)
    sung = sung + vib
    sos = butter(2, [1.0, 6.0], btype="band", fs=SR, output="sos")
    w = sosfiltfilt(sos, rng.standard_normal(n))
    sung += 10.0 * w / np.sqrt(np.mean(w ** 2))
    amp = np.ones(n)
    amp[t < 0.1] = 0
    amp[t > T - 0.1] = 0
    amp = np.convolve(amp, np.ones(960) / 960, mode="same")
    truth = dict(notes=notes, starts=starts, durs=durs, G=G, e=e, T=T, sex=sex)
    return sung, amp, truth, vib


def assert_vib(vib, truth, ext, onset):
    """S15 on the output: the vibrato added is within +-ext, and its onset is what it is called."""
    assert np.abs(vib).max() <= ext + 1e-9, (np.abs(vib).max(), ext)
    for s in truth["starts"]:
        a = int(math.ceil(s * SR)) + 1  # revision 1: the generator's searchsorted gives a sample at
        # t just below s to the note before; the first sample past the start belongs to the note
        if onset == "onset":
            first = np.abs(vib[a:a + int(SR / VIB_RATE) + 1]).max()
            assert first >= 0.99 * ext, (first, ext)
        elif onset == "fade":
            assert np.abs(vib[a:a + int(0.15 * SR) - 1]).max() == 0.0
        else:
            assert np.abs(vib).max() == 0.0


def phrase4(voice_name, scale, sigma, ext, onset, n_notes, seed):
    sung, amp, tr, vib = contour4(voice_name, scale, sigma, ext, onset, n_notes, seed)
    ok, lo, hi = R2.contour_ok(sung, amp)
    assert ok, f"contour outside E2..C6: {lo:.1f} .. {hi:.1f} ({voice_name}, seed {seed})"
    assert_vib(vib, tr, ext, onset)
    import voice
    x = voice.render(dict(sex=tr["sex"], n=len(sung), amp=amp, noise_seed=seed + 1000), sung)
    tr.update(lo=lo, hi=hi)
    return x.astype(np.float32), tr


# ------------------------------------------------------------ provisional tunings and segments

def runs_of(cents, gap=3):
    """infer.segment's bridged voiced runs (infer.py:44-67)."""
    v = ~np.isnan(cents)
    n = len(cents)
    vb = v.copy()
    i = 0
    while i < n:
        if not v[i]:
            j = i
            while j < n and not v[j]:
                j += 1
            if 0 < i and j < n and j - i <= gap:
                vb[i:j] = True
            i = j
        else:
            i += 1
    runs, i = [], 0
    while i < n:
        if vb[i]:
            j = i
            while j < n and vb[j]:
                j += 1
            runs.append((i, j))
            i = j
        else:
            i += 1
    return runs


def filled(x):
    x = x.copy()
    good = ~np.isnan(x)
    if not good.any():
        return None
    x[~good] = np.interp(np.flatnonzero(~good), np.flatnonzero(good), x[good])
    return x


def provisional(cents, rule):
    ok = cents[~np.isnan(cents)]
    if len(ok) == 0:
        return None
    if rule == "P0":
        return float(infer.circ_mean(ok, np.ones(len(ok))))
    parts = []
    for a, b in runs_of(cents):
        x = filled(cents[a:b])
        if x is None:
            continue
        if rule == "PM":
            parts.append(infer.running_median(x, min(25, (b - a) | 1)))
        elif len(x) > 9:
            parts.append(filtfilt(*LP, x))
        else:
            parts.append(np.full(len(x), np.median(x)))
    c = np.concatenate(parts)
    return float(infer.circ_mean(c, np.ones(len(c))))


def segment_r(cents, r0, min_frames=8, med=25, gap=3):
    """infer.segment (infer.py:41-110) with its provisional tuning r0 given."""
    segs = []
    for a, b in runs_of(cents, gap):
        if b - a < min_frames:
            continue
        x = filled(cents[a:b])
        sm = infer.running_median(x, min(med, (b - a) | 1))
        q = np.round((sm - r0) / 100.0)
        cuts = [0] + [k for k in range(1, len(q)) if q[k] != q[k - 1]] + [len(q)]
        parts = [[cuts[k], cuts[k + 1], q[cuts[k]]] for k in range(len(cuts) - 1)]
        merged = True
        while merged and len(parts) > 1:
            merged = False
            lens = [p[1] - p[0] for p in parts]
            k = int(np.argmin(lens))
            if lens[k] >= min_frames:
                break
            if k == 0:
                nb = 1
            elif k == len(parts) - 1:
                nb = k - 1
            else:
                nb = k - 1 if abs(parts[k - 1][2] - parts[k][2]) <= abs(parts[k + 1][2] - parts[k][2]) else k + 1
            lo, hi = min(k, nb), max(k, nb)
            parts[lo] = [parts[lo][0], parts[hi][1], parts[nb][2]]
            del parts[hi]
            merged = True
            m = 0
            while m < len(parts) - 1:
                if parts[m][2] == parts[m + 1][2]:
                    parts[m] = [parts[m][0], parts[m + 1][1], parts[m][2]]
                    del parts[m + 1]
                else:
                    m += 1
        segs += [(a + p[0], a + p[1]) for p in parts if p[1] - p[0] >= 1]
    return [s for s in segs if np.sum(~np.isnan(cents[s[0]:s[1]])) > 0]  # round2.est_segments


def measure(cents, t, rule):
    """MT-006/MT-007 on a take, segmenting with the rule's provisional tuning. Returns
    (spread dict, tuning dict or None, n segments, r0)."""
    r0 = provisional(cents, rule)
    if r0 is None:
        return dict(s=np.inf, uB=np.nan), None, 0, None
    segs = segment_r(cents, r0)
    if not segs:
        return dict(s=np.inf, uB=np.nan), None, 0, r0
    o = R2.infer_global(cents, t, segs, R2.settle_cycles)
    keep = o["dur"] >= R2.TRANS_S
    if keep.sum() < 2:
        return dict(s=np.inf, uB=np.nan), None, len(segs), r0
    sp = R2.spread_all(o["dev"][keep], o["dur"][keep], o["u_settle"][keep])
    d, w, us = o["dev"][keep], o["dur"][keep], o["u_settle"][keep]
    us_rms = float(np.sqrt(np.average(us ** 2, weights=w)))
    u_e = float(np.hypot(R2.ref_u_circ(d, w), us_rms / math.sqrt(R2.n_eff(w))))
    return sp, dict(r=float(o["ref"]), u=u_e, n=int(keep.sum())), len(segs), r0


def take_rows(t, cents, T_take):
    out = {}
    for rule in RULES:
        sp, tun, nseg, r0 = measure(cents, t, rule)
        row = dict(s=float(sp["s"]), uB=float(sp["uB"]), state=FR.state(sp), nseg=nseg, r0=r0,
                   r=tun["r"] if tun else None, u=tun["u"] if tun else None)
        early = {}
        for tc in T_GRID:
            if T_take <= tc + 1.0:
                continue
            k = int(np.searchsorted(t, tc, "right"))
            _, te, _, _ = measure(cents[:k], t[:k], rule)
            early[tc] = None if te is None else dict(r=te["r"], u=te["u"], n=te["n"])
        row["early"] = early
        out[rule] = row
    return out


# ------------------------------------------------------------ runs

def one_synth(args):
    voice_name, scale, sigma, vname, ext, n_notes, seed = args
    x, tr = phrase4(voice_name, scale, sigma, ext, vname, n_notes, seed)
    t, cents, _, nref = FR.track(x)
    assert segment_r(cents, provisional(cents, "P0")) == R2.est_segments(cents)  # P0 is infer.segment
    row = dict(kind="synth", voice=voice_name, scale=scale, sigma=sigma, vib=vname, ext=ext,
               n_notes=n_notes, seed=seed, G=float(tr["G"]), T=float(tr["T"]), lo=tr["lo"], hi=tr["hi"])
    row["rules"] = take_rows(t, cents, float(tr["T"]))
    return row


def one_real(args):
    kind, path = args
    import soundfile as sf
    from scipy.signal import resample_poly
    path = Path(path)
    if kind == "resynth":
        z = np.load(path)
        x = z["y"].astype(np.float32)
    else:
        x, sr = sf.read(path, dtype="float64")
        if x.ndim > 1:
            x = x.mean(axis=1)
        g = math.gcd(SR, sr)
        x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    t, cents, _, nref = FR.track(x)
    assert segment_r(cents, provisional(cents, "P0")) == R2.est_segments(cents)
    states, _ = R2.merge_repeats(R2.score_of(path.stem))
    row = dict(kind=kind, name=path.stem, T=len(x) / SR, states=len(states),
               set=("straight" if "straight" in path.stem else "vibrato"))
    if kind == "resynth":
        ft = R2.truth_per_sample(z["f0"], len(x))
        tc = R2.frame_truth_cents(ft, t)
        tr = R2.truth_spread(tc, t, states)
        row["truth_sd"] = tr["sd"]
    row["rules"] = take_rows(t, cents, len(x) / SR)
    return row


def jobs_synth():
    jobs, seed = [], 20261002 * 10
    for n_notes, sigma, (vname, ext) in itertools.product(LENGTHS, SIGMAS, VIBS):
        for k in range(PER_CELL):
            seed += 1
            v = run.VOICES[k % len(run.VOICES)]
            sc = run.SCALE_NAMES[(k // len(run.VOICES)) % len(run.SCALE_NAMES)]
            jobs.append((v, sc, sigma, vname, ext, n_notes, seed))
    return jobs


def jobs_real():
    names = [Path(l.strip()).name for l in (HERE / "data" / "vocalset-files.txt").read_text().splitlines() if l.strip()]
    originals = [("original", str(R2.CACHE / n)) for n in names]
    assert len(originals) == 77 and all(Path(p).exists() for _, p in originals)
    r2 = sorted(p for p in (R2.E002 / "data" / "cache" / "r2").glob("*.npz")
                if "scales_straight" in p.stem or "row_vibrato" in p.stem)
    assert len(r2) == 40, len(r2)
    return originals + [("resynth", str(q)) for q in r2]


def run_all(procs=18):
    committed_first()
    CACHE.mkdir(parents=True, exist_ok=True)
    js, jr = jobs_synth(), jobs_real()
    chunks = [("real", jr)] + [(f"synth{i:02d}", js[i:i + 300]) for i in range(0, len(js), 300)]
    with Pool(procs) as p:
        for name, jobs in chunks:
            f = CACHE / f"{name}.pkl"
            if f.exists():
                continue  # resume
            t0 = time.time()
            rows = p.map(one_real if name == "real" else one_synth, jobs, chunksize=2)
            pickle.dump(rows, open(f, "wb"))
            print(name, len(rows), f"{time.time() - t0:.0f} s", flush=True)


def time_sample(procs=18):
    """S19: every extreme condition (60 cents onset, 28 notes, sigma 20; no vibrato, 14 notes) and
    the real takes' longest, on the pool at its process count."""
    committed_first()
    js = jobs_synth()
    pick = [j for j in js if j[5] == 28 and j[4] == 60.0 and j[2] == 20][:procs // 2] + \
           [j for j in js if j[5] == 14 and j[3] == "none" and j[2] == 0][:procs // 2]
    t0 = time.time()
    with Pool(procs) as p:
        p.map(one_synth, pick, chunksize=1)
    ts = time.time() - t0
    jr = jobs_real()
    t0 = time.time()
    with Pool(procs) as p:
        p.map(one_real, jr[:procs], chunksize=1)
    tr = time.time() - t0
    n_s, n_r = len(js), len(jr)
    est = ts / len(pick) * n_s + tr / procs * n_r
    print(f"synthetic: {len(pick)} in {ts:.1f} s on {procs}; real: {procs} in {tr:.1f} s; "
          f"estimate for {n_s} + {n_r}: {est:.0f} s")


# ------------------------------------------------------------ checks (S15)

def covered(r_t, r_whole, u_e):
    return bool(abs(float(wrap(r_t - r_whole))) <= 2 * u_e)


def mcnemar(a, b):
    """Exact McNemar on paired booleans: (b better count, a better count, p two-sided)."""
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    nb, na = int(np.sum(b & ~a)), int(np.sum(a & ~b))
    if na + nb == 0:
        return nb, na, 1.0
    return nb, na, float(binomtest(nb, na + nb, 0.5).pvalue)


def check():
    committed_first()
    out = {}
    # 1. contour4 reproduces round2.phrase's contour: rendering both with round 2's arguments
    #    gives identical samples (must pass, 'fade' 50 = vib 1, 'none' = vib 0); 'onset' 50
    #    against round 2's vib 1 must differ (must fail).
    c1 = {}
    for vname, ext, vib in (("fade", 50.0, 1), ("none", 0.0, 0), ("onset", 50.0, 1)):
        x4, _ = phrase4("tenor", "major", 10, ext, vname, 14, 4242)
        x2, _ = R2.phrase("tenor", "major", 10, vib, 14, 4242)
        c1[vname] = bool(len(x4) == len(x2) and np.array_equal(x4, x2))
    out["c1_phrase4_is_round2"] = dict(must_pass_fade=c1["fade"], must_pass_none=c1["none"],
                                       must_fail_onset_differs=not c1["onset"])
    # 2. assert_vib refuses a take that is not what it is called: a 'fade' take called 'onset',
    #    an 'onset' take called 'fade', and a 60-cent take called 40 (must fail); passes as called.
    fails = {}
    s60, a60, tr60, v60 = contour4("tenor", "major", 10, 60.0, "onset", 14, 7)
    sf_, af_, trf, vf = contour4("tenor", "major", 10, 50.0, "fade", 14, 7)
    for name, args in (("fade_called_onset", (vf, trf, 50.0, "onset")),
                       ("onset_called_fade", (v60, tr60, 60.0, "fade")),
                       ("ext60_called_40", (v60, tr60, 40.0, "onset"))):
        try:
            assert_vib(*args)
            fails[name] = False
        except AssertionError:
            fails[name] = True
    passes = {}
    for name, args in (("onset_60", (v60, tr60, 60.0, "onset")), ("fade_50", (vf, trf, 50.0, "fade"))):
        try:
            assert_vib(*args)
            passes[name] = True
        except AssertionError:
            passes[name] = False
    out["c2_assert_vib"] = dict(must_fail=fails, must_pass=passes)
    # 3. segment_r with P0's tuning is infer.segment (must pass, on phrases of every vibrato
    #    condition). On a frame contour of 14 notes on a tuning of 23 cents, each 100 frames
    #    with a 1 Hz wobble of +-5 cents (it crosses its centre within each note, at least 62
    #    frames from either end), segment_r given 23 finds 14 segments (must pass) and given
    #    73, which puts every centre on the quantiser's boundary, more than 14 (must fail).
    same = []
    for vname, ext in VIBS:
        x, _ = phrase4("baritone", "minor", 10, ext, vname, 14, 99)
        t, c, _, _ = FR.track(x)
        same.append(segment_r(c, provisional(c, "P0")) == R2.est_segments(c))
    k = np.arange(100) / FR_HZ
    wob = [100 * m + 23.0 + 5.0 * np.sin(2 * np.pi * 1.0 * k) for m in FR.MELODY]
    cw = np.concatenate([np.concatenate([s_, np.full(12, np.nan)]) for s_ in wob])
    n_own, n_off = len(segment_r(cw, 23.0)), len(segment_r(cw, 73.0))
    out["c3_segment_r"] = dict(must_pass_equal_infer_segment=all(same), must_pass_14_on_own_tuning=n_own == 14,
                               must_fail_on_boundary_not_14=n_off != 14, n_own=n_own, n_off=n_off)
    # 4. the candidates' smoothing: on a frame contour of 14 notes at known centres
    #    (tuning 23 cents), each held 100 frames with a 5.5 Hz vibrato of 50 cents from its
    #    first frame, PM and PL lie within HALF_MARGIN of 23 (must pass), and P0 lies further
    #    (must fail), as its mean J0(pi) = -0.30 of the notes' gives by definition (the mean
    #    of exp(i a sin) over whole cycles is J0(a)). Revision 2: the bound was 2 cents, with
    #    no source, and PM failed it (2.21); HALF_MARGIN is the quantiser's own: segment_r
    #    cuts at 50 cents from the tuning it is given, so a tuning within 25 cents of the
    #    notes' keeps every centre at least half a correct tuning's margin from a cut.
    k = np.arange(100) / FR_HZ
    seg = [100 * m + 23.0 + 50.0 * np.sin(2 * np.pi * VIB_RATE * k) for m in FR.MELODY]
    cc = np.concatenate([np.concatenate([s_, np.full(12, np.nan)]) for s_ in seg])
    d = {r: abs(float(wrap(provisional(cc, r) - 23.0))) for r in RULES}
    from scipy.special import j0
    out["c4_provisional"] = dict(must_pass_PM=d["PM"] <= HALF_MARGIN, must_pass_PL=d["PL"] <= HALF_MARGIN,
                                 must_fail_P0=d["P0"] > HALF_MARGIN, dist=d, j0_pi=float(j0(math.pi)),
                                 half_margin=HALF_MARGIN, first_bound_2_cents_PM_failed=d["PM"] > 2.0)
    # 5. B's coverage test: Delta 0 covered (must pass); a whole-take tuning 2u_e + 0.01 away
    #    not covered (must fail); the wrap: 99 and -1 cents are the same tuning (must pass).
    out["c5_covered"] = dict(must_pass_zero=covered(10.0, 10.0, 1.0),
                             must_fail_beyond=not covered(10.0, 12.01, 1.0),
                             must_pass_wrap=covered(49.5, -49.5, 0.5))
    # 6. McNemar: 10 of 10 discordant one way gives p < 0.05 (must pass); 5 and 5 does not (must fail).
    out["c6_mcnemar"] = dict(must_pass_ten=mcnemar([False] * 10, [True] * 10)[2] < 0.05,
                             must_fail_balanced=not (mcnemar([False] * 5 + [True] * 5, [True] * 5 + [False] * 5)[2] < 0.05))
    (OUT / "round4_checks.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    for key in ("must_pass_fade", "must_pass_none", "must_fail_onset_differs"):
        assert out["c1_phrase4_is_round2"][key], key
    for key in ("must_fail", "must_pass"):
        assert all(out["c2_assert_vib"][key].values()), key
    for key in ("must_pass_equal_infer_segment", "must_pass_14_on_own_tuning", "must_fail_on_boundary_not_14"):
        assert out["c3_segment_r"][key], key
    for key in ("must_pass_PM", "must_pass_PL", "must_fail_P0"):
        assert out["c4_provisional"][key], key
    for key in ("must_pass_zero", "must_fail_beyond", "must_pass_wrap"):
        assert out["c5_covered"][key], key
    for key in ("must_pass_ten", "must_fail_balanced"):
        assert out["c6_mcnemar"][key], key


# ------------------------------------------------------------ report

def load():
    rows = []
    for f in sorted(CACHE.glob("*.pkl")):
        rows += pickle.load(open(f, "rb"))
    return rows


def wilson(k, n):
    return FR.wilson(k, n)


def report():
    committed_first()
    rows = load()
    syn = [r for r in rows if r["kind"] == "synth"]
    rs = [r for r in rows if r["kind"] == "resynth"]
    og = [r for r in rows if r["kind"] == "original"]
    assert len(syn) == len(jobs_synth()) and len(rs) == 40 and len(og) == 77, (len(syn), len(rs), len(og))
    cells = {}
    for r in syn:
        cells.setdefault((r["n_notes"], r["sigma"], r["vib"], r["ext"]), []).append(r)
    res = dict(conditions=dict(per_cell=PER_CELL, sigmas=SIGMAS, lengths=LENGTHS, vibs=VIBS, t_grid=T_GRID,
                               bar_pct=BAR, upper=UPPER), cells={}, real={})
    # A: per cell, per rule
    for key, rr in sorted(cells.items()):
        name = f"L={key[0]} sigma={key[1]} {key[2]} {key[3]:g}"
        d = {}
        for rule in RULES:
            st = [x["rules"][rule]["state"] for x in rr]
            mis = [x["rules"][rule]["state"] != "uncertain" and FR.miss(
                dict(s=x["rules"][rule]["s"], uB=x["rules"][rule]["uB"]), float(x["sigma"])) for x in rr]
            nseg = [x["rules"][rule]["nseg"] for x in rr]
            r0e = [abs(float(wrap(x["rules"][rule]["r0"] - x["G"]))) for x in rr if x["rules"][rule]["r0"] is not None]
            d[rule] = dict(measured=wilson(sum(s == "measured" for s in st), len(st)),
                           at_least=wilson(sum(s == "at least" for s in st), len(st)),
                           uncertain=wilson(sum(s == "uncertain" for s in st), len(st)),
                           miss=wilson(sum(mis), len(mis)), miss_k=int(sum(mis)),
                           segments_equal_notes=wilson(sum(n == key[0] for n in nseg), len(nseg)),
                           segments_median=float(np.median(nseg)),
                           provisional_err_median=float(np.median(r0e)), provisional_err_p95=float(np.percentile(r0e, 95)))
        res["cells"][name] = d
    # A1
    a1 = {}
    for rule in ("PM", "PL"):
        bad = [n for n, d in res["cells"].items()
               if d[rule]["miss"][0] is not None and d[rule]["miss"][0] > BAR and d[rule]["miss_k"] > d["P0"]["miss_k"]]
        a1[rule] = dict(pass_=not bad, failing_cells=bad)
    # A2, A3
    on = [r for r in syn if r["vib"] == "onset" and r["ext"] >= 50]
    a2, a3 = {}, {}
    for rule in ("PM", "PL"):
        m0 = [r["rules"]["P0"]["state"] == "measured" for r in on]
        m1 = [r["rules"][rule]["state"] == "measured" for r in on]
        nb, na, p = mcnemar(m0, m1)
        a2[rule] = dict(more=nb, fewer=na, p=p, measured_P0=int(sum(m0)), measured=int(sum(m1)), n=len(on),
                        pass_=bool(nb > na and p < 0.05))
        worse = []
        for key, rr in cells.items():
            if key[2] != "none":
                continue
            nb2, na2, p2 = mcnemar([r["rules"]["P0"]["state"] == "measured" for r in rr],
                                   [r["rules"][rule]["state"] == "measured" for r in rr])
            if na2 > nb2 and p2 < 0.05:
                worse.append(f"L={key[0]} sigma={key[1]}")
        mr = {q: sum(r["rules"][q]["state"] != "uncertain" and FR.miss(
            dict(s=r["rules"][q]["s"], uB=r["rules"][q]["uB"]), r["truth_sd"]) for r in rs) for q in ("P0", rule)}
        a3[rule] = dict(worse_straight_cells=worse, resynth_miss_P0=mr["P0"], resynth_miss=mr[rule],
                        pass_=bool(not worse and mr[rule] <= mr["P0"]))
    passing = [q for q in ("PM", "PL") if a1[q]["pass_"] and a2[q]["pass_"] and a3[q]["pass_"]]
    if len(passing) == 2:
        win = "PL" if a2["PL"]["measured"] > a2["PM"]["measured"] else "PM"
    else:
        win = passing[0] if passing else "P0"
    res["A"] = dict(A1=a1, A2=a2, A3=a3, passing=passing, winner=win)
    # real takes, A as reported
    for kind, rr in (("resynth", rs), ("original", og)):
        for sset in ("straight", "vibrato"):
            q = [r for r in rr if r["set"] == sset]
            d = {}
            for rule in RULES:
                st = [x["rules"][rule]["state"] for x in q]
                d[rule] = dict(n=len(q), measured=sum(s == "measured" for s in st),
                               at_least=sum(s == "at least" for s in st), uncertain=sum(s == "uncertain" for s in st),
                               segments_over_states_median=float(np.median([x["rules"][rule]["nseg"] / x["states"] for x in q])))
                if kind == "resynth":
                    d[rule]["miss"] = sum(x["rules"][rule]["state"] != "uncertain" and FR.miss(
                        dict(s=x["rules"][rule]["s"], uB=x["rules"][rule]["uB"]), x["truth_sd"]) for x in q)
            res["real"][f"{kind} {sset}"] = d
    # B
    groups = {f"L={k[0]} sigma={k[1]} {k[2]} {k[3]:g}": v for k, v in cells.items()}
    groups["resynth"], groups["original"] = rs, og
    res["B"] = {}
    for rule in sorted({"P0", win}):
        tab, tstar = {}, None
        for tc in T_GRID:
            row, ok_all = {}, True
            for g, rr in groups.items():
                ent = [r for r in rr if tc in r["rules"][rule]["early"] and r["rules"][rule]["r"] is not None]
                have = [r for r in ent if r["rules"][rule]["early"][tc] is not None]
                cov = [covered(r["rules"][rule]["early"][tc]["r"], r["rules"][rule]["r"], r["rules"][rule]["early"][tc]["u"])
                       for r in have]
                dist = [abs(float(wrap(r["rules"][rule]["early"][tc]["r"] - r["rules"][rule]["r"]))) for r in have]
                U = [2 * r["rules"][rule]["early"][tc]["u"] for r in have]
                miss = wilson(len(cov) - sum(cov), len(cov))
                judged = len(ent) >= MIN_B or g in ("resynth", "original")
                if judged and have and miss[0] > BAR:
                    ok_all = False
                row[g] = dict(entered=len(ent), with_tuning=len(have), miss=miss, judged=judged,
                              dist_median=float(np.median(dist)) if dist else None,
                              dist_p95=float(np.percentile(dist, 95)) if dist else None,
                              U_median=float(np.median(U)) if U else None, U_p95=float(np.percentile(U, 95)) if U else None)
            tab[str(tc)] = dict(groups=row, all_pass=ok_all)
            if ok_all and tstar is None:
                tstar = tc
        res["B"][rule] = dict(t_star=tstar, by_t=tab)
    (OUT / "round4.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(dict(A=res["A"], t_star={k: v["t_star"] for k, v in res["B"].items()}), indent=1, default=float))


if __name__ == "__main__":
    cmd = sys.argv[1]
    {"check": check, "time": time_sample, "run": run_all, "report": report}[cmd]()
