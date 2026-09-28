"""E-002 round 4, held in a results file for squillo's review R-10 (iteration 50, S18): the ring
ratio's 2u = 2 sqrt(tau^2 + sigma_w^2 / k) for k shared notes, per fold, from results/r4_ring.json's
fit, and the k the comparable takes actually have. Crude experiment code.

Check of the check: r4_ring.called must call a D 0.001 dB above 2u changed and one 0.001 dB below
not changed, at every k and fold (must pass and must fail, different inputs).

    uv run python r10_two_u.py     # -> results/r10_two_u.json
"""
import json
from pathlib import Path

import numpy as np

import r4_ring

HERE = Path(__file__).parent
d = json.loads((HERE / "results/r4_ring.json").read_text())
ks = sorted({r["k"] for r in d["sensitivity"]["breathy_vs_straight"]["rows"]} | {r["k"] for r in d["sensitivity"]["forte_vs_pp"]["rows"]})
out = dict(source="results/r4_ring.json fit", k_seen_in_sensitivity=ks, no_change_k_median=d["no_change_comparable"]["k_median"], two_u_dB={})
for fold, f in d["fit"].items():
    m = (f["sigma_w_dB"], f["tau_dB"])
    row = {}
    for k in range(1, 13):
        b = 2 * np.sqrt(m[1] ** 2 + m[0] ** 2 / k)
        assert r4_ring.called(dict(D=b + 0.001, k=k), m) and not r4_ring.called(dict(D=b - 0.001, k=k), m), (fold, k)
        row[str(k)] = round(float(b), 4)
    out["two_u_dB"][fold] = row
allv = [v for f in out["two_u_dB"].values() for k, v in f.items() if int(k) <= max(ks)]
out["range_over_k_seen"] = [min(allv), max(allv)]
(HERE / "results/r10_two_u.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
