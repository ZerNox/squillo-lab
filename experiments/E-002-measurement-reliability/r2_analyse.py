"""E-002 round 2, step 4: per-frame pitch uncertainty, three pitch measures
and one tone measure, each with its +-, on real voices. Crude experiment code.
Needs data/cache/r2_frames.npz and r2_tone.json from r2_run.py.

    uv run python r2_analyse.py     # writes results/r2_results.json

Definitions are written in the README (round 2, *Definitions*). Singers are
split in two folds by their number's parity; every rule fitted on one fold is
tested on the other, both ways.
"""

import json

import numpy as np
from scipy.signal import butter, filtfilt

import r2_truth as T

Z = np.load(T.CACHE / "r2_frames.npz")
TONE = json.loads((T.CACHE / "r2_tone.json").read_text())
META = TONE["meta"]
NF = len(META)
SET = np.array([m["set"] for m in META])
SINGER = [m["singer"] for m in META]
FOLD = np.array([int("".join(c for c in s if c.isdigit())) % 2 for s in SINGER])  # 1 odd, 0 even
FIT_CONDS = ["clean", "white-30", "white-20", "white-10", "pink-20", "pink-10"]
ALL_CONDS = FIT_CONDS + ["room-0.4", "room-0.8", "original"]
BINS = [0.0, 0.0025, 0.005, 0.01, 0.02, 0.03, 0.05, 0.07, 0.1]
GROSS = 50.0
U_FLOOR = np.sqrt(3.0)  # squillo metrics MT-003's floor
FR = 125.0  # frames per second (48000 / 384)


def cents_err(c):
    f, t = Z[c + "/f"], Z[c + "/f_true"]
    e = np.full(len(f), np.nan)
    ok = Z[c + "/valid"] & ~np.isnan(f)
    e[ok] = 1200 * np.log2(f[ok] / t[ok])
    return e, ok


ERR = {c: cents_err(c) for c in ALL_CONDS}


# ------------------------------------------------------------ per-frame u
def fit_u(train_mask_by_cond):
    """u per dip bin: half the 95th percentile of |error| (gross errors as misses), floor
    sqrt(3); a bin whose 95th percentile is gross is refused, with every bin above it."""
    e_all, d_all = [], []
    for c in FIT_CONDS:
        e, ok = ERR[c]
        m = ok & train_mask_by_cond[c]
        e_all.append(np.abs(e[m])); d_all.append(Z[c + "/dip"][m])
    e, d = np.concatenate(e_all), np.concatenate(d_all)
    e = np.where(e > GROSS, np.inf, e)
    u, refused = [], False
    for a, b in zip(BINS[:-1], BINS[1:]):
        sel = e[(d >= a) & (d < b)]
        q = np.percentile(sel, 95) if len(sel) else np.inf
        if refused or not np.isfinite(q):
            refused = True
            u.append(np.inf)
        else:
            u.append(max(U_FLOOR, q / 2))
    u = np.maximum.accumulate(np.array(u))
    return u


def u_of(dip, table):
    k = np.clip(np.searchsorted(BINS, dip, side="right") - 1, 0, len(table) - 1)
    return table[k]


def frame_masks(fold):
    fm = FOLD[Z["clean/file"]] == fold  # same file layout for every condition
    return {c: FOLD[Z[c + "/file"]] == fold for c in ALL_CONDS}


def frame_tests():
    out = {"tables": {}, "tests": {}}
    for fit_fold in (1, 0):
        test_fold = 1 - fit_fold
        table = fit_u(frame_masks(fit_fold))
        out["tables"][f"fit on {'odd' if fit_fold else 'even'} singers"] = table.tolist()
        for c in ALL_CONDS:
            e, ok = ERR[c]
            fm = FOLD[Z[c + "/file"]] == test_fold
            valid = Z[c + "/valid"] & fm
            m = ok & fm
            u = u_of(Z[c + "/dip"][m], table)
            acc = np.isfinite(u)
            ea = np.abs(e[m][acc]); ua = u[acc]
            rows = dict(valid=int(valid.sum()), measured_share=float(m.sum() / valid.sum()),
                        accepted_share=float(acc.sum() / valid.sum()),
                        coverage_k2=float(np.mean(ea <= 2 * ua)), gross_share_accepted=float(np.mean(ea > GROSS)),
                        median_u=float(np.median(ua)), floor_only_coverage=float(np.mean(np.abs(e[m]) <= 2 * U_FLOOR)))
            by_set = {}
            for s in sorted(set(SET)):
                ss = SET[Z[c + "/file"][m]][acc] == s
                if ss.any():
                    by_set[s] = dict(frames=int(ss.sum()), coverage_k2=float(np.mean(ea[ss] <= 2 * ua[ss])))
            rows["by_set"] = by_set
            out["tests"][f"{c} | test on {'odd' if test_fold else 'even'} singers"] = rows
    # every frame's u from the table fitted on the other fold, for the measures below
    U = {}
    for c in ALL_CONDS:
        u = np.full(len(Z[c + "/f"]), np.inf)
        for fit_fold in (1, 0):
            table = np.array(out["tables"][f"fit on {'odd' if fit_fold else 'even'} singers"])
            m = FOLD[Z[c + "/file"]] == 1 - fit_fold
            u[m] = u_of(Z[c + "/dip"][m], table)
        U[c] = u
    # the frame-level summary per condition, both folds' tests pooled, for the README
    pooled = {}
    for c in ALL_CONDS:
        e, ok = ERR[c]
        valid = Z[c + "/valid"]
        acc = ok & np.isfinite(U[c])
        ea = np.abs(e[acc])
        g = np.abs(e[ok]) > GROSS
        pooled[c] = dict(valid=int(valid.sum()), measured_share=float(ok.sum() / valid.sum()),
                         gross_share_measured=float(g.mean()),
                         p50_abs=float(np.median(np.abs(e[ok]))), p95_abs_non_gross=float(np.percentile(np.abs(e[ok])[~g], 95)),
                         floor_only_coverage=float(np.mean(np.abs(e[ok]) <= 2 * U_FLOOR)),
                         accepted_share=float(acc.sum() / valid.sum()), coverage_k2=float(np.mean(ea <= 2 * U[c][acc])),
                         gross_share_accepted=float(np.mean(ea > GROSS)))
        # span-mean truth instead of SG-007's instant (clean only matters)
        tm = Z[c + "/f_true_mean"]
        em = 1200 * np.log2(Z[c + "/f"][ok] / tm[ok])
        pooled[c]["p95_abs_non_gross_span_mean_truth"] = float(np.percentile(np.abs(em)[np.abs(em) <= GROSS], 95))
    out["pooled_cross_validated"] = pooled
    return out, U


# ------------------------------------------------------------ contours and measures
B2 = butter(2, 2.0, "low", fs=FR)
BV = butter(2, [3.0, 10.0], "band", fs=FR)


def segments(file_k):
    """Held segments from the clean truth: runs of consecutive valid frames, split where the
    2 Hz low-passed truth leaves the segment's first 0.25 s median by more than 60 cents;
    kept if >= 2 s; trimmed 0.5 s each end after filtering."""
    m = Z["clean/file"] == file_k
    idx = Z["clean/idx"][m]; valid = Z["clean/valid"][m]; ft = Z["clean/f_true"][m]
    out = []
    i = 0
    n = len(idx)
    while i < n:
        if not valid[i]:
            i += 1; continue
        j = i
        while j < n and valid[j] and (j == i or idx[j] == idx[j - 1] + 1):
            j += 1
        run = np.arange(i, j)
        if len(run) >= 250:
            p = 1200 * np.log2(ft[run] / 440.0)
            lp = filtfilt(*B2, p)
            s0 = 0
            while s0 < len(run):
                ref = np.median(lp[s0:s0 + 31])
                s1 = s0 + 1
                while s1 < len(run) and abs(lp[s1] - ref) <= 60:
                    s1 += 1
                if s1 - s0 >= 250:
                    out.append(run[s0:s1])
                s0 = s1
        i = j
    return m, out


def contour(c, gm, seg, U):
    """Measured contour (cents re A4) on a segment's frames: frames refused by YIN or by the u
    rule are gaps; octave outliers (> 600 cents from the segment's median) are dropped;
    gaps filled linearly if they are <= 25 % of the segment and none is longer than 12 frames.
    Returns (contour or None, u per frame)."""
    f = Z[c + "/f"][gm][seg]
    u = U[c][gm][seg]
    p = 1200 * np.log2(f / 440.0)
    good = ~np.isnan(p) & np.isfinite(u)
    if good.sum() < 0.75 * len(seg):
        return None, None
    med = np.median(p[good])
    good &= np.abs(p - med) <= 600
    if good.sum() < 0.75 * len(seg):
        return None, None
    gaps = np.diff(np.concatenate([[0], (~good).astype(int), [0]]))
    starts, ends = np.nonzero(gaps == 1)[0], np.nonzero(gaps == -1)[0]
    if len(starts) and (ends - starts).max() > 12:
        return None, None
    x = np.arange(len(seg))
    return np.interp(x, x[good], p[good]), np.where(good, u, np.nan)


def block_measures(p):
    """Per 1 s block of a segment (after 0.5 s trims): steadiness (SD of the 2 Hz low-passed
    contour), vibrato extent (sqrt 2 x RMS of the 3-10 Hz band-passed contour) and rate
    (the band-passed block's spectral peak, 3-10 Hz, reported only when the peak's +-0.5 Hz
    holds >= 50 % of the band's power)."""
    lp = filtfilt(*B2, p)
    bp = filtfilt(*BV, p)
    lo, hi = 62, len(p) - 62
    out = []
    for b0 in range(lo, hi - 124, 125):
        sl = slice(b0, b0 + 125)
        S = float(np.std(lp[sl]))
        E = float(np.sqrt(2) * np.sqrt(np.mean(bp[sl] ** 2)))
        X = np.abs(np.fft.rfft(bp[sl] * np.hanning(125), 8192)) ** 2
        fr = np.fft.rfftfreq(8192, 1 / FR)
        band = (fr >= 3) & (fr <= 10)
        kk = np.nonzero(band)[0][np.argmax(X[band])]
        if 0 < kk < len(X) - 1:
            a, b_, c = np.log(X[kk - 1:kk + 2] + 1e-30)
            den = a - 2 * b_ + c
            off = 0.5 * (a - c) / den if den < 0 else 0.0
        else:
            off = 0.0
        R = float((kk + off) * FR / 8192)
        share = float(X[(fr >= R - 0.5) & (fr <= R + 0.5)].sum() / X[band].sum())
        out.append(dict(S=S, E=E, R=R if share >= 0.5 else None, b0=b0))
    return out


def measures(U):
    """Block values, measured (per condition) and true (the same function on the truth)."""
    rows = []
    for k in range(NF):
        gm, segs = segments(k)
        for si, seg in enumerate(segs):
            pt = 1200 * np.log2(Z["clean/f_true"][gm][seg] / 440.0)
            tb = block_measures(pt)
            for c in ALL_CONDS[:-1]:
                if c != "clean":
                    # truth is the same for every condition; the frames are the same by construction
                    assert np.array_equal(Z[c + "/idx"][Z[c + "/file"] == k][seg], Z["clean/idx"][gm][seg])
                p, u = contour(c, Z[c + "/file"] == k, seg, U)
                if p is None:
                    rows.append(dict(file=k, seg=si, cond=c, blocks=None, n_true=len(tb)))
                    continue
                mb = block_measures(p)
                for b, t in zip(mb, tb):
                    uu = u[b["b0"]:b["b0"] + 125]
                    b["rms_u"] = float(np.sqrt(np.nanmean(uu ** 2)))
                    b["true"] = t
                rows.append(dict(file=k, seg=si, cond=c, blocks=mb, n_true=len(tb)))
    return rows


def fit_c(rows, fold, key):
    """Tracking u of a block value: c x rms(u_f) (steadiness, extent) or c x rms(u_f) / extent
    (rate), c = the 95th percentile of |error| / (2 x shape) on the fitting fold, pooled over
    FIT_CONDS."""
    r = []
    for row in rows:
        if row["blocks"] is None or FOLD[row["file"]] != fold or row["cond"] not in FIT_CONDS:
            continue
        for b in row["blocks"]:
            t = b["true"]
            if key == "R":
                if b["R"] is None or t["R"] is None:
                    continue
                r.append(abs(b["R"] - t["R"]) / (2 * b["rms_u"] / b["E"]))
            else:
                r.append(abs(b[key] - t[key]) / (2 * b["rms_u"]))
    return float(np.percentile(r, 95))


def take_values(blocks, key, c_fit):
    vals, ut, tv = [], [], []
    for b in blocks:
        if key == "R" and (b["R"] is None or b["true"]["R"] is None):
            continue
        vals.append(b[key]); tv.append(b["true"][key])
        ut.append(c_fit * b["rms_u"] / (b["E"] if key == "R" else 1.0))
    return np.array(vals), np.array(ut), np.array(tv)


def combine(vals, ut):
    """A take's value: the mean of its blocks; u = sqrt(SD^2 / n + mean(u_track)^2), the
    blocks' sampling (GUM 4.2.3) and the tracking taken as fully correlated across blocks."""
    n = len(vals)
    return float(vals.mean()), float(np.sqrt(vals.std(ddof=1) ** 2 / n + ut.mean() ** 2))


def kappa(pairs):
    """The factor by which both halves' u must grow for a 5 % false-change rate:
    the 95th percentile of |a - b| / (2 sqrt(ua^2 + ub^2))."""
    r = [abs(a - b) / (2 * np.sqrt(ua ** 2 + ub ** 2)) for a, ua, b, ub in pairs]
    return float(np.percentile(r, 95)) if len(r) >= 10 else None


def split_half(v, ut):
    h = len(v) // 2
    a, ua = combine(v[:h], ut[:h]); b, ub = combine(v[h:2 * h], ut[h:2 * h])
    return a, ua, b, ub


def measure_tests(rows):
    """Per take (a file under a condition): its blocks from every held segment, in time order."""
    out = {}
    for key, name in (("S", "steadiness"), ("E", "vibrato extent"), ("R", "vibrato rate")):
        res = {"c_fit": {}, "block": {}, "take": {}, "split_half": {}}
        for fit_fold in (1, 0):
            res["c_fit"][f"fit on {'odd' if fit_fold else 'even'}"] = fit_c(rows, fit_fold, key)
        for c in ALL_CONDS[:-1]:
            per_take, n_seg, n_unmeas = {}, 0, 0
            for row in rows:
                if row["cond"] != c:
                    continue
                n_seg += 1
                if row["blocks"] is None:
                    n_unmeas += 1
                    continue
                cf = res["c_fit"][f"fit on {'odd' if FOLD[row['file']] == 0 else 'even'}"]  # fitted on the other fold
                v, ut, tv = take_values(row["blocks"], key, cf)
                t = per_take.setdefault(row["file"], [[], [], []])
                t[0] += list(v); t[1] += list(ut); t[2] += list(tv)
            blk_err, blk_cov, take_err, take_cov, pairs, sets_pairs = [], [], [], [], [], {}
            for k, (v, ut, tv) in per_take.items():
                v, ut, tv = np.array(v), np.array(ut), np.array(tv)
                if len(v) == 0:
                    continue
                blk_err += list(v - tv); blk_cov += list(np.abs(v - tv) <= 2 * ut)
                if len(v) >= 2:
                    m, u = combine(v, ut)
                    take_err.append(m - tv.mean()); take_cov.append(abs(m - tv.mean()) <= 2 * u)
                if len(v) >= 4:
                    pr = split_half(v, ut)
                    pairs.append(pr)
                    sets_pairs.setdefault(SET[k], []).append(pr)
            be = np.array(blk_err); te = np.array(take_err)
            fa = [abs(a - b) > 2 * np.sqrt(ua ** 2 + ub ** 2) for a, ua, b, ub in pairs]
            res["block"][c] = dict(blocks=len(be), median_err=float(np.median(be)) if len(be) else None,
                                   p95_abs_err=float(np.percentile(np.abs(be), 95)) if len(be) else None,
                                   coverage_k2=float(np.mean(blk_cov)) if blk_cov else None)
            res["take"][c] = dict(segments=n_seg, segments_unmeasured=n_unmeas, takes=len(te),
                                  median_err=float(np.median(te)) if len(te) else None,
                                  p95_abs_err=float(np.percentile(np.abs(te), 95)) if len(te) else None,
                                  coverage_k2=float(np.mean(take_cov)) if take_cov else None)
            res["split_half"][c] = dict(takes=len(pairs), false_change_share=float(np.mean(fa)) if fa else None,
                                        kappa=kappa(pairs),
                                        by_set={s_: dict(n=len(v), false_change_share=float(np.mean([abs(a - b) > 2 * np.sqrt(ua ** 2 + ub ** 2) for a, ua, b, ub in v])))
                                                for s_, v in sorted(sets_pairs.items())})
        tv_all = [b["true"][key] for row in rows if row["cond"] == "clean" and row["blocks"] for b in row["blocks"]
                  if b["true"][key] is not None]
        res["truth_range"] = dict(blocks=len(tv_all), p5=float(np.percentile(tv_all, 5)), median=float(np.median(tv_all)), p95=float(np.percentile(tv_all, 95)))
        out[name] = res
    return out


# ------------------------------------------------------------ tone
def tone_tests():
    out = {}
    names = [m["name"] for m in META]
    by = TONE["tone"]

    def take(blocks):
        v = np.array([b["ring"] for b in blocks])
        if len(v) < 2:
            return None
        return float(v.mean()), float(v.std(ddof=1) / np.sqrt(len(v))), v
    conds = [c for c in ALL_CONDS if c != "original"]
    clean = {n: take(by[n]["clean"]) for n in names}
    for c in conds:
        fa, bias, changed, ns, pairs = [], [], [], 0, []
        sets_fa = {}
        for n in names:
            t = take(by[n][c])
            if t is None:
                continue
            ns += 1
            m, u, v = t
            if len(v) >= 4:
                h = len(v) // 2
                a, b = v[:h], v[h:2 * h]
                ua, ub = a.std(ddof=1) / np.sqrt(h), b.std(ddof=1) / np.sqrt(h)
                alarm = abs(a.mean() - b.mean()) > 2 * np.sqrt(ua ** 2 + ub ** 2)
                fa.append(alarm)
                pairs.append((a.mean(), ua, b.mean(), ub))
                sets_fa.setdefault(T.set_of(n), []).append(alarm)
            if c != "clean" and clean[n] is not None:
                bias.append(m - clean[n][0])
                changed.append(abs(m - clean[n][0]) > 2 * np.sqrt(u ** 2 + clean[n][1] ** 2))
        out[c] = dict(takes=ns, of=len(names), split_half_false_change=float(np.mean(fa)) if fa else None, split_half_n=len(fa),
                      kappa=kappa(pairs),
                      split_half_by_set={s: dict(n=len(v), share=float(np.mean(v))) for s, v in sorted(sets_fa.items())},
                      bias_vs_clean_median=float(np.median(bias)) if bias else None,
                      bias_vs_clean_p95_abs=float(np.percentile(np.abs(bias), 95)) if bias else None,
                      called_changed_vs_clean=float(np.mean(changed)) if changed else None)
    us = np.array([t[1] for t in clean.values() if t is not None])
    vals = np.array([t[0] for t in clean.values() if t is not None])
    out["clean_u"] = dict(median=float(np.median(us)), p95=float(np.percentile(us, 95)))
    out["clean_values"] = dict(p5=float(np.percentile(vals, 5)), median=float(np.median(vals)), p95=float(np.percentile(vals, 95)))
    # does it tell forte from pp, same singer, same vowel?
    sep, diffs, trip = [], [], []
    for s in sorted(set(SINGER)):
        f = [n for n in names if T.singer_of(n) == s and T.set_of(n) == "LT-forte"]
        p = [n for n in names if T.singer_of(n) == s and T.set_of(n) == "LT-pp"]
        if f and p and clean[f[0]] and clean[p[0]]:
            (a, ua, _), (b, ub, _) = clean[f[0]], clean[p[0]]
            diffs.append(a - b); trip.append((a - b, ua, ub))
            sep.append(abs(a - b) > 2 * np.sqrt(ua ** 2 + ub ** 2))
    kap = out["clean"]["kappa"]
    sepk = [abs(d) > 2 * kap * np.sqrt(ua ** 2 + ub ** 2) for d, ua, ub in trip]
    out["forte_vs_pp"] = dict(singers=len(sep), told_apart=int(np.sum(sep)), told_apart_with_kappa=int(np.sum(sepk)),
                              forte_higher=int(np.sum(np.array(diffs) > 0)), median_diff_dB=float(np.median(diffs)),
                              min_abs_diff_dB=float(np.min(np.abs(diffs))))
    return out


def main():
    fr, U = frame_tests()
    for k, v in fr["pooled_cross_validated"].items():
        print("frame", k, {a: (round(b, 4) if isinstance(b, float) else b) for a, b in v.items()})
    print("u tables", fr["tables"])
    rows = measures(U)
    mt = measure_tests(rows)
    for name, r in mt.items():
        print(name, "c", r["c_fit"], "truth", r["truth_range"])
        for c in ALL_CONDS[:-1]:
            sh = r["split_half"][c]
            print("  ", c, "block", r["block"][c], "take", r["take"][c], "split", sh["takes"], sh["false_change_share"], "kappa", sh["kappa"])
    tt = tone_tests()
    for c, v in tt.items():
        print("tone", c, v)
    (T.OUT / "r2_results.json").write_text(json.dumps(dict(frames=fr, measures=mt, tone=tt), indent=1))


if __name__ == "__main__":
    main()
