"""E-002 round 5 (squillo iteration 78, F-070 with F-046): held notes trimmed to their first and last
measured cells, and the next step's strength against the number of blocks. Crude experiment code.

    uv run python r5_trim.py check  <squillo>   # the checks of the checks below, no data judged
    uv run python r5_trim.py sample <squillo>   # S19: time a sample of E-004 renderings at the pool
    uv run python r5_trim.py run    <squillo>   # every E-004 round 4 rendering, saved as it goes -> data/cache/r5/
    uv run python r5_trim.py analyse <squillo>  # -> results/r5_trim.json

Needs round 2's data/cache/r2_frames.npz, results/fold2.json and results/fold3_ladder.json, and E-004
round 4's renderings re-made from its code (E-004 r4_held.py `one`, same jobs and seeds), checked against
E-004's data/cache/r4/ and results/r4/diag.json.

Questions.
  squillo F-070: MT-009 rejects a whole piece when the 60-cent cut puts its first or last cell on a cell
  not measured; on E-004 round 4's renderings that lost 26 of 360 written held notes (E-004 r4/diag.json:
  23 begins-unmeasured, 2 ends-unmeasured, 1 filled). If a piece is instead trimmed to its first and last
  measured cells before MT-009's other conditions are applied, how many written held notes are found,
  and do MT-010's coverages on round 2's takes hold?
  squillo F-046: the weakest steadying MT-008 calls improved is a median 0.63 of the steadying SY-002
  allows on 28 original takes (fold 3, L3), because a take's steadiness +- is wide on 2 to 8 blocks. How
  does the next step's strength fall as blocks are added, and how far could it fall at most?

Rules, written and committed before any run (S15, checklist C14). Each is asserted in code where it is
a check; a bar's outcome is the result.

  The trimmed finder, `finder(p, u, trim=True)`: fold2.held_notes (E-002 fold2.py lines 121-166) with
  one change. Each piece the 60-cent cut forms (frames s0 to s1 - 1 of its run) is first trimmed to its
  first and last accepted frames; a piece with none is dropped; MT-009's other conditions (at least 250
  frames, no stretch over 12 not accepted, at most a quarter filled) are then applied to the trimmed
  piece, and its contour is refilled on it alone. The cut positions are unchanged, so every held note the
  current rule finds is found unchanged (its first and last frames are accepted, so trimming is the
  identity on it); asserted on every input, as `superset`. `finder(p, u, trim=False)` is asserted equal
  to fold2.held_notes (frames, contour, accepted mask) on every input it reads.

  Part T (F-070).
  T0 Reproduction, asserted: E-004's renderings re-made with r4_held.one give the cached held notes and
     blocks (data/cache/r4/<seed>.json) on every rendering, and, under the current finder, the same
     found / lost written held notes as diag.json on each of its 26 renderings, 26 lost of 360 on the 9
     new items. Round 2's takes under the current finder and squillo's constants (fold2.json
     measures.spec: table, c, kappa, read, never retyped) reproduce fold2.json measures.spec.eval
     (held notes, takes measured, take_n and take coverage per measure and condition).
  T1 Bar: on the 9 new items' 216 renderings, the trimmed finder loses at most 1 of the 360 written held
     notes. Why 1: diag.json gives 25 of the 26 lost to a piece that begins or ends on a cell not
     measured, which trimming acts on, and 1 to a piece over a quarter filled, which it acts on only by
     removing the head; the lost pieces held 443 to 703 frames, so a trim of the head or tail leaves
     them over 250 unless more than 193 frames are not accepted at an end.
     Bar's check (C11): must pass on the constructed case P below under the trimmed finder (0 of 2 lost),
     must fail on the 216 renderings under the current finder (26 of 360, T0).
  T2 Bar: with the trimmed finder and squillo's constants unchanged, on round 2's clean re-syntheses the
     take's +- (2u) covers its true value on every take measured, for steadiness, extent and rate, as F4
     did (36 of 36, 36 of 36, 23 of 23; that earlier rate was 100 %, C13). Bar's check (C11): must pass
     on the current finder (T0's reproduction, 100 %); must fail on the trimmed finder's takes with every
     take u divided by 1000 (the input differs: the u the bar reads). Revision 2, after the first
     `analyse` stopped on this assertion and printed T2's outcome (true) with it: dividing the block u
     cannot fail the bar, since a take's u is kappa sqrt(s^2/n + u_mean^2) and s dominates; the
     must-fail input is instead every measured block value moved off its truth (steadiness and extent
     +5 cents, rate +1 Hz, SHIFT). The bar itself is unchanged.
  T3 Prediction of no change (C12, read first): squillo's fixtures held-steady, held-wobble and
     held-vibrato have every frame accepted (fold2.json fixtures: 622 frames, 622 accepted, one held
     note 0-621), and sine-220hz has no held note, so the trimmed finder gives each the same held notes
     and take values; asserted. Its must-fail: the constructed case P, where the two finders differ.
  T4 Recorded, no bar: per round 2 condition, held notes, takes measured, take_n and coverage under both
     finders; on all 39 items' 936 renderings, written held notes lost, renderings with at least two
     blocks per item, and CO-005 rule (2)'s one-held-note items (E-004 diag share: 61 of 72).

  Part B (F-046), on round 2's original takes and clean re-syntheses, under the current finder (the
  trimmed one recorded beside it). Fold 3's ladder exactly (fold3_ladder.ladder: the full steadying, alpha
  max, 64 strengths, MT-008), with one addition: the take and each rung are measured on the first n of the
  take's blocks, n = 2 .. B, B the take's own block count. Blocks are matched between the take and a rung
  by their first frame in the take; a rung missing one of the n is not measured at n, so not improved.
  The next step at n is the least strength improved at n; its strength is k * alpha_max / 64 (fold 3 L3).
  B0 Check: at n = B, the next k equals fold3_ladder.json's next_k on every measured take of both
     conditions (must pass); the same comparison against the next_k list rotated by one take must not
     agree on every take (must fail: the input differs).
  B1 Recorded, prediction without a bar: on the takes with at least 4 blocks, more have a step at n = 4
     than at n = 2, and on those with a step at both, the paired median strength falls.
  B2 Recorded, a model's limit, no bar: the floor. With the take's u = kappa * mean tracking u (MT-010
     with s^2/n dropped, as n -> infinity, the block values' mean unchanged), the least strength
     improved on all B blocks: how small a step more blocks of the same singing could ever make shown.
     A model's extrapolation, never a measurement.

  The constructed case of the checks (C1, C3: its conditions asserted on it): 300 frames at 0 cents,
  12 frames not accepted (u infinite), then 330 frames at +200 cents; every accepted frame u = sqrt 3.
  P: the 12 frames sit across the step (frames 300-311), so the 60-cent cut falls on one of them,
     asserted (revision 1, after the first `check` stopped on its own assertion, no data read: the cut
     forms one-frame pieces across the step, so the assertion reads the last cut, where the piece holding
     the second note begins); the trimmed finder finds 2 held notes and the current finder fewer (must pass: trimming
     recovers; the current finder may lose both, since the first piece may also end on one of them).
  Q: the same contour with the 12 frames moved 100 frames into the second note, the step clean; the cut
     falls on an accepted frame, asserted; both finders find the same held notes (must fail: trimming
     recovers nothing).

Crude, disposable lab code: never product code (squillo PLAN.md rule 11).
"""
import importlib.util
import json
import math
import subprocess
import sys
import time
from fractions import Fraction
from multiprocessing import get_context
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
E004 = HERE.parent / "E-004-phrase-library"
CACHE = HERE / "data" / "cache" / "r5"
OUT = HERE / "results" / "r5_trim.json"
POOL = 16
GUARDED = ("r5_trim.py", "fold2.py", "fold3_ladder.py", "r2_analyse.py", "../E-004-phrase-library/r4_held.py")


def committed_first():
    """S15 (C15): refuse to run on an uncommitted edit of this file or of the modules whose rules it runs."""
    for me in GUARDED:
        a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
        b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", me], cwd=HERE)
        if a.returncode or b.returncode:
            sys.exit(f"{me} is not committed as it stands: commit the rules before running")


if __name__ == "__main__":
    committed_first()
    CMD, SQ = sys.argv[1], Path(sys.argv[2])
    sys.argv = sys.argv[:1] + [str(SQ)]   # fold3_ladder reads sys.argv[1] at import as squillo's path

import fold2 as F2          # noqa: E402
import fold3_ladder as L    # noqa: E402
import r2_analyse as A      # noqa: E402

SPEC = json.loads((A.T.OUT / "fold2.json").read_text())["measures"]["spec"]
TABLE = np.array([np.inf if x is None else x for x in SPEC["table"]])
C_SP, K_SP = SPEC["c"], SPEC["kappa"]
F2.SPEC_TABLE = TABLE
CURRENT = F2.held_notes
# revision 2: T2's must-fail shift. 5 cents is MT-010's 2.5 x the median take u for steadiness (2.02 cents,
# fold 3 L3) rounded up; for extent the same 5 cents; for rate 1 Hz, beyond the rate's tracking c (0.16)
# times any block's rms u over its extent. A case, not a tolerance: it only has to fail.
SHIFT = dict(S=5.0, E=5.0, R=1.0)


# ------------------------------------------------------------------ the finder
def finder(p, u, trim):
    """fold2.held_notes (fold2.py lines 121-166); with trim, each piece is trimmed to its first and last
    accepted frames before MT-009's other conditions."""
    acc = ~np.isnan(p) & np.isfinite(u)
    out, n, i = [], len(p), 0
    while i < n:
        if not acc[i]:
            i += 1
            continue
        j, last = i, i
        while j < n and j - last <= F2.MAX_GAP + 1:
            if acc[j]:
                last = j
            j += 1
        run = np.arange(i, last + 1)
        i = last + 1
        if len(run) < F2.MIN_LEN:
            continue
        a = acc[run].copy()
        med = np.median(p[run][a])
        a &= np.abs(np.where(a, p[run], med) - med) <= F2.OCT
        if a.sum() < 2:
            continue
        x = np.arange(len(run))
        lp = F2.filtfilt(*F2.B2, np.interp(x, x[a], p[run][a]))
        s0 = 0
        while s0 < len(run):
            ref = np.median(lp[s0:s0 + 31])
            s1 = s0 + 1
            while s1 < len(run) and abs(lp[s1] - ref) <= F2.SPLIT:
                s1 += 1
            t0, t1 = s0, s1
            if trim:
                k = np.nonzero(a[s0:s1])[0]
                if not len(k):
                    s0 = s1
                    continue
                t0, t1 = s0 + int(k[0]), s0 + int(k[-1]) + 1
            seg = slice(t0, t1)
            aa = a[seg]
            if t1 - t0 >= F2.MIN_LEN and aa[0] and aa[-1]:
                gaps = np.diff(np.concatenate([[0], (~aa).astype(int), [0]]))
                st, en = np.nonzero(gaps == 1)[0], np.nonzero(gaps == -1)[0]
                if (not len(st) or (en - st).max() <= F2.MAX_GAP) and (~aa).mean() <= F2.MAX_FILL:
                    xx = np.arange(t1 - t0)
                    out.append((run[seg], np.interp(xx, xx[aa], p[run][seg][aa]), aa))
            s0 = s1
    return out


def same_notes(a, b):
    return len(a) == len(b) and all(np.array_equal(x[0], y[0]) and np.array_equal(x[1], y[1]) and np.array_equal(x[2], y[2])
                                    for x, y in zip(a, b))


def cuts(p, u):
    """The first frame of every piece after the first in each run (where the 60-cent cut fell)."""
    acc = ~np.isnan(p) & np.isfinite(u)
    a = acc.copy()
    x = np.arange(len(p))
    lp = F2.filtfilt(*F2.B2, np.interp(x, x[a], p[a]))
    out, s0 = [], 0
    while s0 < len(p):
        ref = np.median(lp[s0:s0 + 31])
        s1 = s0 + 1
        while s1 < len(p) and abs(lp[s1] - ref) <= F2.SPLIT:
            s1 += 1
        if s1 < len(p):
            out.append(s1)
        s0 = s1
    return out


def both(p, u):
    """Both finders on one input, with the asserted identities: trim=False is fold2.held_notes, and
    every current held note is a trimmed held note (superset)."""
    cur = CURRENT(p, u)
    assert same_notes(finder(p, u, False), cur)
    tr = finder(p, u, True)
    keys = {(int(f[0]), int(f[-1])) for f, _, _ in tr}
    assert all((int(f[0]), int(f[-1])) in keys for f, _, _ in cur), "superset"
    return cur, tr


def constructed(where):
    p = np.concatenate([np.zeros(300), np.full(342, 200.0)])
    u = np.full(len(p), math.sqrt(3))
    lo = 300 if where == "P" else 400
    u[lo:lo + 12] = np.inf
    # C3: the conditions asserted on what was made
    assert np.sum(~np.isfinite(u)) == 12 and len(p) == 642
    c = cuts(p, u)
    # revision 1: across the step the cut forms one-frame pieces (each piece's reference is the median of
    # its own next 31 frames), so the piece holding the second note begins at the last cut
    if where == "P":
        assert not np.isfinite(u[c[-1]]), ("the second note's piece must begin on a frame not accepted", c)
    else:
        assert all(np.isfinite(u[k]) for k in c), ("every cut must fall on an accepted frame", c)
    return p, u, c[-1]


# ------------------------------------------------------------------ bars
def bar_T1(lost):
    return lost <= 1


def bar_T2(ev):
    return all(ev[m]["clean"]["take_n"] > 0 and ev[m]["clean"]["take_coverage_k2"] == 1.0
               for m in ("steadiness", "vibrato extent", "vibrato rate"))


# ------------------------------------------------------------------ round 2's takes
def r2_eval(finder_fn, shift=False):
    F2.held_notes = finder_fn
    try:
        U = {c: A.u_of(A.Z[c + "/dip"], TABLE) for c in A.ALL_CONDS}
        rows = F2.voice_rows(U, lambda k: C_SP, A.ALL_CONDS, True)
        if shift:   # revision 2: T2's must-fail input, every measured block value moved off its truth
            for r in rows:
                for b in r["blocks"]:
                    b["S"] += SHIFT["S"]
                    b["E"] += SHIFT["E"]
                    if b["R"] is not None:
                        b["R"] += SHIFT["R"]
        return F2.evaluate(rows, K_SP), rows
    finally:
        F2.held_notes = CURRENT


def trimmed(p, u):
    return finder(p, u, True)


def r2_part():
    ev_c, rows_c = r2_eval(CURRENT)
    ref = SPEC["eval"]
    keys = ("held_notes", "takes_measured", "take_n", "take_coverage_k2", "block_n")
    repro = all(ev_c[m][c][k] == ref[m][c][k] for m in ref for c in ref[m] for k in keys)
    assert repro, "T0: round 2 under the current finder must reproduce fold2.json measures.spec.eval"
    ev_t, rows_t = r2_eval(trimmed)
    ev_x, _ = r2_eval(trimmed, True)
    # the superset identity on every take of every condition, and where the finders differ
    diff = []
    for c in A.ALL_CONDS:
        for k in range(A.NF):
            m = A.Z[c + "/file"] == k
            p = F2.cents(A.Z[c + "/f"][m])
            u = A.u_of(A.Z[c + "/dip"][m], TABLE)
            cur, tr = both(p, u)
            if len(tr) != len(cur):
                diff.append(dict(cond=c, file=k, set=str(A.SET[k]), current=len(cur), trimmed=len(tr)))
    T2 = dict(must_pass_current=bar_T2(ev_c), must_fail_shifted=bar_T2(ev_x), outcome=bar_T2(ev_t))
    assert T2["must_pass_current"] and not T2["must_fail_shifted"], T2
    pick = lambda ev: {m: {c: {k: ev[m][c][k] for k in keys} for c in ev[m]} for m in ev}
    return dict(reproduces_fold2=repro, current=pick(ev_c), trimmed=pick(ev_t), takes_where_finders_differ=diff, T2=T2)


# ------------------------------------------------------------------ part B
def ladder_n(p, u):
    """fold3_ladder.ladder, with the take and every rung measured on the first n blocks, n = 2..B."""
    notes, bl, tk = L.measure(p, u)
    if tk is None:
        return None
    start = lambda fr, b: int(fr[b["b0"]])
    def keyed(notes_, bl_):
        out, i = {}, 0
        for fr, con, acc in notes_:
            for b in A.block_measures(con):
                out[start(fr, b)] = bl_[i]
                i += 1
        assert i == len(bl_)
        return out
    kb = keyed(notes, bl)
    order = sorted(kb)
    B = len(order)
    ch = L.full_change(p, notes)
    Fm = float(np.max(np.abs(ch)))
    amax = min(1.0, L.LIMIT / Fm) if Fm > 0 else 1.0
    rungs = []
    for k in range(1, L.K + 1):
        nr, br, _ = L.measure(p + ch * (k * amax / L.K), u)
        rungs.append(keyed(nr, br))
    res = {}
    for n in range(2, B + 1):
        sub = order[:n]
        t = F2.take([kb[s] for s in sub], "S", K_SP["S"])
        nk = None
        for k in range(1, L.K + 1):
            r = rungs[k - 1]
            if all(s in r for s in sub) and L.improved(t, F2.take([r[s] for s in sub], "S", K_SP["S"])):
                nk = k
                break
        res[n] = dict(next_k=nk, strength=None if nk is None else nk * amax / L.K, S=t[0], u=t[1])
    # B2, the floor: u = kappa * mean tracking u on all B blocks, for the take and each rung
    def floor(blocks):
        v = np.array([b["S"] for b in blocks])
        return float(v.mean()), float(K_SP["S"] * np.mean([b["uS"] for b in blocks]))
    tf = floor([kb[s] for s in order])
    fk = next((k for k in range(1, L.K + 1) if all(s in rungs[k - 1] for s in order)
               and L.improved(tf, floor([rungs[k - 1][s] for s in order]))), None)
    assert tf[1] <= tk[1] + 1e-12   # the floor's u is never wider (by construction: a sanity assertion)
    return dict(B=B, alpha_max=amax, by_n=res, floor_next_k=fk, floor_strength=None if fk is None else fk * amax / L.K,
                floor_u=tf[1], u=tk[1])


def part_B(finder_fn):
    F2.held_notes = finder_fn
    try:
        out = {}
        for cond in ("original", "clean"):
            U = A.u_of(A.Z[cond + "/dip"], TABLE)
            rows = []
            for k in range(A.NF):
                m = A.Z[cond + "/file"] == k
                f = A.Z[cond + "/f"][m]
                r = ladder_n(F2.cents(f), np.where(np.isnan(f), np.inf, U[m]))
                if r is not None:
                    r.update(file=k, set=str(A.SET[k]))
                    rows.append(r)
            out[cond] = rows
        return out
    finally:
        F2.held_notes = CURRENT


def summarise_B(rows):
    def med(x):
        return None if not x else round(float(np.median(x)), 4)
    s = dict(takes=len(rows), blocks={str(b): sum(r["B"] == b for r in rows) for b in sorted({r["B"] for r in rows})})
    per_n = {}
    for n in range(2, max(r["B"] for r in rows) + 1):
        rr = [r for r in rows if r["B"] >= n]
        st = [r["by_n"][n]["strength"] for r in rr if r["by_n"][n]["strength"] is not None]
        per_n[str(n)] = dict(takes=len(rr), with_step=len(st), median_strength=med(st),
                             median_u=med([r["by_n"][n]["u"] for r in rr]))
    s["per_n"] = per_n
    four = [r for r in rows if r["B"] >= 4]
    both_ = [r for r in four if r["by_n"][2]["strength"] is not None and r["by_n"][4]["strength"] is not None]
    s["B1"] = dict(takes_4_blocks=len(four), step_at_2=sum(r["by_n"][2]["strength"] is not None for r in four),
                   step_at_4=sum(r["by_n"][4]["strength"] is not None for r in four),
                   step_at_B=sum(r["by_n"][r["B"]]["strength"] is not None for r in four),
                   paired=len(both_), paired_median_2=med([r["by_n"][2]["strength"] for r in both_]),
                   paired_median_4=med([r["by_n"][4]["strength"] for r in both_]),
                   paired_fell=sum(r["by_n"][4]["strength"] < r["by_n"][2]["strength"] for r in both_),
                   paired_rose=sum(r["by_n"][4]["strength"] > r["by_n"][2]["strength"] for r in both_),
                   prediction_holds=None)
    b1 = s["B1"]
    b1["prediction_holds"] = bool(b1["step_at_4"] > b1["step_at_2"] and b1["paired"] and b1["paired_median_4"] < b1["paired_median_2"])
    atB = [r["by_n"][r["B"]]["strength"] for r in rows if r["by_n"][r["B"]]["strength"] is not None]
    fl = [r["floor_strength"] for r in rows if r["floor_strength"] is not None]
    s["B2"] = dict(step_at_B=len(atB), median_strength_at_B=med(atB), floor_step=len(fl), median_floor_strength=med(fl),
                   floor_strength_min=None if not fl else round(min(fl), 4), floor_strength_max=None if not fl else round(max(fl), 4),
                   median_u=med([r["u"] for r in rows]), median_floor_u=med([r["floor_u"] for r in rows]))
    return s


def check_B0(rows_by_cond):
    f3 = json.loads((A.T.OUT / "fold3_ladder.json").read_text())
    res = {}
    for cond, rows in rows_by_cond.items():
        ref = {r["file"]: r["next_k"] for r in f3[cond]["rows"] if r["measured"]}
        assert sorted(ref) == sorted(r["file"] for r in rows), cond
        mine = [r["by_n"][r["B"]]["next_k"] for r in rows]
        theirs = [ref[r["file"]] for r in rows]
        rot = theirs[1:] + theirs[:1]
        res[cond] = dict(must_pass=mine == theirs, must_fail=mine == rot, takes=len(rows))
        assert res[cond]["must_pass"] and not res[cond]["must_fail"], (cond, res[cond])
    return res


# ------------------------------------------------------------------ E-004's renderings
_R = None
STASH = {}


def r4():
    """E-004 r4_held, loaded with E-004's own fold and fold3 (E-002 has a fold.py of its own)."""
    global _R
    if _R is None:
        def load(name, path):
            spec = importlib.util.spec_from_file_location(name, path)
            m = importlib.util.module_from_spec(spec)
            sys.modules[name] = m
            spec.loader.exec_module(m)
            return m
        saved = sys.modules.get("fold")
        load("fold", E004 / "fold.py")
        load("fold3", E004 / "fold3.py")
        _R = load("r4_held", E004 / "r4_held.py")
        if saved is not None:
            sys.modules["fold"] = saved
        _R.held_blocks = spy_blocks
    return _R


def spy_blocks(x):
    """r4_held.held_blocks (lines 307-316), returning the same, and stashing both finders' held notes."""
    c = _R.ctx()
    yin, A4 = c["yin"], c["A"]
    idx, f, dip = yin.yin(x)
    f = yin.in_range(f, 3.0)
    u = np.where(np.isnan(f), np.inf, A4.u_of(np.nan_to_num(dip, nan=1.0), c["table"]))
    p = F2.cents(f)
    assert same_notes(c["fold2"].held_notes(p, u), CURRENT(p, u))
    cur, tr = both(p, u)
    STASH.update(idx=idx, cur=cur, tr=tr)
    return [(int(idx[fr[0]]), int(idx[fr[-1]])) for fr, _, _ in cur], [len(A4.block_measures(con)) for _, con, _ in cur]


def jobs(squillo):
    """r4_held.jobs as round 4 ran it: its 9 items, then the 30 phrases squillo shipped then (the 39 it
    ships now, less those 9), seeds in that order; each job asserted equal to its cached rendering's."""
    R = r4()
    new = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(R.ITEMS_OUT.glob("*.json"))]
    ids = {o["phrase_id"] for o in new}
    old = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((squillo / "fixtures/slice/phrases").glob("*.json"))]
    old = [o for o in old if o["phrase_id"] not in ids]
    assert len(new) == 9 and len(old) == 30, (len(new), len(old))
    out, seed = [], R.SEED0
    for o in new + old:
        for v in R.ctx()["e5run"].VOICES:
            for sigma in (0, 20):
                for vib in (0, 1):
                    seed += 1
                    cached = json.loads((R.CACHE / f"{seed}.json").read_text())
                    assert (cached["id"], cached["voice"], cached["sigma"], cached["vib"]) == (o["phrase_id"], v, sigma, vib)
                    out.append((o["phrase_id"], o["melody"], v, sigma, vib, seed))
    return out, sorted(ids)


def one(job):
    R = r4()
    r = R.one(job)
    cached = json.loads((R.CACHE / f"{job[5]}.json").read_text())
    assert r["held"] == [list(h) for h in cached["held"]] or r["held"] == [tuple(h) for h in cached["held"]], job[:1] + job[2:]
    assert r["blocks"] == cached["blocks"] and r["total_blocks"] == cached["total_blocks"], job[:1] + job[2:]
    c = R.ctx()
    idx = STASH["idx"]
    mel = job[1]
    durs = [Fraction(n["quarters"]) * 60 / mel["tempo_qpm"] for n in mel["notes"]]
    starts = np.concatenate([[0.0], np.cumsum([float(d) for d in durs])[:-1]]) + 0.1
    t = c["e5run"].HOP * (idx + 1) / 48000 - c["e5run"].LAG_S   # E-005 run.track's frame time (r4_diag.py)
    out = dict(id=job[0], voice=job[2], sigma=job[3], vib=job[4], seed=job[5], seconds=r["seconds"])
    for name in ("cur", "tr"):
        held = [(int(idx[fr[0]]), int(idx[fr[-1]])) for fr, _, _ in STASH[name]]
        blocks = [len(c["A"].block_measures(con)) for _, con, _ in STASH[name]]
        notes = []
        for k, d in enumerate(durs):
            if int(d * 125) < 250:
                continue
            fr = np.nonzero((t >= starts[k]) & (t < starts[k] + float(d)))[0]
            found = any(h[0] <= idx[i] <= h[1] for h in held for i in fr)
            notes.append(dict(note=k, found=bool(found)))
        out[name] = dict(held=held, blocks=blocks, total_blocks=int(sum(blocks)), written_held=notes)
    assert out["cur"]["blocks"] == r["blocks"]
    return out


def run_all(js):
    CACHE.mkdir(parents=True, exist_ok=True)
    todo = [j for j in js if not (CACHE / f"{j[5]}.json").exists()]
    print(len(js) - len(todo), "cached,", len(todo), "to run", flush=True)
    t0 = time.time()
    with get_context("fork").Pool(POOL) as p:
        for k, r in enumerate(p.imap_unordered(one, todo, chunksize=1), 1):
            (CACHE / f"{r['seed']}.json").write_text(json.dumps(r) + "\n")
            if k % 50 == 0:
                print(k, "done", round(time.time() - t0), "s", flush=True)
    return time.time() - t0


def wilson(k, n):
    return L.wilson(k, n) if n else None


def r4_part(squillo):
    R = r4()
    js, new = jobs(squillo)
    rows = [json.loads((CACHE / f"{j[5]}.json").read_text()) for j in js]
    assert len(rows) == 936 and all(r["seed"] == j[5] for r, j in zip(rows, js))
    held = json.loads((R.RES / "held.json").read_text())["per_item"]
    diag = json.loads((R.RES / "diag.json").read_text())
    # T0: diag's 26 renderings reproduce, note by note, under the current finder
    by = {(r["id"], r["voice"], r["sigma"], r["vib"]): r for r in rows}
    for d in diag["rows"]:
        r = by[(d["id"], d["voice"], d["sigma"], d["vib"])]
        assert [n["note"] for n in d["notes"]] == [n["note"] for n in r["cur"]["written_held"]], d["id"]
        assert [n["cause"] == "found" for n in d["notes"]] == [n["found"] for n in r["cur"]["written_held"]], d["id"]
    out = dict(renderings=len(rows))
    for name in ("cur", "tr"):
        def lost(sel):
            ns = [n for r in rows if sel(r) for n in r[name]["written_held"]]
            k = sum(not n["found"] for n in ns)
            return dict(written=len(ns), lost=k, lost_wilson95=wilson(k, len(ns)))
        per = {}
        for pid in sorted(held):
            rs = [r for r in rows if r["id"] == pid]
            b = np.array([r[name]["total_blocks"] for r in rs])
            per[pid] = dict(rule2=held[pid]["rule2"], two_blocks=int((b >= 2).sum()), renderings=len(rs),
                            min=int(b.min()), max=int(b.max()))
        one_held = diag["share"]["one_held_note_items"]
        k1 = [sum(per[k]["two_blocks"] for k in one_held), sum(per[k]["renderings"] for k in one_held)]
        out[name] = dict(new_items=lost(lambda r: r["id"] in new), all_items=lost(lambda r: True),
                         one_held_new_two_blocks=k1, one_held_new_two_blocks_wilson95=wilson(*k1),
                         bar_B_items=sorted(k for k in per if per[k]["two_blocks"] == per[k]["renderings"]),
                         per_item=per)
    assert out["cur"]["new_items"]["lost"] == diag["share"]["lost"] and out["cur"]["new_items"]["written"] == diag["share"]["held_notes"]
    assert out["cur"]["one_held_new_two_blocks"] == diag["share"]["two_blocks_one_held"]
    out["T0_reproduces_diag"] = True
    out["T1"] = dict(must_fail_current=bar_T1(out["cur"]["new_items"]["lost"]), outcome=bar_T1(out["tr"]["new_items"]["lost"]))
    assert not out["T1"]["must_fail_current"]
    out["changed"] = [dict(id=r["id"], voice=r["voice"], sigma=r["sigma"], vib=r["vib"], current=r["cur"]["total_blocks"],
                           trimmed=r["tr"]["total_blocks"]) for r in rows if r["cur"]["total_blocks"] != r["tr"]["total_blocks"]]
    return out


# ------------------------------------------------------------------ checks
def checks(squillo):
    res = {}
    P, Q = constructed("P"), constructed("Q")
    for name, (p, u, cut) in (("P", P), ("Q", Q)):
        cur, tr = both(p, u)
        res[name] = dict(cut=int(cut), current=[(int(f[0]), int(f[-1])) for f, _, _ in cur],
                         trimmed=[(int(f[0]), int(f[-1])) for f, _, _ in tr])
    res["P_must_pass_trim_recovers"] = len(res["P"]["trimmed"]) == 2 and len(res["P"]["current"]) < 2
    res["Q_must_fail_trim_recovers"] = len(res["Q"]["trimmed"]) > len(res["Q"]["current"])
    assert res["P_must_pass_trim_recovers"] and not res["Q_must_fail_trim_recovers"], res
    res["T1_must_pass_on_P"] = bar_T1(2 - len(res["P"]["trimmed"]))
    assert res["T1_must_pass_on_P"]
    # T3: squillo's fixtures, no change; its must-fail is P, where the finders differ
    sq = {}
    for name in ("metrics/held-steady.wav", "metrics/held-wobble.wav", "metrics/held-vibrato.wav", "signal/sine-220hz.wav"):
        raw, x = L.wav_samples(squillo / "fixtures" / name)
        assert L.hashlib.sha256(raw).hexdigest() in (squillo / "fixtures/MANIFEST.md").read_text(), name
        p, u = L.fixture_row(x)
        cur, tr = both(p, u)
        F2.held_notes = trimmed
        try:
            t_tr = L.measure(p, u)[2]
        finally:
            F2.held_notes = CURRENT
        sq[name] = dict(same_notes=same_notes(cur, tr), same_take=t_tr == L.measure(p, u)[2],
                        held=[(int(f[0]), int(f[-1])) for f, _, _ in tr])
    res["T3_fixtures"] = sq
    res["T3_must_pass"] = all(v["same_notes"] and v["same_take"] for v in sq.values())
    res["T3_must_fail_on_P"] = same_notes(*both(P[0], P[1]))
    assert res["T3_must_pass"] and not res["T3_must_fail_on_P"]
    return res


def main():
    if CMD == "check":
        print(json.dumps(checks(SQ), indent=1))
    elif CMD == "sample":
        js, _ = jobs(SQ)
        R = r4()
        secs = {}
        for j in js:
            mel = j[1]
            secs[j[0]] = sum(float(Fraction(n["quarters"])) for n in mel["notes"]) * 60 / mel["tempo_qpm"]
        longest, shortest = max(secs, key=secs.get), min(secs, key=secs.get)
        pick = [j for j in js if j[0] in (longest, shortest, "held-ah", "ode-to-joy") and j[2] in ("bass", "soprano_high")]
        t0 = time.time()
        with get_context("fork").Pool(POOL) as p:
            res = p.map(one, pick, chunksize=1)
        wall = time.time() - t0
        total, part = sum(secs[j[0]] + 0.2 for j in js), sum(secs[j[0]] + 0.2 for j in pick)
        t1 = time.time()
        ev, _ = r2_eval(trimmed)
        r2_s = time.time() - t1
        t2 = time.time()
        part_B(CURRENT)
        b_s = time.time() - t2
        out = dict(items=sorted({j[0] for j in pick}), renderings=len(pick), wall_s=wall, estimate_renderings_s=wall * total / part,
                   r2_eval_s=r2_s, part_B_one_finder_s=b_s)
        (HERE / "results" / "r5_sample.json").write_text(json.dumps(out, indent=1) + "\n")
        print(json.dumps(out, indent=1))
    elif CMD == "run":
        js, _ = jobs(SQ)
        print("run", round(run_all(js)), "s")
    elif CMD == "analyse":
        t0 = time.time()
        rep = dict(rules="see the docstring", spec=dict(table=SPEC["table"], c=C_SP, kappa=K_SP))
        rep["checks"] = checks(SQ)
        rep["r2"] = r2_part()
        B = {"current": part_B(CURRENT), "trimmed": part_B(trimmed)}
        rep["B0"] = check_B0(B["current"])
        rep["B"] = {f: {c: summarise_B(rows) for c, rows in v.items()} for f, v in B.items()}
        rep["B_rows"] = {f: {c: [dict(file=r["file"], set=r["set"], B=r["B"], alpha_max=r["alpha_max"],
                                      strength={str(n): x["strength"] for n, x in r["by_n"].items()},
                                      u={str(n): x["u"] for n, x in r["by_n"].items()},
                                      floor_strength=r["floor_strength"], floor_u=r["floor_u"]) for r in rows]
                             for c, rows in v.items()} for f, v in B.items()}
        rep["r4"] = r4_part(SQ)
        rep["seconds"] = round(time.time() - t0, 1)
        OUT.write_text(json.dumps(rep, indent=1, default=lambda o: bool(o) if isinstance(o, np.bool_) else
                                  (None if isinstance(o, float) and not np.isfinite(o) else str(o))) + "\n")
        print(json.dumps({k: v for k, v in rep.items() if k not in ("B_rows",)}, indent=1, default=str)[:20000])


if __name__ == "__main__":
    main()
