"""E-002 round 2, fold into squillo (iteration 34): the per-frame pitch u,
and steadiness, vibrato extent and vibrato rate as take measures. Crude
experiment code. Needs data/cache/r2_frames.npz from r2_run.py.

    uv run python fold2.py <squillo>/fixtures   # writes <dir>/signal, <dir>/metrics WAVs and results/fold2.json

What round 2 left for a spec, and what this adds:

1. One aperiodicity table. Round 2 fitted the per-frame u rule on each fold
   of singers and tested it on the other (result 19). A spec needs one table:
   the same rule fitted on all 20 singers, and the per-bin larger of the two
   folds' tables as the stricter alternative, each reported with what it
   accepts and covers.
2. Held notes found from the measured contour. Round 2 cut held notes from
   the truth (README, Definitions), which a product never has. Here they are
   cut from the measured pitch alone, by the rule written below and in
   squillo's metrics MT-010, and the block and take measures are compared
   with the same functions on the truth over the same frames.
3. The constants: the tracking factor c per measure and the split-half
   factor kappa, fitted on all singers with the table of step 1.
4. Squillo's fixtures, by the formulas squillo's fixtures/MANIFEST.md
   records, and every scenario squillo iteration 34 writes, checked with the
   rules above. Each check is itself run on a case it must fail (S15).

Conditions of the fixtures, written before generating them (S15), each
asserted on the output:
- held notes: 220 Hz carrier, frequency 220 * (1 + a sin(2 pi r t)) Hz, so
  every frame's pitch inside E2..C6 (yin.E2, yin.C6); for the vibrato
  fixture, SG-007's conditions: extent inside +-50 cents, rate at most 7 Hz,
  computed from the exact frequency formula at every sample; amplitude 0.5.
- the aperiodic tone: a 220 Hz sine plus a second sine at 220 * sqrt(2) Hz
  whose amplitude rises linearly over the second from 0 to b, b the smallest
  of 0.01 .. 0.2 (step 0.01) whose frames' aperiodicity spans the table's
  bins from the first to a refused one (found on a float64 draft, asserted on
  the file); peak at most 1. A first form, a constant b, gave every frame
  nearly the same aperiodicity and spanned no bins.
"""
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import numpy as np
from scipy.signal import filtfilt

import r2_analyse as A
import yin
from yin import SR

OUTDIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/e002-fold2")
FIT, ALL = A.FIT_CONDS, A.ALL_CONDS
Z, FOLD, SET = A.Z, A.FOLD, A.SET
B2, BV = A.B2, A.BV
CHOSEN = "max"  # squillo Q-019 part 1: the per-bin larger of the two folds' tables
MAX_GAP, MAX_FILL, MIN_LEN, TRIM, BLOCK, SPLIT, OCT = 12, 0.25, 250, 62, 125, 60.0, 600.0
R = {}


# ------------------------------------------------------------------ 1. tables
def masks(sel):
    return {c: sel(Z[c + "/file"]) for c in ALL}


def check_tables():
    t_odd = A.fit_u(masks(lambda f: FOLD[f] == 1))
    t_even = A.fit_u(masks(lambda f: FOLD[f] == 0))
    old = json.loads((A.T.OUT / "r2_results.json").read_text())["frames"]["tables"]
    # the cache reproduces round 2's committed tables
    assert np.allclose(t_odd, old["fit on odd singers"]) and np.allclose(t_even, old["fit on even singers"])
    t_all = A.fit_u(masks(lambda f: np.ones(len(f), bool)))
    t_max = np.maximum(t_odd, t_even)
    return dict(odd=t_odd, even=t_even, all=t_all, max=t_max)


def coverage(table, fold=None):
    out = {}
    for c in ALL:
        e, ok = A.ERR[c]
        fm = np.ones(len(e), bool) if fold is None else FOLD[Z[c + "/file"]] == fold
        valid = Z[c + "/valid"] & fm
        m = ok & fm
        u = A.u_of(Z[c + "/dip"][m], table)
        acc = np.isfinite(u)
        ea = np.abs(e[m][acc])
        out[c] = dict(accepted_share=float(acc.sum() / valid.sum()), coverage_k2=float(np.mean(ea <= 2 * u[acc])),
                      accepted=int(acc.sum()))
    return out


SPEC_TABLE = None


def frame_part():
    global SPEC_TABLE
    T = check_tables()
    t = T[CHOSEN]
    SPEC_TABLE = np.array([t[0]] + [math.ceil(x * 100) / 100 if np.isfinite(x) else np.inf for x in t[1:]])
    assert t[0] == math.sqrt(3) and np.all(SPEC_TABLE >= t)
    res = {"tables": {k: [None if not np.isfinite(x) else float(x) for x in v] for k, v in T.items()}, "bins": A.BINS}
    # check of the check: coverage with u = 1e9 must be 1, with u = 1e-9 must be below 0.01
    big, small = np.full(8, 1e9), np.full(8, 1e-9)
    assert coverage(big)["clean"]["coverage_k2"] == 1.0 and coverage(small)["clean"]["coverage_k2"] < 0.01
    res["in_sample"] = {k: coverage(T[k]) for k in ("all", "max")}
    # the stricter table tested on each fold (half of it fitted there, so not held out)
    res["max_by_fold"] = {f"{'odd' if f else 'even'}": coverage(T["max"], f) for f in (1, 0)}
    # the procedure cross-validated: round 2 result 19, recomputed
    res["cross_validated"] = {f"fit {'odd' if f else 'even'}, test other": coverage(T["odd" if f else "even"], 1 - f) for f in (1, 0)}
    return T, res


# ------------------------------------------------------------------ 2. held notes from the measured contour
def cents(f):
    return 1200 * np.log2(f / 440.0)


def held_notes(p, u):
    """Held notes from a measured contour alone. p: cents re A4 per frame (nan = no pitch), u per frame
    (inf = refused). Returns a list of (frames, contour, accepted mask), frames as indices into p.

    1. A frame is accepted when it has a pitch and a finite u.
    2. Runs: from an accepted frame to the last accepted frame before a gap of more than 12 frames.
    3. Within a run, an accepted frame more than 600 cents from the run's median is dropped (octave errors).
    4. The run's contour is filled linearly across its gaps and low-passed at 2 Hz (order-2 Butterworth,
       forward and backward); it is cut where the low-passed contour leaves the median of the piece's first
       31 frames (0.25 s) by more than 60 cents.
    5. A piece is a held note when it is at least 250 frames (2 s) long, no gap in it exceeds 12 frames and
       at most 25 % of its frames are filled.
    """
    acc = ~np.isnan(p) & np.isfinite(u)
    out = []
    n = len(p)
    i = 0
    while i < n:
        if not acc[i]:
            i += 1
            continue
        j, last = i, i
        while j < n and j - last <= MAX_GAP + 1:
            if acc[j]:
                last = j
            j += 1
        run = np.arange(i, last + 1)
        i = last + 1
        if len(run) < MIN_LEN:
            continue
        a = acc[run].copy()
        med = np.median(p[run][a])
        a &= np.abs(np.where(a, p[run], med) - med) <= OCT
        if a.sum() < 2:
            continue
        x = np.arange(len(run))
        con = np.interp(x, x[a], p[run][a])
        lp = filtfilt(*B2, con)
        s0 = 0
        while s0 < len(run):
            ref = np.median(lp[s0:s0 + 31])
            s1 = s0 + 1
            while s1 < len(run) and abs(lp[s1] - ref) <= SPLIT:
                s1 += 1
            seg = slice(s0, s1)
            aa = a[seg]
            if s1 - s0 >= MIN_LEN and aa[0] and aa[-1]:
                gaps = np.diff(np.concatenate([[0], (~aa).astype(int), [0]]))
                st, en = np.nonzero(gaps == 1)[0], np.nonzero(gaps == -1)[0]
                if (not len(st) or (en - st).max() <= MAX_GAP) and (~aa).mean() <= MAX_FILL:
                    # re-fill on the piece alone, so a piece never borrows from its neighbours
                    xx = np.arange(s1 - s0)
                    out.append((run[seg], np.interp(xx, xx[aa], p[run][seg][aa]), aa))
            s0 = s1
    return out


def blocks(con, u, acc, c, rate_gate):
    """1 s blocks after trimming 62 frames at each end; round 2's block functions; per block the tracking
    u of each measure (c x rms u of its accepted frames; for the rate, divided by the extent). With
    rate_gate, a block gives a rate only when its extent exceeds twice its tracking u."""
    bm = A.block_measures(con)
    for b in bm:
        uu = u[b["b0"]:b["b0"] + BLOCK][acc[b["b0"]:b["b0"] + BLOCK]]
        rms = float(np.sqrt(np.mean(uu ** 2)))
        b["uS"], b["uE"] = c["S"] * rms, c["E"] * rms
        b["uR"] = c["R"] * rms / b["E"] if b["E"] > 0 else np.inf
        if rate_gate and b["R"] is not None and not b["E"] > 2 * b["uE"]:
            b["R"] = None
    return bm


def take(bl, key, kappa=1.0):
    v = np.array([b[key] for b in bl if b[key] is not None])
    ut = np.array([b["u" + key] for b in bl if b[key] is not None])
    if len(v) < 2:
        return None
    return float(v.mean()), float(kappa * np.sqrt(v.var(ddof=1) / len(v) + ut.mean() ** 2)), len(v)


def voice_rows(U, c_by_file, cond_list, rate_gate):
    """For every file under every condition: its held notes from the measured contour, the blocks, and
    the same block functions on the truth over the same frames (only where every frame is valid)."""
    rows = []
    for c in cond_list:
        fk = Z[c + "/file"]
        for k in range(A.NF):
            m = fk == k
            idx = Z[c + "/idx"][m]
            assert np.all(np.diff(idx) == 1)
            p = cents(Z[c + "/f"][m])
            u = U[c][m]
            notes = held_notes(p, u)
            bl_all, tr_all, n_eval = [], [], 0
            for fr, con, acc in notes:
                bl = blocks(con, u[fr], acc, c_by_file(k), rate_gate)
                if c != "original" and Z[c + "/valid"][m][fr].all():
                    n_eval += 1
                    tb = A.block_measures(cents(Z[c + "/f_true"][m][fr]))
                    if rate_gate:
                        for b, t in zip(bl, tb):
                            if b["R"] is None:
                                t["R"] = None
                    for b, t in zip(bl, tb):
                        b["true"] = t
                bl_all += bl
            rows.append(dict(cond=c, file=k, notes=len(notes), notes_eval=n_eval, blocks=bl_all))
    return rows


def fit_c(rows, fold_sel):
    c = {}
    for key in "SER":
        r = []
        for row in rows:
            if row["cond"] not in FIT or not fold_sel(row["file"]):
                continue
            for b in row["blocks"]:
                t = b.get("true")
                if t is None or b[key] is None or t[key] is None:
                    continue
                r.append(abs(b[key] - t[key]) / (2 * b["u" + key]))
        c[key] = float(np.percentile(r, 95))
    return c


def evaluate(rows, kappa):
    out = {}
    for key, name in (("S", "steadiness"), ("E", "vibrato extent"), ("R", "vibrato rate")):
        res = {}
        for c in ALL:
            rr = [r for r in rows if r["cond"] == c]
            if not rr:
                continue
            be, bc, tc, te, pairs, n_takes, n_notes = [], [], [], [], [], 0, 0
            for r in rr:
                n_notes += r["notes"]
                tk = take(r["blocks"], key, kappa.get(key, 1.0))
                if tk is None:
                    continue
                n_takes += 1
                ev = [b for b in r["blocks"] if "true" in b and b[key] is not None and b["true"][key] is not None]
                for b in ev:
                    be.append(b[key] - b["true"][key]); bc.append(abs(b[key] - b["true"][key]) <= 2 * b["u" + key])
                if len(ev) == len([b for b in r["blocks"] if b[key] is not None]) and len(ev) >= 2:
                    tv = np.mean([b["true"][key] for b in ev])
                    te.append(tk[0] - tv); tc.append(abs(tk[0] - tv) <= 2 * tk[1])
                vb = [b for b in r["blocks"] if b[key] is not None]
                if len(vb) >= 4:
                    h = len(vb) // 2
                    a, b_ = take(vb[:h], key, kappa.get(key, 1.0)), take(vb[h:2 * h], key, kappa.get(key, 1.0))
                    pairs.append((a[0], a[1], b_[0], b_[1], SET[r["file"]]))
            ratio = [abs(a - b) / (2 * math.hypot(ua, ub)) for a, ua, b, ub, _ in pairs]
            res[c] = dict(held_notes=n_notes, takes_measured=n_takes, takes_of=len(rr),
                          block_n=len(be), block_p95_abs_err=float(np.percentile(np.abs(be), 95)) if be else None,
                          block_coverage_k2=float(np.mean(bc)) if bc else None,
                          take_n=len(te), take_median_err=float(np.median(te)) if te else None,
                          take_p95_abs_err=float(np.percentile(np.abs(te), 95)) if te else None,
                          take_coverage_k2=float(np.mean(tc)) if tc else None,
                          split_half_n=len(pairs), split_half_false_change=float(np.mean([x > 1 for x in ratio])) if ratio else None,
                          split_half_p95_ratio=float(np.percentile(ratio, 95)) if len(ratio) >= 10 else None,
                          split_half_sets=sorted(set(s for *_, s in pairs)))
        out[name] = res
    return out


def measure_part(T):
    # 2a. cross-validated: u from the table fitted on the other fold, c fitted on the other fold, kappa 1
    U_cv = {}
    for c in ALL:
        u = np.full(len(Z[c + "/f"]), np.inf)
        for f in (1, 0):
            m = FOLD[Z[c + "/file"]] == 1 - f
            u[m] = A.u_of(Z[c + "/dip"][m], T["odd" if f else "even"])
        U_cv[c] = u
    one = dict(S=1.0, E=1.0, R=1.0)
    res = {}
    for gate in (False, True):
        rows0 = voice_rows(U_cv, lambda k: one, ALL, gate)
        cf = {f: fit_c(rows0, lambda k, f=f: FOLD[k] == f) for f in (1, 0)}
        rows = voice_rows(U_cv, lambda k: cf[1 - FOLD[k]], ALL, gate)
        ev = evaluate(rows, {})
        res[f"cv, rate gate {gate}"] = dict(c_by_fit_fold={("odd" if f else "even"): v for f, v in cf.items()}, eval=ev)
    # 2b. the constants for the spec: the chosen table, c on all singers, kappa from the
    # split halves of the clean re-syntheses (and of the original takes, which need no truth)
    U_all = {c: A.u_of(Z[c + "/dip"], T[CHOSEN]) for c in ALL}
    rows0 = voice_rows(U_all, lambda k: one, ALL, True)
    c_all = fit_c(rows0, lambda k: True)
    rows = voice_rows(U_all, lambda k: c_all, ALL, True)
    ev1 = evaluate(rows, {})
    kappa = {}
    for key, name in (("S", "steadiness"), ("E", "vibrato extent"), ("R", "vibrato rate")):
        cand = [ev1[name][c]["split_half_p95_ratio"] for c in ("clean", "original")]
        cand = [x for x in cand if x is not None]
        kappa[key] = max([1.0] + cand) if cand else None
    ev2 = evaluate(rows, {k: v for k, v in kappa.items() if v is not None})
    res["final"] = dict(c=c_all, kappa=kappa, eval_kappa1=ev1, eval_kappa=ev2)
    # squillo's constants: each rounded up (the stricter side, S11) at two significant figures for c,
    # two decimals for kappa; the table's finite u above sqrt 3 up at two decimals. Re-evaluated with them.
    c_sp = {k: float(sig_up(v, 2)) for k, v in c_all.items()}
    k_sp = {k: math.ceil(v * 100) / 100 for k, v in kappa.items()}
    U_sp = {c: A.u_of(Z[c + "/dip"], SPEC_TABLE) for c in ALL}
    rows = voice_rows(U_sp, lambda k: c_sp, ALL, True)
    res["spec"] = dict(table=[None if not np.isfinite(x) else float(x) for x in SPEC_TABLE], c=c_sp, kappa=k_sp,
                       frames=coverage(SPEC_TABLE), frames_even_held_out=coverage(SPEC_TABLE, 0),
                       eval=evaluate(rows, k_sp))
    return res, c_sp, k_sp


def sig_up(v, n):
    e = math.floor(math.log10(abs(v))) - n + 1
    return math.ceil(v / 10 ** e) * 10 ** e


# ------------------------------------------------------------------ 4. fixtures
pi = math.pi


def wav(samples):
    data = b"".join(struct.pack("<f", s) for s in samples)
    fmt = struct.pack("<HHIIHHH", 3, 1, SR, SR * 4, 4, 32, 0)
    body = (b"WAVE" + b"fmt " + struct.pack("<I", 18) + fmt
            + b"fact" + struct.pack("<I", 4) + struct.pack("<I", len(samples))
            + b"data" + struct.pack("<I", len(data)) + data)
    return b"RIFF" + struct.pack("<I", len(body)) + body


N5 = 240_000  # 5 s
FIX = {
    # f(t) = 220 (1 + 0.023 sin(2 pi 5.5 t)): a 5.5 Hz vibrato
    "metrics/held-vibrato.wav": (N5, lambda n: 0.5 * math.sin(2 * pi * 220 * n / 48000 + 220 * 0.023 / 5.5 * (1 - math.cos(2 * pi * 5.5 * n / 48000))), 0.023, 5.5),
    # f(t) = 220 (1 + 0.012 sin(2 pi 0.5 t)): a slow wobble, one period in 2 s
    "metrics/held-wobble.wav": (N5, lambda n: 0.5 * math.sin(2 * pi * 220 * n / 48000 + 220 * 0.012 / 0.5 * (1 - math.cos(2 * pi * 0.5 * n / 48000))), 0.012, 0.5),
    # f(t) = 220: a steady held note
    "metrics/held-steady.wav": (N5, lambda n: 0.5 * math.sin(2 * pi * 220 * n / 48000), 0.0, 0.0),
    # a 220 Hz sine plus a sine at 220 sqrt(2) Hz whose amplitude rises linearly from 0 to AP_B over the
    # second: no common period, and the aperiodicity grows with the second sine's amplitude
    "metrics/tone-aperiodic.wav": (48_000, lambda n: 0.5 * math.sin(2 * pi * 220 * n / 48000) + AP_B * n / 48000 * math.sin(2 * pi * 220 * math.sqrt(2) * n / 48000), None, None),
}
AP_B = None


def gen(name):
    n, fn, a, r = FIX[name]
    s = [fn(i) for i in range(n)]
    x = np.array(struct.unpack(f"<{n}f", struct.pack(f"<{n}f", *s)), dtype=np.float64)
    assert np.max(np.abs(x)) <= 1.0
    if a is not None:
        t = np.arange(n) / SR
        f = 220 * (1 + a * np.sin(2 * pi * r * t))
        assert f.min() >= yin.E2 and f.max() <= yin.C6
        ext = 1200 * np.log2(f / 220)
        if name.endswith("vibrato.wav"):
            assert ext.max() <= 50 and ext.min() >= -50 and r <= 7, (ext.min(), ext.max())
        return x, s, dict(cents_min=float(ext.min()), cents_max=float(ext.max()))
    return x, s, {}


def truth_contour(name, idx, f):
    """The exact frequency at SG-007's instant, 384 i - 766 + P/2, P from the reported pitch."""
    _, _, a, r = FIX[name]
    P = SR / np.where(np.isnan(f), 220.0, f)
    t = (384 * idx - 766 + P / 2) / SR
    return cents(220 * (1 + a * np.sin(2 * pi * r * t)))


def metrics_of(x, table, c, kappa):
    idx, f, dip = yin.yin(x)
    f = yin.in_range(f, 3.0)
    u = np.where(np.isnan(f), np.nan, A.u_of(np.nan_to_num(dip, nan=1.0), table))
    p = cents(f)
    notes = held_notes(p, np.where(np.isnan(u), np.inf, u))
    bl = []
    for fr, con, acc in notes:
        bl += blocks(con, u[fr], acc, c, True)
    tk = {k: take(bl, k, kappa[k]) for k in "SER"}
    return dict(idx=idx, f=f, dip=dip, u=u, notes=notes, blocks=bl, take=tk)


def fixture_part(T, c, kappa):
    global AP_B
    table = SPEC_TABLE
    first_refused = A.BINS[int(np.argmax(~np.isfinite(table)))]
    # choose the aperiodic tone's final second amplitude: the smallest of 0.01 .. 0.2 (step 0.01) whose
    # frames span the first bin and reach a refused one, found on a float64 draft, then generated for real
    for b in [k / 100 for k in range(1, 21)]:
        t = np.arange(48_000) / SR
        draft = 0.5 * np.sin(2 * pi * 220 * t) + b * t * np.sin(2 * pi * 220 * np.sqrt(2) * t)
        _, fd, dd = yin.yin(draft)
        dd = dd[~np.isnan(yin.in_range(fd, 3.0))]
        if dd.min() < A.BINS[1] and dd.max() >= first_refused:
            AP_B = b
            break
    assert AP_B is not None
    out = {"aperiodic_second_amplitude": AP_B, "first_refused_dip": first_refused}
    for d in ("signal", "metrics"):
        (OUTDIR / d).mkdir(parents=True, exist_ok=True)
    M = {}
    for name in FIX:
        x, s, cond = gen(name)
        blob = wav(s)
        (OUTDIR / name).write_bytes(blob)
        m = metrics_of(x, table, c, kappa)
        M[name] = m
        row = dict(sha256=hashlib.sha256(blob).hexdigest(), bytes=len(blob), conditions=cond,
                   frames=len(m["idx"]), pitch_measured=int((~np.isnan(m["f"])).sum()),
                   accepted=int(np.isfinite(m["u"]).sum()), dip_max_measured=float(np.nanmax(np.where(np.isnan(m["f"]), np.nan, m["dip"]))),
                   dip_min_measured=float(np.nanmin(np.where(np.isnan(m["f"]), np.nan, m["dip"]))),
                   u_values={str(round(float(v), 6)): int(n) for v, n in zip(*np.unique(m["u"][np.isfinite(m["u"])], return_counts=True))},
                   held_notes=[(int(fr[0]), int(fr[-1]), int((~acc).sum())) for fr, _, acc in m["notes"]],
                   blocks=[{k: (None if b[k] is None else float(b[k])) for k in ("S", "E", "R", "uS", "uE", "uR")} for b in m["blocks"]],
                   take={k: v for k, v in m["take"].items()})
        if FIX[name][2] is not None:
            # the true take measures: the same functions on the exact contour over the same frames
            tb = []
            for fr, con, acc in m["notes"]:
                tcon = truth_contour(name, m["idx"][fr], m["f"][fr])
                tb += A.block_measures(tcon)
            row["true_blocks"] = [{k: (None if b[k] is None else float(b[k])) for k in ("S", "E", "R")} for b in tb]
            row["true_take"] = {k: (float(np.mean([b[k] for b in tb if b[k] is not None])) if any(b[k] is not None for b in tb) else None) for k in "SER"}
            row["pitch_err_max"] = float(np.nanmax(np.abs(cents(m["f"]) - truth_contour(name, m["idx"], m["f"]))))
        out[name] = row
    # the pure tones of signal: sine-220hz's aperiodicity, from squillo's committed file
    sq = OUTDIR / "signal" / "sine-220hz.wav"
    if sq.exists():
        raw = sq.read_bytes()
        k = raw.index(b"data") + 8
        xs = np.frombuffer(raw[k:], "<f4").astype(np.float64)
        ms = metrics_of(xs, table, c, kappa)
        out["signal/sine-220hz.wav"] = dict(dip_max_measured=float(np.nanmax(ms["dip"][~np.isnan(ms["f"])])),
                                            pitch_measured=int((~np.isnan(ms["f"])).sum()), held_notes=len(ms["notes"]),
                                            take={k2: v for k2, v in ms["take"].items()})
        M["signal/sine-220hz.wav"] = ms
    return out, M


def scenarios(F, M, T, kappa):
    """Every scenario squillo iteration 34 writes, as a predicate on the lab's results; each is also run on
    an input it must fail."""
    table = SPEC_TABLE
    fr = A.BINS[int(np.argmax(~np.isfinite(table)))]

    def sine_u(m):  # MT-003: every measured cell of a sine carries u = sqrt 3 exactly
        acc = np.isfinite(m["u"])
        return acc.sum() == (~np.isnan(m["f"])).sum() and np.all(m["u"][acc] == math.sqrt(3))

    def aperiodic(m):  # MT-003: u is the table's for its aperiodicity; at or above the first refused, unmeasurable
        meas = ~np.isnan(m["f"])
        ok_u = np.all(m["u"][meas & (m["dip"] < fr)] == A.u_of(m["dip"][meas & (m["dip"] < fr)], table))
        refused = meas & (m["dip"] >= fr)
        return bool(ok_u and refused.any() and np.all(~np.isfinite(m["u"][refused])) and np.isfinite(m["u"][meas]).any()
                    and len(set(m["u"][np.isfinite(m["u"])].tolist())) >= 2)

    def covers(name, key):
        tk, tr = M[name]["take"][key], F[name]["true_take"][key]
        return tk is not None and tr is not None and abs(tk[0] - tr) <= 2 * tk[1]

    def unmeasured(name):
        return all(M[name]["take"][k] is None for k in "SER")

    def improved(a, b, key):  # smaller is better for steadiness
        x1, u1, _ = M[a]["take"][key]; x2, u2, _ = M[b]["take"][key]
        return x1 - x2 > 2 * math.hypot(u1, u2)

    def changed(a, b, key):
        x1, u1, _ = M[a]["take"][key]; x2, u2, _ = M[b]["take"][key]
        return abs(x1 - x2) > 2 * math.hypot(u1, u2)

    V, W, S = "metrics/held-vibrato.wav", "metrics/held-wobble.wav", "metrics/held-steady.wav"
    sc = {
        "SG-008 sine: aperiodicity below the first bin edge": (lambda: F["signal/sine-220hz.wav"]["dip_max_measured"] < A.BINS[1],
                                                                 lambda: F[ "metrics/tone-aperiodic.wav"]["dip_max_measured"] < A.BINS[1]),
        "MT-003 sine: u = sqrt 3": (lambda: sine_u(M["signal/sine-220hz.wav"]), lambda: sine_u(M["metrics/tone-aperiodic.wav"])),
        "MT-003 aperiodic: table and refusal": (lambda: aperiodic(M["metrics/tone-aperiodic.wav"]), lambda: aperiodic(M["signal/sine-220hz.wav"])),
        "MT-009 short tone: unmeasurable": (lambda: unmeasured("signal/sine-220hz.wav"), lambda: unmeasured(V)),
        "MT-010 vibrato: extent covers": (lambda: covers(V, "E"), lambda: covers(S, "E") and F[S]["true_take"]["E"] is not None and abs(M[S]["take"]["E"][0] - F[V]["true_take"]["E"]) <= 2 * M[S]["take"]["E"][1]),
        "MT-010 vibrato: rate covers": (lambda: covers(V, "R"), lambda: M[W]["take"]["R"] is not None and abs(M[W]["take"]["R"][0] - 5.5) <= 2 * M[W]["take"]["R"][1]),
        "MT-010 steady: no rate": (lambda: M[S]["take"]["R"] is None, lambda: M[V]["take"]["R"] is None),
        "MT-010 wobble: steadiness covers": (lambda: covers(W, "S"), lambda: abs(M[S]["take"]["S"][0] - F[W]["true_take"]["S"]) <= 2 * M[S]["take"]["S"][1]),
        "MT-010 steady: 0 within steadiness and extent": (lambda: all(abs(M[S]["take"][k][0]) <= 2 * M[S]["take"][k][1] for k in "SE"), lambda: all(abs(M[W]["take"][k][0]) <= 2 * M[W]["take"][k][1] for k in "SE")),
        "MT-008 wobble -> steady: steadiness improved": (lambda: improved(W, S, "S"), lambda: improved(S, W, "S")),
        "MT-008 steady twice: no change": (lambda: not changed(S, S, "S"), lambda: not changed(W, S, "S")),
        "MT-008 steady -> vibrato: extent changed": (lambda: changed(S, V, "E"), lambda: changed(V, V, "E")),
    }
    out = {}
    for k, (must_pass, must_fail) in sc.items():
        a, b = bool(must_pass()), bool(must_fail())
        out[k] = dict(passes=a, fails_on_wrong_input=not b)
        assert a and not b, (k, a, b)
    return out


def main():
    T, fr = frame_part()
    R["frames"] = fr
    print("tables", fr["tables"])
    for k in ("all", "max"):
        print(k, {c: (round(v["accepted_share"], 3), round(v["coverage_k2"], 3)) for c, v in fr["in_sample"][k].items()})
    for k, v in fr["cross_validated"].items():
        print(k, {c: (round(x["accepted_share"], 3), round(x["coverage_k2"], 3)) for c, x in v.items()})
    mres, c, kappa = measure_part(T)
    R["measures"] = mres
    print("c", c, "kappa", kappa)
    for tag in ("cv, rate gate False", "cv, rate gate True"):
        print(tag, mres[tag]["c_by_fit_fold"])
        for name, v in mres[tag]["eval"].items():
            for cond in ("clean", "white-30", "white-20", "room-0.4", "room-0.8", "original"):
                print("  ", name, cond, v[cond])
    print("spec", {k: mres["spec"][k] for k in ("table", "c", "kappa")})
    print("spec frames", {c: (round(v["accepted_share"], 3), round(v["coverage_k2"], 3)) for c, v in mres["spec"]["frames"].items()})
    print("spec frames, even held out", {c: (round(v["accepted_share"], 3), round(v["coverage_k2"], 3)) for c, v in mres["spec"]["frames_even_held_out"].items()})
    for name, v in mres["spec"]["eval"].items():
        for cond in ("clean", "white-30", "white-20", "room-0.4", "room-0.8", "original"):
            print(" final", name, cond, v[cond])
    F, M = fixture_part(T, c, kappa)
    R["fixtures"] = F
    for k, v in F.items():
        print(k, {a: b for a, b in v.items() if a not in ("blocks", "true_blocks")} if isinstance(v, dict) else v)
    R["scenarios"] = scenarios(F, M, T, kappa)
    print(json.dumps(R["scenarios"], indent=1))
    (A.T.OUT / "fold2.json").write_text(json.dumps(R, indent=1, default=lambda o: None if isinstance(o, float) and not np.isfinite(o) else str(o)))


if __name__ == "__main__":
    main()
