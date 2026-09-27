"""E-003 round 1: analyse every capture in data/cache/raw against the probe.

Per capture: alignment to the looped probe, bit-exactness, gain, lag drift
(inserted or dropped samples), tone frequency error in cents and THD+N,
frequency response from the sweep, alias or image rejection, noise floor,
and the transport: blocks lost, reordered, render quanta skipped, and how
far behind the worker ran. Writes results/runs.json.
"""
import glob
import json
import os

import numpy as np
from scipy.optimize import least_squares

import gen

RAW = "data/cache/raw"
SKIP_S = 0.5  # start-up transient ignored
TONE_MARGIN_S = 0.05


def load_ref(sr, src_sr=None):
    """The probe as an ideal converter would deliver it at sr: the source
    loop itself when the rates match, else its exact band-limited
    resampling (the loop is periodic, so an FFT resample is exact; content
    above the lower Nyquist is removed, as an ideal converter would)."""
    src_sr = src_sr or sr
    x = np.fromfile(f"data/cache/probe{src_sr}.f32", "<f4").astype(np.float64)
    if src_sr == sr:
        return x
    n = int(round(len(x) * sr / src_sr))
    X = np.fft.rfft(x)
    Y = np.zeros(n // 2 + 1, complex)
    m = min(len(X), len(Y)) - 1  # drop the Nyquist bin of the longer one
    Y[:m] = X[:m]
    return np.fft.irfft(Y, n) * n / len(x)


def seg_idx(name, sr):
    a, b = gen.SEGMENTS[name]
    return int(round(a * sr)), int(round(b * sr))


def mask_high(ref, sr):
    m = ref.copy()
    a, b = seg_idx("high", sr)
    m[a - int(0.02 * sr):b + int(0.02 * sr)] = 0
    return m


def circ_lag(x, ref):
    """Lag k (fractional) with x[i] ~ ref[(i + k) mod N]; x has length N."""
    N = len(ref)
    c = np.fft.irfft(np.fft.rfft(ref) * np.conj(np.fft.rfft(x)), N)
    k = int(np.argmax(c))
    y0, y1, y2 = c[(k - 1) % N], c[k], c[(k + 1) % N]
    d = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2) if (y0 - 2 * y1 + y2) != 0 else 0.0
    return k + d, c[k] / np.sqrt(np.sum(ref ** 2) * np.sum(x ** 2))


def frac_shift(ref, k):
    """ref advanced by k samples (circular, band-limited): out[i] = ref(i + k)."""
    N = len(ref)
    f = np.fft.rfftfreq(N)
    return np.fft.irfft(np.fft.rfft(ref) * np.exp(2j * np.pi * f * k), N)


PAD = 4096


def ref_window(ref, pos, n):
    """ref(pos + i) for i in 0..n-1, pos fractional, band-limited, from a
    padded local chunk of the periodic reference."""
    N = len(ref)
    p0 = int(np.floor(pos))
    frac = pos - p0
    idx = (p0 - PAD + np.arange(n + 2 * PAD)) % N
    chunk = ref[idx]
    m = len(chunk)
    f = np.fft.rfftfreq(m)
    sh = np.fft.irfft(np.fft.rfft(chunk) * np.exp(2j * np.pi * f * frac), m)
    return sh[PAD:PAD + n]


def refine(xw, ref, pos):
    """Least-squares fractional position and gain of window xw in ref,
    within one sample of pos: (pos, gain, snr_db)."""
    from scipy.optimize import minimize_scalar

    def cost(d):
        r = ref_window(ref, pos + d, len(xw))
        g = np.dot(xw, r) / np.dot(r, r)
        return np.sum((xw - g * r) ** 2)

    res = minimize_scalar(cost, bounds=(-1, 1), method="bounded", options={"xatol": 1e-4})
    r = ref_window(ref, pos + res.x, len(xw))
    g = np.dot(xw, r) / np.dot(r, r)
    e = xw - g * r
    return pos + res.x, g, float(10 * np.log10(np.sum((g * r) ** 2) / (np.sum(e ** 2) + 1e-30)))


def sine_fit(y, sr, f0):
    t = np.arange(len(y)) / sr
    w = np.hanning(len(y))
    nfft = 1 << 20
    s = np.abs(np.fft.rfft(y * w, nfft))
    lo, hi = int(f0 * 0.9 * nfft / sr), int(f0 * 1.1 * nfft / sr)
    fk = (lo + np.argmax(s[lo:hi])) * sr / nfft

    def res(p):
        return p[0] * np.sin(2 * np.pi * p[2] * t) + p[1] * np.cos(2 * np.pi * p[2] * t) + p[3] - y

    a = 2 * np.dot(y, np.sin(2 * np.pi * fk * t)) / len(y)
    b = 2 * np.dot(y, np.cos(2 * np.pi * fk * t)) / len(y)
    r = least_squares(res, [a, b, fk, 0.0], x_scale=[0.1, 0.1, 1e-3, 1e-3])
    amp = np.hypot(r.x[0], r.x[1])
    thdn = 20 * np.log10(np.sqrt(np.mean(r.fun ** 2)) / (amp / np.sqrt(2)) + 1e-30)
    return r.x[2], amp, thdn


def third_octave_response(x, ref, sr):
    n = len(ref)
    w = np.hanning(n)
    X, R = np.fft.rfft(x * w), np.fft.rfft(ref * w)
    f = np.fft.rfftfreq(n, 1 / sr)
    out = []
    fc = 1000 * 2 ** (np.arange(-14, 14) / 3)
    for c in fc:
        if c < 63 or c > 20000 * 2 ** (-1 / 6):
            continue
        sel = (f >= c * 2 ** (-1 / 6)) & (f < c * 2 ** (1 / 6))
        if not sel.any():
            continue
        out.append((float(c), float(10 * np.log10(np.sum(np.abs(X[sel]) ** 2) / np.sum(np.abs(R[sel]) ** 2)))))
    return out


def peak_dbfs(y, sr, f, width=200.0):
    """Level of the strongest component within f +- width, in dB re amplitude 0.25."""
    w = np.hanning(len(y))
    s = np.abs(np.fft.rfft(y * w)) * 2 / np.sum(w)
    fr = np.fft.rfftfreq(len(y), 1 / sr)
    sel = (fr > f - width) & (fr < f + width)
    return float(20 * np.log10(np.max(s[sel]) / gen.AMP + 1e-30))


APERIODIC = ("sweep", "noise")
WIN_S = 0.1
SEARCH = 1500  # samples either side of the predicted lag


def aperiodic_mask(sr, N, margin_s=0.03):
    """Where a 0.1 s window locates the loop to a fraction of a sample: the
    noise, and the sweep once it passes 1 kHz (below, a window holds a few
    slow cycles and its correlation peak is broad)."""
    m = np.zeros(N, bool)
    a, b = seg_idx("noise", sr)
    m[a + int(margin_s * sr):b - int(margin_s * sr)] = True
    a, b = seg_idx("sweep", sr)
    T = (b - a) / sr
    t1k = T * np.log(1000 / gen.SWEEP_F0) / np.log(gen.SWEEP_F1 / gen.SWEEP_F0)
    m[a + int(t1k * sr):b - int(margin_s * sr)] = True
    return m


def track(x, ref, sr, lag0):
    """Lag per 0.1 s window over the aperiodic parts, following the lag
    from window to window. lag: x[s + i] ~ ref[(s + lag + i) mod N]."""
    N = len(ref)
    win = int(WIN_S * sr)
    ok = aperiodic_mask(sr, N)
    ext = np.concatenate([ref, ref, ref])
    out = []
    lag = lag0
    for s in range(int(SKIP_S * sr), len(x) - win, win // 2):
        p = (s + lag) % N
        pr = int(round(p))
        idx = (pr + np.arange(win)) % N
        if not ok[idx].all():
            continue
        seg = ext[N + pr - SEARCH:N + pr + win + SEARCH]
        xw = x[s:s + win]
        c = np.correlate(seg, xw, "valid")
        j = int(np.argmax(c))
        q = c[j] / np.sqrt(np.sum(xw ** 2) * np.sum(seg[j:j + win] ** 2) + 1e-30)
        jf = float(j)
        if 0 < j < len(c) - 1:
            y0, y1, y2 = c[j - 1], c[j], c[j + 1]
            den = y0 - 2 * y1 + y2
            if den != 0:
                jf = j + 0.5 * (y0 - y2) / den
        new = pr - SEARCH + jf - s
        if q > 0.9:
            pos, g, snr = refine(xw, ref, s + new)
            lag = pos - s
            out.append((s, lag, float(q), float(g), snr))
    return out


def analyse_probe(x, sr, src_sr):
    """Capture of the looped probe at context rate sr, made from src_sr."""
    ref = load_ref(sr, src_sr)
    N = len(ref)
    refm = mask_high(ref, sr)
    s0 = int(SKIP_S * sr)
    xs = x[s0:s0 + N]
    if len(xs) < N:
        return {"error": "capture shorter than one loop"}
    k, corr = circ_lag(xs, refm)
    out = {"corr_first_loop": float(corr)}
    tr = track(x, ref, sr, k - s0)
    out["tracked_windows"] = len(tr)
    if len(tr) < 3:
        out["error"] = "could not track"
        return out
    ts = np.array([t[0] for t in tr]) / sr
    lv = np.array([t[1] for t in tr])
    st = np.diff(lv)
    st = (st + N / 2) % N - N / 2  # the loop wrapping is not a step
    lv = np.r_[lv[0], lv[0] + np.cumsum(st)]
    out["lag_span_samples"] = float(lv.max() - lv.min())
    big = np.abs(st) > 1
    out["lag_steps_over_1_sample"] = int(np.sum(big))
    # a negative step is samples inserted into the capture (it runs behind
    # the source afterwards), a positive one samples dropped; each step is
    # bracketed by the tracked windows either side, in capture time and in
    # the loop's own time, so a step at the loop point can be told apart
    lp = [float(((t[0] + t[1]) % N) / sr) for t in tr]
    out["lag_steps"] = [{"t_s": round(float(ts[i + 1]), 2), "samples": round(float(st[i]), 2),
                         "gap_s": round(float(ts[i + 1] - ts[i]), 2),
                         "from_t_s": round(float(ts[i]), 2),
                         "loop_from_s": round(lp[i], 2), "loop_to_s": round(lp[i + 1], 2)}
                        for i in np.where(big)[0]]
    out["lag_net_samples"] = float(lv[-1] - lv[0])
    smooth = np.abs(st) <= 1
    # drift from the step-free movement only (a steady rate difference)
    out["drift_ppm"] = float(np.sum(st[smooth]) / (ts[-1] - ts[0]) / sr * 1e6) if len(st) else 0.0
    out["track_quality_min"] = float(min(t[2] for t in tr))

    def lag_at(s):
        i = int(np.argmin(np.abs(np.array([t[0] for t in tr]) - s)))
        return tr[i][1]

    def occurrence(name, margin=0):
        """First occurrence of a segment after s0 in the capture, located
        with the lag of the nearest tracked window: (x slice, ref slice)."""
        a, b = seg_idx(name, sr)
        a += margin; b -= margin
        lag = lag_at(s0)
        start = (a - lag - s0) % N + s0
        start = int(round(start))
        lag = lag_at(start)
        start = int(round((a - lag - s0) % N + s0))
        if start + (b - a) > len(x):
            return None, None, None
        return x[start:start + (b - a)], start, lag

    # bit-exactness, and residual against the ideal, per tracked window
    win = int(WIN_S * sr)
    exact = []
    for s_, lag, *_ in tr:
        xw = x[s_:s_ + win]
        if sr == src_sr and abs(lag - round(lag)) < 0.05:
            r = ref[(s_ + int(round(lag)) + np.arange(win)) % N].astype(np.float32)
            exact.append(float(np.mean(xw.astype(np.float32) == r)))
    snr = [t[4] for t in tr]
    # the same, over sweep windows that end below 8 kHz (the voice band)
    a, b = seg_idx("sweep", sr)
    T = (b - a) / sr
    kk = np.log(gen.SWEEP_F1 / gen.SWEEP_F0)
    low = []
    for s_, lag, *rest in tr:
        pe = (s_ + lag + win) % N
        if a <= pe < b and gen.SWEEP_F0 * np.exp((pe - a) / sr / T * kk) <= 8000:
            low.append(rest[2])
    if low:
        out["window_snr_sweep_below_8k_db"] = {"min": float(np.min(low)), "n": len(low)}
    gains = [20 * np.log10(abs(t[3])) for t in tr]
    if exact:
        out["exact_fraction"] = float(np.mean(exact))
        out["windows_fully_exact"] = int(sum(e == 1.0 for e in exact))
        out["windows_checked_exact"] = len(exact)
    out["window_snr_db"] = {"min": float(np.min(snr)), "median": float(np.median(snr))}
    out["window_gain_db"] = {"min": float(np.min(gains)), "max": float(np.max(gains))}
    # gain, from the sweep's occurrence
    y, st0, lag = occurrence("sweep", int(0.05 * sr))
    if y is not None:
        rs = frac_shift(ref, st0 + lag)[:len(y)]
        out["gain_db"] = float(20 * np.log10(abs(np.dot(y, rs) / np.dot(rs, rs))))
    # tones
    tones = {}
    for f in gen.TONES:
        y, _, _ = occurrence(f"tone{int(f)}", int(TONE_MARGIN_S * sr))
        if y is None:
            continue
        fe, amp, thdn = sine_fit(y, sr, f)
        tones[int(f)] = {"cents": float(1200 * np.log2(fe / f)), "thdn_db": float(thdn),
                         "amp_db": float(20 * np.log10(amp / gen.AMP))}
    out["tones"] = tones
    # response from the sweep (+-50 ms)
    a, b = seg_idx("sweep", sr)
    y, st0, lag = occurrence("sweep", -int(0.05 * sr))
    if y is not None:
        rs = frac_shift(ref, st0 + lag)[:len(y)]
        resp = third_octave_response(y, rs, sr)
        ref1k = [d for c, d in resp if abs(c - 1000) < 1][0]
        resp = [(c, d - ref1k) for c, d in resp]
        out["response"] = resp
        out["ripple_80_8k_db"] = float(max(abs(d) for c, d in resp if 80 <= c <= 8000))
        out["ripple_8k_20k_db"] = float(max(abs(d) for c, d in resp if 8000 < c <= 20000))
    # high segment
    y, _, _ = occurrence("high", int(0.05 * sr))
    fh = gen.HIGH.get(src_sr)
    if y is not None:
        if src_sr == 48000 and sr == 44100:
            out["alias_21100_db"] = peak_dbfs(y, sr, 44100 - fh)
        elif src_sr == 44100 and sr == 48000:
            out["tone_21000_db"] = peak_dbfs(y, sr, fh)
            out["image_23100_db"] = peak_dbfs(y, sr, 44100 - fh)
        else:
            out["high_tone_db"] = peak_dbfs(y, sr, fh)
    # noise floor in silence
    y, _, _ = occurrence("silence", int(0.05 * sr))
    if y is not None:
        out["silence_rms_dbfs"] = float(20 * np.log10(np.sqrt(np.mean(y ** 2)) + 1e-30))
        out["silence_exact_zero_fraction"] = float(np.mean(y == 0))
    return out


def analyse_tone(x, sr, f0=1000.0):
    """Firefox's fake microphone: a steady tone. Frequency, THD+N, and
    continuity (one sine fitted per 0.25 s window, phase extrapolated)."""
    s0 = int(SKIP_S * sr)
    y = x[s0:]
    fe, amp, thdn = sine_fit(y[:sr * 2], sr, f0)
    out = {"tone_hz": float(fe), "tone_amp": float(amp), "tone_thdn_db": float(thdn)}
    # global fit over the whole capture: any inserted or dropped sample
    # shows as a phase step
    win = sr // 4
    phases = []
    t = np.arange(win) / sr
    for s in range(0, len(y) - win, win):
        w = y[s:s + win]
        a = 2 * np.dot(w, np.sin(2 * np.pi * fe * t))
        b = 2 * np.dot(w, np.cos(2 * np.pi * fe * t))
        phases.append(np.angle(a + 1j * b))
    ph = np.unwrap(np.array(phases))
    # expected advance per window: 2 pi fe win / sr (already in the fit's frame)
    tt = np.arange(len(ph)) * win / sr
    p = np.polyfit(tt, ph, 1)
    dev = ph - np.polyval(p, tt)
    out["phase_dev_max_samples"] = float(np.max(np.abs(dev)) / (2 * np.pi * fe) * sr)
    out["freq_refined_hz"] = float(fe - p[0] / (2 * np.pi))
    return out


def transport(d, sr):
    frames = np.array(d["frames"])
    recv = np.array(d["recv"])
    done = np.array(d["done"])
    seqs = np.array(d["seqs"])
    out = dict(d["worker"])
    out["blocks"] = int(len(frames))
    step = np.diff(frames)
    out["quanta_skipped"] = int(np.sum(step[step != 128] // 128 - 1)) if len(step) else 0
    out["frame_steps_not_128"] = int(np.sum(step != 128))
    out["seq_gaps"] = int(np.sum(np.diff(seqs) != 1))
    t_audio = (frames - frames[0]) / sr * 1000
    lag = recv - t_audio
    lag -= lag.min()
    out["arrival_lag_ms"] = {"p50": float(np.percentile(lag, 50)), "p99": float(np.percentile(lag, 99)),
                             "max": float(lag.max())}
    behind = done - t_audio
    behind -= behind.min()
    svc = done - recv
    out["service_ms_mean"] = float(np.mean(svc))
    out["period_ms"] = 128 / sr * 1000
    out["utilisation"] = float(np.mean(svc) / (128 / sr * 1000))
    out["behind_end_ms"] = float(behind[-1])
    out["behind_max_ms"] = float(behind.max())
    # clock: context seconds per wall second, from arrival times (robust fit)
    if len(recv) > 100:
        slope = np.polyfit(t_audio, recv - t_audio, 1)[0]
        out["ctx_vs_worker_clock_ppm"] = float(slope * 1e6)
    return out


def main():
    runs = []
    for js in sorted(glob.glob(f"{RAW}/*.json")):
        d = json.load(open(js))
        name = os.path.basename(js)[:-5]
        c = d["condition"]
        r = {"name": name, "browser": d["browser"], "version": d["version"], "condition": c,
             "rep": d["rep"], "ctxRate": d.get("ctxRate"), "settings": d.get("settings")}
        for k in ("error", "ctxError", "sourceError", "workerTimeout"):
            if d.get(k):
                r[k] = d[k]
        if "worker" not in d:
            runs.append(r)
            continue
        sr = d["ctxRate"]
        r["tap"] = d["tap"]["stats"]
        r["clock"] = d["clock"]
        r["drainMs"] = d["drainMs"]
        r["transport"] = transport(d, sr)
        x = np.fromfile(f"{RAW}/{name}.f32", "<f4").astype(np.float64)
        if c["path"] == "mic" and d["browser"] == "firefox":
            r["signal"] = analyse_tone(x, sr)
        else:
            src = c.get("srcRate") or c.get("fakeRate")
            r["signal"] = analyse_probe(x, sr, src)
        runs.append(r)
        s = r["signal"]
        print(name, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items() if k not in ("response", "tones")},
              {k: round(v["cents"], 4) for k, v in s.get("tones", {}).items()})
    json.dump(runs, open("results/runs.json", "w"), indent=1)


if __name__ == "__main__":
    main()
