"""E-002 round 2, step 3: YIN's octave errors on real voices, and two crude
variants. Crude experiment code. Needs data/cache/r2/*.npz (r2_truth.py).

The tracker (threshold 0.1, the first dip under it) against Harvest's f0 on the
original takes, and against the truth on the clean re-synthesis; with the
threshold at 0.05; and with an octave check (take the lag's double when its
CMND dip is deeper). Frames valid as in r2_run.py.

    uv run python r2_octave.py      # writes results/r2_octave.json (after r2_run.py)
"""
import json
from multiprocessing import Pool

import numpy as np

import r2_run as R
import r2_truth as T
import yin

VARIANTS = {"yin-0.1": dict(threshold=0.1), "yin-0.05": dict(threshold=0.05),
            "yin-0.1-octave-check": dict(threshold=0.1, octave_check=True)}


def one(path):
    z = np.load(T.R2 / (path.stem + ".npz"))
    ft = T.truth_per_sample(z["f0"], len(z["x"]))
    out = {}
    for src in ("x", "y"):
        sig = z[src].astype(np.float64)
        for v, kw in VARIANTS.items():
            idx, f, dip = yin.yin(sig, **kw)
            f = yin.in_range(f, 3.0)
            ft_i, _, valid = R.frame_truth(ft, idx, f)
            ok = valid & ~np.isnan(f)
            e = 1200 * np.log2(f[ok] / ft_i[ok])
            out[(src, v)] = (int(valid.sum()), e)
    return path.stem, out


def attribute(n_sample=600):
    """S17: who is wrong where YIN reads an original take an octave above Harvest? A partial at
    Harvest's f0 (its level >= 10 dB over the level at 1.5 times it, where neither reading
    puts a partial) means Harvest's f0 is the voice's. Needs data/cache/r2_frames.npz."""
    Z = np.load(T.CACHE / "r2_frames.npz")
    names = [p.stem for p in T.files()]
    f, t, v, fi, idx = (Z["original/" + k] for k in ("f", "f_true", "valid", "file", "idx"))
    ok = v & ~np.isnan(f)
    e = np.full(len(f), np.nan); e[ok] = 1200 * np.log2(f[ok] / t[ok])
    cand = np.nonzero(np.abs(e - 1200) < 100)[0]
    sel = np.random.default_rng(20260928).choice(cand, min(n_sample, len(cand)), replace=False)
    fr = np.fft.rfftfreq(16384, 1 / yin.SR)

    def lvl(X, hz):
        m = (fr > hz * 0.97) & (fr < hz * 1.03)
        return 20 * np.log10(X[m].max() + 1e-12)
    cache, partial, h1h2 = {}, [], []
    for k in sel:
        n = names[fi[k]]
        if n not in cache:
            cache[n] = np.load(T.R2 / (n + ".npz"))["x"].astype(np.float64)
        a = 384 * (idx[k] - 3)
        X = np.abs(np.fft.rfft(cache[n][a:a + 1536] * np.hanning(1536), 16384))
        partial.append(lvl(X, t[k]) - lvl(X, 1.5 * t[k]) >= 10)
        h1h2.append(lvl(X, t[k]) - lvl(X, 2 * t[k]))
    h1h2 = np.array(h1h2)
    male = np.array([T.singer_of(n).startswith("male") for n in names])[fi[cand]]
    return dict(octave_high_frames=int(len(cand)), from_men_share=float(male.mean()),
                truth_hz_median=float(np.median(t[cand])), sampled=int(len(sel)), partial_at_harvest_f0=int(np.sum(partial)),
                h1_minus_h2_dB=dict(p10=float(np.percentile(h1h2, 10)), median=float(np.median(h1h2)), p90=float(np.percentile(h1h2, 90))))


def main():
    res = Pool(16).map(one, T.files())
    sets = {n: T.set_of(n) for n, _ in res}
    table = {}
    for src, lab in (("x", "original vs Harvest"), ("y", "re-synthesis vs truth")):
        for v in VARIANTS:
            for grp in ["all"] + sorted(set(sets.values())):
                sel = [o[(src, v)] for n, o in res if grp == "all" or sets[n] == grp]
                nv = sum(a for a, _ in sel); e = np.concatenate([b for _, b in sel])
                g = np.abs(e) > 50
                table[f"{lab} | {v} | {grp}"] = dict(
                    valid=int(nv), measured_share=float(len(e) / nv), gross_share=float(g.mean()),
                    octave_high_share=float(np.mean(np.abs(e - 1200) < 100)),
                    octave_low_share=float(np.mean(np.abs(e + 1200) < 100)),
                    p95_abs_non_gross=float(np.percentile(np.abs(e[~g]), 95)))
                if grp == "all":
                    r = table[f"{lab} | {v} | {grp}"]
                    print(lab, v, {k: round(x, 4) for k, x in r.items()})
    table["attribution"] = attribute()
    print("attribution", table["attribution"])
    (T.OUT / "r2_octave.json").write_text(json.dumps(table, indent=1))


if __name__ == "__main__":
    main()
