"""E-002 round 10: continuity as a second witness for frames MT-003 refuses.
Crude experiment code. Same 159 known-f0 re-syntheses, conditions and
fit/test split (odd-numbered sorted singers fit) as round 9.

    uv run python r10_continuity.py      # writes results/r10_continuity.json

Fixed before running. Anchor: a frame MT-003 accepts today (YIN threshold
0.1, in range, aperiodicity < 0.02), shown as is. Witness rule, causal and
with no delay (UI-012): a frame that is not an anchor is shown if the frame
just before it is shown (anchor or witnessed), its CMND has a local minimum
under theta whose interpolated pitch lies within J cents of that previous
pitch (the closest such minimum is taken), and the last anchor is at most L
frames back. Grid: theta in {0.1, 0.2, 0.35}, J in {50, 100}, L in {25, 125}
(200 ms, 1 s). Selection on the fit singers, clean and white-20 pooled: the
largest coverage with gross (>50 cents) <= 1 % of shown frames. Pass on the
test singers: gross <= 1 % of shown, coverage above round 9's held-out
72.9 % clean and 29.5 % white-20. CIs: 95 % bootstrap over test takes (2000).
The ± of witnessed frames: the fit's p95 |error| of non-gross witnessed
frames, its coverage reported on test.
"""

import itertools
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

import r2_run as R
import r2_truth as T
import yin

CONDS = ["clean", "white-20", "white-10", "pink-10"]
GRID = list(itertools.product([0.1, 0.2, 0.35], [50, 100], [25, 125]))
OUT = Path(__file__).parent / "results" / "r10_continuity.json"


def candidates(x):
    idx, win = yin.frame_windows(np.asarray(x))
    tau_min = int(np.floor(yin.SR / 3000.0))
    tau_max = int(np.ceil(yin.SR / 63.0)) + 1
    d, dn = yin.cmnd(win, tau_max)
    cands = []
    for k in range(len(idx)):
        row = dn[k]
        t = np.arange(tau_min + 1, tau_max - 1)
        m = (row[t] < row[t - 1]) & (row[t] <= row[t + 1]) & (row[t] < 0.35)
        fs, ds = [], []
        for tt in t[m]:
            f = yin.SR / yin.parabola(d[k].astype(np.float64), int(tt))
            if not np.isnan(yin.in_range(np.array([f]), 3.0))[0]:
                fs.append(f); ds.append(row[tt])
        cands.append((np.array(fs), np.array(ds)))
    return idx, cands


def track(f_anchor, dip, cands, theta, J, L):
    n = len(f_anchor)
    out = np.full(n, np.nan)
    wit = np.zeros(n, bool)
    last_anchor = -10**9
    for k in range(n):
        if not np.isnan(f_anchor[k]) and dip[k] < 0.02:
            out[k] = f_anchor[k]; last_anchor = k; continue
        if k == 0 or np.isnan(out[k - 1]) or k - last_anchor > L:
            continue
        fs, ds = cands[k]
        ok = ds < theta
        if not ok.any():
            continue
        c = np.abs(1200 * np.log2(fs[ok] / out[k - 1]))
        j = int(np.argmin(c))
        if c[j] <= J:
            out[k] = fs[ok][j]; wit[k] = True
    return out, wit


def one(stem):
    z = np.load(T.R2 / (stem + ".npz"))
    y, f0 = z["y"].astype(np.float64), z["f0"]
    ft = T.truth_per_sample(f0, len(y))
    res = {}
    for cond in CONDS:
        sig, _ = R.condition(y, ft > 0, stem, cond)
        idx, f, dip = yin.yin(sig, threshold=0.1)
        f = yin.in_range(f, 3.0)
        _, cands = candidates(sig)
        per = {}
        for g in GRID:
            out, wit = track(f, dip, cands, *g)
            f_true, _, valid = R.frame_truth(ft, idx, out)
            o, w, t = out[valid], wit[valid], f_true[valid]
            err = np.abs(1200 * np.log2(o / t))
            per[str(g)] = dict(err=err.tolist(), wit=w.tolist())
        # today's product: anchors only
        out0 = np.where(dip < 0.02, f, np.nan)
        f_true, _, valid = R.frame_truth(ft, idx, out0)
        per["base"] = dict(err=np.abs(1200 * np.log2(out0[valid] / f_true[valid])).tolist(),
                           wit=[False] * int(valid.sum()))
        res[cond] = per
    return stem, res


def stats(res, stems, cond, key):
    e = [np.array(res[s][cond][key]["err"], float) for s in stems]
    w = [np.array(res[s][cond][key]["wit"], bool) for s in stems]
    def agg(ix):
        E = np.concatenate([e[i] for i in ix]); W = np.concatenate([w[i] for i in ix])
        sh = ~np.isnan(E)
        return sh.mean(), (sh & (E >= 50)).sum() / max(sh.sum(), 1), E, W
    return agg, len(stems)


def main():
    stems = sorted(p.stem for p in T.R2.glob("*.npz"))
    with Pool(18) as p:
        res = dict(p.map(one, stems))
    singers = sorted({T.singer_of(s) for s in stems})
    fit_s = set(singers[0::2])
    fit = [s for s in stems if T.singer_of(s) in fit_s]
    test = [s for s in stems if T.singer_of(s) not in fit_s]
    fit_table = []
    for key in ["base"] + [str(g) for g in GRID]:
        cov, gr = [], []
        E = np.concatenate([np.array(res[s][c][key]["err"], float) for s in fit for c in ["clean", "white-20"]])
        sh = ~np.isnan(E)
        fit_table.append(dict(key=key, coverage=round(float(sh.mean()), 4),
                              gross=round(float((sh & (E >= 50)).sum() / sh.sum()), 5)))
        print(fit_table[-1])
    ok = [r for r in fit_table if r["key"] != "base" and r["gross"] <= 0.01]
    chosen = max(ok, key=lambda r: r["coverage"])["key"] if ok else None
    print("chosen", chosen)
    U = None
    if chosen:
        E = np.concatenate([np.array(res[s][c][chosen]["err"], float) for s in fit for c in ["clean", "white-20"]])
        W = np.concatenate([np.array(res[s][c][chosen]["wit"], bool) for s in fit for c in ["clean", "white-20"]])
        m = W & (E < 50)
        U = float(np.percentile(E[m], 95))
    rng = np.random.default_rng(10)
    test_res = {}
    for cond in CONDS:
        row = {}
        for key in ["base", chosen] if chosen else ["base"]:
            agg, n = stats(res, test, cond, key)
            cov, gr, E, W = agg(range(n))
            boots = [agg(rng.integers(0, n, n))[:2] for _ in range(2000)]
            bc, bg = np.array(boots).T
            r = dict(coverage=round(float(cov), 4), coverage_ci=[round(float(x), 4) for x in np.percentile(bc, [2.5, 97.5])],
                     gross=round(float(gr), 5), gross_ci=[round(float(x), 5) for x in np.percentile(bg, [2.5, 97.5])])
            if key != "base":
                m = W & (E < 50)
                r["witnessed_share_of_shown"] = round(float(W.sum() / (~np.isnan(E)).sum()), 4)
                r["witnessed_gross"] = round(float((W & (E >= 50)).sum() / max(W.sum(), 1)), 5)
                r["witnessed_within_U"] = round(float((E[m] <= U).mean()), 4) if m.any() else None
            row[key] = r
        test_res[cond] = row
        print(cond, row)
    OUT.write_text(json.dumps(dict(grid=[list(g) for g in GRID], fit_singers=sorted(fit_s), fit=fit_table,
                                   chosen=chosen, U95_witnessed_cents=U, test=test_res), indent=1))


if __name__ == "__main__":
    main()
