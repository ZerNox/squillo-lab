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
BAND_CENTS = 100.0  # R1: a tone frame's band, +-100 cents of the tone
BAND_SHARE = 0.99  # R1: share of the window's power inside the band
MERGE_GAP = 8  # R1: frames; same-tone spans this close are one span, the gap kept
GROSS = 50.0  # R2: cents, the error MT-003's refusal is meant to guard (MT-003's reason)
# R2: the first aperiodicity MT-003 refuses at, read from the table: the first bin whose u is infinite
REFUSE_AT = A.BINS[int(np.argmax(~np.isfinite(TABLE)))]

PATHS = {  # R0: round 1's captures into a 48 kHz context, three runs each
    "firefox bridge 44100->48000": "firefox-stream-fake-src44100-ctx48000-load0-r{}",
    "chrome converter 44100->48000": "chrome-stream-fake48000-src44100-ctx48000-load0-r{}",
    "firefox equal rates 48000->48000": "firefox-stream-fake-src48000-ctx48000-load0-r{}",
}


def min_span_frames():
    """R1: a span shorter than a tone's but longer than the sweep's passage through a +-100 cent band.
    The sweep (gen.py) is exponential over its segment: octaves per second from its own parameters."""
    a, b = gen.SEGMENTS["sweep"]
    oct_per_s = math.log2(gen.SWEEP_F1 / gen.SWEEP_F0) / (b - a)
    sweep_s = (2 * BAND_CENTS / 1200) / oct_per_s + yin.WIN / SR  # band crossing plus one window
    tone_s = min(gen.SEGMENTS[f"tone{int(f)}"][1] - gen.SEGMENTS[f"tone{int(f)}"][0] for f in gen.TONES)
    tone_frames = (tone_s * SR - yin.WIN) / yin.HOP  # frames whose window lies inside one tone
    sweep_frames = sweep_s * SR / yin.HOP
    n = int(math.ceil(2 * sweep_frames))
    assert n < 0.75 * tone_frames, (n, tone_frames)
    return n, sweep_frames, tone_frames


MIN_SPAN, SWEEP_FRAMES, TONE_FRAMES = min_span_frames()


def tone_frames(x):
    """R1: per frame (yin.frame_windows' index), the tone whose +-100 cent band holds >= 99 % of the
    Hann-windowed power, or -1. Found without the pitch tracker."""
    idx, win = yin.frame_windows(x)
    n_fft = 1 << 15
    P = np.abs(np.fft.rfft(win * np.hanning(yin.WIN), n_fft, axis=1)) ** 2
    fr = np.fft.rfftfreq(n_fft, 1 / SR)
    tot = P.sum(axis=1) + 1e-300
    lab = np.full(len(idx), -1)
    for j, f in enumerate(gen.TONES):
        band = (fr >= f * 2 ** (-BAND_CENTS / 1200)) & (fr <= f * 2 ** (BAND_CENTS / 1200))
        lab[P[:, band].sum(axis=1) / tot >= BAND_SHARE] = j
    return idx, lab


def spans(idx, lab, skip_frames=0):
    """R1: runs of one tone, merged across gaps of <= MERGE_GAP frames, kept if >= MIN_SPAN frames."""
    runs = []
    k = 0
    while k < len(lab):
        if lab[k] < 0 or idx[k] < skip_frames:
            k += 1
            continue
        j = k
        while j + 1 < len(lab) and lab[j + 1] == lab[k]:
            j += 1
        runs.append([lab[k], k, j])
        k = j + 1
    merged = []
    for r in runs:
        if merged and merged[-1][0] == r[0] and r[1] - merged[-1][2] - 1 <= MERGE_GAP:
            merged[-1][2] = r[2]
        else:
            merged.append(r)
    return [(t, a, b) for t, a, b in merged if b - a + 1 >= MIN_SPAN]


def measure(x, skip_frames=0):
    """R2: YIN on every frame of every span; error against the tone's nominal frequency."""
    idx, lab = tone_frames(x)
    sp = spans(idx, lab, skip_frames)
    fidx, f0, dip = yin.yin(x)
    assert np.array_equal(fidx, idx)  # frames matched by the index yin returns (S15)
    f0 = yin.in_range(f0, 3.0)  # as r2_measures.py line 88
    rows = []
    for t, a, b in sp:
        f = gen.TONES[t]
        for k in range(a, b + 1):
            refused = (not np.isfinite(f0[k])) or not (dip[k] < REFUSE_AT)
            e = float(yin.cents(f0[k], f)) if np.isfinite(f0[k]) else float("nan")
            u = float(A.u_of(np.array([dip[k]]), TABLE)[0]) if np.isfinite(dip[k]) else float("inf")
            rows.append(dict(tone=f, frame=int(idx[k]), t_s=float((yin.HOP * (idx[k] + 1)) / SR), refused=bool(refused),
                             e=e, u=u, span=(int(idx[a]), int(idx[b]))))
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


def seg_ok(sp, idx_of_span, loop_n):
    """K1: every span lies inside its tone's gen.SEGMENTS interval (modulo the loop), window included."""
    for t, (fa, fb) in zip([s[0] for s in sp], idx_of_span):
        a, b = gen.SEGMENTS[f"tone{int(gen.TONES[t])}"]
        s0 = (yin.HOP * (fa - 3)) % loop_n  # first sample of the first frame's window
        s1 = (yin.HOP * (fb + 1)) % loop_n  # one past the last frame's last sample
        if not (a * SR - 1 <= s0 and s1 <= b * SR + 1):
            return False
    return True


def k1(x, loop_n):
    """K1 as a check: exactly two spans per tone over two loops, each inside its segment."""
    idx, lab = tone_frames(x)
    sp = spans(idx, lab)
    per = [sum(1 for s in sp if s[0] == j) for j in range(len(gen.TONES))]
    ok = per == [2] * len(gen.TONES) and seg_ok(sp, [(idx[a], idx[b]) for _, a, b in sp], loop_n)
    return bool(ok), per


def k2(x, shift, tol):
    """K2 as a check: the median error over accepted frames recovers a known shift within tol."""
    _, rows = measure(x)
    s = summarise(rows)
    return bool(s["median_e"] is not None and abs(s["median_e"] - shift) <= tol), s


def checks():
    out = {}
    # K3: the table and the refusal, read from E-002's fold2.json, as round 2 used them
    assert TABLE[0] == math.sqrt(3) and REFUSE_AT == 0.02, (TABLE, REFUSE_AT)
    out["K3_table"] = dict(table=[None if not np.isfinite(v) else float(v) for v in TABLE], refuse_at=REFUSE_AT,
                           min_span=MIN_SPAN, sweep_frames=SWEEP_FRAMES, tone_frames=TONE_FRAMES)
    ref48 = reference(48000)
    loop_n = len(ref48) // 2
    ok, per = k1(ref48, loop_n)
    assert ok, ("K1 must pass on the reference", per)
    toneless = ref48.copy()
    for f in gen.TONES:
        a, b = (int(round(v * SR)) for v in gen.SEGMENTS[f"tone{int(f)}"])
        toneless[a:b] = 0
        toneless[loop_n + a:loop_n + b] = 0
    bad, per_bad = k1(toneless, loop_n)
    assert not bad, ("K1 must fail on the probe without its tones (sweep only)", per_bad)
    out["K1_segmentation"] = dict(must_pass=dict(ok=ok, spans_per_tone=per),
                                  must_fail=dict(ok=bad, spans_per_tone=per_bad))
    # K2: the reference's own error sets the tolerance (computed, not typed)
    _, rows = measure(ref48)
    s_ref = summarise(rows)
    tol = s_ref["max_abs_e"] + 0.01
    x_sh, sh = shifted(ref48[:loop_n], 0.5)
    good, s_sh = k2(x_sh, sh, tol)
    assert good, ("K2 must pass on the reference made sharp by a known shift", sh, s_sh)
    bad2, s_un = k2(ref48, sh, tol)
    assert not bad2, ("K2 must fail on the unshifted reference", s_un)
    ref441 = reference(44100)
    ok441, per441 = k1(ref441, len(ref441) // 2)
    assert ok441, ("K1 must pass on the 44.1 kHz probe through the ideal converter", per441)
    _, rows441 = measure(ref441)
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


def main():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    res = dict(checks=checks(), paths={}, runs={})
    ref_max = max(v["max_abs_e"] for v in res["checks"]["reference"].values())
    skip = int(SKIP_S * SR / yin.HOP)
    steps = json.loads((HERE / "results/summary.json").read_text())["signal"]
    step_key = {"firefox bridge 44100->48000": "firefox/stream/44100->48000",
                "chrome converter 44100->48000": "chrome/stream/44100->48000",
                "firefox equal rates 48000->48000": "firefox/stream/48000->48000"}
    for path, pat in PATHS.items():
        allrows = []
        for r in range(3):
            name = pat.format(r)
            x = np.fromfile(RAW / f"{name}.f32", "<f4").astype(np.float64)
            sp, rows = measure(x, skip)
            an, cfg = s17(name, rows, ref_max)
            assert cfg["ctxRate"] == 48000
            res["runs"][name] = dict(spans=[(gen.TONES[t], int(a), int(b)) for t, a, b in sp], **summarise(rows),
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
