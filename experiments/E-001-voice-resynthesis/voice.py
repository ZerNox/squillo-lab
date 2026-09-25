"""Synthetic sung phrases with a known intended contour and known errors.

Crude experiment code. Additive source-filter synthesis at 48 kHz: harmonic k
of a continuous-phase f0 contour, amplitude 1/k (glottal source -12 dB/oct plus
lip radiation +6 dB/oct) times a fixed five-formant vowel envelope evaluated at
k*f0(t); aspiration noise through the same formants, 30 dB under the voice.
Formants F1-F3 of /a/: Peterson and Barney (1952), men's and women's means;
F4, F5 and all bandwidths: Klatt (1980) defaults; resonances above F5 are
a crude higher-pole correction (below), so the spectrum above 5 kHz does not
fall at -60 dB/octave. The melody is a scale
fragment (degrees 0 2 4 5 7 5 4 2 0 semitones), not taken from any work.
"""

import numpy as np
from scipy.signal import butter, sosfiltfilt, lfilter

SR = 48_000
FORMANTS = {  # (F, B) in Hz
    "male": [(730, 80), (1090, 90), (2440, 120), (3300, 250), (3750, 200)],
    "female": [(850, 80), (1220, 90), (2810, 120), (4000, 250), (4500, 200)],
}
# Higher-pole correction: resonances continue above F5 as in a uniform tube,
# every 1000 Hz (male) or 1150 Hz (female) up to 20 kHz, bandwidths widening.
for sex, step in (("male", 1000.0), ("female", 1150.0)):
    f = FORMANTS[sex][-1][0] + step
    while f < 20_000:
        FORMANTS[sex].append((f, 200.0 + 0.08 * (f - 4000.0)))
        f += step
VOICES = {  # name: (sex, base note in semitones re A4)
    "bass": ("male", -24),        # A2 110 Hz
    "baritone": ("male", -21),    # C3
    "tenor": ("male", -17),       # E3
    "mezzo": ("female", -12),     # A3
    "soprano": ("female", -7),    # D4
    "soprano_high": ("female", 0),  # A4 to E5
}
DEGREES = [0, 2, 4, 5, 7, 5, 4, 2, 0]
NOTE_S, XFADE_S = 0.45, 0.06


def envelope(sex, f):
    """Magnitude of the cascade of Klatt resonators at frequencies f (DC gain 1)."""
    h = np.ones_like(f)
    for F, B in FORMANTS[sex]:
        r = np.exp(-np.pi * B / SR)
        c1, c2 = 2 * r * np.cos(2 * np.pi * F / SR), -r * r
        z1 = np.exp(-2j * np.pi * f / SR)
        h = h * np.abs((1 - c1 - c2) / (1 - c1 * z1 - c2 * z1 * z1))
    return h


_GRID = np.arange(0.0, SR / 2 + 0.5, 0.5)
_TABLE = {}


def envelope_fast(sex, f):
    """envelope() by linear interpolation on a 0.5 Hz grid."""
    if sex not in _TABLE:
        _TABLE[sex] = envelope(sex, _GRID)
    return np.interp(f, _GRID, _TABLE[sex])


def formant_filter(sex, x):
    for F, B in FORMANTS[sex]:
        r = np.exp(-np.pi * B / SR)
        c1, c2 = 2 * r * np.cos(2 * np.pi * F / SR), -r * r
        x = lfilter([1 - c1 - c2], [1, -c1, -c2], x)
    return x


def step_contour(values, n):
    """Per-note values held for NOTE_S, joined by raised-cosine crossfades."""
    t = np.arange(n) / SR
    out = np.full(n, float(values[0]))
    for i in range(1, len(values)):
        s = np.clip((t - (i * NOTE_S - XFADE_S / 2)) / XFADE_S, 0, 1)
        out += (values[i] - values[i - 1]) * (0.5 - 0.5 * np.cos(np.pi * s))
    return out


def phrase(voice, vibrato, seed):
    """Return dict: n, amp, target and error contours in cents re A4."""
    sex, base = VOICES[voice]
    rng = np.random.default_rng(seed)
    n = int(round(NOTE_S * len(DEGREES) * SR))
    t = np.arange(n) / SR
    target = step_contour([100.0 * (base + d) for d in DEGREES], n)
    if vibrato:
        onset = np.array([(t - i * NOTE_S) for i in range(len(DEGREES))])
        since = np.where(onset >= 0, onset, np.inf).min(axis=0)
        fade = np.clip((since - 0.15) / 0.1, 0, 1)
        target = target + 40.0 * fade * np.sin(2 * np.pi * 5.5 * t)
    offsets = rng.uniform(-50, 50, len(DEGREES))
    offset = step_contour(offsets, n)
    since = np.mod(t, NOTE_S)
    scoop = -60.0 * np.exp(-since / 0.06)
    sos = butter(2, [1.0, 6.0], btype="band", fs=SR, output="sos")
    w = sosfiltfilt(sos, rng.standard_normal(n))
    wobble = 10.0 * w / np.sqrt(np.mean(w ** 2))
    amp = np.clip(np.minimum(t, t[-1] - t) / 0.02, 0, 1)
    return dict(voice=voice, sex=sex, n=n, amp=amp, target=target,
                offset=offset, scoop=scoop, wobble=wobble, offsets=offsets,
                noise_seed=seed + 1000)


def render(p, cents):
    """Render the phrase along an f0 contour given in cents re A4."""
    f0 = 440.0 * 2 ** (cents / 1200)
    phase = 2 * np.pi * np.cumsum(f0) / SR
    y = np.zeros(p["n"])
    kmax = int(20_000 // f0.min())
    for k in range(1, kmax + 1):
        fk = k * f0
        a = np.where(fk < 20_000, envelope_fast(p["sex"], fk) / k, 0.0)
        y += a * np.sin(k * phase)
    rng = np.random.default_rng(p["noise_seed"])
    pulse = 0.5 + 0.5 * np.cos(np.mod(phase, 2 * np.pi))
    noise = formant_filter(p["sex"], rng.standard_normal(p["n"])) * pulse
    noise *= 10 ** (-30 / 20) * np.sqrt(np.mean(y ** 2) / np.mean(noise ** 2))
    y = (y + noise) * p["amp"]
    return 0.5 * y / np.abs(y).max()
