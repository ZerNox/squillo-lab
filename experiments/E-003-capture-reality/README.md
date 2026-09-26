# E-003 — Capture reality in browsers

**Status:** open · **Serves:** VISION §6 (honesty), §12.3 · Absorbs squillo S-001, S-002 and S-003

## Question

When squillo requests raw capture (echo cancellation, noise suppression and
automatic gain control off; mono; 48 kHz), what do current Chrome and Firefox
actually report and deliver? How good is their resampling when the device rate
differs? Does the capture worklet's one message per block reach the engine
worker without loss or glitch?

## Questions squillo is waiting on

Migrated from squillo's retired candidate spikes in review R-04 (squillo
iteration 20; findings F-008, F-009). Each spike's file in
`squillo/docs/spikes/` keeps its reasoning as a record.

- **S-001:** does each target browser (squillo ADR 0012) report
  `echoCancellation`, `noiseSuppression` and `autoGainControl` in
  `getSettings()` after they are requested off? squillo ADR 0002 already
  treats an unreported flag as not raw; this says how often that path is
  taken.
- **S-002:** does each target browser connect a microphone at a rate other
  than 48 kHz to a 48 kHz `AudioContext` without error, and how good is its
  resampler: passband flatness, aliasing, delay? If a resampler's error
  exceeds an exact tolerance in `signal` or `metrics`, those scenarios are
  restated for native-rate input or resampling moves into `signal` (squillo
  Q-005, option D).
- **S-003:** does posting one message per 128-sample block from the capture
  `AudioWorklet` to the engine worker (squillo ADR 0006) lose or delay any
  render quantum, and how far does the worker fall behind while it computes?
  If blocks are lost, the transport becomes a shared-memory ring buffer or
  batched blocks (squillo Q-010 part 1).

## Hypothesis

Chrome and Firefox honour and report all three flags. Resampling is
transparent for pitch but may colour the high spectrum. Safari (not testable on
this machine) reports fewer flags, as squillo ADR 0012 notes.

## Protocol

1. **Automated:** Playwright drives Chrome (fake capture from a known WAV) and
   Firefox (fake media stream). Record `getSettings()` readback and compare the
   delivered samples with the source file: level, spectrum, latency. For
   S-003, post each block to a worker that burns a set CPU load per block,
   and count lost, reordered and late blocks.
2. **`needs-human`:** Joakim opens a local test page in each browser with a real
   microphone and presses one button. The page records the readback and a
   10-second capture of a reference tone played from a phone.

## Result

Not yet run.
