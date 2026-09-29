"""E-003 round 3 (squillo iteration 51, F-034 (b)): Firefox's rate bridge,
frame by frame. Crude experiment code. Rules R1 to R4 and checks K1 to K3
in the README, *Round 3*. No new capture: round 1's cached captures into a
48 kHz context, the only context rate squillo's capture accepts (CA-001).

    uv run --project ../E-002-measurement-reliability python r3_bridge.py checks   # K1-K3, before any capture is read
    uv run --project ../E-002-measurement-reliability python r3_bridge.py          # results/r3/bridge.json
"""
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
E002 = HERE.parent / "E-002-measurement-reliability"
sys.path.insert(0, str(E002))
sys.path.insert(0, str(HERE))
import r2_analyse as A  # noqa: E402
import yin  # noqa: E402

import analyze  # noqa: E402  (round 1: load_ref, the ideal converter)
import gen  # noqa: E402

RAW = HERE / "data/cache/raw"
OUT = HERE / "results/r3"
SPEC = json.loads((E002 / "results/fold2.json").read_text())["measures"]["spec"]
TABLE = np.array([np.inf if v is None else v for v in SPEC["table"]])  # MT-003's table, as r2_measures.py line 33
SR = yin.SR
assert SR == 48_000
SKIP_S = analyze.SKIP_S  # round 1's start-up transient
MARGIN_S = analyze.TONE_MARGIN_S  # R1: round 1's margin inside each tone segment
MATCH = 0.99  # R1: a span's samples must match the reference tone's at this normalised correlation
MATCH_SEARCH = 200  # samples either side of the located position (a quarter-period at 110 Hz is 109)
GROSS = 50.0  # R2: cents, the error MT-003's refusal is meant to guard (MT-003's reason)
# R2: the first aperiodicity MT-003 refuses at, read from the table: the first bin whose u is infinite
REFUSE_AT = A.BINS[int(np.argmax(~np.isfinite(TABLE)))]

PATHS = {  # R0: round 1's captures into a 48 kHz context, three runs each
    "firefox bridge 44100->48000": "firefox-stream-fake-src44100-ctx48000-load0-r{}",
    "chrome converter 44100->48000": "chrome-stream-fake48000-src44100-ctx48000-load0-r{}",
    "firefox equal rates 48000->48000": "firefox-stream-fake-src48000-ctx48000-load0-r{}",
}


def locate(x, src_sr):
    """R1: the capture's lag against the looped probe, as round 1 (analyze.analyse_probe's first lines,
    analyze.track): x[s + i] ~ ref[(s + lag + i) mod N] per tracked 0.1 s window."""
    ref = analyze.load_ref(SR, src_sr)
    N = len(ref)
    s0 = int(SKIP_S * SR)
    k, _ = analyze.circ_lag(x[s0:s0 + N], analyze.mask_high(ref, SR))
    tr = analyze.track(x, ref, SR, k - s0)
    assert len(tr) >= 3, "could not track"
    return ref, N, tr


def spans(x, src_sr):
    """R1: every occurrence of each tone segment after SKIP_S, less MARGIN_S at each end, placed in the
    capture by the lag of the nearest tracked window; the frames whose whole window lies inside it; and
    whether its samples match the reference tone's (normalised correlation >= MATCH within MATCH_SEARCH)."""
    ref, N, tr = locate(x, src_sr)
    ts = np.array([t[0] for t in tr])
    out = []
    for j, f in enumerate(gen.TONES):
        a, b = (int(round(v * SR)) for v in gen.SEGMENTS[f"tone{int(f)}"])
        a += int(MARGIN_S * SR)
        b -= int(MARGIN_S * SR)
        for m in range(-1, len(x) // N + 2):
            sa = a + m * N - tr[0][1] % N  # predicted from the first window's lag, taken modulo the loop
            for _ in range(3):  # then placed with the lag of the window nearest it; the tracked lag
                lag = tr[int(np.argmin(np.abs(ts - sa)))][1]  # wraps by N at the loop, so the occurrence
                base = a - lag  # is the one of a - lag + kN nearest the prediction
                sa = int(round(base + N * round((sa - base) / N)))
            lag_mod = (lag + N / 2) % N - N / 2
            sb = sa + (b - a)
            if sa < int(SKIP_S * SR) or sb > len(x):
                continue
            i0 = int(math.ceil(sa / yin.HOP)) + 3  # first frame whose window starts at or after sa
            i1 = sb // yin.HOP - 1  # last frame whose window ends at or before sb
            if i1 < i0:
                continue
            seg = x[sa:sb]
            p = int(round((sa + lag) % N))
            r = ref[(p - MATCH_SEARCH + np.arange(len(seg) + 2 * MATCH_SEARCH)) % N]
            c = np.correlate(r, seg, "valid")
            norm = np.sqrt(np.sum(seg ** 2) * np.array([np.sum(r[q:q + len(seg)] ** 2) for q in range(len(c))])) + 1e-30
            match = float(np.max(c / norm))
            out.append(dict(tone=j, i0=i0, i1=i1, sa=sa, sb=sb, lag=float(lag_mod), match=match))
    return out


def measure(x, src_sr):
    """R2: YIN on every frame of every span; error against the tone's nominal frequency."""
    sp = spans(x, src_sr)
    fidx, f0, dip = yin.yin(x)
    assert np.array_equal(fidx, np.arange(3, len(x) // yin.HOP))  # frames matched by the index yin returns (S15)
    f0 = yin.in_range(f0, 3.0)  # as r2_measures.py line 88
    rows = []
    for s_ in sp:
        f = gen.TONES[s_["tone"]]
        for i in range(s_["i0"], s_["i1"] + 1):
            k = int(np.searchsorted(fidx, i))
            assert fidx[k] == i
            refused = (not np.isfinite(f0[k])) or not (dip[k] < REFUSE_AT)
            e = float(yin.cents(f0[k], f)) if np.isfinite(f0[k]) else float("nan")
            u = float(A.u_of(np.array([dip[k]]), TABLE)[0]) if np.isfinite(dip[k]) else float("inf")
            rows.append(dict(tone=f, frame=i, t_s=float(yin.HOP * (i + 1) / SR), refused=bool(refused), e=e, u=u))
    return sp, rows


def summarise(rows):
    acc = [r for r in rows if not r["refused"]]
    e = np.abs(np.array([r["e"] for r in acc])) if acc else np.zeros(0)
    cov = [abs(r["e"]) <= 2 * r["u"] for r in acc]
    return dict(frames=len(rows), accepted=len(acc), refused=len(rows) - len(acc),
                max_abs_e=float(e.max()) if len(e) else None, p95_abs_e=float(np.percentile(e, 95)) if len(e) else None,
                median_e=float(np.median([r["e"] for r in acc])) if acc else None,
                gross=int((e > GROSS).sum()), coverage_2u=float(np.mean(cov)) if cov else None)


def reference(src_sr):
    """The probe as an ideal converter delivers it at 48 kHz (round 1's analyze.load_ref), looped twice."""
    x = analyze.load_ref(SR, src_sr)
    return np.concatenate([x, x])


def shifted(x1, cents):
    """The one-loop reference played sharp: the periodic loop FFT-resampled to fewer samples at the
    same rate. Returns the loop twice and the shift it actually has, from the exact length ratio."""
    n = len(x1)
    m = int(round(n / 2 ** (cents / 1200)))
    X = np.fft.rfft(x1)
    Y = np.zeros(m // 2 + 1, complex)
    q = min(len(X), len(Y)) - 1
    Y[:q] = X[:q]
    y = np.fft.irfft(Y, m) * m / n
    return np.concatenate([y, y]), 1200 * math.log2(n / m)


def k1(x, src_sr):
    """K1 as a check: exactly two occurrences per tone over two loops, each matching the reference tone."""
    sp = spans(x, src_sr)
    per = [sum(1 for q in sp if q["tone"] == j) for j in range(len(gen.TONES))]
    ok = per == [2] * len(gen.TONES) and all(q["match"] >= MATCH for q in sp)
    return bool(ok), per, [round(q["match"], 6) for q in sp]


def k2(x, src_sr, shift, tol):
    """K2 as a check: the median error over accepted frames recovers a known shift within tol."""
    _, rows = measure(x, src_sr)
    s = summarise(rows)
    return bool(s["median_e"] is not None and abs(s["median_e"] - shift) <= tol), s


def checks():
    out = {}
    # K3: the table and the refusal, read from E-002's fold2.json, as round 2 used them
    assert TABLE[0] == math.sqrt(3) and REFUSE_AT == 0.02, (TABLE, REFUSE_AT)
    out["K3_table"] = dict(table=[None if not np.isfinite(v) else float(v) for v in TABLE], refuse_at=REFUSE_AT)
    ref48 = reference(48000)
    loop_n = len(ref48) // 2
    ok, per, m = k1(ref48, 48000)
    assert ok, ("K1 must pass on the reference", per, m)
    toneless = ref48.copy()
    for f in gen.TONES:
        a, b = (int(round(v * SR)) for v in gen.SEGMENTS[f"tone{int(f)}"])
        toneless[a:b] = 0
        toneless[loop_n + a:loop_n + b] = 0
    bad, per_bad, m_bad = k1(toneless, 48000)
    assert not bad, ("K1 must fail on the probe without its tones", per_bad, m_bad)
    ref441 = reference(44100)
    ok441, per441, m441 = k1(ref441, 44100)
    assert ok441, ("K1 must pass on the 44.1 kHz probe through the ideal converter", per441, m441)
    out["K1_segmentation"] = dict(must_pass=dict(ok=ok, spans_per_tone=per, match=m),
                                  must_fail=dict(ok=bad, spans_per_tone=per_bad, match=m_bad),
                                  must_pass_44100=dict(ok=ok441, spans_per_tone=per441, match=m441))
    # K2: the reference's own error sets the tolerance (computed, not typed)
    _, rows = measure(ref48, 48000)
    s_ref = summarise(rows)
    tol = s_ref["max_abs_e"] + 0.01
    x_sh, sh = shifted(ref48[:loop_n], 0.5)
    good, s_sh = k2(x_sh, 48000, sh, tol)
    assert good, ("K2 must pass on the reference made sharp by a known shift", sh, s_sh)
    bad2, s_un = k2(ref48, 48000, sh, tol)
    assert not bad2, ("K2 must fail on the unshifted reference", s_un)
    _, rows441 = measure(ref441, 44100)
    s_ref441 = summarise(rows441)
    out["K2_shift"] = dict(tolerance=tol, known_shift=sh, must_pass=dict(ok=good, **s_sh),
                           must_fail=dict(ok=bad2, **s_un))
    out["reference"] = {"probe48000 (ideal)": s_ref, "probe44100 via the ideal converter": s_ref441}
    return out


def s17(name, rows, ref_max):
    """R4: anomalies with their capture time and loop time. Tones lie at loop time 3.0-5.0 s."""
    rj = json.loads((RAW / f"{name}.json").read_text())
    out = []
    for r in rows:
        if r["refused"] or abs(r["e"]) > ref_max + 0.1:
            out.append(dict(t_s=round(r["t_s"], 3), tone=r["tone"], refused=r["refused"],
                            e=None if not np.isfinite(r["e"]) else round(r["e"], 4)))
    return out, rj["cfg"]


def cfg_src(name):
    return json.loads((RAW / f"{name}.json").read_text())["cfg"]["srcRate"]


def main():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    res = dict(checks=checks(), paths={}, runs={})
    ref_max = max(v["max_abs_e"] for v in res["checks"]["reference"].values())
    steps = json.loads((HERE / "results/summary.json").read_text())["signal"]
    step_key = {"firefox bridge 44100->48000": "firefox/stream/44100->48000",
                "chrome converter 44100->48000": "chrome/stream/44100->48000",
                "firefox equal rates 48000->48000": "firefox/stream/48000->48000"}
    for path, pat in PATHS.items():
        allrows = []
        for r in range(3):
            name = pat.format(r)
            x = np.fromfile(RAW / f"{name}.f32", "<f4").astype(np.float64)
            sp, rows = measure(x, cfg_src(name))
            assert all(q["match"] >= MATCH for q in sp), ("R1: every located tone matches the reference's", name)
            an, cfg = s17(name, rows, ref_max)
            assert cfg["ctxRate"] == 48000
            res["runs"][name] = dict(spans=sp, **summarise(rows),
                                     anomalies=an, round1_steps=steps[step_key[path]]["steps"][r])
            allrows += rows
        res["paths"][path] = summarise(allrows)
    br = res["paths"]["firefox bridge 44100->48000"]
    res["decision_b_cents"] = math.ceil(br["max_abs_e"] * 100) / 100  # R3: rounded up to 0.01 cent
    res["seconds"] = round(time.time() - t0, 1)
    (OUT / "bridge.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res["paths"], indent=1), res["decision_b_cents"], res["seconds"])


if __name__ == "__main__":
    if sys.argv[1:] == ["checks"]:
        t0 = time.time()
        c = checks()
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "checks.json").write_text(json.dumps(c, indent=1))
        print(json.dumps(c, indent=1), round(time.time() - t0, 1), "s")
    else:
        main()
