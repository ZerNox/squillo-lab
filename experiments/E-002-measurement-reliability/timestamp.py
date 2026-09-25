"""E-002 round 1, follow-up: which instant does a YIN frame's pitch describe?

YIN compares x[s .. s+W) with x[s+tau .. s+tau+W), W = 1536 - tau_max (773
here), so its estimate refers to the centre of that span, s + (W + tau)/2,
not the pitch window's centre s + 768. Compare the frame's pitch with the
true f0 at both instants under vibrato and glides.
`uv run python timestamp.py` writes results/timestamp.json.
"""
import json
import numpy as np
import run, yin
from yin import SR, HOP, WIN

TAU_MAX = int(np.ceil(SR / 63.0)) + 1
W = WIN - TAU_MAX
out = {"W": W, "tau_max": TAU_MAX}
conds = [("vibrato", dict(rate=r, extent=e)) for r in (5.5, 7.0) for e in (50, 100)] + \
        [("glide", dict(speed=s)) for s in (600, 2400)]
for kind, p in conds:
    per = {"centre": [], "lag_centre": []}
    for f0 in np.exp(run.rng.uniform(np.log(yin.E2), np.log(yin.C6), 24)):
        pp = dict(p, ph=run.rng.uniform(0, 2 * np.pi)) if kind == "vibrato" else p
        x, ft = run.tone("saw12", f0, kind, **pp)
        idx, f, _ = yin.yin(x)
        f = yin.in_range(f, 3.0)
        s = HOP * (idx - 3)
        ok = ~np.isnan(f)
        tau = np.where(ok, SR / np.where(ok, f, 1.0), 0)
        t_lag = np.clip(np.round(s + (W + tau) / 2).astype(int), 0, len(ft) - 1)
        per["centre"].append(run.cents(f, ft[s + WIN // 2]))
        per["lag_centre"].append(np.where(ok, run.cents(f, ft[t_lag]), np.nan))
    key = f"{kind}/" + "/".join(f"{k}={v}" for k, v in p.items())
    out[key] = {r: run.summarise(v, sum(len(a) for a in v)) for r, v in per.items()}
    s = out[key]
    print(key, {r: (round(s[r]["fine_p95_abs"], 2), round(s[r]["fine_max_abs"], 2),
                    round(100 * s[r]["within_3c_of_measured"], 1)) for r in s})
(run.OUT / "timestamp.json").write_text(json.dumps(out, indent=1))
