# E-001 — Voice re-synthesis: the synthesized you

**Status:** open · **Serves:** VISION §3 (core idea), §8 (on-device), §12.1

## Question

Can a singer's own recorded phrase be re-synthesized with **one aspect
improved** (pitch corrected towards the target, pitch steadied, vibrato
regularised) so that it still sounds like them, and how much of that runs
on-device in real time or near it?

## Hypothesis

A source-filter vocoder (WORLD-style analysis: f0, spectral envelope,
aperiodicity) can move pitch and steadiness while keeping identity, for small
steps (tens of cents). Large steps and tone changes degrade identity. Neural
vocoders sound better but may not fit in a browser.

## Protocol

1. Inputs: public-domain-licensed sung recordings (see `data/SOURCES.md`),
   short phrases, several voice types.
2. For each method (start: WORLD via `pyworld`; PSOLA via `praat-parselmouth`;
   later a small neural vocoder), apply controlled modifications: pitch
   correction at 25/50/100 %, stability smoothing, vibrato regularisation.
3. Measure: the modification actually achieved (re-measure with E-002's
   tracker), artefact indicators, processing time per second of audio on this
   machine's CPU.
4. Listening check: `needs-human` step. Joakim rates identity and naturalness
   for a blind set of 20 clips (15 minutes).

## Result

Not yet run.
