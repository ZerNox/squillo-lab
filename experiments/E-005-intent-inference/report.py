"""Summarise E-005 round 1 into results/summary.json and results/summary.md.

Crude experiment code. Intervals are 95 %: Wilson for shares; bootstrap over
phrases (synthetic) or takes (VocalSet) for medians and p95s.
"""

import json
import pickle
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

import infer

HERE = Path(__file__).parent
CACHE = HERE / "data" / "cache"
OUT = HERE / "results"
TRANS_S = 0.1  # segments shorter than this are transitions, not notes
rng = np.random.default_rng(1)


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(100 * p, 2), round(100 * (c - h), 2), round(100 * (c + h), 2)]


def boot(groups, stat, n=400):
    """groups: list of arrays (one per phrase); stat over their concatenation."""
    allv = np.concatenate(groups) if groups else np.array([])
    if len(allv) == 0:
        return [None, None, None]
    est = stat(allv)
    bs = []
    for _ in range(n):
        pick = rng.integers(0, len(groups), len(groups))
        v = np.concatenate([groups[i] for i in pick])
        if len(v):
            bs.append(stat(v))
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return [round(float(est), 2), round(float(lo), 2), round(float(hi), 2)]


def note_calls(item, key):
    """Per true note: (inferred target, segment index) by majority over its mid frames."""
    r = item["res"][key]
    sof, out = r["seg_of_frame"], r["out"]
    nof, mid = item["nof"], item["mid"]
    n_notes = int(nof.max()) + 1
    calls = []
    for k in range(n_notes):
        segs = sof[(nof == k) & mid]
        segs = segs[segs >= 0]
        segs = [s for s in segs if out["dur"][s] >= TRANS_S]
        if not segs:
            calls.append((None, None))
            continue
        s = Counter(segs).most_common(1)[0][0]
        calls.append((int(round(out["target"][s])), s))
    return calls


def attribution(item, key, true_notes):
    calls = note_calls(item, key)
    offs = [c[0] - n for c, n in zip(calls, true_notes) if c[0] is not None]
    if not offs:
        return calls, np.zeros(len(true_notes), bool), None
    modal = Counter(offs).most_common(1)[0][0]
    ok = np.array([c[0] is not None and c[0] - n == modal for c, n in zip(calls, true_notes)])
    return calls, ok, modal


METHODS = [(s, r, n) for s in ("est", "oracle") for r in ("fixed", "global", "local")
           for n in ("chromatic", "key", "hybrid")]


def synth_summary(items):
    S = {}
    ebins = [(0, 20), (20, 35), (35, 50), (50, 75), (75, 1e9)]
    mbins = [(-1e9, 0), (0, 5), (5, 10), (10, 15), (15, 25), (25, 1e9)]
    for key in METHODS:
        name = "/".join(key)
        acc = defaultdict(lambda: [0, 0])
        margin_err = defaultdict(lambda: [0, 0])
        dev_err, cover_rel, cover_abs, score_ratio = defaultdict(list), defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0]), defaultdict(list)
        margins_all = []
        sig_err = defaultdict(list)
        post = []  # (P(correct), correct)
        for it in items:
            c, tr = it["cond"], it["truth"]
            notes = tr["notes"]
            calls, ok, modal = attribution(it, key, notes)
            e, D, w = tr["e"], it["D"], tr["durs"]
            out = it["res"][key]["out"]
            for k in range(len(notes)):
                answered = calls[k][0] is not None
                groups = [("all",), ("sigma", c["sigma"]), ("scale", c["scale"]),
                          ("drift", c["drift"]), ("vib", c["vib"]), ("voice", c["voice"])]
                ae = abs(e[k] + (D[k] if c["drift"] else 0))
                for lo, hi in ebins:
                    if lo <= abs(e[k]) < hi and c["drift"] == 0:
                        groups.append(("abs_e", f"{lo}-{hi if hi < 1e9 else 'inf'}"))
                if c["scale"] == "blue":
                    groups.append(("blue_note", not is_diatonic_note(notes, k)))
                for g in groups:
                    acc[g][1] += 1
                    acc[g][0] += int(ok[k])
                if not answered:
                    continue
                s = calls[k][1]
                m = out["margin"][s]
                margins_all.append((m, bool(ok[k])))
                for lo, hi in mbins:
                    if lo <= m < hi:
                        margin_err[f"{lo if lo > -1e9 else '-inf'}..{hi if hi < 1e9 else 'inf'}"][1] += 1
                        margin_err[f"{lo if lo > -1e9 else '-inf'}..{hi if hi < 1e9 else 'inf'}"][0] += int(not ok[k])
                if not ok[k]:
                    continue
                # estimands: relative to the singer's own (weighted) mean
                if key[1] == "local":
                    wt = w * np.exp(-0.5 * (((tr["starts"] + 0.6 * tr["durs"]) - (tr["starts"][k] + 0.6 * tr["durs"][k])) / 2.0) ** 2)
                    E_rel = e[k] - np.average(e, weights=wt)
                    E_abs = e[k]
                else:
                    E_rel = e[k] + D[k] - np.average(e + D, weights=w)
                    E_abs = e[k] + D[k]
                if key[1] == "fixed":
                    E_rel = E_abs = e[k] + D[k] + tr["G"] - 100 * modal
                d = out["dev"][s]
                us, ur = out["u_settle"][s], out["u_ref"][s]
                gk = ("sigma", c["sigma"], "vib", c["vib"], "drift", c["drift"])
                dev_err[gk].append(d - E_rel)
                dev_err["all"].append(d - E_rel)
                for g in ("all", gk):
                    cover_rel[g][1] += 1
                    cover_rel[g][0] += int(abs(d - E_rel) <= 2 * us)
                    cover_abs[g][1] += 1
                    cover_abs[g][0] += int(abs(d - E_abs) <= 2 * np.hypot(us, ur))
            # phrase spread on the circle, and per-note attribution posterior
            keep = out["dur"] >= TRANS_S
            if keep.sum() >= 3:
                sh = infer.circ_sigma(out["dev"][keep], out["dur"][keep])
                Et = (e - np.average(e, weights=w)) if key[1] == "local" else (e + D - np.average(e + D, weights=w))
                st = np.sqrt(np.average(Et ** 2, weights=w))
                sig_err[(c["sigma"], c["drift"], c["vib"])].append((sh, st))
                pp = infer.p_attrib(out["dev"], sh)
                for k in range(len(notes)):
                    if calls[k][0] is not None:
                        post.append((pp[calls[k][1]], bool(ok[k]), c["sigma"]))
            # phrase score: duration-weighted RMS deviation, notes only
            if keep.sum() >= 3:
                est_rms = np.sqrt(np.average(out["dev"][keep] ** 2, weights=out["dur"][keep]))
                Et = (e - np.average(e, weights=w)) if key[1] == "local" else (e + D - np.average(e + D, weights=w))
                true_rms = np.sqrt(np.average(Et ** 2, weights=w))
                score_ratio[(c["sigma"], c["drift"])].append(est_rms - true_rms)
        margins_all = np.array(margins_all, dtype=float).reshape(-1, 2)
        post = np.array(post, dtype=float).reshape(-1, 3)
        pbins = [(0, 0.5), (0.5, 0.8), (0.8, 0.95), (0.95, 0.99), (0.99, 1.01)]
        calib = {}
        for lo, hi in pbins:
            m = (post[:, 0] >= lo) & (post[:, 0] < hi)
            calib[f"{lo}-{min(hi, 1)}"] = dict(mean_p=round(100 * float(post[m, 0].mean()), 2) if m.any() else None,
                                                 observed=wilson(int(post[m, 1].sum()), int(m.sum())) + [int(m.sum())])
        flag95 = {}
        for sg in ("all",) + tuple(float(x) for x in (0, 10, 20, 30, 40)):
            m = np.ones(len(post), bool) if sg == "all" else post[:, 2] == sg
            fl = post[m, 0] < 0.95
            flag95[str(sg)] = dict(flagged=wilson(int(fl.sum()), int(m.sum())),
                                   err_unflagged=wilson(int((post[m][~fl, 1] == 0).sum()), int((~fl).sum())),
                                   err_flagged=wilson(int((post[m][fl, 1] == 0).sum()), int(fl.sum())))
        sig_summary = {}
        for k, v in sorted(sig_err.items()):
            v = np.array(v)
            fin = np.isfinite(v[:, 0])
            d = v[fin, 0] - v[fin, 1]
            sig_summary[f"sigma={k[0]},drift={k[1]},vib={k[2]}"] = dict(
                true_median=round(float(np.median(v[:, 1])), 2),
                est_minus_true_median=round(float(np.median(d)), 2) if fin.any() else None,
                p5=round(float(np.percentile(d, 5)), 2) if fin.any() else None,
                p95=round(float(np.percentile(d, 95)), 2) if fin.any() else None,
                not_above_chance=int((~fin).sum()), n=len(v))
        S[name] = dict(
            posterior_calibration=calib,
            flag_p95=flag95,
            circ_sigma=sig_summary,
            accuracy={f"{g[0]}={g[1]}" if len(g) > 1 else g[0]: wilson(*v) + [v[1]] for g, v in sorted(acc.items(), key=lambda x: str(x[0]))},
            error_by_margin={k: wilson(*v) + [v[1]] for k, v in margin_err.items()},
            flag=flag_threshold(margins_all),
            dev_err={str(k): dict(n=len(v), median_abs=round(float(np.median(np.abs(v))), 2), p95_abs=round(float(np.percentile(np.abs(v), 95)), 2)) for k, v in dev_err.items() if len(v)},
            coverage_rel_k2={str(k): wilson(*v) + [v[1]] for k, v in cover_rel.items()},
            coverage_abs_k2={str(k): wilson(*v) + [v[1]] for k, v in cover_abs.items()},
            phrase_rms_bias={f"sigma={k[0]},drift={k[1]}": dict(median=round(float(np.median(v)), 2), p5=round(float(np.percentile(v, 5)), 2), p95=round(float(np.percentile(v, 95)), 2), n=len(v)) for k, v in sorted(score_ratio.items())},
        )
    return S


def is_diatonic_note(notes, k):
    """In a 'blue' phrase, is note k an intended blue note? The phrase's major
    key is the diatonic set holding most of its notes."""
    pcs = np.mod(notes, 12)
    best, bc = None, -1
    for t in range(12):
        S = {(t + d) % 12 for d in (0, 2, 4, 5, 7, 9, 11)}
        c = sum(p in S for p in pcs)
        if c > bc:
            best, bc = S, c
    return pcs[k] in best


def flag_threshold(m):
    """Smallest margin threshold whose 'sure' notes (margin >= thr) err at most 1 %."""
    if len(m) == 0:
        return None
    for thr in np.arange(0, 51, 1.0):
        sure = m[:, 0] >= thr
        if sure.sum() == 0:
            break
        err = np.sum(~m[sure, 1].astype(bool))
        if wilson(err, sure.sum())[2] <= 1.0:
            return dict(threshold=float(thr), flagged=wilson(int((~sure).sum()), len(m)),
                        err_sure=wilson(int(err), int(sure.sum())),
                        err_flagged=wilson(int(np.sum(~m[~sure, 1].astype(bool))), int((~sure).sum())))
    return dict(threshold=None)


def real_summary(items):
    R = {}
    ok_items = [it for it in items if it["dtw_bad"] <= 0.2]
    R["takes"] = {f"{k}/{s}": sum(1 for it in items if it["kind"] == k and it["style"] == s) for k in ("scales", "row") for s in ("straight", "vibrato")}
    R["alignment_failed"] = sorted(it["name"] for it in items if it["dtw_bad"] > 0.2)
    R["dtw_bad_median_pct"] = round(100 * float(np.median([it["dtw_bad"] for it in ok_items])), 2)
    R["voiced_pct_median"] = round(100 * float(np.median([it["voiced"] for it in items])), 1)
    for key in METHODS:
        name = "/".join(key)
        acc = defaultdict(lambda: [0, 0])
        devs, margins = defaultdict(list), defaultdict(list)
        sig, post = defaultdict(list), defaultdict(list)
        for it in ok_items:
            calls, ok, modal = attribution(it, key, it["states"])
            g = f"{it['kind']}/{it['style']}"
            out = it["res"][key]["out"]
            acc[g][1] += len(ok)
            acc[g][0] += int(ok.sum())
            acc["all"][1] += len(ok)
            acc["all"][0] += int(ok.sum())
            d = np.array([out["dev"][c[1]] for c, o in zip(calls, ok) if o])
            mg = np.array([out["margin"][c[1]] for c in calls if c[1] is not None])
            devs[g].append(d)
            margins[g].append(mg)
            keep = out["dur"] >= TRANS_S
            sh = infer.circ_sigma(out["dev"][keep], out["dur"][keep])
            sig[g].append(sh)
            pp = infer.p_attrib(out["dev"], sh)
            for c, o in zip(calls, ok):
                if c[1] is not None:
                    post[g].append((pp[c[1]], bool(o)))
        R[name] = dict(
            accuracy={g: wilson(*v) + [v[1]] for g, v in acc.items()},
            abs_dev_median={g: boot([np.abs(x) for x in v], np.median) for g, v in devs.items()},
            abs_dev_p95={g: boot([np.abs(x) for x in v], lambda a: np.percentile(a, 95)) for g, v in devs.items()},
            margins_by_group={g: v for g, v in margins.items()},
            circ_sigma={g: dict(median=round(float(np.median(np.where(np.isfinite(v), v, 1e9))), 2),
                               p10_p90=[round(float(np.percentile(np.where(np.isfinite(v), v, 1e9), q)), 2) for q in (10, 90)],
                               not_above_chance=int(np.sum(~np.isfinite(v))), n=len(v)) for g, v in sig.items()},
            flag_p95={g: dict(flagged=wilson(int(np.sum(np.array(v)[:, 0] < 0.95)), len(v)),
                              err_unflagged=wilson(int(np.sum((np.array(v)[:, 0] >= 0.95) & (np.array(v)[:, 1] == 0))), int(np.sum(np.array(v)[:, 0] >= 0.95))),
                              err_flagged=wilson(int(np.sum((np.array(v)[:, 0] < 0.95) & (np.array(v)[:, 1] == 0))), int(np.sum(np.array(v)[:, 0] < 0.95))))
                      for g, v in post.items()},
        )
    return R


def input_check(synth, real):
    def dips(items):
        return np.concatenate([it["dmin"][np.isfinite(it["dmin"])] for it in items])
    s_straight = [it for it in synth if it["cond"]["vib"] == 0 and it["cond"]["sigma"] == 0 and it["cond"]["drift"] == 0]
    r_straight = [it for it in real if it["style"] == "straight" and it["kind"] == "scales"]
    return dict(
        voiced_pct_synth=[round(100 * float(np.percentile([it["voiced"] for it in synth], q)), 1) for q in (5, 50, 95)],
        voiced_pct_real=[round(100 * float(np.percentile([it["voiced"] for it in real], q)), 1) for q in (5, 50, 95)],
        cmnd_dip_voiced_median_synth=round(float(np.median(dips(s_straight)[dips(s_straight) < 0.1])), 4),
        cmnd_dip_voiced_median_real=round(float(np.median(dips(r_straight)[dips(r_straight) < 0.1])), 4),
    )


if __name__ == "__main__":
    synth = pickle.load(open(CACHE / "synth.pkl", "rb"))
    real = pickle.load(open(CACHE / "real.pkl", "rb"))
    S = synth_summary(synth)
    R = real_summary(real)
    # flag threshold chosen on synthetic applied to real margins
    for key in METHODS:
        name = "/".join(key)
        thr = (S[name]["flag"] or {}).get("threshold")
        mg = R[name].pop("margins_by_group")
        if thr is not None:
            R[name]["flagged_at_synth_threshold"] = {g: wilson(int(np.sum(np.concatenate(v) < thr)), int(sum(len(x) for x in v))) for g, v in mg.items()}
    out = dict(synthetic=S, vocalset=R, input_check=input_check(synth, real),
               n_synth_phrases=len(synth), n_real_takes=len(real))
    if (CACHE / "real_lp.pkl").exists():
        lp = real_summary(pickle.load(open(CACHE / "real_lp.pkl", "rb")))
        out["input_check"]["vocalset_lowpass_4k"] = {m: dict(accuracy=lp[m]["accuracy"], circ_sigma=lp[m]["circ_sigma"])
                                                     for m in ("est/global/chromatic", "oracle/global/chromatic")}
    json.dump(out, open(OUT / "summary.json", "w"), indent=1, default=str)
    print(json.dumps(out["input_check"]), json.dumps(R["takes"]), R["alignment_failed"])
