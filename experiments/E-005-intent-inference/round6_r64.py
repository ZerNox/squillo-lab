"""E-005 round 6, row R6-4's real-take counts (squillo iteration 83, F-074): a diagnostic written
long after round 6's report, never a bar or a selection.

    uv run python round6_r64.py run 18    # -> results/round6_r64.json

Round 6's README row R6-4 states, for the 117 real takes (round 3's cache r3_real.pkl: 40 E-002
WORLD re-syntheses and 77 VocalSet originals), "of 1766 kept notes in the 117 takes, 345 are
measurably off (|d| > 2u) but the gate needs u < 3.75 cents and only 2 notes have 4u <= 15; median
u 14.5 cents". No results file holds these counts (squillo F-074). This script computes them with
round 6's own definitions (round6.take_of, round6.moved_mask's u = hypot(settle u, u_ref) and
|d| > 2u; kept = not round 3's wrong note) and saves them; the README row is then matched to them
or marked.

Definitions, written before the run (each counted over the 117 takes):
  A over takes whose round 3 path exists (kp not None):
    kept      sum of kept notes (~kp["wrong"]);
    off       kept notes with |d| > 2u;
    small_u   kept notes with 4u <= T, T = 15 (round 6's selected gate: |d| > 2u and |d| + 2u <= T
              need 4u < T);
    median_u  median u over kept notes.
  B the same over the takes where round6.moved_mask is not None (K has a value), the takes the gate
    is applied to.
  moved_T15   notes moved under T = 15 (round6.moved_mask), which round6.json's totals give as 0.
The one assert is that the 117 inputs exist and none errored (S15 C10); no outcome is asserted.
"""

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import json
import pickle
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

import round6 as R6

HERE = Path(__file__).parent
GATE = 15.0   # round 6's selected gate (results/round6.json selected_gate)
N_REAL = 117  # round 6's real takes (round6.py run_analyse: len(real) == 117)


def committed_first():
    """S15 C15: refuse to run on an uncommitted edit of this file or of a module it imports."""
    me = Path(__file__).name
    a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
    b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", me, "round6.py", "round5.py", "round3.py"], cwd=HERE)
    if a.returncode or b.returncode:
        sys.exit(f"{me} is not committed as it stands")


def one(row):
    t, c, st = row["t"].astype(float), row["cents"].astype(float), np.asarray(row["states"], float)
    sp, kp = R6.take_of(c, t, st)
    if kp is None:
        return dict(kind=row.get("kind"), path=False)
    u = np.hypot(kp["us"], kp["u_ref"])
    k = ~kp["wrong"]
    mask = R6.moved_mask(kp, GATE)
    return dict(kind=row.get("kind"), path=True, valued=mask is not None, u=[float(v) for v in u[k]],
                off=int((k & (np.abs(kp["d"]) > 2 * u)).sum()), small_u=int((k & (4 * u <= GATE)).sum()),
                moved=int(mask.sum()) if mask is not None else 0)


def tally(rs):
    us = [v for r in rs for v in r["u"]]
    return dict(takes=len(rs), kept=len(us), off=sum(r["off"] for r in rs), small_u=sum(r["small_u"] for r in rs),
                median_u=float(np.median(us)) if us else None)


def main(procs="18"):
    committed_first()
    real = R6.keyed(pickle.load(open(R6.CACHE / "r3_real.pkl", "rb")), "real")
    assert len(real) == N_REAL, len(real)
    with Pool(int(procs)) as p:
        rows = p.map(one, real)
    assert len(rows) == N_REAL
    A = [r for r in rows if r["path"]]
    B = [r for r in A if r["valued"]]
    out = dict(A=tally(A), B=tally(B), moved_T15=sum(r["moved"] for r in A), no_path=len(rows) - len(A),
               by_kind={k: tally([r for r in A if r["kind"] == k]) for k in sorted({r["kind"] for r in A})})
    json.dump(out, open(HERE / "results" / "round6_r64.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    {"run": main}[sys.argv[1]](*sys.argv[2:])
