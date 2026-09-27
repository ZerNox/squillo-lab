"""E-002 round 2, step 2: YIN on real voices with a known f0, clean and in
noise and reverberation; and the ring ratio of the original takes. Crude
experiment code. Needs data/cache/r2/*.npz from r2_truth.py.

    uv run python r2_run.py        # writes data/cache/r2_frames.npz, data/cache/r2_tone.json

Conditions, written down before generating (squillo S15). Each is asserted
on what was generated:

- clean: the re-synthesis as it is.
- white-30, white-20, white-10: white Gaussian noise over 0-24 kHz; SNR is
  the RMS of the take over its voiced samples (truth f0 > 0) against the
  noise's RMS, asserted within 0.01 dB from the generated arrays.
- pink-20, pink-10: noise with power falling 10 dB per decade (1/f) from
  20 Hz to 24 kHz, nothing below; same SNR rule; the slope, fitted to its
  Welch spectrum between 100 Hz and 10 kHz, asserted within 5 % of -10 dB
  per decade.
- room-0.4, room-0.8: convolution with an impulse response of a direct
  impulse at 0 and an exponentially decaying Gaussian tail from 2.5 ms
  (Polack's model), RT60 0.4 s with direct-to-reverberant ratio +6 dB, and
  RT60 0.8 s with DRR 0 dB. RT60 asserted within 5 % from the response's
  Schroeder decay (T20: the -5 to -25 dB span, times 3); DRR within 0.1 dB.
- original: the unmodified take (resampled to 48 kHz), clean, against
  Harvest's f0 of that take: an agreement of two trackers, not an error.

A frame is *valid* for pitch when every truth sample of its 1536-sample
window is voiced, inside E2..C6 (yin.E2, yin.C6, from their semitone numbers),
and the truth moves at most 200 cents across the window (Harvest's octave
jumps excluded). Truth for a frame: the f0 at SG-007's instant,
384 i - 766 + P/2 with P = 48000 / f, f the reported pitch (the truth's own f0
for refused frames). Reverberation: the truth is the direct sound's.
"""

import json
import zlib
from multiprocessing import Pool

import numpy as np
from scipy.signal import fftconvolve, welch

import r2_truth as T
import yin
from yin import SR, E2, C6

SEED = 20260928
CONDS = ["clean", "white-30", "white-20", "white-10", "pink-20", "pink-10", "room-0.4", "room-0.8", "original"]
ROOMS = {"room-0.4": (0.4, 6.0), "room-0.8": (0.8, 0.0)}
RING_LO, RING_HI = (50.0, 2000.0), (2000.0, 4000.0)  # Hz: SPR's two bands (Omori et al. 1996), DC and rumble below 50 Hz left out


def rng_for(name, cond):
    return np.random.default_rng([SEED, zlib.crc32(f"{name}/{cond}".encode())])


def pink(n, rng):
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    g = np.where(f >= 20.0, 1 / np.sqrt(np.maximum(f, 1e-9)), 0.0)
    return np.fft.irfft(X * g, n)


def check_pink(nz):
    fr, P = welch(nz, SR, nperseg=8192)
    m = (fr >= 100) & (fr <= 10_000)
    slope = np.polyfit(np.log10(fr[m]), 10 * np.log10(P[m]), 1)[0]
    assert abs(slope + 10) <= 0.5, slope
    return float(slope)


def rir(rt60, drr_db, rng):
    n = int(1.5 * rt60 * SR)
    t = np.arange(n) / SR
    tail = rng.standard_normal(n) * np.exp(-6.908 * t / rt60)
    tail[t < 0.0025] = 0
    tail *= np.sqrt(1.0 / np.sum(tail ** 2) / 10 ** (drr_db / 10))
    h = tail.copy(); h[0] = 1.0
    # checks from the generated response
    drr = 10 * np.log10(h[0] ** 2 / np.sum(h[1:] ** 2))
    edc = 10 * np.log10(np.cumsum((h ** 2)[::-1])[::-1] / np.sum(h ** 2))
    i5, i25 = np.argmax(edc <= -5), np.argmax(edc <= -25)
    slope = np.polyfit(t[i5:i25], edc[i5:i25], 1)[0]
    t60 = -60 / slope
    assert abs(drr - drr_db) <= 0.1 and abs(t60 - rt60) <= 0.05 * rt60, (rt60, drr_db, t60, drr)
    return h, dict(rt60_measured=float(t60), drr_measured=float(drr))


def condition(sig, voiced, name, cond):
    rng = rng_for(name, cond)
    info = {}
    if cond in ("clean", "original"):
        return sig, info
    if cond.startswith(("white", "pink")):
        snr = float(cond.split("-")[1])
        nz = rng.standard_normal(len(sig)) if cond.startswith("white") else pink(len(sig), rng)
        if cond.startswith("pink"):
            info["pink_slope_dB_per_decade"] = check_pink(nz)
        nz *= np.sqrt(np.mean(sig[voiced] ** 2) / np.mean(nz ** 2) / 10 ** (snr / 10))
        got = 10 * np.log10(np.mean(sig[voiced] ** 2) / np.mean(nz ** 2))
        assert abs(got - snr) <= 0.01, (name, cond, got)
        info["snr_measured"] = float(got)
        return sig + nz, info
    rt60, drr = ROOMS[cond]
    h, info = rir(rt60, drr, rng)
    return fftconvolve(sig, h)[: len(sig)], info


def frame_truth(ft, idx, f):
    """Truth at SG-007's instant, validity per frame."""
    s = 384 * (idx - 3)
    ok = ~np.isnan(f)
    ref = np.array([ft[a:a + 1536] for a in s])
    allv = (ref > 0).all(1)
    safe = np.where(ref > 0, ref, 1.0)
    rng_c = 1200 * np.log2(safe.max(1) / safe.min(1))
    inr = (ref >= E2).all(1) & (ref <= C6).all(1)
    valid = allv & inr & (rng_c <= 200)
    f_true_c = ft[np.clip(s + 1536 // 2, 0, len(ft) - 1)]
    P = SR / np.where(ok, f, np.where(f_true_c > 0, f_true_c, 220.0))
    pos = np.clip(np.round(384 * idx - 766 + P / 2).astype(int), 0, len(ft) - 1)
    # also: the geometric mean of the truth over the samples YIN compares, s .. s + 773 + P
    cl = np.concatenate([[0.0], np.cumsum(np.log(np.where(ft > 0, ft, 1.0)))])
    end = np.clip(s + 773 + np.round(P).astype(int), 0, len(ft))
    f_mean = np.exp((cl[end] - cl[s]) / np.maximum(end - s, 1))
    return ft[pos], f_mean, valid


def ring_blocks(sig, idx, f):
    """Ring ratio per 1 s block (125 frames): L(2-4 kHz) - L(50 Hz-2 kHz), dB, from the
    Hann-windowed power spectra of the pitch windows of the frames YIN measured."""
    fr = np.fft.rfftfreq(1536, 1 / SR)
    lo = (fr >= RING_LO[0]) & (fr < RING_LO[1]); hi = (fr >= RING_HI[0]) & (fr < RING_HI[1])
    w = np.hanning(1536)
    out = []
    for b0 in range(0, len(idx) - 124, 125):
        sel = [k for k in range(b0, b0 + 125) if not np.isnan(f[k])]
        if len(sel) < 60:
            continue
        W = np.stack([sig[384 * (idx[k] - 3): 384 * (idx[k] - 3) + 1536] * w for k in sel])
        P = (np.abs(np.fft.rfft(W, axis=1)) ** 2).sum(0)
        out.append(dict(block=b0 // 125, frames=len(sel), ring=float(10 * np.log10(P[hi].sum() / P[lo].sum()))))
    return out


def one(path):
    z = np.load(T.R2 / (path.stem + ".npz"))
    x, y, f0 = z["x"].astype(np.float64), z["y"].astype(np.float64), z["f0"]
    ft = T.truth_per_sample(f0, len(x))
    voiced = ft > 0
    frames, tone, infos = {}, {}, {}
    for cond in CONDS:
        base = x if cond == "original" else y
        sig, info = condition(base, voiced, path.stem, cond)
        infos[cond] = info
        idx, f, dip = yin.yin(sig)
        f = yin.in_range(f, 3.0)
        f_true, f_mean, valid = frame_truth(ft, idx, f)
        frames[cond] = dict(idx=idx, f=f, dip=dip, f_true=f_true, f_true_mean=f_mean, valid=valid)
        # tone on the original take under the same condition (reverb and noise applied to x)
        if cond != "original":
            sx, _ = condition(x, voiced, path.stem, cond)
            i2, f2, _ = yin.yin(sx)
            tone[cond] = ring_blocks(sx, i2, yin.in_range(f2, 3.0))
    return path.stem, frames, tone, infos


def main():
    fs = T.files()
    with Pool(16) as pool:
        res = pool.map(one, fs)
    arrays = {}
    meta = []
    for k, (name, frames, tone, infos) in enumerate(res):
        meta.append(dict(name=name, set=T.set_of(name), singer=T.singer_of(name), conditions=infos))
        for cond, d in frames.items():
            for key, v in d.items():
                arrays.setdefault(f"{cond}/{key}", []).append(v)
            arrays.setdefault(f"{cond}/file", []).append(np.full(len(d["idx"]), k))
    np.savez_compressed(T.CACHE / "r2_frames.npz", **{k: np.concatenate(v) for k, v in arrays.items()})
    (T.CACHE / "r2_tone.json").write_text(json.dumps(dict(meta=meta, tone={r[0]: r[2] for r in res})))
    snr = [i["snr_measured"] for m in meta for c, i in m["conditions"].items() if "snr_measured" in i]
    rt = {c: [m["conditions"][c]["rt60_measured"] for m in meta] for c in ROOMS}
    print("files", len(meta), "SNR checks", len(snr), "RT60 measured", {c: (min(v), max(v)) for c, v in rt.items()})
    n_valid = {c: int(np.concatenate(arrays[f"{c}/valid"]).sum()) for c in CONDS}
    print("valid frames", n_valid)


if __name__ == "__main__":
    main()
