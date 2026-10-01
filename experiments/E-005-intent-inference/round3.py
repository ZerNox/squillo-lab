"""E-005 round 3 (squillo iteration 59, squillo F-045 and F-041's first case):
each note's centre and aim, with an honest +-, and the rung that centres it.

Crude experiment code. Rounds 1 and 2 and the folds stay unchanged; this file
adds, never replaces. It imports round 2's generator pieces and estimators
and fold 2's refusal (squillo MT-003).

    uv run python round3.py check          # the checks, each checked (S15) -> results/round3_checks.json
    uv run python round3.py time 36 18     # S19: a sample spread over the conditions, on the pool
    uv run python round3.py synth 18       # 1680 phrases -> data/cache/r3_synth.pkl (resumes)
    uv run python round3.py real           # 40 E-002 re-syntheses, 77 VocalSet originals -> data/cache/r3_real.pkl
    uv run python round3.py select         # the two selections, fit half only -> results/round3_select.json
    uv run python round3.py rungs 18       # H3 on the held-out half and real takes -> data/cache/r3_rungs.pkl
    uv run python round3.py report         # -> results/round3.json
    uv run python round3.py posthoc 18     # revision 2, after the report: labelled diagnostics -> results/round3_posthoc.json

Why (squillo F-045): only `steadiness` has a ladder, so a take with no held
note has no far vision. The rung that would serve every take moves each
note's centre towards the note it aimed at. That needs, per note, a centre
with an honest +- and an aim that is right, or a gate that keeps a wrong aim
from moving the singer towards a wrong note. A library phrase's written
notes are the first case (squillo F-041): there the aim is known.

Measurand, per note: the note's realised centre minus its aim on the
singer's own realised tuning, delta = C - A. C is round 2's centre rule
(`settle_cycles`: the median of 30..90 % of the note, or the mean over whole
vibrato cycles where the fitted vibrato is at least 25 cents) applied to the
sung contour itself over the note's true boundaries, as round 2's realised
truth (`round2.one_synth`, `realised_c`). A = 100 n + tau, n the written
note and tau the duration-weighted linear mean of C - 100 n over the take's
notes: the singer's own tuning, not A4 = 440 Hz. A global sharpness of the
whole take is the singer's tuning and is invisible (round 1). For the real
re-syntheses the true boundaries are the known f0 aligned to the score,
round 2's truth procedure (`round2.truth_spread`).

Two paths, each estimating d (the estimate of delta) for every note it keeps:
  free   reference-free, for any song: round 2's segmentation, centre and
         global circular tuning r, the aim the nearest semitone on r
         (`round2.infer_global`), MT-003's refusal on. The note's estimated
         aim is r + 100 k in absolute cents; it is *right* when it lies
         within 50 cents of A (both are absolute cents re A4).
  known  the written melody (repeats merged to states), aligned by round 2's
         DTW (`round2.align`), centres by `settle_cycles`, deviations from
         100 n on the weighted linear tuning, a state more than 150 cents
         from its aim on the weighted-median tuning a wrong note, never
         moved and never folded into the tuning (`round2.known_melody`).

Inputs, conditions written before generating (S15):
  random   round 2's generator (`round2.melody`, its body copied into
           `render` with the notes given), 14 and 28 notes, sigma 0, 10,
           20, 30 cents, straight or vibrato (5.5 Hz +-50 cents faded in
           from 150 ms, round2.py line 140), 60 phrases per cell, 960;
  library  E-004 fold 2's 30 squillo items (`squillo-lab E-004 @ d0f9cde`,
           results/items/*.json), their written notes and tempo, sung by the
           same voice with the same error model, transposed as E-004 run.py
           `_one` (mean on the voice's base + 5, then by octaves) but kept
           inside round 2's range (top <= min(12, base + 17), bottom >= -25
           semitones re A4, round2.py line 109), sigma 0, 10, 20, 30, straight
           or vibrato, three renderings each, 720;
  (revision 1, before any run: where that placement leaves the item outside
  the voice's range, its lowest note goes on the range's floor, -25);
  every sounding sample of the contour inside ADR 0007's E2..C6, asserted
  on the generated contour (`round2.contour_ok`); every item's transposition
  fits every voice, asserted. The error model is round 2's: tuning G
  uniform in +-50 cents, per-note error normal of sd sigma, a scoop from
  below on half the notes (30..100 cents, 60 ms), wobble 1..6 Hz 10 cents RMS.
  Real: E-002 round 2's 40 WORLD re-syntheses (20 straight scales, 20
  vibrato rounds; `squillo-lab E-002 @ e7d2bf4`), whose f0 is known, and the
  77 VocalSet originals of round 1 (CC BY 4.0, not committed), H3 only.

Halves: a phrase is in the *fit* half when its seed is odd, *held out* when
even. Both selections below read the fit half only; every result is reported
on the held-out half.

Candidates for the per-note standard uncertainty u (selection 1, in order):
  P1  the note's settle u alone (round 2's, which holds 1 cent for the tracker);
  P2  P1 (+) the tuning's u: free, round 2's `ref_u_circ` (the circular
      mean's delta-method standard error); known, s / sqrt(n_eff), the
      weighted linear mean's (GUM E.4.3 form), s the known-melody spread.
Bar B1 (the per-note +-): in every cell (path x source x sigma x vibrato)
with at least 20 counted notes, the share of counted notes with
|d - delta| > 2u is at most 5 %, the share a k = 2 interval claims (GUM,
JCGM 100:2008, 6.3.3). Counted: found and right (free) or kept and not a
wrong note (known), in a phrase the path does not call uncertain (free: the
take's sigma-hat above chance; known: a finite spread).
Selection 1, per path: the first candidate passing B1 in every cell of the
fit half; if none, the first passing in every cell with sigma <= 20 (round 2:
sigma-hat honest while the true spread is at most 25 cents), its range
stated; if none, P2, and the per-note +- is reported not honest.

The move: a note is moved by m = -clip(d, -50, +50) cents at full strength
(the far vision), -clip(s d, ...) at strength s, the clip squillo SY-002's.
It is *harmful* when |delta + m| > |delta|: the moved note lies further
from its true aim than the sung one (a wrong aim moves it towards a wrong
note; an overshoot moves it past its aim by more than it was off).
Gate candidates (selection 2), every one also requiring |d| > 2u (the note
measurably off its aim; otherwise nothing is moved) with u selection 1's:
  free   phrase state Phi in {any (sigma-hat above chance), measured (U25:
         sigma-hat + 2 u_B <= 25, fold 2)} x T in {50, 40, 30, 20}: moved
         only when |d| + 2u <= T, in that order (Phi any first);
  known  T in {none, 50, 40, 30, 20}, in that order.
Bar B2 (no move the wrong way): in every cell with at least 20 moved notes,
the share of moved notes that the full-strength move harms is at most
2.5 %, one tail of the k = 2 interval of B1 (a move the wrong way is a
one-sided exclusion).
Selection 2, per path: among the gates passing B2 in every cell of the fit
half, the one moving most notes on the fit half (a tie: the earlier in the
order above); if none passes, no centring for that path, reported.

H3 (reported, no bar): with the selected u and gate, on the held-out half
and on the real takes, the rung is the take's pitch with each moved note's
frames shifted by its m (squillo SY-004: the rung's measures come from this
description, never from re-synthesized samples), measured again by the same
path; is it *improved* over the take? free: fold 2's `compare` (MT-008's
form where both are measured under U25, the one-sided form on honest ends);
known: round 2's `t_K` (MT-008's form on the linear spread). At strengths
s = 0.25, 0.5, 0.75, 1: the share of phrases with any moved note, with an
improved far vision (s = 1), and the least s improved.

Checks (S15), each with a must-pass and a must-fail case: `check` below,
results in results/round3_checks.json.
"""

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import json
import math
import pickle
import subprocess
import sys
import time
from fractions import Fraction
from multiprocessing import Pool
from pathlib import Path

import numpy as np

import run
import infer
import round2 as R2
import fold_refusal as FR
import synth  # noqa: F401  (puts E-001 on sys.path)
import voice

HERE = Path(__file__).parent
CACHE = HERE / "data" / "cache"
OUT = HERE / "results"
ITEMS = HERE.parent / "E-004-phrase-library" / "results" / "items"
P = R2.P
SR = R2.SR
SIGMAS = (0, 10, 20, 30)
LENGTHS = (14, 28)
PER_CELL = 60
REPS = 3
B1_MAX = 5.0    # per cent, GUM 6.3.3 at k = 2
B2_MAX = 2.5    # per cent, one tail
MIN_CELL = 20   # notes counted (B1) or moved (B2) for a cell to be judged
CLIP = 50.0     # cents, squillo SY-002
STRENGTHS = (0.25, 0.5, 0.75, 1.0)
GATES = dict(free=[(phi, T) for phi in ("any", "measured") for T in (50, 40, 30, 20)],
             known=[("any", T) for T in (None, 50, 40, 30, 20)])
NAMES = ("C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B")


def committed_first():
    """S15: refuse to run on an uncommitted edit of this file, or before it is committed."""
    me = Path(__file__).name
    a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
    b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", me], cwd=HERE)
    if a.returncode or b.returncode:
        sys.exit(f"{me} is not committed as it stands: commit the rules before running")


# ------------------------------------------------------------ inputs

def midi(p):
    """'C#4', 'Eb5', 'G3' -> MIDI number."""
    letter, rest = p[0], p[1:]
    acc = 0
    while rest and rest[0] in "#b":
        acc += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    return 12 * (int(rest) + 1) + "C D EF G A B".index(letter) + acc


def items():
    out = []
    for f in sorted(ITEMS.glob("*.json")):
        d = json.loads(f.read_text())
        m = d["melody"]
        notes = [midi(n["pitch"]) - 69 for n in m["notes"]]
        beats = [float(Fraction(n["quarters"])) for n in m["notes"]]
        out.append((d["phrase_id"], np.array(notes, float), np.array(beats) * 60.0 / m["tempo_qpm"]))
    assert len(out) == 30, len(out)
    return out


def transpose(semis, base):
    """E-004 run.py `_one`'s transposition, inside round 2's range; None when it cannot fit."""
    s = np.asarray(semis, float).copy()
    s += np.round(base + 5 - s.mean())
    hi, lo = min(12, base + 17), -25
    while s.max() > hi:
        s -= 12
    while s.min() < lo:
        s += 12
    if s.max() > hi or s.min() < lo:
        # Revision 1 (before any run; check C1 found apres-un-reve, blue-umbrella and
        # lamplighter outside the bass's range under the placement above): the lowest
        # note on the range's floor, when the span fits at all.
        s += lo - s.min()
    if s.max() > hi or s.min() < lo:
        return None
    return s


def render(voice_name, notes, durs, sigma, vib, seed, shift=0.0):
    """round2.phrase's body with the notes and durations given (S15: the contour asserted)."""
    from scipy.signal import butter, sosfiltfilt
    sex, base = voice.VOICES[voice_name]
    rng = np.random.default_rng(seed)
    notes = np.asarray(notes, float)
    durs = np.asarray(durs, float)
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
    ok, lo, hi = R2.contour_ok(sung, amp)
    if not ok:
        raise AssertionError(f"contour outside E2..C6: {lo:.1f} .. {hi:.1f} cents ({voice_name}, seed {seed})")
    x = voice.render(dict(sex=sex, n=n, amp=amp, noise_seed=seed + 1000), sung)
    return x.astype(np.float32), dict(notes=notes, starts=starts, durs=durs, G=G, e=e, sung=sung, amp=amp, lo=lo, hi=hi)


def jobs():
    out = []
    seed = 2026100159 * 10
    for n_notes in LENGTHS:
        for sigma in SIGMAS:
            for vib in (0, 1):
                for k in range(PER_CELL):
                    seed += 1
                    out.append(dict(source=f"random{n_notes}", sigma=sigma, vib=vib, seed=seed,
                                    voice=run.VOICES[k % 6], scale=run.SCALE_NAMES[(k // 6) % 5], n_notes=n_notes))
    for i, (pid, _, _) in enumerate(items()):
        for sigma in SIGMAS:
            for vib in (0, 1):
                for rep in range(REPS):
                    seed += 1
                    out.append(dict(source="library", sigma=sigma, vib=vib, seed=seed, item=pid,
                                    voice=run.VOICES[(i + 2 * rep + sigma // 10 + vib) % 6]))
    return out


def make(job, shift=0.0):
    """The phrase of a job: its notes and durations, then rendered."""
    if job["source"] == "library":
        it = {p: (n, d) for p, n, d in items()}[job["item"]]
        notes = transpose(it[0], voice.VOICES[job["voice"]][1])
        assert notes is not None, job
        durs = it[1]
    else:
        rng = np.random.default_rng(job["seed"])
        for _ in range(100):
            m = R2.melody(job["scale"], voice.VOICES[job["voice"]][1], rng, job["n_notes"])
            if m is not None:
                break
        notes, durs = m
    return render(job["voice"], notes, durs, job["sigma"], job["vib"], job["seed"], shift)


# ------------------------------------------------------------ the two paths

def free_path(cents, t):
    segs = R2.est_segments(cents)
    if not segs:
        return None
    o = R2.infer_global(cents, t, segs, R2.settle_cycles)
    keep = o["dur"] >= R2.TRANS_S
    if keep.sum() >= 2:
        sp = R2.spread_all(o["dev"][keep], o["dur"][keep], o["u_settle"][keep])
        u_ref = R2.ref_u_circ(o["dev"][keep], o["dur"][keep])
    else:
        sp, u_ref = dict(s=np.inf, uB=np.nan), np.inf
    return dict(segs=segs, keep=keep, centre=o["settle"], aim=o["ref"] + P * o["target"], d=o["dev"],
                us=o["u_settle"], dur=o["dur"], u_ref=float(u_ref), sp=sp, state=FR.state(sp))


def known_path(cents, t, states, al=None):
    states = np.asarray(states, float)
    segs, T, bad = al if al is not None else R2.align(cents, states)
    ok = [i for i, s in enumerate(segs) if s is not None and s[1] - s[0] >= 1
          and np.sum(~np.isnan(cents[s[0]:s[1]])) > 0]
    if not ok:
        return None
    st = R2.settle_cycles(cents, t, [segs[i] for i in ok])
    keep = st[:, 1] >= R2.TRANS_S
    idx = np.array(ok)[keep]
    c, w, us = st[keep, 0], st[keep, 1], st[keep, 2]
    dev = c - P * states[idx]
    if len(dev) == 0:
        return None
    wrong = np.abs(dev - R2.wmedian(dev, w)) > R2.WRONG_NOTE
    g = ~wrong
    tun = float(np.average(dev[g], weights=w[g]))
    d = dev - tun
    n = R2.n_eff(w[g])
    if n <= 1:
        s, uB, u_ref = np.nan, np.nan, np.inf
    else:
        s = math.sqrt(np.average(d[g] ** 2, weights=w[g]) * n / (n - 1))
        a = s / math.sqrt(2 * (n - 1))
        uB = float(np.hypot(a, np.sqrt(np.average(us[g] ** 2, weights=w[g]))))
        u_ref = s / math.sqrt(n)
    return dict(idx=idx, segs=[segs[i] for i in idx], centre=c, aim=P * states[idx] + tun, d=d, us=us, dur=w,
                wrong=wrong, u_ref=float(u_ref), sp=dict(s=float(s), uB=float(uB)), bad=bad)


def u_of(path, cand):
    return path["us"] if cand == "P1" else np.hypot(path["us"], path["u_ref"])


# ------------------------------------------------------------ truth

def centres(tc, t, segs):
    return R2.settle_cycles(tc, t, segs)


def truth_synth(tr, t):
    """Per note and per state: C (the settle rule on the sung contour over the true
    boundaries), tau (weighted linear mean of C - 100 n over notes), A = 100 n + tau."""
    pos = np.clip(np.round(t * SR).astype(int), 0, len(tr["sung"]) - 1)
    tc = np.where(tr["amp"][pos] >= 0.999, tr["sung"][pos], np.nan)
    nof, mid = run.note_frames(t, tr["starts"], tr["durs"])
    tsegs = run.oracle_from(nof)
    note_of = np.array([int(nof[a]) for a, b in tsegs])
    assert len(note_of) == len(tr["notes"]) and np.all(note_of == np.arange(len(tr["notes"]))), "a note without frames"
    st = centres(tc, t, tsegs)
    C, w = st[:, 0], st[:, 1]
    tau = float(np.average(C - P * tr["notes"], weights=w))
    states, st_of_note = R2.merge_repeats(tr["notes"])
    ssegs = []
    for j in range(len(states)):
        ks = np.flatnonzero(st_of_note == j)
        ssegs.append((tsegs[ks[0]][0], tsegs[ks[-1]][1]))
    sC = centres(tc, t, ssegs)[:, 0]
    return dict(nof=nof, mid=mid, notes=tr["notes"], C=C, A=P * tr["notes"] + tau, tau=tau,
                states=states, sC=sC, sA=P * states + tau, n_states_found=len(states))


def truth_resynth(tc, t, states):
    """Round 2's truth procedure (`truth_spread`): the known f0 aligned to the score;
    per state C by the settle rule; tau over states that are not wrong notes."""
    segs, T, bad = R2.align(tc, states)
    ok = [j for j, s in enumerate(segs) if s is not None and s[1] - s[0] >= 1]
    st = centres(tc, t, [segs[j] for j in ok])
    C, w = st[:, 0], st[:, 1]
    dev = C - P * np.asarray(states, float)[ok]
    good = np.abs(dev - R2.wmedian(dev, w)) <= R2.WRONG_NOTE
    tau = float(np.average(dev[good], weights=w[good]))
    nof = np.full(len(t), -1)
    mid = np.zeros(len(t), bool)
    for j in ok:
        a, b = segs[j]
        nof[a:b] = j
        L = b - a
        mid[a + int(0.3 * L):a + max(int(0.9 * L), int(0.3 * L) + 1)] = True
    sC = np.full(len(states), np.nan)
    sC[ok] = C
    return dict(nof=nof, mid=mid, notes=np.asarray(states, float), C=sC, A=P * np.asarray(states, float) + tau,
                tau=tau, states=np.asarray(states, float), sC=sC, sA=P * np.asarray(states, float) + tau,
                n_states_found=len(ok), all_found=len(ok) == len(states), truth_bad=bad)


# ------------------------------------------------------------ per-note records

def free_records(fp, tru):
    """Per true note: found, right, d, delta, u_s, u_ref, phrase state."""
    rows = []
    if fp is None:
        return np.zeros((0, 7))
    calls = R2.note_calls(tru["nof"], tru["mid"], fp["segs"], None, fp["keep"])
    for k, c in enumerate(calls):
        if c is None or not np.isfinite(tru["C"][k]):
            rows.append((0, 0, np.nan, np.nan, np.nan, np.nan, -1))
            continue
        right = abs(fp["aim"][c] - tru["A"][k]) < 50.0
        rows.append((1, int(right), fp["d"][c], tru["C"][k] - tru["A"][k], fp["us"][c], fp["u_ref"], c))
    return np.array(rows, float)


def known_records(kp, tru):
    """Per kept state: wrong, d, delta, u_s, u_ref, state index."""
    if kp is None:
        return np.zeros((0, 6))
    rows = []
    for i, j in enumerate(kp["idx"]):
        rows.append((int(kp["wrong"][i]), kp["d"][i], tru["sC"][j] - tru["sA"][j], kp["us"][i], kp["u_ref"], j))
    return np.array(rows, float)


def one(job):
    x, tr = make(job)
    t, cents, dmin, n_ref = FR.track(x)
    tru = truth_synth(tr, t)
    fp = free_path(cents, t)
    kp = known_path(cents, t, tru["states"])
    row = dict(job)
    row.update(fit=job["seed"] % 2 == 1, frames_refused=n_ref, lo=tr["lo"], hi=tr["hi"],
               free=free_records(fp, tru), known=known_records(kp, tru),
               free_state=fp["state"] if fp else "uncertain", free_sp=fp["sp"] if fp else None,
               known_sp=kp["sp"] if kp else None, t=t.astype(np.float32), cents=cents.astype(np.float32),
               states=tru["states"])
    return row


# ------------------------------------------------------------ runs

def run_synth(procs="18"):
    committed_first()
    path = CACHE / "r3_synth.pkl"
    done = pickle.load(open(path, "rb")) if path.exists() else []
    seen = {r["seed"] for r in done}
    todo = [j for j in jobs() if j["seed"] not in seen]
    print(len(done), "done,", len(todo), "to do", flush=True)
    t0 = time.time()
    with Pool(int(procs)) as p:
        for k, r in enumerate(p.imap_unordered(one, todo, chunksize=1), 1):
            done.append(r)
            if k % 100 == 0 or k == len(todo):
                pickle.dump(done, open(path, "wb"))
                print(k, f"{time.time() - t0:.0f} s", flush=True)


def time_sample(n="36", procs="18"):
    """S19: a sample over every condition (each source x sigma x vibrato, extremes
    included), on the pool at the process count the run uses, each item to its end."""
    committed_first()
    js = jobs()
    pick, seen = [], {}
    for j in js:
        key = (j["source"], j["sigma"], j["vib"])
        if seen.get(key, 0) < max(1, int(n) // 24):
            pick.append(j)
            seen[key] = seen.get(key, 0) + 1
    t0 = time.time()
    with Pool(int(procs)) as p:
        rows = p.map(one, pick, chunksize=1)
    dt = time.time() - t0
    print(f"{len(pick)} phrases on {procs} processes: {dt:.1f} s, {dt / len(pick):.3f} s per phrase of wall time;"
          f" {len(js)} phrases: {len(js) * dt / len(pick) / 60:.1f} min")
    pickle.dump(rows, open(CACHE / "r3_sample.pkl", "wb"))
    t0 = time.time()
    sel = dict(free=dict(u="P2", gate=("any", 50)), known=dict(u="P2", gate=("any", None)))
    with Pool(int(procs)) as p:
        p.map(rung_one, [(r, sel) for r in rows], chunksize=1)
    dt = time.time() - t0
    print(f"rungs: {dt:.1f} s, {dt / len(rows):.3f} s per phrase")


def one_real(args):
    kind, path = args
    import soundfile as sf
    from scipy.signal import resample_poly
    name = Path(path).stem
    states, _ = R2.merge_repeats(R2.score_of(name))
    states = np.asarray(states, float)
    if kind == "resynth":
        z = np.load(path)
        x, f0 = z["y"].astype(np.float32), z["f0"]
    else:
        x, sr = sf.read(path, dtype="float64")
        if x.ndim > 1:
            x = x.mean(axis=1)
        g = math.gcd(SR, sr)
        x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    t, cents, dmin, n_ref = FR.track(x)
    row = dict(kind=kind, name=name, set=("scales_straight" if "scales_straight" in name else
                                          "row_vibrato" if "row_vibrato" in name else
                                          "row_straight" if "row_straight" in name else "scales_vibrato"),
               t=t.astype(np.float32), cents=cents.astype(np.float32), states=states)
    fp = free_path(cents, t)
    kp = known_path(cents, t, states)
    row.update(free_state=fp["state"] if fp else "uncertain", free_sp=fp["sp"] if fp else None,
               known_sp=kp["sp"] if kp else None)
    if kind == "resynth":
        ft = R2.truth_per_sample(f0, len(x))
        tc = R2.frame_truth_cents(ft, t)
        tru = truth_resynth(tc, t, states)
        row.update(free=free_records(fp, tru), known=known_records(kp, tru), all_found=tru["all_found"],
                   n_states=len(states), n_found=tru["n_states_found"])
    return row


def run_real():
    committed_first()
    names = [Path(l.strip()).name for l in (HERE / "data" / "vocalset-files.txt").read_text().splitlines() if l.strip()]
    originals = [("original", CACHE / n) for n in names]
    assert all(p.exists() for _, p in originals)
    r2 = sorted(p for p in (R2.E002 / "data" / "cache" / "r2").glob("*.npz")
                if "scales_straight" in p.stem or "row_vibrato" in p.stem)
    assert len(r2) == 40, len(r2)
    with Pool(18) as p:
        rows = p.map(one_real, [("resynth", q) for q in r2] + originals)
    pickle.dump(rows, open(CACHE / "r3_real.pkl", "wb"))
    print(len(rows), "real takes")


# ------------------------------------------------------------ bars and selections

def wilson(k, n):
    return FR.wilson(k, n)


def b1_miss(rows, path, cand):
    """Counted notes and misses of |d - delta| <= 2u, per phrase list."""
    k = n = 0
    for r in rows:
        a = r[path]
        if len(a) == 0:
            continue
        if path == "free":
            if r["free_state"] == "uncertain":
                continue
            m = (a[:, 0] == 1) & (a[:, 1] == 1)
            d, dl, us, ur = a[m, 2], a[m, 3], a[m, 4], a[m, 5]
        else:
            if r["known_sp"] is None or not np.isfinite(r["known_sp"]["s"]):
                continue
            m = a[:, 0] == 0
            d, dl, us, ur = a[m, 1], a[m, 2], a[m, 3], a[m, 4]
        u = us if cand == "P1" else np.hypot(us, ur)
        k += int(np.sum(np.abs(d - dl) > 2 * u))
        n += int(m.sum())
    return k, n


def moved(r, path, cand, gate, s=1.0):
    """Per-note (free: per true note; known: per kept state) move and its truth:
    returns arrays (moved mask, m, delta) over the records. Free: every true note
    whose called segment is moved (so a misattributed note is moved too)."""
    a = r[path]
    phi, T = gate
    if len(a) == 0:
        return np.zeros(0, bool), np.zeros(0), np.zeros(0)
    if path == "free":
        if r["free_state"] == "uncertain" or (phi == "measured" and r["free_state"] != "measured"):
            return np.zeros(len(a), bool), np.zeros(len(a)), a[:, 3]
        found = a[:, 0] == 1
        d, dl, us, ur = a[:, 2], a[:, 3], a[:, 4], a[:, 5]
    else:
        if r["known_sp"] is None or not np.isfinite(r["known_sp"]["s"]):
            return np.zeros(len(a), bool), np.zeros(len(a)), a[:, 2]
        found = a[:, 0] == 0
        d, dl, us, ur = a[:, 1], a[:, 2], a[:, 3], a[:, 4]
    u = us if cand == "P1" else np.hypot(us, ur)
    with np.errstate(invalid="ignore"):
        mv = found & (np.abs(d) > 2 * u)
        if T is not None:
            mv &= np.abs(d) + 2 * u <= T
    m = np.where(mv, -np.clip(s * np.nan_to_num(d), -CLIP, CLIP), 0.0)
    return mv, m, dl


def harmful(m, dl):
    return np.abs(dl + m) > np.abs(dl)


def b2(rows, path, cand, gate):
    k = n = 0
    for r in rows:
        mv, m, dl = moved(r, path, cand, gate)
        k += int(np.sum(harmful(m[mv], dl[mv])))
        n += int(mv.sum())
    return k, n


def cells(rows):
    c = {}
    for r in rows:
        src = r.get("source", r.get("set"))
        c.setdefault((src, r.get("sigma", -1), r.get("vib", -1)), []).append(r)
    return c


def judge(rows, fn, bar, label):
    """Every cell with >= MIN_CELL counted: share <= bar. Returns (pass, table)."""
    tab, ok = [], True
    for key, rs in sorted(cells(rows).items(), key=lambda kv: str(kv[0])):
        k, n = fn(rs)
        w = wilson(k, n)
        judged = n >= MIN_CELL
        good = (not judged) or 100.0 * k / n <= bar
        ok &= good
        tab.append(dict(cell=list(key), k=k, n=n, share=w, judged=judged, passes=good))
    return ok, tab


def select_u(rows, path):
    for cand in ("P1", "P2"):
        ok, _ = judge(rows, lambda rs: b1_miss(rs, path, cand), B1_MAX, cand)
        if ok:
            return dict(u=cand, range="every cell")
    for cand in ("P1", "P2"):
        ok, _ = judge([r for r in rows if r["sigma"] <= 20], lambda rs: b1_miss(rs, path, cand), B1_MAX, cand)
        if ok:
            return dict(u=cand, range="sigma <= 20")
    return dict(u="P2", range="none: per-note +- not honest")


def select_gate(rows, path, cand):
    best = None
    for gate in GATES[path]:
        ok, _ = judge(rows, lambda rs: b2(rs, path, cand, gate), B2_MAX, str(gate))
        if not ok:
            continue
        n = b2(rows, path, cand, gate)[1]
        if best is None or n > best[1]:
            best = (gate, n)
    return None if best is None else dict(gate=list(best[0]), moved_fit=best[1])


def select():
    committed_first()
    rows = [r for r in pickle.load(open(CACHE / "r3_synth.pkl", "rb")) if r["fit"]]
    out = {}
    for path in ("free", "known"):
        su = select_u(rows, path)
        sg = select_gate(rows, path, su["u"])
        out[path] = dict(**su, gate=sg)
    out["fit_phrases"] = len(rows)
    json.dump(out, open(OUT / "round3_select.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


# ------------------------------------------------------------ H3: the rung

def rung_cents(cents, segs, moves):
    y = np.array(cents, float)
    for (a, b), m in zip(segs, moves):
        if m != 0.0:
            y[a:b] = y[a:b] + m
    return y


def seg_moves(r, path, cand, gate, s):
    """Moves per estimated segment (free) or kept state (known), recomputed from the take's pitch."""
    t, cents = r["t"].astype(float), r["cents"].astype(float)
    phi, T = gate
    if path == "free":
        fp = free_path(cents, t)
        if fp is None or fp["state"] == "uncertain" or (phi == "measured" and fp["state"] != "measured"):
            return None, None, fp
        u = u_of(fp, cand)
        mv = fp["keep"] & (np.abs(fp["d"]) > 2 * u)
        if T is not None:
            mv &= np.abs(fp["d"]) + 2 * u <= T
        m = np.where(mv, -np.clip(s * fp["d"], -CLIP, CLIP), 0.0)
        return fp["segs"], m, fp
    kp = known_path(cents, t, r["states"])
    if kp is None or not np.isfinite(kp["sp"]["s"]):
        return None, None, kp
    u = u_of(kp, cand)
    mv = ~kp["wrong"] & (np.abs(kp["d"]) > 2 * u)
    if T is not None:
        mv &= np.abs(kp["d"]) + 2 * u <= T
    m = np.where(mv, -np.clip(s * kp["d"], -CLIP, CLIP), 0.0)
    return kp["segs"], m, kp


def t_K(a, b):
    if not (np.isfinite(a["s"]) and np.isfinite(b["s"])):
        return 0
    d = a["s"] - b["s"]
    return int(np.sign(d)) if abs(d) > 2 * math.hypot(a["uB"], b["uB"]) else 0


def rung_one(args):
    r, sel = args
    t, cents = r["t"].astype(float), r["cents"].astype(float)
    out = {}
    for path in ("free", "known"):
        if sel[path]["gate"] is None:
            out[path] = None
            continue
        cand, gate = sel[path]["u"], tuple(sel[path]["gate"])
        res = {}
        for s in STRENGTHS:
            segs, m, take = seg_moves(r, path, cand, gate, s)
            if segs is None or not np.any(m):
                res[s] = dict(any_moved=False, cmp=0)
                continue
            y = rung_cents(cents, segs, m)
            if path == "free":
                sp = FR.measure(y, t)[0]
                res[s] = dict(any_moved=True, cmp=FR.compare(take["sp"], sp), take=take["sp"], rung=sp,
                              n_moved=int(np.sum(m != 0)))
            else:
                kr = known_path(y, t, r["states"])
                sp = kr["sp"] if kr else dict(s=np.nan, uB=np.nan)
                res[s] = dict(any_moved=True, cmp=t_K(take["sp"], sp), take=take["sp"], rung=sp,
                              n_moved=int(np.sum(m != 0)))
        out[path] = res
    return dict(key=r.get("seed", r.get("name")), out=out)


def _sel():
    s = json.load(open(OUT / "round3_select.json"))
    for p in ("free", "known"):
        if s[p]["gate"] is not None:
            s[p]["gate"] = s[p]["gate"]["gate"]
    return s


def run_rungs(procs="18"):
    committed_first()
    sel = _sel()
    rows = [r for r in pickle.load(open(CACHE / "r3_synth.pkl", "rb")) if not r["fit"]]
    real = pickle.load(open(CACHE / "r3_real.pkl", "rb"))
    with Pool(int(procs)) as p:
        a = p.map(rung_one, [(r, sel) for r in rows], chunksize=2)
        b = p.map(rung_one, [(r, sel) for r in real], chunksize=1)
    pickle.dump(dict(synth=a, real=b), open(CACHE / "r3_rungs.pkl", "wb"))
    print(len(a), len(b))


# ------------------------------------------------------------ checks (S15)

def check():
    committed_first()
    out = {}
    its = items()
    # C1 generator: every item fits every voice (must pass); a 30-semitone span cannot (must fail);
    #    the contour assert on the highest and lowest voice at sigma 30 with vibrato (must pass), +1500 cents raises (must fail)
    fits = [(pid, v) for pid, n, _ in its for v in run.VOICES if transpose(n, voice.VOICES[v][1]) is None]
    wide = transpose(np.array([0.0, 30.0]), voice.VOICES["bass"][1])
    js = [j for j in jobs() if j["source"] == "library" and j["sigma"] == 30 and j["vib"] == 1]
    ext = []
    for j in js:
        if j["voice"] in ("bass", "soprano_high"):
            _, tr = make(j)
            ext.append((tr["lo"], tr["hi"]))
            if len(ext) >= 4:
                break
    try:
        make(js[0], shift=1500.0)
        raised = False
    except AssertionError:
        raised = True
    out["c1_generator"] = dict(items_not_fitting=fits, wide_fits=wide is not None, extremes=ext, shifted_raises=raised,
                               passes=not fits and wide is None and raised and
                               all(R2.E2_CENTS <= lo and hi <= R2.C6_CENTS for lo, hi in ext))
    assert out["c1_generator"]["passes"], out["c1_generator"]
    # C2 the truth's centre: on a contour of known constants over known boundaries the settle rule
    #    returns them (must pass); the same expectation on a contour with one note 5 cents off fails (must fail)
    t = np.arange(400) * R2.HOP_S
    vals = np.array([-1200.0, -1000.0, -950.0, -700.0])
    nof = np.repeat(np.arange(4), 100)
    tc = vals[nof].astype(float)
    tc[::37] = np.nan
    segs = run.oracle_from(nof)

    def match(contour):
        return bool(np.all(np.abs(centres(contour, t, segs)[:, 0] - vals) < 1e-9))
    bad = tc.copy()
    bad[200:300] += 5.0
    out["c2_truth_centre"] = dict(must_pass=match(tc), must_fail=match(bad))
    assert out["c2_truth_centre"] == dict(must_pass=True, must_fail=False)
    # C3 known_path reproduces round 2's known_melody s and u_B (must pass), not another phrase's (must fail)
    sample = [j for j in jobs() if j["sigma"] == 20 and j["vib"] == 0][::50][:3]
    got = []
    for j in sample:
        x, tr = make(j)
        tt, cents, _, _ = FR.track(x)
        states, _ = R2.merge_repeats(tr["notes"])
        al = R2.align(cents, states)
        got.append((known_path(cents, tt, states, al)["sp"], R2.known_melody(cents, tt, states, R2.settle_cycles, al)))
    same = all(abs(a["s"] - b["s"]) < 1e-9 and abs(a["uB"] - b["uB"]) < 1e-9 for a, b in got)
    other = all(abs(got[i][0]["s"] - got[(i + 1) % len(got)][1]["s"]) < 1e-9 for i in range(len(got)))
    out["c3_known_equals_round2"] = dict(phrases=[j["seed"] for j in sample], must_pass=same, must_fail=other)
    assert same and not other
    # C4, C5 the bars on reference conditions: 12 phrases of one cell (random14, sigma 10, straight)
    js = [j for j in jobs() if j["source"] == "random14" and j["sigma"] == 10 and j["vib"] == 0][:12]
    rows = [one(j) for j in js]
    oracle = []
    for r in rows:
        q = dict(r)
        a = r["free"].copy()
        a[:, 2] = a[:, 3]  # d := delta, the truth as the estimate
        q["free"] = a
        oracle.append(q)
    k, n = b1_miss(oracle, "free", "P1")
    zero = []
    for r in rows:
        q = dict(r)
        a = r["free"].copy()
        a[:, 4] = 0.0
        a[:, 5] = 0.0  # u := 0
        q["free"] = a
        zero.append(q)
    kz, nz = b1_miss(zero, "free", "P1")
    out["c4_b1_bar"] = dict(must_pass=[k, n], must_fail=[kz, nz],
                            passes=n >= MIN_CELL and 100 * k / n <= B1_MAX and 100 * kz / nz > B1_MAX)
    assert out["c4_b1_bar"]["passes"], out["c4_b1_bar"]
    h_ok = h_bad = nm = 0
    for r in oracle:
        mv, m, dl = moved(r, "free", "P1", ("any", None))
        h_ok += int(np.sum(harmful(m[mv], dl[mv])))
        h_bad += int(np.sum(harmful(-m[mv], dl[mv])))
        nm += int(mv.sum())
    out["c5_b2_bar"] = dict(moved=nm, must_pass_harmful=h_ok, must_fail_harmful=h_bad,
                            passes=nm >= MIN_CELL and h_ok == 0 and 100 * h_bad / nm > B2_MAX)
    assert out["c5_b2_bar"]["passes"], out["c5_b2_bar"]
    # C6 the rung: exactly the moved segments' frames shift, NaN stays NaN (must pass);
    #    a segment off by one frame is caught by the same comparison (must fail)
    r = rows[0]
    cents = r["cents"].astype(float)
    fp = free_path(cents, r["t"].astype(float))
    m = np.where(np.arange(len(fp["segs"])) % 2 == 0, 7.0, 0.0)
    y = rung_cents(cents, fp["segs"], m)
    exp = cents.copy()
    for (a, b), mm in zip(fp["segs"], m):
        exp[a:b] += mm

    def same_frames(u, v):
        return bool(np.array_equal(np.isnan(u), np.isnan(v)) and np.allclose(u[~np.isnan(u)], v[~np.isnan(v)], atol=0, rtol=0))
    shifted = rung_cents(cents, [(a + 1, b + 1) for a, b in fp["segs"]], m)
    out["c6_rung"] = dict(must_pass=same_frames(y, exp), must_fail=same_frames(shifted, exp))
    assert out["c6_rung"] == dict(must_pass=True, must_fail=False)
    json.dump(out, open(OUT / "round3_checks.json", "w"), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float))


# ------------------------------------------------------------ report

def report():
    committed_first()
    rows = pickle.load(open(CACHE / "r3_synth.pkl", "rb"))
    real = pickle.load(open(CACHE / "r3_real.pkl", "rb"))
    rg = pickle.load(open(CACHE / "r3_rungs.pkl", "rb"))
    sel = json.load(open(OUT / "round3_select.json"))
    fit = [r for r in rows if r["fit"]]
    held = [r for r in rows if not r["fit"]]
    res = dict(selection=sel, phrases=dict(fit=len(fit), held=len(held)),
               inputs=dict(lo=min(r["lo"] for r in rows), hi=max(r["hi"] for r in rows),
                           refused_share=float(np.mean([r["frames_refused"] for r in rows]))))
    for path in ("free", "known"):
        cand = sel[path]["u"]
        p = res[path] = {}
        for half, rs in (("fit", fit), ("held", held)):
            for c in ("P1", "P2"):
                ok, tab = judge(rs, lambda q: b1_miss(q, path, c), B1_MAX, c)
                p[f"B1_{c}_{half}"] = dict(passes=ok, cells=tab)
            if sel[path]["gate"]:
                g = tuple(sel[path]["gate"]["gate"])
                ok, tab = judge(rs, lambda q: b2(q, path, cand, g), B2_MAX, str(g))
                p[f"B2_{half}"] = dict(passes=ok, cells=tab)
        for g in GATES[path]:
            p[f"B2_fit_all_{g}"] = judge(fit, lambda q: b2(q, path, cand, g), B2_MAX, str(g))[0]
        # attribution, found notes, held out (free)
        if path == "free":
            att = {}
            for key, rs in sorted(cells(held).items(), key=lambda kv: str(kv[0])):
                a = np.concatenate([r["free"] for r in rs if len(r["free"])])
                att[str(key)] = dict(found=wilson(int(a[:, 0].sum()), len(a)), right_of_found=wilson(int(a[a[:, 0] == 1, 1].sum()), int(a[:, 0].sum())),
                                     uncertain=sum(r["free_state"] == "uncertain" for r in rs),
                                     measured=sum(r["free_state"] == "measured" for r in rs), phrases=len(rs))
            p["attribution_held"] = att
        # real re-syntheses
        rr = [r for r in real if r["kind"] == "resynth"]
        out = {}
        for st in ("scales_straight", "row_vibrato"):
            b = [r for r in rr if r["set"] == st]
            ball = [r for r in b if r["all_found"]]
            kk, nn = b1_miss(ball, path, cand)
            kk2, nn2 = b1_miss(b, path, cand)
            ent = dict(takes=len(b), all_states_found=len(ball), B1_all_found=wilson(kk, nn), B1_every_take=wilson(kk2, nn2))
            if sel[path]["gate"]:
                g = tuple(sel[path]["gate"]["gate"])
                h, nm = b2(ball, path, cand, g)
                h2, nm2 = b2(b, path, cand, g)
                ent.update(B2_all_found=wilson(h, nm), B2_every_take=wilson(h2, nm2))
            ent["states"] = Counter_states(b, path)
            out[st] = ent
        p["real_resynth"] = out
    # H3
    def h3(entries, rowsref):
        res3 = {}
        for path in ("free", "known"):
            if sel[path]["gate"] is None:
                res3[path] = None
                continue
            bykey = {e["key"]: e["out"][path] for e in entries}
            c = {}
            for key, rs in sorted(cells(rowsref).items(), key=lambda kv: str(kv[0])):
                o = [bykey[r.get("seed", r.get("name"))] for r in rs]
                anym = sum(x[1.0]["any_moved"] for x in o)
                imp = sum(x[1.0]["cmp"] == 1 for x in o)
                worse = sum(x[s]["cmp"] == -1 for x in o for s in STRENGTHS)
                least = [min([s for s in STRENGTHS if x[s]["cmp"] == 1]) for x in o if any(x[s]["cmp"] == 1 for s in STRENGTHS)]
                c[str(key)] = dict(phrases=len(o), any_moved=wilson(anym, len(o)), far_vision_improved=wilson(imp, len(o)),
                                   least_s_improved_median=float(np.median(least)) if least else None,
                                   least_s_counts={str(s): least.count(s) for s in STRENGTHS}, worse_any_s=worse)
            res3[path] = c
        return res3
    res["H3_held"] = h3(rg["synth"], held)
    res["H3_real"] = h3(rg["real"], real)
    by = {}
    for r in real:
        k = f"{r['kind']}/{r['set']}"
        e = by.setdefault(k, dict(takes=0, free_states={}, known_s=[], known_uB=[]))
        e["takes"] += 1
        e["free_states"][r["free_state"]] = e["free_states"].get(r["free_state"], 0) + 1
        if r["known_sp"] and np.isfinite(r["known_sp"]["s"]):
            e["known_s"].append(r["known_sp"]["s"])
            e["known_uB"].append(r["known_sp"]["uB"])
    for e in by.values():
        e["known_s_median"] = _med(e.pop("known_s"))
        e["known_uB_median"] = _med(e.pop("known_uB"))
    res["real_states"] = by
    json.dump(res, open(OUT / "round3.json", "w"), indent=1, default=float)
    print("written results/round3.json")


def _med(x):
    return float(np.median(x)) if len(x) else None


def Counter_states(b, path):
    out = {}
    for r in b:
        k = r["free_state"] if path == "free" else ("finite" if r["known_sp"] and np.isfinite(r["known_sp"]["s"]) else "none")
        out[k] = out.get(k, 0) + 1
    return out


# ------------------------------------------------------------ revision 2: post hoc (after the run, labelled)

def posthoc(procs="18"):
    """Post hoc, written after `report` (revision 2), never a selection: (a) B2 for every
    gate on both halves, with the worst judged cell; (b) H3 for the known path with no
    T gate (every note measurably off and not a wrong note moved), held-out half and real."""
    committed_first()
    rows = pickle.load(open(CACHE / "r3_synth.pkl", "rb"))
    real = pickle.load(open(CACHE / "r3_real.pkl", "rb"))
    sel = _sel()
    out = dict(note="post hoc: written after the run's report; not a selection", gates=[])
    for half in (True, False):
        rs = [r for r in rows if r["fit"] == half]
        for path in ("free", "known"):
            cand = sel[path]["u"]
            for g in GATES[path]:
                ok, tab = judge(rs, lambda q: b2(q, path, cand, g), B2_MAX, str(g))
                j = [c for c in tab if c["judged"]]
                worst = max(j, key=lambda c: c["k"] / c["n"]) if j else None
                out["gates"].append(dict(half="fit" if half else "held", path=path, u=cand, gate=[g[0], g[1]], passes=ok,
                                         moved=sum(c["n"] for c in tab), harmed=sum(c["k"] for c in tab),
                                         worst_cell=worst))
    s2 = dict(free=dict(u=sel["free"]["u"], gate=None), known=dict(u=sel["known"]["u"], gate=["any", None]))
    held = [r for r in rows if not r["fit"]]
    with Pool(int(procs)) as p:
        a = p.map(rung_one, [(r, s2) for r in held], chunksize=2)
        b = p.map(rung_one, [(r, s2) for r in real], chunksize=1)
    h = {}
    for name, entries, ref in (("held", a, held), ("real", b, real)):
        by = {e["key"]: e["out"]["known"] for e in entries}
        c = {}
        for key, rs in sorted(cells(ref).items(), key=lambda kv: str(kv[0])):
            o = [by[r.get("seed", r.get("name"))] for r in rs]
            ds = [x[1.0]["take"]["s"] - x[1.0]["rung"]["s"] for x in o if x[1.0]["any_moved"]]
            bd = [2 * math.hypot(x[1.0]["take"]["uB"], x[1.0]["rung"]["uB"]) for x in o if x[1.0]["any_moved"]]
            c[str(key)] = dict(phrases=len(o), any_moved=wilson(sum(x[1.0]["any_moved"] for x in o), len(o)),
                               far_vision_improved=wilson(sum(x[1.0]["cmp"] == 1 for x in o), len(o)),
                               worse_any_s=sum(x[s]["cmp"] == -1 for x in o for s in STRENGTHS),
                               spread_drop_median=_med(ds), bound_median=_med(bd))
        h[name] = c
    out["H3_known_no_T"] = h
    json.dump(out, open(OUT / "round3_posthoc.json", "w"), indent=1, default=float)
    print("written results/round3_posthoc.json")


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    dict(check=check, time=time_sample, synth=run_synth, real=run_real, select=select, rungs=run_rungs,
         report=report, posthoc=posthoc)[cmd](*args)
