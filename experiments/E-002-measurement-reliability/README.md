# E-002 — Measurement reliability and uncertainty

**Status:** answered (round 1, pitch, answered on synthetic input; round 2, real voices, pitch ± and four aspects, squillo iteration 28; round 3, octave errors and reverberation, squillo iteration 36; a real room is E-003's `needs-human` step, an amateur's voice E-005's) · **Serves:** VISION §5 (what is measured), §6 (honesty), §12.2

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

### Round 2: real voices, the pitch ±, and four aspects (squillo iteration 28, 2026-09-27)

Set by squillo review R-05: on VocalSet, pitch stability, vibrato rate and
extent, and one tone or resonance measure, each with its ± and the conditions
where it fails; S15's assertions first. squillo finding F-028 asks for a
per-frame pitch *u* for voices.

**Run:** `uv sync && uv run python fetch.py $(cat data/vocalset-files.txt) &&
uv run python r2_truth.py check && uv run python r2_truth.py &&
uv run python r2_run.py && uv run python r2_octave.py &&
uv run python r2_analyse.py` (about 9 minutes on 16 processes; the fetch
reads 147 MB by range requests). Numbers: `results/r2_truth.json`,
`results/r2_octave.json`, `results/r2_results.json`. Tools: Python 3.13.14,
numpy 2.5.3, scipy 1.18.1, pyworld 0.3.5, soundfile 0.14.0.

**Inputs.** 159 VocalSet 1.1 takes by 20 singers (CC BY 4.0; list and
licence in `data/SOURCES.md`), resampled from 44.1 to 48 kHz: long tones
straight, forte, pianissimo and *messa di voce* (80), vibrato arpeggios (19),
"Row, row, row your boat" with vibrato (20), breathy scales (20), straight
scales (20).

**A real voice with a known f0.** Following the approach of Salamon et al.
(2017, "An analysis/synthesis framework for automatic f0 annotation of
multitrack datasets", ISMIR 2017; read from its datasets' Zenodo record
1481168, the paper itself not read), each take is analysed and re-synthesized,
and the f0 used for synthesis is the truth of the new signal. Here WORLD
(Morise, Yokomori and Ozawa 2016, doi:10.1587/transinf.2015EDP7457, pyworld
0.3.5): Harvest f0 at 1 ms (71 to 1100 Hz, wider than E2..C6), CheapTrick,
D4C, synthesis at 48 kHz. The truth at a sample is Harvest's f0 interpolated
linearly there, as WORLD's synthesis advances its phase.

**Checks, written before generating and asserted in code (S15).**

| Check | Result |
| :--- | :--- |
| WORLD synthesis of a known contour (envelope and aperiodicity from one real frame), read by the tracker at SG-007's instant; steady 220 Hz must be within SG-005's 3 cents | Steady: 370 of 370 frames measured, max 0.58 cents, p95 0.40. A 5.5 Hz, ±50-cent vibrato: max 2.32, p95 1.74. Frames whose window starts in the first 10 ms (synthesis onset) left out, after the first run found frame 3 unmeasured there |
| The truth procedure on one take of every set first | Ran (`r2_truth.py check`); truth inside 63.2–902.6 Hz, 98.0–99.8 % of voiced samples inside E2..C6 |
| Each re-synthesis's long-term spectrum within the range of real recordings, in 1/3-octave bands (100 Hz–8 kHz) where both have energy (≥ −50 dB re the file's total) | The median band difference from its own original is 1.10 dB (p95 2.92, max 4.96); between two long-tone takes of one singer it is 0.99 to 10.05 dB (median 3.90, 120 pairs). Every file inside. The first form of this check, each band inside the extremes of all 159 originals, failed for 54 of 2704 bands by up to 4.64 dB: on a held note a band's level hinges on one harmonic, so pooled extremes are not the range of a take (squillo L-031). The bound is the largest same-singer pair over all singers; against each file's own singer's largest pair (2.12 to 10.05 dB) every file is inside too, the smallest margin 1.13 dB (re-checked at squillo R-06, iteration 30) |
| Frames used for pitch | Every truth sample of the 1536-sample window voiced, inside E2..C6 (from `yin.E2`, `yin.C6`), moving at most 200 cents: 184 685 frames per condition |
| Conditions | White noise 30, 20, 10 dB and pink noise (−10 dB per decade, fitted slopes asserted within 0.5 dB per decade) 20, 10 dB SNR against the take's voiced RMS, 795 SNRs asserted within 0.01 dB of target; two rooms, a direct impulse plus an exponentially decaying Gaussian tail from 2.5 ms: RT60 0.4 s at DRR +6 dB and 0.8 s at DRR 0 dB, Schroeder T20 asserted within 5 % (measured 0.388–0.409 s and 0.786–0.812 s) and DRR within 0.1 dB. The rooms are models, not rooms |

**Definitions.** Tracker as round 1 (threshold 0.1, lags to 763 samples,
acceptance E2..C6 widened by 3 cents). A frame's error is against the truth at
SG-007's instant, 384 *i* − 766 + *P*/2; against the truth's mean over the
samples YIN compares instead, p95s move by at most 0.55 cents. *Gross*: more
than 50 cents. Held notes: runs of valid frames, split where the truth's
2 Hz low-pass leaves its first 0.25 s median by more than 60 cents, kept if
at least 2 s, trimmed 0.5 s at each end, cut into 1 s blocks (125 frames).
Per block: **steadiness**, the standard deviation of the pitch contour
low-passed at 2 Hz (cents); **vibrato extent**, √2 × the RMS of the contour
band-passed at 3–10 Hz (cents, the amplitude of a sinusoid of that RMS);
**vibrato rate**, the band-passed block's spectral peak in 3–10 Hz, reported
when the peak's ±0.5 Hz holds at least half the band's power. A measured
contour fills refused frames linearly when they are at most 25 % of the note
and no gap exceeds 12 frames, drops frames more than 600 cents from the note's
median, and otherwise the note is unmeasured. The truth of a block measure is
the same function on the truth contour. **Ring ratio**, the tone measure: the
level in 2–4 kHz minus the level in 50 Hz–2 kHz, dB, summed over the
Hann-windowed spectra of the frames YIN measured in each 1 s block, on the
original takes (the bands of Omori, Kacker, Carroll, Riley and Blaugrund
1996, *Singing power ratio*, J. Voice 10(3), 228–235,
doi:10.1016/s0892-1997(96)80003-8, as an energy ratio rather than their peak
ratio; the 2–4 kHz band holds the singer's formant cluster). A take's value
is the mean of its blocks; its *u* is √(SD²/*n* + *ū*²), the blocks'
sampling (GUM 4.2.3) and the tracking *u* taken as fully correlated across
blocks. Singers are split in two folds by their number's parity; every rule
is fitted on one fold and tested on the other, both ways.

**Results.**

| # | Question | Result |
| :--- | :--- | :--- |
| 15 | Per-frame pitch error on real voices, clean | Re-synthesis against its truth: 92.0 % of valid frames measured, 4.63 % of them gross, p50 1.22 cents, p95 of the non-gross 6.92. The original takes against Harvest's f0 (two trackers, not a truth): 1.99 % gross, p50 0.83, p95 5.61. Round 1's synthetic harmonic tones: p95 at most 0.93 |
| 16 | Does MT-003's floor, *u* = √3 cents (± 3.46), cover real voices? | No. It covers 79.8 % of measured frames clean, 78.6 % at 20 dB white noise, 72.7 % at 10 dB, 53.0 % in the 0.4 s room and 30.4 % in the 0.8 s room (re-synthesis); 87.1 % of the original takes' frames against Harvest |
| 17 | YIN's octave errors on real voices (S17: where do they fall?) | On the original takes, YIN reads 1.59 % of frames an octave above Harvest, 4.27 % in forte and in straight long tones; 93.2 % of those frames are men's, at a median 351 Hz, where /a/ puts the second harmonic far above the first. In 598 of 600 such frames sampled, a partial sits at Harvest's f0 (≥ 10 dB above 1.5 times it), so YIN is wrong: the first harmonic lies a median 19.3 dB under the second (p10 −25.7, p90 −13.9). Round 1's `weakf0` tone, 20 dB under, had none: its other harmonics held the period. The re-synthesis doubles the share (3.23 %): WORLD's output adds its own, as E-001 found, so rows 15, 18 and 19 overstate gross errors in that respect |
| 18 | Two crude variants against octave errors | Threshold 0.05: gross 1.99 → 0.64 % on the originals (4.63 → 2.17 % re-synthesized) at 91.6 → 86.4 % measured. Taking twice the lag when its dip is deeper: octave-high errors vanish (0.01 %) and octave-low ones rise to 9.03 %. Neither fixes the tracker; the first trades frames for errors |
| 19 | A per-frame *u* from the CMND dip (F-028), cross-validated across singers | Rule: in dip bins with edges 0, 0.0025, 0.005, 0.01, 0.02, 0.03, 0.05, 0.07, 0.1, *u* = half the 95th percentile of \|error\| (gross errors counting as misses), at least √3, non-decreasing; a bin whose 95th percentile is gross is refused, with all above it. Fitted on clean and noise. The two folds' tables: *u* = 1.73, 1.87, 2.44, 4.25 cents, refused from dip 0.02 (odd singers); 1.73, 1.87, 2.33, 2.93, 4.21, 5.70, refused from 0.05 (even). On the other fold, ± 2*u* covers 92.3 % of accepted frames clean, 94.0 % (white 30 dB), 95.0 % (white 20), 93.5 % (white 10), 94.7 % (pink 20), 93.6 % (pink 10), with 78.7, 66.6, 42.0, 7.5, 42.7, 8.7 % of valid frames accepted. What it misses are mostly octave errors: 2.0 % of accepted frames clean, 5.9 % at 10 dB. In the rooms it covers 76.2 % (0.4 s) and 55.0 % (0.8 s): the dip does not see reverberation (p95 of the non-gross 17.6 and 31.8 cents). On the original takes against Harvest: 97.2 % |
| 20 | Steadiness | Truth over 190 clean blocks: p5 2.7, median 6.3, p95 14.0 cents. Tracking error per block: p95 0.65 cents clean, 0.35 (white 30), 2.83 (0.4 s room), 2.78 (0.8 s room). A tracking *u* of 0.058 to 0.112 × the frames' RMS *u* (fitted per fold) covers 92.1 % of blocks clean, 95.1 % at 30 dB, 65.6 % and 46.9 % in the rooms. A take's ± 2*u* covers its truth in 48 of 48 takes clean, 93.5 % (0.4 s) and 93.8 % (0.8 s): the sampling term dominates. Held notes measurable: 125 of 178 clean, 61 at 30 dB, 21 at 20 dB, none at 10 dB, 80 and 40 in the rooms |
| 21 | Vibrato extent | Truth: p5 6.0, median 47.3, p95 110.5 cents. Per block, p95 tracking error 2.44 cents clean, 1.73 at 30 dB; in the rooms biased low, median −2.6 and −4.5 cents, p95 20.3 and 28.9. A take's ± 2*u* covers 48 of 48 clean and 80.6 % and 31.3 % in the rooms |
| 22 | Vibrato rate | Truth, 136 blocks with a clear peak: p5 4.17, median 4.99, p95 6.20 Hz. Tracking error per block p95 0.016 Hz clean, 0.054 and 0.17 Hz in the rooms; a tracking *u* of 0.11 to 0.13 × RMS *u* / extent covers 92.6 % clean, 57.9 % and 30.8 % in the rooms. The rate barely depends on the tracker |
| 23 | Do the three pitch measures' ± hold between the halves of one take? | Split-half (first against second half of a take's blocks, at least 4 blocks): the change test 2√(*u*₁² + *u*₂²) is passed by 13 of 15 clean takes for steadiness and extent (false change 13 %); *u* must grow by κ = 1.17 (steadiness) and 2.16 (extent) for a 5 % false-change rate. Vibrato rate: 8 takes, too few for κ. Few takes have 4 blocks of held notes; these κ are rough |
| 24 | Ring ratio | 158 of 159 takes measured clean: p5 −28.6, median −17.5, p95 −6.2 dB; *u* from its blocks median 1.15 dB (p95 2.37). Between the halves of one take the change test fires for 28.5 % of takes: the ratio moves with the notes sung, and the halves sing different notes (25–45 % in long tones and the round, 10 % in breathy scales). κ = 2.04 clean. It tells forte from pianissimo in 19 of 20 singers at 2*u*, 12 of 20 at 2κ*u* (forte higher in 19; median difference 8.9 dB) |
| 25 | Ring ratio in noise and rooms | Bias against the clean take: white 30 dB median +0.10 dB (p95 \|3.1\|), 20 dB +0.61 (4.2), 10 dB +1.69 (8.0); pink 20 dB +0.64, 10 dB +1.78. The change test calls the noisy take changed from the clean one in 3.2 % (30 dB), 10.1 % (20 dB) and 38.8 % (10 dB) of takes. Rooms: median −0.05 and −0.38 dB, called changed in 1.3 % and 3.8 % |

**What this says for squillo.**

- **F-028.** On real voices the pitch *u* is not √3 cents: that floor covers
  about 80 % of frames. The CMND dip gives a per-frame *u* of 1.7 to 5.7
  cents with a refusal above it, holding 92–95 % on singers it was not fitted
  on, clean and in noise down to 10 dB. The remaining misses are octave errors,
  which no ± covers.
- **ADR 0007's YIN has octave errors on real voices**: 1.6 % of frames on the
  originals, 4.3 % in forte and straight long tones, 93 % of them men's,
  where the first harmonic is 14–26 dB under the second. Two crude fixes fail or cost frames. The
  tracker, or a continuity rule, is squillo's to revisit.
- **Reverberation is the condition the per-frame ± cannot see.** In the
  modelled rooms the pitch error's p95 grows 2.5- to 4.6-fold, the dip does
  not predict it (the ± covers 76 % and 55 %), and the vibrato extent is
  biased low. VISION §6 needs
  squillo to say so, so a room or reverberation estimate is needed before
  pitch-based measures are shown with a ±.
- **Steadiness, vibrato rate and vibrato extent** are measured on held notes
  with a tracking error far below their spread across singers (steadiness
  p95 0.65 cents against a median of 6.3; extent 2.4 against 47; rate
  0.016 Hz against 4.99 Hz), clean and at 30 dB. Their ± is dominated by the
  take's own sampling, which the halves of a take say is understated by a
  factor of 1.2 to 2.2 (15 takes).
- **The ring ratio** tells forte from pianissimo in 19 of 20 singers, but it
  moves with the notes sung. Two takes compare only on the same material, and
  its block *u* needs a κ of about 2. It needs 30 dB SNR: at 20 dB it is
  called changed in one take in ten. The microphone's own response shifts it
  and is unknown to squillo (E-003).

**Limits.** Re-synthesized voices carry WORLD's artefacts (more octave errors
than the originals, row 17). Twenty trained singers on /a/, no amateurs, no
other vowel. Noise is stationary. The rooms are models. Browsers, microphones
and WASM are not in the path. Held notes of at least 2 s are few in scales
and songs, so the measures rest mostly on long tones, and the split-half
tests on 8 to 15 takes.

### Round 2, fold into squillo (squillo iteration 34, 2026-09-28)

**Run:** `uv run python fold2.py <squillo>/fixtures` (about 1 minute on one
process; needs round 2's `data/cache/r2_frames.npz`). It writes squillo's
four new `fixtures/metrics/` files by the formulas squillo's
`fixtures/MANIFEST.md` records (pure Python binary64, rounded to `f32`; two
runs byte-identical) and `results/fold2.json`. Written for squillo findings
F-028 and F-031.

**What round 2 left for a spec.** (1) Two *u* tables, one per fold of
singers; a spec needs one. (2) Held notes were cut from the truth, which a
product never has. (3) The factors *c* (tracking) and κ (split halves) were
per fold or rough. The cache reproduces round 2's two tables exactly
(asserted).

**Held notes from the measured contour** (`held_notes` in `fold2.py`,
squillo `metrics` MT-009): a frame counts when it has a pitch and a finite
*u*; a run goes from such a frame to the last one before a gap of more than
12 frames; within a run a frame more than 600 cents from the run's median is
dropped; the run is filled linearly, low-passed at 2 Hz (order-2
Butterworth, forward and backward) and cut where the low-passed contour
leaves the median of the piece's first 31 frames by more than 60 cents; a
piece is a held note when it is at least 250 frames long, starts and ends
on a counted frame, has no gap over 12 frames and at most 25 % filled
frames. Blocks, measures and the take's value as round 2 (*Definitions*),
with the take's *u* = κ √(SD²/*n* + *ū*²), at least two blocks. New: a block
gives a vibrato rate only when its extent exceeds twice its tracking *u*,
so a straight tone gives none. The truth is the same block functions on the
truth contour over the same frames, where every frame is valid.

**Checks (S15).** Every scenario squillo writes is a predicate in
`scenarios()`, run once on its fixture (must pass) and once on another
fixture where it must fail: all 12 pass and all 12 fail on the wrong input.
The coverage function is checked with *u* = 10⁹ (must give 1) and 10⁻⁹
(must give < 0.01). Fixture conditions asserted from the exact formula at
every sample: every frequency inside E2–C6; the vibrato fixture −40.28 to
+39.37 cents at 5.5 Hz, inside SG-007's ±50 cents and 7 Hz. A first form of
the aperiodic tone, a second sine of constant amplitude, gave every frame
nearly the same aperiodicity and spanned no bins; its amplitude now rises
across the second.

| # | Question | Result |
| :--- | :--- | :--- |
| F1 | One table | Fitted on all 20 singers: *u* = 1.73, 1.87, 2.39, 3.45 cents, refused from aperiodicity 0.02. The per-bin larger of the two folds' tables is the odd singers' table itself: 1.73, 1.87, 2.44, 4.25, refused from 0.02. Rounded up at two decimals (1.73 = √3 kept, 1.88, 2.44, 4.26), it covers, on the even singers it was not fitted on, 95.2 % of accepted frames clean (70.2 % of valid frames accepted), 96.6 % at 30 dB white noise, 98.2 % at 20 dB, 99.8 % at 10 dB, 97.9 % and 99.6 % in pink noise at 20 and 10 dB; 81.9 % and 64.9 % in the two rooms; 98.1 % of the original takes against Harvest. On all 20 singers: 94.5 % clean, 96.1–99.0 % in noise |
| F2 | Held notes cut from the measured contour, cross-validated (*u* table and *c* from the other fold, κ = 1) | 123 held notes clean (round 2's truth cut: 125), 46 of 159 takes with at least two blocks. Per block, ± 2 × tracking *u* covers the truth in 93.7 % (steadiness), 90.5 % (extent) and 91.3 % (rate) of blocks clean; the take's ± covers 42 of 42 takes for steadiness and extent, 31 of 31 for rate |
| F3 | The constants, with F1's table on all singers | *c* = 0.0775 (steadiness), 0.400 (extent), 0.153 (rate), rounded up to 0.078, 0.41, 0.16. κ, the 95th percentile of \|*a* − *b*\| / 2√(*u*ₐ² + *u*ᵦ²) over split halves (at least four blocks), the larger of the clean re-syntheses and the original takes: 1.32 (steadiness; 16 and 20 takes), 1.56 (extent; 16 and 20), 2.50 (rate; 10 original takes, too few clean), rounded up to 1.33, 1.57, 2.51. With them the split halves call a false change in 6.3 % and 5.0 % (steadiness), 0 % and 5.0 % (extent), 0 % and 10 % (rate) of takes, in sample |
| F4 | The constants as squillo states them, on all takes | Clean: 117 held notes, 43 takes measured; per block ± 2*u* covers 94.4 % (steadiness), 95.1 % (extent), 95.3 % (rate); per take 36 of 36, 36 of 36, 23 of 23, take error p95 0.23 cents, 1.63 cents, 0.024 Hz. White 30 dB: 30 takes, 100 % of takes covered. Rooms (F-030): extent biased low (take median −2.1 cents at 0.4 s), 73 % and 50 % of takes covered |
| F5 | squillo's fixtures | `held-vibrato.wav` (5 s, 5.5 Hz, −40.28/+39.37 cents): steadiness 0.467 ± 0.36 (*U*), extent 39.27 ± 2.23 cents, rate 5.4994 ± 0.035 Hz, against 0.474, 39.82 and 5.4994 by the same functions on the exact contour. `held-wobble.wav` (0.5 Hz, ±20.8 cents): steadiness 14.633 ± 0.36 against 14.634, no rate. `held-steady.wav`: steadiness and extent within their ± of 0, no rate. `tone-aperiodic.wav`: aperiodicity 2.0 × 10⁻⁵ to 0.0259 over 122 measured frames, *u* 1.73 (38 frames), 1.88 (16), 2.44 (22), 4.26 (33), 13 refused. `signal/sine-220hz.wav`: aperiodicity at most 1.4 × 10⁻⁵, no held note. Every frame of the held fixtures has *u* = √3 |

**What this says for squillo.** One table can be stated, with evidence on
singers it was not fitted on: the odd fold's table, which is also the
stricter of the two. Held notes can be found without a truth, and the three
measures keep their coverage. κ above 1 is needed for each, on few takes.
Reverberation still breaks the extent (F-030), and nothing here measures
an amateur.

**Limits.** As round 2. κ rests on 10 to 20 split takes; the rate's on the
original takes only. The held-note rule was written for this data and
checked on it, not on independent takes.

### Round 3: octave errors and reverberation (squillo iteration 36, 2026-09-28)

Set by squillo review R-07: compare candidate fixes for YIN's octave-high
errors against round 2's truth (squillo F-029), and build a reverberation
estimate from the take that widens *u* or marks the take, checked on
modelled rooms held out (F-030). The ring ratio on repeated material
(F-036) only if room was left: it was not run.

**Run:** `uv run python r3_octave.py check && uv run python r3_octave.py &&
uv run python r3_room.py run && uv run python r3_room.py sweep &&
uv run python r3_room.py analyse`. Time (S19), from one item of the slowest
condition timed first: the largest take through `r3_octave.py`'s five
conditions and the then 45 variants (37 in the final grid) took 8.8 s on one process, so 159 takes about
1 minute on 16; the run took 6.4 minutes (the analysis and the 300-frame
attributions are serial). `r3_room.py run` 2.7 minutes, `sweep` 46 s,
`analyse` seconds. Needs round 2's `data/cache/r2/*.npz` and
`r2_frames.npz`. Numbers: `results/r3_octave.json`,
`results/r3_octave_check.json`, `results/r3_room.json`. Tools as round 2.

**What squillo shows.** Since squillo iteration 34 `metrics` MT-003 refuses
a frame whose aperiodicity (YIN's *d*′ at the chosen lag) is 0.02 or more
and gives the rest a *u* of √3, 1.88, 2.44 or 4.26 cents (`fold2.json`,
`measures.spec.table`, read by `r3_octave.spec_table()`). So every variant
below is judged twice: on the frames it measures (round 2's view) and on the
frames MT-003 then accepts, which are the ones squillo shows.

#### Part A: octave errors (`r3_octave.py`)

**Variants**, written in the file's docstring before running; each starts
from round 1's tracker and may replace its lag *t* by the deepest *d*′ dip
*t*₂ within 2*t* ± 3 (round 2's `octave_check` window), all causal:
`base-0.1` (ADR 0007's tracker as E-002 runs it), `base-0.05`; `sub(a, d)`,
a subharmonic check in the CMND: take *t*₂ when the depth *D*(*t*) ≥ *d*
and *D*(*t*₂) < *a* *D*(*t*), *D* the vertex of the parabola through *d*′ at
the lag and its neighbours, *a* ∈ {0.05, 0.1, 0.2, 0.5}, *d* ∈ {0.005, 0.01,
0.02}; `spec(b)`, a subharmonic check in the spectrum: take *t*₂ when the
power at the odd multiples of *f*/2 exceeds *b* dB of the power at the
multiples of *f* (up to 4 kHz), *b* ∈ {−30, −25, −20, −15, −10}, only
where *f*/2 ≥ 125 Hz, the Hann main-lobe width at 1536 samples; `cont`, a
continuity rule: take *t*₂ when the pitch is 1100 to 1300 cents above the
median of the previous 31 frames' reported pitches (at least 16 of them)
and *d*′(*t*₂) < 0.1; and `cont+` each of the others. Each family's
parameters are chosen on one fold of singers and tested on the other, by a
rule written before running: the smallest mean gross share of measured
frames on `clean` and `original`, keeping the measured share within 1 point
of `base-0.1`'s, among variants that pass every must-pass check.

**Checks (S15), run before the analysis (`r3_octave.py check`).**

| Check | Must | Result |
| :--- | :--- | :--- |
| squillo's eleven `fixtures/signal/` files | pass: every variant reports what `base-0.1` reports | Every variant, every frame of all eleven |
| Round 1's steady harmonic tones, E2..C6 by semitone, `saw6`, `saw12`, `weakf0` (from `run.py`'s own `spectrum()` and `render()`), 5490 frames each | pass: no gross error | Every variant but `sub(·, 0.005)` and `cont+sub(·, 0.005)`, which halve 122 to 366 of `saw6`'s frames; those eight are excluded from the fit. A first form of `sub` on *d*′ at the whole-sample lags failed this check for every parameter (up to 1464 of 5490 frames), because *d*′ at a whole lag grows with the lag's distance from the period; at the vertex these tones give *D* at most 0.008. A first form of `spec` without the 125 Hz bound read correct tones near E2 at −5 dB (leakage) |
| `saw12` at 350 Hz with H1 26 dB under H2 (round 2 result 17's p10, 25.7 dB) and the other odd harmonics 10 or 20 dB down, 247 frames | fail for `base-0.1` (asserted) | `base-0.1` reads 247 of 247 frames an octave high in both. Explored first: with H1 alone 20 to 40 dB down, it read 175 to 440 Hz tones correctly; the odd harmonics' weakness is what misleads it. At −10 dB MT-003 refuses all 247 frames (aperiodicity ≥ 0.02), and `sub(·, ≥ 0.01)` and `spec(≤ −20)` read all 247 correctly. **At −20 dB MT-003 accepts all 247 an octave high**, and only `spec(−25)` and `spec(−30)` correct them |
| The octave classes | pass and fail on errors known by construction | 0, 1200, −1200, 1150, 60 cents classed as expected |

**Results.** Percentages of valid frames (measured, accepted) or of
measured and accepted frames (gross, octave, coverage). *Original*: the
VocalSet takes against Harvest, two trackers, not a truth.

| # | Question | Result |
| :--- | :--- | :--- |
| 26 | The rule's choice, and held out | Fit on odd singers: `sub(0.5, 0.01)`; on even: `sub(0.5, 0.02)`. `base-0.05` fails the measured-share rule on both folds (over all takes it measures 4.6 points fewer valid frames clean, 5.2 original). On the singers not fitted on, gross errors among measured frames fall from 3.24 to 0.81 % (clean) and 1.02 to 0.47 % (original) on the even singers, 5.69 to 2.44 % and 2.72 to 0.79 % on the odd; octave-high errors almost vanish (original: 0.94 → 0.02 %, 2.09 → 0.01 %), octave-low ones appear (original: 0.04 → 0.39 %, 0.09 → 0.24 %). `cont+sub` is best on the odd singers (clean 2.08 %) and worse on the even (1.59 %); `cont` alone and `spec` do less |
| 27 | What squillo shows, all 159 takes | `base-0.1` with MT-003: 71.7 % of valid frames accepted clean, 72.2 % original; gross errors among them **0.56 % clean and 0.02 % original**; ±2*u* covers 94.5 % and 98.3 %. With `sub(0.5, 0.01)`: 75.3 % and 74.1 % accepted, gross 0.25 % and **0.36 %**, coverage 94.8 % and 98.0 %. With `sub(0.5, 0.02)`: 75.2 %, 74.1 %; gross 0.55 %, 0.21 %. So MT-003's refusal already keeps octave errors out of what squillo shows on the real takes: the frames YIN reads an octave high mostly have *d*′ ≥ 0.02 (original takes: 1.59 % of measured frames octave-high, 0.02 % of accepted frames gross). The fixes buy 1.9 to 3.6 points of accepted frames at 9 to 15 times the gross share on the real takes (0.023 % → 0.21 and 0.36 %) |
| 28 | S17: who is wrong at the new octave-low frames? | On the original takes, where `sub(0.5, 0.01)` reads an octave below Harvest (603 frames), a partial sits at its pitch in 9 of 300 sampled (≥ 10 dB above the level at 1.5 times it): in 97 % the variant is wrong, not Harvest. `sub(0.5, 0.02)`: 13 of 300 (395 frames). `base-0.1`'s own 115 octave-low frames: 5 of 115 |
| 29 | Where the errors were | `base-0.1`, original takes: men 3.34 % gross measured, 0.04 % accepted; straight long tones 5.84 % and 0.04 %; women 0.33 % and 0.01 %. `sub(0.5, 0.02)`: men 0.90 % and 0.32 %, straight long tones 1.86 % and 0.31 % |
| 30 | Noise | White 20 dB: `base-0.1` accepts 28.9 %, 0.79 % gross; `sub(0.5, 0.01)` 31.8 %, 0.23 %. At 10 dB both accept 1.2–2.4 % of valid frames |
| 31 | The spectral check's cost | `spec(−25)`, the one setting that fixes the −20 dB tone of the checks, reads 4.52 % of the original takes' frames an octave low; `spec(−30)` 13.7 %. `spec(−20)`: 1.21 % |

**What part A says for squillo.** ADR 0007's YIN with MT-003's refusal
already shows almost no octave errors on real voices: 0.02 % of accepted
frames on 159 VocalSet takes against Harvest, 0.56 % on the WORLD
re-syntheses, whose own artefacts round 2 found (result 17). The best
candidate fix, a subharmonic check on the CMND's interpolated depths,
removes octave-high errors among measured frames but trades them for
octave-low ones, which MT-003 then accepts: on the real takes it raises the
gross share of what squillo shows from 0.02 % to 0.21–0.36 % for 2–4
points more frames. No candidate dominates. A voice whose odd harmonics
are 20 dB under the evens would be shown an octave high with a ±; whether
real voices do that is unmeasured beyond these takes. For squillo's F-029:
a `signal` scenario on the −10 dB tone (read an octave high, aperiodicity
≥ 0.02, so unmeasurable in `metrics`) is writable today; the −20 dB tone
is a known limit.

#### Part B: reverberation (`r3_room.py`)

**Conditions**, in the file's docstring before generating: nine fitting
rooms, RT60 0.3, 0.6 and 1.0 s at DRR +12, +6 and 0 dB, round 2's room
model and seeding, DRR asserted within 0.1 dB and T20 within 5 % on the
tail (0.292–0.313, 0.587–0.611, 0.983–1.014 s measured); the held-out rooms
are round 2's two (0.4 s at +6 dB, 0.8 s at 0 dB), regenerated and asserted
to give round 2's cached pitches frame for frame (as are `clean` and
`white-20`). A first run measured T20 on the whole response as round 2 did
and stopped on its own assertion: at +12 dB the direct impulse holds 94 %
of the energy and the −5 to −25 dB span straddles the direct step (0.315 s
for a 0.3 s tail). The tracker is `base-0.1` with MT-003. A take is shown
honestly when ±2*u* covers at least 95 % of the accepted frames of the
takes left unmarked.

| # | Question | Result |
| :--- | :--- | :--- |
| 32 | How much reverberation breaks the ± (all 159 takes) | Clean 94.5 %; noise 96.1–99.0 %; original takes 98.3 %. Every room breaks it: RT60 0.3 / 0.6 / 1.0 s at DRR +12 dB 89.8 / 88.6 / 88.2 %, at +6 dB 81.3 / 78.6 / 77.8 %, at 0 dB 65.2 / 62.0 / 59.5 %; the held-out rooms 79.7 % and 60.7 % (on the even singers alone 81.9 % and 64.9 %, squillo F-030's figures). The DRR matters far more than the RT60 |
| 33 | How much direct sound it needs (`sweep`) | At DRR +18 dB 93.3 / 92.7 / 92.8 %, at +24 dB 94.1 / 94.1 / 94.0 % (RT60 0.3 / 0.6 / 1.0 s), against 94.5 % clean. The rule written for it (every RT60 at least 95 % on both folds) is met by no DRR, because clean itself is 93.9 % on the odd singers; at +24 dB every room is within 0.5 points of clean |
| 34 | A decay estimate: the steepest fall of the take's level over 6, 12 or 25 frames (48, 96, 200 ms), absolute or relative to the level above the take's floor | Medians over all takes, fall over 96 ms: clean 35.5 dB, original 32.9, white 20 dB 13.6, room 0.3 s +12 dB 26.7, room 0.4 s 18.7, room 0.8 s 11.7. By the rule written before running, the chosen candidate on both folds is the 48 ms fall (the fewest dry takes of the fitting fold marked: 89.4 % odd, 85.9 % even; `fit.*.chosen`), marked below 25.5 dB (fit odd) or 23.8 dB (fit even). Held out, on the even singers it marks 55 % of clean takes, 86 % at 30 dB SNR, every take at 20 dB and below, 62 % of the original takes, and 99–100 % of the takes in every room, the held-out rooms included; on the odd singers 59 %, 73 %, 94 % at 20 dB, 61 % of originals, and the unmarked 3 % of the 0.3 s, +12 dB room cover only 81.3 %. The 96 ms fall does no better (46–53 % of clean takes marked; the other way round its unmarked room takes cover 63.5 %). Noise masks the decay as a room does, and a take with no clear offset cannot show one |
| 35 | A roughness estimate (added after the first look at the fitting fold, written in the docstring before its run): the median or 90th percentile of \|*p*(*i*) − (*p*(*i* − 1) + *p*(*i* + 1))/2\| over accepted frames | Separates nothing: medians 1.21 cents clean, 1.19 original, 0.94–1.21 in the rooms. Reverberation biases the contour smoothly (it pulls vibrato peaks towards the mean, round 2 result 21), not frame to frame. By the rule it marks every take or meets the rule nowhere |
| 36 | The rule's bar | Written as 95 % and never run on the condition that must pass it: clean covers 93.9 % on the odd singers and 95.2 % on the even (`bar_check`; the 0.8 s room, which must fail it, gives 57.6 % and 64.9 %), so on the odd fold the rule could be met only by marking dry takes (squillo L-036). Post hoc, with the bar at each fold's own clean coverage (93.9 % odd, 95.2 % even) instead of 95 %: the same picture: every decay candidate that meets it still marks 46–98 % of the held-out clean takes and 94–100 % at 20 dB white noise (`fit_post_hoc_bar_clean`) |

**What part B says for squillo.** No estimate tried here tells a
reverberant take from a dry or noisy one well enough to mark it: the ones
that mark the rooms mark most dry takes too. None was tried as a widening
of *u*. Every modelled room
breaks the pitch ± (60–90 % coverage against 94.5 % clean), and it takes
a direct sound 24 dB above the reverberation (a microphone close to the
mouth in a treated room) before coverage returns to within half a point of
clean. VISION §6 then needs squillo to state the condition rather than
detect it: the pitch ± is honest for close, dry capture, and the singer is
told so. The original VocalSet takes, recorded in a real treated room,
cover 98.3 % against Harvest, which is two trackers agreeing, not a truth.
A real room is E-003's `needs-human` step.

**Limits.** Modelled rooms (an exponential Gaussian tail, no early
reflections, no frequency dependence), one estimate family per idea and
crude; trained singers on /a/; WORLD re-syntheses for the truth. The octave
checks' must-fail tones are built, not recorded. Nothing here measures an
amateur, another vowel or a real room. F-036 (the ring ratio on repeated
material) was not run.

### Beyond round 3

Amateur voices and other vowels (E-005's `needs-human` step); a real room
(E-003's); the ring ratio on repeated material (F-036); a reverberation
estimate of another kind (spectral smearing of the partials, or a blind
RT60 method with its own evidence) if squillo ever needs detection rather
than a stated condition.
