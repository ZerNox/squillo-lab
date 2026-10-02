"""E-005 round 7, post hoc (squillo iteration 83): written after round7.py's report, so a diagnostic,
never a bar or a selection.

    uv run python round7_posthoc.py run    # -> results/round7_posthoc.json

Round 7 selected F = 0.75 (a value only when the notes kept are at least 0.75 of the written
states). What does that cost on takes that sing the whole phrase, and why did MT-014 as it stands
fail?
  P1 cost: round 5's cached takes (r5_synth.pkl: R 1680, O 240, L 120; r5_real.pkl: 40 E-002
     re-syntheses, 77 VocalSet originals), each with its `on` K: the share kept / states (5th, 50th
     percentile, minimum) and, per F in round7.FS, how many keep a value (measured or at least)
     against F = 0, by source and set.
  P2 mechanism, round 7's rows at F = 0, per mode: among takes whose statement excludes sigma and
     among those that do not, the share with a found segment not inside a sung note aimed at it
     (seg_right < seg_found).
No check here asserts an outcome; the one assert is that the inputs exist in their counts.
"""

import json
import pickle
import subprocess
import sys
from pathlib import Path

import numpy as np

import round7 as R7

HERE = Path(__file__).parent


def committed_first():
    """S15 C15: refuse to run on an uncommitted edit of this file or of a module it imports."""
    me = Path(__file__).name
    a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
    b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", me, *R7.MODS], cwd=HERE)
    if a.returncode or b.returncode:
        sys.exit(f"{me} is not committed as it stands")


def share(sp):
    return R7.kept(sp) / sp["states"] if sp["states"] else 0.0


def p1_group(rs):
    sh = np.array([share(r["on"]) for r in rs])
    out = dict(n=len(rs), share_p5=float(np.percentile(sh, 5)), share_p50=float(np.median(sh)), share_min=float(sh.min()))
    for F in R7.FS:
        out[f"valued_F{F}"] = sum(R7.state_f(r["on"], F) != "too few" for r in rs)
    return out


def main():
    committed_first()
    syn = pickle.load(open(R7.CACHE / "r5_synth.pkl", "rb"))
    real = pickle.load(open(R7.CACHE / "r5_real.pkl", "rb"))
    assert len(syn) == 2040 and len(real) == 117, (len(syn), len(real))
    p1 = {s: p1_group([r for r in syn if r["src"] == s]) for s in ("R", "O", "L")}
    for kind in ("resynth", "original"):
        rk = [r for r in real if r["kind"] == kind]
        p1[f"real_{kind}_all"] = p1_group(rk)
        for tag in ("scales_straight", "row_vibrato", "scales_vibrato", "row_straight"):
            g = [r for r in rk if tag in r["name"]]
            if g:
                p1[f"real_{kind}_{tag}"] = p1_group(g)
    rows = pickle.load(open(R7.CACHE / "r7_synth.pkl", "rb"))
    assert len(rows) == len(R7.jobs())
    p2 = {}
    for m in R7.MODES:
        rs = [r for r in rows if r["mode"] == m]
        ex = [r for r in rs if R7.excl_f(r["on"], r["sigma"], 0.0)]
        ok = [r for r in rs if not R7.excl_f(r["on"], r["sigma"], 0.0)]
        mis = lambda g: (sum(r["seg_right"] < r["seg_found"] for r in g), len(g))
        p2[m] = dict(excluded=mis(ex), not_excluded=mis(ok),
                     excluded_states={s: sum(R7.state_f(r["on"], 0.0) == s for r in ex) for s in ("measured", "at least")})
    out = dict(P1=p1, P2=p2)
    json.dump(out, open(HERE / "results" / "round7_posthoc.json", "w"), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    {"run": main}[sys.argv[1]](*sys.argv[2:])
