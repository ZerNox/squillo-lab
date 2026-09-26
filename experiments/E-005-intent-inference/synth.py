"""Synthetic sung phrases with known intended notes and known errors.

Crude experiment code. The voice is E-001's additive source-filter voice
(squillo-lab E-001 @ e43cdf7, voice.py: /a/ formants, higher-pole
correction, aspiration 30 dB down), driven here by random melodies instead of
E-001's fixed scale fragment. Melodies are random walks on a scale, generated
from a seed: original by construction, taken from no work.

Intended pitch of note i, in cents re A4: 100 * n_i + G + D(t_i). Sung:
intended + e_i + scoop + vibrato + wobble, where
  G     global tuning of the singer, uniform in [-50, 50] cents: no error,
        a cappella singers pick their own reference;
  D     linear drift of that reference over the phrase (condition);
  e_i   per-note offset, normal with sd sigma (condition): the error;
  scoop onset from below on half the notes, depth 30-100 cents, 60 ms decay;
  vib   5.5 Hz, +-50 cents, from 150 ms after onset (condition);
  wobble 1-6 Hz band noise, 10 cents RMS (as E-001).
"""

import sys
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfiltfilt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "E-001-voice-resynthesis"))
import voice  # noqa: E402  (E-001's synthesizer)

SR = voice.SR
SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "pentatonic": [0, 2, 4, 7, 9],
    "blue": [0, 2, 4, 5, 7, 9, 11],  # major, with intended b3 and b7 (below)
}
XF = 0.06  # crossfade between notes, s


def melody(scale, base, rng, n_notes=14):
    """Intended notes (semitones re A4) and durations (s)."""
    degs = SCALES[scale]
    tonic = base + int(rng.integers(0, 12)) - 5
    span = len(degs) + len(degs) // 2 + 1  # scale positions, about 1.5 octaves
    pos = int(rng.integers(len(degs) // 2, len(degs)))
    notes = []
    for _ in range(n_notes):
        octv, k = divmod(pos, len(degs))
        n = tonic + 12 * octv + degs[k]
        if scale == "blue" and degs[k] in (4, 11) and rng.random() < 0.3:
            n -= 1  # an intended blue note: b3 for 3, b7 for 7
        notes.append(n)
        step = rng.choice([-3, -2, -1, -1, 0, 1, 1, 2, 3])
        pos = int(np.clip(pos + step, 0, span - 1))
    notes = np.array(notes)
    # keep inside the tracker's range (ADR 0007: E2 to C6) with a whole tone
    # to spare, and inside the voice: at most A5 (+12 re A4)
    while notes.max() > min(12, base + 17):
        notes -= 12
    while notes.min() < -27:
        notes += 12
    durs = rng.uniform(0.25, 0.8, n_notes)
    return notes, durs


def contour(values, starts, n):
    t = np.arange(n) / SR
    out = np.full(n, float(values[0]))
    for i in range(1, len(values)):
        s = np.clip((t - (starts[i] - XF / 2)) / XF, 0, 1)
        out += (values[i] - values[i - 1]) * (0.5 - 0.5 * np.cos(np.pi * s))
    return out


def phrase(voice_name, scale, sigma, drift, vib, seed):
    sex, base = voice.VOICES[voice_name]
    rng = np.random.default_rng(seed)
    notes, durs = melody(scale, base, rng)
    starts = np.concatenate([[0.0], np.cumsum(durs)[:-1]]) + 0.1
    T = starts[-1] + durs[-1] + 0.1
    n = int(round(T * SR))
    t = np.arange(n) / SR
    G = rng.uniform(-50, 50)
    e = rng.normal(0, sigma, len(notes))
    d_total = drift * rng.choice([-1, 1])
    D = d_total * (t / T - 0.5)
    sung = contour(100.0 * notes + e, starts, n) + G + D
    since = t - starts[np.clip(np.searchsorted(starts, t, "right") - 1, 0, None)]
    scoop_on = rng.random(len(notes)) < 0.5
    depth = rng.uniform(30, 100, len(notes)) * scoop_on
    idx = np.clip(np.searchsorted(starts, t, "right") - 1, 0, None)
    sung -= depth[idx] * np.exp(-np.maximum(since, 0) / 0.06)
    if vib:
        fade = np.clip((since - 0.15) / 0.1, 0, 1)
        sung += 50.0 * fade * np.sin(2 * np.pi * 5.5 * t)
    sos = butter(2, [1.0, 6.0], btype="band", fs=SR, output="sos")
    w = sosfiltfilt(sos, rng.standard_normal(n))
    sung += 10.0 * w / np.sqrt(np.mean(w ** 2))
    amp = np.ones(n)
    amp[t < 0.1] = 0
    amp[t > T - 0.1] = 0
    amp = np.convolve(amp, np.ones(960) / 960, mode="same")  # 20 ms ramps
    p = dict(sex=sex, n=n, amp=amp, noise_seed=seed + 1000)
    x = voice.render(p, sung)
    truth = dict(notes=notes, starts=starts, durs=durs, G=G, e=e,
                 drift=d_total, T=T, scale=scale)
    return x.astype(np.float32), truth
