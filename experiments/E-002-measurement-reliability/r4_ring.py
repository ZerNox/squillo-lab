"""E-002 round 4: the ring ratio on repeated material, with a noise gate
(squillo iteration 49; finding F-036). Crude experiment code.

    uv run python r4_ring.py check     # synthetic checks of the checks; writes results/r4_check.json
    uv run python r4_ring.py time      # S19: time a sample at the pool; prints the estimate
    uv run python r4_ring.py run       # per take and condition: note occurrences; data/cache/r4_occ.pkl
    uv run python r4_ring.py analyse   # fits and tests; writes results/r4_ring.json

Round 2 (results 24, 25) found that the ring ratio moves with the notes
sung, so the halves of one take were called changed in 28.5 % of takes, and
that noise biases it. Round 4 asks whether comparing two renditions **note
by note, on the notes both sing** makes it a measure squillo can compare,
and whether a gate read from the take itself keeps noise from calling a
change. Everything below was written, and committed, before the run
(squillo S15, L-041).

Inputs. Round 2's 159 VocalSet 1.1 originals (CC BY 4.0; data/SOURCES.md),
resampled to 48 kHz, read as r2_run.py line 147 reads them (`z["x"]` from
data/cache/r2/<stem>.npz). Noise: r2_run.condition (lines 97-110) on the
original with round 2's seeds, so every noisy signal is round 2's tone
condition sample for sample (white 30, 20, 10 dB, pink 20, 10 dB SNR against
the take's voiced RMS; SNR asserted within 0.01 dB there, pink's slope
within 0.5 dB per decade).

Definitions.

- Frames: YIN as round 2 (yin.yin, threshold 0.1; yin.in_range(f, 3.0)),
  the pitch window of frame i being samples 384 (i - 3) .. + 1536
  (r2_run.py line 137). A frame's band powers: the Hann-windowed power
  spectrum of its pitch window summed over bins whose centre lies in
  50 Hz-2 kHz (lo) and 2-4 kHz (hi), r2_run.py lines 48, 130-131.
- Note of a frame: its pitch in cents re A4 smoothed by a centred running
  median over 25 frames (200 ms, one vibrato cycle at 5 Hz) of the accepted
  frames, needing 13 accepted in the window; the take's tuning is the
  circular mean of the smoothed cents modulo 100; note = round((cs - tuning)
  / 100).
- Occurrence: a maximal run of consecutive frames with the same note, at
  least 37 frames long, trimmed by 6 frames at each end (48 ms: the pitch
  window spans 4 frames, so a trimmed frame's window holds one note), so at
  least 25 frames (0.2 s) are kept.
- Noise estimate of a take: the median per-frame lo and hi band power over
  the 10 % of all its frames with the lowest total power (50 Hz-24 kHz),
  voiced or not. Where the take has no quiet stretch this over-estimates the
  noise, so the gate errs towards refusing.
- A side (half of a take, or a whole take) per note: the sums of lo and hi
  band power over every kept frame of its occurrences of that note, and the
  frame count n. Ring ratio of a note: 10 log10(sum hi / sum lo), dB.
  Its hi-band SNR: 10 log10((sum hi / n - N_hi) / N_hi), refused where the
  difference is not positive.
- Variants. V0: no gate. V1(g): a note of a side counts only if its hi-band
  SNR is at least g dB. V2(g): V1, and the noise estimate is subtracted from
  both sums before the ratio, sum - n N (refused where either is not
  positive).
- Halves: split at the median frame index of the clean take's kept
  occurrence frames; an occurrence belongs to the half holding its centre
  frame. The noisy take uses the clean take's split.
- Comparison of sides A and B: shared notes are those both sides count;
  k their number; d_n = ring_B(n) - ring_A(n); D = mean d_n. Not comparable
  when k = 0.
- The ± model, a one-way random-effects model (d_n = Delta + e_pair + e_n),
  fitted on clean no-change pairs (a take's two halves) of one fold:
  sigma_w^2 = the pooled within-pair variance of d_n (pairs with k >= 2),
  tau^2 = max(0, mean over pairs of D^2 - sigma_w^2 mean(1/k)) (no change,
  so Delta = 0). u(D) = sqrt(tau^2 + sigma_w^2 / k). Called changed when
  |D| > 2 u (coverage factor 2, GUM 6.3.3).
- Folds: singers split by their number's parity (round 2's split); every fit
  on one fold is tested on the other, both ways, and pooled.
- Unmatched reference, on the same takes: round 2's own test recomputed
  (1 s blocks from r2_tone.json's clean condition, first against second half
  of the blocks, at least 4, called changed at 2 sqrt(ua^2 + ub^2)); and at
  note level, D_un = ring over all kept frames of B minus of A, whose RMS
  over no-change pairs is set against the matched D's.

Tests and bars.

- B1, repeated material: on the test folds, the matched comparison's false
  change on clean no-change pairs is at most 5 % (the rate a coverage factor
  of 2 is meant to give), pooled over both folds; Wilson 95 % interval and
  the share by set reported.
- B1's own check: applied to the fitting fold's clean pairs (must pass) and
  to the same halves with half B's 2-4 kHz band raised by 6.02 dB (an FFT
  gain of 2 in amplitude on bins in [2000, 4000) Hz, spliced in at the
  split's sample) on the test fold (must fail: false change above 5 %).
- Sensitivity, no bar, reported: forte against pp long tones and straight
  against breathy scales, the same singer, whole take against whole take,
  with the other fold's fit: comparable pairs, called changed, the sign.
- B3, the gate: for V1 and V2, g is the smallest of 0, 3, 6, 10, 15, 20, 25,
  30 dB for which, on the fitting fold, false change is at most 5 % in every
  noise condition, comparing each noisy half with the other half clean
  (both directions, pooled; the same g gates both sides); a condition with
  fewer than 20 comparable pairs on the fitting fold passes (nothing would be
  shown). On the test fold, with that g: false change and comparable share
  per condition, clean included. B3 passes for a variant if every noise
  condition with at least 20 comparable pairs is at most 5 %. Recommended:
  the passing variant with more comparable pairs at white 20 dB; a tie goes
  to V1, the simpler.
- B3's own check: V0 (no gate) at white 10 dB on the fitting fold must fail
  (round 2's result 25 called 38.8 % changed there, found before this rule).
  Must pass: the chosen g at clean on the fitting fold.

Synthetic check of the pipeline (`check`), before any real take is read.
A harmonic take, 48 kHz, 0.5 s per note, harmonics to 8 kHz with a fixed
envelope A(f) = exp(-f / 1500) (1 + 3 exp(-((f - 2800) / 400)^2)), so the
ring ratio depends on the note. Notes: equal-tempered at A4 = 440 Hz between
C4 and C6 whose every harmonic lies at least 3 bins (93.75 Hz) from 50,
2000 and 4000 Hz, asserted on the generated f0s; at least 8 needed. Half A
sings the first five, half B the fourth to the eighth, so two notes are
shared. S0: B's envelope as A's. S1: B's harmonics in [2000, 4000) Hz
doubled in amplitude. The expected ring of each note is computed from its
harmonic amplitudes (sum of A^2 by band, the Hann window's power gain
common to both bands). Bound: epsilon, the largest share of a Hann window's
power (1536 points, transform on a grid of 1/64 bin) that falls 3 bins or
more from its peak over sub-bin offsets, computed from the window; a note's
ring may err by at most 10 log10((1 + eps P_other / P_band) / (1 - eps)) in
each band, both bands' errors added. The unmatched expectation pools the
notes' sums weighted by the kept frames each note has in the side. Must pass: S0's per-note rings within
the bound of expected, matched D within twice the bound of 0, the unmatched
D within twice the largest bound of the eight notes of its expected value, which must be further than
that from 0 (the note dependence exists in the input). Must fail for "no
change": S1's matched D within twice the bound of 20 log10(2) and further
than twice the bound from 0.
"""

import json
import pickle
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

import r2_run as R
import r2_truth as T
import yin
from yin import SR, E2, C6

HERE = Path(__file__).parent
OUT = HERE / "results"
OCC = T.CACHE / "r4_occ.pkl"
NOISE = ["white-30", "white-20", "white-10", "pink-20", "pink-10"]
GRID = [0, 3, 6, 10, 15, 20, 25, 30]
MED, MED_MIN, RUN_MIN, TRIM = 25, 13, 37, 6
QUIET = 0.10
POOL = 16
FR = np.fft.rfftfreq(yin.WIN, 1 / SR)
LO = (FR >= R.RING_LO[0]) & (FR < R.RING_LO[1])
HI = (FR >= R.RING_HI[0]) & (FR < R.RING_HI[1])
ALL = FR >= R.RING_LO[0]
HANN = np.hanning(yin.WIN)


# ------------------------------------------------------------ frames and notes
def frame_powers(sig, idx):
    s = yin.HOP * (idx - 3)
    W = np.stack([sig[a:a + yin.WIN] for a in s]) * HANN
    P = np.abs(np.fft.rfft(W, axis=1)) ** 2
    return P[:, LO].sum(1), P[:, HI].sum(1), P[:, ALL].sum(1)


def notes_of(f):
    c = np.where(np.isnan(f), np.nan, 1200 * np.log2(np.where(np.isnan(f), 1.0, f) / 440.0))
    n = len(c)
    cs = np.full(n, np.nan)
    h = MED // 2
    for k in range(n):
        if np.isnan(c[k]):
            continue
        w = c[max(0, k - h):k + h + 1]
        if np.count_nonzero(~np.isnan(w)) >= MED_MIN:
            cs[k] = np.nanmedian(w)
    ok = ~np.isnan(cs)
    if not ok.any():
        return np.full(n, np.nan), None
    tun = float(np.angle(np.mean(np.exp(2j * np.pi * cs[ok] / 100))) / (2 * np.pi) * 100)
    note = np.full(n, np.nan)
    note[ok] = np.round((cs[ok] - tun) / 100)
    return note, tun


def occurrences(note, idx, plo, phi):
    """Runs of one note >= RUN_MIN frames (consecutive frame indices), trimmed TRIM each end."""
    out = []
    n = len(note)
    s = 0
    for i in range(1, n + 1):
        if i == n or note[i] != note[s] or np.isnan(note[i]) or idx[i] != idx[i - 1] + 1:
            if not np.isnan(note[s]) and i - s >= RUN_MIN:
                a, b = s + TRIM, i - TRIM
                out.append(dict(note=int(note[s]), i0=int(idx[a]), i1=int(idx[b - 1]), n=b - a,
                                lo=float(plo[a:b].sum()), hi=float(phi[a:b].sum())))
            s = i
    return out


def analyse_signal(sig):
    idx, f, _ = yin.yin(sig)
    f = yin.in_range(f, 3.0)
    plo, phi, pall = frame_powers(sig, idx)
    note, tun = notes_of(f)
    occ = occurrences(note, idx, plo, phi)
    q = pall <= np.quantile(pall, QUIET)
    return dict(occ=occ, tuning=tun, N_lo=float(np.median(plo[q])), N_hi=float(np.median(phi[q])),
                quiet_accepted_share=float(np.mean(~np.isnan(f[q]))), frames=int(len(idx)))


def split_of(a):
    fr = np.concatenate([np.arange(o["i0"], o["i1"] + 1) for o in a["occ"]]) if a["occ"] else np.array([0])
    return float(np.median(fr))


def boost_hi(x):
    X = np.fft.rfft(x)
    fr = np.fft.rfftfreq(len(x), 1 / SR)
    X[(fr >= R.RING_HI[0]) & (fr < R.RING_HI[1])] *= 2.0
    return np.fft.irfft(X, len(x))


def one(path):
    z = np.load(T.R2 / (path.stem + ".npz"))
    x, f0 = z["x"].astype(np.float64), z["f0"]
    voiced = T.truth_per_sample(f0, len(x)) > 0
    res = {"clean": analyse_signal(x)}
    sp = split_of(res["clean"])
    res["split"] = sp
    cut = int(yin.HOP * (sp - 3) + yin.WIN)  # the split frame's window end: later frames' windows start past it
    xb = np.concatenate([x[:cut], boost_hi(x)[cut:]])
    res["boost"] = analyse_signal(xb)
    for c in NOISE:
        sig, info = R.condition(x, voiced, path.stem, c)
        res[c] = analyse_signal(sig)
        res[c]["cond_info"] = info
    return path.stem, res


# ------------------------------------------------------------ comparison
def side(a, which=None, split=None):
    """Per note: [sum lo, sum hi, n] over the occurrences of one half (0, 1) or all (None)."""
    d = {}
    for o in a["occ"]:
        if which is not None:
            h = 0 if (o["i0"] + o["i1"]) / 2 < split else 1
            if h != which:
                continue
        s = d.setdefault(o["note"], [0.0, 0.0, 0])
        s[0] += o["lo"]; s[1] += o["hi"]; s[2] += o["n"]
    return dict(notes=d, N_lo=a["N_lo"], N_hi=a["N_hi"])


def rings(sd, variant, g):
    out = {}
    for nt, (lo, hi, n) in sd["notes"].items():
        if variant != "V0":
            ex = hi / n - sd["N_hi"]
            if ex <= 0 or 10 * np.log10(ex / sd["N_hi"]) < g:
                continue
        if variant == "V2":
            lo, hi = lo - n * sd["N_lo"], hi - n * sd["N_hi"]
            if lo <= 0 or hi <= 0:
                continue
        out[nt] = 10 * np.log10(hi / lo)
    return out


def compare(A, B, variant="V0", g=0):
    ra, rb = rings(A, variant, g), rings(B, variant, g)
    sh = sorted(set(ra) & set(rb))
    if not sh:
        return None
    d = np.array([rb[n] - ra[n] for n in sh])
    return dict(k=len(sh), D=float(d.mean()), d=d.tolist())


def unmatched(A, B):
    def r(sd):
        lo = sum(v[0] for v in sd["notes"].values()); hi = sum(v[1] for v in sd["notes"].values())
        return 10 * np.log10(hi / lo) if lo > 0 and hi > 0 else None
    a, b = r(A), r(B)
    return None if a is None or b is None else b - a


def fit(pairs):
    """pairs: list of compare() results (no change). Returns sigma_w, tau."""
    num = sum(float(np.sum((np.array(p["d"]) - p["D"]) ** 2)) for p in pairs if p["k"] >= 2)
    den = sum(p["k"] - 1 for p in pairs if p["k"] >= 2)
    sw2 = num / den
    tau2 = max(0.0, float(np.mean([p["D"] ** 2 for p in pairs])) - sw2 * float(np.mean([1 / p["k"] for p in pairs])))
    return float(np.sqrt(sw2)), float(np.sqrt(tau2))


def called(p, m):
    sw, tau = m
    return abs(p["D"]) > 2 * np.sqrt(tau ** 2 + sw ** 2 / p["k"])


def wilson(k, n, z=1.959964):
    if n == 0:
        return None
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [float(c - h), float(c + h)]


def share(flags):
    k, n = int(np.sum(flags)), len(flags)
    return dict(called=k, of=n, share=(k / n if n else None), wilson95=wilson(k, n))


# ------------------------------------------------------------ synthetic check
def hann_eps():
    """Largest share of the Hann window's power 3 bins or more from its peak, over sub-bin offsets:
    the window's transform on a grid of 1/64 bin, sampled at whole-bin steps from each of 64 offsets."""
    L, S = yin.WIN, 64
    W = np.abs(np.fft.fft(HANN, S * L)) ** 2  # W[j] at offset j / S bins (circular)
    q = np.arange(-L // 2, L // 2)
    worst = 0.0
    for j0 in range(S):
        pos = q + j0 / S  # offsets of the sampled bins from the peak, in bins
        vals = W[(S * q + j0) % (S * L)]
        worst = max(worst, float(vals[np.abs(pos) >= 3].sum() / vals.sum()))
    return worst


def envelope(f):
    return np.exp(-f / 1500) * (1 + 3 * np.exp(-((f - 2800) / 400) ** 2))


def synth_notes():
    ok = []
    for m in range(-9, 16):  # C4 .. C6 re A4
        f0 = 440 * 2 ** (m / 12)
        h = f0 * np.arange(1, int(8000 // f0) + 1)
        if all(np.min(np.abs(h - e)) >= 3 * SR / yin.WIN for e in (50.0, 2000.0, 4000.0)):
            ok.append(m)
    return ok


def synth_take(ms_a, ms_b, gain_b):
    out = []
    t = np.arange(int(0.5 * SR)) / SR
    for half, ms in ((0, ms_a), (1, ms_b)):
        for m in ms:
            f0 = 440 * 2 ** (m / 12)
            h = np.arange(1, int(8000 // f0) + 1)
            A = envelope(h * f0)
            if half == 1:
                A = A * np.where((h * f0 >= 2000) & (h * f0 < 4000), gain_b, 1.0)
            out.append((A[:, None] * np.sin(2 * np.pi * np.outer(h * f0, t))).sum(0))
    x = np.concatenate(out)
    return 0.05 * x / np.max(np.abs(x))


def expected_ring(m, gain):
    f0 = 440 * 2 ** (m / 12)
    h = f0 * np.arange(1, int(8000 // f0) + 1)
    A = envelope(h)
    hi = (h >= 2000) & (h < 4000)
    lo = (h >= 50) & (h < 2000)
    A = A * np.where(hi, gain, 1.0)
    return 10 * np.log10((A[hi] ** 2).sum() / (A[lo] ** 2).sum()), (A[hi] ** 2).sum(), (A[lo] ** 2).sum()


def check():
    eps = hann_eps()
    ms = synth_notes()
    assert len(ms) >= 8, ms
    ma, mb = ms[:5], ms[3:8]
    out = dict(eps=eps, notes=ms[:8], shared=ms[3:5])

    def bound(m, gain):
        _, phi, plo = expected_ring(m, gain)
        return float(10 * np.log10((1 + eps * plo / phi) / (1 - eps)) + 10 * np.log10((1 + eps * phi / plo) / (1 - eps)))

    for case, gain in (("S0", 1.0), ("S1", 2.0)):
        x = synth_take(ma, mb, gain)
        a = analyse_signal(x)
        sp = split_of(a)
        A, B = side(a, 0, sp), side(a, 1, sp)
        per = []
        for which, msx, gx, sd in ((0, ma, 1.0, A), (1, mb, gain, B)):
            rr = rings(sd, "V0", 0)
            # note numbers are relative to the take's tuning, which is 0 here within rounding
            assert sorted(rr) == sorted(msx), (case, which, sorted(rr), msx)
            for m in msx:
                e = expected_ring(m, gx)[0]
                b = bound(m, gx)
                per.append(dict(half=which, note=m, measured=rr[m], expected=e, bound=b, ok=bool(abs(rr[m] - e) <= b)))
        cm = compare(A, B)
        b2 = 2 * max(bound(m, g) for m in ms[3:5] for g in (1.0, gain))
        un = unmatched(A, B)
        # pooled sums weight each note by its kept frames, read from the sides; per-frame power is
        # proportional to the note's sum of A^2 (one amplitude scale for the whole take)
        def pooled(sd, msx, gx):
            hi = sum(sd["notes"][m][2] * expected_ring(m, gx)[1] for m in msx)
            lo = sum(sd["notes"][m][2] * expected_ring(m, gx)[2] for m in msx)
            return 10 * np.log10(hi / lo)
        un_exp = pooled(B, mb, gain) - pooled(A, ma, 1.0)
        nf = sorted({v[2] for v in A["notes"].values()} | {v[2] for v in B["notes"].values()})
        want = 0.0 if case == "S0" else 20 * np.log10(2.0)
        un_b = 2 * max(bound(m, g) for m in ms[:8] for g in (1.0, gain))
        res = dict(per_note=per, frames_per_note=nf, matched_D=cm["D"], matched_k=cm["k"], matched_bound=b2,
                   matched_want=want, unmatched_D=un, unmatched_expected=float(un_exp), unmatched_bound=un_b)
        assert all(p["ok"] for p in per), per
        assert cm["k"] == 2 and abs(cm["D"] - want) <= b2, res
        assert abs(un - un_exp) <= un_b, res
        if case == "S0":
            assert abs(un_exp) > un_b, res  # the note dependence is in the input
        else:
            assert abs(cm["D"]) > b2, res  # a real change is seen
        out[case] = res
    (OUT / "r4_check.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: (v if k in ("eps", "notes", "shared") else {kk: vv for kk, vv in v.items() if kk != "per_note"}) for k, v in out.items()}, indent=1))


# ------------------------------------------------------------ run and analyse
def timed(path):
    t0 = time.time()
    one(path)
    return time.time() - t0


def time_sample():
    fs = T.files()
    sample = fs[::16]  # every 16th file, spread over singers and sets
    t0 = time.time()
    with Pool(POOL) as p:
        ts = p.map(timed, sample)
    wall = time.time() - t0
    print(f"sample {len(sample)} files at pool {POOL}: wall {wall:.1f} s, per file {np.mean(ts):.1f} s (max {max(ts):.1f})")
    print(f"estimate for {len(fs)} files: {np.mean(ts) * len(fs) / POOL / 60:.1f} min (+ the slowest file)")


def run():
    fs = T.files()
    done = pickle.loads(OCC.read_bytes()) if OCC.exists() else {}
    todo = [p for p in fs if p.stem not in done]
    with Pool(POOL) as p:
        for i, (stem, res) in enumerate(p.imap_unordered(one, todo)):
            done[stem] = res
            if i % 16 == 15:
                OCC.write_bytes(pickle.dumps(done))
    OCC.write_bytes(pickle.dumps(done))
    print("takes", len(done))


def fold_of(stem):
    return int("".join(ch for ch in T.singer_of(stem) if ch.isdigit())) % 2


def analyse(sample=None):
    D = pickle.loads(OCC.read_bytes())
    stems = sorted(D) if sample is None else sorted(D)[:sample]
    sets = {s: T.set_of(s) for s in stems}
    res = dict(takes=len(stems))

    def halves(s, cond="clean"):
        a = D[s][cond]; sp = D[s]["split"]
        return side(a, 0, sp), side(a, 1, sp)

    # clean no-change pairs, V0
    nc = {}
    for s in stems:
        A, B = halves(s)
        p = compare(A, B)
        if p:
            p["unmatched"] = unmatched(A, B)
            nc[s] = p
    res["no_change_comparable"] = dict(of=len(stems), comparable=len(nc),
                                       by_set={t: sum(1 for s in nc if sets[s] == t) for t in sorted(set(sets.values()))},
                                       k_median=float(np.median([p["k"] for p in nc.values()])))
    models = {}
    for f in (0, 1):
        models[f] = fit([p for s, p in nc.items() if fold_of(s) == f])
    res["fit"] = {("odd" if f else "even"): dict(sigma_w_dB=m[0], tau_dB=m[1]) for f, m in models.items()}
    # B1 on the test folds
    test = [(s, called(p, models[1 - fold_of(s)])) for s, p in nc.items()]
    res["B1_test"] = share([c for _, c in test])
    res["B1_test"]["by_set"] = {t: share([c for s, c in test if sets[s] == t]) for t in sorted(set(sets.values()))}
    res["B1_test"]["pass"] = res["B1_test"]["share"] <= 0.05
    fitf = [called(p, models[fold_of(s)]) for s, p in nc.items()]
    res["B1_check_fitting_fold"] = share(fitf); res["B1_check_fitting_fold"]["pass"] = res["B1_check_fitting_fold"]["share"] <= 0.05
    bo = []
    for s in stems:
        A = halves(s)[0]
        B = side(D[s]["boost"], 1, D[s]["split"])
        p = compare(A, B)
        if p:
            bo.append((called(p, models[1 - fold_of(s)]), p["D"]))
    res["B1_check_boost_test_fold"] = share([c for c, _ in bo])
    res["B1_check_boost_test_fold"]["D_median"] = float(np.median([d for _, d in bo]))
    res["B1_check_boost_test_fold"]["pass"] = res["B1_check_boost_test_fold"]["share"] <= 0.05
    # unmatched references
    res["unmatched_note_level"] = dict(rms_D_matched=float(np.sqrt(np.mean([p["D"] ** 2 for p in nc.values()]))),
                                       rms_D_unmatched=float(np.sqrt(np.mean([p["unmatched"] ** 2 for p in nc.values() if p["unmatched"] is not None]))))
    tone = json.loads((T.CACHE / "r2_tone.json").read_text())["tone"]
    r2f = []
    for s in stems:
        v = np.array([b["ring"] for b in tone[s]["clean"]])
        if len(v) >= 4:
            h = len(v) // 2
            a, b = v[:h], v[h:2 * h]
            ua, ub = a.std(ddof=1) / np.sqrt(h), b.std(ddof=1) / np.sqrt(h)
            r2f.append(bool(abs(a.mean() - b.mean()) > 2 * np.sqrt(ua ** 2 + ub ** 2)))
    res["round2_test_same_takes"] = share(r2f)
    # sensitivity
    sens = {}
    for name, (ta, tb) in (("forte_vs_pp", ("LT-pp", "LT-forte")), ("breathy_vs_straight", ("SC-breathy", "SC-straight"))):
        rows = []
        for sg in sorted({T.singer_of(s) for s in stems}):
            a = [s for s in stems if T.singer_of(s) == sg and sets[s] == ta]
            b = [s for s in stems if T.singer_of(s) == sg and sets[s] == tb]
            if a and b:
                p = compare(side(D[a[0]]["clean"]), side(D[b[0]]["clean"]))
                rows.append(None if p is None else dict(singer=sg, k=p["k"], D=p["D"], called=bool(called(p, models[1 - fold_of(a[0])]))))
        ok = [r for r in rows if r]
        sens[name] = dict(singers=len(rows), comparable=len(ok), called_changed=sum(r["called"] for r in ok),
                          b_higher=sum(r["D"] > 0 for r in ok), D_median=float(np.median([r["D"] for r in ok])) if ok else None,
                          k_median=float(np.median([r["k"] for r in ok])) if ok else None, rows=ok)
    res["sensitivity"] = sens

    # B3: the gate
    def gate_pairs(s, cond, variant, g):
        A, B = halves(s)
        An, Bn = side(D[s][cond], 0, D[s]["split"]), side(D[s][cond], 1, D[s]["split"])
        return [p for p in (compare(An, B, variant, g), compare(A, Bn, variant, g)) if p]

    def gate_stats(fold_stems, fold_model, cond, variant, g):
        flags = []
        for s in fold_stems:
            m = fold_model(s)
            if cond == "clean":
                A, B = halves(s)
                ps = [p for p in [compare(A, B, variant, g)] if p]
            else:
                ps = gate_pairs(s, cond, variant, g)
            flags += [called(p, m) for p in ps]
        n_all = len(fold_stems) * (1 if cond == "clean" else 2)
        st = share(flags); st["comparable_share"] = len(flags) / n_all if n_all else None
        return st

    b3 = {}
    for variant in ("V0", "V1", "V2"):
        per_fold = {}
        for f in (0, 1):
            fit_st = [s for s in stems if fold_of(s) == f]
            test_st = [s for s in stems if fold_of(s) != f]
            grid = [0] if variant == "V0" else GRID
            chosen = None
            for g in grid:
                ok = True
                for c in NOISE:
                    st = gate_stats(fit_st, lambda s: models[f], c, variant, g)
                    if st["of"] >= 20 and st["share"] > 0.05:
                        ok = False
                        break
                if ok:
                    chosen = g
                    break
            per_fold[f] = dict(g=chosen)
            gg = chosen if chosen is not None else grid[-1]
            per_fold[f]["test"] = {c: gate_stats(test_st, lambda s: models[f], c, variant, gg) for c in ["clean"] + NOISE}
            per_fold[f]["fit_clean"] = gate_stats(fit_st, lambda s: models[f], "clean", variant, gg)
            per_fold[f]["fit_white10"] = gate_stats(fit_st, lambda s: models[f], "white-10", variant, gg)
        pooled = {}
        for c in ["clean"] + NOISE:
            k = sum(per_fold[f]["test"][c]["called"] for f in (0, 1)); n = sum(per_fold[f]["test"][c]["of"] for f in (0, 1))
            tot = sum(1 for _ in stems) * (1 if c == "clean" else 2)
            pooled[c] = dict(called=k, of=n, share=(k / n if n else None), wilson95=wilson(k, n), comparable_share=n / tot)
        passed = all(pooled[c]["of"] < 20 or pooled[c]["share"] <= 0.05 for c in NOISE) and all(per_fold[f]["g"] is not None for f in (0, 1))
        b3[variant] = dict(g={("even" if f == 0 else "odd") + "_fit": per_fold[f]["g"] for f in (0, 1)}, test_pooled=pooled, pass_=passed,
                           fit_clean={("even" if f == 0 else "odd") + "_fit": per_fold[f]["fit_clean"] for f in (0, 1)},
                           fit_white10={("even" if f == 0 else "odd") + "_fit": per_fold[f]["fit_white10"] for f in (0, 1)})
    res["B3"] = b3
    # B3's own check: V0 at white-10 on the fitting fold must fail
    res["B3_check"] = dict(
        V0_white10_fit_must_fail={k: dict(v, fails=bool(v["share"] is not None and v["share"] > 0.05)) for k, v in b3["V0"]["fit_white10"].items()},
        chosen_g_clean_fit_must_pass={var: {k: dict(v, passes=bool(v["share"] is not None and v["share"] <= 0.05)) for k, v in b3[var]["fit_clean"].items()}
                                      for var in ("V1", "V2")})
    cands = [v for v in ("V1", "V2") if b3[v]["pass_"]]
    res["recommended"] = (max(cands, key=lambda v: (b3[v]["test_pooled"]["white-20"]["of"], v == "V1")) if cands else None)
    # the noise estimates
    res["noise_estimate"] = dict(quiet_accepted_share_median=float(np.median([D[s]["clean"]["quiet_accepted_share"] for s in stems])),
                                 clean_hi_snr_note_median_dB=float(np.median([10 * np.log10(max(v[1] / v[2] - D[s]["clean"]["N_hi"], 1e-30) / D[s]["clean"]["N_hi"])
                                                                              for s in stems for v in side(D[s]["clean"])["notes"].values()])))
    return res


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "check":
        check()
    elif cmd == "time":
        time_sample()
    elif cmd == "run":
        run()
    elif cmd == "analyse":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else None
        t0 = time.time()
        r = analyse(n)
        print(f"analysis {time.time() - t0:.1f} s")
        if n is None:
            (OUT / "r4_ring.json").write_text(json.dumps(r, indent=1))
        print(json.dumps({k: v for k, v in r.items() if k not in ("sensitivity", "B3")}, indent=1))
        print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "rows"} for k, v in r["sensitivity"].items()}, indent=1))
        print(json.dumps(r["B3"], indent=1))


# ------------------------------------------------------------ post hoc
def posthoc():
    """Written after r4_ring.json was seen (squillo iteration 49), so nothing here is a
    tested rule: on the clean no-change pairs, the mean D by set (a direction B minus A,
    so for a scale the descent minus the ascent), and how d_n goes with the change in the
    note's 50 Hz-2 kHz level per frame (dB, B minus A), the singer's level on that note."""
    D = pickle.loads(OCC.read_bytes())
    rows = []
    for s in sorted(D):
        a, sp = D[s]["clean"], D[s]["split"]
        A, B = side(a, 0, sp), side(a, 1, sp)
        for n in sorted(set(A["notes"]) & set(B["notes"])):
            la, lb = A["notes"][n], B["notes"][n]
            rows.append(dict(set=T.set_of(s), stem=s,
                             d=10 * np.log10(lb[1] / lb[0]) - 10 * np.log10(la[1] / la[0]),
                             dl=10 * np.log10(lb[0] / lb[2]) - 10 * np.log10(la[0] / la[2])))
    out = {}
    for t in sorted({r["set"] for r in rows}):
        pr = {}
        for r in rows:
            if r["set"] == t:
                pr.setdefault(r["stem"], []).append(r["d"])
        Ds = [float(np.mean(v)) for v in pr.values()]
        out[t] = dict(pairs=len(Ds), D_mean=float(np.mean(Ds)), D_sd=float(np.std(Ds, ddof=1)) if len(Ds) > 1 else None,
                      B_higher=int(np.sum(np.array(Ds) > 0)))
    d = np.array([r["d"] for r in rows]); dl = np.array([r["dl"] for r in rows])
    slope, icpt = np.polyfit(dl, d, 1)
    res = d - (slope * dl + icpt)
    out["level"] = dict(notes=len(d), r=float(np.corrcoef(d, dl)[0, 1]), slope_dB_per_dB=float(slope),
                        rms_d=float(np.sqrt(np.mean(d ** 2))), rms_d_after_level=float(np.sqrt(np.mean(res ** 2))),
                        dl_rms=float(np.sqrt(np.mean(dl ** 2))))
    (OUT / "r4_posthoc.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


def posthoc_same_vowel():
    """Post hoc, after r4_ring.json and the per-set means were seen: the ± refitted on the sets
    whose halves sing the same vowel on the same notes with no designed change (the scales, straight
    and breathy, and the vibrato arpeggios; not the round, whose halves sing other words, nor
    messa di voce, whose loudness changes by design, nor the long tones, whose halves share
    almost no notes). Tested on the other fold as B1, with the boost and the sensitivity pairs."""
    D = pickle.loads(OCC.read_bytes())
    keep = ("SC-straight", "SC-breathy", "VIB-arpeggio")
    stems = [s for s in sorted(D) if T.set_of(s) in keep]
    nc = {}
    for s in stems:
        a, sp = D[s]["clean"], D[s]["split"]
        p = compare(side(a, 0, sp), side(a, 1, sp))
        if p:
            nc[s] = p
    m = {f: fit([p for s, p in nc.items() if fold_of(s) == f]) for f in (0, 1)}
    out = dict(sets=keep, pairs=len(nc), k_median=float(np.median([p["k"] for p in nc.values()])),
               fit={("odd" if f else "even"): dict(sigma_w_dB=v[0], tau_dB=v[1]) for f, v in m.items()})
    out["false_change_test"] = share([called(p, m[1 - fold_of(s)]) for s, p in nc.items()])
    out["false_change_fit"] = share([called(p, m[fold_of(s)]) for s, p in nc.items()])
    bo = []
    for s in stems:
        a, sp = D[s]["clean"], D[s]["split"]
        p = compare(side(a, 0, sp), side(D[s]["boost"], 1, sp))
        if p:
            bo.append(called(p, m[1 - fold_of(s)]))
    out["boost_6dB_called_test"] = share(bo)
    u = {f: [float(np.sqrt(v[1] ** 2 + v[0] ** 2 / k)) for k in (1, 3, 7)] for f, v in m.items()}
    out["two_u_dB_at_k_1_3_7"] = {("odd" if f else "even"): [2 * x for x in v] for f, v in u.items()}
    sens = {}
    for name, (ta, tb) in (("forte_vs_pp", ("LT-pp", "LT-forte")), ("breathy_vs_straight", ("SC-breathy", "SC-straight"))):
        rows = []
        for sg in sorted({T.singer_of(s) for s in D}):
            a = [s for s in D if T.singer_of(s) == sg and T.set_of(s) == ta]
            b = [s for s in D if T.singer_of(s) == sg and T.set_of(s) == tb]
            if a and b:
                p = compare(side(D[a[0]]["clean"]), side(D[b[0]]["clean"]))
                if p:
                    rows.append(dict(D=p["D"], k=p["k"], called=bool(called(p, m[1 - fold_of(a[0])]))))
        sens[name] = dict(comparable=len(rows), called_changed=sum(r["called"] for r in rows), b_higher=sum(r["D"] > 0 for r in rows))
    out["sensitivity"] = sens
    (OUT / "r4_posthoc_same_vowel.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__" and sys.argv[1] == "posthoc":
    posthoc()
    posthoc_same_vowel()
