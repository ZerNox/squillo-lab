"""E-002 round 1, fold into squillo (iteration 24). Crude experiment code.

1. Writes squillo's four new `fixtures/signal/` files, by the formulas its
   MANIFEST records, in pure Python binary64 (math.sin, math.cos), rounded to
   f32 with struct.pack('<f').
2. Runs E-002's YIN (threshold 0.1, lags to 63 Hz, acceptance E2..C6 widened
   by 3 cents) on every squillo signal fixture, old and new, and checks the
   scenarios squillo iteration 24 writes.
3. Re-measures timestamp.py's moving-pitch conditions against the instant
   squillo's SG-007 states: sample position 384 i - 766 + P / 2, P = 48000 / f
   the reported period in samples, the mean position of the samples YIN's
   difference function compares (W = 773, so s + (W - 1 + P) / 2).

`uv run python fold.py <dir>` writes the new WAVs to <dir> and
results/fold.json.
"""
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import numpy as np

import run
import yin
from yin import SR, HOP, WIN, cents

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/e002-fold")
OUT.mkdir(parents=True, exist_ok=True)
N = 48_000
pi = math.pi


def wav(samples):
    data = b"".join(struct.pack("<f", s) for s in samples)
    fmt = struct.pack("<HHIIHHH", 3, 1, SR, SR * 4, 4, 32, 0)
    body = (b"WAVE" + b"fmt " + struct.pack("<I", 18) + fmt
            + b"fact" + struct.pack("<I", 4) + struct.pack("<I", len(samples))
            + b"data" + struct.pack("<I", len(data)) + data)
    return b"RIFF" + struct.pack("<I", len(body)) + body


def f_c6_plus_7():
    return 440 * 2 ** (15.07 / 12)


def f_e2_minus_7():
    return 440 * 2 ** (-29.07 / 12)


NEW = {
    "sine-c6-plus-7c.wav": lambda n: 0.5 * math.sin(2 * pi * f_c6_plus_7() * n / 48000),
    "sine-e2-minus-7c.wav": lambda n: 0.5 * math.sin(2 * pi * f_e2_minus_7() * n / 48000),
    # log-linear glide from 220 Hz up at 600 cents/s: f(t) = 220 * 2 ** (t / 2)
    "glide-220hz-600c.wav": lambda n: 0.5 * math.sin(
        2 * pi * 220 * (2 ** (n / 96000) - 1) / (math.log(2) / 2)),
    # vibrato: f(t) = 220 * (1 + 0.029 * sin(2 pi 5.5 t))
    "vibrato-220hz-5p5hz.wav": lambda n: 0.5 * math.sin(
        2 * pi * 220 * n / 48000 + 220 * 0.029 / 5.5 * (1 - math.cos(2 * pi * 5.5 * n / 48000))),
}
TRUE = {  # true f0 at time t in seconds
    "glide-220hz-600c.wav": lambda t: 220 * 2 ** (t / 2),
    "vibrato-220hz-5p5hz.wav": lambda t: 220 * (1 + 0.029 * np.sin(2 * np.pi * 5.5 * t)),
}
STEADY = {
    "sine-220hz.wav": 220.0, "sine-220hz-overshoot.wav": 220.0,
    "sine-e2.wav": yin.E2, "sine-c6.wav": yin.C6,
    "sine-c2.wav": 440 * 2 ** (-33 / 12), "sine-c7.wav": 440 * 2 ** (27 / 12),
    "silence.wav": None,
    "sine-c6-plus-7c.wav": f_c6_plus_7(), "sine-e2-minus-7c.wav": f_e2_minus_7(),
}

out = {"fixtures": {}, "instant": {}}
for name, fn in NEW.items():
    b = wav([fn(n) for n in range(N)])
    (OUT / name).write_bytes(b)
    out["fixtures"][name] = {"sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}


def read(path):
    b = path.read_bytes()
    assert len(b) == 192_058, path
    return np.frombuffer(b[-192_000:], dtype="<f4").astype(np.float64)


def instant(idx, f):
    """Sample position SG-007 states for frame i with reported pitch f."""
    return HOP * idx - 766 + (SR / f) / 2


for name in sorted(set(STEADY) | set(TRUE)):
    p = OUT / name if name in NEW else run.FIX / name
    x = read(p)
    idx, f, _ = yin.yin(x)
    f = yin.in_range(f, 3.0)
    ok = ~np.isnan(f)
    r = {"frames": int(len(idx)), "first": int(idx[0]), "measured": int(ok.sum())}
    if ok.any():
        if name in TRUE:
            t = instant(idx[ok], f[ok]) / SR
            e = cents(f[ok], TRUE[name](t))
            s = HOP * (idx[ok] - 3)
            r["max_abs_cents_at_instant"] = float(np.max(np.abs(e)))
            r["max_abs_cents_at_window_centre"] = float(
                np.max(np.abs(cents(f[ok], TRUE[name]((s + WIN / 2) / SR)))))
            r["instant_ms_before_end"] = [float(v) for v in
                                           ((HOP * idx[ok] + HOP - instant(idx[ok], f[ok])) / SR * 1000)[[0, -1]]]
        elif STEADY[name]:
            r["max_abs_cents"] = float(np.max(np.abs(cents(f[ok], STEADY[name]))))
            r["min_max_reported_cents_vs_true"] = [float(v) for v in
                                                   (lambda c: (c.min(), c.max()))(cents(f[ok], STEADY[name]))]
    out["fixtures"].setdefault(name, {}).update(r)
    print(name, r)

# ---- moving pitch, E-002's conditions, at SG-007's instant
rng = np.random.default_rng(20260926)
run.rng = rng
conds = [("vibrato", dict(rate=r, extent=e)) for r in (5.5, 7.0) for e in (50, 100)] + \
        [("glide", dict(speed=s)) for s in (600, 2400)]
for timbre in ("pure", "saw12"):
    for kind, p in conds:
        errs, meas, tot = [], 0, 0
        for f0 in np.exp(rng.uniform(np.log(yin.E2), np.log(yin.C6), 24)):
            pp = dict(p, ph=rng.uniform(0, 2 * np.pi)) if kind == "vibrato" else p
            x, ft = run.tone(timbre, f0, kind, **pp)
            idx, f, _ = yin.yin(x)
            f = yin.in_range(f, 3.0)
            ok = ~np.isnan(f)
            tot += len(idx); meas += int(ok.sum())
            pos = instant(idx[ok], f[ok])
            truth = np.interp(pos, np.arange(len(ft)), ft)
            errs.append(cents(f[ok], truth))
        e = np.abs(np.concatenate(errs))
        k = int((e <= 3).sum()); n = len(e)
        z = 1.959964
        c = (k + z * z / 2) / (n + z * z); h = z * math.sqrt(k * (n - k) / n + z * z / 4) / (n + z * z)
        key = f"{timbre}/{kind}/" + "/".join(f"{a}={b}" for a, b in p.items())
        out["instant"][key] = {"tones": 24, "frames": tot, "measured": meas,
                               "p95_abs": float(np.percentile(e, 95)), "max_abs": float(e.max()),
                               "within_3c": k / n, "within_3c_wilson95": [c - h, c + h]}
        print(key, {a: round(b, 3) if isinstance(b, float) else b for a, b in out["instant"][key].items()})

(run.OUT / "fold.json").write_text(json.dumps(out, indent=1))
