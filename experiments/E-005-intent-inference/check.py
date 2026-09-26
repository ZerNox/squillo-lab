"""S15 input check: long-term spectrum of synthetic phrases against unmodified
VocalSet takes. Crude experiment code.

    uv run python check.py   # -> results/input_check.json

Welch PSD (8192-point Hann, 48 kHz), summed in one-third-octave bands, in dB
relative to the strongest band of the same input.
"""

import json
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly, welch

import synth

HERE = Path(__file__).parent
CENTRES = [250, 500, 1000, 2000, 4000, 8000, 16000]


def bands(x, sr=48_000):
    f, p = welch(x, sr, nperseg=8192)
    allc = 1000 * 2 ** (np.arange(-12, 13) / 3)
    lv = {}
    for c in allc:
        m = (f >= c * 2 ** (-1 / 6)) & (f < c * 2 ** (1 / 6))
        lv[c] = 10 * np.log10(p[m].sum() + 1e-30)
    top = max(lv.values())
    return {c: round(lv[min(allc, key=lambda a: abs(a - c))] - top, 1) for c in CENTRES}


out = {"synthetic": {}, "vocalset": {}}
for i, (v, sc) in enumerate([("bass", "major"), ("tenor", "minor"), ("mezzo", "major"), ("soprano", "pentatonic")]):
    x, _ = synth.phrase(v, sc, 20, 0, 0, 777 + i)
    out["synthetic"][v] = bands(x)
for name in ["m1_scales_straight_a", "m3_scales_straight_a", "f2_scales_straight_a", "f5_scales_straight_a",
             "m3_row_straight", "f2_row_straight"]:
    x, sr = sf.read(HERE / "data" / "cache" / f"{name}.wav")
    x = resample_poly(x, 160, 147) if sr == 44_100 else x
    out["vocalset"][name] = bands(x)
rng = {c: [min(d[c] for d in out["vocalset"].values()), max(d[c] for d in out["vocalset"].values())] for c in CENTRES}
out["vocalset_range"] = rng
out["synthetic_inside"] = {v: {c: rng[c][0] - 3 <= d[c] <= rng[c][1] + 3 for c in CENTRES} for v, d in out["synthetic"].items()}
json.dump(out, open(HERE / "results" / "input_check.json", "w"), indent=1, default=str)
print(json.dumps(out, indent=1, default=str))
