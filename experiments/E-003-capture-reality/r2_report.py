"""E-003 round 2: rules 5 and 6 over every capture (README, *Round 2*).
Called by `r2_measures.py` with no argument. Crude experiment code."""
import json
import math
from collections import defaultdict
from multiprocessing import Pool

import numpy as np

import r2_measures as X

BOOT, SEED = 1000, 20260928


def w_of(r, target):
    """The least w on X.widening's 0.01 grid from 1 with mean(r <= w) >= target, r = |err| / 2u."""
    if not len(r) or not np.isfinite(target):
        return float("nan")
    k = math.ceil(round(target * len(r), 9))
    q = np.sort(r)[max(k, 1) - 1]
    return max(1.0, math.ceil(round(q * 100, 9)) / 100)


def pooled(items):
    e = np.concatenate([i["err"] for i in items]) if items else np.array([])
    u = np.concatenate([i["u"] for i in items]) if items else np.array([])
    return e, u, sum(i["valid"] for i in items), sum(i["accepted"] for i in items)


def frame_boot(pairs):
    """frame_block's bootstrapped quantities only (no percentiles of the error)."""
    ed, ud, vd, ad = pooled([d for d, _ in pairs])
    ec, uc, vc, ac = pooled([c for _, c in pairs])
    cd, cc = X.coverage(ed, ud), X.coverage(ec, uc)
    return dict(w=w_of(ec / (2 * uc), cd), coverage_drop=cd - cc, accepted_share_drop=ad / vd - ac / vc,
                gross_rise=float(np.mean(ec > 50) - np.mean(ed > 50)))


def frame_block(pairs):
    """pairs: [(direct frame stats, capture frame stats)] on the same takes."""
    ed, ud, vd, ad = pooled([d for d, _ in pairs])
    ec, uc, vc, ac = pooled([c for _, c in pairs])
    cd, cc = X.coverage(ed, ud), X.coverage(ec, uc)
    return dict(direct=dict(valid=vd, accepted=ad, accepted_share=ad / vd if vd else None, coverage=cd,
                            p95_abs_err=float(np.percentile(ed, 95)) if len(ed) else None,
                            gross_share=float(np.mean(ed > 50)) if len(ed) else None),
                capture=dict(valid=vc, accepted=ac, accepted_share=ac / vc if vc else None, coverage=cc,
                             p95_abs_err=float(np.percentile(ec, 95)) if len(ec) else None,
                             gross_share=float(np.mean(ec > 50)) if len(ec) else None),
                w=w_of(ec / (2 * uc), cd))


def take_block(pairs):
    """pairs: [(direct take measures, capture take measures)]."""
    out = {}
    for k, name in X.KEYS.items():
        both = [(d["take"][k], c["take"][k]) for d, c in pairs if d["take"][k] and c["take"][k]]
        only_d = sum(1 for d, c in pairs if d["take"][k] and not c["take"][k])
        only_c = sum(1 for d, c in pairs if c["take"][k] and not d["take"][k])
        moved = [abs(c["value"] - d["value"]) > 2 * d["u"] for d, c in both]
        wt = [(d, c) for d, c in both if d["truth"] is not None and c["truth"] is not None]
        cov_d = sum(abs(d["value"] - d["truth"]) <= 2 * d["u"] for d, _ in wt)
        r = np.array([abs(c["value"] - c["truth"]) / (2 * c["u"]) for _, c in wt])
        cov_c = int(np.sum(r <= 1.0))
        w = w_of(r, cov_d / len(wt)) if wt else float("nan")
        out[name] = dict(both=len(both), direct_only=only_d, capture_only=only_c,
                         moved=int(sum(moved)), moved_share=float(np.mean(moved)) if moved else None,
                         with_truth=len(wt), direct_covers_truth=int(cov_d), capture_covers_truth=cov_c, w_take=w,
                         median_shift=float(np.median([c["value"] - d["value"] for d, c in both])) if both else None,
                         median_ratio_u=float(np.median([c["u"] / d["u"] for d, c in both])) if both else None)
    return out


def boot(rows, fn, keys, rng):
    """95 % percentile intervals of fn(...)[key] over bootstrap resamples of the singers."""
    singers = sorted({r["singer"] for r in rows})
    by = defaultdict(list)
    for r in rows:
        by[r["singer"]].append(r)
    vals = defaultdict(list)
    for _ in range(BOOT):
        pick = rng.choice(len(singers), len(singers), replace=True)
        b = fn([x for i in pick for x in by[singers[i]]])
        for name, kf in keys.items():
            v = kf(b)
            if v is not None and np.isfinite(v):
                vals[name].append(v)
    return {n: ([float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if (v := vals.get(n)) else None)
            for n in keys}


def main():
    inputs = json.loads((X.OUT / "inputs.json").read_text())["rows"]
    meta = {(r["stem"], r["cond"]): r for r in inputs}
    caps = sorted(tuple(p.name[:-5].split(".")) for p in X.CAP.glob("*.json"))
    assert len(caps) == 440, len(caps)
    # the vectorised w_of against rule 5's grid search, on the checks' own inputs (S15)
    x, ft = X.read_input("f1_long_straight_a", "clean")
    st = X.frame_stats(X.frames(x, ft))
    cov = X.coverage(st["err"], st["u"])
    for m in (1.0, 3.0, 0.5):
        assert w_of(m * st["err"] / (2 * st["u"]), cov) == X.widening(m * st["err"], st["u"], cov), m
    import pickle
    cache = X.CAP.parent / "measures.pkl"
    if cache.exists():
        D, Cp = pickle.loads(cache.read_bytes())
    else:
        with Pool(16) as pool:
            D = {k: (fs, tm) for k, fs, tm in pool.map(X.direct, sorted(meta))}
            Cp = {k: (fs, tm, info) for k, fs, tm, info in pool.map(X.captured, caps)}
        cache.write_bytes(pickle.dumps((D, Cp)))
    print("measured", len(D), "inputs,", len(Cp), "captures", flush=True)
    groups = defaultdict(list)
    for (stem, cond, req), (fs, tm, info) in Cp.items():
        groups[(req, cond)].append(dict(stem=stem, singer=meta[(stem, cond)]["singer"], set=meta[(stem, cond)]["set"],
                                        cfs=fs, ctm=tm, info=info, dfs=D[(stem, cond)][0], dtm=D[(stem, cond)][1]))
    rng = np.random.default_rng(SEED)
    R = dict(versions=sorted({i["version"] for _, _, i in Cp.values() if i.get("version")}), groups={})
    for (req, cond), rows in sorted(groups.items()):
        ok = [r for r in rows if r["cfs"] is not None]
        fb = frame_block([(r["dfs"], r["cfs"]) for r in ok])
        tb = take_block([(r["dtm"], r["ctm"]) for r in ok])
        g = dict(captures=len(rows), with_anomaly=len(rows) - len(ok),
                 anomalies=[dict(stem=r["stem"], at=[(a["input_s"], a["shift"], a["to_end_s"]) for a in r["info"]["anomalies"]])
                            for r in rows if r["cfs"] is None],
                 readback=sorted({json.dumps({k: r["info"]["settings"].get(k) for k in (
                     "echoCancellation", "noiseSuppression", "autoGainControl", "sampleRate", "channelCount")})
                     for r in rows}),
                 gain_median=float(np.median([r["info"]["gain"] for r in ok])),
                 gain_range=[float(min(r["info"]["gain"] for r in ok)), float(max(r["info"]["gain"] for r in ok))],
                 full_scale_share=float(np.mean([r["info"]["peak"] >= 0.999 for r in ok])),
                 residual_db_median=float(np.median([r["info"]["residual_db"] for r in ok])),
                 lost_blocks=sum(r["info"]["worker"]["lost"] for r in ok),
                 frames=fb, takes=tb)
        fci = boot(ok, lambda rs: frame_boot([(r["dfs"], r["cfs"]) for r in rs]),
                   {k: (lambda b, k=k: b[k]) for k in ("w", "coverage_drop", "accepted_share_drop")}, rng)
        g["frames"].update(w_ci95=fci["w"], coverage_drop_ci95=fci["coverage_drop"],
                           accepted_share_drop_ci95=fci["accepted_share_drop"])
        tkeys = {f"{n}|{q}": (lambda b, n=n, q=q: b[n][q]) for n in X.KEYS.values() for q in ("w_take", "moved_share")}
        tci = boot(ok, lambda rs: take_block([(r["dtm"], r["ctm"]) for r in rs]), tkeys, rng)
        for name in X.KEYS.values():
            g["takes"][name]["w_take_ci95"] = tci[f"{name}|w_take"]
            g["takes"][name]["moved_share_ci95"] = tci[f"{name}|moved_share"]
        R["groups"][f"{req} {cond}"] = g
        t = g["takes"]
        print(f"{req:8s}{cond:9s} n={len(rows)} anom={g['with_anomaly']} gain={g['gain_median']:.2f} fs={g['full_scale_share']:.2f} "
              f"acc {fb['direct']['accepted_share']:.3f}->{fb['capture']['accepted_share']:.3f} "
              f"cov {fb['direct']['coverage']:.3f}->{fb['capture']['coverage']:.3f} w={fb['w']} {g['frames']['w_ci95']} | "
              + " ".join(f"{n[:6]} {v['both']}+{v['direct_only']}-{v['capture_only']} mv {v['moved']} wt {v['w_take']}" for n, v in t.items()),
              flush=True)
    # rule 6's fallback: raw did not pass (w above 1.00), so each processed request is compared with
    # the raw capture of the same input, over inputs where neither capture has an anomaly
    R["vs_raw"] = {}
    for (req, cond), rows in sorted(groups.items()):
        if req == "raw":
            continue
        raw = {r["stem"]: r for r in groups[("raw", cond)]}
        ok = [dict(singer=r["singer"], dfs=raw[r["stem"]]["cfs"], cfs=r["cfs"], dtm=raw[r["stem"]]["ctm"], ctm=r["ctm"])
              for r in rows if r["cfs"] is not None and raw[r["stem"]]["cfs"] is not None]
        fb = frame_block([(r["dfs"], r["cfs"]) for r in ok])
        tb = take_block([(r["dtm"], r["ctm"]) for r in ok])
        fci = boot(ok, lambda rs: frame_boot([(r["dfs"], r["cfs"]) for r in rs]),
                   {k: (lambda b, k=k: b[k]) for k in ("w", "coverage_drop", "accepted_share_drop", "gross_rise")}, rng)
        fb.update({f"{k}_ci95": v for k, v in fci.items()})
        tkeys = {f"{n}|{q}": (lambda b, n=n, q=q: b[n][q]) for n in X.KEYS.values() for q in ("w_take", "moved_share")}
        tci = boot(ok, lambda rs: take_block([(r["dtm"], r["ctm"]) for r in rs]), tkeys, rng)
        for name in X.KEYS.values():
            tb[name]["w_take_ci95"] = tci[f"{name}|w_take"]
            tb[name]["moved_share_ci95"] = tci[f"{name}|moved_share"]
        R["vs_raw"][f"{req} {cond}"] = dict(inputs=len(ok), frames=fb, takes=tb,
                                             widens=dict(frames=bool(fb["w_ci95"] and fb["w_ci95"][0] > 1.0),
                                                         takes={n: bool(v["w_take_ci95"] and v["w_take_ci95"][0] > 1.0)
                                                                for n, v in tb.items()}))
        f = fb
        print(f"vs raw {req:8s}{cond:9s} n={len(ok)} acc {f['direct']['accepted_share']:.3f}->{f['capture']['accepted_share']:.3f} "
              f"cov {f['direct']['coverage']:.4f}->{f['capture']['coverage']:.4f} gross {f['direct']['gross_share']:.4f}->{f['capture']['gross_share']:.4f} "
              f"w={f['w']} {f['w_ci95']} | " + " ".join(f"{n[:6]} {v['both']} mv {v['moved']} wt {v['w_take']} {v['w_take_ci95']}" for n, v in tb.items()), flush=True)
    # rule 6: the reference condition must pass
    bars = {}
    for cond in ("clean", "white-20"):
        g = R["groups"][f"raw {cond}"]
        f = g["frames"]
        bars[f"raw {cond}"] = dict(
            coverage_within_1_point=abs(f["capture"]["coverage"] - f["direct"]["coverage"]) <= 0.01,
            w_is_1=f["w"] == 1.0,
            takes_moved_at_most_5pc={n: (v["moved_share"] is None or v["moved_share"] <= 0.05) for n, v in g["takes"].items()})
    R["reference_bar"] = bars
    R["widens"] = {k: dict(frames=bool(g["frames"]["w_ci95"] and g["frames"]["w_ci95"][0] > 1.0),
                           takes={n: bool(v["w_take_ci95"] and v["w_take_ci95"][0] > 1.0) for n, v in g["takes"].items()})
                   for k, g in R["groups"].items()}
    (X.OUT / "analysis.json").write_text(json.dumps(R, indent=1, default=float))
    print(json.dumps(dict(reference_bar=bars, widens=R["widens"]), indent=1))


if __name__ == "__main__":
    main()
