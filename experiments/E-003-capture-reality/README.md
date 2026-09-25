# E-003 — Capture reality in browsers

**Status:** open · **Serves:** VISION §6 (honesty), §12.3 · Absorbs squillo S-001 and S-002

## Question

When squillo requests raw capture (echo cancellation, noise suppression and
automatic gain control off; mono; 48 kHz), what do current Chrome and Firefox
actually report and deliver? How good is their resampling when the device rate
differs?

## Hypothesis

Chrome and Firefox honour and report all three flags. Resampling is
transparent for pitch but may colour the high spectrum. Safari (not testable on
this machine) reports fewer flags, as squillo ADR 0012 notes.

## Protocol

1. **Automated:** Playwright drives Chrome (fake capture from a known WAV) and
   Firefox (fake media stream). Record `getSettings()` readback and compare the
   delivered samples with the source file: level, spectrum, latency.
2. **`needs-human`:** Joakim opens a local test page in each browser with a real
   microphone and presses one button. The page records the readback and a
   10-second capture of a reference tone played from a phone.

## Result

Not yet run.
