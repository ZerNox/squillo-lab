# E-002 — Measurement reliability and uncertainty

**Status:** open · **Serves:** VISION §5 (what is measured), §6 (honesty), §12.2

## Question

For each candidate aspect (pitch accuracy, pitch stability, vibrato rate and
depth, and tone or resonance descriptors), how accurately can it be measured
from a sung phrase, and **how do we compute an honest ± for each value**?
Which further aspects turn out measurable?

## Hypothesis

Pitch-based aspects can be measured to within a few cents on clean input with
established trackers (YIN / pYIN / SWIPE / CREPE-class). Uncertainty grows with
noise, reverberation and breathiness, and must be estimated per recording, not
fixed. Tone descriptors are measurable but harder to make perceptually
meaningful.

## Protocol

1. **Ground truth by construction:** synthesized sung tones with known f0
   contours (steady, glides, vibrato at known rate and depth), plus added
   noise and reverb at controlled levels.
2. **Real voices:** openly licensed sung datasets with reference annotations
   where they exist (licences verified in `data/SOURCES.md`).
3. Run each tracker; compare with ground truth; report error distributions per
   condition, and test candidate per-recording uncertainty estimators against
   the observed error.
4. Survey the literature for further measurable aspects; add each as a
   sub-experiment.

## Questions squillo is waiting on

Set by review R-03 (squillo iteration 15) as round 1's scope: pitch only.

- **F-013:** does YIN at squillo's frame axis (384-sample frames, a
  1536-sample window, 48 kHz; squillo ADR 0007) meet ±3 cents on pure tones
  from E2 to C6, and what is its error on harmonic, vibrato and gliding tones
  and with noise? Compare pYIN.
- **F-017:** how far outside E2 to C6 must a tone be before it is reliably
  unmeasurable: the guard band at the range edges, in cents.

## Result

Not yet run.
