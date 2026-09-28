"""E-002 fold 3 (squillo iteration 42): the steadying ladder `coach` would ask of
`synthesis`, on round 2's takes and on squillo's fixtures. Crude experiment
code. Needs data/cache/r2_frames.npz (r2_run.py) and results/fold2.json.

    uv run python fold3_ladder.py <squillo>      # writes results/fold3_ladder.json

The question (squillo Q-023): if the next step is the least steadying of a
take that `metrics` MT-008 would call improved, and the far vision the most
steadying `synthesis` SY-002 allows, how often is a step offered on real
takes, and how often would a stricter rule, "never steadier than the take's
own steadiest block", still offer one?

Rules, written before the run (S15: a rule written before a run is a check):

1. A take's measures are fold 2's spec rules (squillo metrics MT-003,
   MT-009, MT-010): the per-frame u from the spec table, c and kappa read
   from results/fold2.json `measures.spec` (never retyped), the held notes
   and blocks by fold2.held_notes and fold2.blocks.
2. The full steadying change: for each held note, its 2 Hz contour lp
   (fold2's B2, forward and backward, on the note's refilled contour, as
   r2_analyse.block_measures computes it) and m the mean of lp over the
   note; each accepted frame of the note gets m - lp; every other frame 0.
3. F = the largest |change|; alpha_max = min(1, 50 / F), so no change
   exceeds squillo synthesis SY-002's 50 cents.
4. Strength k of 64: the change times k * alpha_max / 64. The rung's pitch
   is the take's measured pitch plus it, with the take's u (squillo
   synthesis SY-004), measured by rule 1.
5. MT-008: improved when S - S' > 2 hypot(u, u'), both measured.
6. Next step (rule A): the least k improved. Far vision A: the greatest
   k improved (k = 64 wherever the outcome is monotone in k).
   Rule B: as A, offered only when S' at the next step is not below the
   take's steadiest block (the least block S).
7. Reported on the original takes (real voices) and on the clean
   re-syntheses; a take enters when its steadiness is measured.

Checks of the checks (S15), each asserted:
- k = 0 reproduces the take's own S and u exactly (the rung machinery adds
  nothing).
- MT-008 on held-wobble.wav then held-steady.wav is improved (must pass, as
  squillo analyzers AN-006's scenario), and held-wobble.wav against itself
  is not (must fail).
- On held-wobble.wav the full steadying is improved (must pass) and
  strength 0 is not (must fail).
"""
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.signal import filtfilt

import fold2 as F2
import r2_analyse as A

SQ = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("../../../squillo")
SPEC = json.loads((A.T.OUT / "fold2.json").read_text())["measures"]["spec"]
TABLE = np.array([np.inf if x is None else x for x in SPEC["table"]])
C, KAPPA = SPEC["c"], SPEC["kappa"]
F2.SPEC_TABLE = TABLE
K = 64
LIMIT = 50.0  # squillo synthesis SY-002


def measure(p, u):
    """Rule 1: held notes, blocks, the take's steadiness (value, u, n) or None."""
    notes = F2.held_notes(p, u)
    bl = []
    for fr, con, acc in notes:
        bl += F2.blocks(con, u[fr], acc, C, True)
    return notes, bl, F2.take(bl, "S", KAPPA["S"])


def full_change(p, notes):
    """Rule 2."""
    ch = np.zeros(len(p))
    for fr, con, acc in notes:
        lp = filtfilt(*A.B2, con)
        ch[fr[acc]] = lp.mean() - lp[acc]
    return ch


def improved(t1, t2):
    return t1 is not None and t2 is not None and t1[0] - t2[0] > 2 * np.hypot(t1[1], t2[1])


def ladder(p, u):
    notes, bl, tk = measure(p, u)
    if tk is None:
        return dict(measured=False, blocks=len(bl))
    ch = full_change(p, notes)
    Fm = float(np.max(np.abs(ch)))
    amax = min(1.0, LIMIT / Fm) if Fm > 0 else 1.0
    same = measure(p + 0 * ch, u)[2]
    assert same == tk, (same, tk)  # check: strength 0 reproduces the take
    rungs = []
    for k in range(1, K + 1):
        r = measure(p + ch * (k * amax / K), u)[2]
        rungs.append(r)
    imp = [improved(tk, r) for r in rungs]
    nk = next((k for k in range(1, K + 1) if imp[k - 1]), None)
    fk = next((k for k in range(K, 0, -1) if imp[k - 1]), None)  # the far vision: the strongest improved
    smin = min(b["S"] for b in bl)
    monotone = all(imp[i] <= imp[i + 1] for i in range(K - 1))
    out = dict(measured=True, blocks=len(bl), S=tk[0], u=tk[1], S_min_block=smin, F=Fm, alpha_max=amax,
               next_k=nk, far_k=fk, full_S=None if rungs[-1] is None else rungs[-1][0],
               full_u=None if rungs[-1] is None else rungs[-1][1], full_improved=imp[-1], monotone=monotone)
    if nk is not None:
        out["next_S"], out["next_u"] = rungs[nk - 1][0], rungs[nk - 1][1]
        out["next_strength"] = nk * amax / K
        out["B"] = rungs[nk - 1][0] >= smin
        out["far_S"], out["far_u"] = rungs[fk - 1][0], rungs[fk - 1][1]
        out["next_max_change"] = float(np.max(np.abs(ch * nk * amax / K)))
    return out


def take_rows(cond):
    rows = []
    U = A.u_of(A.Z[cond + "/dip"], TABLE)
    for k in range(A.NF):
        m = A.Z[cond + "/file"] == k
        idx = A.Z[cond + "/idx"][m]
        assert np.all(np.diff(idx) == 1)
        f = A.Z[cond + "/f"][m]
        p = F2.cents(f)
        u = np.where(np.isnan(f), np.inf, U[m])
        r = ladder(p, u)
        r.update(file=k, set=str(A.SET[k]), singer=A.SINGER[k])
        rows.append(r)
    return rows


def summary(rows):
    ms = [r for r in rows if r["measured"]]
    nx = [r for r in ms if r["next_k"] is not None]
    b = [r for r in nx if r["B"]]
    fx = [r for r in ms if r["full_improved"]]
    return dict(takes=len(rows), measured=len(ms), step_A=len(nx), step_B=len(b), full_improved=len(fx),
                far_at_full=sum(r["far_k"] == K for r in nx), capped=sum(r["alpha_max"] < 1 for r in ms), monotone=sum(r["monotone"] for r in ms),
                next_strength=[round(r["next_strength"], 4) for r in nx],
                next_max_change=[round(r["next_max_change"], 2) for r in nx],
                S=[round(r["S"], 2) for r in ms], u=[round(r["u"], 2) for r in ms],
                blocks=[r["blocks"] for r in ms],
                full_S=[None if r["full_S"] is None else round(r["full_S"], 2) for r in ms],
                sets_measured=sorted(set(r["set"] for r in ms)), sets_step_A=sorted(set(r["set"] for r in nx)))


def wav_samples(path):
    raw = path.read_bytes()
    k = raw.index(b"data") + 8
    return raw, np.frombuffer(raw[k:], "<f4").astype(np.float64)


def fixture_row(x):
    idx, f, dip = F2.yin.yin(x)
    f = F2.yin.in_range(f, 3.0)
    u = np.where(np.isnan(f), np.inf, A.u_of(np.nan_to_num(dip, nan=1.0), TABLE))
    return F2.cents(f), u


def main():
    R = {"rules": "see the docstring", "spec": dict(table=SPEC["table"], c=C, kappa=KAPPA), "K": K, "limit": LIMIT}
    manifest = (SQ / "fixtures/MANIFEST.md").read_text()
    fx = {}
    P = {}
    for name in ("metrics/held-wobble.wav", "metrics/held-steady.wav", "metrics/held-vibrato.wav",
                 "signal/sine-220hz.wav", "synthesis/voice-220hz-wobble.wav"):
        raw, x = wav_samples(SQ / "fixtures" / name)
        h = hashlib.sha256(raw).hexdigest()
        assert h in manifest, name  # the file squillo lists, byte for byte
        p, u = fixture_row(x)
        P[name] = (p, u)
        fx[name] = dict(sha256=h, **ladder(p, u))
    R["fixtures"] = fx
    # checks of the checks
    pw, uw = P["metrics/held-wobble.wav"]
    ps, us = P["metrics/held-steady.wav"]
    tw, ts = measure(pw, uw)[2], measure(ps, us)[2]
    chk = {"MT-008 wobble -> steady improved (must pass)": improved(tw, ts),
           "MT-008 wobble -> wobble improved (must fail)": improved(tw, tw),
           "full steadying of held-wobble improved (must pass)": fx["metrics/held-wobble.wav"]["full_improved"],
           "strength 0 of held-wobble improved (must fail)": improved(tw, measure(pw, uw)[2])}
    assert chk["MT-008 wobble -> steady improved (must pass)"] and not chk["MT-008 wobble -> wobble improved (must fail)"]
    assert chk["full steadying of held-wobble improved (must pass)"] and not chk["strength 0 of held-wobble improved (must fail)"]
    R["checks"] = chk
    for k, v in fx.items():
        print(k, {a: b for a, b in v.items() if a != "sha256"})
    for cond in ("original", "clean"):
        t0 = time.time()
        rows = take_rows(cond)
        R[cond] = dict(summary=summary(rows), rows=rows, seconds=round(time.time() - t0, 1))
        s = R[cond]["summary"]
        print(cond, {a: b for a, b in s.items() if not isinstance(b, list)}, R[cond]["seconds"], "s")
        print("  next strength", s["next_strength"])
        print("  next max change", s["next_max_change"])
    (A.T.OUT / "fold3_ladder.json").write_text(json.dumps(R, indent=1, default=lambda o: None if isinstance(o, float) and not np.isfinite(o) else (bool(o) if isinstance(o, np.bool_) else str(o))))


if __name__ == "__main__":
    main()
