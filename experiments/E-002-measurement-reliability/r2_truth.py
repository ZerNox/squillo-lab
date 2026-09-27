"""E-002 round 2, step 1: real voices with a known f0, by analysis and
re-synthesis. Crude experiment code.

Salamon, Bittner, Bonada, Bosch, Gomez and Bello (2017), "An
analysis/synthesis framework for automatic f0 annotation of multitrack
datasets", ISMIR 2017: re-synthesize a real recording from its own analysis,
and the f0 used for synthesis is the truth of the new signal. Here WORLD
(Morise, Yokomori and Ozawa 2016, doi:10.1587/transinf.2015EDP7457), through
pyworld: Harvest f0 at 1 ms, CheapTrick envelope, D4C aperiodicity,
synthesis at 48 kHz. WORLD's synthesis advances the excitation phase by the
f0 interpolated per sample, so the truth at a sample is Harvest's f0
linearly interpolated there.

    uv run python r2_truth.py check   # the truth procedure on one input of every set
    uv run python r2_truth.py         # every file in data/vocalset-files.txt

Writes data/cache/r2/<stem>.npz (not committed) and results/r2_truth.json.
"""

import json
import sys
import warnings
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

warnings.filterwarnings("ignore", category=UserWarning)
import pyworld as pw  # noqa: E402

import yin  # noqa: E402
from yin import SR, E2, C6  # noqa: E402

HERE = Path(__file__).parent
CACHE = HERE / "data" / "cache"
R2 = CACHE / "r2"
OUT = HERE / "results"
FP = 1.0  # WORLD frame period, ms
F0_FLOOR, F0_CEIL = 71.0, 1100.0  # Harvest search range, wider than E2..C6 (82.4..1046.5 Hz)
assert F0_FLOOR < E2 and F0_CEIL > C6
ENERGY_DB = -50.0  # a 1/3-octave band "has energy" at >= -50 dB re the file's 100 Hz..8 kHz total


def set_of(name):
    for key, tag in (("long_straight", "LT-straight"), ("long_forte", "LT-forte"),
                     ("long_pp", "LT-pp"), ("long_messa", "LT-messa"),
                     ("arpeggios_vibrato", "VIB-arpeggio"), ("row_vibrato", "VIB-row"),
                     ("scales_breathy", "SC-breathy"), ("scales_straight", "SC-straight")):
        if key in name:
            return tag
    raise ValueError(name)


def _names():
    return [l.strip() for l in (HERE / "data" / "vocalset-files.txt").read_text().splitlines() if l.strip()]


def singer_of(stem):
    """From the zip path (FULL/<singer>/...): two files carry no singer prefix in their name."""
    return {Path(n).stem: n.split("/")[1] for n in _names()}[stem]


def files():
    return [CACHE / Path(n).name for n in _names()]


def load48(path):
    x, sr = sf.read(path)
    assert x.ndim == 1 and sr == 44_100, (path, x.shape, sr)
    return resample_poly(x, 160, 147)  # 44.1 kHz -> 48 kHz


def truth_per_sample(f0, n):
    """Harvest f0 (frame k at k*FP ms) linearly interpolated at every sample; 0 = unvoiced."""
    tk = np.arange(len(f0)) * FP / 1000 * SR
    ts = np.arange(n)
    f = np.interp(ts, tk, f0)
    # a sample is voiced only if both neighbouring analysis frames are
    k = np.minimum((ts / (FP / 1000 * SR)).astype(int), len(f0) - 2)
    voiced = (f0[k] > 0) & (f0[k + 1] > 0)
    return np.where(voiced, f, 0.0)


def analyse(path):
    x = load48(path)
    f0, t = pw.harvest(x, SR, f0_floor=F0_FLOOR, f0_ceil=F0_CEIL, frame_period=FP)
    sp = pw.cheaptrick(x, f0, t, SR)
    ap = pw.d4c(x, f0, t, SR)
    y = pw.synthesize(f0, sp, ap, SR, frame_period=FP)[: len(x)]
    if len(y) < len(x):
        y = np.pad(y, (0, len(x) - len(y)))
    return x, y, f0


def third_octave_levels(x, voiced):
    """Long-term level in 1/3-octave bands 100 Hz..8 kHz over voiced samples, dB re total."""
    from scipy.signal import welch
    fr, P = welch(x[voiced], SR, nperseg=4096)
    centres = 1000 * 2 ** (np.arange(-10, 10) / 3)
    centres = centres[(centres >= 100) & (centres <= 8000)]
    L = np.array([P[(fr >= c * 2 ** (-1 / 6)) & (fr < c * 2 ** (1 / 6))].sum() for c in centres])
    return centres, 10 * np.log10(L / L.sum())


def one(path):
    out = R2 / (path.stem + ".npz")
    x, y, f0 = analyse(path)
    ft = truth_per_sample(f0, len(x))
    v = ft > 0
    np.savez_compressed(out, x=x.astype(np.float32), y=y.astype(np.float32), f0=f0)
    c, Lx = third_octave_levels(x, v)
    _, Ly = third_octave_levels(y, v)
    return dict(name=path.stem, set=set_of(path.stem), singer=singer_of(path.stem),
                seconds=len(x) / SR, voiced_share=float(v.mean()),
                voiced_in_range_share=float(((ft >= E2) & (ft <= C6)).sum() / max(v.sum(), 1)),
                truth_min_hz=float(ft[v].min()) if v.any() else None,
                truth_max_hz=float(ft[v].max()) if v.any() else None,
                bands_hz=c.tolist(), L_orig=Lx.tolist(), L_resynth=Ly.tolist())


def world_self_check():
    """WORLD synthesis with a known contour: a steady 220 Hz and a 5.5 Hz, +-50 cent
    vibrato, envelope and aperiodicity taken from one real frame. YIN at squillo's
    frame axis must read the contour at SG-007's instant within SG-005's 3 cents
    on a steady tone, or the truth procedure is not a truth."""
    x = load48(files()[0])
    f0, t = pw.harvest(x, SR, f0_floor=F0_FLOOR, f0_ceil=F0_CEIL, frame_period=FP)
    sp = pw.cheaptrick(x, f0, t, SR)
    ap = pw.d4c(x, f0, t, SR)
    k = int(np.argmax(f0))  # a voiced frame
    n = 3000  # 3 s at 1 ms
    res = {}
    for kind in ("steady", "vibrato"):
        tt = np.arange(n) * FP / 1000
        ff = np.full(n, 220.0) if kind == "steady" else 220.0 * 2 ** (50 / 1200 * np.sin(2 * np.pi * 5.5 * tt))
        y = pw.synthesize(ff, np.repeat(sp[k:k + 1], n, 0), np.repeat(ap[k:k + 1], n, 0), SR, frame_period=FP)
        ft = truth_per_sample(ff, len(y))
        idx, f, _ = yin.yin(y)
        f = yin.in_range(f, 3.0)
        keep = 384 * (idx - 3) >= SR // 100  # windows starting after the synthesis onset (10 ms)
        idx, f = idx[keep], f[keep]
        ok = ~np.isnan(f)
        pos = np.clip(np.round(384 * idx - 766 + SR / np.where(ok, f, 220.0) / 2).astype(int), 0, len(y) - 1)
        e = yin.cents(f[ok], ft[pos[ok]])
        res[kind] = dict(frames=int(len(idx)), measured=int(ok.sum()),
                         max_abs=float(np.abs(e).max()), p95_abs=float(np.percentile(np.abs(e), 95)))
    print("WORLD self-check", res)
    assert res["steady"]["measured"] == res["steady"]["frames"] and res["steady"]["max_abs"] <= 3.0, res
    return res


def main():
    R2.mkdir(parents=True, exist_ok=True)
    fs = files()
    if sys.argv[1:] == ["check"]:
        chk = world_self_check()
        firsts = {}
        for p in fs:
            firsts.setdefault(set_of(p.stem), p)
        for s, p in firsts.items():
            r = one(p)
            Lo, Ly = np.array(r["L_orig"]), np.array(r["L_resynth"])
            d = (Ly - Lo)[(Lo >= ENERGY_DB) & (Ly >= ENERGY_DB)]
            print(s, p.stem, f"voiced {r['voiced_share']:.2f}", f"in range {r['voiced_in_range_share']:.3f}",
                  f"truth {r['truth_min_hz']:.1f}..{r['truth_max_hz']:.1f} Hz",
                  "resynth-orig 1/3-oct dB: max |d|", round(float(np.abs(d).max()), 2))
        return
    with Pool(16) as pool:
        rows = pool.map(one, fs)
    chk = world_self_check()
    # S15: a re-synthesized voice's long-term spectrum must lie within the range of real
    # recordings. Compared only in 1/3-octave bands where both have energy (>= ENERGY_DB).
    # The measure: the median |level difference| over those bands. The range: that measure
    # between two long-tone takes (/a/, different dynamics) of the same singer, over all
    # singers. Condition: each file's resynth-vs-original measure <= the range's maximum.
    import itertools
    by = {r["name"]: r for r in rows}

    def med_diff(a, b):
        a, b = np.array(a), np.array(b)
        e = (a >= ENERGY_DB) & (b >= ENERGY_DB)
        return float(np.median(np.abs(a - b)[e]))
    own = {n: med_diff(r["L_orig"], r["L_resynth"]) for n, r in by.items()}
    lt = {}
    for n, r in by.items():
        if r["set"].startswith("LT-"):
            lt.setdefault(r["singer"], []).append(n)
    pairs = [med_diff(by[a]["L_orig"], by[b]["L_orig"]) for ns in lt.values() for a, b in itertools.combinations(ns, 2)]
    bound = max(pairs)
    failed = {n: v for n, v in own.items() if v > bound}
    # the first, band-by-band form of the check, kept as a report: each energetic band of a
    # resynth inside the originals' band range over all files
    Lo = np.array([r["L_orig"] for r in rows]); Ly = np.array([r["L_resynth"] for r in rows])
    E = (Lo >= ENERGY_DB) & (Ly >= ENERGY_DB)
    lo = np.where(E, Lo, np.inf).min(0); hi = np.where(E, Lo, -np.inf).max(0)
    excess = np.where(E, np.maximum(lo - Ly, Ly - hi), -np.inf)
    ov = np.array(list(own.values())); pr = np.array(pairs)
    summary = dict(files=len(rows), world_self_check=chk, energy_dB=ENERGY_DB,
                   resynth_vs_own_original_median_band_dB=dict(median=float(np.median(ov)), p95=float(np.percentile(ov, 95)), max=float(ov.max())),
                   same_singer_two_takes_median_band_dB=dict(pairs=len(pr), min=float(pr.min()), median=float(np.median(pr)), max=float(pr.max())),
                   failed=failed,
                   band_by_band_report=dict(bands_compared=int(E.sum()), bands_outside=int((excess > 0).sum()),
                                            max_excess_dB=float(excess.max())),
                   rows=rows)
    (OUT / "r2_truth.json").write_text(json.dumps(summary, indent=1))
    print("files", len(rows), summary["resynth_vs_own_original_median_band_dB"],
          summary["same_singer_two_takes_median_band_dB"], summary["band_by_band_report"])
    assert not failed, failed


if __name__ == "__main__":
    main()
