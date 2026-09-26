"""Reference-free intent inference from a pitch track. Crude experiment code.

Input: per-frame pitch in cents re A4 (nan where unvoiced) on squillo's frame
axis (ADR 0007: 384-sample frames at 48 kHz, E-002's YIN). Output per note
segment: settle pitch, inferred target, deviation, margin to the nearest
decision boundary, and a standard uncertainty for the deviation.

Steps:
  1. Segment: voiced runs, a 200 ms running median, quantise to semitones
     against a provisional reference, merge runs shorter than 64 ms.
     Or take oracle boundaries (known by construction or by score alignment).
  2. Settle pitch: median of the raw frames from 30 % to 90 % of the segment
     (skips onset scoops and the glide into the next note).
  3. Reference r (the singer's own tuning, cents mod 100): 'fixed' (A4 = 440),
     'global' (duration-weighted circular mean of settle pitches mod 100),
     'local' (the same, weighted also by a Gaussian of 2 s in time).
  4. Target: 'chromatic' (nearest semitone on r), 'key' (nearest member of the
     best-fitting diatonic or harmonic-minor set, fitted on a Gaussian time
     window of 2 s), 'hybrid' (chromatic when within 25 cents of a semitone
     or when that semitone is in the key, else key).
"""

import numpy as np

HOP_S = 384 / 48_000
DIATONIC = [0, 2, 4, 5, 7, 9, 11]
HARM_MINOR = [0, 2, 3, 5, 7, 8, 11]
SETS = [frozenset((t + d) % 12 for d in s) for s in (DIATONIC, HARM_MINOR) for t in range(12)]
TAU = 0.1      # s, assumed correlation time of within-note wobble (for n_eff)
U_TRACK = 1.0  # cents, tracker standard uncertainty (E-002: harmonic tones max 0.98)


def running_median(x, k):
    h = k // 2
    xp = np.pad(x, h, mode="edge")
    return np.median(np.lib.stride_tricks.sliding_window_view(xp, k), axis=1)


def circ_mean(c, w):
    z = np.sum(w * np.exp(2j * np.pi * np.asarray(c) / 100.0))
    return 100.0 / (2 * np.pi) * np.angle(z)


def segment(cents, min_frames=8, med=25, gap=3):
    """Return list of (start, end) frame index pairs, end exclusive."""
    v = ~np.isnan(cents)
    n = len(cents)
    # bridge unvoiced gaps of at most `gap` frames inside voiced runs
    vb = v.copy()
    i = 0
    while i < n:
        if not v[i]:
            j = i
            while j < n and not v[j]:
                j += 1
            if 0 < i and j < n and j - i <= gap:
                vb[i:j] = True
            i = j
        else:
            i += 1
    runs, i = [], 0
    while i < n:
        if vb[i]:
            j = i
            while j < n and vb[j]:
                j += 1
            runs.append((i, j))
            i = j
        else:
            i += 1
    ok = cents[v]
    r0 = circ_mean(ok, np.ones(len(ok)))
    segs = []
    for a, b in runs:
        if b - a < min_frames:
            continue
        x = cents[a:b].copy()
        good = ~np.isnan(x)
        x[~good] = np.interp(np.flatnonzero(~good), np.flatnonzero(good), x[good])
        sm = running_median(x, min(med, (b - a) | 1))
        q = np.round((sm - r0) / 100.0)
        cuts = [0] + [k for k in range(1, len(q)) if q[k] != q[k - 1]] + [len(q)]
        parts = [[cuts[k], cuts[k + 1], q[cuts[k]]] for k in range(len(cuts) - 1)]
        merged = True
        while merged and len(parts) > 1:
            merged = False
            lens = [p[1] - p[0] for p in parts]
            k = int(np.argmin(lens))
            if lens[k] >= min_frames:
                break
            if k == 0:
                nb = 1
            elif k == len(parts) - 1:
                nb = k - 1
            else:
                nb = k - 1 if abs(parts[k - 1][2] - parts[k][2]) <= abs(parts[k + 1][2] - parts[k][2]) else k + 1
            lo, hi = min(k, nb), max(k, nb)
            parts[lo] = [parts[lo][0], parts[hi][1], parts[nb][2]]
            del parts[hi]
            merged = True
            # join neighbours that now share a semitone
            m = 0
            while m < len(parts) - 1:
                if parts[m][2] == parts[m + 1][2]:
                    parts[m] = [parts[m][0], parts[m + 1][1], parts[m][2]]
                    del parts[m + 1]
                else:
                    m += 1
        segs += [(a + p[0], a + p[1]) for p in parts if p[1] - p[0] >= 1]
    return segs


def settle(cents, segs):
    out = []
    for a, b in segs:
        L = b - a
        lo, hi = a + int(0.3 * L), a + max(int(0.9 * L), int(0.3 * L) + 1)
        x = cents[lo:hi]
        x = x[~np.isnan(x)]
        if len(x) == 0:
            x = cents[a:b][~np.isnan(cents[a:b])]
        dur = L * HOP_S
        n_eff = max(1.0, len(x) * HOP_S / TAU)
        sd = np.std(x) if len(x) > 1 else 0.0
        # median's standard error ~ 1.2533 sd / sqrt(n_eff)
        out.append((np.median(x), dur, np.hypot(1.2533 * sd / np.sqrt(n_eff), U_TRACK)))
    return np.array(out).reshape(-1, 3)


def infer(cents, segs, ref="global", snap="hybrid", t_sigma=2.0):
    """Return dict of per-segment arrays."""
    st = settle(cents, segs)
    s, dur, u_s = st[:, 0], st[:, 1], st[:, 2]
    mid = np.array([(a + b) / 2 * HOP_S for a, b in segs])
    n = len(s)
    if ref == "fixed":
        r = np.zeros(n)
    elif ref == "global":
        r = np.full(n, circ_mean(s, dur))
    else:
        r = np.array([circ_mean(s, dur * np.exp(-0.5 * ((mid - m) / t_sigma) ** 2)) for m in mid])
        r = np.unwrap(r, period=100.0)  # a drifting reference must not jump a semitone
    rel = s - r
    m_chrom = np.round(rel / 100.0)
    dev_c = rel - 100 * m_chrom
    target = m_chrom.copy()
    margin = 50 - np.abs(dev_c)
    in_key = np.ones(n, bool)
    if snap in ("key", "hybrid"):
        for i in range(n):
            w = dur * np.exp(-0.5 * ((mid - mid[i]) / t_sigma) ** 2)
            best, bc = None, np.inf
            for S in SETS:
                members = np.array(sorted(S))
                pc = np.mod(rel, 1200.0) / 100.0  # fractional pitch class
                d = np.abs(((pc[:, None] - members[None, :] + 6) % 12) - 6).min(axis=1)
                c = np.sum(w * np.minimum(d, 1.0) ** 2)
                if c < bc:
                    best, bc = members, c
            # nearest member of best set, in absolute semitones
            cand = np.floor(rel[i] / 100.0 / 12) * 12 + np.concatenate([best - 12, best, best + 12])
            dist = np.abs(rel[i] / 100.0 - cand)
            k = int(np.argmin(dist))
            m_key = cand[k]
            in_key[i] = (m_chrom[i] % 12) in set(best.tolist())
            use_key = snap == "key" or (not in_key[i] and abs(dev_c[i]) > 25)
            if use_key:
                target[i] = m_key
                srt = np.sort(cand)
                j = int(np.searchsorted(srt, m_key))
                lo_b = (srt[j - 1] + m_key) / 2 if j > 0 else m_key - 0.5
                hi_b = (srt[j + 1] + m_key) / 2 if j + 1 < len(srt) else m_key + 0.5
                margin[i] = 100 * min(rel[i] / 100 - lo_b, hi_b - rel[i] / 100)
            elif snap == "hybrid" and not in_key[i]:
                margin[i] = 25 - abs(dev_c[i])  # distance to the hybrid's own rule
    dev = rel - 100 * target
    # reference uncertainty: sd of deviations over the effective count
    wn = dur if ref != "fixed" else None
    if wn is not None:
        n_eff = wn.sum() ** 2 / np.sum(wn ** 2)
        u_r = np.sqrt(np.sum(wn * (dev - np.average(dev, weights=wn)) ** 2) / wn.sum()) / np.sqrt(n_eff)
    else:
        u_r = 0.0
    return dict(settle=s, dur=dur, mid=mid, ref=r, target=target, dev=dev,
                margin=margin, u_settle=u_s, u_ref=np.full(n, u_r), in_key=in_key)


def circ_sigma(dev, w):
    """Wrapped-normal spread (cents) of deviations on a 100-cent circle.

    Invariant to which semitone a note was attributed to, so misattribution
    cannot shrink it. Mean resultant length R, bias-corrected for the
    effective count (R^2 -> (n R^2 - 1) / (n - 1)); sigma = P / (2 pi)
    sqrt(-2 ln R), P = 100 cents. Returns inf when R^2 is not above chance.
    """
    w = np.asarray(w, float)
    z = np.sum(w * np.exp(2j * np.pi * np.asarray(dev) / 100.0)) / w.sum()
    n = w.sum() ** 2 / np.sum(w ** 2)
    r2 = (n * abs(z) ** 2 - 1) / (n - 1) if n > 1 else 0.0
    if r2 <= 0:
        return np.inf
    return 100.0 / (2 * np.pi) * np.sqrt(-np.log(min(r2, 1 - 1e-12)))


def p_attrib(dev, sigma):
    """Posterior that a note's attributed semitone is the one aimed for,
    assuming wrapped-normal errors of spread sigma and equal priors."""
    dev = np.asarray(dev, float)
    if not np.isfinite(sigma):
        return np.zeros_like(dev)
    sigma = max(sigma, 1.0)
    k = np.arange(-3, 4)
    lik = np.exp(-0.5 * ((dev[:, None] + 100.0 * k[None, :]) / sigma) ** 2)
    return lik[:, 3] / lik.sum(axis=1)
