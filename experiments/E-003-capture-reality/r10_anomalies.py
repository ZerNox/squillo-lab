"""E-003 round 2, re-checked in squillo's review R-10 (iteration 50): were the captures rule 3a
left out timing faults, or a steady tone's period ambiguity? Crude experiment code.

Rule, written and committed before this script runs on any capture:

  R1. For each capture rule 3a left out, take its usable windows' shifts from the whole lag
      (`r2_measures.align`) and, for each anomalous window, the input's pitch period P there: 48 000
      over the median of the known f0 (the `.truth.npy`) over the window's samples where it is voiced.
  R2. The capture's anomaly is *period ambiguity*, not a timing fault, when both hold:
      (a) every anomalous window's |shift| lies within 5 % of P or of 2P;
      (b) the shifted windows form one stretch with usable windows on both sides, and every usable
          window outside it sits within 64 samples of the whole lag (rule 3a's own bound). An inserted
          or lost block shifts every later window, so a stretch that returns to the whole lag is not one.
      Otherwise the capture stays out, as rule 3a had it.
  R3. A capture called period ambiguity is measured as rule 3a measures a capture with no anomaly
      (aligned at the whole lag), and round 2's report is re-run with it in, into results/r10/;
      results/r2/ is not touched.

Checks of the checks, run first and asserted:
  C1 (must pass): the report re-run from round 2's own cache reproduces results/r2/analysis.json's
      vs_raw and groups frames w and w_ci95 exactly.
  C2 (must fail, different input): the rule-7 check's 480-sample insertion into f1_long_straight_a
      at 5 s is not called period ambiguity.
  C3 (must pass / must fail on the classifier): a window shifted by round(P) between unshifted windows
      is period ambiguity; the same shifted by round(1.5 P), or by round(P) on every window to the
      end, is not.

    uv run --project ../E-002-measurement-reliability python r10_anomalies.py
    uv run --project ../E-002-measurement-reliability python r10_anomalies.py posthoc   # added after the run, labelled
"""
import json
import pickle
import shutil
import sys
from pathlib import Path

import numpy as np

import r2_measures as X

HERE = Path(__file__).parent
POSHOC_DOC = "post hoc (R-10): R2 (a) alone, every shifted window within 5 % of P, 2P or 3P; (b) dropped"
POSTHOC = sys.argv[1:] == ["posthoc"]
OUT = HERE / ("results/r10/posthoc" if POSTHOC else "results/r10")
TMP = HERE / "data/cache/r10"


def period_at(stem, w0):
    ft = np.load(X.IN / f"{stem}.truth.npy").astype(np.float64)
    seg = ft[w0:w0 + X.WIN]
    seg = seg[seg > 0]
    return float(X.SR / np.median(seg)) if len(seg) else float("nan")


def classify(windows, periods, whole_tol=X.SHIFT):
    """windows: usable windows in order, each dict(w0, shift); periods: {w0: P} for the anomalous ones.
    Returns (is_period_ambiguity, detail)."""
    shifted = [i for i, w in enumerate(windows) if abs(w["shift"]) >= X.SHIFT]
    if not shifted:
        return False, "no shifted window"
    lo, hi = shifted[0], shifted[-1]
    one_stretch = shifted == list(range(lo, hi + 1))
    both_sides = lo > 0 and hi < len(windows) - 1
    rest_whole = all(abs(w["shift"]) < whole_tol for i, w in enumerate(windows) if i < lo or i > hi)
    ratios = []
    per = True
    for i in shifted:
        P = periods.get(windows[i]["w0"], float("nan"))
        r = abs(windows[i]["shift"]) / P
        ratios.append(round(r, 3))
        per &= bool(abs(r - 1) <= 0.05 or abs(r - 2) <= 0.10)  # within 5 % of P or of 2P
    ok = bool(per and one_stretch and both_sides and rest_whole)
    return ok, dict(ratios=ratios, one_stretch=one_stretch, both_sides=both_sides, rest_whole=rest_whole)


def usable_windows(stem, cond, req):
    x, _ = X.read_input(stem, cond)
    cap = np.fromfile(X.CAP / f"{stem}.{cond}.{req}.f32", "<f4").astype(np.float64)
    _, L, anom, win = X.align(cap, x)
    return [w for w in win if w["usable"]], anom


def checks():
    R = {}
    # C2: the insertion from rule 7
    stem = "f1_long_straight_a"
    x, _ = X.read_input(stem, "clean")
    ins = np.concatenate([x[:5 * X.SR], np.zeros(480), x[5 * X.SR:]])
    _, _, anom, win = X.align(ins, x)
    use = [w for w in win if w["usable"]]
    per = {w["w0"]: period_at(stem, w["w0"]) for w in use}
    ok, d = classify(use, per)
    R["C2_insertion_not_period"] = dict(anomalies=len(anom), classified_period=ok, detail=d, must=bool(anom) and not ok)
    # C3: the classifier on constructed windows, P from the same input
    base = [dict(w0=i * X.WIN, shift=0) for i in range(10)]
    P = period_at(stem, 4 * X.WIN)
    per = {w["w0"]: P for w in base}

    def with_shift(idx, s):
        return [dict(w, shift=s) if i in idx else w for i, w in enumerate(base)]
    a, _ = classify(with_shift({4, 5}, round(P)), per)
    b, _ = classify(with_shift({4, 5}, round(1.5 * P)), per)
    c, _ = classify(with_shift(set(range(4, 10)), round(P)), per)
    R["C3_classifier"] = dict(P=P, one_period=a, one_and_half=b, to_the_end=c, must=a and not b and not c)
    return R


def main():
    R = dict(checks=checks(), posthoc=POSHOC_DOC if POSTHOC else None)
    assert all(v["must"] for v in R["checks"].values()), R["checks"]
    import r2_report
    cache = X.CAP.parent / "measures.pkl"
    D, Cp = pickle.loads(cache.read_bytes())
    TMP.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    link = TMP / "cap"
    if not link.exists():
        link.symlink_to(X.CAP.resolve())
    shutil.copy(X.OUT / "inputs.json", OUT / "inputs.json")
    orig_out, orig_cap = X.OUT, X.CAP
    X.OUT, X.CAP = OUT, link

    def report(cp, name):
        (TMP / "measures.pkl").write_bytes(pickle.dumps((D, cp)))
        r2_report.main()
        res = json.loads((OUT / "analysis.json").read_text())
        (OUT / "analysis.json").rename(OUT / name)
        return res

    # C1: the pipeline reproduces round 2 from its own cache
    orig = json.loads((orig_out / "analysis.json").read_text())
    again = report(Cp, "analysis_reproduced.json")
    same = all(again[s][k]["frames"]["w"] == orig[s][k]["frames"]["w"]
               and again[s][k]["frames"]["w_ci95"] == orig[s][k]["frames"]["w_ci95"]
               for s in ("groups", "vs_raw") for k in orig[s])
    R["checks"]["C1_reproduces_round2"] = dict(must=same)
    assert same, "C1"
    (OUT / "analysis_reproduced.json").unlink()

    # R1, R2 on every capture rule 3a left out
    left = [k for k, v in Cp.items() if v[0] is None]
    rows, keep = [], []
    for key in sorted(left):
        stem, cond, req = key
        use, anom = usable_windows(stem, cond, req)
        per = {a["input_sample"]: period_at(stem, a["input_sample"]) for a in anom}
        per.update({w["w0"]: period_at(stem, w["w0"]) for w in use if abs(w["shift"]) >= X.SHIFT})
        ok, d = classify(use, per)
        if POSTHOC:  # post hoc, labelled: (a) alone, whole multiples 1 to 3 of P within 5 %
            ok = all(min(abs(r - m) / m for m in (1, 2, 3)) <= 0.05 for r in d["ratios"])
        rows.append(dict(capture=".".join(key), shifts=[(w["w0"] / X.SR, w["shift"]) for w in use],
                         periods={str(k / X.SR): round(v, 1) for k, v in per.items()}, period_ambiguity=ok, detail=d))
        if ok:
            keep.append(key)
    R["left_out"] = rows

    # R3: measure the kept ones at the whole lag, as rule 3a measures a capture with no anomaly
    real_align = X.align

    def align_no_anom(cap, ref):
        a, L, _, win = real_align(cap, ref)
        return a, L, [], win
    X.align = align_no_anom
    Cp2 = dict(Cp)
    for key in keep:
        k, fs, tm, info = X.captured(key)
        Cp2[k] = (fs, tm, info)
    X.align = real_align
    new = report(Cp2, "analysis.json")
    X.OUT, X.CAP = orig_out, orig_cap
    cmp = {}
    for s in ("vs_raw", "groups"):
        for k in orig[s]:
            o, n = orig[s][k], new[s][k]
            of, nf = o["frames"], n["frames"]
            cmp[f"{s} {k}"] = dict(
                inputs=(o.get("inputs", o.get("captures")), n.get("inputs", n.get("captures"))),
                w=(of["w"], nf["w"]), w_ci95=(of["w_ci95"], nf["w_ci95"]),
                takes_moved={m: ((o["takes"][m]["moved"], o["takes"][m]["both"]), (n["takes"][m]["moved"], n["takes"][m]["both"]))
                             for m in X.KEYS.values()})
    R["round2_vs_with_kept"] = cmp
    (OUT / "r10_anomalies.json").write_text(json.dumps(R, indent=1, default=float))
    for r in rows:
        print(r["capture"], "period ambiguity" if r["period_ambiguity"] else "stays out", r["detail"], r["shifts"])
    for k, v in cmp.items():
        print(k, v["inputs"], "w", v["w"], v["w_ci95"])


if __name__ == "__main__":
    main()
