# E-002 — Measurement reliability and uncertainty

**Status:** running (round 1, pitch, answered on synthetic input; round 2 open) · **Serves:** VISION §5 (what is measured), §6 (honesty), §12.2

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

Migrated from squillo's retired candidate spike S-004 in review R-04
(squillo iteration 20; finding F-009):

- **S-004:** for each `squillo/fixtures/signal/` fixture, how far apart, in
  cents, are the pitches the same tracker reports in each target browser's
  WASM and in a native build, and in `f32` against `f64` arithmetic? The
  spread is the numeric epsilon squillo ADR 0007 records. Round 1 measured
  `f32` against `f64` on the host (numpy, not WASM; result row 9); the WASM
  targets wait for the lab's Rust / WASM toolchain.

## Result

### Round 1: pitch, synthetic ground truth (squillo iteration 16, 2026-09-25)

**Run:** `uv sync && uv run python run.py && uv run python timestamp.py &&
uv run python uncertainty.py && uv run python report.py` (`run.py` took 466 s on
the development machine; the others take seconds). Full tables: [`results/summary.md`](results/summary.md);
raw numbers: `results/*.json`.

**Conditions.** 48 kHz, squillo ADR 0007's frame axis: 384-sample frames,
the pitch of frame *i* from the 1536 samples ending with it, frames 3 onward.
Tones 1 s, additive synthesis in float64, peak 0.5, random harmonic phases,
harmonics above 20 kHz dropped; seed 20260925. Timbres: pure sine; harmonic
at −6 dB/octave (`saw6`) and −12 dB/octave (`saw12`); `weakf0`, −12 dB/octave
with the fundamental 20 dB under the second harmonic. Vibrato: sinusoidal,
rate 5.5 and 7 Hz, extent ±50 and ±100 cents. Glides: log-linear, 600 and
2400 cents/s. Noise: white Gaussian over the full 0–24 kHz band, SNR against
the tone's RMS. Steady tones: the 41 semitones E2 to C6; other conditions:
24 tones log-uniform over E2 to C6. Error is in cents against the true f0,
which for moving pitch is taken at a stated instant (below). *Gross* error:
more than 50 cents (MIREX raw pitch accuracy). Intervals are 95 %: Wilson for
shares, bootstrap over tones for percentiles. Maxima are observed maxima over
the frames stated, not bounds.

**Trackers.** `yin.py`: YIN (de Cheveigné and Kawahara 2002) steps 1–4, CMND
threshold 0.1, lags 16 to 763 samples (3000 to 63 Hz, so out-of-range tones
are found and then refused), parabolic interpolation on the raw difference
function *d*. A frame with no CMND dip under the threshold is unmeasurable. A
frame is measured when its f0 lies within E2 to C6 widened by a margin *m*
(3 cents unless stated). Compared: interpolation on the CMND *d′*; librosa
1.0.0 `pyin` at the same frame length and hop, `center=False`, with 10-cent
and 1-cent bins. Tools: Python 3.13.14, numpy 2.5.3, scipy 1.18.1.

**Results.**

| # | Question | Result |
| :--- | :--- | :--- |
| 1 | squillo's seven `fixtures/signal/` files (SG-001 to SG-006) | YIN passes every scenario: 122 of 122 frames measured for the 220 Hz, overshoot, E2 and C6 sines, max error 0.026 cents (C6); 0 of 122 measured for C2, C7 and silence |
| 2 | F-013: ±3 cents on pure tones, E2 to C6 | Holds with a wide margin: 5002 frames, 0 gross, max 0.03 cents. Interpolating on *d′* instead of *d*: max 0.40 cents |
| 3 | Harmonic steady tones | Max 0.98 cents (`saw6`), 0.12 (`saw12`), 0.26 (`weakf0`); no octave errors in 5002 frames each (gross share 0.00 %, Wilson upper bound 0.08 %). Error grows with pitch: `saw6` p95 0.19 cents below A3, 0.93 above C5 |
| 4 | Noise (`saw12`, threshold 0.1) | 40 dB: max 0.36 cents. 30 dB: p95 0.76 [0.58, 0.87], max 2.57, all within ±3. 20 dB: p95 5.15 [3.81, 7.37], max 19.6, 85.7 % within ±3. 10 dB: p95 41 cents, 1.75 % gross. 5 and 0 dB: **no frame measured**; YIN refuses rather than guesses. Threshold 0.2 changes little at ≥ 20 dB and adds gross errors at 10 dB (31.8 %) |
| 5 | Vibrato and glides: which instant does a frame's pitch describe? | Against the true f0 at the pitch window's centre, errors are large: p95 11 to 30 cents under vibrato, 4.5 and 17 cents on glides, biased on glides (mean −3.5 cents at 600 cents/s). Against the true f0 at **YIN's lag centre**, *s* + (*W* + τ)/2 with *W* = 773 and τ the period found, the error collapses: vibrato p95 1.3 (5.5 Hz ±50), 2.9 (5.5 Hz ±100), 1.5 (7 Hz ±50), 3.8 (7 Hz ±100) cents; glides 0.5 (600 cents/s), 2.0 (2400 cents/s). That instant lies 17.9 ms (E2) to 23.5 ms (C6) before the frame's end, and depends on the period and on the lag range. Round 1 measured the window centre and the lag centre; the frame's end is worse (p95 up to 48 cents) |
| 6 | pYIN | librosa's `pyin` is biased at this window: median 5.1 cents on steady tones, p95 25 cents on pure tones below A3, with 10-cent or 1-cent bins alike. Its difference function is computed from a whole-frame autocorrelation over a shrinking overlap, and it interpolates on *d′*, so this is librosa's implementation at 1536 samples, not the pYIN method as such. It measured more frames than YIN at 0 and 5 dB SNR, with p95 errors of 41 to 45 cents. Round 1 gives no reason to prefer it; ADR 0007's reason for rejecting it (Viterbi revises frames after later frames arrive) is unchanged |
| 7 | F-017: guard band at the range edges | Over 976 frames per offset, YIN's pure-tone error at both edges is at most 0.026 cents. With acceptance widened by *m* cents, every tone more than *m* + 0.03 cents outside is refused, and every tone inside is measured. At *m* = 0, a tone exactly at E2 or C6 is measured in only 50.4 % and 63.0 % of frames; SG-004 and SG-005 then conflict. At *m* = 3, a tone 3 cents outside is measured in 50.3 % (E2) and 76.1 % (C6) of frames, and a tone 3.5 cents outside in none. So a pure-tone guard band of 0.03 cents beyond *m* suffices for this tracker. A band of twice the tolerance (unmeasurable beyond 6 cents, *m* = 3) holds with a margin of 2.97 cents |
| 8 | Out-of-range tones | Below 63 Hz (600 and 1200 cents under E2) YIN finds no period; C2 and higher tones below E2 are found, then refused. Above C6 up to C7 the period is found (max error 0.08 cents), then refused; none is taken for an octave inside the range |
| 9 | float32 vs float64 arithmetic in YIN (numpy 2.5.3, not WASM) | 10 004 frames: max difference 0.0082 cents, p99 0.0028; no measured/unmeasurable disagreement. A first bound for squillo's S-004 question on the host, not across WASM targets |
| 10 | A per-frame uncertainty candidate (protocol step 3) | YIN's CMND value at the chosen dip orders the error. `saw12` in white noise at 40 to 10 dB SNR, 24 tones each: dip < 0.01, 10 111 frames, p95 1.9 cents, max 11.4; 0.01–0.02, p95 8.0; 0.02–0.05, p95 32; 0.05–0.1, p95 49, 4.2 % gross. A candidate for an honest per-frame ± and for refusing a frame; calibrating it needs real voices (round 2) |

**What this says for squillo.**

- ADR 0007's YIN at its frame axis meets SG-005's ±3 cents on pure tones by a
  factor of 100, and on harmonic tones by a factor of 3 or more, down to 30 dB
  white-noise SNR. The tolerance is not what limits it; noise is.
- F-017 has a number: guard band 0.03 cents beyond the acceptance margin for
  pure tones. The spec change is squillo's to make.
- For moving pitch, "the pitch of frame *i*" needs an instant, or exact
  scenarios on vibrato and glides cannot be written. The instant YIN measures
  depends on the period and on the lag range, which are implementation
  details. This affects SG-003 and the `metrics` time axis.
- Honesty (VISION §6): at 10 dB SNR YIN still reports frames up to 50 cents
  off. A fixed tolerance cannot describe that; a per-frame ± can, and the
  CMND dip is a candidate for it.

**Limits.** Synthetic tones only: no breathiness, jitter, shimmer, formant
movement, reverberation, or band-limited noise. No real voice, no browser, no
WASM. The 10- and 1-cent pYIN rows use librosa's implementation only.

### Round 1, fold into squillo (squillo iteration 24, 2026-09-26)

**Run:** `uv run python fold.py <dir>` (8 s). It writes squillo's four new
`fixtures/signal/` files to `<dir>` by the formulas squillo's
`fixtures/MANIFEST.md` records (pure Python binary64, `math.sin`, rounded to
`f32`; Python 3.13.14 on glibc 2.43, two runs byte-identical), runs the
tracker above (threshold 0.1, lags to 763 samples, acceptance E2 to C6
widened by 3 cents) on all eleven signal fixtures, and re-measures result 5's
moving-pitch conditions against a closed-form instant. Numbers:
`results/fold.json`.

**The instant.** YIN's difference function compares samples *s* to
*s* + *W* − 1 with the samples one period *P* later, *W* = 1536 − 763 = 773,
so the mean position of the samples compared is *s* + (*W* − 1 + *P*)/2. For
frame *i* (*s* = 384(*i* − 3)) that is sample position **384 *i* − 766 +
*P*/2**, with *P* = 48 000 / *f* the reported period in samples: 17.9 ms (E2)
to 23.5 ms (C6) before the frame's end. Result 5 used *s* + (*W* + *P*)/2,
half a sample later, and rounded it to a sample.

| # | Question | Result |
| :--- | :--- | :--- |
| 11 | squillo's two guard-band fixtures, pure sines 7 cents above C6 and 7 cents below E2 | 0 of 122 frames measured in each |
| 12 | squillo's glide fixture (sine, 220 Hz rising at 600 cents/s) and vibrato fixture (sine, 220 · (1 + 0.028 sin(2π · 5.5 t)) Hz, +47.8 / −49.2 cents), against the true f0 at the instant | 122 of 122 frames measured in each; max error 0.18 cents (glide), 0.93 (vibrato). Against the window centre: 3.9 and 9.9 cents, so the scenarios tell the two instants apart |
| 13 | The seven iteration-14 fixtures, reported pitch against the tone | 220 Hz and overshoot max 0.0013 cents; E2 0.0006; C6 −0.026 to +0.011; C2, C7, silence 0 of 122 measured |
| 14 | Result 5's conditions at the instant, 24 tones each, pure and `saw12` (seed 20260926) | Every measured frame within ±3 cents under vibrato of ±50 cents at 5.5 and 7 Hz (max 2.68, `saw12` at 7 Hz) and glides of 600 cents/s (max 1.00); Wilson 95 % lower bound 99.86 % in each. In every condition, every frame whose true f0 stays within E2 to C6 across its window is measured (0 unmeasured of 2462 to 2928 such frames per condition). Beyond that the ±3 cents no longer holds for every frame: ±100 cents vibrato 92.6–98.2 % within ±3, max 5.7; 2400 cents/s glides 99.9–100 %, max 3.5 |

**What this says for squillo.** The instant is exact once the lag range is
fixed, and at it the ±3 cents holds on moving pitch up to ±50 cents of
vibrato at 7 Hz and 600 cents/s of glide, on synthetic tones. Deeper or
faster movement needs a per-frame ± (result 10) rather than the fixed
tolerance.

### Round 2 (open)

Openly licensed sung datasets with f0 annotations (licences in
`data/SOURCES.md`); reverberation; calibration of the CMND-dip estimator
against observed error; then vibrato rate and extent, stability and tone
descriptors.
