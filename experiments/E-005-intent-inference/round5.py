"""E-005 round 5 (squillo iteration 73, F-041): the known-melody spread under MT-003's refusal.

Crude experiment code. Rounds 1-4 and the folds stay unchanged; this file adds,
never replaces. It imports round 2's generator and estimators, the fold's
refusal, round 3's library renderer and round 4's onset generator.

    uv run python round5.py check          # the checks, each checked (S15) -> results/round5_checks.json
    uv run python round5.py time 36 18     # S19 sample on the pool, after the rules commit
    uv run python round5.py synth 18       # 2040 phrases -> data/cache/r5_synth.pkl (saves every 100, resumes)
    uv run python round5.py real           # 40 E-002 re-syntheses, 77 VocalSet originals -> data/cache/r5_real.pkl
    uv run python round5.py report         # -> results/round5.json

Question (squillo R-14 section 8, iteration 73; F-041, F-033 (c), Q-021 part 6).
Round 2 (R7, R8) found that for a library phrase the spread about its written
notes, unwrapped (the known-melody spread, K), is honest to 40 cents and sees
improvement two to three times as often as the take's own wrapped spread. It
measured with every frame YIN gave. Squillo `metrics` MT-003 now makes a frame
with aperiodicity >= 0.02 unmeasurable. Does K stay honest under the refusal,
and in which states may squillo show it? Its fold needs the alignment rule
stated exactly, so it is stated here and checked against an independent
implementation (c2).

THE MEASURE K, stated exactly (round2.align, round2.dtw_T, round2.known_melody;
reimplemented here as known_parts / k_spread and checked against round 2's
cached values in c1):
  1. Cells: the take's pitch frames (hop 384 at 48 kHz) that MT-003 measures;
     a refused or unvoiced frame is a gap.
  2. Written states: the phrase's written notes in semitones, consecutive
     repeats merged into one state (round2.merge_repeats).
  3. The contour aligned: the measured cells in order, gaps skipped, each
     replaced by the median of the 25 cells centred on it (200 ms; the ends
     padded with the end value, infer.running_median).
  4. Transposition: r0 = the circular mean (100-cent circle, equal weights)
     of that contour; candidates T = r0 + 100 k, k = -45 .. 45.
  5. Alignment: the path assigning each contour cell i a state j(i), with
     j(first) = 0, j(last) = the last state, and j(i) - j(i - 1) in {0, 1};
     cost sum_i min(|x_i - 100 s_j(i) - T|, 300) cents; T the candidate of
     least total cost, the first in increasing k on a tie; the path then the
     least-cost path at that T, a tie between staying and moving resolved
     to staying (round2.dtw_T: `back = move < stay`).
  6. A state's segment: its first to its last mapped cell, in frame index,
     gaps inside included; a state with no cell is not found.
  7. Each found state's centre by round 2's settle (round2.settle_cycles:
     the whole-cycle mean where the fitted vibrato amplitude is >= 25 cents,
     else the median, over 30-90 % of the segment), its duration and settle
     u; states shorter than 0.1 s dropped (round2.TRANS_S).
  8. dev = centre - 100 * state. A note more than 150 cents from the
     duration-weighted median of dev is a wrong note, counted apart and
     left out (round2.WRONG_NOTE).
  9. Tuning: the duration-weighted mean of the kept dev. K = sqrt(weighted
     mean of (dev - tuning)^2 * n / (n - 1)), n = (sum w)^2 / sum w^2;
     u_B = K / sqrt(2 (n - 1)) (+) the weighted rms of the settle u's
     (GUM E.4.3 (+) settle, round 2's u_B). Fewer than two kept notes
     (n <= 1): no value.

CANDIDATE STATES for K, each: "too few" when K has no value; "measured",
K +- 2 u_B, when its upper end K + 2 u_B <= X; otherwise "at least", its lower
end K - 2 u_B only. X in order: inf (always measured, round 2's K), 40 (the
largest spread round 2 tested), 35, 30.

INPUTS, conditions written before generating (S15):
  - R: round 2's synthetic design under its own seeds (round2.jobs_synth),
    the first 40 phrases of each of its 42 cells (14, 28, 56 notes;
    sigma 0, 10, 15, 20, 25, 30, 40; straight or 5.5 Hz +-50 cents faded
    in), 1680 phrases; every contour asserted inside E2..C6 by
    round2.phrase (round2.py:119-160, contour_ok);
  - O: round 4's onset condition (round4.jobs_synth, 50 cents full from
    each note's first sample), the first 40 of each of its 6 cells
    (14, 28 notes x sigma 0, 10, 20), 240 phrases; contour and vibrato
    asserted by round4.phrase4 (assert_vib);
  - L: E-004 fold 2's 30 library items (round3.items), each at sigma 0
    and 20, straight and vibrato faded in, one rendering each, 120
    phrases, by round3.make (contour asserted in round3.render);
  - real: round 2's 40 E-002 re-syntheses (known f0; truth from round 2's
    cache r2_real.pkl, unchanged by the refusal) and 77 VocalSet originals.
  Every phrase is tracked once; K is computed with every frame YIN gives
  (`off`, only for c1's reproduction of round 2) and with the refusal (`on`).
  The take's own wrapped spread under MT-007 (fold_refusal.measure, U25) is
  computed on the same frames for the power comparison.

TRUTH: the population spread sigma the generator draws each note's error
from (fold_refusal's bar, round 2's R3); the realised spread is reported.
For re-syntheses, round 2's truth_spread on the known f0, judged on the
takes whose truth found every score state.

BARS, before the run:
  B1 honesty: in every cell of R (40 phrases), O (40) and L (30: item x
     sigma x vibrato pooled over items), the candidate's shown statement
     excludes sigma in at most BAR_MISS = 5 % of phrases (GUM 6.3.3,
     k = 2; fold_refusal's BAR). Excludes: measured and |K - sigma| > 2 u_B,
     or at least and K - 2 u_B > sigma.
  Selection: the first candidate in X order that passes B1. None passing:
     K is not honest under the refusal, and F-041 says so.
  B2 false change, for the selected candidate: on pairs of phrases of one
     R cell (phrases 2i and 2i + 1), pooled over sigma in each length x
     vibrato condition (140 pairs), the comparison (MT-008's form where
     both are measured; the later measured with its upper end below the
     earlier's lower end, or the reverse; nothing else compared) calls a
     change in at most BAR_MISS.
  B3 real: on the re-syntheses whose truth found every state, in each set
     (straight scales, vibrato rounds), the selected candidate excludes
     the true spread in at most BAR_MISS.
  Reported with no bar: power 20 -> 0 and 40 -> 10 cents (phrase k of one
  cell against phrase k of the other) for K and for the wrapped spread on
  the same phrases; states found, wrong notes, refused frames; the
  originals' halves (kept notes split into first and second half, each
  half's K compared) and states.

CHECKS (S15), each with a must-pass and a must-fail case whose input differs:
  c1 the reimplemented K equals round 2's cached `known` (s, uB) within
     REPRO_TOL on the same phrase without the refusal; must fail against
     the next phrase's cached values. In `check` on 4 phrases; in `report`
     on every R phrase.
  c2 the alignment: round2.dtw_T equals an independent full-matrix dynamic
     programme (ref_align) in T, path and cost on random cases; must fail
     when the reference is given one state a semitone off.
  c3 the refusal drops exactly the frames at d' >= 0.02: squillo's
     tone-aperiodic.wav, 13 refused (E-002 fold F5); must fail with the
     threshold at 0.2 (none refused).
  c4 bar B1 on reference conditions, round 2's cached values (no refusal):
     K always measured on the sigma <= 30 cells must pass; the wrapped
     spread always shown as measured on the sigma = 40 cells must fail.
  c5 the comparison: a phrase against itself is no change; against the same
     values with K lowered by three times the bound it must call one.
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
from multiprocessing import Pool
from pathlib import Path

import numpy as np

import run
import infer
import round2 as R2
import fold_refusal as FR

HERE = Path(__file__).parent
CACHE = HERE / "data" / "cache"
OUT = HERE / "results"
SQ = HERE.parents[2] / "squillo"
P = R2.P
REFUSE = FR.REFUSE          # squillo MT-003: aperiodicity >= 0.02 unmeasurable
BAR_MISS = FR.BAR           # per cent, fold_refusal's bar: the share a k = 2 interval claims (GUM 6.3.3)
XS = (math.inf, 40.0, 35.0, 30.0)  # candidate upper-end limits, in selection order (docstring)
REPRO_TOL = 1e-9            # fold_refusal's reproduction tolerance: same code on the same input, float64
PER_CELL_R = 40             # phrases per cell of round 2's design
PER_CELL_O = 40             # phrases per onset cell of round 4's design
L_SIGMAS = (0, 20)
L_SEED = 2026100273 * 10
APERIODIC_REFUSED = 13      # E-002 fold F5: tone-aperiodic.wav, 13 frames refused (squillo-lab E-005 fold_refusal checks)


def committed_first():
    """S15: refuse to run on an uncommitted edit of this file, or before it is committed."""
    me = Path(__file__).name
    a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
    b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", me], cwd=HERE)
    if a.returncode or b.returncode:
        sys.exit(f"{me} is not committed as it stands: commit the rules before running")


# ------------------------------------------------------------ the measure K

def known_parts(cents, t, states, al=None):
    """Steps 3-8: (dev, w, us) of the kept notes, and the counts."""
    states = np.asarray(states, float)
    segs, T, bad = al if al is not None else R2.align(cents, states)
    ok = [i for i, s in enumerate(segs) if s is not None and s[1] - s[0] >= 1
          and np.sum(~np.isnan(cents[s[0]:s[1]])) > 0]
    info = dict(states=len(states), found=0, wrong=0, bad=float(bad), T=float(T))
    if not ok:
        return np.zeros(0), np.zeros(0), np.zeros(0), info
    st = R2.settle_cycles(cents, t, [segs[i] for i in ok])
    keep = st[:, 1] >= R2.TRANS_S
    idx = np.array(ok)[keep]
    dev = st[keep, 0] - P * states[idx]
    w, us = st[keep, 1], st[keep, 2]
    info["found"] = int(keep.sum())
    if len(dev) == 0:
        return dev, w, us, info
    wrong = np.abs(dev - R2.wmedian(dev, w)) > R2.WRONG_NOTE
    info["wrong"] = int(wrong.sum())
    return dev[~wrong], w[~wrong], us[~wrong], info


def k_spread(dev, w, us):
    """Step 9."""
    if len(dev) < 2:
        return dict(s=math.nan, uB=math.nan, n=0.0)
    n = R2.n_eff(w)
    if n <= 1:
        return dict(s=math.nan, uB=math.nan, n=float(n))
    d = dev - np.average(dev, weights=w)
    s = math.sqrt(np.average(d ** 2, weights=w) * n / (n - 1))
    a = s / math.sqrt(2 * (n - 1))
    return dict(s=float(s), uB=float(math.hypot(a, math.sqrt(np.average(us ** 2, weights=w)))), n=float(n))


def known(cents, t, states):
    dev, w, us, info = known_parts(cents, t, states)
    sp = k_spread(dev, w, us)
    sp.update(info)
    return sp, (dev, w, us)


def state(sp, X):
    if not np.isfinite(sp["s"]):
        return "too few"
    return "measured" if sp["s"] + 2 * sp["uB"] <= X else "at least"


def excludes(sp, truth, X):
    st = state(sp, X)
    if st == "measured":
        return abs(sp["s"] - truth) > 2 * sp["uB"]
    if st == "at least":
        return sp["s"] - 2 * sp["uB"] > truth
    return False


def compare(a, b, X):
    """+1 b (later) better, -1 worse, 0 no change shown (docstring, B2)."""
    sa, sb = state(a, X), state(b, X)
    if sa == "measured" and sb == "measured":
        d = a["s"] - b["s"]
        return int(np.sign(d)) if abs(d) > 2 * math.hypot(a["uB"], b["uB"]) else 0
    if sb == "measured" and sa == "at least" and b["s"] + 2 * b["uB"] < a["s"] - 2 * a["uB"]:
        return 1
    if sa == "measured" and sb == "at least" and a["s"] + 2 * a["uB"] < b["s"] - 2 * b["uB"]:
        return -1
    return 0


# ------------------------------------------------------------ jobs

def jobs():
    import round3 as R3
    import round4 as R4
    out = []
    for j in FR.jobs_cut(PER_CELL_R):
        v, sc, sg, vib, L, seed = j
        out.append(dict(src="R", voice=v, scale=sc, sigma=sg, vib=vib, n_notes=L, seed=seed))
    count = {}
    for j in R4.jobs_synth():
        v, sc, sg, vname, ext, L, seed = j
        if vname == "onset" and ext == 50.0:
            k = (L, sg)
            count[k] = count.get(k, 0) + 1
            if count[k] <= PER_CELL_O:
                out.append(dict(src="O", voice=v, scale=sc, sigma=sg, vib="onset50", n_notes=L, seed=seed))
    seed = L_SEED
    for i, (pid, _, _) in enumerate(R3.items()):
        for sg in L_SIGMAS:
            for vib in (0, 1):
                seed += 1
                out.append(dict(src="L", item=pid, sigma=sg, vib=vib, seed=seed,
                                voice=run.VOICES[(i + sg // 10 + vib) % 6]))
    assert len(out) == 1680 + 240 + 120, len(out)
    return out


def make(job):
    """The phrase: (x, written states, sigma's draws)."""
    if job["src"] == "R":
        x, tr = R2.phrase(job["voice"], job["scale"], job["sigma"], job["vib"], job["n_notes"], job["seed"])
    elif job["src"] == "O":
        import round4 as R4
        x, tr = R4.phrase4(job["voice"], job["scale"], job["sigma"], 50.0, "onset", job["n_notes"], job["seed"])
    else:
        import round3 as R3
        x, tr = R3.make(dict(source="library", item=job["item"], sigma=job["sigma"], vib=job["vib"],
                             seed=job["seed"], voice=job["voice"]))
    states, _ = R2.merge_repeats(tr["notes"])
    e = np.asarray(tr["e"], float)
    w = np.asarray(tr["durs"], float)
    realised = float(np.sqrt(np.average((e - np.average(e, weights=w)) ** 2, weights=w)))
    return x, states, realised


def one(job):
    x, states, realised = make(job)
    t, c0, dmin = run.track(x)
    voiced = ~np.isnan(c0)
    c1 = c0.copy()
    c1[voiced & (dmin >= REFUSE)] = np.nan
    row = dict(job, realised=realised, frames_measured=int(voiced.sum()),
               frames_refused=int((voiced & (dmin >= REFUSE)).sum()))
    if job["src"] == "R":
        row["off"] = known(c0, t, states)[0]
    row["on"] = known(c1, t, states)[0]
    row["wrapped"] = FR.measure(c1, t)[0]
    return row


def run_synth(procs="18"):
    committed_first()
    procs = int(procs)
    path = CACHE / "r5_synth.pkl"
    rows = pickle.load(open(path, "rb")) if path.exists() else []
    done = {(r["src"], r["seed"]) for r in rows}
    todo = [j for j in jobs() if (j["src"], j["seed"]) not in done]
    t0 = time.time()
    with Pool(procs) as p:
        for k, r in enumerate(p.imap_unordered(one, todo, chunksize=2), 1):
            rows.append(r)
            if k % 100 == 0 or k == len(todo):
                pickle.dump(rows, open(path, "wb"))
                print(f"{len(rows)} phrases, {round((time.time() - t0) / 60, 1)} min", flush=True)


def time_sample(n="36", procs="18"):
    """S19: n jobs spread over every source and the extremes (56 notes, sigma 40, vibrato;
    onset; library), on the pool, each to its end."""
    committed_first()
    n, procs = int(n), int(procs)
    J = jobs()
    pick = []
    for sg in (0, 40):
        for vib in (0, 1):
            pick += [j for j in J if j["src"] == "R" and j["n_notes"] == 56 and j["sigma"] == sg and j["vib"] == vib][: n // 12]
    pick += [j for j in J if j["src"] == "O"][:: 240 // (n // 3)][: n // 3]
    pick += [j for j in J if j["src"] == "L"][:: 120 // (n // 3)][: n // 3]
    t0 = time.time()
    with Pool(procs) as p:
        rows = p.map(one, pick, chunksize=1)
    dt = time.time() - t0
    assert len(rows) == len(pick)
    R = sum(1 for j in J if j["src"] == "R")
    print(f"{len(pick)} jobs on {procs} processes: {dt:.1f} s, {dt / len(pick):.3f} s each; "
          f"all {len(J)} est. {dt / len(pick) * len(J) / 60:.1f} min (R alone {R})")


# ------------------------------------------------------------ real voices

def one_real(args):
    kind, path = args
    import soundfile as sf
    from scipy.signal import resample_poly
    name = Path(path).stem
    states, _ = R2.merge_repeats(R2.score_of(name))
    if kind == "resynth":
        x = np.load(path)["y"].astype(np.float32)
    else:
        x, sr = sf.read(path, dtype="float64")
        if x.ndim > 1:
            x = x.mean(axis=1)
        g = math.gcd(R2.SR, sr)
        x = resample_poly(x, R2.SR // g, sr // g).astype(np.float32)
    t, c0, dmin = run.track(x)
    voiced = ~np.isnan(c0)
    c1 = c0.copy()
    c1[voiced & (dmin >= REFUSE)] = np.nan
    sp, (dev, w, us) = known(c1, t, states)
    h = len(dev) // 2
    halves = [k_spread(dev[:h], w[:h], us[:h]), k_spread(dev[h:], w[h:], us[h:])]
    return dict(kind=kind, name=name, on=sp, halves=halves, wrapped=FR.measure(c1, t)[0],
                frames_measured=int(voiced.sum()), frames_refused=int((voiced & (dmin >= REFUSE)).sum()))


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
    pickle.dump(rows, open(CACHE / "r5_real.pkl", "wb"))
    print(len(rows), "real takes")


# ------------------------------------------------------------ checks (S15)

def ref_align(x, p, Ts):
    """c2: an independent statement of step 5: for each T the full cost matrix by plain loops,
    total cost D[last, last]; T the first least; path by backtracking, staying on a tie."""
    best = None
    for T in Ts:
        N, J = len(x), len(p)
        C = [[min(abs(x[i] - p[j] - T), 300.0) for j in range(J)] for i in range(N)]
        D = [[math.inf] * J for _ in range(N)]
        D[0][0] = C[0][0]
        for i in range(1, N):
            for j in range(J):
                stay = D[i - 1][j]
                move = D[i - 1][j - 1] if j > 0 else math.inf
                D[i][j] = C[i][j] + min(stay, move)
        if best is None or D[N - 1][J - 1] < best[0]:
            best = (D[N - 1][J - 1], T, D)
    cost, T, D = best
    N, J = len(x), len(p)
    path = [0] * N
    j = J - 1
    for i in range(N - 1, -1, -1):
        path[i] = j
        if i > 0 and j > 0 and D[i - 1][j - 1] < D[i - 1][j]:
            j -= 1
    return np.array(path), float(T), float(cost)


def dtw_cost(x, p, path, T):
    return float(np.sum(np.minimum(np.abs(x - p[path] - T), 300.0)))


def check():
    committed_first()
    out = {}
    cache = pickle.load(open(CACHE / "r2_synth.pkl", "rb"))
    by_seed = {r["seed"]: r for r in cache}
    # c1: four phrases, K without the refusal against round 2's cache
    picks = [j for j in FR.jobs_cut(1) if j[4] == 14 and j[2] in (0, 30)]
    assert len(picks) == 4
    pas, fail = [], []
    for v, sc, sg, vib, L, seed in picks:
        x, tr = R2.phrase(v, sc, sg, vib, L, seed)
        t, c0, _ = run.track(x)
        states, _ = R2.merge_repeats(tr["notes"])
        sp = known(c0, t, states)[0]
        for lst, ref in ((pas, by_seed[seed]["known"]), (fail, by_seed[seed + 1]["known"])):
            lst.append(abs(sp["s"] - ref["s"]) <= REPRO_TOL and abs(sp["uB"] - ref["uB"]) <= REPRO_TOL)
    out["c1_reproduces_round2"] = dict(must_pass=[sum(pas), len(pas)], must_fail_next_phrase=[sum(fail), len(fail)])
    assert all(pas) and not any(fail), out["c1_reproduces_round2"]
    # c2: alignment against the independent reference
    rng = np.random.default_rng(73)
    ok_pass, ok_fail = [], []
    for case in range(20):
        J = int(rng.integers(3, 7))
        p = P * np.cumsum(rng.integers(-3, 4, J)).astype(float)
        lens = rng.integers(2, 6, J)
        x = np.concatenate([np.full(n, p[j]) for j, n in enumerate(lens)]) + rng.normal(0, 20, lens.sum()) + 37.0
        Ts = 37.0 + P * np.arange(-3, 4)
        pa, Ta, _ = R2.dtw_T(x, p, Ts)
        pr, Tr, cr = ref_align(x, p, Ts)
        ok_pass.append(bool(np.array_equal(pa, pr) and Ta == Tr and abs(dtw_cost(x, p, pa, Ta) - cr) <= 1e-9 * max(1.0, cr)))
        q = p.copy()
        q[J // 2] += P  # the reference given one state a semitone off
        pq, Tq, cq = ref_align(x, q, Ts)
        ok_fail.append(bool(np.array_equal(pa, pq) and Ta == Tq and abs(dtw_cost(x, p, pa, Ta) - cq) <= 1e-9 * max(1.0, cq)))
    out["c2_alignment_reference"] = dict(must_pass=[sum(ok_pass), 20], must_fail_state_off=[sum(ok_fail), 20])
    assert all(ok_pass) and not any(ok_fail), out["c2_alignment_reference"]
    # c3: the refusal
    import soundfile as sf
    xa, _ = sf.read(SQ / "fixtures" / "metrics" / "tone-aperiodic.wav", dtype="float32")
    t, c0, dmin = run.track(xa)
    v = ~np.isnan(c0)
    n02, n2 = int((v & (dmin >= REFUSE)).sum()), int((v & (dmin >= 10 * REFUSE)).sum())
    out["c3_refusal"] = dict(must_pass_refused=n02, expected=APERIODIC_REFUSED, must_fail_threshold_0p2=n2)
    assert n02 == APERIODIC_REFUSED and n2 != APERIODIC_REFUSED, out["c3_refusal"]
    # c4: bar B1 on round 2's cached values
    def worst(rows, getsp, X):
        cells = {}
        for r in rows:
            cells.setdefault((r["n_notes"], r["vib"], r["sigma"]), []).append(excludes(getsp(r), float(r["sigma"]), X))
        return max(100.0 * sum(v) / len(v) for v in cells.values())
    wp = worst([r for r in cache if r["sigma"] <= 30], lambda r: r["known"], math.inf)
    wf = worst([r for r in cache if r["sigma"] == 40 and np.isfinite(r["cyc"]["s"])], lambda r: r["cyc"], math.inf)
    out["c4_bar"] = dict(must_pass_worst_percent=round(wp, 2), must_fail_worst_percent=round(wf, 2), bar=BAR_MISS)
    assert wp <= BAR_MISS < wf, out["c4_bar"]
    # c5: the comparison
    a = cache[0]["known"]
    lo = dict(s=a["s"] + 3 * 2 * math.hypot(a["uB"], a["uB"]), uB=a["uB"])  # earlier wider: later a improved
    out["c5_compare"] = dict(must_pass_self=compare(a, a, math.inf), must_fail_lowered=compare(lo, a, math.inf))
    assert out["c5_compare"]["must_pass_self"] == 0 and out["c5_compare"]["must_fail_lowered"] == 1, out["c5_compare"]
    json.dump(out, open(OUT / "round5_checks.json", "w"), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float))


# ------------------------------------------------------------ report

def wilson(k, n):
    return FR.wilson(k, n)


def cells_of(rows):
    c = {}
    for r in rows:
        if r["src"] == "L":
            key = f"L sigma={r['sigma']} vib={r['vib']}"
        else:
            key = f"{r['src']} L={r['n_notes']} vib={r['vib']} sigma={r['sigma']}"
        c.setdefault(key, []).append(r)
    for v in c.values():
        v.sort(key=lambda r: r["seed"])
    return c


def report():
    committed_first()
    rows = pickle.load(open(CACHE / "r5_synth.pkl", "rb"))
    real = pickle.load(open(CACHE / "r5_real.pkl", "rb"))
    r2c = {r["seed"]: r for r in pickle.load(open(CACHE / "r2_synth.pkl", "rb"))}
    r2real = pickle.load(open(CACHE / "r2_real.pkl", "rb"))
    assert len(rows) == 2040 and len({(r["src"], r["seed"]) for r in rows}) == 2040
    assert len(real) == 117
    out = dict(conditions=dict(refuse_at=REFUSE, bar_percent=BAR_MISS, candidates=[str(x) for x in XS],
                               phrases={s: sum(r["src"] == s for r in rows) for s in "ROL"}))
    # c1 on every R phrase
    R = [r for r in rows if r["src"] == "R"]
    def same(a, b, both_missing=True):
        if not np.isfinite(b["s"]) or not np.isfinite(a["s"]):
            return both_missing and not np.isfinite(a["s"]) and not np.isfinite(b["s"])
        return abs(a["s"] - b["s"]) <= REPRO_TOL and abs(a["uB"] - b["uB"]) <= REPRO_TOL
    out["c1_check_all"] = dict(must_pass=[sum(same(r["off"], r2c[r["seed"]]["known"]) for r in R), len(R)],
                               must_fail_next=[sum(same(r["off"], r2c[r["seed"] + 1]["known"], False) for r in R if r["seed"] + 1 in r2c), len(R)])
    assert out["c1_check_all"]["must_pass"][0] == len(R) and out["c1_check_all"]["must_fail_next"][0] == 0
    fm = sum(r["frames_measured"] for r in rows)
    out["frames_refused_percent"] = round(100 * sum(r["frames_refused"] for r in rows) / fm, 2)
    cl = cells_of(rows)
    # B1 per candidate
    b1 = {}
    for X in XS:
        per = {}
        for key, rs in sorted(cl.items()):
            k = sum(excludes(r["on"], float(r["sigma"]), X) for r in rs)
            per[key] = dict(miss=wilson(k, len(rs)), measured=sum(state(r["on"], X) == "measured" for r in rs),
                            at_least=sum(state(r["on"], X) == "at least" for r in rs),
                            too_few=sum(state(r["on"], X) == "too few" for r in rs))
        worst = max(per.items(), key=lambda kv: kv[1]["miss"][0])
        b1[str(X)] = dict(passes=all(v["miss"][0] <= BAR_MISS for v in per.values()), worst=[worst[0], worst[1]["miss"]],
                          measured=sum(v["measured"] for v in per.values()), cells=per)
    out["B1"] = b1
    sel = next((X for X in XS if b1[str(X)]["passes"]), None)
    out["selected"] = str(sel) if sel is not None else None
    Xs = sel if sel is not None else math.inf
    # without the refusal, for comparison: K always measured
    out["B1_off_inf_worst"] = max(((key, wilson(sum(excludes(r["off"], float(r["sigma"]), math.inf) for r in rs), len(rs)))
                                   for key, rs in cl.items() if key.startswith("R")), key=lambda kv: kv[1][0])
    # lower end and realised
    rep = [r for r in rows if state(r["on"], Xs) != "too few"]
    out["lower_end_holds"] = wilson(sum(r["on"]["s"] - 2 * r["on"]["uB"] <= r["sigma"] for r in rep), len(rep))
    meas = [r for r in rows if state(r["on"], Xs) == "measured"]
    out["measured_covers_realised"] = wilson(sum(abs(r["on"]["s"] - r["realised"]) <= 2 * r["on"]["uB"] for r in meas), len(meas))
    out["uB_median_by_cell"] = {k: round(float(np.median([r["on"]["uB"] for r in rs if np.isfinite(r["on"]["uB"])])), 2) for k, rs in sorted(cl.items())}
    out["states_found"] = dict(every_state=sum(r["on"]["found"] == r["on"]["states"] for r in rows), of=len(rows),
                               wrong_notes=sum(r["on"]["wrong"] for r in rows),
                               every_state_by_src={s: [sum(r["on"]["found"] == r["on"]["states"] for r in rows if r["src"] == s),
                                                       sum(r["src"] == s for r in rows)] for s in "ROL"})
    # B2 and power on R
    fc, pw = {}, {}
    for L in R2.LENGTHS:
        for vib in (0, 1):
            calls = []
            for sg in R2.SIGMAS:
                rs = cl[f"R L={L} vib={vib} sigma={sg}"]
                calls += [compare(rs[2 * i]["on"], rs[2 * i + 1]["on"], Xs) != 0 for i in range(len(rs) // 2)]
            fc[f"L={L} vib={vib}"] = wilson(sum(calls), len(calls))
            for a, b in ((20, 0), (40, 10)):
                A, B = cl[f"R L={L} vib={vib} sigma={a}"], cl[f"R L={L} vib={vib} sigma={b}"]
                rk = [compare(x["on"], y["on"], Xs) for x, y in zip(A, B)]
                rw = [FR.compare(x["wrapped"], y["wrapped"]) for x, y in zip(A, B)]
                pw[f"L={L} vib={vib} {a}->{b}"] = dict(known_improved=wilson(sum(v == 1 for v in rk), len(rk)),
                                                       known_worse=sum(v == -1 for v in rk),
                                                       wrapped_improved=wilson(sum(v == 1 for v in rw), len(rw)))
    out["B2_false_change"] = dict(cells=fc, passes=all(v[0] <= BAR_MISS for v in fc.values()))
    out["power"] = pw
    # real
    truth = {r["name"]: r["truth"] for r in r2real["resynth"]}
    rr = {}
    for kind, sets in (("resynth", ("scales_straight", "row_vibrato")),
                       ("original", ("scales_straight", "row_straight", "scales_vibrato", "row_vibrato"))):
        for S in sets:
            b = [r for r in real if r["kind"] == kind and S in r["name"]]
            d = dict(takes=len(b), frames_refused_percent=round(100 * sum(r["frames_refused"] for r in b) / sum(r["frames_measured"] for r in b), 2),
                     measured=sum(state(r["on"], Xs) == "measured" for r in b), at_least=sum(state(r["on"], Xs) == "at least" for r in b),
                     too_few=sum(state(r["on"], Xs) == "too few" for r in b),
                     K_median=round(float(np.median([r["on"]["s"] for r in b if np.isfinite(r["on"]["s"])])), 2),
                     uB_median=round(float(np.median([r["on"]["uB"] for r in b if np.isfinite(r["on"]["uB"])])), 2),
                     every_state_found=sum(r["on"]["found"] == r["on"]["states"] for r in b),
                     wrong_notes=sum(r["on"]["wrong"] for r in b),
                     wrapped_measured=sum(FR.state(r["wrapped"]) == "measured" for r in b))
            if kind == "resynth":
                full = [r for r in b if truth[r["name"]]["found"] == truth[r["name"]]["states"]]
                d["truth_every_state"] = len(full)
                d["miss_on_full_truth"] = wilson(sum(excludes(r["on"], truth[r["name"]]["sd"], Xs) for r in full), len(full))
            else:
                hv = [compare(r["halves"][0], r["halves"][1], Xs) != 0 for r in b]
                d["halves_false_change"] = [int(sum(hv)), len(hv)]
            rr[f"{kind} {S}"] = d
    out["real"] = rr
    out["B3_passes"] = all(v["miss_on_full_truth"][0] <= BAR_MISS for k, v in rr.items() if k.startswith("resynth"))
    json.dump(out, open(OUT / "round5.json", "w"), indent=1, default=float)
    print(json.dumps({k: v for k, v in out.items() if k not in ("B1", "uB_median_by_cell", "power")}, indent=1, default=float))
    print(json.dumps({X: {k: v for k, v in b.items() if k != "cells"} for X, b in b1.items()}, indent=1, default=float))
    print(json.dumps(pw, indent=1, default=float))


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    dict(check=check, time=time_sample, synth=run_synth, real=run_real, report=report)[cmd](*args)
