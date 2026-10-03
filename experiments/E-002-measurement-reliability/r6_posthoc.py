"""E-002 round 6, post hoc (squillo iteration 88, F-075): written after r6_fixture.py's results were read,
committed before it runs, counted apart from the round's hypothesis. Crude experiment code.

    uv run python r6_posthoc.py <squillo>      # -> results/r6_posthoc.json

Why. The round's results give the 2 Hz contour a least distance of 0.037 cents from the 60-cent threshold
over the frames where pieces are formed (results/r6_fixture.json margin_cents). A cut that an
implementation's arithmetic can move would make a scenario that names exact frames fragile. ADR 0007
records the host's f32 against f64 difference, at most 0.0082 cents per frame (squillo-lab E-002 @
00bf2e9); the WASM targets are unmeasured.

What it records, no bar:
  D1 For each piece formed on the fixture's contour (the cut loop of fold2.held_notes as r5_trim.cuts
     runs it): its first frame, the frame it is cut at, and the contour's least distance from the
     threshold over its frames (to the cut frame included), in squillo's frame numbers.
  D2 Each measured cell's pitch moved by an independent uniform offset in [-e, +e] cents, e in E_SWEEP,
     N_SEEDS seeds each (numpy default_rng(seed)): on how many the round's outcome H holds (trimmed: two
     held notes of one block each and steadiness measured; untrimmed: one, steadiness unmeasurable), and
     on how many every held note's first and last frames and every block's frames equal the fixture's
     under each finder. e = 0.0082 is ADR 0007's host epsilon; 0.037 the margin; the rest a sweep.
  D3 The float32 tracking's largest difference from float64 on the fixture's measured cells, in cents.
Its check (C10): D2's comparison of frames is run with e = 0 (must pass: the frames equal the fixture's)
and on Q's cells (must fail: Q's notes differ from the fixture's), before any e > 0 is run.

Crude, disposable lab code: never product code (squillo PLAN.md rule 11).
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
GUARDED = ("r6_posthoc.py", "r6_fixture.py", "r5_trim.py", "fold2.py", "fold3_ladder.py", "r2_analyse.py", "yin.py")


def committed_first():
    """S15 (C15): refuse to run on an uncommitted edit of this file or of the modules whose rules it runs."""
    for me in GUARDED:
        a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
        b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", me], cwd=HERE)
        if a.returncode or b.returncode:
            sys.exit(f"{me} is not committed as it stands: commit the rules before running")


if __name__ == "__main__":
    committed_first()
    SQ = Path(sys.argv[1])
    sys.argv = sys.argv[:1] + [str(SQ)]

import r6_fixture as R6     # noqa: E402

T, F2 = R6.T, R6.F2
E_SWEEP = (0.0082, 0.037, 0.1, 0.3, 1.0, 3.0)
N_SEEDS = 200
OUT = HERE / "results" / "r6_posthoc.json"


def pieces(p, u):
    a = ~np.isnan(p) & np.isfinite(u)
    x = np.arange(len(p))
    lp = F2.filtfilt(*F2.B2, np.interp(x, x[a], p[a]))
    out, s0 = [], 0
    while s0 < len(p):
        ref = np.median(lp[s0:s0 + 31])
        s1 = s0 + 1
        while s1 < len(p) and abs(lp[s1] - ref) <= F2.SPLIT:
            s1 += 1
        seg = lp[s0:min(s1 + 1, len(p))]
        out.append(dict(first=s0 + 3, cut=(s1 + 3 if s1 < len(p) else None),
                        margin=float(np.min(np.abs(np.abs(seg - ref) - F2.SPLIT)))))
        s0 = s1
    return out


def outcome(p, u, idx):
    n_tr, t_tr = R6.notes_of(p, u, idx, True)
    n_cu, t_cu = R6.notes_of(p, u, idx, False)
    H = (len(n_tr) == 2 and all(len(n["blocks"]) == 1 for n in n_tr) and t_tr["S"] is not None
         and len(n_cu) == 1 and len(n_cu[0]["blocks"]) == 1 and t_cu["S"] is None)
    return H, (n_tr, n_cu)


def main():
    m = json.loads(R6.OUT.read_text())["selection"]["m"]
    x0, gap = R6.samples(m)
    raw, x = R6.as_file(x0)
    idx, p, u = R6.track(x)
    rep = dict(rules="see the docstring", m=m)
    rep["D1"] = pieces(p, u)
    H0, ref = outcome(p, u, idx)
    assert H0
    xq, _ = R6.samples(m, "Q")
    _, xq = R6.as_file(xq)
    iq, pq, uq = R6.track(xq)
    chk = dict(D2_must_pass_e0=outcome(p, u, idx)[1] == ref, D2_must_fail_Q=outcome(pq, uq, iq)[1] == ref)
    assert chk["D2_must_pass_e0"] and not chk["D2_must_fail_Q"]
    rep["checks"] = chk
    meas = np.isfinite(u)
    D2 = {}
    for e in E_SWEEP:
        h = same = 0
        for s in range(N_SEEDS):
            q = p.copy()
            q[meas] += np.random.default_rng(s).uniform(-e, e, int(meas.sum()))
            H, got = outcome(q, u, idx)
            h += H
            same += got == ref
        D2[str(e)] = dict(seeds=N_SEEDS, H_holds=h, frames_unchanged=same)
    rep["D2"] = D2
    _, p32, u32 = R6.track(x, np.float32)
    rep["D3_max_abs_cents"] = float(np.max(np.abs(p32[meas] - p[meas])))
    OUT.write_text(json.dumps(rep, indent=1, default=R6.plain) + "\n")
    print(json.dumps(rep, indent=1, default=R6.plain))


if __name__ == "__main__":
    main()
