# E-002 — Measurement reliability and uncertainty

**Status:** answered (round 1, pitch, answered on synthetic input; round 2, real voices, pitch ± and four aspects, squillo iteration 28; round 3, octave errors and reverberation, squillo iteration 36; fold 3, the steadying ladder, squillo iteration 42; round 4, the ring ratio on repeated material, squillo iteration 49, whose separate-takes step is `needs-human`; round 5, held notes trimmed to their measured cells and the next step against blocks, squillo iteration 78; round 6, a fixture that tells trimmed pieces from untrimmed ones, squillo iteration 88, folded in 89; round 7, the numeric epsilon across WASM targets, squillo iteration 92; a real room is E-003's `needs-human` step, an amateur's voice E-005's) · **Serves:** VISION §5 (what is measured), §6 (honesty), §12.2

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
  `f32` against `f64` on the host (numpy, not WASM; result row 9); round 7
  (squillo iteration 92) measured the WASM targets in Chrome and Firefox.

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

### Fold 3: the steadying ladder (squillo iteration 42, 2026-09-28)

**Run:** `uv run python fold3_ladder.py <squillo>` (about 11 s on one process, 5.3 s and 4.8 s for the two conditions in `seconds`;
a sample of 10 takes timed first at 0.006 s each for a take with no
measured steadiness; needs round 2's `data/cache/r2_frames.npz` and
`results/fold2.json`). Writes `results/fold3_ladder.json`. Written for
squillo's first `coach` spec (Q-023): what next step and far vision can
`coach` ask of `synthesis`, whose rungs change pitch only (squillo SY-002)?

**Rules, written in the docstring before the run.** A take's steadiness
is fold 2's spec rules, with the *u* table, *c* and κ read from
`fold2.json` `measures.spec`. The *full steadying* gives each accepted
frame of each held note the note's mean 2 Hz contour minus its 2 Hz
contour there (the slow wander removed, vibrato kept) and every other
frame 0. It is scaled by α_max = min(1, 50 / its largest change), so no
change exceeds squillo SY-002's 50 cents, and tried at 64 strengths, *k* ×
α_max / 64. A rung's pitch is the take's measured pitch plus the change,
with the take's *u* (squillo SY-004), measured by the same rules, and
compared with the take by MT-008. **Rule A:** the next step is the least
*k* whose rung is improved, the far vision the greatest. **Rule B:** as A,
offered only when the next step's steadiness is not below the take's
steadiest block.

**Checks (S15),** each asserted in `main()`: strength 0 reproduces the
take's steadiness and *u* exactly, on every measured take and fixture;
MT-008 calls `held-wobble.wav` then `held-steady.wav` improved (must pass)
and `held-wobble.wav` against itself not (must fail); the full steadying
of `held-wobble.wav` is improved (must pass) and strength 0 is not (must
fail). Every fixture is read from squillo's `fixtures/` and its SHA-256
asserted to be in its `MANIFEST.md`. **R-09 (squillo iteration 45,
L-041):** both must-fail cases above call MT-008 on identical arguments,
so they could not have passed; "strength 0 reproduces" is a sanity
assertion, not a check. Added and re-run, every other value unchanged:
MT-008 calls `held-steady.wav` then `held-wobble.wav` not improved (must
fail, false as it should be); the steadying reversed on `held-wobble.wav`,
the wander doubled, is not improved (must fail, false); every rung's
change is asserted at most 50 cents and 0 outside a held note's accepted
frames (the 50-cent assertion would stop the run on the unscaled change of
the 34 capped takes; the zero assertion has no must-fail case). Rule B is
reported and not chosen; it has no must-pass or must-fail case. The Wilson
intervals below are computed in `wilson()` and held in `summary`'s
`wilson95_*` keys.

| # | Question | Result |
| :--- | :--- | :--- |
| L1 | How often is a step offered on real voices (rule A)? | Original takes, 20 trained singers: steadiness is measured on 47 of 159 takes (all long tones: messa di voce 16, pianissimo 12, straight 12, forte 7). A next step exists on **28 of 47** (Wilson 95 % 45–72 %), 28 of 159 takes overall (12.5–24.3 %). On the WORLD re-syntheses: 19 of 43 (30–59 %) |
| L2 | Rule B, never steadier than the singer's own steadiest block | **4 of 47** original takes (3.4–19.9 %); 1 of 43 re-syntheses. The least improvement MT-008 can show lies beyond the steadiest block on 24 of the 28 takes where A offers a step |
| L3 | How small is the next step? | The least improved strength is a median 0.63 of the steadying SY-002 allows on the original takes (0.11 to 0.98), 0.55 on the re-syntheses: on real voices the smallest step that can be shown is most of the way. Its largest change per frame is 7.7 to 48.4 cents. Median steadiness 7.16 cents, median take *u* 2.02 cents; 2 blocks on 17 of the 47 takes |
| L4 | Does SY-002's 50 cents bind? | The full steadying exceeds 50 cents on some frame of 34 of 47 original takes (29 of 43 re-syntheses), so α_max < 1 there. Where a step exists, the far vision's steadiness is a median 2.09 cents |
| L5 | Is the outcome monotone in strength? | On 46 of 47 original takes and 43 of 43 re-syntheses. On the other (file 82) the strongest steadying is not improved; the greatest improved strength is 63 of 64. Far vision at the full strength on 27 of the 28 |
| L6 | squillo's fixtures | `held-wobble.wav` and `synthesis/voice-220hz-wobble.wav`: a step, at 3 of 64 (largest change 1.10 cents), far vision at 64 of 64 (steadiness 14.63 → 0.056, largest change 23.40 cents); rule B offers none (its three blocks' `steadiness` 14.6307 to 14.6343 cents, `fold2.json`, the take's 0.0018 above its steadiest). `held-steady.wav` and `held-vibrato.wav`: steadiness measured, no strength improved, so no step (the vibrato's 0.467 cents is 2 Hz leakage the steadying cannot remove: 0.459 at full strength). `signal/sine-220hz.wav`: steadiness unmeasurable, no held note. MT-008's margin, *S* − *S*′ − 2√(*u*² + *u*′²) (`margins` per strength): on `held-wobble.wav` −0.053 cents at strength 2 and +0.175 at 3, the next step; on `held-steady.wav` −0.508 and on `held-vibrato.wav` at most −0.499 at every strength |

**What this says for squillo.** Rule A offers a step on most real takes
where steadiness is measured; rule B on few, because a take's ± for
steadiness is wide against the spread of its blocks. "Reachable" can then
mean what `synthesis` delivers and `metrics` can show, not what the singer
has already sung. The next step is the *least* step that can be shown,
which on real voices is not small: the ladder from a take to its far
vision has one or two measurable rungs, not many. Steadiness is
unmeasured on 112 of 159 takes (scales and arpeggios have no 2 s held
note), so an exercise that gives held notes is a precondition of any step.

**Limits.** Trained singers, long tones only; no amateur. The rung is
evaluated from its description, as squillo SY-004 states it, never from
synthesized audio. The grid of 64 strengths was chosen before the run; a
finer grid could move a next step by at most one strength.

### Round 4: the ring ratio on repeated material, with a noise gate (squillo iteration 49, 2026-09-28)

Set by squillo review R-09 for iteration 49 (finding F-036): round 2's ring
ratio (results 24, 25) tells forte from pianissimo but moves with the notes
sung, so the halves of one take were called changed in 28.5 % of takes, and
noise biases it (called changed in 10.1 % of takes at 20 dB SNR). Squillo
compares a measure only between runs of the same exercise and subject
(`coach` CO-002), which is repeated material. Round 4 asks whether comparing
two renditions **note by note, on the notes both sing**, with a ± from
repeated material, makes the ring ratio comparable, and whether a gate read
from the take's own quiet frames keeps noise from calling a change.

**Rules, written in `r4_ring.py`'s docstring and committed before any real
take was read** (S15, L-041): the note of a frame (a 25-frame running median
of its pitch, against the take's own tuning), occurrences (runs of at least
37 frames, trimmed 6 at each end), a side's ring ratio per note, the
comparison of two sides on their shared notes (D, the mean difference over
*k* shared notes), a random-effects ± fitted on no-change pairs of one fold
of singers (*u*² = τ² + σ_w²/*k*, called changed beyond 2*u*), the noise
estimate (median band power over the take's quietest 10 % of frames) and
three variants: no gate (V0), a gate on each note's 2–4 kHz SNR (V1), and
the gate with the noise subtracted (V2). Bars: **B1**, the matched
comparison's false change on the halves of a take, tested on the other fold,
at most 5 %; **B3**, with the gate chosen on one fold, false change at most
5 % in every noise condition on the other, comparing a noisy half with the
other half clean. Sensitivity (forte against pp, breathy against straight
scales, same singer) is reported with no bar.

**Checks of the checks.**

| Check | Result |
| :--- | :--- |
| Synthetic pipeline check (`r4_ring.py check`, `results/r4_check.json`), before any real take: a harmonic take whose envelope makes the ring ratio depend on the note, half A on five notes, half B on five with two shared; every harmonic at least 3 bins from 50 Hz, 2 kHz and 4 kHz (asserted; 8 such notes between C4 and C6). Bound per note from the Hann window's own leakage 3 bins out, ε = 1.14 × 10⁻⁴ (computed from the window) | Must pass, S0 (same envelope): every note's ring within its bound of the value from the harmonic amplitudes; matched D = 0.000 dB (*k* = 2, bound 0.0044); the unmatched D 0.6707 dB against 0.6707 expected, so the note dependence is in the input. Must fail for "no change", S1 (B's 2–4 kHz harmonics doubled): matched D 6.0206 dB against 20 log10 2 = 6.0206 (bound 0.0047) |
| B1's own check | Must pass, the fitting fold's own clean pairs: 3 of 79 called changed (3.8 %), passes. Must fail, the halves with half B's 2–4 kHz band raised 6.02 dB by an FFT gain, on the test fold: 19 of 71 called changed (26.8 %, Wilson 17.9–38.1 %; D median +6.63 dB), fails the bar as it must. The bar can fail, and the ± is wide enough that a real 6 dB change is mostly missed (result 38) |
| B3's own check | Must fail, V0 (no gate) at white 10 dB on the fitting fold: fails with the odd singers as the fitting fold (4 of 34, 11.8 %) but **passes with the even singers** (1 of 41, 2.4 %). Round 2's 38.8 % was under round 2's block *u*, far narrower than this ± (result 37), so it does not carry over. The gate's bar is checked on one fold of two. Must pass, the chosen gate on clean input on the fitting fold: 1 of 33 and 2 of 46 (V1 and V2 alike), passes |

**Run** (S19): `uv run python r4_ring.py check && uv run python r4_ring.py
time && uv run python r4_ring.py run && uv run python r4_ring.py analyse &&
uv run python r4_ring.py posthoc`. The timed sample was 10 files at a pool
of 16, 5.6 s each, estimated at 0.9 minutes for 159. That underestimates: 10
files keep only 10 of the 16 processes busy, not the full pool S19 asks
for. The run took 1 minute 24 seconds. The analysis took 0.2 s on the
first 16 takes' outputs and 5.9 s on all. Numbers: `results/r4_ring.json`
(the bars), `results/r4_check.json`, and `results/r4_posthoc.json` and
`results/r4_posthoc_same_vowel.json` (post hoc, see below). Occurrences
cache: `data/cache/r4_occ.pkl` (not committed; regenerated by `run`).

**Results.** The ± model is *u* = √(τ² + σ_w²/*k*) over *k* shared notes,
called changed beyond 2*u*. All shares are on the test fold, pooled over
both folds, with Wilson 95 % intervals.

| # | Question | Result |
| :--- | :--- | :--- |
| 37 | How far apart are two renditions of the same notes? | Of 159 takes, 79 have halves that share a note (median *k* 2): 19 of 20 in each scale set, 12 vibrato arpeggios, 15 rounds, and only 14 of 80 long tones, whose halves sing other notes. The same note in the other half differs by σ_w = 3.46 dB (even singers) and 3.97 dB (odd). The halves as a whole differ by τ = 3.83 and 3.85 dB beyond that. So 2*u* is at least 2τ = 7.7 dB, whatever *k* |
| 38 | B1: false change on repeated material | 3 of 79 (3.8 %, 1.3–10.6 %): **passes**. It passes because the ± is wide. The three calls, and one more on the fitting fold, are on the round (whose halves sing other words) and on messa di voce (whose loudness changes by design); none is on a scale or an arpeggio. A 6.02 dB rise in the 2–4 kHz band is called in 26.8 % |
| 39 | Does matching notes remove round 2's problem? | Round 2's test on the same takes calls 45 of 158 changed (28.5 %). The matched comparison calls 3.8 %, but only because its ± is wider. The discrepancy itself did not shrink: the RMS of D over the 79 no-change pairs is 4.69 dB matched against 3.96 dB unmatched. The ring ratio moves between renditions of the same notes by as much as between different notes |
| 40 | Sensitivity, whole take against whole take, same singer | Forte against pp: 17 of 20 singers comparable (median *k* 3), forte higher in 15, D median +7.75 dB, **called changed for 6 of 17**. Straight against breathy scales: 20 comparable (median *k* 7), straight higher in 18, D median +6.99 dB, called for 8 of 20. Round 2, unmatched with a block *u*, told forte from pp in 19 of 20 |
| 41 | B3: the noise gate | V0 (no gate) fails (pink 20 dB 6.9 %; with the odd fold as fit, no *g* passes). **V1 and V2 pass, both with *g* = 0 dB on both folds**: a note counts only where its 2–4 kHz power exceeds the noise estimate. V1 on the test fold: clean 3.8 %, white 30 dB 4.6 % (7 of 153), white 20 dB 3.6 % (5 of 137), white 10 dB 0 of 55, pink 20 dB 4.3 % (6 of 138), pink 10 dB 0 of 54. Comparable pairs: 48 % at 30 dB, 43 % at 20 dB, 17 % at 10 dB. V2 differs by one call at clean (4 of 79) and at white 30 dB (6 of 153). Recommended by the rule: V1 (a tie at white 20 dB, 137 pairs each) |
| 42 | The noise estimate | The take's quietest 10 % of frames are unvoiced in the median take (share accepted by YIN 0). The median note's 2–4 kHz SNR, clean, is 46.3 dB |

**Post hoc** (`r4_ring.py posthoc`, written after the results above were
seen, so a reading and not a test). By set, the mean D (second half minus
first) is +5.99 dB for the round, with the second half higher in 13 of 15:
its halves sing other words on other vowels. It is −3.33 dB for messa di
voce (SD 7.99), whose loudness changes by design. It is +0.17 and +0.80 dB
(SD 2.62 and 3.26) for breathy and straight scales, whose descent sings the
ascent's notes on the same vowel. Refitted on the same-vowel sets only
(scales and vibrato arpeggios, 50 pairs, median *k* 5): σ_w 3.21 and 3.50
dB, τ 2.72 and 2.64 dB, so 2*u* is 8.4–8.8 dB at *k* = 1, 6.6 at *k* = 3
and 5.9–6.0 at *k* = 7. False change 1 of 50 (2.0 %). The 6.02 dB rise is
called in 20 of 47 (42.6 %). Forte against pp is called for 9 of 17 and
breathy against straight for 11 of 20. Singing level explains almost none
of it: over 288 shared notes, d_n correlates with the change in the note's
50 Hz–2 kHz level at r = 0.11, and removing a fitted slope (0.15 dB per dB)
takes its RMS from 4.78 to 4.64 dB.

**What this says for squillo (F-036).**

- **On repeated material the ring ratio can show only large changes.**
  Even on the same notes and the same vowel, two renditions differ by about
  2.6–3.8 dB as a whole (τ) and 3.2–4.0 dB note by note (σ_w). A comparison
  calls a change only beyond about 6 to 11 dB (2*u*: 8.1–8.3 dB at *k* = 7
  and 10.3–11.1 dB at *k* = 1 on the fit over all sets, 8.0–11.1 dB over
  the *k* 1 to 9 the takes have and 9.1–9.5 dB at the no-change pairs'
  median *k* = 2, held in `results/r10_two_u.json` since R-10; 5.9–6.0 and
  8.4–8.8 dB on the post-hoc refit with the same vowel), about the size of the difference
  between forte and pianissimo (median 7.75 dB). It sees that difference in
  6–9 of 17 singers and a 6 dB rise in 27–43 % of cases. As a measure of
  progress in tone it would mostly say "no change shown".
- **Matching notes is necessary but not enough.** It keeps a comparison to
  the notes both takes sing, and a take without shared notes is not
  compared. It does not make renditions agree: the rendition term τ
  dominates the ±, and more shared notes cannot shrink it.
- **Words matter.** Halves on other vowels differ by +6 dB on average (the
  round), so an own-song comparison is honest only on the same line. The
  vowel is not measured here.
- **The noise gate passes its bar, checked on one fold only.** Counting a
  note only where its 2–4 kHz power exceeds the take's own noise estimate
  keeps false change at or under 4.6 % down to 10 dB SNR. But its
  must-fail case (no gate at white 10 dB) failed the bar only with the odd
  singers as the fit (11.8 %), and passed it with the even ones (2.4 %),
  so on that fold the bar could not tell a gate from none (R-10: the gate
  is shown on one fold of two). Below about 20 dB it leaves most
  takes with nothing comparable.
- **Checks asserted (squillo iteration 63, F-054 (a)).** Since R-10,
  `B1_check_*` and `B3_check` were written to `r4_ring.json` and never
  asserted (S15). `r4_ring.py` now refuses to run uncommitted
  (`committed_first`) and `assert_checks` stops `analyse` before
  `r4_ring.json` is written unless B1's fitting-fold check passes, its
  6.02 dB boost fails the bar, the chosen gate passes on clean input on both
  fitting folds (V1 and V2), and no gate at white 10 dB fails the bar with
  the odd singers as the fit; with the even singers its pass (1 of 41) is
  asserted unchanged, so the gate stays shown on one fold of two. Re-run
  after the rules commit: `r4_ring.json` byte-identical, no value moved.
  Must-fail of the asserts, each on `r4_ring.json` with one outcome changed
  (the boost called in none, the fitting fold over 5 %, no gate passing on
  the odd fold, failing on the even, V2 failing clean): 5 of 5 stop it.
  `tools/checkkeys.py` flags `B3_check` by name only: it is asserted through
  the local `b3` (`assert_checks`), read by hand.
- For the fold: squillo can specify tone as the ring ratio compared note by
  note with *u* = √(τ² + σ_w²/*k*), from τ and σ_w above, and say what size
  of change it can show. Or it can leave tone out of the first slice, with
  that size as the reason. The microphone's response (round 2) is still
  unknown. It cancels only between takes on the same microphone.
- **Folded in squillo iteration 52** (Q-029 part 1 A, F-036): tone is left
  out of the first slice. Squillo's `metrics` MT-001 states that catalogue
  version 2 holds no measure of tone, with τ, σ_w, 2*u* 8.0–11.1 dB and
  forte against pp called for 6 of 17 as the reason (`@ 6d99459`), and
  `ui` UI-001 tells the singer, in words, that tone is not measured and
  why (ADR 0004, ADR 0017, ADR 0020). The `needs-human` step below, on
  separate takes, may re-rank it.

**Limits.** VocalSet holds no second take of the same material. The two
renditions are the halves of one take (a scale's ascent and descent), so τ
may differ between separate takes. Twenty trained singers, /a/ except in
the round. Noise is stationary and added. The rooms were not run.

**Needs a human** (15 minutes, any microphone, a quiet room): record four
takes of the same one-octave major scale on "ah", up and down, at a
comfortable pitch: `same1.wav` and `same2.wav` sung the same way, then
`ring1.wav` and `ring2.wav` with a brighter, more ringing tone. Run
`uv run python r4_ring.py run` first if `data/cache/r4_occ.pkl` is missing,
then `uv run python r4_own.py same1.wav same2.wav ring1.wav ring2.wav`. It
writes `results/own_r4.json`: each pair's D, *k*, 2*u* and whether a change
is called. The ± is fitted on all of round 4's no-change pairs, both folds.
Note in `results/own_r4.md` whether you heard the difference the numbers
report. Commit the two results files, never the audio. A smoke run on
VocalSet's f1 scales passed (the same file twice gives D = 0, not called;
breathy against straight gives D = −13.03 dB, called).

### Fold F1 re-read per set and on E-003's inputs (squillo iteration 63, F-052)

**Run:** `uv run python f052_sets.py check`, then `uv run python
f052_sets.py run` (writes `results/f052_sets.json`). Rules, bars R1 and
R2, and the checks P1 and P4 are in the script's docstring, committed
before any run (`f052_sets.py`, its first commit). Needs round 2's
`data/cache/r2_frames.npz` and `data/cache/r2/*.npz`, and E-003 round 2's
`data/cache/r2/measures.pkl` and `in/` files.

**Estimate (S19), committed before the full run.** `time`: 8 of the 80
long tones (singers f1 and m11, all four sets) through P4's live
recompute and P5's binary64 measure in 1.0 s at a pool of 16, so the 80 in
under 0.2 minutes; the analysis (81 per-set selections per condition
group, 1000 singer resamples each) is array arithmetic on counts, under a
minute. `check` alone ran in seconds.

**Result** (`results/f052_sets.json`; 12.4 s in all, `seconds`, of which
P4 and P5 8.9 s at a pool of 16, inside the estimate; a second run
identical but for `seconds`). Coverage is the share of
accepted frames within ±2*u* under MT-003's table as squillo states it;
intervals are 95 % over 1000 resamples of the singers.

| # | Question | Result |
| :--- | :--- | :--- |
| F052-1 | Checks | P1: fold F1's spec coverage recomputed from the cache, 94.46 % on 132 373 accepted frames (all 20) and 95.25 % on 56 414 (the even ten), equal to `fold2.json`; with the table's entries above √3 times 0.9, 93.37 %, not equal, as it must not be. E-003's raw clean direct 93.20 % on 69 649, equal to `analysis.json`; its white-20 frames 96.06 % on 27 163, not equal. P4: E-003's clean frame statistics recomputed from its 80 written files equal the pickle's in 80 of 80 takes, and the white-20 pickle's in 0 of 80. R2's own check: all sets clean, held out, 95.25 % (93.66–96.35 %), not shown under, as it must not be; room 0.8 s, 64.93 % (57.63–69.74 %), shown under, as it must be. `tools/checkkeys.py`: 0 flagged |
| F052-2 | Is the shortfall the subset or the input path? (P3, P5) | **The subset.** G = 94.46 − 93.20 = 1.26 points (0.58–2.18), shown. S, all 159 takes against the 80 long tones on E-002's own frames (94.46 against 93.20 %): 1.26 points (0.58–2.18), shown. P, E-002's 80 against E-003's: 0.0016 points (−0.0074 to +0.0104), not shown; of it, level and padding 0 exactly (the binary64 padded signal gives E-002's frames' coverage, 93.2018 %), 16-bit rounding 0.0016 points (not shown): 5 of 80 takes accept a frame more or fewer, 69 651 against 69 649 in all. **The frame-validity rule is not a cause**: valid frames are equal take by take, 0 of 80 differing, 90 583 on every side |
| F052-3 | ±2*u* per set, clean, on the ten held-out singers (R2) | LT-straight 98.38 % (97.65–99.12), SC-straight 99.41 % (99.12–99.67), SC-breathy 97.64 % (95.93–98.84), VIB-arpeggio 98.98 % (98.13–99.69): shown at or over 95 %. LT-forte 94.04 % (90.29–96.63), LT-messa 93.23 % (88.83–95.68): not shown either way. **LT-pp 91.36 % (88.39–94.24) and VIB-row 91.22 % (89.34–93.78): shown under 95 %.** All sets 95.25 % (93.66–96.35): not shown either way, so fold F1's 95.2 % is a point whose singer interval reaches below 95 % |
| F052-4 | The same on all 20 singers, and on E-003's inputs | E-002 clean, all 20: LT-straight 96.51 %, LT-forte 94.02 %, LT-messa 92.08 %, LT-pp 90.93 %, SC-straight 98.50 %, SC-breathy 96.45 %, VIB-arpeggio 97.93 %, VIB-row 90.74 %. E-003's inputs, clean, all 20: LT-straight 96.51 % (92.39–98.72), LT-forte 94.02 % (91.95–95.88), LT-pp 90.93 % (88.38–93.28), LT-messa 92.07 % (88.89–94.76); the even ten 94.17 % over the four. In noise coverage rises as frames are refused: E-002 held out, white 20 dB, 95.7–99.9 % per set; the room at 0.4 s, 66.5 % (LT-pp) to 91.6 % (LT-straight) |

**What this says for squillo.** MT-003's table does not fail on E-003's
input path: the 93.20 % is the long tones' own coverage, the same on
E-002's frames to 0.002 points. The pooled 95.2 % on held-out singers
hides a spread by material: on soft long tones and on the sung round, the
one set with words and consonants and so the closest to a singer's own
song, ±2*u* is shown to cover under 95 % (91.4 % and 91.2 % held out). No
bound changes here, and nothing refits the table; by the rule written
before the run, these are limits MT-003's reason states with their
numbers, in squillo iteration 64's fold. Why these two sets fall short
was not asked and is not attributed.

**Limits.** Twenty trained singers re-synthesized with WORLD for a known
pitch (round 2's limits); ten held-out singers per set, so a set's
interval is wide (up to 7 points); the bootstrap resamples singers, not
takes, and treats the ten as exchangeable. Nothing here measures an
amateur or a real microphone.

### Round 5: held notes trimmed to their measured cells, and the next step against blocks (squillo iteration 78, F-070, F-046)

**Run:** `uv run python r5_trim.py check <squillo>`, `sample`, `run`, then
`analyse` (writes `results/r5_trim.json`). Rules T0 to T4 and B0 to B2,
the bars T1 and T2 and the constructed cases P and Q are in the script's
docstring, committed before any run (`5dd50dc`; revision 1, `check`'s
own assertion on the constructed case, before any data was read). Needs
round 2's `data/cache/r2_frames.npz`, `results/fold2.json` and
`results/fold3_ladder.json`, and E-004 round 4's `data/cache/r4/`,
`results/r4/held.json` and `results/r4/diag.json`; the 936 renderings
are re-made by E-004's `r4_held.one` into `data/cache/r5/`, resumable.

**Estimate (S19), committed before the full run.** `sample`: 32
renderings (the longest and shortest items, `held-ah` and `ode-to-joy`,
bass and high soprano, every spread and vibrato condition) in 8.9 s at a
pool of 16, so the 936 in about 232 s (`results/r5_sample.json`); round
2's evaluation under one finder 10.1 s and part B under one finder 14.2 s
on one process, so `analyse` (three evaluations, the finders compared on
every take, part B twice, the renderings read) about 2 minutes.

**Revisions, each committed before the run it governs.** (1, `0e07c44`) `check`
stopped on its own assertion before any data was read: across the step
the cut forms one-frame pieces, so the constructed case's cut is read at
the piece holding the second note. (2, `827c63d`) The first `analyse` stopped on
T2's must-fail case and printed T2's outcome (true) with it: dividing
the block *u* by 1000 cannot fail the bar, since a take's *u* is
κ √(*s*²/*n* + *ū*²) and *s* dominates; the must-fail input became every
block value moved off its truth (`SHIFT`), written after that outcome was
seen; the bar is unchanged. (3, `6e3676a`) The next `analyse` stopped on B0 (fold
3's next step reproduced on 31 of 47 original takes; part B's summaries
unseen): the steadying moves the cut by a few frames, so a rung's blocks
rarely start on the take's frames; a rung at *n* is measured on its own
first *n* blocks in time order, and on all at *n* = *B*, as fold 3.

**Checks (S15; C1, C3, C10 to C19 applied).** P and Q, the constructed
contours, have their conditions asserted on them: in P the piece holding
the second note begins on a frame not accepted (frame 310, after one-frame
pieces from 300; trimmed, it begins at 312), in Q every cut falls on an accepted frame.
The trimmed finder recovers P's second note (2 held notes against 1,
must pass) and nothing in Q (2 and 2, must fail). `finder(trim=False)`
equals `fold2.held_notes` and every current held note is a trimmed one,
asserted on every take of every condition and every rendering. T0: the
936 renderings re-made equal their cached held notes and blocks, diag's
26 renderings match note by note, 26 of 360 lost; round 2's evaluation
under the current finder equals `fold2.json` `measures.spec.eval`. T1's
bar passes on P and fails on the current finder's 26. T2's bar passes on
the current finder and fails on the shifted blocks. T3: squillo's
`held-steady`, `held-wobble`, `held-vibrato` and `sine-220hz` give the
same held notes and take values under both finders (must pass); P does
not (must fail). B0: at *n* = *B*, fold 3's next step on 47 of 47
original and 43 of 43 clean takes (must pass); against the list rotated
by one take, not (must fail). `tools/checkkeys.py r5_trim.py
results/r5_trim.json`: 0 flagged.

**Result** (`results/r5_trim.json`; the 936 renderings in 253 s at a
pool of 16, inside the estimate; `analyse` 76.3 s). Strengths are
fractions of the steadying SY-002 allows (fold 3's `next_strength`).

| # | Question | Result |
| :--- | :--- | :--- |
| T1 | Written held notes lost, E-004 round 4's 9 new items, 216 renderings | **Trimmed: 1 of 360** (Wilson 95 % 0.0–1.6 %; `halfway-home`, tenor, spread 20, vibrato, which still gives 2 blocks), against 26 of 360 (5.0–10.4 %) now. **Bar T1 passes.** All 39 items, 936 renderings: 2 of 456 lost (0.1–1.6 %) against 50 of 456 (8.4–14.2 %) |
| T2 | MT-010's coverage on round 2's clean re-syntheses, squillo's constants unchanged | Trimmed: 125 held notes (117 now), 45 takes measured (43); the take's ± covers its true value on **38 of 38** takes for steadiness and extent and **25 of 25** for rate (now 36, 36, 23). **Bar T2 passes.** White 30 dB 31 of 31 (29 now); white and pink 20 dB unchanged in takes; the rooms unchanged in coverage (extent 8 of 11 at 0.4 s, 1 of 2 at 0.8 s, F-030) |
| T4 | Where the finders differ | 28 take-conditions gain one held note each (clean 8, original 9; original takes measured 50, was 47). Renderings: 58 of 936 gain blocks, none lose any. Every item CO-005 rule (2) gives at least 2 blocks now gives MT-009 at least 2 on all 24 renderings (11 items, against 6; with `holy-holy-holy` below, 12 items give 2 on all 24, `bar_B_items`): `abide-with-me` 24 of 24 (14 now), `le-pays-des-reves` 24 of 24 (18), the three new one-held-note items 72 of 72 (61 of 72 now, Wilson 94.9–100 %). `apres-un-reve` (rule (2): 1) 2 of 24, `holy-holy-holy` (rule (2): 1) 24 of 24 |
| B1 | The next step against the blocks, original takes with at least 4 blocks (20) | Under the current (untrimmed) finder, as the rules set (`B.current`); the trimmed finder, MT-009's from squillo iteration 79, is recorded beside it (`B.trimmed`, below). **More blocks do not make the next step smaller.** A step at 2 blocks on 12, at 4 on 10, at all *B* on 14. On the 6 with a step at both 2 and 4, the median strength 0.70 at 2 and 0.59 at 4 (4 fell, 2 rose). Over all takes per *n*, the median strength stays 0.50 to 0.68 from *n* = 2 (0.566, 47 takes) to 8 (0.679, 2 takes), while the median take *u* falls from 1.97 to 1.13 cents. The prediction (more steps at 4 than at 2, and the paired median falling) **does not hold**. Clean re-syntheses alike: 8 at 2, 6 at 4 of 16; paired 0.67 to 0.60 on 4. **Trimmed finder** (`B.trimmed`): of the 20 original takes with at least 4 blocks, a step at 2 on 11, at 4 on 9, at all *B* on 12; paired 0.73 to 0.58 on 5 (4 fell, 1 rose); over all takes the median strength 0.49 to 0.68 from *n* = 2 (0.540, 50 takes) to 8 (0.679, 2); the prediction does not hold. Clean: 8 at 2, 7 at 4 of 17 (squillo R-16, F-076) |
| B2 | The floor: the take's *u* with the spread of its blocks dropped (κ *ū*), a model | The least strength improved would be a median **0.115** (0.063–0.245) on 47 of 47 original takes, against 0.627 measured on 28 of 47 with all blocks; median *u* 0.23 against 2.02 cents (current finder, `B.current`). Trimmed finder (`B.trimmed`): 0.115 (0.030–0.302) on 50 of 50, against 0.609 on 26 of 50; median *u* 0.23 against 2.11 cents. Clean: 0.109 on 43 of 43 (trimmed 45 of 45) |

**What this says for squillo.** F-070: trimming each piece to its first
and last measured cells finds the written held notes MT-009 now loses (25
of the 26) and costs nothing measured: every held note found now is found
unchanged, and MT-010's coverage holds on the takes it adds. A `metrics`
change can state it, with CO-005 rule (2) no longer overstating for a
phrase with one held note on these renderings. F-046: a take's
`steadiness` ± is wide because its blocks differ from one another (the
*s*²/*n* term), not because tracking is coarse (median κ *ū* 0.23 cents);
adding blocks of the same singing narrows it only as 1/√*n*, and over 2 to
8 blocks the next step stayed most of the way. So "longer held notes" is
not a lever on these takes, and the coarse ladder is the honest one under
MT-008 as it stands. The floor says what is lost: compared with tracking
alone, the least rung would be a median 0.115 of the steadying, not 0.627. One lever was not
measured here: a rung is the take itself changed, so the take and its
rung share their blocks' spread, and a paired comparison (per-block
differences) would not pay it; whether `metrics` may call a rung improved
that way, when the singer's next take is compared unpaired, is a
decision for squillo's fold, not a result.

**Limits.** Twenty trained singers, long tones (round 2's limits); E-004's
renderings are E-005's synthetic voice. Part B takes the first *n* blocks
of a take as the shorter take, so a shorter held note's own 2 Hz contour
and cut are not modelled; 2 to 8 blocks only, few takes at 6 or more. The
floor is a model's extrapolation, never a measurement. Pooling the blocks
of several takes is not measured.

**Folded** in squillo iteration 79 (change `fold-held-notes-trimmed`):
`metrics` MT-009 trims each piece to its first and last measured cells
(ADR 0004, F-070 fixed); `coach` CO-004 compares a rung with the take only
as MT-008 compares two takes, never by pairing their blocks, so the
coarse ladder stays (ADR 0018, F-046 closed with its reason). No `metrics`
fixture tells the two finders apart (T3), so squillo logs F-075 for one.

### Round 5, the 40th phrase (squillo iteration 87, F-060's fold)

E-004 fold 4 ships a 40th phrase, *Hên Wlad fy Nhadau*, so round 5's T4
counts on the shipped phrases' renderings, which squillo cites (MT-009's
reason, ADR 0004, ADR 0022), are extended by its 24 renderings, made and
measured exactly as round 5's. `r5_add.py`, rules committed before the
run (`0ed5788`); `uv run python r5_add.py run <squillo>` (10 s at a pool
of 12) -> `results/r5_add.json`, rows in `data/cache/r5_add/`.

| # | Question | Result (conditions; uncertainty) |
| ---: | :--- | :--- |
| A0 | Does `measure` reproduce round 5? | Yes: on round 5's first two jobs it equals the saved rows under both finders (must pass); against the other seed's row it differs (must fail) |
| A2 | The anthem's 24 renderings (4 voices, σ 0 and 20 cents, vibrato off and on) | Its one written held note, the final half note, is exactly 250 frames, MT-009's least. **Lost on 9 of 24** renderings under the trimmed finder and on 9 of 24 under the current one; no rendering gives two blocks (0 to 1), as predicted |
| A2 | The 40 shipped phrases (round 5's 39 plus these) | Trimmed finder: **11 of 480** written held notes lost, Wilson 95 % 1.3–4.1 % (39: 2 of 456); current finder: 59 of 480, 9.7–15.5 % |

Not diagnosed: why each of the 9 is lost. A note of exactly 250 frames is
held only if every one of its frames is measured and inside one piece, so
any frame refused or cut at either end loses it; that is the bound's
arithmetic, not a measured cause.

**S15 by hand.** `tools/checkkeys.py r5_add.py`: 0 flags on the script
alone before its run, and 0 with `results/r5_add.json`. `A0_must_pass`
and `A0_must_fail` are asserted; `prediction_no_two_blocks` is a
prediction, recorded, true.

### Round 6: a fixture that tells trimmed pieces from untrimmed ones (squillo iteration 88, F-075)

**Question.** Round 5's T3 found no squillo fixture on which MT-009's
trimmed pieces (squillo iteration 79) and the untrimmed ones give
different held notes, so an implementer who kept the old rule would pass
every MT-009 scenario. Is there a short generated tone, round 5's
constructed case P made into samples, that tells them apart, robustly to
the tracker's arithmetic?

**Run:** `uv run python r6_fixture.py <squillo>` ->
`results/r6_fixture.json` and `results/r6/two-notes-gap.wav`, in a few
seconds; then `uv run python r6_posthoc.py <squillo>` (4 s) -> `results/r6_posthoc.json`.
The fixture's formula, conditions K1 to K4, the selection rule for the
silence's length, the hypothesis H, the robustness check R1 and the
checks' must-fail inputs are in the script's docstring, committed before
any run (`ec38f04`). **Revision 1** (`7a94e25`): the first run stopped
writing the results file on a numpy bool after every assertion had
passed and before anything was printed; no rule changed. The post hoc
script was written after the results were read and committed before it
ran (`378075f`); it is counted apart.

**The fixture.** Mono, 48 kHz, IEEE float 32-bit (fold 2's writer):
0.5 sin(2π · 220 · *n* / 48000) for 124 800 samples (2.6 s), then 384 *m*
samples of 0, then 0.5 sin(2π · 220 · 2^(2/12) · *n* / 48000), *n* from
0 again, for 124 800 samples: A3, silence, B3, 200 cents apart. The
selection rule takes the least *m* in 1 to 16 for which K1 to K4 hold:
both tones inside E2 to C6 and peak at most 1 (K1); every frame whose
pitch window holds one tone only measured (K2); the frames not measured
one stretch of at most 12, so the take is one run (K3); the last cut,
where the piece holding the second tone begins, on a frame not measured
with a frame not measured either side (K4). *m* = 1 to 8 met K1 to K3 but
not K4; **m = 9** met all four: 3456 samples of silence, 253 056
samples (5.272 s) in all, sha256
`2c00ad4d861ef889dbdef6e489fcf553a3cb73b988a43c642376f6125e5678fd`.

**Checks (S15; C1, C3, C10, C11, C14 to C18 applied).** K1 to K4 are
asserted on the file as written and read back. Each check ran on the
fixture (must pass) and on an input that differs in what it reads (must
fail), all before H was computed: K3 fails at *m* = 20 (one stretch, frames
326 to 347); K4 and the finders' difference fail on Q, the same
silence moved 100 frames into the second tone (the last cut, frame 331,
is measured; both finders give the same two held notes, 3 to 320 and 331
to 658; Q also fails K3, since its clean step refuses frames 326 and 327,
whose windows hold both tones, a second stretch beside the silence's 426
to 436); R1 (float32 tracking gives every cell the same state and both
finders the same held notes' first and last frames and measured cells,
from which the blocks' frames follow) fails when the fixture's float64
states are compared with Q's float32 ones. Round 5's identities
(untrimmed equals `fold2.held_notes`; every untrimmed held note is a
trimmed one) are asserted on all three inputs. `tools/checkkeys.py`:
0 flags on each script alone before its run; with the results, 1 flag on
each, `checks`, the object that holds the asserted keys (each of its
members is asserted by name), read by hand.

**Result** (`results/r6_fixture.json`; numpy YIN, the MT-003 table of
`fold2.json`, MT-009 to MT-011's constants as squillo states them).

| # | Question | Result (conditions; uncertainty) |
| :--- | :--- | :--- |
| K | The cells | Frames 3 to 658; not measured: frames **326 to 336**, one stretch, every other frame measured. The cut across the step forms one-frame pieces, cut at frames 325 to 335; the last, where the second tone's piece begins, is frame 335, not measured |
| H | Trimmed against untrimmed (MT-009 as stated, and as before iteration 79) | **H holds.** Trimmed: **two held notes, frames 3 to 324 and 337 to 658**, one block each (**65 to 189** and **399 to 523**), so `steadiness` is measured (2.2 × 10⁻⁶ cents, standard *u* 0.18, 2 blocks) and `vibrato-extent` too (0.00024 cents, *u* 1.11); `vibrato-rate` unmeasurable. Untrimmed: **one held note, frames 3 to 324**, one block (65 to 189), so `steadiness`, `vibrato-extent` and `vibrato-rate` are each unmeasurable |
| R1 | float32 tracking | Same cell states, same held notes under both finders |
| D1 | Post hoc: how near a cut is to moving | The pieces' least distance from the 60-cent threshold is 1.0 cents for the first piece (cut at 325) and 3.9 to 28.7 cents for the one-frame pieces; 0.037 cents for the last piece, which is never cut. That figure includes each piece's first frame, which the cut loop never tests, so it is a lower bound, and no cut lies within it |
| D2 | Post hoc: every measured cell moved by an independent uniform offset in ±*e* cents, 200 seeds per *e* | *e* = 0.0082 (ADR 0007's host epsilon), 0.037, 0.1, 0.3 and 1.0: H holds and every held note's and block's frames equal the fixture's on **200 of 200** under both finders. *e* = 3.0: H holds on 200 of 200, the frames equal on 186 of 200 |
| D3 | Post hoc: float32 against float64 tracking | Largest difference on the measured cells 0.0020 cents (0.0019993) |

**What this says for squillo.** F-075 can be settled: the fixture tells
the two rules apart in a way a test sees, two held notes against one and
`steadiness` measured against unmeasurable, and the frames a scenario
would name (held notes 3 to 324 and 337 to 658, blocks 65 to 189 and 399
to 523) did not move under offsets up to 1 cent per cell, against a
float32 tracking that differs by at most 0.0020 cents (D3) and ADR
0007's host epsilon of 0.0082. Folded in squillo iteration 89
(change `fold-two-notes-gap`): the file, byte for byte and regenerated
identical at `1c8f7f0`, is `fixtures/metrics/two-notes-gap.wav`, and
MT-009's scenario on it names those frames and `steadiness` measured.

**Limits.** One tracker (numpy YIN at squillo's frame axis); the WASM
targets' epsilon is unmeasured (squillo Stage E, iterations 92 and 93;
measured since, round 7),
and D2's offsets are independent per cell, not the correlated error an
arithmetic change gives. Silence is the only refusal used; a real glide
refused for aperiodicity (E-004 round 4's lost notes) is not modelled
here, round 5 measured that on renderings.

### Round 7: the numeric epsilon across WASM targets (squillo iteration 92, S-004)

**Question.** S-004 above: how far apart are the pitches the same tracker
reports in each target browser's WASM, in a native build and in numpy,
in `f32` and in `f64` arithmetic? The spread is squillo ADR 0007's
*Numeric epsilon*, whose host part (`f32` against `f64` in numpy,
0.0082 cents, result 9) is all that was measured. Serves VISION §5, §6,
§12.2.

**What runs.** `wasm/` is ADR 0007's YIN, as `yin.py` runs it (frame
axis, lags 16 to 763, *W* = 773, CMND threshold 0.1, first dip then down
it, parabolic interpolation on *d*), in Rust, in four variants: the
difference function as a sum of squared differences (`direct`, de
Cheveigné and Kawahara 2002, eq. 6) or as `yin.py` computes it, *e*₀ +
*e*_τ − 2*r* with *r* by FFT (`fft`, realfft 3.5.0 over rustfft 6.4.1),
each in `f64` or `f32` throughout. Input samples are `f32` everywhere,
as ADR 0002 delivers them. Targets: native x86-64 (rustfft's run-time
AVX/SSE paths), and WASM plain and with `simd128` (rustfft's
`wasm_simd`), each in the installed Chrome and Firefox, headless, in a
module worker (E-001 round 2's harness). numpy's `yin.py` in `float64`
is the reference; numpy in `float32` is result 9's host path.

**Inputs** (`r7_inputs.py`): squillo's eleven `fixtures/signal/` files,
byte for byte, SHA-256 checked against squillo's `fixtures/MANIFEST.md`;
round 1's generator (`run.py` `tone`, `add_noise`), seed 20261003, the 41
semitones E2 to C6 pure and `saw12` clean (result 9's design) and `saw12`
at 20 and 10 dB SNR (result 4: frames near the threshold); and one
original take per VocalSet singer, 20, as round 2 resampled them
(`r2_truth.py` line 72, saved `float32` line 112), the first in sorted
order.

**Hypotheses** (`r7_analyse.py` `HYPOTHESES`, committed before any
output existed). **H1:** for each build and variant, Chrome's and
Firefox's outputs are bit-identical on every frame (WebAssembly's
numeric operations are deterministic IEEE 754 except NaN payloads;
E-001 round 2 found its outputs identical across both browsers). **H2:**
for the direct variants, every browser build equals the native build
bit for bit (only +, −, ×, ÷ and comparisons; Rust neither fuses nor
reassociates; no libm, no run-time SIMD dispatch). **H3,** no bar: per
target and variant, the largest difference in cents from numpy's
`float64` on frames where both chose the same lag, and the counts of
frames whose decisions differ: a period found or not, the lag chosen,
`metrics`' acceptance (inside E2 to C6 widened by 3 cents, and
aperiodicity under 0.02, MT-003). No earlier rate exists for noisy or
real input, so no bar is set (C13).

**Checks (S15; C1, C3, C5, C10, C14 to C18 applied).** Inputs: each
fixture's hash (must fail: one byte changed); each tone's f0 inside E2
to C6, its peak 0.5 and its SNR read from the output, not the parameter;
every input `float32` and finite; `r7_inputs.py`'s lag-returning copy of
`yin.yin` equal to it bit for bit on every input (must fail: one input
against another). Analysis, every check before any outcome: every output
present and well formed (must fail: one value dropped); `compare` gives
0 on the reference against itself, 1 cent within float64's rounding
(`CENTS_F64_TOL`, from its definition) when every f0 is raised by 1 cent,
and one found mismatch when one frame is made NaN; `same_bits` detects a
one-ulp change; the Rust port chooses `yin.py`'s lag on every fixture
frame in both `f64` variants natively (must fail: one fixture against
another).

**Run:** `uv run python r7_inputs.py <squillo>`, `./r7_build.sh`,
`wasm/target/release/native`, `node r7_run.mjs`, `uv run python
r7_analyse.py` -> `results/r7.json`. **Estimate (S19),**
committed before the full run: a sample of six inputs spread over the
conditions (silence, C7 out of range, E2 pure, `saw12` at 10 dB on C6 and
at 20 dB, one VocalSet take; 13.27 s of audio) ran to its end in every
target: native 0.88 s for all four variants, each browser build 1.3 to
2.0 s. The full run is 350.9 s of audio, 26.4 times the sample: native
about 25 s, each of the four browser builds about 55 s with launch, the
inputs step 19 s (run), and the analysis, vectorised per input over
195 inputs and 22 outputs, under a minute.

**Revision 1** (`r7_analyse.py`, committed before the second run): the
first analysis passed every check and stopped on `json.dumps` of a numpy
bool before writing or printing any outcome, as round 6's revision 1
did; numpy scalars are now written as Python values. No rule changed.

**Checks, their numbers.** Inputs: 11 fixture hashes equal to
`MANIFEST.md`'s (each must-fail detected); 164 tones inside E2 to C6,
peak 0.5, SNR as set; the lag-returning copy equal to `yin.yin` bit for
bit on all 195 inputs in both arithmetics (86 536 frames; must-fail
detected). Analysis: all nine checks true (`results/r7.json` `checks`),
among them the Rust port choosing `yin.py`'s lag on every frame of the
eleven fixtures in both `f64` variants. `tools/checkkeys.py`: 0 flags on
each script alone before its first run; with `results/r7.json`, 2 on
`r7_analyse.py`, read by hand: `inputs_checks` is the container that
carries `r7_inputs.py`'s checks, and `reference_must_fail_detected` is
asserted in `r7_inputs.py` (line 202) before it is set. With the results,
`r7_inputs.py` is flagged for `r7_analyse.py`'s keys, which it does not
hold.
The check `checkkeys.py` gained after this round (squillo L-066) flags
`r7_inputs.py`'s `json.dumps` of `sets.json` (line 211), which has no
`default=`; that write completed, and the script is left as it ran.
The check `checkkeys.py` gained after this round (squillo L-066) flags
`r7_inputs.py`'s `json.dumps` of `sets.json` (line 211), which has no
`default=`; that write completed, and the script is left as it ran.

**Result** (`results/r7.json`; 195 inputs, 350.9 s of audio, **43 268
frames**: fixtures 1342, tones 20 008, VocalSet 21 918; 38 015 of them
with a period found by both sides; Rust 1.98.1, wasm-bindgen 0.2.129,
Chrome 154.0.8037.57, Firefox 156.0, numpy 2.5.3, one i7-12700H; maxima
are observed maxima over these frames, not bounds).

| # | Question | Result (conditions; uncertainty) |
| :--- | :--- | :--- |
| H1 | Chrome against Firefox, same build and variant | **Holds**, 8 of 8 (two builds, four variants): bit-identical f0, aperiodicity and lag on every frame |
| H2 | Direct variants, each browser build against native | **Holds**, 8 of 8: bit-identical. Beyond H2, the four WASM builds (plain and `simd128`, both browsers) are bit-identical to one another in all four variants, the FFT ones included; only the FFT variants differ between native and WASM (`identical_pairs`) |
| H3 | Largest difference from numpy `float64`, frames with the same lag, every target | `f64-direct` **3.6 × 10⁻¹¹ cents**; `f64-fft` **1.8 × 10⁻¹⁰**; `f32-direct` **0.0058** (p99 0.00017); `f32-fft` **0.0671** in WASM (p99 0.0021) and **0.0417** native (p99 0.0020); numpy `float32` 0.0667 (p99 0.0021). The largest are on the synthetic tones; on VocalSet `f32-fft` reaches 0.0054 (WASM) and `f32-direct` 0.0014 |
| H3 | Decisions | **None differ**, in any target or variant: 0 of 43 268 frames with a period found on one side only, 0 with another lag, 0 with `metrics`' acceptance changed (range widened by 3 cents, aperiodicity under 0.02) |
| H3 | Aperiodicity | Largest difference from numpy `float64`: 1.9 × 10⁻⁶ in `f32`, 5.7 × 10⁻¹⁵ in `f64`, against MT-003's refusal at 0.02 |
| X | Across targets, same variant: each WASM build against native | `direct`: 0 (identical). `f64-fft`: 1.1 × 10⁻¹⁰ cents. `f32-fft`: **0.0595 cents**, aperiodicity 3.6 × 10⁻⁷; no decision differs |
| T | Cost, seconds per second of audio, one thread | `direct`: native 0.030 to 0.031, WASM 0.034 to 0.036. `fft`: native 0.0019 (`f32`) and 0.0024 (`f64`); WASM `simd128` 0.0032 to 0.0034 (`f32`) and 0.0046 (`f64`); WASM plain 0.0064 to 0.0125 (`f32`) and 0.0095 to 0.0195 (`f64`) |

**What this says for squillo.** ADR 0007's numeric epsilon is a
property of the arithmetic and of how the difference function is
computed, not of the browser: one WASM module gives the same bits in
Chrome and Firefox, plain or `simd128`, and the direct sum gives the
same bits natively too. Against `float64`, the largest pitch difference
is 0.0671 cents, in `float32` by FFT, inside SG-005's ±3 cents, and
the host's 0.0082 (result 9), measured on clean tones, was not the
worst case: the noisy tones gave the larger. No frame's decision changed in 43 268, but
that is a count, not a guarantee: a frame whose CMND or aperiodicity
lies nearer 0.1 or 0.02 than the differences measured (1.9 × 10⁻⁶ in
`float32`) can flip. The
fold is squillo's (iteration 93): ADR 0007's *Numeric epsilon* records
these numbers, and SG-005's measurement tolerance stays apart from them.

**Limits.** One machine (x86-64, i7-12700H) and one browser version
each; no ARM device and no mobile browser, so a native ARM build with
fused multiply-add was not measured. One implementation per variant:
another FFT library or summation order gives another `float32`
difference, of the same kind but not these exact numbers. Inputs at 48
kHz `float32`; noise is white.

### Beyond round 3

Amateur voices and other vowels (E-005's `needs-human` step); a real room
(E-003's); the ring ratio on repeated material (F-036, round 4: separate takes of one scale, the `needs-human` step above); a reverberation
estimate of another kind (spectral smearing of the partials, or a blind
RT60 method with its own evidence) if squillo ever needs detection rather
than a stated condition.
