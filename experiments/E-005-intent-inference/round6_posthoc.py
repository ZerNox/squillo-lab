"""E-005 round 6, post hoc (squillo iteration 76): written after round6.py's report, so a
diagnostic, never a selection or a bar.

    uv run python round6_posthoc.py run 18    # -> results/round6_posthoc.json

Round 6 found no centring rung called improved, at any gate or strength. Why?
  D1 on every fresh phrase with a value of K: at full strength, under the selected
     gate (T = 15) and UNGATED (every kept note with |d| > 2u moved, round 3's
     post hoc), K's fall (take K minus rung K, the rung from its description)
     against MT-008's bound 2 sqrt(uB_take^2 + uB_rung^2); improved counts; the
     settle term's share of uB (the weighted rms settle u over uB).
  D2 WORLD delivery of the gated full-strength moves (round 6 delivered none,
     since no rung was reached): on up to two fresh phrases per cell with a moved
     note under T = 15, round6.world_one at strength 64 / 64; per moved note the
     achieved shift (rung samples' centre minus identity's) minus the requested m.
No check here asserts an outcome; the one assert is that the inputs exist and none
errored (S15 C10).
"""

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import json
import math
import pickle
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

import round3 as R3
import round5 as R5
import round6 as R6

HERE = Path(__file__).parent
GATE = 15.0   # round 6's selected gate (results/round6.json selected_gate)


def committed_first():
    """S15 C15: refuse to run on an uncommitted edit of this file or of a module it imports."""
    me = Path(__file__).name
    a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
    b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", me, "round6.py", "round5.py", "round3.py"], cwd=HERE)
    if a.returncode or b.returncode:
        sys.exit(f"{me} is not committed as it stands")


def d1(row):
    t, c, st = row["t"].astype(float), row["cents"].astype(float), np.asarray(row["states"], float)
    sp, kp = R6.take_of(c, t, st)
    if kp is None or not np.isfinite(sp["s"]):
        return None
    u = np.hypot(kp["us"], kp["u_ref"])
    kept = ~kp["wrong"]
    out = dict(cell=(row["source"], row["sigma"], row["vib"]), K=sp["s"], uB=sp["uB"],
               settle_share=float(math.sqrt(np.average(kp["us"][kept] ** 2, weights=kp["dur"][kept])) / sp["uB"]))
    for name, mask in (("gated", R6.moved_mask(kp, GATE)), ("ungated", kept & (np.abs(kp["d"]) > 2 * u))):
        if not mask.any():
            out[name] = None
            continue
        r = R6.rung_sp(c, t, st, kp, R6.moves_at(kp, mask, R6.GRID))
        out[name] = dict(moved=int(mask.sum()), fall=sp["s"] - r["s"], bound=2 * math.hypot(sp["uB"], r["uB"]),
                         call=R5.compare(sp, r, R6.X_CAP), rung_state=R5.state(r, R6.X_CAP))
    return out


def run(procs="18"):
    committed_first()
    fr = R6.keyed(pickle.load(open(R6.CACHE / "r6_fresh.pkl", "rb")), "fresh")
    rows6 = {a["key"]: a for a in pickle.load(open(R6.CACHE / "r6_rows.pkl", "rb"))}
    assert len(fr) == 720
    with Pool(int(procs)) as p:
        D = p.map(d1, fr, chunksize=4)
    out = dict(gate=GATE, phrases=len(fr), with_value=sum(d is not None for d in D))
    cells = {}
    for d in D:
        if d is not None:
            cells.setdefault(str(d["cell"]), []).append(d)
    tab = {}
    for key, ds in sorted(cells.items()):
        e = dict(phrases=len(ds), settle_share_median=round(float(np.median([d["settle_share"] for d in ds])), 3))
        for name in ("gated", "ungated"):
            g = [d[name] for d in ds if d[name] is not None]
            e[name] = dict(with_moves=len(g), improved=sum(x["call"] == 1 for x in g), worse=sum(x["call"] == -1 for x in g),
                           fall_median=round(float(np.median([x["fall"] for x in g])), 2) if g else None,
                           bound_median=round(float(np.median([x["bound"] for x in g])), 2) if g else None,
                           moved_median=float(np.median([x["moved"] for x in g])) if g else None)
        tab[key] = e
    out["D1_cells"] = tab
    for name in ("gated", "ungated"):
        g = [d[name] for d in D if d is not None and d[name] is not None]
        out[f"D1_{name}"] = dict(with_moves=len(g), improved=sum(x["call"] == 1 for x in g), worse=sum(x["call"] == -1 for x in g),
                                 fall_over_bound_max=round(float(max(x["fall"] / x["bound"] for x in g)), 3) if g else None)
    # D2: WORLD delivery of the gated full-strength moves
    jobs, count = [], {}
    for r in sorted(fr, key=lambda r: r["seed"]):
        a = rows6[r["key"]]
        cell = (r["source"], r["sigma"], r["vib"])
        if a["gates"].get(str(GATE), {}).get("moved", 0) > 0 and count.get(cell, 0) < 2:
            count[cell] = count.get(cell, 0) + 1
            jobs.append(("fresh", r, a, str(GATE)))
    with Pool(int(procs)) as p:
        W = p.map(R6.world_one, jobs, chunksize=1)
    assert len(W) == len(jobs) and all(w["moved"] > 0 for w in W)
    ach = [(a, b) for w in W for a, b in w["achieved"]]
    err = [b - a for a, b in ach]
    dk = [abs(w["samples"]["s"] - w["desc"]["s"]) for w in W if np.isfinite(w["samples"]["s"]) and np.isfinite(w["desc"]["s"])]
    di = [abs(w["identity"]["s"] - w["take"]["s"]) for w in W if np.isfinite(w["identity"]["s"]) and np.isfinite(w["take"]["s"])]
    out["D2_world"] = dict(pairs=len(W), cells=len(count), moved_notes_matched=len(ach),
                           requested_abs_median=round(float(np.median([abs(a) for a, _ in ach])), 2) if ach else None,
                           achieved_minus_requested_p5_p50_p95=[round(float(np.percentile(err, q)), 3) for q in (5, 50, 95)] if err else None,
                           achieved_minus_requested_abs_max=round(float(np.max(np.abs(err))), 3) if err else None,
                           K_samples_minus_desc_abs_median_max=[round(float(np.median(dk)), 3), round(float(np.max(dk)), 3)] if dk else None,
                           K_identity_minus_take_abs_median_max=[round(float(np.median(di)), 3), round(float(np.max(di)), 3)] if di else None,
                           call_desc=[w["call_desc"] for w in W].count(1), call_samples=[w["call_samples"] for w in W].count(1))
    json.dump(out, open(R6.OUT / "round6_posthoc.json", "w"), indent=1, default=float)
    print(json.dumps({k: v for k, v in out.items() if k != "D1_cells"}, indent=1, default=float))
    for k, v in tab.items():
        print(k, v)


if __name__ == "__main__":
    dict(run=run)[sys.argv[1]](*sys.argv[2:])
