"""E-005 round 7 (squillo iteration 83, F-073): the spread about a phrase's written notes when the
take sings only part of the phrase, holds one note across several written notes, or is one
wandering tone. Crude experiment code; adds to rounds 2-6, never replaces them.

    uv run python round7.py check          # the checks, each checked (S15) -> results/round7_checks.json
    uv run python round7.py time 24 18     # S19 sample on the pool, after the rules commit
    uv run python round7.py synth 18       # every job -> data/cache/r7_synth.pkl (saves every 100, resumes)
    uv run python round7.py report         # -> results/round7.json

Question (squillo F-073, R-16 section 8 for iteration 83). Squillo MT-014 (round 5's K, fold 5's
X = 40) measures a take given a library phrase's written notes, and is intent uncertain only when
fewer than two notes are kept. Round 5's phrases sang every written note. Fold 6 (F6-4) found one
tone wandering slowly about its pitch, given fourteen written notes, aligned to two of them and
measured, 8.047 +- 27.130 cents. Does MT-014's shown statement still hold the singer's spread when
a take sings only some of the phrase's notes, or holds one note where two or three are written;
does one tone given a phrase get a value; and would a least share of written notes kept before a
value is given be needed?

THE MEASURE: round5.known on the take's pitch with MT-003's refusal on (round5.one's form,
aperiodicity >= round5.REFUSE refused), the written notes being the WHOLE phrase's (as squillo
`runner` RU-014 passes them), states as round5.state at X = 40 (MT-014, fold 5).

INPUTS, conditions written before generating (S15 C1 to C3):
  Base jobs: round 2's synthetic design under its own seeds (round2.jobs_synth), the first 40 of each
  cell with 14 or 28 notes, sigma 0, 10, 20, 30, straight or vibrato faded in (16 cells, 640 jobs):
  exactly round 5's R phrases in those cells (round5.jobs via fold_refusal.jobs_cut(40)), so that
  each mode is paired with round 5's cached full take of the same melody, tuning G and errors e.
  phrase7 draws the random numbers in round2.phrase's order (round2.py:122-160: melody, G, e,
  scoop_on, depth, the 1-6 Hz wobble) on the whole written phrase, then sings a part of it:
    - head50 / head25: the first ceil(0.5 N) / ceil(0.25 N) written notes;
    - tail25: the last ceil(0.25 N);
    - mid50: ceil(0.5 N) notes centred, starting at floor((N - m) / 2);
    - hold2 / hold3: the written notes in consecutive groups of 2 / 3 from the first (the last
      group may be shorter); each group sung as ONE note at its first note's pitch plus that note's
      error e, lasting the group's summed durations. The singer aimed at the group's first note.
  Each sung note keeps its own draws (e, scoop depth); the wobble is drawn for the sung length; the
  contour asserted inside E2..C6 (round2.contour_ok) and the sung pitch list asserted equal to the
  written subset it claims (C3). Mode full is round 5's cached row (src R, `on`), reproduced on
  4 phrases by check r1.
  - tone: per base job of sigma 0 (4 cells: 14, 28 notes x straight, vibrato; 160 takes), one tone
    of 4.0 s at the phrase's first written note plus G and its e, with that note's scoop, the
    generator's 1-6 Hz wobble and, when vib, the faded-in vibrato, plus a slow wander of 20 cents at
    0.5 Hz (fold 6's held-wobble.wav: 0.5 Hz, -20.90 to +20.65 cents, squillo fixtures/MANIFEST.md),
    given all the phrase's written notes.

TRUTH: the population spread sigma of the sung notes' errors (round 5's B1 truth); the realised
spread of the sung notes is recorded. For a tone: one note, so no spread exists to state (MT-007's
reason: the spread of one note is undefined); a value given for it is a claim with no truth.

CANDIDATE RULES, in selection order: a value (measured or at least) only when the notes kept
(found - wrong) are at least F of the written states (after round2.merge_repeats), else intent
uncertain ("too few"), on top of MT-014's two notes; F = 0 (MT-014 as it stands), 0.25, 0.5, 0.75.

BARS, before the run (BAR_MISS = round5.BAR_MISS, 5 %, GUM 6.3.3 at k = 2):
  B1 honesty: in every cell (mode x N x sigma x vibrato, 40 takes) the candidate's shown statement
     excludes sigma (round5.excludes at X = 40; too few excludes nothing) in at most BAR_MISS.
  B5 one tone: in every tone cell (N x vibrato, 40 takes) a value is given in at most BAR_MISS.
  Selection: the first candidate passing B1 in every cell and B5 in every tone cell. None passing:
     that is the result, and F-073 says so.
  Reported with no bar: per cell the share measured, at least and too few under each candidate;
  notes found and kept against the sung and written counts; the share of found states (>= 0.1 s)
  whose segment's middle frame lies inside a sung note aimed at that state ("right"); the
  realised spread; the same per-cell exclusions for mode full from round 5's cache.

CHECKS (S15 C10, C11), each run before any bar's outcome is computed, each with a must-pass and a
must-fail case whose input differs:
  r1 phrase7 in mode full reproduces round 5's cached K (`on`: s, uB within round5.REPRO_TOL) on
     4 base jobs; must fail against the next job's cached values.
  r2 the generator's subset claim: head25 on one job sings exactly notes[:m] (asserted in phrase7);
     must fail: the claim checked against notes[1:m+1].
  r3 bar B1 on the reference condition (C11): round 5's cached full rows of these 16 cells, F = 0,
     must pass in every cell; must fail with the truth moved to sigma + 30 cents (the term moved is
     the truth in |K - truth| > 2 u_B; round 5's u_B medians 3.1 to 13.6 cents, R5-1, so a 30-cent
     shift exceeds 2 u_B for most takes and fails some cell).
  r4 bar B5 on reference inputs: squillo's held-steady.wav given notes-a-major-up-down.json (fold 6
     H1: too few) must pass it (no value); must fail on round 5's cached full rows of one cell
     (14 notes, sigma 0, straight), which are measured.
  r5 the share rule: take-in-tune.wav given its 14 notes (fold 6 M1: 14 of 14 found) keeps a value
     at F = 0.75; must fail: held-steady.wav given the same notes (1 of 14) is refused at F = 0.25.
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
import synth
import round2 as R2
import round5 as R5
import fold_refusal as FR

HERE = Path(__file__).parent
CACHE = HERE / "data" / "cache"
OUT = HERE / "results"
SR = R2.SR
X40 = 40.0                     # MT-014's upper-end limit (fold 5, squillo ADR 0015)
BAR_MISS = R5.BAR_MISS         # per cent, GUM 6.3.3 at k = 2 (fold_refusal's BAR)
REPRO_TOL = R5.REPRO_TOL       # same code on the same input, float64
LENGTHS = (14, 28)
SIGMAS = (0, 10, 20, 30)
PER_CELL = 40                  # round 5's phrases per cell
MODES = ("head50", "head25", "tail25", "mid50", "hold2", "hold3")
FS = (0.0, 0.25, 0.5, 0.75)    # candidate least shares of written states kept, selection order
TONE_S = 4.0                   # s, the tone's length (fold 6's held tones are 5 s; 4 s keeps it under a 14-note phrase's length)
WANDER_C, WANDER_HZ = 20.0, 0.5  # fold 6 held-wobble.wav: 0.5 Hz, -20.90 .. +20.65 cents (squillo MANIFEST)
SHIFT_FAIL = 30.0              # r3's must-fail truth shift, cents (docstring)
MODS = ["round7.py", "round5.py", "round2.py", "fold_refusal.py", "run.py", "infer.py", "synth.py", "fold5.py"]


def committed_first():
    """S15 C15: refuse to run on an uncommitted edit of this file or of any module it imports."""
    me = Path(__file__).name
    a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
    b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", *MODS], cwd=HERE)
    if a.returncode or b.returncode:
        sys.exit(f"{me} or a module it imports is not committed as it stands: commit the rules before running")


# ------------------------------------------------------------ inputs

def base_jobs():
    out = []
    for v, sc, sg, vib, L, seed in FR.jobs_cut(PER_CELL):
        if L in LENGTHS and sg in SIGMAS:
            out.append(dict(voice=v, scale=sc, sigma=sg, vib=vib, n_notes=L, seed=seed))
    assert len(out) == len(LENGTHS) * len(SIGMAS) * 2 * PER_CELL, len(out)
    return out


def jobs():
    out = [dict(j, mode=m) for j in base_jobs() for m in MODES]
    out += [dict(j, mode="tone") for j in base_jobs() if j["sigma"] == 0]
    return out


def sung_plan(mode, N):
    """(indices of the written notes each sung note aims at, groups of written indices it covers)."""
    if mode == "full":
        return [[i] for i in range(N)]
    if mode in ("head50", "head25"):
        m = math.ceil((0.5 if mode == "head50" else 0.25) * N)
        return [[i] for i in range(m)]
    if mode == "tail25":
        m = math.ceil(0.25 * N)
        return [[i] for i in range(N - m, N)]
    if mode == "mid50":
        m = math.ceil(0.5 * N)
        a = (N - m) // 2
        return [[i] for i in range(a, a + m)]
    if mode in ("hold2", "hold3"):
        g = int(mode[-1])
        return [list(range(i, min(i + g, N))) for i in range(0, N, g)]
    if mode == "tone":
        return [[0]]
    raise ValueError(mode)


def phrase7(job, claim_check=None):
    """round2.phrase's draws on the whole written phrase, then the part sung (docstring)."""
    import voice
    from scipy.signal import butter, sosfiltfilt
    sex, base = voice.VOICES[job["voice"]]
    rng = np.random.default_rng(job["seed"])
    for _ in range(100):
        m = R2.melody(job["scale"], base, rng, job["n_notes"])
        if m is not None:
            break
    notes, durs = m
    N = len(notes)
    G = rng.uniform(-50, 50)
    e = rng.normal(0, job["sigma"], N)
    scoop_on = rng.random(N) < 0.5
    depth = rng.uniform(30, 100, N) * scoop_on
    groups = sung_plan(job["mode"], N)
    aim = np.array([g[0] for g in groups])
    if job["mode"] == "tone":
        sd = np.array([TONE_S])
    else:
        sd = np.array([durs[g].sum() for g in groups])
    s_notes, s_e, s_depth = notes[aim], e[aim], depth[aim]
    # C3: the sung pitches are the written subset the mode claims
    want = notes[[g[0] for g in sung_plan(job["mode"], N)]]
    assert np.array_equal(s_notes, want)
    if claim_check is not None:
        return np.array_equal(s_notes, notes[claim_check])
    starts = np.concatenate([[0.0], np.cumsum(sd)[:-1]]) + 0.1
    T = starts[-1] + sd[-1] + 0.1
    n = int(round(T * SR))
    t = np.arange(n) / SR
    sung = synth.contour(100.0 * s_notes + s_e, starts, n) + G
    idx = np.clip(np.searchsorted(starts, t, "right") - 1, 0, None)
    since = t - starts[idx]
    sung -= s_depth[idx] * np.exp(-np.maximum(since, 0) / 0.06)
    if job["vib"]:
        fade = np.clip((since - 0.15) / 0.1, 0, 1)
        sung += 50.0 * fade * np.sin(2 * np.pi * 5.5 * t)
    sos = butter(2, [1.0, 6.0], btype="band", fs=SR, output="sos")
    w = sosfiltfilt(sos, rng.standard_normal(n))
    sung += 10.0 * w / np.sqrt(np.mean(w ** 2))
    if job["mode"] == "tone":
        sung += WANDER_C * np.sin(2 * np.pi * WANDER_HZ * t)
    amp = np.ones(n)
    amp[t < 0.1] = 0
    amp[t > T - 0.1] = 0
    amp = np.convolve(amp, np.ones(960) / 960, mode="same")
    ok, lo, hi = R2.contour_ok(sung, amp)
    if not ok:
        raise AssertionError(f"contour outside E2..C6: {lo:.1f} .. {hi:.1f} cents ({job})")
    x = voice.render(dict(sex=sex, n=n, amp=amp, noise_seed=job["seed"] + 1000), sung)
    states, state_of = R2.merge_repeats(notes)
    truth = dict(notes=notes, states=states, state_of=state_of, aim=aim, starts=starts, durs=sd, e=s_e)
    return x.astype(np.float32), truth


def right_share(cents, t, states, tr):
    """Share of found states (>= 0.1 s) whose segment's middle frame lies in a sung note aimed at it."""
    segs, _, _ = R2.align(cents, states)
    found = right = 0
    for j, s in enumerate(segs):
        if s is None or s[1] - s[0] < 1 or (s[1] - s[0]) * R2.HOP_S < R2.TRANS_S:
            continue
        found += 1
        tm = t[(s[0] + s[1]) // 2]
        k = np.flatnonzero((tr["starts"] <= tm) & (tm < tr["starts"] + tr["durs"]))
        if len(k) and tr["state_of"][tr["aim"][k[0]]] == j:
            right += 1
    return found, right


def one(job):
    x, tr = phrase7(job)
    t, c0, dmin = run.track(x)
    voiced = ~np.isnan(c0)
    c1 = c0.copy()
    c1[voiced & (dmin >= R5.REFUSE)] = np.nan
    sp = R5.known(c1, t, tr["states"])[0]
    w = tr["durs"]
    e = tr["e"]
    realised = float(np.sqrt(np.average((e - np.average(e, weights=w)) ** 2, weights=w))) if len(e) > 1 else math.nan
    fnd, rgt = right_share(c1, t, tr["states"], tr)
    return dict(job, on=sp, sung=len(tr["aim"]), written=len(tr["states"]), realised=realised,
                seg_found=fnd, seg_right=rgt, frames_refused=int((voiced & (dmin >= R5.REFUSE)).sum()))


# ------------------------------------------------------------ the rules

def kept(sp):
    return sp["found"] - sp["wrong"]


def state_f(sp, F):
    st = R5.state(sp, X40)
    if st != "too few" and kept(sp) < F * sp["states"]:
        return "too few"
    return st


def excl_f(sp, truth, F):
    st = state_f(sp, F)
    if st == "measured":
        return abs(sp["s"] - truth) > 2 * sp["uB"]
    if st == "at least":
        return sp["s"] - 2 * sp["uB"] > truth
    return False


def cell_key(r):
    return (r["mode"], r["n_notes"], r["sigma"], r["vib"])


def b1_cells(rows, F, shift=0.0):
    cells = {}
    for r in rows:
        k = cell_key(r)
        c = cells.setdefault(k, [0, 0])
        c[0] += 1
        c[1] += int(excl_f(r["on"], r["sigma"] + shift, F))
    out = {"|".join(map(str, k)): dict(n=n, excl=x, pct=100.0 * x / n, ok=100.0 * x / n <= BAR_MISS)
           for k, (n, x) in sorted(cells.items())}
    return all(v["ok"] for v in out.values()), out


def b5_cells(rows, F):
    cells = {}
    for r in rows:
        k = (r["mode"], r["n_notes"], r["vib"])
        c = cells.setdefault(k, [0, 0])
        c[0] += 1
        c[1] += int(state_f(r["on"], F) != "too few")
    out = {"|".join(map(str, k)): dict(n=n, valued=x, pct=100.0 * x / n, ok=100.0 * x / n <= BAR_MISS)
           for k, (n, x) in sorted(cells.items())}
    return all(v["ok"] for v in out.values()), out


def r5_full_rows():
    rows = [r for r in pickle.load(open(CACHE / "r5_synth.pkl", "rb")) if r["src"] == "R"
            and r["n_notes"] in LENGTHS and r["sigma"] in SIGMAS]
    assert len(rows) == len(base_jobs()), len(rows)
    return [dict(r, mode="full") for r in rows]


# ------------------------------------------------------------ checks (S15)

def run_checks():
    """r1 to r5; each must-pass and must-fail asserted; no bar's outcome is computed here."""
    import fold5 as F5
    out = {}
    cached = {r["seed"]: r["on"] for r in r5_full_rows()}
    B = base_jobs()
    ok_p = ok_f = 0
    for k in range(4):
        j = dict(B[k * 41], mode="full")
        nxt = cached[B[k * 41 + 1]["seed"]]
        sp = one(j)["on"]
        c = cached[j["seed"]]
        ok_p += abs(sp["s"] - c["s"]) <= REPRO_TOL and abs(sp["uB"] - c["uB"]) <= REPRO_TOL
        ok_f += abs(sp["s"] - nxt["s"]) <= REPRO_TOL and abs(sp["uB"] - nxt["uB"]) <= REPRO_TOL
    out["r1"] = dict(must_pass_equal=int(ok_p), must_fail_equal=int(ok_f))
    assert ok_p == 4 and ok_f == 0, out["r1"]
    j = dict(B[0], mode="head25")
    m = math.ceil(0.25 * j["n_notes"])
    p, f = phrase7(j, list(range(m))), phrase7(j, list(range(1, m + 1)))
    out["r2"] = dict(must_pass=bool(p), must_fail=bool(f))
    assert p and not f, out["r2"]
    full = r5_full_rows()
    p, _ = b1_cells(full, 0.0)
    f, _ = b1_cells(full, 0.0, SHIFT_FAIL)
    out["r3"] = dict(must_pass=bool(p), must_fail=bool(f))
    assert p and not f, out["r3"]
    H = F5.manifest_hashes()
    notes = json.loads((F5.SQ / "fixtures/metrics/notes-a-major-up-down.json").read_text())["notes"]
    _, steady = F5.k_of(F5.load("held-steady.wav", H), notes)
    _, intune = F5.k_of(F5.load("take-in-tune.wav", H), notes)
    p, _ = b5_cells([dict(mode="tone", n_notes=14, vib=0, on=steady)], 0.0)
    f, _ = b5_cells([dict(r, mode="tone") for r in full if r["n_notes"] == 14 and r["sigma"] == 0 and not r["vib"]], 0.0)
    out["r4"] = dict(must_pass=bool(p), must_fail=bool(f), steady_state=R5.state(steady, X40))
    assert p and not f, out["r4"]
    p = state_f(intune, 0.75) != "too few"
    f = state_f(steady, 0.25) != "too few"
    out["r5"] = dict(must_pass=bool(p), must_fail=bool(f), intune_kept=kept(intune), steady_kept=kept(steady),
                     states=intune["states"])
    assert p and not f, out["r5"]
    return out


def check():
    committed_first()
    out = run_checks()
    json.dump(out, open(OUT / "round7_checks.json", "w"), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float))


# ------------------------------------------------------------ the run

def time_sample(n="24", procs="18"):
    """S19: n jobs over every mode and the extremes (28 notes, sigma 30, vibrato; 14 notes, sigma 0, straight)."""
    committed_first()
    n, procs = int(n), int(procs)
    J = jobs()
    pick = []
    for m in MODES + ("tone",):
        sel = [j for j in J if j["mode"] == m and ((j["n_notes"] == 28 and j["vib"] == 1 and j["sigma"] in (0, 30))
                                                  or (j["n_notes"] == 14 and j["vib"] == 0 and j["sigma"] == 0))]
        pick += sel[:: max(1, len(sel) // max(1, n // 7))][: max(1, n // 7)]
    t0 = time.time()
    with Pool(procs) as p:
        rows = p.map(one, pick, chunksize=1)
    dt = time.time() - t0
    assert len(rows) == len(pick)
    print(f"{len(pick)} jobs on {procs} processes: {dt:.1f} s, {dt / len(pick):.3f} s each; "
          f"all {len(J)} est. {dt / len(pick) * len(J) / 60:.1f} min")


def run_synth(procs="18"):
    committed_first()
    procs = int(procs)
    path = CACHE / "r7_synth.pkl"
    rows = pickle.load(open(path, "rb")) if path.exists() else []
    done = {(r["mode"], r["seed"]) for r in rows}
    todo = [j for j in jobs() if (j["mode"], j["seed"]) not in done]
    t0 = time.time()
    with Pool(procs) as p:
        for k, r in enumerate(p.imap_unordered(one, todo, chunksize=2), 1):
            rows.append(r)
            if k % 100 == 0 or k == len(todo):
                pickle.dump(rows, open(path, "wb"))
                print(f"{len(rows)} jobs, {round((time.time() - t0) / 60, 1)} min", flush=True)


def report():
    committed_first()
    checks = run_checks()  # C10: every check of a check before any bar's outcome
    rows = pickle.load(open(CACHE / "r7_synth.pkl", "rb"))
    assert len(rows) == len(jobs()) and len({(r["mode"], r["seed"]) for r in rows}) == len(rows)
    main = [r for r in rows if r["mode"] != "tone"]
    tone = [r for r in rows if r["mode"] == "tone"]
    full = r5_full_rows()
    cand = {}
    for F in FS:
        p1, c1 = b1_cells(main, F)
        p5, c5 = b5_cells(tone, F)
        worst = max(c1.items(), key=lambda kv: kv[1]["pct"])
        cand[str(F)] = dict(B1_passes=p1, B5_passes=p5, B1_worst=worst, B1_failing=[k for k, v in c1.items() if not v["ok"]],
                            B5=c5, B1_cells=c1)
    sel = next((F for F in FS if cand[str(F)]["B1_passes"] and cand[str(F)]["B5_passes"]), None)

    def states_table(rs, keyf):
        out = {}
        for r in rs:
            k = "|".join(map(str, keyf(r)))
            d = out.setdefault(k, dict(n=0, found=[], kept=[], sung=r.get("sung", r["n_notes"]), written=r.get("written", r["on"]["states"]), seg_found=0,
                                       seg_right=0, uB=[], **{f"F{F}": {"measured": 0, "at least": 0, "too few": 0} for F in FS}))
            d["n"] += 1
            d["found"].append(r["on"]["found"])
            d["kept"].append(kept(r["on"]))
            d["seg_found"] += r.get("seg_found", 0)
            d["seg_right"] += r.get("seg_right", 0)
            if np.isfinite(r["on"]["uB"]):
                d["uB"].append(r["on"]["uB"])
            for F in FS:
                d[f"F{F}"][state_f(r["on"], F)] += 1
        for d in out.values():
            d["found_median"] = float(np.median(d.pop("found")))
            d["kept_median"] = float(np.median(d.pop("kept")))
            u = d.pop("uB")
            d["uB_median"] = float(np.median(u)) if u else None
            d["seg_right_pct"] = 100.0 * d["seg_right"] / d["seg_found"] if d["seg_found"] else None
        return out

    by_mode = states_table(main + full, lambda r: (r["mode"], r["n_notes"], r["vib"]))
    by_tone = states_table(tone, lambda r: (r["mode"], r["n_notes"], r["vib"]))
    _, full_b1 = b1_cells(full, 0.0)
    res = dict(x=X40, bar_miss=BAR_MISS, fs=FS, jobs=len(rows), checks=checks, selected=sel, candidates=cand,
               full_B1_r5=full_b1, states_by_mode=by_mode, states_tone=by_tone,
               tone_rows=[dict(n_notes=r["n_notes"], vib=r["vib"], seed=r["seed"], on=r["on"]) for r in tone])
    json.dump(res, open(OUT / "round7.json", "w"), indent=1, default=float)
    print(json.dumps(dict(selected=sel, **{F: dict(B1=v["B1_passes"], B5=v["B5_passes"], worst=v["B1_worst"],
                                                failing=v["B1_failing"]) for F, v in cand.items()}), indent=1, default=float))


if __name__ == "__main__":
    {"check": check, "time": time_sample, "synth": run_synth, "report": report}[sys.argv[1]](*sys.argv[2:])
