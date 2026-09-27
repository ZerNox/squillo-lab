"""E-003: generate the probe signal at 48 000 and 44 100 Hz.

One 8-second loop, the same segments at both rates (seconds):
  0.50-2.50  exponential sweep 50 Hz -> 20 kHz, amplitude 0.25
  3.00-5.00  pure tones 110, 220, 440, 880 Hz, 0.5 s each, amplitude 0.25
  0.05-0.45  digital silence (noise floor)
  5.25-6.25  high tone: 23 kHz at 48 kHz (above 44.1 kHz's Nyquist: aliasing
             test), 21 kHz at 44.1 kHz (image at 23.1 kHz inside 48 kHz's
             band: imaging test), amplitude 0.25
  6.50-7.90  white noise band-limited to 20 kHz, RMS 0.05, fixed seed; the
             same noise at both rates (made at 48 kHz, resampled to 44.1 kHz
             by a polyphase filter). With the sweep, the aperiodic parts that
             locate the loop unambiguously, so a dropped or inserted sample
             shows as a lag step
  elsewhere  digital silence
Each segment has 10 ms raised-cosine ramps. Quantized to 16-bit PCM (round,
no dither), so the float the browser should deliver is exactly int16 / 32768.

Written: data/cache/probe<rate>.wav (for Chrome's fake capture) and
data/cache/probe<rate>.f32 (the same values as little-endian float32, for the
stream path). Conditions are asserted on the output (squillo S15).
"""
import json
import numpy as np
from scipy.signal import resample_poly
import soundfile as sf

LOOP_S = 8.0
AMP = 0.25
NOISE_RMS = 0.05
TONES = [110.0, 220.0, 440.0, 880.0]
E2, C6 = 82.4069, 1046.502  # squillo ADR 0007's pitch range
SEGMENTS = {
    "sweep": (0.50, 2.50),
    "tone110": (3.00, 3.50), "tone220": (3.50, 4.00),
    "tone440": (4.00, 4.50), "tone880": (4.50, 5.00),
    "high": (5.25, 6.25),
    "silence": (0.05, 0.45),
    "noise": (6.50, 7.90),
}
SWEEP_F0, SWEEP_F1 = 50.0, 20000.0
HIGH = {48000: 23000.0, 44100: 21000.0}


def ramp(n, sr, ramp_s=0.010):
    r = int(round(ramp_s * sr))
    w = np.ones(n)
    h = 0.5 - 0.5 * np.cos(np.pi * np.arange(r) / r)
    w[:r] = h
    w[-r:] = h[::-1]
    return w


def probe(sr):
    n = int(round(LOOP_S * sr))
    x = np.zeros(n)
    a, b = (int(round(v * sr)) for v in SEGMENTS["sweep"])
    t = np.arange(b - a) / sr
    T = (b - a) / sr
    k = np.log(SWEEP_F1 / SWEEP_F0)
    phase = 2 * np.pi * SWEEP_F0 * T / k * (np.exp(t / T * k) - 1)
    x[a:b] = AMP * np.sin(phase) * ramp(b - a, sr)
    for f in TONES:
        a, b = (int(round(v * sr)) for v in SEGMENTS[f"tone{int(f)}"])
        t = np.arange(b - a) / sr
        x[a:b] = AMP * np.sin(2 * np.pi * f * t) * ramp(b - a, sr)
    a, b = (int(round(v * sr)) for v in SEGMENTS["high"])
    t = np.arange(b - a) / sr
    x[a:b] = AMP * np.sin(2 * np.pi * HIGH[sr] * t) * ramp(b - a, sr)
    a, b = (int(round(v * 48000)) for v in SEGMENTS["noise"])
    rng = np.random.default_rng(3)
    nz = rng.standard_normal(b - a)
    F = np.fft.rfft(nz)
    F[np.fft.rfftfreq(b - a, 1 / 48000) > 20000] = 0
    nz = np.fft.irfft(F, b - a)
    if sr != 48000:
        nz = resample_poly(nz, 147, 160)
    nz = nz / np.sqrt(np.mean(nz ** 2)) * NOISE_RMS
    a, b = (int(round(v * sr)) for v in SEGMENTS["noise"])
    nz = nz[:b - a]
    x[a:a + len(nz)] = nz * ramp(len(nz), sr)
    q = np.round(np.clip(x, -1, 1) * 32768).astype(np.int16)
    return q


def check(sr, q):
    """S15: every condition asserted on the generated output."""
    y = q.astype(np.float64) / 32768
    checks = {}
    a, b = (int(round(v * sr)) for v in SEGMENTS["noise"])
    peak = float(np.max(np.abs(np.r_[y[:a], y[b:]])))
    assert peak <= AMP + 1 / 32768, peak
    checks["peak_outside_noise"] = peak
    # tones inside the pitch range, measured from the output by FFT peak
    for f in TONES:
        assert E2 <= f <= C6
        a, b = (int(round(v * sr)) for v in SEGMENTS[f"tone{int(f)}"])
        seg = y[a:b] * np.hanning(b - a)
        spec = np.abs(np.fft.rfft(seg, 1 << 22))
        fpk = np.argmax(spec) * sr / (1 << 22)
        assert abs(1200 * np.log2(fpk / f)) < 1.0, (f, fpk)
        checks[f"tone{int(f)}_measured_hz"] = round(float(fpk), 3)
    # sweep's top below this file's Nyquist, and inside 20 kHz
    assert SWEEP_F1 < sr / 2
    # high tone: below own Nyquist; for 48 kHz above 44.1 kHz's Nyquist
    # (it must alias if not filtered); for 44.1 kHz its image 44.1k - f
    # lies below 48 kHz's Nyquist
    fh = HIGH[sr]
    a, b = (int(round(v * sr)) for v in SEGMENTS["high"])
    spec = np.abs(np.fft.rfft(y[a:b] * np.hanning(b - a), 1 << 22))
    fpk = np.argmax(spec) * sr / (1 << 22)
    assert abs(fpk - fh) < 1.0, fpk
    checks["high_measured_hz"] = round(float(fpk), 3)
    assert fh < sr / 2
    if sr == 48000:
        assert fh > 44100 / 2
        checks["high_alias_at_44100_hz"] = 44100 - fh
    else:
        assert 44100 - fh < 48000 / 2
        checks["high_image_at_48000_hz"] = 44100 - fh
    # noise: RMS as specified, nothing above 20 kHz (beyond the ramps), no clipping
    a, b = (int(round(v * sr)) for v in SEGMENTS["noise"])
    r0 = int(0.02 * sr)
    nzq = y[a + r0:b - r0]
    rms = float(np.sqrt(np.mean(nzq ** 2)))
    assert abs(rms / NOISE_RMS - 1) < 0.02, rms
    sp = np.abs(np.fft.rfft(nzq * np.hanning(len(nzq)))) ** 2
    fr = np.fft.rfftfreq(len(nzq), 1 / sr)
    above = 10 * np.log10(np.sum(sp[fr > 20500]) / np.sum(sp) + 1e-30)
    assert above < -60, above
    assert np.max(np.abs(q)) < 32767
    checks["noise_rms"] = round(rms, 5)
    checks["noise_energy_above_20500_db"] = round(float(above), 1)
    checks["peak_int16"] = int(np.max(np.abs(q)))
    # silence is digital zero
    a, b = (int(round(v * sr)) for v in SEGMENTS["silence"])
    assert np.all(q[a:b] == 0)
    # loop is continuous: starts and ends at zero
    assert q[0] == 0 and q[-1] == 0
    # segments do not overlap
    iv = sorted(SEGMENTS.values())
    assert all(iv[i][1] <= iv[i + 1][0] for i in range(len(iv) - 1)), iv
    return checks


def main():
    out = {}
    for sr in (48000, 44100):
        q = probe(sr)
        out[sr] = check(sr, q)
        sf.write(f"data/cache/probe{sr}.wav", q, sr, subtype="PCM_16")
        (q.astype(np.float32) / 32768).astype("<f4").tofile(f"data/cache/probe{sr}.f32")
        # verify the WAV round-trips exactly
        r, rs = sf.read(f"data/cache/probe{sr}.wav", dtype="int16")
        assert rs == sr and np.array_equal(r, q)
    # the needs-human step's tone, played from a phone: 440 Hz (inside
    # E2-C6), 12 s, amplitude 0.5, 50 ms ramps
    sr = 48000
    n = 12 * sr
    tone = 0.5 * np.sin(2 * np.pi * 440.0 * np.arange(n) / sr) * ramp(n, sr, 0.05)
    tq = np.round(tone * 32768).astype(np.int16)
    assert np.max(np.abs(tq)) <= 16384 and E2 <= 440.0 <= C6
    sf.write("data/cache/tone440.wav", tq, sr, subtype="PCM_16")
    with open("results/probe_checks.json", "w") as f:
        json.dump({"segments": SEGMENTS, "tones": TONES, "high": HIGH,
                   "checks": out}, f, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
