"""E-002 round 3, part A: candidate fixes for YIN's octave-high errors on real
voices (squillo F-029), compared against round 2's truth. Crude experiment
code. Needs data/cache/r2/*.npz (r2_truth.py) and results/fold2.json.

    uv run python r3_octave.py check   # S15: the variants on known inputs (seconds)
    uv run python r3_octave.py         # writes data/cache/r3_octave.npz and results/r3_octave.json

Every variant is causal: a frame's pitch uses its own 1536-sample window and,
for the continuity rule, the pitches already reported for earlier frames,
never a later sample (squillo ADR 0007: a frame's value is final when
computed). Each starts from round 1's tracker (yin.py: threshold 0.1, lags
16..764, the first dip under the threshold followed down to its local
minimum, parabolic interpolation on d) and may replace its lag t by the
deepest CMND dip t2 within 2t - 3 .. 2t + 3 (round 2's `octave_check`
window), when t2 is an interior local minimum there and below the lag
range's end. Then the acceptance is round 1's (E2..C6 widened by 3 cents).

Variants, written down before running:

- base-0.1: the tracker as squillo ADR 0007 records it (E-002's parameters).
- base-0.05: threshold 0.05 (round 2 result 18).
- sub(a, d): a subharmonic check in the CMND. Take t2 when D(t) >= d and
  D(t2) < a * D(t), D the depth of the parabola through d' at the lag and
  its two neighbours (its vertex, at least 0). a in {0.05, 0.1, 0.2, 0.5},
  d in {0.005, 0.01, 0.02}. d keeps a periodic window, whose D(t) and D(t2)
  are both near 0, from switching on noise in the ratio (round 2's
  octave_check, a = 1, d = 0, on d' itself, made 9 % octave-low errors).
  A first form compared d' at the whole-sample lags, with d in {0.001 ..
  0.01}: it failed its must-pass check, halving round 1's harmonic tones
  (up to 1464 of 5490 frames, `saw6`), because d' at a whole-sample lag
  grows with the lag's distance from the period, so the two dips are not
  comparable. At the vertex, round 1's tones give D(t) at most 0.008.
- spec(b): a subharmonic check in the spectrum. From the window's Hann
  spectrum (8192-point FFT), the power at the odd multiples of f/2 against
  the power at the multiples of f, f the reported pitch, each partial's
  power the largest bin within f/8 of it, multiples up to 4 kHz. Take t2
  when the odd-to-even ratio exceeds b dB, b in {-30, -25, -20, -15, -10},
  and f/2 is at least 125 Hz, the Hann window's main-lobe width at 1536
  samples (4 SR / 1536), so a partial at f reaches f/2's band only through
  its side lobes (at most -31.5 dB). A first form without that bound read
  round 1's correct harmonic tones at -5 dB near E2 (leakage).
  A pitch read at twice the true f0 has partials at the odd multiples of
  f/2 (the true odd harmonics); a correct pitch has none there.
- cont: a continuity rule. The reference is the median of the pitches
  reported (after acceptance) for the previous 31 frames (0.25 s, squillo
  metrics MT-009's first-median span), when at least 16 of them have one.
  Take t2 when the frame's pitch is 1100 to 1300 cents above the reference
  (round 2's octave-high class, |error - 1200| < 100) and d'(t2) < 0.1.
- cont+sub(a, d), cont+spec(b): either switch.

Conditions evaluated: the clean re-synthesis against its truth, the original
takes against Harvest's f0 (two trackers, not a truth: attributed below as
round 2 did), white noise at 20 and 10 dB SNR and pink noise at 10 dB (round
2's generator, r2_run.condition, same seeds). Valid frames, SG-007's instant
and the error as round 2 (r2_run.frame_truth). Gross: |error| > 50 cents;
octave-high: |error - 1200| < 100; octave-low: |error + 1200| < 100.

Fitting: each parameterised family's parameters are chosen on one fold of
singers (round 2's parity folds) and tested on the other, both ways. The
criterion, written before running: the smallest mean of the gross shares
of measured frames on `clean` and `original`, among parameters that keep
the measured share of valid frames on both within 1 point of base-0.1's on
the fitting fold, and pass every must-pass case of `check()`. Then with squillo metrics MT-003's table (read from
results/fold2.json, `measures.spec.table`), per variant: the share of valid frames
accepted, the coverage of +-2u among accepted frames, the gross share of
accepted frames.
"""
import json
import sys
import zlib
from multiprocessing import Pool

import numpy as np

import r2_run as R
import r2_truth as T
import yin
from yin import SR, E2, C6

CONDS = ["clean", "original", "white-20", "white-10", "pink-10"]
ALPHAS = [0.05, 0.1, 0.2, 0.5]
DELTAS = [0.005, 0.01, 0.02]
BETAS = [-30.0, -25.0, -20.0, -15.0, -10.0]
MAINLOBE = 4 * SR / 1536  # Hz, Hann main-lobe full width at the pitch window
TAU_MIN = int(np.floor(SR / 3000.0))
TAU_MAX = int(np.ceil(SR / 63.0)) + 1
REF_N, REF_MIN = 31, 16
BINS = [0.0, 0.0025, 0.005, 0.01, 0.02, 0.03, 0.05, 0.07, 0.1]
FOLD2 = json.loads((T.OUT / "fold2.json").read_text())


def spec_table():
    t = FOLD2["measures"]["spec"]["table"]
    return np.array([np.inf if x is None else x for x in t])


def u_of(dip, table):
    k = np.clip(np.searchsorted(BINS, dip, side="right") - 1, 0, len(table) - 1)
    return table[k]


def variants():
    v = ["base-0.1", "base-0.05", "cont"]
    v += [f"sub({a},{d})" for a in ALPHAS for d in DELTAS]
    v += [f"spec({b:g})" for b in BETAS]
    v += ["cont+" + x for x in v[3:]]
    return v


VARIANTS = variants()


def pick(dn_row, thr):
    below = np.nonzero(dn_row[TAU_MIN:TAU_MAX] < thr)[0]
    if len(below) == 0:
        return -1
    t = TAU_MIN + below[0]
    while t + 1 < TAU_MAX and dn_row[t + 1] < dn_row[t]:
        t += 1
    return t


def f_at(d_row, t):
    if t <= TAU_MIN or t >= TAU_MAX - 1:
        return np.nan
    return SR / yin.parabola(d_row, t)


def depth(row, t):
    """Vertex of the parabola through d' at t - 1, t, t + 1, at least 0 (d'(t) if it opens down)."""
    a, b, c = row[t - 1], row[t], row[t + 1]
    den = a - 2 * b + c
    return max(b - (a - c) ** 2 / (8 * den), 0.0) if den > 0 else b


def odd_even_db(win, f):
    """Power at odd multiples of f/2 against multiples of f (dB), from the Hann spectrum."""
    X = np.abs(np.fft.rfft(win * np.hanning(len(win)), 8192)) ** 2
    fr = np.fft.rfftfreq(8192, 1 / SR)
    df = fr[1]

    def pw(hz):
        lo, hi = int(np.ceil((hz - f / 8) / df)), int(np.floor((hz + f / 8) / df))
        return X[max(lo, 0):hi + 1].max()
    odd = [pw((2 * k - 1) * f / 2) for k in range(1, 64) if (2 * k - 1) * f / 2 <= 4000]
    even = [pw(k * f) for k in range(1, 64) if k * f <= 4000]
    if not odd or not even:
        return -np.inf
    return 10 * np.log10(sum(odd) / sum(even) + 1e-30)


def frame_candidates(x):
    """Per frame: base-0.1's lag, pitch and dip; the doubled-lag candidate; the odd-even ratio;
    base-0.05's pitch and dip."""
    idx, win = yin.frame_windows(np.asarray(x, np.float64))
    d, dn = yin.cmnd(win, TAU_MAX)
    n = len(idx)
    out = {k: np.full(n, np.nan) for k in ("f", "dip", "f2", "dip2", "D", "D2", "oe", "f05", "dip05")}
    for k in range(n):
        row = dn[k]
        t = pick(row, 0.1)
        if t < 0:
            out["dip"][k] = row[TAU_MIN:TAU_MAX].min()
        else:
            out["dip"][k] = row[t]
            out["f"][k] = f_at(d[k], t)
            lo2, hi2 = 2 * t - 3, min(2 * t + 4, TAU_MAX - 1)
            if lo2 < hi2:
                t2 = lo2 + int(np.argmin(row[lo2:hi2]))
                if lo2 < t2 < hi2 - 1:
                    out["dip2"][k] = row[t2]
                    out["D"][k], out["D2"][k] = depth(row, t), depth(row, t2)
                    out["f2"][k] = f_at(d[k], t2)
            if np.isfinite(out["f"][k]):
                out["oe"][k] = odd_even_db(win[k], out["f"][k])
        t5 = pick(row, 0.05)
        if t5 < 0:
            out["dip05"][k] = row[TAU_MIN:TAU_MAX].min()
        else:
            out["dip05"][k] = row[t5]
            out["f05"][k] = f_at(d[k], t5)
    return idx, out


def accept(f):
    return yin.in_range(f, 3.0)


def switch_rule(name, c):
    has2 = np.isfinite(c["f2"])
    if name.startswith("sub("):
        a, dd = (float(s) for s in name[4:-1].split(","))
        return has2 & (c["D"] >= dd) & (c["D2"] < a * c["D"])
    if name.startswith("spec("):
        b = float(name[5:-1])
        return has2 & (c["oe"] > b) & (c["f"] / 2 >= MAINLOBE)
    raise ValueError(name)


def run_variant(name, c):
    """(f accepted or nan, dip at the chosen lag) per frame."""
    if name == "base-0.1":
        return accept(c["f"]), c["dip"]
    if name == "base-0.05":
        return accept(c["f05"]), c["dip05"]
    cont = name.startswith("cont")
    rest = name[5:] if name.startswith("cont+") else ("" if name == "cont" else name)
    sw = switch_rule(rest, c) if rest else np.zeros(len(c["f"]), bool)
    f = np.where(sw, c["f2"], c["f"])
    dip = np.where(sw, c["dip2"], c["dip"])
    if not cont:
        return accept(f), dip
    out_f = np.full(len(f), np.nan)
    out_d = dip.copy()
    has2 = np.isfinite(c["f2"]) & (c["dip2"] < 0.1)
    lo, hi = 2 ** (1100 / 1200), 2 ** (1300 / 1200)
    hist = []
    for k in range(len(f)):
        fk = f[k]
        if not sw[k] and has2[k] and np.isfinite(fk):
            prev = [h for h in hist[-REF_N:] if h == h]
            if len(prev) >= REF_MIN:
                r = fk / np.median(prev)
                if lo <= r <= hi:
                    fk = c["f2"][k]; out_d[k] = c["dip2"][k]
        fa = fk if (np.isfinite(fk) and E2 * 2 ** (-3 / 1200) <= fk <= C6 * 2 ** (3 / 1200)) else np.nan
        out_f[k] = fa
        hist.append(fa)
    return out_f, out_d


def one(path):
    z = np.load(T.R2 / (path.stem + ".npz"))
    x, y = z["x"].astype(np.float64), z["y"].astype(np.float64)
    ft = T.truth_per_sample(z["f0"], len(x))
    voiced = ft > 0
    res = {}
    for cond in CONDS:
        base = x if cond == "original" else y
        sig, _ = R.condition(base, voiced, path.stem, cond)
        idx, c = frame_candidates(sig)
        per = {}
        for v in VARIANTS:
            f, dip = run_variant(v, c)
            f_true, _, valid = R.frame_truth(ft, idx, f)
            per[v] = (f, dip, f_true)
        res[cond] = dict(idx=idx, valid=valid, oe=c["oe"], per=per)
    return path.stem, res


# ------------------------------------------------------------------ S15 checks
def check():
    """Each variant on inputs whose answer is known without it. Must pass: squillo's eleven
    signal fixtures (every variant reports what base-0.1 reports) and round 1's steady harmonic
    tones E2..C6 (no gross error). Must fail for base-0.1: tones built to be read an octave high.
    Round 1's `saw12` (run.py's spectrum()) at 350 Hz (round 2 result 17: men's /a/ at a median
    351 Hz) with H1 26 dB under H2 (result 17's p10, 25.7 dB, rounded to the far side) and every
    other odd harmonic 10 or 20 dB under its level there. Explored before fixing the case: with
    H1 alone 20 to 40 dB under H2 base-0.1 never read 175 to 440 Hz tones an octave high; with the
    odd harmonics also 10 dB down it did in every frame."""
    import soundfile as sf
    from pathlib import Path
    fx = sorted((Path(__file__).parents[3] / "squillo" / "fixtures" / "signal").glob("*.wav"))
    assert len(fx) == 11, fx
    out = {"fixtures": {}, "harmonic": {}, "weak_h1": {}}
    for p in fx:
        x, sr = sf.read(p); assert sr == SR
        _, c = frame_candidates(x)
        f0, _ = run_variant("base-0.1", c)
        diff = {}
        for v in VARIANTS:
            f, _ = run_variant(v, c)
            same = np.array_equal(np.isnan(f), np.isnan(f0)) and np.allclose(f[~np.isnan(f)], f0[~np.isnan(f0)], rtol=0, atol=1e-9)
            if not same:
                diff[v] = int(np.sum(~((np.isnan(f) & np.isnan(f0)) | (np.abs(f - f0) <= 1e-9))))
        out["fixtures"][p.name] = diff
    # round 1's steady harmonic timbres, from run.py's own spectrum() and render() (run.py lines 41-67)
    import run as R1
    rng = np.random.default_rng(20260929)
    t1 = np.ones(SR)
    for name in ("saw6", "saw12", "weakf0"):
        g = {v: 0 for v in VARIANTS}; n = 0
        for s in range(-29, 16):  # E2..C6, semitones re A4
            f0 = 440 * 2 ** (s / 12)
            sp = R1.spectrum(name, f0)
            _, c = frame_candidates(R1.render(f0 * t1, sp, rng.uniform(0, 2 * np.pi, len(sp))))
            for v in VARIANTS:
                f, _ = run_variant(v, c)
                e = 1200 * np.log2(f[~np.isnan(f)] / f0)
                g[v] += int(np.sum(np.abs(e) > 50))
            n += len(c["f"])
        out["harmonic"][name] = dict(frames=n, gross_by_variant={v: k for v, k in g.items() if k})
    for odd_db in (10, 20):
        sp = R1.spectrum("saw12", 350.0).copy()
        sp[0] = sp[1] * 10 ** (-26 / 20)
        sp[2::2] *= 10 ** (-odd_db / 20)
        _, c = frame_candidates(R1.render(350.0 * np.ones(2 * SR), sp, rng.uniform(0, 2 * np.pi, len(sp))))
        for v in VARIANTS:
            f, dip = run_variant(v, c)
            e = 1200 * np.log2(f[~np.isnan(f)] / 350.0)
            u = u_of(dip[~np.isnan(f)], spec_table())
            out["weak_h1"][f"odd -{odd_db} dB | {v}"] = dict(measured=int(len(e)), octave_high=int(np.sum(np.abs(e - 1200) < 100)),
                                                            correct=int(np.sum(np.abs(e) <= 50)),
                                                            refused_by_mt003=int(np.sum(~np.isfinite(u))),
                                                            octave_high_accepted=int(np.sum((np.abs(e - 1200) < 100) & np.isfinite(u))))
        base = out["weak_h1"][f"odd -{odd_db} dB | base-0.1"]
        assert base["octave_high"] == base["measured"] > 0, ("must-fail case not failed by base-0.1", base)
    # the octave classes themselves, on errors known by construction
    e = np.array([0.0, 1200.0, -1200.0, 1150.0, 60.0])
    assert list(np.abs(e - 1200) < 100) == [False, True, False, True, False]
    assert list(np.abs(e + 1200) < 100) == [False, False, True, False, False]
    bad = set(v for d in out["fixtures"].values() for v in d)
    bad |= set(v for h in out["harmonic"].values() for v in h["gross_by_variant"])
    out["fails_must_pass"] = sorted(bad)
    print("variants failing a must-pass case:", out["fails_must_pass"])
    return out


# ------------------------------------------------------------------ analysis
def load_all():
    import r2_analyse as A
    fold = A.FOLD
    res = Pool(16).map(one, T.files())
    names = [r[0] for r in res]
    assert names == [p.stem for p in T.files()]
    # reproduction check: base-0.1 on clean and original equals round 2's cached frames
    for cond in ("clean", "original", "white-20"):
        f_cached = A.Z[cond + "/f"]
        f_new = np.concatenate([r[1][cond]["per"]["base-0.1"][0] for r in res])
        assert np.array_equal(np.isnan(f_cached), np.isnan(f_new)) and np.allclose(f_cached[~np.isnan(f_cached)], f_new[~np.isnan(f_new)], atol=1e-9), cond
    return res, fold, np.array([T.set_of(n) for n in names]), np.array([T.singer_of(n).startswith("male") for n in names])


def stats(res, cond, v, files, table):
    valid_n = meas = gross = oh = ol = acc = cov = gacc = 0
    ne = []
    for k in files:
        r = res[k][1][cond]
        f, dip, ft = r["per"][v]
        va = r["valid"]
        ok = va & ~np.isnan(f)
        e = 1200 * np.log2(f[ok] / ft[ok])
        valid_n += int(va.sum()); meas += int(ok.sum())
        gross += int(np.sum(np.abs(e) > 50)); oh += int(np.sum(np.abs(e - 1200) < 100)); ol += int(np.sum(np.abs(e + 1200) < 100))
        ne.append(np.abs(e[np.abs(e) <= 50]))
        u = u_of(dip[ok], table)
        a = np.isfinite(u)
        acc += int(a.sum()); cov += int(np.sum(np.abs(e[a]) <= 2 * u[a])); gacc += int(np.sum(np.abs(e[a]) > 50))
    ne = np.concatenate(ne) if ne else np.zeros(0)
    return dict(valid=valid_n, measured_share=meas / valid_n, gross_share=gross / max(meas, 1),
                octave_high_share=oh / max(meas, 1), octave_low_share=ol / max(meas, 1),
                p95_abs_non_gross=float(np.percentile(ne, 95)) if len(ne) else None,
                accepted_share=acc / valid_n, coverage_k2=cov / max(acc, 1), gross_share_accepted=gacc / max(acc, 1))


def family(v):
    if v.startswith("cont+sub"):
        return "cont+sub"
    if v.startswith("cont+spec"):
        return "cont+spec"
    for p in ("sub", "spec"):
        if v.startswith(p):
            return p
    return v


def attribute(res, v, n_sample=300):
    """S17, as round 2: where the variant reads an original take an octave below Harvest, is there a
    partial at the variant's pitch (level >= 10 dB over the level at 1.5 times it)? If so Harvest
    missed the voice's f0; if not the variant is wrong."""
    rows = []
    for k, (name, r) in enumerate(res):
        o = r["original"]
        f, _, ft = o["per"][v]
        ok = o["valid"] & ~np.isnan(f)
        e = np.full(len(f), np.nan); e[ok] = 1200 * np.log2(f[ok] / ft[ok])
        for i in np.nonzero(np.abs(e + 1200) < 100)[0]:
            rows.append((k, i, f[i]))
    if not rows:
        return dict(octave_low_frames=0)
    sel = np.random.default_rng(20260929).choice(len(rows), min(n_sample, len(rows)), replace=False)
    fr = np.fft.rfftfreq(16384, 1 / SR)
    cache, partial = {}, []
    for j in sel:
        k, i, f = rows[j]
        name = res[k][0]
        if name not in cache:
            cache[name] = np.load(T.R2 / (name + ".npz"))["x"].astype(np.float64)
        a = 384 * (res[k][1]["original"]["idx"][i] - 3)
        X = np.abs(np.fft.rfft(cache[name][a:a + 1536] * np.hanning(1536), 16384))

        def lvl(hz):
            m = (fr > hz * 0.97) & (fr < hz * 1.03)
            return 20 * np.log10(X[m].max() + 1e-12)
        partial.append(lvl(f) - lvl(1.5 * f) >= 10)
    return dict(octave_low_frames=len(rows), sampled=int(len(sel)), partial_at_variant_pitch=int(np.sum(partial)))


def main():
    if sys.argv[1:] == ["check"]:
        chk = check()
        T.OUT.joinpath("r3_octave_check.json").write_text(json.dumps(chk, indent=1))
        return
    chk = check()
    table = spec_table()
    res, fold, sets, male = load_all()
    files_by_fold = {f: [k for k in range(len(res)) if fold[k] == f] for f in (1, 0)}
    allk = list(range(len(res)))
    out = {"check": chk, "table": [None if not np.isfinite(x) else float(x) for x in table],
           "fit": {}, "held_out": {}, "all_singers": {}}
    # fit each family on one fold, test on the other
    fams = {}
    for v in VARIANTS:
        fams.setdefault(family(v), []).append(v)
    for fit_fold in (1, 0):
        fk, tk = files_by_fold[fit_fold], files_by_fold[1 - fit_fold]
        base = {c: stats(res, c, "base-0.1", fk, table) for c in ("clean", "original")}
        chosen = {}
        for fam, vs in fams.items():
            best = None
            for v in vs:
                if v in chk["fails_must_pass"]:
                    continue
                s = {c: stats(res, c, v, fk, table) for c in ("clean", "original")}
                if any(s[c]["measured_share"] < base[c]["measured_share"] - 0.01 for c in s):
                    continue
                score = (s["clean"]["gross_share"] + s["original"]["gross_share"]) / 2
                if best is None or score < best[0]:
                    best = (score, v)
            chosen[fam] = best[1] if best else None
        key = f"fit on {'odd' if fit_fold else 'even'}, test on {'even' if fit_fold else 'odd'}"
        out["fit"][key] = chosen
        out["held_out"][key] = {fam: ({c: stats(res, c, v, tk, table) for c in CONDS} if v else None)
                                for fam, v in chosen.items()}
        # base-0.05 kept for comparison even when it fails the measured-share criterion
        out["held_out"][key]["base-0.05 (unconstrained)"] = {c: stats(res, c, "base-0.05", tk, table) for c in CONDS}
    # every variant on all singers, clean and original, for the README's tables
    for v in VARIANTS:
        out["all_singers"][v] = {c: stats(res, c, v, allk, table) for c in CONDS}
    # where the errors were: forte and straight long tones, men
    out["by_group"] = {}
    for v in ["base-0.1"] + sorted({x for d in out["fit"].values() for x in d.values() if x}):
        for g, ks in (("LT-forte", [k for k in allk if sets[k] == "LT-forte"]),
                      ("LT-straight", [k for k in allk if sets[k] == "LT-straight"]),
                      ("men", [k for k in allk if male[k]]), ("women", [k for k in allk if not male[k]])):
            out["by_group"][f"{v} | {g}"] = {c: stats(res, c, v, ks, table) for c in ("clean", "original")}
    out["attribution"] = {v: attribute(res, v) for v in ["base-0.1", "base-0.05"] + sorted({x for d in out["fit"].values() for x in d.values() if x})}
    T.OUT.joinpath("r3_octave.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out["fit"], indent=1))
    for key, d in out["held_out"].items():
        print(key)
        for fam, s in d.items():
            if s:
                print(f"  {fam:28s}", {c: (round(s[c]['measured_share'], 4), round(s[c]['gross_share'], 4), round(s[c]['octave_high_share'], 4), round(s[c]['octave_low_share'], 4), round(s[c]['accepted_share'], 4), round(s[c]['coverage_k2'], 4)) for c in ("clean", "original")})
    print(json.dumps(out["attribution"], indent=1))


if __name__ == "__main__":
    main()
