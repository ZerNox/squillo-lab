"""E-003 round 2 (squillo iteration 47): what browser processing does to
squillo's measures. Crude experiment code. Rules in the README, *Round 2*,
rules 3 to 7.

    uv run --project ../E-002-measurement-reliability python r2_measures.py checks   # rule 7, before any capture
    uv run --project ../E-002-measurement-reliability python r2_measures.py          # results/r2/analysis.json
"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).parent
E002 = HERE.parent / "E-002-measurement-reliability"
sys.path.insert(0, str(E002))
import fold2 as F  # noqa: E402
import r2_analyse as A  # noqa: E402
import r2_run as RR  # noqa: E402
import yin  # noqa: E402

IN = HERE / "data/cache/r2/in"
CAP = HERE / "data/cache/r2/cap"
OUT = HERE / "results/r2"
SPEC = json.loads((E002 / "results/fold2.json").read_text())["measures"]["spec"]
TABLE = np.array([np.inf if v is None else v for v in SPEC["table"]])
C, KAPPA = SPEC["c"], SPEC["kappa"]
SR, WIN = 48_000, 48_000
SHIFT = 64  # samples: half a 128-sample render quantum (rule 3a)
KEYS = {"S": "steadiness", "E": "vibrato_extent", "R": "vibrato_rate"}


# ------------------------------------------------------------------ rule 3: alignment
def xlag(a, b):
    """Lag L maximising sum a[n + L] b[n] (a[n + L] ~ b[n]), by FFT cross-correlation."""
    n = 1 << int(np.ceil(np.log2(len(a) + len(b))))
    c = np.fft.irfft(np.fft.rfft(a, n) * np.conj(np.fft.rfft(b, n)), n)
    k = int(np.argmax(c))
    return k if k < n // 2 else k - n


def align(cap, ref):
    """The capture as samples of the input's time (nan where not covered), the whole lag, and the
    per-window lags (rule 3 as revised before the full run, README *Round 2*, rule 3a): a 1 s window
    is usable when the capture correlates with it at 0.8 or more at its own lag; an anomaly is a
    usable window shifted from the whole's lag by 64 samples or more (half a render quantum) whose
    next usable window is shifted by the same amount within 2 samples, as an inserted or lost block
    shifts every later window; recorded by its position in the input."""
    L = xlag(cap, ref)
    a = np.full(len(ref), np.nan)
    n = np.arange(len(ref))
    j = n + L
    ok = (j >= 0) & (j < len(cap))
    a[ok] = cap[j[ok]]
    windows = []
    for w0 in range(0, len(ref) - WIN + 1, WIN):
        seg = ref[w0:w0 + WIN]
        if np.sqrt(np.mean(seg ** 2)) < 1e-3:  # a window of the pads or a pause: no lag to measure
            continue
        lo, hi = w0 + L - 2400, w0 + L + WIN + 2400  # 50 ms either side
        if lo < 0 or hi > len(cap):
            continue
        cc = np.correlate(cap[lo:hi], seg, "valid")
        k = int(np.argmax(np.abs(cc)))
        lw = k + lo - w0
        c = cap[w0 + lw:w0 + lw + WIN]
        r = float(np.dot(seg, c) / np.sqrt(np.dot(seg, seg) * np.dot(c, c))) if np.dot(c, c) > 0 else 0.0
        windows.append(dict(w0=w0, lag=lw, shift=lw - L, corr=r, usable=r >= 0.8))
    use = [w for w in windows if w["usable"]]
    anomalies = []
    for w, nx in zip(use, use[1:] + [None]):
        if abs(w["shift"]) >= SHIFT and nx is not None and abs(nx["shift"] - w["shift"]) <= 2:
            anomalies.append(dict(input_sample=w["w0"], input_s=w["w0"] / SR, lag=w["lag"], whole=L,
                                  shift=w["shift"], corr=w["corr"], to_end_s=(len(ref) - w["w0"]) / SR))
    return a, L, anomalies, windows


# ------------------------------------------------------------------ rule 4: measures
def frames(x, ft):
    idx, f, dip = yin.yin(np.nan_to_num(x))
    f = yin.in_range(f, 3.0)
    s = 384 * (idx - 3)
    covered = np.array([not np.isnan(x[max(a, 0):a + 1536]).any() and a >= 0 for a in s])
    f = np.where(covered, f, np.nan)
    f_true, _, valid = RR.frame_truth(ft, idx, f)
    u = np.where(np.isnan(f), np.inf, A.u_of(np.nan_to_num(dip, nan=1.0), TABLE))
    return dict(idx=idx, f=f, u=u, f_true=f_true, valid=valid & covered, covered=covered)


def take_measures(fr, ft, add_vibrato=None):
    """Held notes from the measured contour, blocks and take values with their take +- (fold2), and the
    same block functions on the truth over the same frames where every frame is valid."""
    p = F.cents(fr["f"])
    if add_vibrato is not None:
        p = p + add_vibrato * np.sin(2 * np.pi * 5.0 * fr["idx"] / 125.0)
    u = fr["u"]
    notes = F.held_notes(p, u)
    bl, tb = [], []
    for fi, con, acc in notes:
        b = F.blocks(con, u[fi], acc, C, True)
        bl += b
        if fr["valid"][fi].all():
            t = A.block_measures(F.cents(fr["f_true"][fi]))
            for x, y in zip(b, t):
                if x["R"] is None:
                    y["R"] = None
            tb += t
        else:
            tb += [None] * len(b)
    out = {}
    for k in "SER":
        tk = F.take(bl, k, KAPPA[k])
        tv = [t[k] for t, b in zip(tb, bl) if b[k] is not None and t is not None and t[k] is not None]
        nb = sum(1 for b in bl if b[k] is not None)
        out[k] = None if tk is None else dict(value=tk[0], u=tk[1], blocks=tk[2],
                                               truth=float(np.mean(tv)) if len(tv) == nb and nb else None)
    return dict(notes=len(notes), take=out)


def frame_stats(fr):
    v = fr["valid"]
    acc = v & ~np.isnan(fr["f"]) & np.isfinite(fr["u"])
    err = np.abs(1200 * np.log2(fr["f"][acc] / fr["f_true"][acc]))
    return dict(valid=int(v.sum()), accepted=int(acc.sum()), err=err, u=fr["u"][acc])


# ------------------------------------------------------------------ rule 5: comparisons
def coverage(err, u, w=1.0):
    return float(np.mean(err <= 2 * w * u)) if len(err) else float("nan")


def widening(err, u, target):
    """The least w on a 0.01 grid from 1 at which coverage of +-2wu reaches target."""
    for w in np.arange(1.0, 20.0001, 0.01):
        if coverage(err, u, w) >= target:
            return round(float(w), 2)
    return float("inf")


def read_input(stem, cond):
    x, sr = sf.read(IN / f"{stem}.{cond}.wav", dtype="float64")
    assert sr == SR
    return x, np.load(IN / f"{stem}.truth.npy").astype(np.float64)


def direct(key):
    stem, cond = key
    x, ft = read_input(stem, cond)
    fr = frames(x, ft)
    return key, frame_stats(fr), take_measures(fr, ft)


def captured(key):
    stem, cond, req = key
    x, ft = read_input(stem, cond)
    meta = json.loads((CAP / f"{stem}.{cond}.{req}.json").read_text())
    cap = np.fromfile(CAP / f"{stem}.{cond}.{req}.f32", "<f4").astype(np.float64)
    a, L, anom, win = align(cap, x)
    if anom:  # rule 3a: a capture with an anomaly is left out of both analyses, and counted
        return key, None, None, dict(lag=L, anomalies=anom, windows=len(win),
                                     shifts=[w["shift"] for w in win if w["usable"]],
                                     settings=meta.get("settings"), worker=meta.get("worker"))
    fr = frames(a, ft)
    ok = ~np.isnan(a)
    g = float(np.dot(a[ok], x[ok]) / np.dot(x[ok], x[ok])) if ok.any() else float("nan")
    res = a[ok] - g * x[ok]
    info = dict(lag=L, anomalies=anom, windows=len(win), windows_usable=sum(w["usable"] for w in win),
                shifts=[w["shift"] for w in win if w["usable"]], covered_s=float(ok.sum() / SR),
                gain=g, residual_db=float(10 * np.log10(np.sum(res ** 2) / np.sum(a[ok] ** 2))),
                peak=float(np.nanmax(np.abs(a))), settings=meta.get("settings"), worker=meta.get("worker"),
                version=meta.get("version"))
    tm = take_measures(fr, ft)
    return key, frame_stats(fr), tm, info


def moved(tm_a, tm_b):
    """Per measure: (took, a moved beyond b's +-2u) over takes measured on both."""
    out = {}
    for k in "SER":
        a, b = tm_a["take"][k], tm_b["take"][k]
        out[k] = None if a is None or b is None else bool(abs(a["value"] - b["value"]) > 2 * b["u"])
    return out


# ------------------------------------------------------------------ rule 7: checks of the checks
def checks():
    stem = "f1_long_straight_a"
    x, ft = read_input(stem, "clean")
    a, L, anom, _ = align(x, x)
    ins = np.concatenate([x[:5 * SR], np.zeros(480), x[5 * SR:]])
    b, L2, anom2, _ = align(ins, x)
    from scipy.signal import lfilter
    ap = lfilter([-0.5, 1.0], [1.0, -0.5], x)  # first-order allpass: 3 samples' group delay at low frequencies
    _, L3, anom3, _ = align(ap, x)
    fr = frames(x, ft)
    st = frame_stats(fr)
    cov = coverage(st["err"], st["u"])
    w_self = widening(st["err"], st["u"], cov)
    w_tripled = widening(3 * st["err"], st["u"], cov)
    tm = take_measures(fr, ft)
    tm_vib = take_measures(fr, ft, add_vibrato=60.0)
    m_self, m_vib = moved(tm, tm), moved(tm_vib, tm)
    R = dict(
        align_self=dict(lag=L, anomalies=len(anom), must=L == 0 and not anom),
        align_allpass=dict(lag=L3, anomalies=len(anom3), must=not anom3),
        align_insert=dict(lag=L2, anomalies=[an["input_s"] for an in anom2],
                          must=bool(anom2) and all(an["input_s"] < 5.0 for an in anom2)),
        widening_self=dict(w=w_self, coverage=cov, must=w_self == 1.0),
        widening_tripled=dict(w=w_tripled, must=w_tripled > 1.0),
        take_self=dict(moved=m_self, must=not any(v for v in m_self.values() if v is not None)),
        take_vibrato_60=dict(moved=m_vib, extent=(tm["take"]["E"], tm_vib["take"]["E"]), must=bool(m_vib["E"])),
    )
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "checks.json").write_text(json.dumps(R, indent=1, default=float))
    print(json.dumps(R, indent=1, default=float))
    assert all(v["must"] for v in R.values()), {k: v["must"] for k, v in R.items()}


if __name__ == "__main__":
    if sys.argv[1:] == ["checks"]:
        checks()
    else:
        import r2_report
        r2_report.main()
