"""E-002 round 8: squillo's YIN (ADR 0007) against a published method, pYIN
(Mauch & Dixon 2014, librosa's implementation), on the 159 VocalSet takes (20
singers, CC BY 4.0, data/SOURCES.md) re-synthesized by WORLD for a known f0
(round 2, r2_truth.py). Crude experiment code. Needs data/cache/r2/*.npz.

    uv run python r8_pyin.py      # writes results/r8_pyin.json

Fixed before running:
- Conditions: clean, white-20, white-10, pink-10 (r2_run.condition, same seeds).
- YIN: yin.yin, in range E2..C6 with 3-cent margin (as round 2), truth at its
  SG-007 instant, validity as r2_run.frame_truth. "squillo" additionally
  applies MT-003's refusal (dip >= 0.02 refused, round 2 fold), as the product does.
- pYIN: librosa.pyin, frame_length 1536, hop 384, center=False (each frame the
  same 1536 samples as squillo's frame idx = t + 3), fmin 63, fmax 1200 Hz,
  other parameters librosa's defaults; unvoiced-flagged frames count as no
  estimate; same in-range rule; truth at the window centre; same validity.
- Per valid frame: estimate within 50 cents ("hit"), gross (>50 cents),
  or none. Report hit share (raw pitch accuracy, RPA), gross share of
  estimates, none share, and |error| p50/p95 cents over hits, by condition
  and by singer sex (VocalSet f*/m*), with 95 % bootstrap CIs over takes
  (2000 resamples, seed 8).
"""

import json
from multiprocessing import Pool
from pathlib import Path

import librosa
import numpy as np

import r2_run as R
import r2_truth as T
import yin
from yin import SR

CONDS = ["clean", "white-20", "white-10", "pink-10"]
OUT = Path(__file__).parent / "results" / "r8_pyin.json"


def window_truth(ft, n):
    s = 384 * np.arange(n)
    ok = s + 1536 <= len(ft)
    s = s[ok]
    ref = np.stack([ft[a:a + 1536] for a in s])
    allv = (ref > 0).all(1)
    safe = np.where(ref > 0, ref, 1.0)
    rng_c = 1200 * np.log2(safe.max(1) / safe.min(1))
    inr = (ref >= yin.E2).all(1) & (ref <= yin.C6).all(1)
    return ft[s + 768], allv & inr & (rng_c <= 200), ok


def score(f, f_true, valid):
    f, t = f[valid], f_true[valid]
    est = ~np.isnan(f)
    err = np.full(len(f), np.nan)
    err[est] = np.abs(1200 * np.log2(f[est] / t[est]))
    hit = est & (err < 50)
    return dict(n=int(len(f)), hit=int(hit.sum()), gross=int((est & ~hit).sum()), est=int(est.sum()),
                errs=err[hit].tolist())


def one(stem):
    z = np.load(T.R2 / (stem + ".npz"))
    x, y, f0 = z["x"].astype(np.float64), z["y"].astype(np.float64), z["f0"]
    ft = T.truth_per_sample(f0, len(x))
    out = {}
    for cond in CONDS:
        sig, _ = R.condition(y, ft > 0, stem, cond)
        idx, f, dip = yin.yin(sig)
        f = yin.in_range(f, 3.0)
        f_true, _, valid = R.frame_truth(ft, idx, f)
        fs = np.where(dip < 0.02, f, np.nan)
        fp, vflag, _ = librosa.pyin(sig, fmin=63.0, fmax=1200.0, sr=SR, frame_length=1536, hop_length=384, center=False)
        fp = yin.in_range(np.where(vflag, fp, np.nan), 3.0)
        pt, pvalid, ok = window_truth(ft, len(fp))
        out[cond] = dict(yin=score(f, f_true, valid), squillo=score(fs, f_true, valid),
                         pyin=score(fp[ok], pt, pvalid))
    return stem, out


def summarise(per, stems, rng):
    keys = ["hit", "gross", "est", "n"]
    arr = {k: np.array([per[s][k] for s in stems], float) for k in keys}
    def stats(ix):
        a = {k: arr[k][ix].sum() for k in keys}
        return a["hit"] / a["n"], a["gross"] / max(a["est"], 1), 1 - a["est"] / a["n"]
    point = stats(np.arange(len(stems)))
    boots = np.array([stats(rng.integers(0, len(stems), len(stems))) for _ in range(2000)])
    lo, hi = np.percentile(boots, [2.5, 97.5], axis=0)
    errs = np.concatenate([per[s]["errs"] for s in stems]) if stems else np.array([])
    names = ["rpa", "gross_of_estimates", "no_estimate"]
    r = {nm: dict(value=round(float(point[i]), 5), ci95=[round(float(lo[i]), 5), round(float(hi[i]), 5)]) for i, nm in enumerate(names)}
    r["valid_frames"] = int(arr["n"].sum())
    r["hit_abs_cents_p50"] = round(float(np.percentile(errs, 50)), 3)
    r["hit_abs_cents_p95"] = round(float(np.percentile(errs, 95)), 3)
    return r


def main():
    stems = sorted(p.stem for p in T.R2.glob("*.npz"))
    with Pool(18) as p:
        res = dict(p.map(one, stems))
    singer = {s: T.singer_of(s) for s in stems}
    groups = {"all": stems, "female": [s for s in stems if singer[s].startswith("f")],
              "male": [s for s in stems if singer[s].startswith("m")]}
    summary = {}
    for cond in CONDS:
        for tr in ["yin", "squillo", "pyin"]:
            for g, ss in groups.items():
                rng = np.random.default_rng(8)
                summary[f"{cond}/{tr}/{g}"] = summarise({s: res[s][cond][tr] for s in ss}, ss, rng)
    meta = dict(takes=len(stems), singers=len(set(singer.values())), librosa=librosa.__version__,
                groups={g: len(v) for g, v in groups.items()})
    OUT.write_text(json.dumps(dict(meta=meta, summary=summary), indent=1))
    for k, v in summary.items():
        print(k, v["rpa"]["value"], v["rpa"]["ci95"], "gross", v["gross_of_estimates"]["value"], "none", v["no_estimate"]["value"], "p50/p95", v["hit_abs_cents_p50"], v["hit_abs_cents_p95"])


if __name__ == "__main__":
    main()
