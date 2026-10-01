"""E-002 fold F1 re-read per set, and on E-003 round 2's inputs (squillo
iteration 63, finding F-052). Crude experiment code. Everything below was
written, and committed, before any run (squillo S15, S19).

    uv run python f052_sets.py check   # P1 and P4's cache check, with their must-fail cases
    uv run python f052_sets.py time    # S19: P5 on a sample at the pool; prints the estimate
    uv run python f052_sets.py run     # everything; writes results/f052_sets.json

The question (F-052). On E-002's 80 long tones as E-003 round 2 wrote them
(16-bit, -26 dBFS voiced RMS, 1 s of digital silence either side), MT-003's
+-2u covers 93.20 % of accepted frames (`squillo-lab E-003 @ 1ddd33c`,
results/r2/analysis.json groups["raw clean"].frames.direct.coverage), where
fold F1 found 94.5 % on all 20 singers over all 159 takes and 95.2 % on the
ten singers the table was not fitted on (results/fold2.json
measures.spec.frames and frames_even_held_out, clean). Is the shortfall the
long-tone subset, the input path (level, padding, 16-bit rounding), or the
frame-validity rule? And does +-2u reach 95 % per set on held-out singers?

Inputs, all cached, none regenerated:
- E-002 round 2's frames, data/cache/r2_frames.npz (r2_run.py): 159
  re-synthesized VocalSet takes, 20 singers, 8 sets, 9 conditions; the set
  and singer of each take from data/cache/r2_tone.json "meta".
- MT-003's table as squillo states it: results/fold2.json
  measures.spec.table (sqrt 3, 1.88, 2.44, 4.26 cents, refused from 0.02),
  the odd singers' table rounded up, so the even singers are held out.
- E-003 round 2's direct frame statistics, ../E-003-capture-reality/data/
  cache/r2/measures.pkl (r2_report.py; r2_measures.direct): the 80 long
  tones as written, clean and white-20, all 20 singers.
- For P5, E-002's re-syntheses data/cache/r2/<stem>.npz and E-003's written
  files ../E-003-capture-reality/data/cache/r2/in/<stem>.<cond>.wav.

Definitions.
- A frame is accepted when it is valid (r2_run.frame_truth), has a pitch,
  and its aperiodicity gives a finite u under the table; coverage is the
  share of accepted frames with |error| <= 2u, error in cents against the
  truth at SG-007's instant. This is fold2.coverage and E-003's
  r2_measures.frame_stats with r2_measures.coverage, unchanged.
- Interval: 95 % percentile interval over 1000 bootstrap resamples of the
  singers in the selection (seed 20261001), frames pooled per resample, as
  E-003's r2_report.boot resamples singers. Every quantity of one table is
  resampled jointly (the same singers per resample).

Parts.
- P1, reproduction (a check). Recomputed here from the caches: fold2.json's
  spec coverage and accepted count, clean, all 20 singers and even held out,
  and E-003's raw clean direct coverage and accepted count, must equal the
  committed values (accepted exactly; coverage within 1e-12, the rounding of
  a mean of 10^5 booleans in binary64 being far below it). Must fail: the
  same with every finite entry of the table above sqrt 3 multiplied by 0.9
  (a different input to the same computation) must not equal fold2.json's
  all-singer coverage; and E-003's pooled white-20 direct frames must not
  equal its raw clean coverage.
- P2, per set. For every set and every condition of r2_analyse.ALL_CONDS:
  accepted share and coverage, with intervals, (a) on the ten even singers
  (held out) and (b) on all 20. E-003's 80 per long-tone set, clean and
  white-20, on all 20 and on the even ten.
- P3, the decomposition (clean, all 20 singers). G = cov(E-002, all 159) -
  cov(E-003 direct, the 80) = S + P, S = cov(E-002, all 159) - cov(E-002,
  the 80 long tones) (the subset), P = cov(E-002, the 80) - cov(E-003
  direct, the 80) (the input path), each with its interval.
- P4, the pairing. The 80 E-003 stems must be exactly E-002's LT-* takes
  (asserted). Per take: valid and accepted frames on both sides, and the
  takes where they differ. The frame-validity rule is the same function on
  both sides (r2_run.frame_truth); a difference in valid frames can come
  only from the input path, and is reported, not assumed.
  Cache check: E-003's clean direct statistics recomputed live from the
  written files (r2_measures.read_input, frames, frame_stats) must equal the
  pickle's for every take (counts exactly, err and u arrays exactly). Must
  fail: the live clean statistics compared with the pickle's white-20 for
  the same take must differ.
- P5, the input path split. Each of the 80 re-syntheses scaled by E-003's
  gain and padded exactly as r2_gen.make does, but left in binary64 (no
  16-bit rounding), measured by E-003's r2_measures.frames against the
  float32 truth r2_gen.make saves; the padded truth must equal E-003's
  saved truth.npy exactly (asserted), and the binary64 signal must lie
  within one 16-bit step of the written file (asserted, r2_gen.make's own
  condition). P = P_level_pad + P_16bit, P_level_pad = cov(E-002, the 80) -
  cov(binary64 padded), P_16bit = cov(binary64 padded) - cov(E-003 direct),
  each with its interval.

Bars and rules, written before any run.
- R1, attribution: a component of P3 or P5 is **shown** when its 95 %
  interval excludes 0, and **not shown** otherwise. The README names the
  shown components and their share of G; nothing else is attributed.
- R2, per set, clean, held-out even singers: a set is **shown under 95 %**
  when its interval's upper end is below 0.95, **shown at or over** when its
  lower end is at least 0.95, and **not shown either way** otherwise. Must
  pass (not shown under): all sets pooled, clean, held out, fold F1's own
  95.2 %. Must fail (shown under): all sets pooled, room-0.8, held out
  (fold F1: 64.9 %). Both are asserted before R2 is applied to any set.
- What follows for squillo, written before: a set shown under 95 % clean on
  held-out singers is a limit MT-003's reason states with its numbers, in
  iteration 64's fold; nothing here refits the table or changes a bound.
"""
import json
import math
import os
import pickle
import subprocess
import sys
import time
from multiprocessing import Pool
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
E003 = HERE.parent / "E-003-capture-reality"
sys.path.append(str(E003))
import r2_analyse as A  # noqa: E402
import r2_truth as T  # noqa: E402

OUT = HERE / "results"
SEED, BOOT = 20261001, 1000
LEVEL_DBFS, PAD = -26.0, 48_000  # r2_gen.py lines 23-24, read from the code
LT = ("LT-straight", "LT-forte", "LT-pp", "LT-messa")
POOL = 16


def committed_first():
    """squillo L-047 (S15): refuse to run on an uncommitted edit of this script."""
    here = Path(__file__).resolve()
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", here.name], cwd=here.parent,
                             capture_output=True).returncode == 0
    r = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", here.name], cwd=here.parent)
    if not tracked or r.returncode != 0:
        raise SystemExit(f"{here.name} has uncommitted edits: commit its rules first (S15, L-047)")


FOLD2 = json.loads((OUT / "fold2.json").read_text())["measures"]["spec"]
TABLE = np.array([np.inf if v is None else v for v in FOLD2["table"]])
E3AN = json.loads((E003 / "results/r2/analysis.json").read_text())["groups"]
META = json.loads((T.CACHE / "r2_tone.json").read_text())["meta"]
NAMES = [m["name"] for m in META]
SINGER = np.array([m["singer"] for m in META])
SETS = np.array([m["set"] for m in META])
EVEN = np.array([int("".join(ch for ch in s if ch.isdigit())) % 2 == 0 for s in SINGER])
SINGERS = sorted(set(SINGER))


# ------------------------------------------------------------------ per-singer counts
def e002_counts(cond, table, files):
    """Per singer: (valid, accepted, covered) over the takes in `files` (bool per take), fold2.coverage's
    arithmetic."""
    e, ok = A.ERR[cond]
    fk = A.Z[cond + "/file"]
    valid = A.Z[cond + "/valid"]
    u = np.full(len(e), np.inf)
    u[ok] = A.u_of(A.Z[cond + "/dip"][ok], table)
    acc = ok & np.isfinite(u)
    cov = np.zeros(len(e), bool)
    cov[acc] = np.abs(e[acc]) <= 2 * u[acc]
    sel = files[fk]
    sg = np.searchsorted(SINGERS, SINGER[fk])
    out = np.zeros((len(SINGERS), 3), np.int64)
    for j, m in enumerate((valid, acc, cov)):
        out[:, j] = np.bincount(sg[sel & m], minlength=len(SINGERS))
    return out


def stats_counts(stats_by_stem, stems):
    """Per singer (valid, accepted, covered) from E-003-style frame stats {stem: dict(valid, accepted, err, u)}."""
    out = np.zeros((len(SINGERS), 3), np.int64)
    for s in stems:
        st = stats_by_stem[s]
        k = SINGERS.index(T.singer_of(s))
        out[k] += (st["valid"], st["accepted"], int(np.sum(st["err"] <= 2 * st["u"])))
    return out


def cov_of(c):
    return float(c[:, 2].sum() / c[:, 1].sum()) if c[:, 1].sum() else float("nan")


def share_of(c):
    return float(c[:, 1].sum() / c[:, 0].sum()) if c[:, 0].sum() else float("nan")


PICKS = None


def picks():
    global PICKS
    if PICKS is None:
        rng = np.random.default_rng(SEED)
        PICKS = rng.integers(0, len(SINGERS), (BOOT, len(SINGERS)))
    return PICKS


def interval(fn, counts, members):
    """95 % percentile interval of fn(resampled counts...) over resamples of the singers in `members`
    (indices into SINGERS); counts is a list of per-singer arrays resampled jointly."""
    mem = np.array(members)
    vals = []
    for p in picks():
        idx = mem[p[:len(mem)] % len(mem)]
        v = fn(*[c[idx] for c in counts])
        if np.isfinite(v):
            vals.append(v)
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def summary(c, members):
    return dict(valid=int(c[members, 0].sum()), accepted=int(c[members, 1].sum()),
                accepted_share=share_of(c[members]), coverage=cov_of(c[members]),
                coverage_ci95=interval(cov_of, [c], members))


ALL20 = list(range(len(SINGERS)))
EVEN10 = [i for i, s in enumerate(SINGERS) if int("".join(ch for ch in s if ch.isdigit())) % 2 == 0]


def r2_verdict(ci):
    if ci[1] < 0.95:
        return "shown under 95 %"
    if ci[0] >= 0.95:
        return "shown at or over 95 %"
    return "not shown either way"


# ------------------------------------------------------------------ E-003 frames
def e003_pickle():
    D, _ = pickle.loads((E003 / "data/cache/r2/measures.pkl").read_bytes())
    return {k: v[0] for k, v in D.items()}


def live_direct(stem):
    import r2_measures as X
    x, ft = X.read_input(stem, "clean")
    return stem, X.frame_stats(X.frames(x, ft))


def float_padded(stem):
    """r2_gen.make's signal for `clean`, left in binary64 (P5)."""
    import r2_measures as X
    import soundfile as sf
    z = np.load(T.R2 / f"{stem}.npz")
    y, f0 = z["y"].astype(np.float64), z["f0"]
    ft = T.truth_per_sample(f0, len(y))
    voiced = ft > 0
    g = 10 ** (LEVEL_DBFS / 20) / np.sqrt(np.mean(y[voiced] ** 2))
    x = np.concatenate([np.zeros(PAD), g * y, np.zeros(PAD)])
    ftp = np.concatenate([np.zeros(PAD), ft, np.zeros(PAD)]).astype(np.float32).astype(np.float64)
    saved = np.load(X.IN / f"{stem}.truth.npy").astype(np.float64)
    assert np.array_equal(ftp, saved), stem
    r, _ = sf.read(X.IN / f"{stem}.clean.wav", dtype="float64")
    assert len(r) == len(x) and np.abs(r - x).max() <= 1 / 32768, stem
    return stem, X.frame_stats(X.frames(x, ftp))


def lt_stems():
    return sorted(n for n, s in zip(NAMES, SETS) if s in LT)


# ------------------------------------------------------------------ P1 and the cache check
def check(live=None):
    res = {}
    allf = np.ones(len(META), bool)
    c = e002_counts("clean", TABLE, allf)
    fs, fe = FOLD2["frames"]["clean"], FOLD2["frames_even_held_out"]["clean"]
    got = dict(all_acc=int(c[:, 1].sum()), all_cov=cov_of(c), even_acc=int(c[EVEN10, 1].sum()), even_cov=cov_of(c[EVEN10]))
    must_pass = (got["all_acc"] == fs["accepted"] and abs(got["all_cov"] - fs["coverage_k2"]) <= 1e-12
                 and got["even_acc"] == fe["accepted"] and abs(got["even_cov"] - fe["coverage_k2"]) <= 1e-12)
    t09 = np.where(np.isfinite(TABLE) & (TABLE > math.sqrt(3)), 0.9 * TABLE, TABLE)
    c9 = e002_counts("clean", t09, allf)
    must_fail_reproduces = abs(cov_of(c9) - fs["coverage_k2"]) <= 1e-12
    res["P1_e002_reproduces"] = dict(got=got, fold2_all=fs, fold2_even=fe, must_pass=bool(must_pass))
    res["P1_e002_table_0p9_must_fail"] = dict(coverage=cov_of(c9), reproduces=bool(must_fail_reproduces))
    assert must_pass, res["P1_e002_reproduces"]
    assert not must_fail_reproduces, res["P1_e002_table_0p9_must_fail"]
    P = e003_pickle()
    stems = lt_stems()
    assert sorted(s for s, cond in P if cond == "clean") == stems, "P4: the 80 are not E-002's LT takes"
    d = E3AN["raw clean"]["frames"]["direct"]
    cc = stats_counts({s: P[(s, "clean")] for s in stems}, stems)
    cw = stats_counts({s: P[(s, "white-20")] for s in stems}, stems)
    e3_pass = int(cc[:, 1].sum()) == d["accepted"] and abs(cov_of(cc) - d["coverage"]) <= 1e-12
    e3_fail = int(cw[:, 1].sum()) == d["accepted"] and abs(cov_of(cw) - d["coverage"]) <= 1e-12
    res["P1_e003_reproduces"] = dict(accepted=int(cc[:, 1].sum()), coverage=cov_of(cc), committed=d, must_pass=bool(e3_pass))
    res["P1_e003_white20_must_fail"] = dict(accepted=int(cw[:, 1].sum()), coverage=cov_of(cw), reproduces=bool(e3_fail))
    assert e3_pass, res["P1_e003_reproduces"]
    assert not e3_fail, res["P1_e003_white20_must_fail"]
    if live is not None:  # P4's cache check
        same = {s: all(np.array_equal(np.asarray(live[s][k]), np.asarray(P[(s, "clean")][k])) for k in ("valid", "accepted", "err", "u"))
                for s in live}
        other = {s: all(np.array_equal(np.asarray(live[s][k]), np.asarray(P[(s, "white-20")][k])) for k in ("valid", "accepted", "err", "u"))
                 for s in live}
        res["P4_cache_check"] = dict(takes=len(live), equal=sum(same.values()), must=all(same.values()))
        res["P4_cache_white20_must_fail"] = dict(takes=len(live), equal=sum(other.values()), must=not any(other.values()))
        assert res["P4_cache_check"]["must"], res["P4_cache_check"]
        assert res["P4_cache_white20_must_fail"]["must"], res["P4_cache_white20_must_fail"]
    return res


# ------------------------------------------------------------------ the run
def run():
    t0 = time.time()
    stems = lt_stems()
    with Pool(POOL) as pool:
        live = dict(pool.map(live_direct, stems))
        flt = dict(pool.map(float_padded, stems))
    print(f"P4 live and P5 binary64: {time.time() - t0:.1f} s", flush=True)
    R = dict(checks=check(live))
    # R2's own check, before any set
    allf = np.ones(len(META), bool)
    ref_pass = summary(e002_counts("clean", TABLE, allf), EVEN10)
    ref_fail = summary(e002_counts("room-0.8", TABLE, allf), EVEN10)
    R["checks"]["R2_clean_all_sets_must_not_be_under"] = dict(ref_pass, verdict=r2_verdict(ref_pass["coverage_ci95"]),
                                                              must=r2_verdict(ref_pass["coverage_ci95"]) != "shown under 95 %")
    R["checks"]["R2_room08_all_sets_must_be_under"] = dict(ref_fail, verdict=r2_verdict(ref_fail["coverage_ci95"]),
                                                           must=r2_verdict(ref_fail["coverage_ci95"]) == "shown under 95 %")
    assert R["checks"]["R2_clean_all_sets_must_not_be_under"]["must"], R["checks"]["R2_clean_all_sets_must_not_be_under"]
    assert R["checks"]["R2_room08_all_sets_must_be_under"]["must"], R["checks"]["R2_room08_all_sets_must_be_under"]
    # P2
    p2 = {}
    for cond in A.ALL_CONDS:
        p2[cond] = {}
        for s in sorted(set(SETS)) + ["all"]:
            files = np.ones(len(META), bool) if s == "all" else SETS == s
            c = e002_counts(cond, TABLE, files)
            row = dict(takes=int(files.sum()), even_held_out=summary(c, EVEN10), all_20=summary(c, ALL20))
            row["even_held_out"]["R2"] = r2_verdict(row["even_held_out"]["coverage_ci95"]) if cond == "clean" else None
            p2[cond][s] = row
    R["P2_e002_by_set"] = p2
    P = e003_pickle()
    e3 = {}
    for cond in ("clean", "white-20"):
        e3[cond] = {}
        for s in list(LT) + ["all"]:
            st = [x for x in stems if s == "all" or T.set_of(x) == s]
            c = stats_counts({x: P[(x, cond)] for x in st}, st)
            e3[cond][s] = dict(takes=len(st), even=summary(c, EVEN10), all_20=summary(c, ALL20))
    R["P2_e003_by_set"] = e3
    # P3 and P5, jointly resampled
    lt = np.isin(SETS, LT)
    c_all = e002_counts("clean", TABLE, allf)
    c_lt = e002_counts("clean", TABLE, lt)
    c_flt = stats_counts(flt, stems)
    c_e3 = stats_counts({x: P[(x, "clean")] for x in stems}, stems)
    comps = dict(G=lambda a, l, f, e: cov_of(a) - cov_of(e), S=lambda a, l, f, e: cov_of(a) - cov_of(l),
                 P=lambda a, l, f, e: cov_of(l) - cov_of(e), P_level_pad=lambda a, l, f, e: cov_of(l) - cov_of(f),
                 P_16bit=lambda a, l, f, e: cov_of(f) - cov_of(e))
    dec = {}
    for name, fn in comps.items():
        v = fn(c_all, c_lt, c_flt, c_e3)
        ci = interval(fn, [c_all, c_lt, c_flt, c_e3], ALL20)
        dec[name] = dict(value=v, ci95=ci, R1="shown" if (ci[0] > 0 or ci[1] < 0) else "not shown")
    dec["coverages"] = dict(e002_all_159=cov_of(c_all), e002_lt_80=cov_of(c_lt), binary64_padded_80=cov_of(c_flt),
                            e003_direct_80=cov_of(c_e3))
    assert abs(dec["S"]["value"] + dec["P"]["value"] - dec["G"]["value"]) <= 1e-12
    R["P3_P5_decomposition"] = dec
    # P4, per take
    rows = []
    for x in stems:
        k = NAMES.index(x)
        one = np.zeros(len(META), bool); one[k] = True
        a = e002_counts("clean", TABLE, one).sum(0)
        f, e = flt[x], P[(x, "clean")]
        rows.append(dict(stem=x, set=T.set_of(x), e002=[int(v) for v in a], binary64=[int(f["valid"]), int(f["accepted"])],
                         e003=[int(e["valid"]), int(e["accepted"])]))
    R["P4_pairing"] = dict(
        takes=len(rows),
        valid_differs_e002_vs_e003=sum(r["e002"][0] != r["e003"][0] for r in rows),
        valid_sum=dict(e002=sum(r["e002"][0] for r in rows), binary64=sum(r["binary64"][0] for r in rows), e003=sum(r["e003"][0] for r in rows)),
        accepted_sum=dict(e002=sum(r["e002"][1] for r in rows), binary64=sum(r["binary64"][1] for r in rows), e003=sum(r["e003"][1] for r in rows)),
        accepted_differs_e002_vs_e003=sum(r["e002"][1] != r["e003"][1] for r in rows),
        accepted_differs_binary64_vs_e003=sum(r["binary64"][1] != r["e003"][1] for r in rows),
        rows=rows)
    R["seconds"] = time.time() - t0
    (OUT / "f052_sets.json").write_text(json.dumps(R, indent=1))
    print(json.dumps({k: v for k, v in R.items() if k not in ("P2_e002_by_set", "P4_pairing")}, indent=1)[:6000])
    for cond in ("clean",):
        for s, v in p2[cond].items():
            h, a = v["even_held_out"], v["all_20"]
            print(f"{cond:8s}{s:13s} held-out {h['coverage']:.4f} {h['coverage_ci95']} {h['R2']}  all-20 {a['coverage']:.4f} acc {a['accepted_share']:.3f}")


def time_sample():
    """S19: P4's live recompute and P5 on a sample spread over the four sets, at the pool."""
    stems = lt_stems()
    sample = [s for s in stems if s.startswith(("f1_", "m11_"))]
    t0 = time.time()
    with Pool(POOL) as pool:
        pool.map(live_direct, sample)
        pool.map(float_padded, sample)
    dt = time.time() - t0
    print(f"{len(sample)} takes in {dt:.1f} s at pool {POOL}; 80 takes est. {dt * 80 / len(sample) / 60:.1f} min "
          f"(an upper bound: the pool is not full on the sample)")


if __name__ == "__main__":
    committed_first()
    cmd = sys.argv[1]
    if cmd == "check":
        print(json.dumps(check(), indent=1, default=float))
    elif cmd == "time":
        time_sample()
    elif cmd == "run":
        run()
