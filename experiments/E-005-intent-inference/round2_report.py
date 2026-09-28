"""E-005 round 2: summarise data/cache/r2_*.pkl into results/round2.json. Crude experiment code.

Intervals are 95 %: Wilson for shares.
"""

import itertools
import json
import math
import pickle

import numpy as np

import round2 as R

SPLIT = R.SPLIT


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None, None, 0]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(100 * p, 1), round(100 * (c - h), 1), round(100 * (c + h), 1), n]


def med(x):
    x = [v for v in x if v is not None and np.isfinite(v)]
    return round(float(np.median(x)), 2) if x else None


def state(sp):
    if not np.isfinite(sp["s"]):
        return "uncertain"
    return "measured" if sp["s"] <= SPLIT else "at least"


def covers(sp, truth, u):
    return abs(sp["s"] - truth) <= 2 * sp[u]


def n_covers(sp, truth):
    lo, hi = sp["N"]
    return np.isfinite(lo) and lo <= truth <= hi


# ------------------------------------------------------------ improvement tests

def lower(sp):
    return sp["s"] - 2 * sp["uB"] if np.isfinite(sp["s"]) else -np.inf


def t_B(a, b):
    """MT-008 as specified: both measured, difference beyond 2 sqrt(u1^2 + u2^2). +1 b better, -1 worse, 0 none."""
    if state(a) != "measured" or state(b) != "measured":
        return 0
    d = a["s"] - b["s"]
    return int(np.sign(d)) if abs(d) > 2 * math.hypot(a["uB"], b["uB"]) else 0


def t_D(a, b):
    if not (np.isfinite(a["s"]) and np.isfinite(b["s"])):
        return 0
    d = a["s"] - b["s"]
    return int(np.sign(d)) if abs(d) > 2 * math.hypot(a["uD"], b["uD"]) else 0


def t_N(a, b):
    la, ha = a["N"]
    lb, hb = b["N"]
    if not (np.isfinite(la) and np.isfinite(lb)):
        return 0
    if hb < la:
        return 1
    if ha < lb:
        return -1
    return 0


def t_L(a, b):
    """One-sided on honest ends only: the better take measured (its upper end honest,
    fold F2), its upper end below the other's lower end (honest everywhere, fold F3)."""
    if state(b) == "measured" and np.isfinite(a["s"]) and b["s"] + 2 * b["uB"] < lower(a):
        return 1
    if state(a) == "measured" and np.isfinite(b["s"]) and a["s"] + 2 * a["uB"] < lower(b):
        return -1
    return 0


def t_K(a, b):
    """Known melody: the linear spread, MT-008's form at every spread."""
    if not (np.isfinite(a["s"]) and np.isfinite(b["s"])):
        return 0
    d = a["s"] - b["s"]
    return int(np.sign(d)) if abs(d) > 2 * math.hypot(a["uB"], b["uB"]) else 0


TESTS = dict(B=t_B, D=t_D, N=t_N, L=t_L)

# Two-state rules: when is sigma-hat shown as measured (value +- 2 u_B), else only its lower end?
# S10: squillo MT-007 as specified (sigma-hat <= 10). U<n>: when the upper end sigma-hat + 2 u_B <= n.
RULES = ("S10", "U20", "U25", "U30", "U35")


def measured(sp, rule):
    if not np.isfinite(sp["s"]):
        return False
    if rule == "S10":
        return sp["s"] <= SPLIT
    return sp["s"] + 2 * sp["uB"] <= float(rule[1:])


def miss(sp, rule, truth):
    """The shown statement excludes the truth: measured, outside +- 2 u_B; at least, lower end above it.
    Intent uncertain shows no number and cannot miss."""
    if not np.isfinite(sp["s"]):
        return False
    if measured(sp, rule):
        return abs(sp["s"] - truth) > 2 * sp["uB"]
    return sp["s"] - 2 * sp["uB"] > truth


def t_rule(rule):
    def f(a, b):
        """MT-008's form where both are measured under the rule; else the one-sided form on
        honest ends: the better take measured, its upper end below the other's lower end."""
        ma, mb = measured(a, rule), measured(b, rule)
        if ma and mb:
            d = a["s"] - b["s"]
            return int(np.sign(d)) if abs(d) > 2 * math.hypot(a["uB"], b["uB"]) else 0
        if mb and np.isfinite(a["s"]) and b["s"] + 2 * b["uB"] < lower(a):
            return 1
        if ma and np.isfinite(b["s"]) and a["s"] + 2 * a["uB"] < lower(b):
            return -1
        return 0
    return f


for _r in RULES:
    TESTS["R" + _r] = t_rule(_r)


# ------------------------------------------------------------ synthetic

def synth_report(rows):
    out = {}
    cells = {}
    for r in rows:
        cells.setdefault((r["n_notes"], r["vib"], r["sigma"]), []).append(r)
    # S15: the contour asserted in the generator; restate the extremes computed from the output
    out["inputs"] = dict(phrases=len(rows), contour_min=round(min(r["lo"] for r in rows), 1),
                         contour_max=round(max(r["hi"] for r in rows), 1),
                         E2_C6=[R.E2_CENTS, R.C6_CENTS])
    # Q1 and Q2 per cell
    q = {}
    for (L, vib, sg), rs in sorted(cells.items()):
        c = dict(n=len(rs))
        for st in ("med", "cyc"):
            sps = [r[st] for r in rs]
            rep = [sp for sp in sps if np.isfinite(sp["s"])]
            c[st] = dict(
                states={k: sum(state(sp) == k for sp in sps) for k in ("measured", "at least", "uncertain")},
                s_median=med([sp["s"] for sp in rep]), uB_median=med([sp["uB"] for sp in rep]),
                uD_median=med([sp["uD"] for sp in rep]), settle_u_median=med([sp["us"] for sp in rep]),
                B=wilson(sum(covers(sp, sg, "uB") for sp in rep), len(rep)),
                D=wilson(sum(covers(sp, sg, "uD") for sp in rep), len(rep)),
                C=wilson(sum(covers(sp, sg, "uC") for sp in rep), len(rep)),
                realised=dict(  # against the realised truth (the sung contour's note centres), as for real voices
                    B=wilson(sum(covers(r[st], r["realised_c"], "uB") for r in rs if np.isfinite(r[st]["s"])), len(rep)),
                    C=wilson(sum(covers(r[st], r["realised_c"], "uC") for r in rs if np.isfinite(r[st]["s"])), len(rep)),
                    D=wilson(sum(covers(r[st], r["realised_c"], "uD") for r in rs if np.isfinite(r[st]["s"])), len(rep)),
                    s_minus_truth_p5_p50_p95=[round(float(q), 1) for q in np.percentile(
                        [r[st]["s"] - r["realised_c"] for r in rs if np.isfinite(r[st]["s"])], [5, 50, 95])] if rep else None),
                N=wilson(sum(n_covers(sp, sg) for sp in sps), len(sps)),
                N_upper_finite=sum(np.isfinite(sp["N"][1]) for sp in sps),
                N_width_median=med([sp["N"][1] - sp["N"][0] for sp in sps if np.isfinite(sp["N"][1])]),
                lower_B_honest=wilson(sum(sp["s"] - 2 * sp["uB"] <= sg for sp in rep), len(rep)),
                misses_low_B=sum(sp["s"] + 2 * sp["uB"] < sg for sp in rep),
                misses_high_B=sum(sp["s"] - 2 * sp["uB"] > sg for sp in rep))
        k = [r["known"] for r in rs]
        km = [r["known_med"] for r in rs]
        c["realised_c_median"] = med([r["realised_c"] for r in rs])
        c["known"] = dict(s_median=med([x["s"] for x in k]), uB_median=med([x["uB"] for x in k]),
                          uA_median=med([x["uA"] for x in k]),
                          realised=dict(
                              B=wilson(sum(abs(x["s"] - r["realised_c"]) <= 2 * x["uB"] for x, r in zip(k, rs)), len(rs)),
                              C=wilson(sum(abs(x["s"] - r["realised_c"]) <= 2 * math.hypot(x["uA"], math.sqrt(3)) for x, r in zip(k, rs)), len(rs)),
                              s_minus_truth_p5_p50_p95=[round(float(q), 1) for q in np.percentile([x["s"] - r["realised_c"] for x, r in zip(k, rs)], [5, 50, 95])]),
                          B=wilson(sum(abs(x["s"] - sg) <= 2 * x["uB"] for x in k if np.isfinite(x["s"])), sum(np.isfinite(x["s"]) for x in k)),
                          B_realised=wilson(sum(abs(x["s"] - r["realised"]) <= 2 * x["uB"] for x, r in zip(k, rs) if np.isfinite(x["s"])), sum(np.isfinite(x["s"]) for x in k)),
                          C=wilson(sum(abs(x["s"] - sg) <= 2 * math.hypot(x["uA"], math.sqrt(3)) for x in k if np.isfinite(x["s"])), sum(np.isfinite(x["s"]) for x in k)),
                          B_median_settle=wilson(sum(abs(x["s"] - sg) <= 2 * x["uB"] for x in km if np.isfinite(x["s"])), sum(np.isfinite(x["s"]) for x in km)),
                          wrong_notes=sum(x["wrong"] for x in k), states=med([x["states"] for x in k]),
                          found_all=sum(x["found"] == x["states"] for x in k),
                          misses_low=sum(x["s"] + 2 * x["uB"] < sg for x in k), misses_high=sum(x["s"] - 2 * x["uB"] > sg for x in k))
        q[f"L={L},vib={vib},sigma={sg}"] = c
    out["cells"] = q
    # Q2 by the reported value, pooled over lengths, sigma-hat > SPLIT
    bins = {}
    for st in ("med", "cyc"):
        for vib in (0, 1):
            for lo, hi in ((0, 10), (10, 15), (15, 20), (20, 25), (25, 30), (30, 1e9)):
                for L in R.LENGTHS:
                    b = [r for r in rows if r["vib"] == vib and r["n_notes"] == L and lo <= r[st]["s"] < hi]
                    bins[f"{st} vib={vib} L={L} s in [{lo},{hi})"] = dict(
                        B=wilson(sum(covers(r[st], r["sigma"], "uB") for r in b), len(b)),
                        D=wilson(sum(covers(r[st], r["sigma"], "uD") for r in b), len(b)),
                        N=wilson(sum(n_covers(r[st], r["sigma"]) for r in b), len(b)))
    out["by_reported"] = bins
    # N overall, by length
    out["N_overall"] = {f"{st} L={L}": wilson(sum(n_covers(r[st], r["sigma"]) for r in rows if r["n_notes"] == L),
                                             sum(r["n_notes"] == L for r in rows))
                        for st in ("med", "cyc") for L in R.LENGTHS}
    out["D_above_split"] = {f"{st} L={L} vib={vib}": wilson(
        sum(covers(r[st], r["sigma"], "uD") for r in rows if r["n_notes"] == L and r["vib"] == vib and np.isfinite(r[st]["s"]) and r[st]["s"] > SPLIT),
        sum(1 for r in rows if r["n_notes"] == L and r["vib"] == vib and np.isfinite(r[st]["s"]) and r[st]["s"] > SPLIT))
        for st in ("med", "cyc") for L in R.LENGTHS for vib in (0, 1)}
    out["B_measured"] = {f"{st} vib={vib}": wilson(
        sum(covers(r[st], r["sigma"], "uB") for r in rows if r["vib"] == vib and state(r[st]) == "measured"),
        sum(1 for r in rows if r["vib"] == vib and state(r[st]) == "measured")) for st in ("med", "cyc") for vib in (0, 1)}
    # the two-state rules, per true sigma (no prior over singers needed)
    rules = {}
    for st in ("med", "cyc"):
        for L, vib in itertools.product(R.LENGTHS, (0, 1)):
            for rule in RULES:
                per = {}
                for sg in R.SIGMAS:
                    sps = [r[st] for r in cells[(L, vib, sg)]]
                    per[sg] = dict(miss=wilson(sum(miss(sp, rule, sg) for sp in sps), len(sps)),
                                   miss_realised=wilson(sum(miss(r[st], rule, r["realised_c"]) for r in cells[(L, vib, sg)]), len(sps)),
                                   measured=sum(measured(sp, rule) for sp in sps),
                                   uncertain=sum(not np.isfinite(sp["s"]) for sp in sps))
                worst = max(per.values(), key=lambda v: v["miss"][0])
                worst_r = max(per.values(), key=lambda v: v["miss_realised"][0])
                rules[f"{st} L={L} vib={vib} {rule}"] = dict(
                    worst_miss=worst["miss"], worst_miss_realised=worst_r["miss_realised"],
                    measured=sum(v["measured"] for v in per.values()), by_sigma={str(k): v for k, v in per.items()})
    out["rules"] = rules
    # the rules pooled over the design's sigma grid (the fold's F2 view, by what is shown)
    pooled = {}
    for st in ("med", "cyc"):
        for vib in (0, 1):
            for rule in RULES:
                m = [r for r in rows if r["vib"] == vib and measured(r[st], rule)]
                ab = [r for r in m if r[st]["s"] > SPLIT]
                pooled[f"{st} vib={vib} {rule}"] = dict(
                    measured_cover_sigma=wilson(sum(covers(r[st], r["sigma"], "uB") for r in m), len(m)),
                    measured_cover_realised=wilson(sum(covers(r[st], r["realised_c"], "uB") for r in m), len(m)),
                    above_split_cover_realised=wilson(sum(covers(r[st], r["realised_c"], "uB") for r in ab), len(ab)),
                    max_measured_s=round(max(r[st]["s"] for r in m), 1) if m else None)
    out["rules_pooled"] = pooled
    rep = [r for r in rows if np.isfinite(r["cyc"]["s"])]
    out["lower_end_honest_cyc"] = dict(
        sigma=wilson(sum(r["cyc"]["s"] - 2 * r["cyc"]["uB"] <= r["sigma"] for r in rep), len(rep)),
        realised=wilson(sum(r["cyc"]["s"] - 2 * r["cyc"]["uB"] <= r["realised_c"] for r in rep), len(rep)),
        uncertain=len(rows) - len(rep))
    # Q3: null pairs (disjoint, same cell) and power pairs (same length, vib; index k of each cell)
    q3 = {}
    for st in ("med", "cyc"):
        for L, vib in itertools.product(R.LENGTHS, (0, 1)):
            nulls = {k: [0, 0] for k in list(TESTS) + ["K"]}
            for sg in R.SIGMAS:
                rs = cells[(L, vib, sg)]
                for i in range(0, len(rs) - 1, 2):
                    a, b = rs[i], rs[i + 1]
                    for name, fn in TESTS.items():
                        nulls[name][0] += fn(a[st], b[st]) != 0
                        nulls[name][1] += 1
                    nulls["K"][0] += t_K(a["known"], b["known"]) != 0
                    nulls["K"][1] += 1
            power = {}
            for s1, s2 in ((10, 0), (20, 10), (20, 0), (25, 15), (30, 20), (30, 10), (40, 20), (40, 10)):
                A, B = cells[(L, vib, s1)], cells[(L, vib, s2)]
                pw = {}
                for name, fn in TESTS.items():
                    res = [fn(a[st], b[st]) for a, b in zip(A, B)]
                    pw[name] = dict(improved=wilson(sum(x == 1 for x in res), len(res)), worse=sum(x == -1 for x in res))
                res = [t_K(a["known"], b["known"]) for a, b in zip(A, B)]
                pw["K"] = dict(improved=wilson(sum(x == 1 for x in res), len(res)), worse=sum(x == -1 for x in res))
                power[f"{s1}->{s2}"] = pw
            q3[f"{st} L={L} vib={vib}"] = dict(false_change={k: wilson(*v) for k, v in nulls.items()}, power=power)
    out["improvement"] = q3
    # Q5 per-note +-: rightly attributed notes, |dev - truth| <= 2 hypot(u_settle, u_ref)
    q5 = {}
    for st in ("med", "cyc"):
        for vib in (0, 1):
            for sg in R.SIGMAS:
                k_c = k_1 = n = 0
                for r in rows:
                    if r["vib"] != vib or r["sigma"] != sg:
                        continue
                    arr = r[st + "_notes"]
                    u_rc, u_r1 = r[st + "_uref"]
                    ok = (arr[:, 0] == 1) & (arr[:, 1] == 1)
                    dev, tru, us = arr[ok, 2], arr[ok, 3], arr[ok, 4]
                    # the deviation is on the circular reference, the truth on the weighted mean of e: they
                    # differ by the reference's error (which u_ref must cover) and by whole semitones of
                    # transposition (the modal offset), removed by wrapping, never by subtracting a take's offset
                    if len(dev) < 2:
                        continue
                    diff = (dev - tru + 50.0) % 100.0 - 50.0
                    k_c += int(np.sum(np.abs(diff) <= 2 * np.hypot(us, u_rc)))
                    k_1 += int(np.sum(np.abs(diff) <= 2 * np.hypot(us, u_r1)))
                    n += len(dev)
                q5[f"{st} vib={vib} sigma={sg}"] = dict(circ=wilson(k_c, n), round1=wilson(k_1, n))
    out["per_note_pm"] = q5
    return out


# ------------------------------------------------------------ real

def real_report(real):
    out = {}
    rs = real["resynth"]
    res = {}
    for st in ("med", "cyc"):
        for S in ("SC-straight", "VIB-row"):
            b = [r for r in rs if r["set"] == S]
            tr = [r["truth"]["sd"] for r in b]
            sps = [r[st] for r in b]
            rep = [(sp, t) for sp, t in zip(sps, tr) if np.isfinite(sp["s"])]
            res[f"{st} {S}"] = dict(
                takes=len(b), truth_sd_median=med(tr),
                truth_definition_diff_median=med([abs(r["truth"]["sd"] - r["truth"]["sd_median_centre"]) for r in b]),
                truth_definition_diff_max=round(max(abs(r["truth"]["sd"] - r["truth"]["sd_median_centre"]) for r in b), 2),
                truth_max_abs_dev_median=med([r["truth"]["max_abs"] for r in b]),
                truth_notes_beyond_50=None,
                states={k: sum(state(sp) == k for sp in sps) for k in ("measured", "at least", "uncertain")},
                s_median=med([sp["s"] for sp, _ in rep]), s_minus_truth_median=med([sp["s"] - t for sp, t in rep]),
                B=wilson(sum(covers(sp, t, "uB") for sp, t in rep), len(rep)),
                D=wilson(sum(covers(sp, t, "uD") for sp, t in rep), len(rep)),
                C=wilson(sum(covers(sp, t, "uC") for sp, t in rep), len(rep)),
                A=wilson(sum(covers(sp, t, "uA") for sp, t in rep), len(rep)),
                s_minus_truth_p5_p50_p95=[round(float(q), 1) for q in np.percentile([sp["s"] - t for sp, t in rep], [5, 50, 95])] if rep else None,
                N=wilson(sum(n_covers(sp, t) for sp, t in zip(sps, tr)), len(sps)),
                N_upper_finite=sum(np.isfinite(sp["N"][1]) for sp in sps),
                lower_B_honest=wilson(sum(sp["s"] - 2 * sp["uB"] <= t for sp, t in rep), len(rep)),
                lower_N_honest=wilson(sum(sp["N"][0] <= t for sp, t in zip(sps, tr) if np.isfinite(sp["N"][0])),
                                      sum(np.isfinite(sp["N"][0]) for sp in sps)))
        for S in ("SC-straight", "VIB-row"):
            b = [r for r in rs if r["set"] == S]
            res[f"{st} {S}"]["uB_median"] = med([r[st]["uB"] for r in b])
            res[f"{st} {S}"]["settle_u_rms_median"] = med([r[st]["us"] for r in b])
            res[f"{st} {S}"]["rules"] = {rule: dict(
                miss=wilson(sum(miss(r[st], rule, r["truth"]["sd"]) for r in b), len(b)),
                miss_other_truth=wilson(sum(miss(r[st], rule, r["truth"]["sd_median_centre"]) for r in b), len(b)),
                measured=sum(measured(r[st], rule) for r in b)) for rule in RULES}
        for S in ("SC-straight", "VIB-row"):
            b = [r for r in rs if r["set"] == S and np.isfinite(r[st]["s"])]
            z = [abs(r[st]["s"] - r["truth"]["sd"]) / r[st]["uB"] for r in b]
            # how conservative u_B is on real voices: |sigma-hat - truth| / u_B (coverage at k = 2 needs <= 2)
            res[f"{st} {S}"]["abs_err_over_uB_p50_p95_max"] = [round(float(q), 2) for q in np.percentile(z, [50, 95, 100])]
            res[f"{st} {S}"]["settle_share_of_uB2_median"] = med([r[st]["us"] ** 2 / r[st]["uB"] ** 2 for r in b])
        for S in ("SC-straight", "VIB-row"):
            b = [r for r in rs if r["set"] == S]
            k = [(r["known"], r["truth"]["sd"]) for r in b]
            res[f"known {S}"] = dict(
                s_median=med([x["s"] for x, _ in k]), s_minus_truth_median=med([x["s"] - t for x, t in k]),
                s_minus_truth_p5_p50_p95=[round(float(q), 1) for q in np.percentile([x["s"] - t for x, t in k], [5, 50, 95])],
                A=wilson(sum(abs(x["s"] - t) <= 2 * x["uA"] for x, t in k if np.isfinite(x["s"])), sum(np.isfinite(x["s"]) for x, _ in k)),
                C=wilson(sum(abs(x["s"] - t) <= 2 * math.hypot(x["uA"], math.sqrt(3)) for x, t in k if np.isfinite(x["s"])), sum(np.isfinite(x["s"]) for x, _ in k)),
                uB_median=med([x["uB"] for x, _ in k]),
                B=wilson(sum(abs(x["s"] - t) <= 2 * x["uB"] for x, t in k if np.isfinite(x["s"])), sum(np.isfinite(x["s"]) for x, _ in k)),
                abs_err_over_uB_p50_p95_max=[round(float(q), 2) for q in np.percentile(
                    [abs(x["s"] - t) / x["uB"] for x, t in k if np.isfinite(x["s"])], [50, 95, 100])],
                wrong_notes=sum(x["wrong"] for x, _ in k), found_all=sum(x["found"] == x["states"] for x, _ in k))
    out["resynth"] = res
    # originals: states, halves (false change), flag
    og = real["originals"]
    o = {}
    for st in ("med", "cyc"):
        for kind, style in itertools.product(("scales", "row"), ("straight", "vibrato")):
            b = [r for r in og if r["kind"] == kind and r["style"] == style]
            o[f"{st} {kind} {style}"] = dict(
                takes=len(b), states={k: sum(state(r[st]["sp"]) == k for r in b) for k in ("measured", "at least", "uncertain")},
                s_median=med([r[st]["sp"]["s"] for r in b]),
                N_lower_median=med([r[st]["sp"]["N"][0] for r in b]),
                N_upper_finite=sum(np.isfinite(r[st]["sp"]["N"][1]) for r in b),
                known_s_median=med([r["known"]["s"] for r in b]), known_uB_median=med([r["known"]["uB"] for r in b]),
                uB_median=med([r[st]["sp"]["uB"] for r in b]),
                measured_under={rule: sum(measured(r[st]["sp"], rule) for r in b) for rule in RULES})
        fc = {}
        for name, fn in TESTS.items():
            v = [fn(*r[st]["halves"]) for r in og if None not in r[st]["halves"]]
            fc[name] = wilson(sum(x != 0 for x in v), len(v))
        o[f"{st} halves false change"] = fc
    out["originals"] = o
    out["flag"] = flag_fit(og)
    return out


def flag_fit(og):
    """Q5 flag: posterior with a uniform outlier share pi; pi by maximum likelihood of
    right / wrong attribution on one half of the singers, checked on the other."""
    singers = sorted({r["singer"] for r in og}, key=lambda s: (s[0], int(s[1:])))
    halves = (singers[0::2], singers[1::2])

    def notes(sset, st="cyc"):
        out = []
        for r in og:
            if r["singer"] not in sset:
                continue
            x = r[st]
            s = x["s_take"]
            ok = x["found"] & ~np.isnan(x["dev"])
            for d, right in zip(x["dev"][ok], x["right"][ok]):
                out.append((d, s, bool(right), r["style"]))
        return out

    grid = np.round(np.arange(0.0, 0.301, 0.005), 3)
    res = {}
    for fit_i, test_i in ((0, 1), (1, 0)):
        tr, te = notes(halves[fit_i]), notes(halves[test_i])

        def post(ns, pi):
            return np.array([R.p_attrib_mix(np.array([d]), s, pi)[0] for d, s, _, _ in ns])

        ll = []
        y = np.array([rt for _, _, rt, _ in tr])
        for pi in grid:
            p = np.clip(post(tr, pi), 1e-9, 1 - 1e-9)
            ll.append(float(np.sum(np.where(y, np.log(p), np.log(1 - p)))))
        pi_hat = float(grid[int(np.argmax(ll))])
        yt = np.array([rt for _, _, rt, _ in te])
        cell = dict(fit_singers=halves[fit_i], pi_hat=pi_hat, test_notes=len(te), test_wrong=int((~yt).sum()))
        for name, pi in (("round1", 0.0), ("mixture", pi_hat)):
            p = post(te, pi)
            unf = p >= 0.95
            cell[name] = dict(flagged=wilson(int((~unf).sum()), len(p)),
                              wrong_among_unflagged=wilson(int((~yt[unf]).sum()), int(unf.sum())),
                              predicted_wrong_among_unflagged=round(100 * float(np.mean(1 - p[unf])), 2) if unf.any() else None,
                              by_style={sty: wilson(int(sum((not rt) and u for (_, _, rt, s2), u in zip(te, unf) if s2 == sty)),
                                                    int(sum(u for (_, _, _, s2), u in zip(te, unf) if s2 == sty)))
                                        for sty in ("straight", "vibrato")})
        res[f"fit on half {fit_i}, test on half {test_i}"] = cell
    return res


def add_uC(sp):
    """The fold's candidate C: sampling (GUM E.4.3) (+) sqrt(3) cents, the pitch floor of
    squillo MT-003 (SG-005's +-3 cents as a rectangular bound, GUM 4.3.7), no settle term."""
    sp["uC"] = float(math.hypot(sp["uA"], math.sqrt(3))) if np.isfinite(sp.get("uA", np.nan)) else np.nan


def main():
    out = {}
    syn = pickle.load(open(R.CACHE / "r2_synth.pkl", "rb"))
    for r in syn:
        add_uC(r["med"])
        add_uC(r["cyc"])
    out["synthetic"] = synth_report(syn)
    p = R.CACHE / "r2_real.pkl"
    if p.exists():
        real = pickle.load(open(p, "rb"))
        for r in real["resynth"]:
            add_uC(r["med"])
            add_uC(r["cyc"])
        for r in real["originals"]:
            add_uC(r["med"]["sp"])
            add_uC(r["cyc"]["sp"])
        out["real"] = real_report(real)
    json.dump(out, open(R.OUT / "round2.json", "w"), indent=1, default=float)
    print("written", R.OUT / "round2.json")


if __name__ == "__main__":
    main()
