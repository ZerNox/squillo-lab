"""E-005 round 6 (squillo iteration 76, F-045): a centring rung for a library phrase.

Crude experiment code. Rounds 1-5 and the folds stay unchanged; this file adds,
never replaces. It imports round 3's generator, known path, truth and rung, and
round 5's measure K (squillo MT-014 as folded in iteration 74).

    uv run python round6.py check           # the checks, each checked (S15) -> results/round6_checks.json
    uv run python round6.py time 24 18      # S19 sample on the pool, after the rules commit
    uv run python round6.py fresh 18        # 720 fresh held-out phrases -> data/cache/r6_fresh.pkl (saves every 100, resumes)
    uv run python round6.py analyse 18      # every phrase x gate x strength -> data/cache/r6_rows.pkl
    uv run python round6.py world 18        # WORLD re-syntheses of the rung -> data/cache/r6_world.pkl
    uv run python round6.py report          # -> results/round6.json

QUESTION (squillo R-15 section 8, iteration 76; F-045). Only `steadiness` has a
ladder, so a take with no held note has no far vision. Round 3 found, for a
library phrase, an honest per-note distance from the written note on the
singer's own tuning (d, u = settle u (+) K / sqrt(n_e), R3-2), but no gate safe
in every cell (|d| + 2u <= 20 failed one held-out cell, R3-3) and a centred
rung never called improved by the take's wrapped spread (R3-4). Round 5 and
squillo MT-014 now give a library phrase a spread about its written notes (K),
two to three times as powerful. Does a centring rung for a library phrase, built
from MT-014's own deviations, (1) get called improved by MT-014 and MT-008, on how
many synthetic phrases and real re-syntheses, (2) at the cost of how many notes
moved the wrong way, per cell, (3) at which weakest strength, and (4) does a
WORLD re-synthesis of it deliver what its description claims?

THE TAKE'S MEASURE: round5.known on the take's measured pitch (MT-003's refusal
on), the written states merged (K1 to K9); its state at X = 40 (MT-014,
round5.state). Per kept note (round3.known_path, which K reproduces: check k1):
d = its deviation minus the tuning, u = hypot(settle u, K / sqrt(n_e)) (round 3's
P2, the candidate R3-2 selected), w its duration.

THE RUNG for gate T: a kept, not wrong note is MOVED when |d| > 2u (measurably off
its written note on the singer's tuning) and |d| + 2u <= T. Strength k / 64,
k = 1 .. 64 (squillo ADR 0018's grid): each moved note's segment shifted by
m = -clip(k / 64 * d, +-50) cents (SY-002's bound), every other frame unchanged
(round3.rung_cents). The rung is MEASURED FROM ITS DESCRIPTION (squillo CO-003,
SY-004): round5.known recomputed on the shifted contour, the take's own frames,
alignment run again. It is CALLED IMPROVED when round5.compare(take, rung, 40) = +1
(MT-008 in MT-014's states). REACHABLE strengths: those called improved; the next
step the weakest, the far vision the strongest (squillo CO-004's rule).
GATES, in order: T = 20 (round 3's), 15, 10: each at least as safe as round 3's,
since a note moved under T = 15 or 10 is moved under 20.

TRUTH: per kept state, delta = its realised centre minus its aim on the singer's
realised tuning, from round 3's truth (truth_synth for synthetic phrases,
truth_resynth for E-002's re-syntheses; round3.known_records' column 2, matched by
state index). A moved note is HARMED when |delta + m| > |delta| at full strength
(round 3's B2 definition). Harm at a strength s < 1 implies harm at 1 (the move
points the same way and is shorter), so full strength is the strictest. The rung's
improvement is TRUE when the weighted SD of (delta + m) over the kept notes with
a truth, at the far vision's strength, is below the weighted SD of delta.

INPUTS, conditions written before generating (S15 C1, C2):
  - SELECTION set: round 3's 1680 cached phrases (data/cache/r3_synth.pkl), both
    halves: 960 random phrases (14, 28 notes) and 720 renderings of E-004 fold 2's
    30 library items, sigma 0, 10, 20, 30, straight or 5.5 Hz +-50 cents faded in;
    every contour asserted inside E2..C6 by round3.render (round3.py:248-250,
    R2.contour_ok). Round 3's T = 20 result on its held-out half is already known,
    so this set selects and never judges.
  - FRESH held-out set: round 3's generator (round3.make, round3.one) under new
    seeds (base FRESH_SEED), PER_CELL_FRESH = 30 random phrases per cell
    (2 lengths x 4 sigma x 2 vibrato x 30 = 480) and each library item once per
    sigma x vibrato (30 x 8 = 240): 720 phrases, the same asserts.
  - REAL: round 3's cached rows (r3_real.pkl): E-002's 40 WORLD re-syntheses of
    VocalSet (20 straight scales, 20 vibrato rounds) with their truth, and 77
    VocalSet originals (no truth; reported only).
  Cells: (source, sigma, vibrato), 24; real by set.

BARS, written before the run:
  B2 harm: in every cell with >= MIN_CELL (20) moved notes, at most B2_MAX
     (2.5 %) of moved notes harmed (round 3's B2).
  Selection: the first gate in order that passes B2 on the SELECTION set. None
     passing: no gate is safe, and the rung is reported only as a diagnostic
     under T = 20.
  B2 held out: the selected gate on the FRESH set, every judged cell; and on the
     real re-syntheses, per set with >= 20 moved notes.
  B4 honesty of "improved": of the FRESH phrases whose far vision is called
     improved under the selected gate, the improvement is not true in at most
     BAR_MISS (5 %, GUM 6.3.3 at k = 2), pooled, and in every cell with >= 20
     such phrases; on the real re-syntheses whose truth found every state,
     reported.
  Reported with no bar: per cell, the phrases with a reachable rung, the
     next step's and far vision's strengths (median, range), moved notes per
     phrase, K before and after; the same for the selection set and every
     gate (labelled diagnostic); real takes.
  W, WORLD delivery (no bar): on WORLD_PER_CELL fresh phrases per cell that have
     a far vision under the selected gate (or T = 20 when none is selected) and on
     the 40 E-002 re-syntheses (their far vision, else full strength with the
     gate's moves, else no move), WORLD (pyworld 0.3.5; E-001 run.py:79's Harvest
     settings, 60-1100 Hz, 5 ms; CheapTrick, D4C) re-synthesizes the take unchanged
     (identity) and with each moved segment's f0 times 2^(m / 1200) over its time
     span. Both are tracked (MT-003 refusal on) and measured by round5.known.
     Reported: K from the rung's samples against K from its description; the
     identity's K against the take's; per moved note, the achieved shift (rung
     samples' centre minus identity's) minus the requested m; whether
     compare(take, rung samples) agrees with the description's call.

CHECKS (S15), each with a must-pass and a must-fail case whose input differs:
  k1 the measure: round5.known's (s, uB) on a cached take equals round3.known_path's
     sp within REPRO_TOL (same code path, float64) on 4 phrases; must fail against
     the next phrase's.
  k2 the rung's description: round5.known on round3.rung_cents with every kept
     note moved by -d (strength 1, no gate) is K = 0 within ZERO_TOL on a phrase
     whose alignment is unchanged; must fail with the moves reversed (+d).
  k3 bar B2 on reference moves (12 selection phrases, random14, sigma 10,
     straight): m = -delta on every kept note harms 0; m = +delta harms all.
  k4 bar B4 on reference rungs (the same 12): m = -delta, every true; m = +delta,
     none true.
  k5 the fresh generator: round3.one on round 3's own first job reproduces its
     cached contour exactly (array_equal, NaN as NaN); must fail against round 3's
     second job's contour.
  k6 truth matched by state: every selection phrase's recomputed kept-state indices
     equal round 3's cached column 5; must fail with the indices shifted by one.
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
import warnings
from multiprocessing import Pool
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore", category=UserWarning, module="pyworld")

import run
import round2 as R2
import round3 as R3
import round5 as R5
import fold_refusal as FR

HERE = Path(__file__).parent
CACHE = HERE / "data" / "cache"
OUT = HERE / "results"
SR = R2.SR
X_CAP = 40.0                # squillo MT-014's upper end for measured (ADR 0015, Q-040 part 2)
GATES = (20.0, 15.0, 10.0)  # round 3's T = 20, then stricter (docstring)
GRID = 64                   # squillo ADR 0018: strengths k / 64
CLIP = R3.CLIP              # squillo SY-002: |change| <= 50 cents
B2_MAX = R3.B2_MAX          # round 3: 2.5 %, one tail
MIN_CELL = R3.MIN_CELL      # round 3: 20 moved notes for a cell to be judged
BAR_MISS = FR.BAR           # 5 %, GUM 6.3.3 at k = 2
REPRO_TOL = R5.REPRO_TOL    # round 5: same code on the same input, float64
ZERO_TOL = 1e-6             # cents: K of notes all shifted onto their written notes; float64 sums over <= 60 notes of values <= 3000 cents
PER_CELL_FRESH = 30
FRESH_SEED = 2026100276 * 10
WORLD_PER_CELL = 2
F0_FLOOR, F0_CEIL, FP = 60.0, 1100.0, 5.0   # E-001 run.py:79


def committed_first():
    """S15 C15: refuse to run on an uncommitted edit of this file or of any module it imports."""
    me = Path(__file__).name
    a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
    mods = [me, "run.py", "round2.py", "round3.py", "round5.py", "fold_refusal.py", "infer.py", "synth.py"]
    b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", *mods], cwd=HERE)
    if a.returncode or b.returncode:
        sys.exit(f"{me} or a module it imports is not committed as it stands: commit the rules before running")


# ------------------------------------------------------------ the take, the moves, the rung

def take_of(cents, t, states):
    """The take's K (MT-014) and round 3's per-note path; None when no note is kept."""
    sp = R5.known(cents, t, states)[0]
    kp = R3.known_path(cents, t, states)
    return sp, kp


def moved_mask(kp, T):
    if kp is None or not np.isfinite(kp["sp"]["s"]):
        return None
    u = np.hypot(kp["us"], kp["u_ref"])
    return ~kp["wrong"] & (np.abs(kp["d"]) > 2 * u) & (np.abs(kp["d"]) + 2 * u <= T)


def moves_at(kp, mask, k):
    return np.where(mask, -np.clip(k / GRID * kp["d"], -CLIP, CLIP), 0.0)


def rung_sp(cents, t, states, kp, m):
    return R5.known(R3.rung_cents(cents, kp["segs"], m), t, states)[0]


def truth_of(kp, rec):
    """delta per kept state of kp, from round 3's records (column 5 the state, column 2 delta)."""
    by = {int(j): dl for j, dl in zip(rec[:, 5], rec[:, 2])} if len(rec) else {}
    return np.array([by.get(int(j), np.nan) for j in kp["idx"]])


def wsd(x, w):
    if len(x) < 2:
        return math.nan
    mu = np.average(x, weights=w)
    return float(math.sqrt(np.average((x - mu) ** 2, weights=w)))


def analyse_one(row):
    """Per gate: moves, harm, every strength's call, truth of the far vision."""
    t, cents, states = row["t"].astype(float), row["cents"].astype(float), np.asarray(row["states"], float)
    sp, kp = take_of(cents, t, states)
    out = dict(key=row.get("key"), set=row.get("set"), source=row.get("source"), sigma=row.get("sigma", -1),
               vib=row.get("vib", -1), all_found=row.get("all_found"), take=sp, take_state=R5.state(sp, X_CAP), gates={})
    if kp is None:
        return out
    rec = row.get("known")
    dl = truth_of(kp, rec) if rec is not None else np.full(len(kp["idx"]), np.nan)
    kept = ~kp["wrong"]
    out["kept"] = int(kept.sum())
    prev = None
    for T in GATES:
        mask = moved_mask(kp, T)
        if mask is None:
            out["gates"][str(T)] = dict(moved=0, harmed=0, reach=[], note="take K has no value")
            continue
        g = dict(moved=int(mask.sum()))
        m1 = moves_at(kp, mask, GRID)
        h = mask & np.isfinite(dl) & (np.abs(dl + m1) > np.abs(dl))
        g["harmed"] = int(h.sum())
        g["moved_with_truth"] = int((mask & np.isfinite(dl)).sum())
        if prev is not None and np.array_equal(mask, prev[0]):
            g.update({k: v for k, v in prev[1].items() if k not in g})
            out["gates"][str(T)] = g
            continue
        reach, ks = [], {}
        if mask.any():
            for k in range(1, GRID + 1):
                r = rung_sp(cents, t, states, kp, moves_at(kp, mask, k))
                c = R5.compare(sp, r, X_CAP)
                if c == 1:
                    reach.append(k)
                if k in (GRID // 4, GRID // 2, GRID) or c == 1:
                    ks[k] = dict(s=r["s"], uB=r["uB"], call=c, state=R5.state(r, X_CAP))
                if c == -1:
                    g["worse_at"] = g.get("worse_at", []) + [k]
        g["reach"] = reach
        g["rungs"] = ks
        if reach:
            kf = reach[-1]
            mf = moves_at(kp, mask, kf)
            ok = kept & np.isfinite(dl)
            g["true_take"] = wsd(dl[ok], kp["dur"][ok])
            g["true_rung"] = wsd((dl + mf)[ok], kp["dur"][ok])
            g["true"] = bool(g["true_rung"] < g["true_take"]) if np.isfinite(g["true_take"]) else None
            dk = np.where(mask, kp["d"], np.nan)
            g["moved_d"] = [float(v) for v in dk[mask]]
        out["gates"][str(T)] = g
        prev = (mask, {k: v for k, v in g.items() if k not in ("moved", "harmed", "moved_with_truth")})
    return out


# ------------------------------------------------------------ inputs

def fresh_jobs():
    out = []
    seed = FRESH_SEED
    for n_notes in R3.LENGTHS:
        for sigma in R3.SIGMAS:
            for vib in (0, 1):
                for k in range(PER_CELL_FRESH):
                    seed += 1
                    out.append(dict(source=f"random{n_notes}", sigma=sigma, vib=vib, seed=seed,
                                    voice=run.VOICES[k % 6], scale=run.SCALE_NAMES[(k // 6) % 5], n_notes=n_notes))
    for i, (pid, _, _) in enumerate(R3.items()):
        for sigma in R3.SIGMAS:
            for vib in (0, 1):
                seed += 1
                out.append(dict(source="library", sigma=sigma, vib=vib, seed=seed, item=pid,
                                voice=run.VOICES[(i + sigma // 10 + vib) % 6]))
    assert len(out) == 720, len(out)
    return out


def run_fresh(procs="18"):
    committed_first()
    path = CACHE / "r6_fresh.pkl"
    rows = pickle.load(open(path, "rb")) if path.exists() else []
    done = {r["seed"] for r in rows}
    todo = [j for j in fresh_jobs() if j["seed"] not in done]
    t0 = time.time()
    with Pool(int(procs)) as p:
        for k, r in enumerate(p.imap_unordered(R3.one, todo, chunksize=2), 1):
            rows.append(r)
            if k % 100 == 0 or k == len(todo):
                pickle.dump(rows, open(path, "wb"))
                print(f"{len(rows)} fresh phrases, {round((time.time() - t0) / 60, 1)} min", flush=True)


def keyed(rows, tag):
    for r in rows:
        r["key"] = f"{tag}:{r.get('seed', r.get('name'))}"
    return rows


def run_analyse(procs="18"):
    committed_first()
    sel = keyed(pickle.load(open(CACHE / "r3_synth.pkl", "rb")), "sel")
    fr = keyed(pickle.load(open(CACHE / "r6_fresh.pkl", "rb")), "fresh")
    real = keyed(pickle.load(open(CACHE / "r3_real.pkl", "rb")), "real")
    assert len(sel) == 1680 and len(fr) == 720 and len(real) == 117
    t0 = time.time()
    with Pool(int(procs)) as p:
        rows = p.map(analyse_one, sel + fr + real, chunksize=4)
    pickle.dump(rows, open(CACHE / "r6_rows.pkl", "wb"))
    print(f"{len(rows)} rows, {round((time.time() - t0) / 60, 1)} min")


def time_sample(n="24", procs="18"):
    """S19: n fresh jobs over the extremes (28 notes, library; sigma 0 and 30; vibrato and not),
    generated and analysed to their end on the pool; then WORLD on n // 4 of them."""
    committed_first()
    n, procs = int(n), int(procs)
    J = fresh_jobs()
    pick = []
    for src in ("random28", "library", "random14"):
        for sg in (0, 30):
            for vib in (0, 1):
                pick += [j for j in J if j["source"] == src and j["sigma"] == sg and j["vib"] == vib][: max(1, n // 12)]
    pick = pick[:n]
    t0 = time.time()
    with Pool(procs) as p:
        rows = p.map(R3.one, pick, chunksize=1)
    tg = time.time() - t0
    keyed(rows, "fresh")
    t0 = time.time()
    with Pool(procs) as p:
        an = p.map(analyse_one, rows, chunksize=1)
    ta = time.time() - t0
    wj = [(r, a) for r, a in zip(rows, an)][: max(1, n // 4)]
    t0 = time.time()
    with Pool(procs) as p:
        p.map(world_one, [("fresh", r, a, "20.0") for r, a in wj], chunksize=1)
    tw = time.time() - t0
    print(f"{len(pick)} generated in {tg:.1f} s ({tg / len(pick):.3f} s each): 720 est. {tg / len(pick) * 720 / 60:.1f} min")
    print(f"{len(rows)} analysed in {ta:.1f} s ({ta / len(rows):.3f} s each): 2517 est. {ta / len(rows) * 2517 / 60:.1f} min")
    print(f"{len(wj)} WORLD in {tw:.1f} s ({tw / len(wj):.3f} s each): 88 est. {tw / len(wj) * 88 / 60:.1f} min")


# ------------------------------------------------------------ WORLD

def audio_of(src, row):
    if src == "fresh":
        x, _ = R3.make({k: row[k] for k in ("source", "sigma", "vib", "seed", "voice", "scale", "n_notes", "item") if k in row})
        return np.asarray(x, float)
    return np.load(R2.E002 / "data" / "cache" / "r2" / f"{row['name']}.npz")["y"].astype(float)


def world_one(args):
    import pyworld as pw
    src, row, an, gate = args
    t, cents, states = row["t"].astype(float), row["cents"].astype(float), np.asarray(row["states"], float)
    sp, kp = take_of(cents, t, states)
    x = audio_of(src, row)
    f0, tw = pw.harvest(x, SR, f0_floor=F0_FLOOR, f0_ceil=F0_CEIL, frame_period=FP)
    spec = pw.cheaptrick(x, f0, tw, SR)
    ap = pw.d4c(x, f0, tw, SR)
    y_id = pw.synthesize(f0, spec, ap, SR, frame_period=FP)[: len(x)]
    g = an["gates"].get(gate, {})
    mask = moved_mask(kp, float(gate))
    k = g["reach"][-1] if g.get("reach") else GRID
    m = moves_at(kp, mask, k) if mask is not None else np.zeros(0)
    c = np.zeros(len(tw))
    if mask is not None:
        for (a, b), mv in zip(kp["segs"], m):
            if mv != 0.0:
                c[(tw >= t[a]) & (tw <= t[b - 1])] = mv
    y_r = pw.synthesize(f0 * 2.0 ** (c / 1200.0), spec, ap, SR, frame_period=FP)[: len(x)]
    out = dict(key=row["key"], src=src, set=row.get("set"), source=row.get("source"), sigma=row.get("sigma"),
               vib=row.get("vib"), strength=k, reached=bool(g.get("reach")), moved=int(mask.sum()) if mask is not None else 0,
               take=sp, desc=rung_sp(cents, t, states, kp, m) if mask is not None else sp)
    meas = {}
    for name, y in (("identity", y_id), ("rung", y_r)):
        ty, cy, _, _ = FR.track(y.astype(np.float32))
        meas[name] = (ty, cy, R5.known(cy, ty, states)[0], R3.known_path(cy, ty, states))
    out["identity"], out["samples"] = meas["identity"][2], meas["rung"][2]
    out["call_desc"] = R5.compare(sp, out["desc"], X_CAP)
    out["call_samples"] = R5.compare(sp, out["samples"], X_CAP)
    ki, kr = meas["identity"][3], meas["rung"][3]
    ach = []
    if mask is not None and ki is not None and kr is not None:
        ci = {int(j): c_ for j, c_ in zip(ki["idx"], ki["centre"])}
        cr = {int(j): c_ for j, c_ in zip(kr["idx"], kr["centre"])}
        for j, mv, mk in zip(kp["idx"], m, mask):
            if mk and int(j) in ci and int(j) in cr:
                ach.append((float(mv), float(cr[int(j)] - ci[int(j)])))
    out["achieved"] = ach
    return out


def run_world(procs="18"):
    committed_first()
    sel_rows = pickle.load(open(CACHE / "r6_rows.pkl", "rb"))
    gate = _selected(sel_rows) or "20.0"
    by = {a["key"]: a for a in sel_rows}
    fr = keyed(pickle.load(open(CACHE / "r6_fresh.pkl", "rb")), "fresh")
    real = keyed(pickle.load(open(CACHE / "r3_real.pkl", "rb")), "real")
    jobs, count = [], {}
    for r in sorted(fr, key=lambda r: r["seed"]):
        a = by[r["key"]]
        cell = (r["source"], r["sigma"], r["vib"])
        if a["gates"].get(gate, {}).get("reach") and count.get(cell, 0) < WORLD_PER_CELL:
            count[cell] = count.get(cell, 0) + 1
            jobs.append(("fresh", r, a, gate))
    jobs += [("real", r, by[r["key"]], gate) for r in real if r["kind"] == "resynth"]
    t0 = time.time()
    with Pool(int(procs)) as p:
        rows = p.map(world_one, jobs, chunksize=1)
    pickle.dump(dict(gate=gate, rows=rows), open(CACHE / "r6_world.pkl", "wb"))
    print(f"{len(rows)} WORLD pairs, {round((time.time() - t0) / 60, 1)} min")


# ------------------------------------------------------------ judging

def cell_of(a):
    if a["key"].startswith("real"):
        return ("real", a["set"])
    return (a["source"], a["sigma"], a["vib"])


def b2_table(rows, gate):
    c = {}
    for a in rows:
        g = a["gates"].get(gate)
        if g is None:
            continue
        k, n = c.get(cell_of(a), (0, 0))
        c[cell_of(a)] = (k + g["harmed"], n + g.get("moved_with_truth", 0))
    tab = {str(key): dict(harmed=k, moved=n, share=FR.wilson(k, n), judged=n >= MIN_CELL,
                          passes=n < MIN_CELL or 100.0 * k / n <= B2_MAX) for key, (k, n) in sorted(c.items(), key=str)}
    return all(v["passes"] for v in tab.values()), tab


def _selected(rows):
    sel = [a for a in rows if a["key"].startswith("sel")]
    for T in GATES:
        if b2_table(sel, str(T))[0]:
            return str(T)
    return None


def b4(rows, gate):
    c = {}
    for a in rows:
        g = a["gates"].get(gate, {})
        if g.get("reach") and g.get("true") is not None:
            k, n = c.get(cell_of(a), (0, 0))
            c[cell_of(a)] = (k + (not g["true"]), n + 1)
    k = sum(v[0] for v in c.values())
    n = sum(v[1] for v in c.values())
    cells = {str(key): dict(not_true=v[0], called=v[1], share=FR.wilson(*v),
                            passes=v[1] < MIN_CELL or 100.0 * v[0] / v[1] <= BAR_MISS) for key, v in sorted(c.items(), key=str)}
    return dict(pooled=FR.wilson(k, n), not_true=k, called=n,
                passes=(n == 0 or 100.0 * k / n <= BAR_MISS) and all(v["passes"] for v in cells.values()), cells=cells)


def reach_table(rows, gate):
    c = {}
    for a in rows:
        c.setdefault(cell_of(a), []).append(a)
    out = {}
    for key, rs in sorted(c.items(), key=str):
        gs = [a["gates"].get(gate, {}) for a in rs]
        reach = [g for g in gs if g.get("reach")]
        nxt = [g["reach"][0] for g in reach]
        far = [g["reach"][-1] for g in reach]
        out[str(key)] = dict(phrases=len(rs), with_moves=sum(g.get("moved", 0) > 0 for g in gs),
                             reachable=FR.wilson(len(reach), len(rs)), reachable_n=len(reach),
                             next_step_k=[int(np.min(nxt)), int(np.median(nxt)), int(np.max(nxt))] if nxt else None,
                             far_k=[int(np.min(far)), int(np.median(far)), int(np.max(far))] if far else None,
                             contiguous=sum(g["reach"] == list(range(g["reach"][0], g["reach"][-1] + 1)) for g in reach),
                             worse_any=sum(bool(g.get("worse_at")) for g in gs),
                             moved_median=float(np.median([g.get("moved", 0) for g in gs])) if gs else 0.0,
                             take_states={s: sum(a["take_state"] == s for a in rs) for s in ("measured", "at least", "too few")})
    return out


# ------------------------------------------------------------ checks (S15)

def check():
    committed_first()
    out = {}
    cache = pickle.load(open(CACHE / "r3_synth.pkl", "rb"))
    # k1: round5.known equals round3.known_path's sp
    picks = [r for r in cache if r["source"] == "random14" and r["vib"] == 0][:4]
    ok_p, ok_f = [], []
    for i, r in enumerate(picks):
        t, c, st = r["t"].astype(float), r["cents"].astype(float), np.asarray(r["states"], float)
        sp, kp = take_of(c, t, st)
        nxt = picks[(i + 1) % 4]
        _, kq = take_of(nxt["cents"].astype(float), nxt["t"].astype(float), np.asarray(nxt["states"], float))
        for lst, ref in ((ok_p, kp["sp"]), (ok_f, kq["sp"])):
            lst.append(abs(sp["s"] - ref["s"]) <= REPRO_TOL and abs(sp["uB"] - ref["uB"]) <= REPRO_TOL)
    out["k1_measure"] = dict(must_pass=[sum(ok_p), 4], must_fail_next_phrase=[sum(ok_f), 4])
    k1 = out["k1_measure"]
    assert k1["must_pass"][0] == 4 and k1["must_fail_next_phrase"][0] == 0, k1
    # k2: the rung's description, every kept note moved onto its written note
    k2 = None
    for r in cache:
        if r["source"] != "random14" or r["sigma"] != 10 or r["vib"] != 0:
            continue
        t, c, st = r["t"].astype(float), r["cents"].astype(float), np.asarray(r["states"], float)
        sp, kp = take_of(c, t, st)
        if kp is None or kp["wrong"].any() or not np.isfinite(sp["s"]):
            continue
        rp = rung_sp(c, t, st, kp, -kp["d"])
        rf = rung_sp(c, t, st, kp, kp["d"])
        if rp["found"] == sp["found"]:
            k2 = dict(seed=r["seed"], must_pass_K=rp["s"], must_fail_K=rf["s"], take_K=sp["s"], tol=ZERO_TOL)
            break
    out["k2_description"] = k2
    assert k2 is not None, "k2: no phrase with every note kept and the alignment unchanged"
    assert out["k2_description"]["must_pass_K"] <= ZERO_TOL and out["k2_description"]["must_fail_K"] > ZERO_TOL, k2
    # k3, k4: bars B2 and B4 on reference moves
    ref = [r for r in cache if r["source"] == "random14" and r["sigma"] == 10 and r["vib"] == 0][:12]
    hp = hf = np_ = tp = tf = nt = 0
    for r in ref:
        t, c, st = r["t"].astype(float), r["cents"].astype(float), np.asarray(r["states"], float)
        _, kp = take_of(c, t, st)
        dl = truth_of(kp, r["known"])
        ok = ~kp["wrong"] & np.isfinite(dl)
        hp += int(np.sum(np.abs(dl[ok] - dl[ok]) > np.abs(dl[ok])))
        hf += int(np.sum(np.abs(dl[ok] + dl[ok]) > np.abs(dl[ok])))
        np_ += int(np.sum(ok & (dl != 0)))
        w = kp["dur"][ok]
        tt = wsd(dl[ok], w)
        tp += int(wsd(dl[ok] - dl[ok], w) < tt)
        tf += int(wsd(dl[ok] + dl[ok], w) < tt)
        nt += 1
    out["k3_B2_reference"] = dict(must_pass_harmed=hp, must_fail_harmed=hf, moved=np_)
    out["k4_B4_reference"] = dict(must_pass_true=tp, must_fail_true=tf, phrases=nt)
    k3, k4 = out["k3_B2_reference"], out["k4_B4_reference"]
    assert k3["must_pass_harmed"] == 0 and k3["must_fail_harmed"] == k3["moved"] > 0, k3
    assert k4["must_pass_true"] == k4["phrases"] == 12 and k4["must_fail_true"] == 0, k4
    # k5: the fresh generator reproduces round 3's cached contour
    j3 = R3.jobs()[:2]
    r0 = R3.one(j3[0])
    by = {r["seed"]: r for r in cache}
    same = bool(np.array_equal(r0["cents"], by[j3[0]["seed"]]["cents"], equal_nan=True))
    other = bool(np.array_equal(r0["cents"], by[j3[1]["seed"]]["cents"], equal_nan=True))
    out["k5_generator"] = dict(must_pass=same, must_fail_next_job=other)
    assert out["k5_generator"]["must_pass"] and not out["k5_generator"]["must_fail_next_job"], out["k5_generator"]
    # k6: truth matched by state index on every selection phrase
    good = shifted = n6 = 0
    for r in cache:
        _, kp = take_of(r["cents"].astype(float), r["t"].astype(float), np.asarray(r["states"], float))
        idx = [] if kp is None else [int(j) for j in kp["idx"]]
        cached = [int(j) for j in r["known"][:, 5]]
        n6 += 1
        good += idx == cached
        shifted += len(idx) > 0 and [j + 1 for j in idx] == cached
    out["k6_truth_by_state"] = dict(must_pass=[good, n6], must_fail_shifted=[shifted, n6])
    assert out["k6_truth_by_state"]["must_pass"][0] == n6 and out["k6_truth_by_state"]["must_fail_shifted"][0] == 0, out["k6_truth_by_state"]
    json.dump(out, open(OUT / "round6_checks.json", "w"), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float))


# ------------------------------------------------------------ report

def report():
    committed_first()
    rows = pickle.load(open(CACHE / "r6_rows.pkl", "rb"))
    world = pickle.load(open(CACHE / "r6_world.pkl", "rb"))
    sel = [a for a in rows if a["key"].startswith("sel")]
    fr = [a for a in rows if a["key"].startswith("fresh")]
    real = [a for a in rows if a["key"].startswith("real")]
    assert len(sel) == 1680 and len(fr) == 720 and len(real) == 117
    out = dict(conditions=dict(X_cap=X_CAP, gates=list(GATES), grid=GRID, B2_max=B2_MAX, min_cell=MIN_CELL,
                               bar_miss=BAR_MISS, phrases=dict(selection=len(sel), fresh=len(fr), real=len(real))))
    out["B2_selection"] = {str(T): dict(zip(("passes", "cells"), b2_table(sel, str(T)))) for T in GATES}
    gsel = _selected(rows)
    out["selected_gate"] = gsel
    g = gsel or "20.0"
    out["gate_reported"] = g
    out["B2_fresh"] = dict(zip(("passes", "cells"), b2_table(fr, g)))
    resyn = [a for a in real if a.get("all_found") is not None]
    out["B2_real_resynth"] = dict(zip(("passes", "cells"), b2_table(resyn, g)))
    out["B4_fresh"] = b4(fr, g)
    out["B4_real_resynth_all_found"] = b4([a for a in resyn if a["all_found"]], g)
    out["reach_fresh"] = reach_table(fr, g)
    out["reach_real"] = reach_table(real, g)
    out["diagnostic_every_gate"] = {str(T): dict(reach_selection=reach_table(sel, str(T)), reach_fresh=reach_table(fr, str(T)),
                                                 B2_fresh=b2_table(fr, str(T))[1], B4_fresh=b4(fr, str(T)))
                                    for T in GATES}
    tot = lambda rr: dict(phrases=len(rr), reachable=sum(bool(a["gates"].get(g, {}).get("reach")) for a in rr),
                          moved_notes=sum(a["gates"].get(g, {}).get("moved", 0) for a in rr),
                          harmed=sum(a["gates"].get(g, {}).get("harmed", 0) for a in rr),
                          worse_any=sum(bool(a["gates"].get(g, {}).get("worse_at")) for a in rr))
    out["totals"] = dict(selection=tot(sel), fresh=tot(fr), real_resynth=tot(resyn),
                         real_original=tot([a for a in real if a.get("all_found") is None]))
    W = world["rows"]
    def wsum(ws):
        dk = [abs(w["samples"]["s"] - w["desc"]["s"]) for w in ws if np.isfinite(w["samples"]["s"]) and np.isfinite(w["desc"]["s"])]
        di = [abs(w["identity"]["s"] - w["take"]["s"]) for w in ws if np.isfinite(w["identity"]["s"]) and np.isfinite(w["take"]["s"])]
        ach = [b - a for w in ws for a, b in w["achieved"]]
        return dict(pairs=len(ws), with_moves=sum(w["moved"] > 0 for w in ws), reached=sum(w["reached"] for w in ws),
                    K_samples_minus_desc_abs=[round(float(np.median(dk)), 3), round(float(np.max(dk)), 3)] if dk else None,
                    K_identity_minus_take_abs=[round(float(np.median(di)), 3), round(float(np.max(di)), 3)] if di else None,
                    achieved_minus_requested=[round(float(np.percentile(ach, q)), 3) for q in (5, 50, 95)] if ach else None,
                    moved_notes_matched=len(ach),
                    call_agrees=sum(w["call_samples"] == w["call_desc"] for w in ws),
                    improved_desc=sum(w["call_desc"] == 1 for w in ws), improved_samples=sum(w["call_samples"] == 1 for w in ws))
    out["W_world"] = dict(gate=world["gate"], fresh=wsum([w for w in W if w["src"] == "fresh"]),
                          real_scales_straight=wsum([w for w in W if w["src"] == "real" and w["set"] == "scales_straight"]),
                          real_row_vibrato=wsum([w for w in W if w["src"] == "real" and w["set"] == "row_vibrato"]))
    json.dump(out, open(OUT / "round6.json", "w"), indent=1, default=float)
    print(json.dumps({k: v for k, v in out.items() if k not in ("diagnostic_every_gate", "B2_selection")}, indent=1, default=float))
    print(json.dumps({T: v["passes"] for T, v in out["B2_selection"].items()}))


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    dict(check=check, time=time_sample, fresh=run_fresh, analyse=run_analyse, world=run_world, report=report)[cmd](*args)
