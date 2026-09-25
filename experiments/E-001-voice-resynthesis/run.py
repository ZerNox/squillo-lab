"""E-001 round 1: re-synthesize sung phrases with pitch corrected or steadied.

Crude experiment code. `uv run python run.py` writes results/results.json and
results/summary.md. Needs data/cache/*.wav from fetch.py (VocalSet 1.1).

Inputs: 24 synthetic phrases (voice.py) whose intended contour and errors are
known, and 19 VocalSet singers' straight-tone scales on /a/.
Requests, in cents, applied by each method to its own f0 track:
  id      no change (analysis and re-synthesis only)
  c25..   note-centre correction, 25/50/100 % of the note's offset from its
          intended note
  s50..   steadying, 50/100 % of the wobble about the note centre removed
Measured on squillo's frame axis with E-002's YIN (squillo-lab E-002 @ 00bf2e9),
each frame's pitch taken at YIN's lag centre (E-002 result 5).
"""

import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import parselmouth
import pyworld as pw
import soundfile as sf
from scipy.signal import resample_poly

sys.path.insert(0, str(Path(__file__).parent.parent / "E-002-measurement-reliability"))
import yin  # noqa: E402
import resynth  # noqa: E402
import voice  # noqa: E402

SR = 48_000
HERE = Path(__file__).parent
OUT = HERE / "results"
CACHE = HERE / "data" / "cache"
W = 1536 - (int(np.ceil(SR / 63.0)) + 1)  # 773, E-002's YIN span
MODS = {"id": ("id", 0.0), "c25": ("corr", 0.25), "c50": ("corr", 0.5),
        "c100": ("corr", 1.0), "s50": ("steady", 0.5), "s100": ("steady", 1.0)}
SEED = 20260925


def cents(a, b):
    return 1200.0 * np.log2(a / b)


# ---------------------------------------------------------------- inputs

def synthetic_inputs():
    out = []
    for v in voice.VOICES:
        for vib in (False, True):
            for seed in (1, 2):
                out.append(dict(kind="synthetic", name=f"{v}_{'vib' if vib else 'plain'}_{seed}",
                                voice=v, vib=vib, seed=seed))
    return out


def real_inputs():
    return [dict(kind="vocalset", name=f.stem.split("_")[0], path=str(f))
            for f in sorted(CACHE.glob("*_scales_straight_a.wav"))]


def load(inp):
    """Return x and the request grid: times (s), the correction offset and
    the wobble in cents, plus the intended contour for synthetic input."""
    if inp["kind"] == "synthetic":
        p = voice.phrase(inp["voice"], inp["vib"], SEED + inp["seed"])
        sung = p["target"] + p["offset"] + p["scoop"] + p["wobble"]
        x = voice.render(p, sung)
        t = np.arange(p["n"]) / SR
        return x, dict(t=t, offset=p["offset"], wobble=p["wobble"], sung=sung, p=p)
    x, sr = sf.read(inp["path"], dtype="float64")
    x = resample_poly(x, 160, 147)  # 44.1 -> 48 kHz
    x = 0.5 * x / np.abs(x).max()
    # Requests from Harvest's f0 on the input: the note centre is a 250 ms
    # running median of the voiced pitch; its intended note the nearest
    # equal-tempered note re A4 = 440 Hz. Crude intent; E-005 owns intent.
    f0, t = pw.harvest(x, SR, f0_floor=60, f0_ceil=1100, frame_period=5.0)
    c = np.where(f0 > 0, cents(np.where(f0 > 0, f0, 1), 440.0), np.nan)
    half = 25
    pad = np.pad(c, half, constant_values=np.nan)
    win = np.lib.stride_tricks.sliding_window_view(pad, 2 * half + 1)
    with np.errstate(all="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            centre = np.nanmedian(win, axis=1)
    offset = centre - 100 * np.round(centre / 100)
    offset = np.convolve(np.nan_to_num(offset), np.ones(11) / 11, mode="same")
    wobble = np.clip(np.nan_to_num(c - centre), -50, 50)
    offset[np.isnan(c)] = 0
    wobble[np.isnan(c)] = 0
    return x, dict(t=t, offset=offset, wobble=wobble)


def request(grid, mod):
    kind, a = MODS[mod]
    s = np.zeros_like(grid["t"]) if kind == "id" else -a * grid["offset" if kind == "corr" else "wobble"]
    return lambda tt: np.interp(tt, grid["t"], s)


# ---------------------------------------------------------------- measures

def track(x):
    idx, f, dip = yin.yin(x)
    f = yin.in_range(f, 3.0)
    s = yin.HOP * (idx - 3)
    tau = SR / np.where(np.isnan(f), 1.0, f)
    t_lag = (s + (W + tau) / 2) / SR
    return f, t_lag


MEL = 700.0 * (10 ** (np.linspace(np.log10(1 + 80 / 700), np.log10(1 + 8000 / 700), 40)) - 1)


def mcep(x):
    """CheapTrick envelope in dB at 40 mel-spaced frequencies, 80 Hz to 8 kHz,
    per 5 ms frame, and the voiced mask (DIO plus StoneMask)."""
    f0, t = pw.dio(x, SR, f0_floor=60, f0_ceil=1100, frame_period=5.0)
    f0 = pw.stonemask(x, f0, t, SR)
    sp = pw.cheaptrick(x, f0, t, SR)
    freqs = np.arange(sp.shape[1]) * SR / (2 * (sp.shape[1] - 1))
    db = 10 * np.log10(np.array([np.interp(MEL, freqs, row) for row in sp]) + 1e-20)
    return db, f0 > 0


def _lsd(a, b):
    d = a - b
    d = d - d.mean(axis=-1, keepdims=True)  # gain-normalised
    return np.sqrt((d ** 2).mean(axis=-1))


def mcd(a, b):
    """Envelope distance in dB: median over voiced frames of the gain-normalised
    RMS difference, and the same for the long-term mean envelopes."""
    (ca, va), (cb, vb) = a, b
    n = min(len(ca), len(cb))
    v = va[:n] & vb[:n]
    d = _lsd(ca[:n][v], cb[:n][v])
    lt = _lsd(ca[:n][va[:n]].mean(0), cb[:n][vb[:n]].mean(0))
    return float(np.median(d)), float(lt)


def hnr(x):
    h = parselmouth.Sound(x, SR).to_harmonicity_cc(0.01, 75, 0.1, 1.0).values[0]
    return float(h[h > -199].mean())


def measure(x, y, fx, tx, shift, ref, ref_env, ref_hnr, sung=None):
    fy, _ = track(y)
    ok = ~np.isnan(fx) & ~np.isnan(fy)
    req = shift(tx[ok])
    ach = cents(fy[ok], fx[ok])
    r = dict(n_x=int((~np.isnan(fx)).sum()), n_y=int((~np.isnan(fy)).sum()),
             n_both=int(ok.sum()), err=(ach - req).tolist(), req=req.tolist(), ach=ach.tolist())
    if sung is not None:  # absolute error against the requested contour
        tt = np.clip(np.round(tx[ok] * SR).astype(int), 0, len(sung) - 1)
        r["abs_err"] = (cents(fy[ok], 440.0) - (sung[tt] + req)).tolist()
    r["mcd"], r["lt_mcd"] = mcd(mcep(y), ref_env)
    r["dhnr"] = hnr(y) - ref_hnr
    return r


def task(args):
    inp, method = args
    x, grid = load(inp)
    fx, tx = track(x)
    a = resynth.analyse(method, x)
    rows = {}
    for mod in MODS:
        shift = request(grid, mod)
        y = resynth.synthesize(a, shift)
        if inp["kind"] == "synthetic":
            s = shift(grid["t"])
            ref = voice.render(grid["p"], grid["sung"] + s)  # the ideal: same voice, requested contour
            sung = grid["sung"]
        else:
            ref, sung = x, None
        r = measure(x, y, fx, tx, shift, ref, mcep(ref), hnr(ref), sung)
        if inp["kind"] == "synthetic":  # the tracker's floor: the ideal measured the same way
            fr, _ = track(ref)
            ok = ~np.isnan(fx) & ~np.isnan(fr)
            tt = np.clip(np.round(tx[ok] * SR).astype(int), 0, len(sung) - 1)
            r["ideal_abs_err"] = (cents(fr[ok], 440.0) - (sung[tt] + shift(tx[ok]))).tolist()
        rows[mod] = r
    print(inp["name"], method, flush=True)
    return inp["name"], inp["kind"], method, rows


def identity_scale():
    """LT-MCD between singers of the same sex, and within one singer (first
    half of the scale against the second), on the unmodified inputs."""
    envs = {}
    for inp in real_inputs():
        x, _ = load(inp)
        c, v = mcep(x)
        h = len(c) // 2
        envs[inp["name"]] = (c, v, h)
    within = [mcd((c[:h], v[:h]), (c[h:2 * h], v[h:2 * h]))[1] for c, v, h in envs.values()]
    between = {"male": [], "female": []}
    names = sorted(envs)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if a[0] == b[0]:
                between["male" if a[0] == "m" else "female"].append(
                    mcd(envs[a][:2], envs[b][:2])[1])
    return dict(within=within, between=between)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    jobs = [(i, m) for i in synthetic_inputs() + real_inputs() for m in resynth.METHODS]
    with Pool(10) as pool:
        res = pool.map(task, jobs, chunksize=1)
        scale = pool.apply(identity_scale)
    out = {"results": [dict(name=n, kind=k, method=m, mods=r) for n, k, m, r in res],
           "identity_scale": scale}
    (CACHE / "raw.json").write_text(json.dumps(out))
    print("wrote", CACHE / "raw.json")
