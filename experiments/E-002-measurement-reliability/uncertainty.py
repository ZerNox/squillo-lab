"""E-002 round 1, follow-up: does YIN's own CMND minimum (the aperiodicity
of the chosen dip) predict a frame's error? A first candidate per-frame
uncertainty estimator (protocol step 3). Steady -12 dB/oct tones in white
noise, 24 tones per SNR. `uv run python uncertainty.py` writes
results/uncertainty.json.
"""
import json
import numpy as np
import run, yin

bins = [0, 0.01, 0.02, 0.05, 0.1]
rows = {f"{a}-{b}": [] for a, b in zip(bins[:-1], bins[1:])}
by_snr = {}
for snr in (40, 30, 25, 20, 15, 10):
    errs, dms = [], []
    for f0 in np.exp(run.rng.uniform(np.log(yin.E2), np.log(yin.C6), 24)):
        x, ft = run.tone("saw12", f0)
        x = run.add_noise(x, snr)
        idx, f, dm = yin.yin(x)
        f = yin.in_range(f, 3.0)
        ok = ~np.isnan(f)
        errs.append(np.abs(run.cents(f[ok], f0))); dms.append(dm[ok])
    e, d = np.concatenate(errs), np.concatenate(dms)
    by_snr[snr] = {"measured_frames": int(len(e)), "median_dmin": float(np.median(d)) if len(d) else None}
    for a, b in zip(bins[:-1], bins[1:]):
        m = (d >= a) & (d < b)
        rows[f"{a}-{b}"].append(e[m])
out = {"by_snr": by_snr, "by_dmin": {}}
for k, v in rows.items():
    e = np.concatenate(v)
    out["by_dmin"][k] = None if len(e) == 0 else {
        "frames": int(len(e)), "median": float(np.median(e)), "p95": float(np.percentile(e, 95)),
        "max": float(e.max()), "gross_frac": float(np.mean(e > 50))}
    print(k, out["by_dmin"][k])
print(by_snr)
(run.OUT / "uncertainty.json").write_text(json.dumps(out, indent=1))
