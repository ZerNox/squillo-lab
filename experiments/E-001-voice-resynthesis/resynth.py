"""Re-synthesis methods: each shifts its own f0 track by a requested contour.

Crude experiment code. A request is a function s(t) in cents; each method
multiplies the f0 it analysed by 2**(s(t)/1200) and re-synthesizes, leaving
everything else it analysed unchanged.

- world_harvest, world_dio: WORLD (Morise, Yokomori and Ozawa 2016,
  doi:10.1587/transinf.2015EDP7457) through pyworld: Harvest or DIO plus
  StoneMask for f0, CheapTrick envelope, D4C aperiodicity, 5 ms frames.
- psola: Praat's Manipulation (pitch 0.01 s, floor 60 Hz, ceiling 1100 Hz),
  PitchTier points shifted, overlap-add resynthesis.
"""

import time

import numpy as np
import parselmouth
import pyworld as pw
from parselmouth.praat import call

SR = 48_000
F0_FLOOR, F0_CEIL = 60.0, 1100.0
METHODS = ("world_harvest", "world_dio", "psola")


def _fit(y, n):
    y = np.asarray(y, dtype=np.float64)
    return y[:n] if len(y) >= n else np.pad(y, (0, n - len(y)))


def analyse(method, x):
    x = np.ascontiguousarray(x, dtype=np.float64)
    if method == "world_harvest":
        f0, t = pw.harvest(x, SR, f0_floor=F0_FLOOR, f0_ceil=F0_CEIL, frame_period=5.0)
    elif method == "world_dio":
        f0, t = pw.dio(x, SR, f0_floor=F0_FLOOR, f0_ceil=F0_CEIL, frame_period=5.0)
        f0 = pw.stonemask(x, f0, t, SR)
    elif method == "psola":
        snd = parselmouth.Sound(x, SR)
        manip = call(snd, "To Manipulation", 0.01, F0_FLOOR, F0_CEIL)
        pt = call(manip, "Extract pitch tier")
        k = call(pt, "Get number of points")
        ts = np.array([call(pt, "Get time from index", i) for i in range(1, k + 1)])
        fs = np.array([call(pt, "Get value at index", i) for i in range(1, k + 1)])
        return dict(method=method, n=len(x), manip=manip, ts=ts, fs=fs)
    else:
        raise ValueError(method)
    sp = pw.cheaptrick(x, f0, t, SR)
    ap = pw.d4c(x, f0, t, SR)
    return dict(method=method, n=len(x), f0=f0, t=t, sp=sp, ap=ap)


def synthesize(a, shift):
    """shift: callable, times in s -> cents."""
    if a["method"] == "psola":
        manip, ts, fs = a["manip"], a["ts"], a["fs"]
        new = call("Create PitchTier", "shifted", 0.0, a["n"] / SR)
        for ti, fi in zip(ts, fs * 2 ** (shift(ts) / 1200)):
            call(new, "Add point", float(ti), float(fi))
        call([manip, new], "Replace pitch tier")
        y = call(manip, "Get resynthesis (overlap-add)").values[0]
        return _fit(y, a["n"])
    f0 = np.where(a["f0"] > 0, a["f0"] * 2 ** (shift(a["t"]) / 1200), 0.0)
    y = pw.synthesize(f0, a["sp"], a["ap"], SR, 5.0)
    return _fit(y, a["n"])


def timed(method, x, shift):
    t0 = time.perf_counter()
    a = analyse(method, x)
    t1 = time.perf_counter()
    y = synthesize(a, shift)
    t2 = time.perf_counter()
    return y, t1 - t0, t2 - t1
