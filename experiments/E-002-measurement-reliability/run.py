"""E-002 round 1: pitch only. `uv run python run.py` writes results/.

Synthetic ground truth at 48 kHz, 1 s per tone, frames and windows as squillo
ADR 0007. Errors are in cents against the true f0. Fixed seeds.
"""

import json
import sys
import time
from pathlib import Path

import librosa
import numpy as np
import scipy
import soundfile as sf

import yin
from yin import SR, HOP, WIN, E2, C6, cents

OUT = Path(__file__).parent / "results"
OUT.mkdir(exist_ok=True)
FIX = Path(__file__).parents[3] / "squillo" / "fixtures" / "signal"
DUR = 1.0
N = int(SR * DUR)
GROSS = 50.0  # cents; MIREX raw pitch accuracy criterion
rng = np.random.default_rng(20260925)


# ---------------------------------------------------------------- signals
def f0_track(kind, f0, t, **p):
    if kind == "steady":
        return np.full_like(t, f0)
    if kind == "vibrato":
        return f0 * 2 ** (p["extent"] / 1200 * np.sin(2 * np.pi * p["rate"] * t + p["ph"]))
    if kind == "glide":
        # log-linear, centred on f0 at t = DUR/2
        return f0 * 2 ** (p["speed"] / 1200 * (t - DUR / 2))
    raise ValueError(kind)


def render(f_inst, spectrum, phases):
    """Additive synthesis; harmonics above 20 kHz dropped per sample."""
    phase = 2 * np.pi * np.cumsum(f_inst) / SR
    x = np.zeros_like(f_inst)
    for k, (amp, ph) in enumerate(zip(spectrum, phases), start=1):
        if amp == 0:
            continue
        mask = k * f_inst < 20_000
        x += np.where(mask, amp * np.sin(k * phase + ph), 0.0)
    return 0.5 * x / np.max(np.abs(x))


def spectrum(kind, f0):
    K = int(20_000 // f0)
    k = np.arange(1, K + 1, dtype=float)
    if kind == "pure":
        s = np.zeros(K); s[0] = 1.0
    elif kind == "saw6":  # -6 dB/octave
        s = 1 / k
    elif kind == "saw12":  # -12 dB/octave, a common glottal-source slope
        s = 1 / k ** 2
    elif kind == "weakf0":  # -12 dB/oct, fundamental 20 dB under the 2nd harmonic
        s = 1 / k ** 2
        s[0] = s[1] * 0.1 if K > 1 else 1.0
    else:
        raise ValueError(kind)
    return s


def tone(timbre, f0, kind="steady", **p):
    t = np.arange(N) / SR
    f = f0_track(kind, f0, t, **p)
    s = spectrum(timbre, f0 * 2 ** (abs(p.get("extent", 0)) / 1200))
    return render(f, s, rng.uniform(0, 2 * np.pi, len(s))), f


def add_noise(x, snr_db):
    n = rng.standard_normal(len(x))
    n *= np.sqrt(np.mean(x ** 2) / np.mean(n ** 2) / 10 ** (snr_db / 10))
    return x + n


def references(f_true, idx):
    """True f0 for frame i: at window centre, at frame end, log-mean over window."""
    ends = HOP * idx + HOP - 1
    starts = ends - WIN + 1
    centre = f_true[(starts + ends) // 2]
    end = f_true[ends]
    logmean = np.array([2 ** np.mean(np.log2(f_true[s:e + 1])) for s, e in zip(starts, ends)])
    return {"centre": centre, "end": end, "logmean": logmean}


# ---------------------------------------------------------------- trackers
def run_yin(x, **kw):
    idx, f, _ = yin.yin(x, **kw)
    return idx, f


def run_pyin(x, resolution=0.1, fmin=63.0, fmax=2100.0):
    f, voiced, _ = librosa.pyin(
        x.astype(np.float64), fmin=fmin, fmax=fmax, sr=SR, frame_length=WIN,
        hop_length=HOP, center=False, resolution=resolution)
    idx = np.arange(3, 3 + len(f))
    n = N // HOP - 3
    return idx[:n], np.where(voiced, f, np.nan)[:n]


# ---------------------------------------------------------------- stats
def boot_ci(per_tone_vals, stat, B=2000):
    """95 % bootstrap interval over tones (frames within a tone are correlated)."""
    vals = [v for v in per_tone_vals if len(v)]
    if not vals:
        return [None, None]
    r = np.random.default_rng(1)
    out = []
    for _ in range(B):
        pick = r.integers(0, len(vals), len(vals))
        out.append(stat(np.concatenate([vals[i] for i in pick])))
    return [float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))]


def wilson(k, n):
    if n == 0:
        return [None, None]
    z = 1.96
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [float(c - h), float(c + h)]


def summarise(errs_per_tone, n_frames):
    """errs_per_tone: list of arrays of signed cents error (nan = unmeasured)."""
    allv = np.concatenate(errs_per_tone)
    meas = ~np.isnan(allv)
    e = np.abs(allv[meas])
    fine = e[e <= GROSS]
    gross = int(np.sum(e > GROSS))
    per_fine = [np.abs(v[~np.isnan(v)]) for v in errs_per_tone]
    per_fine = [v[v <= GROSS] for v in per_fine]
    p95 = lambda a: np.percentile(a, 95)
    return {
        "tones": len(errs_per_tone),
        "frames": int(n_frames),
        "measured_frac": float(meas.mean()),
        "measured_ci95": wilson(int(meas.sum()), len(allv)),
        "gross_frac_of_measured": float(gross / max(1, meas.sum())),
        "gross_ci95": wilson(gross, int(meas.sum())),
        "fine_median_abs": float(np.median(fine)) if len(fine) else None,
        "fine_p95_abs": float(p95(fine)) if len(fine) else None,
        "fine_p95_ci95": boot_ci(per_fine, p95) if len(fine) else [None, None],
        "fine_max_abs": float(fine.max()) if len(fine) else None,
        "within_3c_of_measured": float(np.mean(e <= 3.0)) if len(e) else None,
        "within_3c_ci95": wilson(int(np.sum(e <= 3.0)), len(e)),
        "fine_mean_signed": float(np.mean(allv[meas][np.abs(allv[meas]) <= GROSS])) if len(fine) else None,
    }


def condition(name, make, trackers, refs=("logmean",), n_tones=40):
    """make(f0) -> (x, f_true). Tones log-uniform over E2..C6 (semitone grid first)."""
    grid = E2 * 2 ** (np.arange(0, 40) / 12)  # E2 .. B5
    grid = np.append(grid, C6)
    f0s = grid if n_tones >= len(grid) else np.exp(rng.uniform(np.log(E2), np.log(C6), n_tones))
    per = {(tr, ref): [] for tr in trackers for ref in refs}
    band = {(tr, ref): {"low": [], "mid": [], "high": []} for tr in trackers for ref in refs}
    for f0 in f0s:
        x, f_true = make(f0)
        for tr, fn in trackers.items():
            idx, f = fn(x)
            f = yin.in_range(f, 3.0)
            R = references(f_true, idx)
            for ref in refs:
                err = cents(f, R[ref])
                per[(tr, ref)].append(err)
                b = "low" if f0 < 220 else ("high" if f0 > 523.25 else "mid")
                band[(tr, ref)][b].append(err)
    res = {}
    for (tr, ref), v in per.items():
        n = sum(len(a) for a in v)
        res[f"{tr}|{ref}"] = summarise(v, n)
        res[f"{tr}|{ref}"]["by_band"] = {
            b: summarise(vv, sum(len(a) for a in vv)) if vv else None
            for b, vv in band[(tr, ref)].items()}
    print(f"  {name}: done", flush=True)
    return res


# ---------------------------------------------------------------- experiments
def exp_fixtures():
    """The squillo `signal` fixtures, SG-001..SG-006 as scenarios."""
    out = {}
    refs = {"sine-220hz": 220.0, "sine-220hz-overshoot": 220.0, "sine-e2": E2, "sine-c6": C6}
    for p in sorted(FIX.glob("*.wav")):
        x, sr = sf.read(p, dtype="float32")
        assert sr == SR
        idx, f = run_yin(x)
        g = yin.in_range(f, 3.0)
        r = {"frames": int(N // HOP), "first_index": int(idx[0]),
             "measured": int(np.sum(~np.isnan(g))), "of": int(len(idx))}
        if p.stem in refs:
            r["max_abs_cents"] = float(np.nanmax(np.abs(cents(g, refs[p.stem]))))
        out[p.stem] = r
    return out


def exp_edges(margins=(0.0, 3.0, 6.0)):
    """F-017. Pure tones at offsets outside and inside each range edge."""
    offs = np.concatenate([-np.array([1200, 600, 400, 200, 100, 50, 25, 12, 9, 6, 4.5, 3.5, 3, 2, 1, 0.5]),
                           [0.0, 0.5, 1, 2, 3]])
    res = {}
    for edge, fe, sign in (("E2", E2, -1), ("C6", C6, +1)):
        # sign: direction out of the range; offset < 0 in `offs` means outside
        for off in offs:
            # off < 0 is outside the range: below E2, above C6
            f0 = fe * 2 ** ((off if sign < 0 else -off) / 1200)
            meas = {m: 0 for m in margins}
            errs = []
            trials = 8
            for _ in range(trials):
                x, _ = tone("pure", f0)
                idx, f = run_yin(x)
                errs.append(cents(f, f0))
                for m in margins:
                    meas[m] += int(np.sum(~np.isnan(yin.in_range(f, m))))
            e = np.abs(np.concatenate(errs))
            res[f"{edge}{'-' if off < 0 else '+'}{abs(off):g}"] = {
                "edge": edge, "cents_outside": float(-off), "f0": float(f0),
                "frames": trials * 122,
                "yin_found_frac": float(np.mean(~np.isnan(np.concatenate(errs)))),
                "yin_max_abs_err_cents": float(np.nanmax(e)) if np.any(~np.isnan(e)) else None,
                "measured_frac_by_accept_margin": {str(m): meas[m] / (trials * 122) for m in margins},
            }
    return res


def exp_precision():
    """float32 vs float64 arithmetic in YIN, same float32 input, pure and harmonic tones."""
    diffs = []
    for f0 in E2 * 2 ** (np.arange(0, 41) / 12):
        for timbre in ("pure", "saw12"):
            x, _ = tone(timbre, f0)
            x = x.astype(np.float32)
            _, a, _ = yin.yin(x, dtype=np.float64)
            _, b, _ = yin.yin(x, dtype=np.float32)
            both = ~np.isnan(a) & ~np.isnan(b)
            diffs.append(np.abs(cents(a[both], b[both])))
            diffs.append(np.full(int(np.sum(np.isnan(a) != np.isnan(b))), np.inf))
    d = np.concatenate(diffs)
    return {"frames": int(len(d)), "decision_mismatches": int(np.sum(np.isinf(d))),
            "max_abs_cents": float(np.max(d[np.isfinite(d)])),
            "p99_abs_cents": float(np.percentile(d[np.isfinite(d)], 99))}


def main():
    t0 = time.time()
    results = {"conditions": {
        "sr": SR, "hop": HOP, "window": WIN, "duration_s": DUR, "gross_cents": GROSS,
        "yin": "de Cheveigne & Kawahara 2002 steps 1-4, threshold 0.1 unless stated, "
               "lag search 16..763 samples (3000..63 Hz), parabolic interpolation on d",
        "pyin": f"librosa {librosa.__version__} pyin, frame_length 1536, hop 384, center=False, "
                "fmin 63, fmax 2100",
        "accept": "a frame is measured if its f0 lies within E2..C6 widened by 3 cents",
        "numpy": np.__version__, "scipy": scipy.__version__, "python": sys.version.split()[0],
        "seed": 20260925,
    }}
    print("fixtures", flush=True)
    results["fixtures"] = exp_fixtures()
    print("edges", flush=True)
    results["edges"] = exp_edges()
    print("precision", flush=True)
    results["precision_f32_vs_f64"] = exp_precision()

    trk = {
        "yin": lambda x: run_yin(x),
        "yin_interp_dprime": lambda x: run_yin(x, interp="dn"),
        "pyin_10c": lambda x: run_pyin(x, 0.1),
        "pyin_1c": lambda x: run_pyin(x, 0.01),
    }
    fast = {k: trk[k] for k in ("yin", "pyin_10c")}
    three = ("centre", "end", "logmean")
    C = {}
    print("conditions", flush=True)
    for timbre in ("pure", "saw6", "saw12", "weakf0"):
        C[f"steady/{timbre}"] = condition(
            f"steady/{timbre}", lambda f0, t=timbre: tone(t, f0), trk, n_tones=41)
    for rate in (5.5, 7.0):
        for ext in (50, 100):
            C[f"vibrato/saw12/{rate}Hz/{ext}c"] = condition(
                f"vibrato {rate} {ext}",
                lambda f0, r=rate, e=ext: tone("saw12", f0, "vibrato", rate=r, extent=e,
                                               ph=rng.uniform(0, 2 * np.pi)),
                fast, refs=three, n_tones=24)
    for speed in (600, 2400):
        C[f"glide/saw12/{speed}c_per_s"] = condition(
            f"glide {speed}", lambda f0, s=speed: tone("saw12", f0, "glide", speed=s),
            fast, refs=three, n_tones=24)
    for snr in (40, 30, 20, 10, 5, 0):
        C[f"noise/saw12/{snr}dB"] = condition(
            f"noise {snr}", lambda f0, s=snr: (lambda xf: (add_noise(xf[0], s), xf[1]))(tone("saw12", f0)),
            fast, n_tones=24)
        C[f"noise/saw12/{snr}dB/yin_thr0.2"] = condition(
            f"noise {snr} thr0.2",
            lambda f0, s=snr: (lambda xf: (add_noise(xf[0], s), xf[1]))(tone("saw12", f0)),
            {"yin": lambda x: run_yin(x, threshold=0.2)}, n_tones=24)
    results["accuracy"] = C
    results["runtime_s"] = time.time() - t0
    (OUT / "results.json").write_text(json.dumps(results, indent=1))
    print("wrote results/results.json in", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
