"""E-001 round 3, after the run (squillo L-054): where the two BS.1770 meters differ, read from
both codes. Holds no rule; diagnoses revision 2's failed agreement (m11, c100, 0.0500).

  (a) K-weighting: pyloudnorm 0.2.0's two biquads against BS.1770-4's 48 kHz coefficients,
      the response difference in dB over 20 Hz-20 kHz (and from 50 and 80 Hz);
  (b) framing: pyloudnorm counts blocks as round((T - 0.4) / 0.1) + 1 and sums a final block
      shorter than 400 ms over the full block length; this script's meter counts whole blocks
      only. Reproduced on the failed case: this meter's gating with pyloudnorm's filters, under
      each framing, against pyloudnorm's own reading.

`uv run python r3_meters.py` -> results/r3/meters.json."""
import json
from pathlib import Path

import numpy as np
import pyloudnorm as pyln
from scipy.signal import freqz, lfilter

import r3_loudness as r

HERE = Path(__file__).parent
M = pyln.Meter(r.SR)
HS, HP = M._filters["high_shelf"], M._filters["high_pass"]
f = np.geomspace(20, 20000, 4000)


def resp(b1, a1, b2, a2):
    h = freqz(b1, a1, worN=f, fs=r.SR)[1] * freqz(b2, a2, worN=f, fs=r.SR)[1]
    return 20 * np.log10(np.abs(h))


d = resp(HS.b, HS.a, HP.b, HP.a) - resp(r.K1_B, r.K1_A, r.K2_B, r.K2_A)
out = {"filters_db": {str(lo): [float(d[f >= lo].min()), float(d[f >= lo].max())] for lo in (20, 50, 80)},
       "filters_at_997": float(np.interp(997, f, d))}


def level(x, frame):
    z = lfilter(HP.b, HP.a, lfilter(HS.b, HS.a, x))
    n, hop = int(0.4 * r.SR), int(0.1 * r.SR)
    m = (len(z) - n) // hop + 1 if frame == "whole" else int(np.round((len(z) / r.SR - 0.4) / 0.1)) + 1
    zz = np.array([np.sum(z[j * hop:j * hop + n] ** 2) / n for j in range(m)])
    return float(r.lk(zz[r.gates(zz)].mean())), m, len(z[(m - 1) * hop:(m - 1) * hop + n])


y = np.fromfile(HERE / "data/cache/r3/out/m11.c100.native.f64", "<f8").astype(np.float32).astype(np.float64)
x = np.fromfile(HERE / "data/cache/r3/m11.x.f64", "<f8")
case = {}
for nm, v in (("take", x), ("rung", y)):
    w, rr = level(v, "whole"), level(v, "round")
    case[nm] = dict(standard=r.bs1770(v), pyln=r.pyln_l(v), pyfilters_whole_blocks=w[0], blocks_whole=w[1],
                    pyfilters_round_blocks=rr[0], blocks_round=rr[1], last_block_samples=rr[2])
out["m11_c100"] = case
out["reproduced"] = max(abs(c["pyfilters_round_blocks"] - c["pyln"]) for c in case.values())
(HERE / "results/r3/meters.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
