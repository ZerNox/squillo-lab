"""E-005 fold 5, part 2 (squillo iteration 74, F-041): round 5's bars B2 and B3, and its
power and real-take states, re-read at the 40-cent cap squillo chooses (X = 40). Crude
experiment code; reads round 5's cached rows, changes nothing in round5.py.

    uv run python fold5_x40.py run     # -> results/fold5_x40.json

Why: round 5 applied B2 (false change) and B3 (re-syntheses) only to the selected candidate,
X = inf (round5.py report: `Xs = sel`). Squillo ADR 0015 chooses X = 40, which B1 passed
(results/round5.json B1["40.0"]), so its B2 and B3 are read here before any squillo text
cites them (S18).

Inputs: data/cache/r5_synth.pkl (2040 rows) and r5_real.pkl (117), round 5's, unchanged;
round 2's r2_real.pkl for the re-syntheses' truth. Round 5's own functions (round5.state,
round5.excludes, round5.compare, round5.cells_of) at X40 = round5.XS[1].

Rules, written and committed before the run (BAR = round5.BAR_MISS, 5 %):
  B2@40: in each of the six length x vibrato conditions, pairs of phrases of one R cell
    (2i, 2i + 1), pooled over sigma (140 pairs), the comparison at X = 40 calls a change in
    at most BAR.
  B3@40: on the re-syntheses whose truth found every state, in each set, the statement at
    X = 40 excludes the true spread in at most BAR.
  Reported with no bar: the halves of the originals (false changes), each real set's states,
  the power 20 -> 0 and 40 -> 10 at X = 40, and the lower end over all reported phrases.
Checks of the checks (S15), each on an input that differs:
  C1 must pass: this script's B2 and B3 code at X = inf reproduces round5.json's B2 cells and
     B3 miss counts exactly.
  C2 must fail: the B2 rule applied to pairs across cells (sigma 40 earlier, sigma 0 later,
     straight, 56 notes, phrase k against phrase k) calls a change in more than BAR.
"""

import json
import math
import pickle
import subprocess
import sys
from pathlib import Path

import numpy as np

import round2 as R2
import round5 as R5
import fold_refusal as FR

HERE = Path(__file__).parent
CACHE = HERE / "data" / "cache"
OUT = HERE / "results"
X40 = R5.XS[1]  # 40 cents, round 5's cap at the largest spread round 2 tested
assert X40 == 40.0
BAR = R5.BAR_MISS


def committed_first():
    """S15: refuse to run on an uncommitted edit of this file, or before it is committed."""
    me = Path(__file__).name
    a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
    b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", me], cwd=HERE)
    if a.returncode or b.returncode:
        sys.exit(f"{me} is not committed as it stands: commit the rules before running")


def b2(cl, X):
    fc = {}
    for L in R2.LENGTHS:
        for vib in (0, 1):
            calls = []
            for sg in R2.SIGMAS:
                rs = cl[f"R L={L} vib={vib} sigma={sg}"]
                calls += [R5.compare(rs[2 * i]["on"], rs[2 * i + 1]["on"], X) != 0 for i in range(len(rs) // 2)]
            fc[f"L={L} vib={vib}"] = R5.wilson(sum(calls), len(calls))
    return fc


def real_sets(real, truth, X):
    rr = {}
    for kind, sets in (("resynth", ("scales_straight", "row_vibrato")),
                       ("original", ("scales_straight", "row_straight", "scales_vibrato", "row_vibrato"))):
        for S in sets:
            b = [r for r in real if r["kind"] == kind and S in r["name"]]
            d = dict(takes=len(b), measured=sum(R5.state(r["on"], X) == "measured" for r in b),
                     at_least=sum(R5.state(r["on"], X) == "at least" for r in b),
                     too_few=sum(R5.state(r["on"], X) == "too few" for r in b))
            if kind == "resynth":
                full = [r for r in b if truth[r["name"]]["found"] == truth[r["name"]]["states"]]
                d["miss_on_full_truth"] = R5.wilson(sum(R5.excludes(r["on"], truth[r["name"]]["sd"], X) for r in full), len(full))
            else:
                hv = [R5.compare(r["halves"][0], r["halves"][1], X) != 0 for r in b]
                d["halves_false_change"] = [int(sum(hv)), len(hv)]
            rr[f"{kind} {S}"] = d
    return rr


def main():
    committed_first()
    rows = pickle.load(open(CACHE / "r5_synth.pkl", "rb"))
    real = pickle.load(open(CACHE / "r5_real.pkl", "rb"))
    r2real = pickle.load(open(CACHE / "r2_real.pkl", "rb"))
    assert len(rows) == 2040 and len(real) == 117
    truth = {r["name"]: r["truth"] for r in r2real["resynth"]}
    r5 = json.load(open(OUT / "round5.json"))
    cl = R5.cells_of(rows)
    # C1: reproduction at X = inf
    fc_inf = b2(cl, math.inf)
    rr_inf = real_sets(real, truth, math.inf)
    c1 = (fc_inf == {k: v for k, v in r5["B2_false_change"]["cells"].items()}
          and all(rr_inf[k]["miss_on_full_truth"] == r5["real"][k]["miss_on_full_truth"] for k in rr_inf if k.startswith("resynth")))
    # the run at X = 40
    fc = b2(cl, X40)
    rr = real_sets(real, truth, X40)
    pw = {}
    for L in R2.LENGTHS:
        for vib in (0, 1):
            for a, b in ((20, 0), (40, 10)):
                A, B = cl[f"R L={L} vib={vib} sigma={a}"], cl[f"R L={L} vib={vib} sigma={b}"]
                rk = [R5.compare(x["on"], y["on"], X40) for x, y in zip(A, B)]
                rw = [FR.compare(x["wrapped"], y["wrapped"]) for x, y in zip(A, B)]
                pw[f"L={L} vib={vib} {a}->{b}"] = dict(known_improved=R5.wilson(sum(v == 1 for v in rk), len(rk)),
                                                       known_worse=sum(v == -1 for v in rk),
                                                       wrapped_improved=R5.wilson(sum(v == 1 for v in rw), len(rw)))
    rep = [r for r in rows if R5.state(r["on"], X40) != "too few"]
    lower = R5.wilson(sum(r["on"]["s"] - 2 * r["on"]["uB"] <= r["sigma"] for r in rep), len(rep))
    # C2: across cells must fail the B2 bar
    A, B = cl["R L=56 vib=0 sigma=40"], cl["R L=56 vib=0 sigma=0"]
    across = R5.wilson(sum(R5.compare(x["on"], y["on"], X40) != 0 for x, y in zip(A, B)), len(A))
    res = dict(x=X40, B2_at_40=dict(cells=fc, passes=all(v[0] <= BAR for v in fc.values())),
               B3_at_40_passes=all(v["miss_on_full_truth"][0] <= BAR for k, v in rr.items() if k.startswith("resynth")),
               real_at_40=rr, power_at_40=pw, lower_end_holds_at_40=lower,
               check_C1_reproduces_round5_at_inf=c1, must_fail_C2_across_cells=across,
               must_fail_C2_exceeds_bar=across[0] > BAR)
    json.dump(res, open(OUT / "fold5_x40.json", "w"), indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))
    assert res["check_C1_reproduces_round5_at_inf"]
    assert res["must_fail_C2_exceeds_bar"]


if __name__ == "__main__":
    {"run": main}[sys.argv[1]](*sys.argv[2:])
