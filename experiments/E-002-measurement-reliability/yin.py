"""YIN at squillo's frame axis (squillo ADR 0007). Crude experiment code.

de Cheveigne and Kawahara (2002), doi:10.1121/1.1458024, steps 1 to 4:
difference function, cumulative mean normalised difference (CMND), absolute
threshold, parabolic interpolation. Step 5 (best local estimate) and step 6
are not used: squillo needs a frame's pitch final when computed.

Frame i holds samples 384i .. 384i+383; its pitch window is the 1536
samples ending with frame i (frames 0..2 are not applicable).
"""

import numpy as np

SR = 48_000
HOP = 384
WIN = 1536
E2 = 440.0 * 2 ** (-29 / 12)
C6 = 440.0 * 2 ** (15 / 12)


def cents(f, ref):
    return 1200.0 * np.log2(np.asarray(f) / np.asarray(ref))


def frame_windows(x):
    n_frames = len(x) // HOP
    idx = np.arange(3, n_frames)
    starts = HOP * (idx - 3)
    win = np.stack([x[s:s + WIN] for s in starts]) if len(idx) else np.zeros((0, WIN))
    return idx, win


def cmnd(win, tau_max, dtype=np.float64):
    """Difference function d and CMND d' for each row of win (frames x WIN)."""
    w = win.astype(dtype)
    W = WIN - tau_max
    n_fft = 1 << int(np.ceil(np.log2(WIN + W)))
    a = np.fft.rfft(w[:, :W], n_fft)
    b = np.fft.rfft(w, n_fft)
    # r[t] = sum_{j<W} x[j] x[j+t]
    r = np.fft.irfft(np.conj(a) * b, n_fft)[:, :tau_max + 1].astype(dtype)
    sq = np.concatenate([np.zeros((w.shape[0], 1), dtype), np.cumsum(w * w, axis=1)], axis=1)
    e0 = sq[:, W:W + 1]
    taus = np.arange(tau_max + 1)
    et = sq[:, taus + W] - sq[:, taus]
    d = e0 + et - 2 * r
    d[:, 0] = 0
    d = np.maximum(d, 0)
    cs = np.cumsum(d[:, 1:], axis=1)
    dn = np.ones_like(d)
    with np.errstate(divide="ignore", invalid="ignore"):
        dn[:, 1:] = np.where(cs > 0, d[:, 1:] * taus[1:] / cs, 1.0)
    return d, dn


def parabola(y, t):
    a, b, c = y[t - 1], y[t], y[t + 1]
    den = a - 2 * b + c
    if den <= 0:
        return float(t)
    return t + 0.5 * (a - c) / den


def yin(x, threshold=0.1, f_lo=63.0, f_hi=3000.0, interp="d", dtype=np.float64, octave_check=False):
    """Return (frame indices, f0 in Hz or nan, min CMND) for frames 3..n-1.

    The lag search spans periods of f_hi to f_lo (default 3000 Hz to 63 Hz,
    wider than E2..C6 so that out-of-range tones are found, then refused).
    No dip under the threshold means unmeasurable (nan).
    """
    idx, win = frame_windows(np.asarray(x))
    tau_min = int(np.floor(SR / f_hi))
    tau_max = int(np.ceil(SR / f_lo)) + 1
    assert tau_max < WIN // 2 + 2, "window too short for f_lo"
    d, dn = cmnd(win, tau_max, dtype)
    f0 = np.full(len(idx), np.nan)
    dmin = np.full(len(idx), np.nan)
    for k in range(len(idx)):
        row = dn[k]
        below = np.nonzero(row[tau_min:tau_max] < threshold)[0]
        if len(below) == 0:
            dmin[k] = row[tau_min:tau_max].min()
            continue
        t = tau_min + below[0]
        while t + 1 < tau_max and row[t + 1] < row[t]:
            t += 1
        if octave_check:  # E-002 round 2 variant: prefer a deeper dip at twice the lag
            lo2, hi2 = 2 * t - 3, min(2 * t + 4, tau_max - 1)
            if lo2 < hi2:
                t2 = lo2 + int(np.argmin(row[lo2:hi2]))
                if row[t2] < row[t] and lo2 < t2 < hi2 - 1:
                    t = t2
        dmin[k] = row[t]
        if t <= tau_min or t >= tau_max - 1:
            continue
        y = d[k] if interp == "d" else row
        f0[k] = SR / parabola(y.astype(np.float64), t)
    return idx, f0, dmin


def in_range(f0, margin_cents):
    lo = E2 * 2 ** (-margin_cents / 1200)
    hi = C6 * 2 ** (margin_cents / 1200)
    return np.where((f0 >= lo) & (f0 <= hi), f0, np.nan)
