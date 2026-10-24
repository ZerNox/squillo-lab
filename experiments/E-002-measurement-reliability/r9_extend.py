"""E-002 round 9: what keeping frames past MT-003's refusal (aperiodicity
0.02) would cost. Crude experiment code. Same 159 known-f0 re-syntheses and
conditions as round 8.

    uv run python r9_extend.py      # writes results/r9_extend.json

Fixed before running: aperiodicity bins [0.02,0.03), [0.03,0.045), [0.045,0.065),
[0.065,0.1), YIN keeping its threshold 0.1 (a first run at 0.35 changed which dip YIN picks, so it measured another tracker; discarded). Fit on the odd-numbered singers (sorted
VocalSet ids, 10 of 20), test on the others. Per bin, from the fit singers'
clean and white-20 frames: gross share (>50 cents) and the 95th percentile
|error| of non-gross frames (an expanded U for that bin, k = 2 coverage
target 95 %). A bin is kept only if its fit gross share <= 1 %. On the test
singers: coverage (valid frames shown) and gross share at each cut-off
(product today = 0.02), and the share of non-gross shown frames within each
bin's U (coverage of the ±), per condition.
"""

import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

import r2_run as R
import r2_truth as T
import yin

CONDS = ["clean", "white-20", "white-10", "pink-10"]
BINS = [0.0, 0.02, 0.03, 0.045, 0.065, 0.1]
OUT = Path(__file__).parent / "results" / "r9_extend.json"


def one(stem):
    z = np.load(T.R2 / (stem + ".npz"))
    y, f0 = z["y"].astype(np.float64), z["f0"]
    ft = T.truth_per_sample(f0, len(y))
    out = {}
    for cond in CONDS:
        sig, _ = R.condition(y, ft > 0, stem, cond)
        idx, f, dip = yin.yin(sig, threshold=0.1)
        f = yin.in_range(f, 3.0)
        f_true, _, valid = R.frame_truth(ft, idx, f)
        f, d, t = f[valid], dip[valid], f_true[valid]
        err = np.abs(1200 * np.log2(f / t))
        out[cond] = dict(err=err.tolist(), dip=d.tolist())
    return stem, out


def main():
    stems = sorted(p.stem for p in T.R2.glob("*.npz"))
    with Pool(18) as p:
        res = dict(p.map(one, stems))
    singers = sorted({T.singer_of(s) for s in stems})
    fit_s = set(singers[0::2])
    fit = [s for s in stems if T.singer_of(s) in fit_s]
    test = [s for s in stems if T.singer_of(s) not in fit_s]
    def cat(ss, conds):
        e = np.concatenate([res[s][c]["err"] for s in ss for c in conds])
        d = np.concatenate([res[s][c]["dip"] for s in ss for c in conds])
        return e, d
    e, d = cat(fit, ["clean", "white-20"])
    table = []
    for lo, hi in zip(BINS[:-1], BINS[1:]):
        m = (d >= lo) & (d < hi) & ~np.isnan(e)
        g = e[m] >= 50
        U = float(np.percentile(e[m][~g], 95)) if (~g).sum() else None
        table.append(dict(lo=lo, hi=hi, frames=int(m.sum()), gross=round(float(g.mean()), 5) if m.any() else None,
                          U95_cents=round(U, 2) if U else None))
    keep = [b for b in table if b["gross"] is not None and b["gross"] <= 0.01]
    print("fit table"); [print(b) for b in table]
    test_res = {}
    for cond in CONDS:
        e, d = cat(test, [cond])
        n = len(e)
        row = {}
        for cut in BINS[1:]:
            shown = ~np.isnan(e) & (d < cut)
            g = shown & (e >= 50)
            Uf = np.full(n, np.nan)
            for b in table:
                Uf[(d >= b["lo"]) & (d < b["hi"])] = b["U95_cents"] or np.nan
            ng = shown & ~g
            row[str(cut)] = dict(coverage=round(float(shown.mean()), 4), gross_of_shown=round(float(g.sum() / max(shown.sum(), 1)), 5),
                                 within_U=round(float((e[ng] <= Uf[ng]).mean()), 4))
        test_res[cond] = dict(valid_frames=n, by_cutoff=row)
        print(cond, n, {k: (v["coverage"], v["gross_of_shown"], v["within_U"]) for k, v in row.items()})
    OUT.write_text(json.dumps(dict(fit_singers=sorted(fit_s), table=table, kept_bins=keep, test=test_res), indent=1))


if __name__ == "__main__":
    main()
