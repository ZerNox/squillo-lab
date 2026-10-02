"""E-001 round 3, descriptive analysis written after the run (holds no rule): from
results/r3/loudness.json, (a) how far the rungs of one take differ in loudness among
themselves, (b) dL by sex of VocalSet singer, (c) the rungs' and takes' sample peaks (whether any rung exceeds full scale), (d) the per-item
list for the README.
`uv run python r3_describe.py` -> results/r3/describe.json."""
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
R = HERE / "results" / "r3"
rep = json.loads((R / "loudness.json").read_text())
out = {}
for kind in ("vocalset", "synthetic", "fixture"):
    by = {}
    for i in rep["items"]:
        if i["kind"] == kind:
            by.setdefault(i["input"], []).append(i["dL"])
    spread = [max(v) - min(v) for v in by.values() if len(v) > 1]
    out[f"between_rungs_{kind}"] = dict(takes=len(spread), max=float(max(spread)), median=float(np.median(spread)))
for s in ("f", "m"):
    dl = [i["dL"] for i in rep["items"] if i["kind"] == "vocalset" and i["input"].startswith(s)]
    out[f"vocalset_{s}"] = dict(n=len(dl), median=float(np.median(dl)), min=float(min(dl)), max=float(max(dl)))
pk = []
for i in rep["items"]:
    d = HERE / "data" / "cache" / ("f1" if i["kind"] == "fixture" else "r3")
    y = np.fromfile(d / "out" / f'{i["input"]}.{i["request"]}.native.f64', dtype="<f8").astype(np.float32)
    x = np.fromfile(d / f'{i["input"]}.x.f64', dtype="<f8")
    pk.append((float(np.abs(y).max()), float(np.abs(x).max()), i["kind"], i["input"], i["request"]))
out["peaks"] = dict(rung_max=max(pk)[0], at=max(pk)[2:], its_take=max(pk)[1],
                    rungs_over_full_scale=sum(p[0] > 1.0 for p in pk), take_max=max(p[1] for p in pk))
out["vocalset_items"] = {f'{i["input"]}/{i["request"]}': round(i["dL"], 3) for i in rep["items"] if i["kind"] == "vocalset"}
(R / "describe.json").write_text(json.dumps(out, indent=1))
print(json.dumps({k: v for k, v in out.items() if k != "vocalset_items"}, indent=1))
