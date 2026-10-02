# E-005 — Intent inference: pitch accuracy without a reference

**Status:** needs-human (round 1 folded into squillo `metrics`, iteration 27; round 2 done, squillo iteration 31; round 3, per-note centre and aim, squillo iteration 59; one `needs-human` step) · **Serves:** VISION §3 (every song is your cover; the next step), §4.3, §5 (reference-free), §6, §12.4

## Question

Squillo never compares a singer with an original. For pitch accuracy it must
infer **the note the singer was aiming for** from the take itself. How reliably
can that be done, and how is the uncertainty of the inference carried into the
accuracy score honestly?

## Hypothesis

For most phrases, the intended notes can be inferred from a key or scale
estimate plus where the voice settles within each note, so that a note sung
sharp or flat by a few tens of cents is attributed to the right target.
Inference fails on deliberate blue notes, glides and non-Western tunings, and
must then say "intent uncertain" rather than score.

## Protocol

1. **Ground truth by construction:** synthesized sung phrases with known
   intended notes, then rendered with controlled errors (offsets, drift, scoops,
   vibrato), in several keys and scales.
2. **Real voices:** openly licensed sung datasets with note annotations, public
   domain songs only.
3. Candidate inference methods: nearest equal-tempered note; key or scale
   estimate, then nearest scale note; note segmentation plus per-note settling
   pitch; combinations.
4. Report attribution accuracy per error size and condition, and test how the
   inference's own uncertainty should widen the accuracy score's ±.

## Round 1 (squillo iteration 21)

```
uv run python run.py synth     # 600 synthetic phrases, about 2 min on 18 processes
uv run python fetch.py $(cat data/vocalset-files.txt)
uv run python run.py real      # 77 VocalSet takes
E005_LOWPASS=4000 uv run python run.py real   # input check, below
uv run python report.py        # -> results/summary.json
uv run python check.py         # -> results/input_check.json
```

**Inputs.** *Synthetic:* 600 phrases of 14 notes, 0.25–0.8 s each, random
walks on a scale (major, natural minor, harmonic minor, major pentatonic,
and "blue": major with an intended ♭3 or ♭7 on 30 % of the 3rds and 7ths),
in a random key, sung by E-001's source-filter voice (`squillo-lab E-001 @
e43cdf7`, `voice.py`) in six voice types from bass to high soprano, all
notes inside ADR 0007's E2–C6. Each note's intended pitch is 100·n + G + D(t):
G, the singer's own tuning, uniform in ±50 cents and **not an error** (an
unaccompanied singer picks their own reference); D a linear drift of that
reference, 0 or 60 cents end to end. Sung: intended + e (the per-note
error, normal with sd σ = 0, 10, 20, 30 or 40 cents) + a scoop from below on
half the notes (30–100 cents, 60 ms decay) + vibrato (none, or 5.5 Hz ±50
cents) + wobble (1–6 Hz, 10 cents RMS). Six phrases per cell of scale × σ ×
drift × vibrato. *Real:* VocalSet 1.1 (CC BY 4.0, not committed; `data/SOURCES.md`):
the C-major scale exercise on /a/, straight tone (19 singers) and molto
vibrato (20), and the traditional round "Row, row, row your boat" (public
domain), straight (19) and vibrato (19). Trained singers, studio recordings.

**Pitch.** E-002's YIN (`yin.py`, squillo-lab `afff13f`) at squillo's
frame axis (ADR 0007), threshold 0.1, E2–C6 widened by 3 cents, each frame's
instant 20 ms before its end (YIN's lag centre, E-002 result 5).

**Inference** (`infer.py`), reference-free: nothing but the take.
1. *Segmentation:* voiced runs (gaps up to 3 frames bridged), a 200 ms
   running median, quantised to semitones on a provisional reference, runs
   under 64 ms merged into a neighbour (`est`). For comparison, true note
   boundaries (`oracle`): known by construction, or from aligning the take
   to its score (VocalSet).
2. *Settle pitch:* median of the frames from 30 % to 90 % of the segment.
3. *Reference* r: `fixed` (A4 = 440 Hz); `global` (duration-weighted
   circular mean of the settle pitches modulo 100 cents); `local` (the same,
   also weighted by a 2 s Gaussian in time, unwrapped).
4. *Target:* `chromatic` (nearest semitone on r); `key` (nearest member of
   the best-fitting diatonic or harmonic-minor set over a 2 s Gaussian
   window); `hybrid` (chromatic if within 25 cents of a semitone or if the
   semitone is in the key, otherwise key).
5. *Deviation* = settle − target. Standard uncertainty: the settle
   median's (1.2533 sd / √n_eff, one effective sample per 0.1 s, an assumed
   correlation time) combined with 1 cent for the tracker (E-002) and, for
   the absolute case, the reference's (sd of deviations / √n_eff over notes).
6. *Phrase spread* σ̂: the wrapped-normal spread of the deviations on the
   100-cent circle, from the duration-weighted mean resultant length,
   bias-corrected for the effective count. It does not depend on which
   semitone a note was given, so misattribution cannot shrink it. "Not
   above chance" when the corrected resultant length is ≤ 0.
7. *Per-note posterior* that the attributed semitone is the aimed one,
   under wrapped-normal errors of spread σ̂; a note is **flagged** unsure
   when it is below 0.95.

**Measures.** *Attribution:* a note is right when its inferred semitone
minus its intended one equals the phrase's modal difference (transposition
is not an error); a note is called by the segment holding most of its
settle-window frames; notes with no segment count as wrong. *Deviation
error:* for rightly attributed notes, deviation minus the true error
relative to the singer's duration-weighted mean (`e − ē`, plus `D − D̄`
under a global reference; drift is absorbed by a local one). Intervals are
95 %: Wilson for shares, bootstrap over takes for medians and p95s.
VocalSet truth: dynamic time warping of the 200 ms running median against
the score, transposition searched in 25-cent steps; 1.7 % of frames (median
over takes) lie more than 100 cents from their aligned note, and every take
aligned. Python 3.13.14, numpy 2.5.3, scipy 1.18.1, soundfile 0.14.0.

**Input check** (squillo standing instruction S15). The measure is pitch,
not a spectral distance. One-third-octave long-term spectrum relative to its
strongest band (`results/input_check.json`): synthetic inside VocalSet's
range ± 3 dB at 250 Hz, 1, 2 and 4 kHz; outside at 500 Hz (synthetic −15 to
−19 dB, VocalSet −5.6 to 0) and at 8 and 16 kHz (synthetic 6 to 23 dB darker).
So the VocalSet takes were re-run low-passed at 4 kHz (8th-order
Butterworth), where both have energy: attribution with `est/global/chromatic`
84.1 % → 84.0 % overall, straight scales and round unchanged, vibrato takes
within 1.8 points, inside their intervals; phrase spread within 2.0 cents.
YIN finds 95.6 % of synthetic frames voiced (median) against 83.7 % of
VocalSet frames; median CMND dip 0.002 against 0.0034.

**Results.** Numbers for `est` segmentation unless marked; all in
`results/summary.json`.

| # | Question | Result |
| :--- | :--- | :--- |
| 1 | How often is the aimed-for note found? Synthetic, `global/chromatic` | σ = 0: 99.9 % (99.7–100); 10: 98.9 % (98.2–99.3); 20: 92.3 % (90.9–93.5); 30: 81.4 % (79.4–83.2); 40: 71.3 % (69.0–73.4); 1680 notes each. By the note's own error: \|e\| < 20 cents 98.6 %, 20–35 89.9 %, 35–50 69.4 %, 50–75 40.7 %, ≥ 75 10.3 %. The ceiling is set by the 50-cent boundary: a normal error stays inside it with probability 98.8, 90.4 and 78.9 % at σ = 20, 30, 40, and the reference's own error costs a further 6–9 points. Oracle segmentation adds 0.1–1.3 points |
| 2 | Does the reference matter? | Yes. A fixed A4 = 440 Hz finds 88.3 % at σ = 0 (86.7–89.8), because a singer's own tuning lies anywhere in ±50 cents; the singer's own reference (`global`) 99.9 %. `local` equals `global` within the intervals (drift 60 cents: 87.6 against 86.8 %) |
| 3 | Does a key or scale help? | Little, and it costs honesty. `key` gains 1.9 points at σ = 20, 3.6 at 30, 3.5 at 40, and loses 0.5 at σ = 0; on intended blue notes it finds 64.3 % (53.6–73.7, 84 notes) against 94.0 % (86.8–97.4) for `chromatic`. `hybrid` finds 85.7 % of blue notes and gains 2.3–3.1 points at σ ≥ 20. Scale type otherwise does not matter: all five within 87.6–89.9 %, overlapping intervals |
| 4 | Real voices (VocalSet, trained singers), `global/chromatic` | Straight scales 95.0 % (92.1–96.9, 323 notes), straight round 92.8 % (89.3–95.2, 304); molto vibrato scales 75.0 % (70.1–79.3, 340), vibrato round 74.0 % (68.8–78.6, 304). With the score's boundaries: 96.3, 94.4, 86.8, 78.6 %. Misattributions are mostly ±1 semitone, the note landing 30–50 cents from its neighbour relative to the singer's own reference, spread over the whole score (not one misread score note); the tracker reads 5 notes an octave or more off, in three takes (a countertenor's two, one baritone's); under vibrato the settle window holds under two vibrato cycles. Median \|deviation\| of rightly attributed notes: straight 10.4 cents (scales, 8.1–11.7) and 10.4 (round, 8.7–12.5); vibrato 13.3 and 12.7 |
| 5 | Can the take's intonation spread be measured without attributing notes? | Yes, up to a spread of about 20 cents on 14 notes. σ̂ − true spread, synthetic, no drift, straight: σ = 0: +2.3 (p5–p95 1.1 to 3.7); 10: +0.3 (−1.7 to 2.2); 20: +1.1 (−3.6 to 10.1); 30: −1.5 (−12.6 to 6.5), with 13 of 30 phrases not above chance; 40: −18.4 (−29.5 to −0.4), 21 of 30 not above chance. Vibrato adds +6.7 at σ = 0. Real: straight scales σ̂ median 15.7 cents (p10–p90 12.8–23.0), straight round 17.1 (11.6–25.4); molto vibrato scales 31.2, 8 of 20 takes not above chance; vibrato round 26.5, 3 of 19 |
| 6 | Does the inference know when it is unsure? | Per phrase, yes: σ̂ not above chance is the take saying "intent uncertain" (§6). Per note, only while the spread is small. Flagged at posterior < 0.95, synthetic: σ = 0: 3.9 % flagged, 0.0 % wrong among the rest (≤ 0.24); 10: 8.0 %, 0.19 % (0.07–0.57); 20: 40 %, 2.4 % (1.6–3.5); 30: 58 %, 11.3 %; 40: 64 %, 22.6 %. A note sung more than 50 cents off is attributed to its neighbour with a small deviation and looks sure; no per-note rule sees it. Real straight scales: 3.4 % flagged, yet 4.2 % (2.5–7.0) wrong among the rest: the real tail is heavier than a wrapped normal of spread σ̂ |
| 7 | Does the deviation's ± hold? | Only with the reference's uncertainty in it, and only for small spreads. Coverage at k = 2, synthetic, straight, no drift: σ = 0: 97.1 %; 10: 91.0 %; 20: 78.3 %; 30: 61.1 %; 40: 45.5 %. Without the reference's term, 96.9, 83.1, 66.4, 28.6, 22.4 %. With vibrato 99.8 to 82.2 % (the settle's own spread is larger). Deviation error, σ = 0 straight: median 0.85 cents, p95 5.8 |
| 8 | Does a phrase score flatter? | The duration-weighted RMS deviation of attributed notes does, beyond 20 cents: minus the true RMS, median −0.1 at σ = 10, −0.5 at 20, −6.1 at 30 (p5–p95 −14.5 to −1.3), −13.8 at 40 (−30.5 to −3.8), because misattributed notes read as small errors. At σ = 0 it overstates by 3.5 (the wobble and settle noise) |

**What this says for squillo.**

- VISION §12.4 is answerable, within a stated range. Reference-free pitch
  accuracy works when it is measured **against the singer's own tuning**,
  not against A4 = 440 Hz, and **by nearest semitone**, not by snapping to a
  guessed key: a key gains a few points only where the take is too spread
  to score anyway, and it rewrites intended blue notes.
- **What is measurable:** a note sung up to about 20 to 35 cents off its
  aim, in a take whose note-to-note spread is at most about 20 cents on 14
  notes. There, 98.9 % or more of notes are found at σ ≤ 10 and 92 % at
  σ = 20, and the spread σ̂ is within a few cents of the truth.
- **What is not:** a note more than 50 cents off. Without a reference it is
  indistinguishable from its neighbour sung the other way. Squillo must
  never report a large error as a small one: the phrase-level spread σ̂ is
  the honest summary, because misattribution cannot shrink it, while an RMS
  of per-note deviations flatters by 6 to 14 cents at σ = 30 to 40.
- **Saying so** (§6): a take whose σ̂ is not above chance says "intent
  uncertain". Trained singers' straight takes never did; molto-vibrato takes
  did in 11 of 39.
- A global uniform sharpness of the whole take is **invisible** without a
  reference; it is the singer's tuning. Drift of that tuning is an error
  under a global reference and invisible under a local one; which one the
  dashboard shows is a decision for `metrics` and `coach`.
- The per-note ± is not yet honest beyond σ = 10 (question 7), and the
  per-note flag misses real voices' heavier tail (question 6). A spec must
  not rely on either until round 2.

**Limits.** Synthetic voices are E-001's, darker above 8 kHz and weaker at
500 Hz than VocalSet's (checked above). Errors are normal and independent
per note; real errors are heavier-tailed. VocalSet is trained singers in a
studio: no amateurs, no rooms, no browser. The VocalSet truth comes from
aligning to the score, not from note annotations. 14-note phrases: longer
takes narrow σ̂'s spread. Tempered 12-tone tunings only; non-Western
tunings and deliberate glides are not tested. Segmentation is crude and
untuned; vibrato hurts it most (75 % against 87 % with true boundaries).

**Round 2 (planned at round 1).** A settle estimate over whole vibrato cycles; a per-note ± whose reference term follows the circular estimate; a heavier-tailed flag fitted on VocalSet and checked on held-out singers; takes longer than 14 notes; a glide-aware segmentation. Done in squillo iteration 31 (below), except the glide-aware segmentation, which is left for a later round.

## Fold into squillo `metrics` (squillo iteration 27)

```
uv run python fold.py coverage            # 2400 phrases, 10.6 min on 18 processes -> results/fold.json
uv run python fold.py fixtures <dir>      # squillo's four fixtures/metrics/ takes, checked
```

**Question.** Round 1 found the take's spread σ̂ honest "to about 20
cents" but gave it no ±. Which standard uncertainty makes σ̂ ± 2u cover the
singer's intonation spread, and where does it stop holding?

**Measurand.** The singer's intonation spread: the standard deviation of
their note-centre errors relative to their own tuning, √(σ² + var *D*),
with σ the generating per-note sd and *D* the drift of their tuning at the
notes (a global reference counts drift as error). Also checked against the
take's realised spread (round 1's truth).

**Inputs.** Round 1's design (`synth.py`, unchanged) with four new seed
sets, 2400 phrases, 120 per cell of σ × drift × vibrato; `est`
segmentation, `global` reference, `chromatic` target, notes ≥ 0.1 s.
S15: every note centre lies inside ADR 0007's E2–C6 (−2900 to +1500 cents
re A4): extremes −2784.7 and +1293.5, 0 of 2400 phrases outside. (The
first version of this check compared with +300 cents, an error in the
bound, not the inputs; found by reading the output, corrected before any
result was used.)

**Candidates**, at coverage factor k = 2:
A, sampling only, GUM (JCGM 100:2008) E.4.3: *u*² = σ̂² / (2(*n*ₑ − 1)),
*n*ₑ the duration-weighted effective note count; B, A combined with the
notes' duration-weighted mean settle variance (`infer.settle`'s *u*, which
holds 1 cent for the tracker); C, A combined with √3 cents in place of B's
settle term.

**Results** (`results/fold.json`, `coverage`). Wilson 95 % intervals.

| # | Question | Result |
| :--- | :--- | :--- |
| F1 | Which candidate covers? | B, while the true spread is ≤ 20 cents: every cell 97.2–100 % (lower bounds ≥ 92.2), with and without drift or vibrato; the σ = 20 cell with drift and no vibrato, whose true spread is a median 26.1 cents, 97.1 % (90.0) (corrected at squillo R-06, iteration 30: the first write-up put that cell under ≤ 20). A fails at σ = 0 (0.8 %: it ignores reading noise); C fails under vibrato at σ = 0 (5.8 %). At σ ≥ 30 without vibrato every candidate fails (B 44.9–87.9 %), always on the **low** side: σ̂ saturates near 25 cents (median 24.3–25.9 at σ = 30 and 40) |
| F2 | Where does σ̂ ± 2u_B hold, by the reported value? | σ̂ ≤ 10 cents: 342 of 342 phrases covered (98.9–100 %); without vibrato 100 % (97.9–100, 181), with 100 % (97.7–100, 161). Above 10 cents, without vibrato, it fails: 91.8 % at 10–12.5 (49), 85.3 % at 12.5–15 (34), 82.4 % at 20–25 (222) |
| F3 | Is the lower end honest everywhere? | Yes. σ̂ − 2u_B exceeds the true spread in 1 of 1775 reported phrases (99.9 % honest, 99.7–100); among σ̂ > 10, 1432 of 1433 (99.6–100) |
| F4 | What does a singer get? | σ ≤ 10, no drift: mostly *measured*. σ = 0: 238 measured, 236 *at least*, 6 *intent uncertain*; σ = 10: 102, 334, 44; σ = 20: 2, 367, 111; σ = 30: 0, 262, 218; σ = 40: 0, 234, 246 (of 480 each). *u_B* median 3.65 cents without vibrato, 19.2 with (the settle window holds under two vibrato cycles; round 2) |

So squillo can state three things honestly: σ̂ ± 2u_B when σ̂ ≤ 10 cents;
only "at least σ̂ − 2u_B" when σ̂ > 10; "intent uncertain" when σ̂ is not
above chance. Synthetic only (round 1's limits apply); real voices'
heavier tail is untested here.

**Fixtures** (`results/fold.json`, `fixtures`). Four takes for squillo's
`fixtures/metrics/`, by the formula squillo's MANIFEST records: 14 sines,
*A* = 0.5, the A-major scale from A3 up to A4 and back, on a tuning 23 cents
above A4 = 440 Hz, each 0.4 s with 10 ms raised-cosine ramps after 0.1 s of
silence, 0.1 s of silence at the end; 340 800 `f32` samples. Asserted: every
note in E2–C6 (217.04 to 447.82 Hz), deviations of mean 0 inside ±50 cents,
peak ≤ 0.5, every gap exactly zero. Byte-identical on two runs (CPython
3.13.14, glibc 2.43). E-002's YIN: every frame whose window lies inside a
note's unramped part within 0.01 cents of the note; every note found, settle
within 0.003 cents.

| Fixture | Deviations | σ̂ | *u_B* | State | Check |
| :--- | :--- | ---: | ---: | :--- | :--- |
| `take-in-tune.wav` | none | 0.001 | 1.000 | measured | ± 2u contains 0 |
| `take-spread-5c.wav` | sd 5 exactly | 5.223 | 1.432 | measured | contains 5, excludes 0 |
| `take-drift-60c.wav` | −30 to +30 linear, sd 18.605 | 22.374 | 4.501 | at least | lower end 13.37, in (0, 18.605] |
| `take-uncertain.wav` | evenly round the circle | — | — | intent uncertain | not above chance |

Improvement, `take-spread-5c` then `take-in-tune`: difference 5.222 cents,
2√(*u*₁² + *u*₂²) = 3.492, so improved.

## Round 2 (squillo iteration 31)

```
uv run python round2.py check      # the checks, each checked (S15), 1.5 min -> results/round2_checks.json
uv run python round2_amp.py        # the vibrato gate, 22 s -> results/round2_amp.json
uv run python round2.py synth      # 5040 phrases, 66 min on 18 processes -> data/cache/r2_synth.pkl
uv run python round2.py real       # 77 VocalSet takes and 40 E-002 re-syntheses, 11 s
uv run python round2.py report     # -> results/round2.json
```

Timing (S19): one phrase takes 4.3 s at 14 notes and 29.0 s at 56 on one
process with the machine loaded, so 1680 phrases per length on 18
processes (28 notes taken as 12 s, between the two) estimate 70 minutes;
the run took 66.

**Questions** (squillo R-06; F-032, ADR 0015's and ADR 0005's deferrals).
Q1: does a note centre over whole vibrato cycles shrink the ± under
vibrato? Q2: can the take's spread σ̂ show a measured value, with an
honest ± 2*u*, above the fold's 10 cents, with longer takes? Q3: how often
does an improvement test call a change that is not there, and how often
does it see one that is? Q4: may a library phrase's known melody inform
the intent? Q5: are the per-note ± and flag honest yet?

**Inputs.** *Synthetic:* round 1's generator with 14, 28 and 56 notes,
σ = 0, 10, 15, 20, 25, 30, 40 cents, straight or 5.5 Hz ±50-cent vibrato,
no drift (the fold covered drift), 120 phrases per cell, 5040 in all
(`round2.phrase`). The lowest note is kept at least 25 semitones below A4
so that tuning, error, scoop, vibrato and wobble stay above E2. *Real:*
round 1's 77 VocalSet takes (trained singers, CC BY 4.0, not committed),
and 40 of E-002 round 2's WORLD re-syntheses of VocalSet takes (20 straight
scales, 20 vibrato rounds; `squillo-lab E-002 @ e7d2bf4`), whose f0 is
known, so their true spread is known. *Truth:* for synthetic phrases, the
population σ and the realised spread: the sung contour at each frame's
instant, each note's centre by the same settle rule over the true
boundaries, the duration-weighted SD about the singer's weighted-mean
tuning. For the re-syntheses, the same on the known f0 aligned to the score
by dynamic time warping. Python 3.13.14, numpy 2.5.3, scipy 1.18.1.

**Candidates.** *Settle:* `med`, round 1's median over 30–90 % of the
note; `cyc`, the mean over the largest whole number of cycles of the
fitted vibrato rate (3.5–8 Hz, least squares), used where the fitted
amplitude is at least 25 cents, frames more than 200 cents from the
window's median dropped as f0 glitches (E-002 result 21: vibrato extent
p95 110.5 cents), otherwise the median. The 25-cent gate
(`results/round2_amp.json`): VocalSet straight notes' fitted amplitude p75
22.8 cents, vibrato notes' p25 41.8, so 19.9 % of straight and 86.9 % of
vibrato notes (of 604 and 579) take the cycle mean; synthetic 0.0 % and
84.9 %. *u of σ̂:* B, the fold's (GUM E.4.3 sampling ⊕ the notes' settle
*u*); D, a delta-method *u* for the circular estimator ⊕ settle; N, a
Neyman interval by simulation from the take's own weights and settle *u*s.
*When σ̂ is shown as measured:* S10, squillo MT-007 (σ̂ ≤ 10); U*n*, when
the upper end σ̂ + 2*u*_B ≤ *n* cents, *n* = 20 to 35; otherwise only the
lower end σ̂ − 2*u*_B, as MT-007. *Improvement tests* (+1 better, −1 worse):
B, MT-008 as specified (both measured under S10, difference beyond
2√(*u*₁² + *u*₂²)); R*rule*, MT-008's form where both are measured under the
rule, else the better take measured with its upper end below the other's
lower end; D, N; K, MT-008's form on the known-melody spread. *Known
melody* (Q4): the take aligned to the phrase's notes by dynamic time
warping (transposition searched on the take's own circular reference), each
note's centre by `cyc`, deviations from the written notes about the
singer's weighted-mean tuning, a linear SD with no 50-cent wrap, *u* = B;
a note more than 150 cents from its aim (on the weighted-median tuning) is
counted apart as a wrong note, never folded into the spread. *Per note*
(Q5): the reference's *u* from the circular estimate (delta method); a flag
whose posterior mixes a uniform share π of any semitone into round 1's
wrapped normal, π fitted by maximum likelihood on half the VocalSet
singers and tested on the other half.

**Checks** (squillo S15; `results/round2_checks.json`), each run on a case
it must pass and one it must fail:

| Check | Criterion, from its definition | Must pass | Must fail |
| :--- | :--- | :--- | :--- |
| Generator: every sounding sample in E2–C6 | ADR 0007's semitones, −2900 to +1500 cents re A4 | 56-note high soprano at σ = 40 with vibrato: −1330.6 to +485.6; all 5040 phrases −2712.6 to +1349.0 | The same shifted +1500 cents raises |
| Known f0 matched to frames by YIN's index | Half a frame's glide at 1200 cents/s, 4.8 cents | Median 3.2 cents | Shifted one frame: 12.8 |
| Whole-cycle centre on a known sinusoid, 0.2–0.6 s windows | Half a frame of phase left over at each end, *A* sin(π*f h*)/π = 2.19 cents | Max error 0.59 | Round 1's median: 20.4 |
| Interval machinery on the model alone (14 and 56 notes, σ 0–30) | N covers ≥ 92 % in every cell | 93.5–98.5 % | N told *u* = 0 when settle noise is 15 cents: 0 % |
| Truth procedures, one input of every condition | Every note and score state found | Synthetic, 3 lengths × 2: every state and note found, realised spread at σ = 0 is 2.4–5.3 cents (the wobble) | — (E-002 re-synthesis: straight scale 17 of 17 states; vibrato round 15 of 16) |

**R-07 (squillo iteration 35) on the last row.** One of the five checks
falls short of the heading: the truth procedures have no must-fail case. On
one input of every condition, their own criterion fails once: the E-002
re-synthesis of the vibrato round finds 15 of its 16 score states (DTW off
on 6.8 % of frames, against 0.7 % on the straight scale;
`round2_checks.json`, `c5_truth_procedures`). The vibrato round's results
(R5, real vibrato *u*_B 70.5 → 32.9) therefore rest on a truth that
misses one state in the input checked. The loss has not been measured,
and squillo's fold of this round (F-033) re-checks it before use.

The first two criteria were typed at first (3 cents and 0.5 cent) and
failed on their must-pass cases; each was replaced by the bound its
definition gives before any result was used (squillo L-033).

**Results** (`results/round2.json`; Wilson 95 % intervals; `cyc` unless
marked).

| # | Question | Result |
| :--- | :--- | :--- |
| R1 | Does a centre over whole vibrato cycles shrink the ±? | Yes, under vibrato, and nothing changes without it: *u*_B 2.6 to 2.8 times smaller synthetic and 2.1 times re-synthesized real (squillo iteration 43 replaced "about threefold"). Synthetic, σ = 0 with vibrato: median settle *u* 19.1 → 6.8 cents (14 notes), 18.4 → 7.0 (56); *u*_B 19.2 → 7.0. Straight phrases identical (no note passes the gate). Re-synthesized VocalSet vibrato rounds: *u*_B median 70.5 → 32.9 cents, still covering 15 of 15; straight scales 14.8 → 11.1, 20 of 20. VocalSet originals, *u*_B median: scales straight 15.1 → 10.8, round straight 19.3 → 12.8, scales vibrato 64.8 → 31.8, round vibrato 50.0 → 31.2. Measured share at σ = 10, vibrato, 56 notes: 24 → 50 of 120 |
| R2 | Is σ̂ ± 2*u*_B honest above 10 cents? | Yes, while the true spread is at most 25 cents; above that σ̂ saturates (median 23.5–31.5 at σ = 40) and only its lower end holds. Against the realised spread, B covers 98.6–100 % in every cell with σ ≤ 25 (all lengths, with and without vibrato); at σ = 30, 87.7–100 %; at σ = 40, 58.2–96.7 %. The lower end σ̂ − 2*u*_B holds in 4441 of 4441 reported phrases (99.9–100); 599 say *intent uncertain*. D equals B within 1 point; N misses at σ = 0 (41.7–81.7 % without vibrato, because its model leaves out the wobble) and is dropped |
| R3 | Where may σ̂ be shown as measured? | **When its upper end σ̂ + 2*u*_B is at most 25 cents** (U25). Judged per true σ, where no prior over singers enters: the shown statement excludes the truth in at most 1.7 % of phrases in the worst cell (0.5–5.9; 14 notes, straight, σ = 20 and 25), 0 % in most. U30 fails that: 5.0 % (2.3–10.5; the same, σ = 30). Pooled over the design's σ grid, U25's measured values cover σ in 99.3 % of 898 straight (98.5–99.7) and 99.8 % of 523 vibrato phrases (98.9–100); the 308 straight and 58 vibrato phrases measured above 10 cents cover their realised spread in 99.7 % (98.2–99.9) and 100 % (93.8–100). Measured values reach σ̂ = 17.6 cents. S10 (MT-007 today) is also honest, and measures fewer (590 against 898 straight phrases). Drift is not in round 2's inputs |
| R4 | Do longer takes help? | Less than hoped: the settle term is most of *u*_B. At σ = 20, straight, median *u*_B 6.8 (14 notes), 5.9 (28), 5.8 (56). They do cut *intent uncertain*: at σ = 30, straight, 55, 45 and 19 of 120 |
| R5 | On real takes? | Trained singers' straight takes are still shown only as a lower end, because the notes' settle *u* makes up a median 92 % of *u*_B². Re-synthesized straight scales: true spread median 18.3 cents; σ̂ − truth p5 to p95 −10.6 to +3.7; \|σ̂ − truth\| / *u*_B p95 0.84, max 1.41, so *u*_B is about twice what coverage needs on these takes. Under U25 no real take is measured (upper ends from 25 cents up); under U30 two straight scales. VocalSet originals: σ̂ median 16.8 (scales straight), 17.3 (round straight), 21.8 and 25.1 with vibrato |
| R6 | Does an improvement test call changes that are not there? | No. On pairs of phrases from the same cell, every test's false-change rate is 0 to 0.7 % in every length and vibrato condition (420 pairs each), and the test squillo MT-008 takes (`RU25`) calls 0 of 420 in each of the six; on the two halves of each VocalSet take, 0 of 77 for every test (0–4.8 %) |
| R7 | Does it see changes that are there? | MT-008 as specified never does: 0 % in every pair of cells, because a σ̂ ≤ 10 carries a *u*_B near 4 to 5 cents. With U25, straight, 20 → 0 cents: 24.2 % (14 notes), 28.3 % (28), 20.8 % (56); 40 → 10: 1.7 %, 10.0 %, 25.0 %; under vibrato 0 to 0.8 %. With the known melody (K), straight, 20 → 0: 55.0, 71.7, 67.5 %; 40 → 10: 44.2, 71.7, 80.0 %; vibrato 40 → 10: 20.0, 34.2, 36.7 %; never *worse* |
| R8 | May a library phrase's known melody inform intent? | Yes, and it removes the 50-cent wrap. With the notes known, the linear spread covers the realised spread in 99.2–100 % of phrases in every synthetic cell up to σ = 40 (*u*_B median 3.2–13.1 cents), and does not saturate (median 34.5–37.6 at σ = 40, against 23.5–31.5 wrapped). Re-synthesized VocalSet: 20 of 20 in each set, \|σ̂ − truth\| / *u*_B max 0.56 (straight scales) and 0.34 (vibrato rounds); σ̂ − truth p5 to p95 −5.9 to +2.0 and −2.8 to +21.6; every score state found in 17 of 20 and 10 of 20 takes; 12 of about 340 straight-scale notes more than 150 cents from their aim, counted apart as wrong notes. Real *u*_B stays large (median 11.4 cents straight, 54.8 vibrato rounds): the settle term again |
| R9 | Is the per-note ± honest yet? | No, beyond σ = 0. With the reference's *u* from the circular estimate, coverage at *k* = 2 of rightly attributed notes, straight: 97.7 % (σ = 0), 90.4 (10), 87.1 (20), 80.9 (30); round 1's term 97.7, 90.5, 86.4, 65.7 |
| R10 | Is a heavier-tailed per-note flag honest? | Not stably. π fitted on one half of the singers is 0.065, on the other 0.12. Tested on the other half, wrong among unflagged notes: 5.4 % (3.5–8.2) and 1.5 % (0.4–5.4), flagging 40.5 % and 77.9 % of notes (round 1's flag: 7.6 % and 4.8 %); straight takes 3.0 % and 1.9 %, vibrato 9.4 % and 0.0 %. The model's own prediction, 3.2 % and 4.3 %, misses the first half |

**What this says for squillo.**

- VISION §12.4 has its automated answer. Against the singer's own tuning,
  by nearest semitone, the take's spread σ̂ can be shown **measured, ±
  2*u*_B, whenever its upper end is at most 25 cents**, not only when σ̂ ≤
  10; above that, only its lower end; *intent uncertain* when not above
  chance. Checked per true spread up to 40 cents, 14 to 56 notes, straight
  and vibrato. The improvement test keeps MT-008's form, applied where both
  takes are measured, plus a one-sided form on honest ends.
- The **whole-cycle centre** should replace the median where a note has
  vibrato of at least 25 cents: it cuts *u*_B 2.1 to 2.8 times under vibrato
  and changes nothing without it.
- A library phrase's **known melody should inform intent**: the spread
  about the written notes, unwrapped, is honest to 40 cents and sees
  improvement two to three times as often as the wrapped spread. A note
  far from its written pitch is a wrong note, shown apart, never averaged
  in.
- On **real trained voices** the pitch-spread ± is still too wide to show a
  typical improvement: the notes' settle *u* (one effective sample per
  0.1 s, round 1's assumption) is most of it, and on the re-syntheses it is
  about twice what coverage needs. F-032 stands for pitch; a singer's
  progress rests first on steadiness and vibrato (E-002 round 2, F-031), as
  Joakim directed. Calibrating the settle *u* on E-002's re-syntheses is
  the lever for a later round.
- Per-note ± and flags stay out of the specs.

**Limits.** Synthetic voices are E-001's (round 1's checks apply); no drift
in round 2; errors normal per note. The real truth is WORLD re-syntheses of
trained singers in a studio, whose note centres are defined by the same
settle rule as the estimate: it tests the tracker, segmentation and
reference, not whether a centre is where the singer aimed. VocalSet's
vibrato round lost one score state in the truth alignment. No amateurs,
rooms or browsers. The 25-cent threshold is the largest tested (20, 25,
30, 35) that held in every cell; it is evidence, not a perceptual bound.

**Needs a human (15 minutes).** VocalSet's singers are trained; squillo's
first singer is not.

1. On any microphone in a quiet room, sing the traditional round "Row, row,
   row your boat" (public domain) once through, twice, at any pitch and
   pace, unaccompanied, no vibrato on purpose; save `row1.wav`, `row2.wav`
   (5 minutes).
2. `uv run python run.py own row1.wav row2.wav` writes `results/own.json`:
   notes, notes attributed right, σ̂, notes flagged, median |deviation|
   (1 minute).
3. Listen to each take once and write in `results/own.md` whether σ̂ and
   the flagged notes match what you hear (5 minutes).
4. Commit `results/own.json` and `results/own.md`, never the audio.

## Fold with MT-003's refusal (squillo iteration 38)

```
uv run python fold_refusal.py check           # the checks, each checked (S15), 30 s -> results/fold_refusal_checks.json
uv run python fold_refusal.py time_pool 72 18 # S19 under the pool itself
uv run python fold_refusal.py synth 60 8      # 2520 of round 2's phrases, 31 min on 8 processes -> data/cache/fr_synth.pkl
uv run python fold_refusal.py real            # 77 VocalSet originals, 40 E-002 re-syntheses, 6 s
uv run python fold_refusal.py report          # -> results/fold_refusal.json
uv run python fold_refusal.py fixtures <dir>  # squillo's fixtures/metrics/ takes -> results/fold_refusal_fixtures.json
```

**Question** (squillo F-033 (e), R-07). Squillo's `metrics` MT-003 makes a
frame unmeasurable when its aperiodicity (YIN's *d*′ at the chosen lag,
squillo SG-008) is 0.02 or more. Round 2 measured with every frame YIN
gave. Does round 2's rule hold with the refusal: σ̂ shown measured, ±
2*u*_B, when its upper end is at most 25 cents (U25), its lower end
otherwise, with the note centre over whole vibrato cycles (`cyc`)? Does the
improvement test (MT-008's form where both are measured, the one-sided
form on honest ends otherwise) still call no change that is not there?

**Bar, written before the run** (S15, L-036): in every cell of round 2's
design (length × vibrato × σ), the shown statement excludes the singer's
spread (the population σ, round 2's R3 truth) in at most 5 % of phrases,
the share a *k* = 2 interval claims (GUM 6.3.3).

**Inputs.** Round 2's generator and seeds, unchanged (`round2.phrase`,
`round2.jobs_synth`); the first 60 of each cell's 120 phrases, 2520 in all
(the design cut before the run, S19, below). Each phrase tracked once;
`off` measures with every frame YIN gives (round 2), `on` with the refusal.
Real: round 2's 77 VocalSet originals and 40 E-002 re-syntheses, their
truth read from round 2's cache (`r2_real.pkl`), unchanged by the refusal.
Python 3.13.14, numpy 2.5.3, scipy 1.18.1.

**Timing (S19).** One 56-note vibrato phrase took 4.0–5.1 s on one idle
process, and the estimate from it, 12 minutes for 5040 phrases on 18
processes, was wrong by more than four times: the first run was stopped
by its own 50-minute time limit with nothing saved (squillo L-037). Timed
under the pool itself (`time_pool`), the machine gives 0.77 s (6
processes), 0.86 (12) and 0.87 (18) of wall time per phrase, whatever the
count: `voice.render` is bound by memory, not cores. 5040 phrases would
take 65 minutes, so the design was cut to 60 per cell, estimated at 33
minutes; it took 31, saving every 100 phrases.

**Checks** (`results/fold_refusal_checks.json`), each run on a case it
must pass and one it must fail:

| Check | Must pass | Must fail |
| :--- | :--- | :--- |
| The pipeline without the refusal reproduces round 2's cached `cyc` σ̂ and *u*_B, within 10⁻⁹ | One phrase per cell at 14 and 56 notes: 28 of 28; the whole run: 2520 of 2520 | The next cell's phrase: matched 0 of 28 |
| The refusal drops exactly the frames at *d*′ ≥ 0.02 | squillo's `tone-aperiodic.wav`: 13 refused, 109 measured (E-002 fold F5: 13 refused), every refused frame at *d*′ ≥ 0.02 and none kept; `sine-220hz.wav`: none refused | The threshold mistyped as 0.2: none refused on `tone-aperiodic.wav` |
| The bar | Round 2's cached values, U25: worst cell 1.7 % (0.5–5.9, 120; 14 notes, straight, σ = 20) | Round 2's cached values, U35: worst cell 10.0 % (5.8–16.7) |

**Results** (`results/fold_refusal.json`; Wilson 95 % intervals).

| # | Question | Result |
| :--- | :--- | :--- |
| FR1 | How many frames does the refusal take? | Synthetic: 4.6 % of the 5 272 599 frames YIN measured (3.6 % straight, 5.6 % with vibrato). Real: 10.4 % (VocalSet scales, straight) and 16.2 % (round, straight); 36.5 % and 39.2 % with vibrato; re-syntheses 11.5 % (scales) and 40.9 % (vibrato round) |
| FR2 | Does U25 still pass the bar? | Yes. With the refusal the worst cell excludes the spread in 3.3 % (2 of 60; 0.9–11.4; 14 notes, straight, σ = 20 and σ = 25), the same as without it on the same phrases; every other cell 0 of 60. Measured: 689 of 2520 phrases (726 without), covering σ in 99.4 % (98.5–99.8); 192 measured above 10 cents, the largest 17.64 |
| FR3 | Does the lower end hold? | Yes: 2192 of 2192 phrases that give one (99.8–100); without the refusal 2220 of 2220 |
| FR4 | False changes | None: 0 of 210 pairs of phrases from the same cell in each of the six length × vibrato conditions, with and without the refusal (0–1.8 % each); 0 of 77 halves of VocalSet originals |
| FR5 | Power, straight, 20 → 0 cents | 23.3 % (14 notes), 40.0 % (28), 18.3 % (56) with the refusal; 21.7, 35.0, 15.0 without. 40 → 10: 0, 11.7, 23.3 %. Under vibrato 0 in every case |
| FR6 | Real takes | Still no real take measured. *u*_B median with the refusal: 10.72 (scales, straight), 11.73 (round, straight), 25.9 and 25.6 with vibrato (31.8 and 31.2 without: the refusal removes the noisiest vibrato frames); *intent uncertain* rises under vibrato (scales 5 → 7 of 20, round 3 → 9 of 19). Re-syntheses whose truth found every score state (20 of 20 straight scales, 15 of 20 vibrato rounds, R-07's caveat): the shown statement excludes the true spread in 0 of 20 and 0 of 15, the lower end holds in 20 of 20 and 15 of 15 |

**Fixtures for squillo** (`results/fold_refusal_fixtures.json`; two runs
byte-identical, CPython 3.13.14, `math`, `struct.pack('<f')`, GNU C
Library 2.43). The fold's layout (`fold.py`): `take-spread-15c.wav`, the
fold's 5-cent deviations times three (population sd exactly 15), 340 800
samples; `take-vibrato-in-tune.wav`, fourteen notes on the tuning, each
0.8 s (38 400 samples) with the fold's gaps and ramps and phase
2π*f*·*m*/48000 + *f*·0.0204/5.5·(1 − cos(2π·5.5·*m*/48000)), a 5.5 Hz
vibrato from 35.68 cents below to 34.96 cents above, 609 600 samples;
`tone-weak-odd.wav`, E-002 round 3's must-fail tone (350 Hz, harmonic *k*
at 1/*k*² to 20 kHz, the first 26 dB under the second, every other odd
harmonic 10 dB under its 1/*k*² level), sine phase 0, scaled by 0.5 over
the sum of the amplitudes, 48 000 samples. With the refusal and the `cyc`
centre:

| Fixture | σ̂ | *u*_B | State (U25) | Check |
| :--- | ---: | ---: | :--- | :--- |
| `take-in-tune.wav` | 0.001 | 1.000 | measured | contains 0 |
| `take-spread-5c.wav` | 5.226 | 1.432 | measured | contains 5, excludes 0 |
| `take-spread-15c.wav` | 16.897 | 3.461 | measured, upper end 23.82 | contains 15, excludes 5; *at least* under MT-007's old rule (must fail) |
| `take-vibrato-in-tune.wav` | 0.059 | 1.005 | measured | contains 0; round 1's median centre: *u*_B 14.3, *at least* (must fail) |
| `take-drift-60c.wav` | 22.484 | 4.522 | at least, lower end 13.441 | in (0, 18.6052] |
| `take-uncertain.wav` | — | — | intent uncertain | |
| `tone-weak-odd.wav` | | | | YIN reads all 122 frames an octave high (*d*′ at least 0.0469); MT-003 refuses all 122 |

Comparisons: 15c → 5c improved, 5c → in-tune improved, 5c → 5c no
change, drift → in-tune improved (one-sided), in-tune → drift worse, drift
→ drift no change (two lower ends).

A first form of `take-vibrato-in-tune.wav`, at ±50 cents (VocalSet's
median extent is 47.3, E-002 result 21), split its 14 notes into 98
segments, *at least*: round 1's provisional tuning, the circular mean of
all frames, turns when a vibrato wider than 38.3 cents runs through every
frame (the mean of e^(iπ*A* sin θ / 50) over a cycle is J₀(π*A*/50),
negative from there), and the notes then sit near the semitone boundary.
Iteration 38 wrote *u*_B 36.6 from a run no results file kept; the
re-derivation below (squillo iteration 43, `results/f040_wide_vibrato.json`)
gives 98 segments and *u*_B 37.466 at +50 / −51.5 cents, 38.094 at ±50
exactly, and does not reproduce 36.6. Round 2's phrases start each note straight and fade the vibrato
in, so they did not meet it. Honest (the lower end is below 0), but a wide
vibrato from the onset may never be measured: squillo F-040.

**What this says for squillo.** Round 2's rule, centre and comparison hold
with MT-003's refusal: fold them into `metrics` (MT-006 to MT-008) and ADR
0015. Nothing in the synthetic evidence moved beyond sampling. The refusal
takes a large share of real vibrato frames (36–41 %), which lowers *u*
there and raises *intent uncertain*. No real straight take is measured,
with or without it (F-032 stands for pitch).

**Limits.** Half of round 2's phrases (the cut above); round 2's limits
otherwise (synthetic voices, no drift, trained singers).

## F-040's numbers re-derived (squillo iteration 43)

Squillo F-043 (m): F-040's "98 segments, *u* 36.6 cents" was in no results
file. `f040_wide_vibrato.py` rebuilds `take-vibrato-in-tune.wav` with
`fold_refusal.py`'s own generator, changing only the vibrato's width, and
measures each take with the same pipeline (MT-003's refusal, the centre
over whole cycles, U25). Conditions and checks are in its docstring,
written before the run. Four seconds on one process.

**Checks.** Must pass: at the fixture's β = 0.0204 the take is
byte-identical to the committed fixture (its sha256 in
`results/fold_refusal_fixtures.json`), gives 14 segments and the same state
and *s* (measured, 0.059). Must fail: the split test (segments above 14) is
false on the fixture and true on at least one take above 38.3 cents. All
pass.

**Result** (`results/f040_wide_vibrato.json`). 14 in-tune notes of 800 ms,
vibrato 5.5 Hz from every note's first sample, f = f_j (1 + β sin), named
by the upward extent in cents:

| Upward extent, cents | 30 | 35.0 (fixture) | 36 | 37 | 38 | 39 | 40 | 41 | 42 | 43 | 44 | 45 | 50 |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Provisional tuning, cents (truth 23) | 26.3 | 32.1 | 36.0 | 42.6 | −48.2 | −40.9 | −36.7 | −34.2 | −32.7 | −31.7 | −31.0 | −30.4 | −28.9 |
| Segments (14 notes) | 14 | 14 | 14 | 14 | 14 | 14 | 14 | 40 | 70 | 90 | 96 | 98 | 98 |
| State | measured | measured | measured | measured | measured | measured | measured | at least | at least | at least | at least | at least | at least |
| *u*_B, cents | 1.003 | 1.005 | 1.005 | 1.006 | 1.006 | 1.007 | 1.007 | 11.593 | 21.803 | 26.987 | 28.812 | 31.098 | 37.466 |

Symmetric in cents (f = f_j 2^(*A* sin / 1200)): ±45 gives 98 segments,
*u*_B 30.579; ±50 gives 98, *u*_B 38.094.

**What this says for squillo.** F-040 holds in kind and its 98 segments
reproduce; its *u* 36.6 does not (37.466 or 38.094, by the vibrato's
form). The provisional tuning moves away from the truth as the vibrato
widens and has turned by 38 cents, as J₀ predicts, but on this take the
notes split only from 41 cents; 38.3 cents is where the tuning turns, not
where measurement fails. **Limits.** One synthetic take, one rate, one
tuning (23 cents); where the split begins depends on them and is not
measured more widely.

**Checks made able to fail (squillo iteration 47, F-050 a).** R-09 found
two faults: the split test's must-fail case took its expectation from
F-040's own claim (J₀ turns negative above 38.3 cents), and the takes' ±*A*
extremes and 14 × 800 ms structure were stated, not asserted. Now:

| Check | Must pass | Must fail | Result |
| :--- | :--- | :--- | :--- |
| Split test (segments > 14) | 14 plain notes (the fixture's melody, no vibrato): 14 segments, false | the same 14 and a fifteenth, the last a whole tone higher: 15 segments, true | both as they must; still false on the fixture |
| Each take is what it is called (`assert_take`): the samples equal the generator's exact phase formula on the sample grid within 10⁻⁹ (0 found), the instantaneous frequency's extremes on the grid equal the take's +*A* and lower extreme within 0.01 cents and lie inside E2..C6, and the output holds 14 runs of 38 398 to 38 400 non-zero samples each after a gap of at least 4 800 | every take in the table and both cents-model takes | the 36-cent take's samples called the fixture; the 15-note take called 14 notes: both refused | as they must |

F-040's claim is kept as a reported result, not a check
(`f040_claim_result`): the first splitting take is at +41 cents, the last
whole one at +40. Every row of the table above is unchanged.

## Round 3: each note's centre and aim, and the rung that centres it (squillo iteration 59)

```
uv run python round3.py check          # the checks, each checked (S15), 25 s -> results/round3_checks.json
uv run python round3.py time 48 18     # S19 sample, on the pool
uv run python round3.py synth 18       # 1680 phrases, 9.7 min on 18 processes -> data/cache/r3_synth.pkl
uv run python round3.py real           # 40 E-002 re-syntheses, 77 VocalSet originals, 6 s -> data/cache/r3_real.pkl
uv run python round3.py select         # the two selections, fit half only -> results/round3_select.json
uv run python round3.py rungs 18       # H3, 20 s -> data/cache/r3_rungs.pkl
uv run python round3.py report         # -> results/round3.json
uv run python round3.py posthoc 18     # revision 2, after the report -> results/round3_posthoc.json
```

**Question** (squillo F-045, R-11's focus for iteration 59; F-041's first
case). Only `steadiness` has a ladder, so a take with no held note has no
far vision. The rung that would serve every take moves each note's centre
towards the note it aimed at. Can each note's centre, and its distance from
its aim, be given an honest ±; can a gate keep a wrong aim from moving the
singer towards a wrong note; and is the centred rung a step `metrics` calls
improved? Reference-free (any song) and with the written melody (a library
phrase).

**Rules first.** The measurand, the candidates, the bars B1 and B2, both
selections and every check are in `round3.py`'s docstring, committed before
any run (`815cbdc`). Revision 1 (`7d4c87f`), before any run: check C1 found
three wide library items (`apres-un-reve`, `blue-umbrella`, `lamplighter`)
outside the bass's range under E-004's placement, so where that placement
does not fit the lowest note goes on the range's floor. Revision 2 (`71c8f08`), after
the report: post hoc diagnostics, labelled as such, never a selection.

**Measurand**, per note: δ = *C* − *A*, the note's realised centre (round 2's
centre rule on the sung contour over its true boundaries) minus its aim on
the singer's own realised tuning (100 *n* + τ, τ the weighted linear mean of
*C* − 100 *n*). *d* is its estimate. Two paths: **free**, round 2's
segmentation, centre and circular tuning, the aim the nearest semitone
(*right* when within 50 cents of *A*); **known**, the written notes aligned by
round 2's DTW, deviations on the weighted linear tuning, a note more than
150 cents off a wrong note, never moved. MT-003's refusal on throughout.

**Inputs.** 960 random phrases (round 2's generator, 14 and 28 notes) and
720 renderings of E-004 fold 2's 30 library items (`squillo-lab E-004 @
d0f9cde`, three each), σ = 0, 10, 20, 30 cents, straight or vibrato (5.5 Hz
±50 cents faded in), six voices, round 2's error model. Every sounding
sample inside ADR 0007's E2–C6, asserted: extremes −2659.5 and +1319.7
cents. Halves by seed: 840 *fit*, 840 *held out*; both selections read the
fit half only. Real: E-002's 40 WORLD re-syntheses (known f0; 20 straight
scales, 20 vibrato rounds, every score state found by the truth alignment in
40 of 40) and the 77 VocalSet originals (H3 only).

**Candidates and bars.** Per-note *u*: P1, the note's settle *u*; P2, P1 ⊕
the tuning's *u* (free: round 2's circular delta method; known: *s*/√*n*ₑ).
**B1**: in every cell with ≥ 20 counted notes, |*d* − δ| > 2*u* in at most
5 % (GUM 6.3.3, *k* = 2). A note is moved by *m* = −clip(*s d*, ±50) (SY-002's
clip), only when |*d*| > 2*u*; it is *harmed* when |δ + *m*| > |δ|. Gates:
free, phrase state (σ̂ above chance, or measured under U25) × |*d*| + 2*u* ≤
*T*, *T* = 50, 40, 30, 20; known, *T* = none, 50, 40, 30, 20. **B2**: in every
cell with ≥ 20 moved notes, at most 2.5 % harmed at full strength (one
tail of B1's interval). **H3**, reported with no bar: the rung (the take's
pitch with each moved note shifted, SY-004's description) measured again;
improved by fold 2's `compare` (free) or round 2's `t_K` (known), at *s* =
0.25, 0.5, 0.75, 1.

**Timing (S19).** 48 phrases, two in each of the 24 conditions, on the
18-process pool: 0.50 s of wall time per phrase, 14.0 minutes for 1680; the
rung step 0.057 s per phrase. The run took 9.7 minutes.

**Checks** (`results/round3_checks.json`):

| Check | Must pass | Must fail | Result |
| :--- | :--- | :--- | :--- |
| C1 generator: every item fits every voice; the contour inside E2–C6 | 30 items × 6 voices fit (after revision 1); 4 extreme renderings (bass and high soprano, σ = 30, vibrato) inside | a 30-semitone span does not fit; a rendering shifted +1500 cents raises | as they must |
| C2 the truth's centre rule | four constant notes with gaps: centres equal within 10⁻⁹ | the same expectation on a contour with one note 5 cents off: refused | as they must |
| C3 the known path equals round 2's `known_melody` (*s*, *u*_B, 10⁻⁹) | 3 phrases, each against itself | each against the next phrase's | as they must |
| C4 bar B1 on reference conditions (12 phrases, random14, σ = 10, straight) | *d* := δ: 0 of 168 missed | *u* := 0: 168 of 168 missed | as they must |
| C5 bar B2 on reference conditions (the same 12) | moves from the truth: 0 of 99 harmed | the same moves reversed: 99 of 99 harmed | as they must |
| C6 the rung's frames | moved segments shift exactly, NaN stays NaN | every segment one frame late: caught | as they must |

**Results** (`results/round3.json`, `round3_select.json`; post hoc
`round3_posthoc.json`; Wilson 95 % intervals).

| # | Question | Result |
| :--- | :--- | :--- |
| R3-1 | Reference-free, is the per-note ± honest? | **No.** Neither candidate passes B1, even with σ ≤ 20, so selection 1 reports it not honest. Held out, P2 misses in 0.5 % (random14, σ = 0, vibrato) to 25.8 % (random14, σ = 30, straight; 59 of 229); it passes in 7 of 24 cells (every σ = 0 cell but the library's under vibrato, 5.6 %, and two σ = 10 vibrato cells). Real re-syntheses: 7.0 % (4.6–10.3; 316 notes, straight scales), 13.6 % (8.4–21.3; 110, vibrato rounds). The aim itself is mostly right: of found notes, 100 % at σ = 0 straight, 96.4–98.5 % at σ = 20 on random phrases, 92.1–96.8 % on library phrases, 79.7–86.7 % at σ = 30 |
| R3-2 | With the written melody? | **Yes, with P2** (settle *u* ⊕ *s*/√*n*ₑ): B1 holds in 24 of 24 cells on the fit half and 24 of 24 held out, worst 3.7 % (2.1–6.4; random14, σ = 30, straight; 12 of 323), the library's cells 0.0–1.2 %. P1 alone fails from σ = 10 (held out 5.9 % to 37.8 %). Real re-syntheses: straight scales 3.3 % (1.9–5.8; 333 notes), **vibrato rounds 6.4 % (4.0–10.0; 265)**, above the bar |
| R3-3 | Can a gate keep moves from going the wrong way (B2)? | Free: **no gate** passes on the fit half (the nearest, σ̂ measured and *T* = 20, harms 6 of 168 moved notes in random28, σ = 10, straight, 3.6 %), so no reference-free centring. Known: only *T* = 20 passes on the fit half (6 of 470 moved notes harmed, every judged cell within 2.5 %) and it **fails one held-out cell**: library, σ = 10, vibrato, 2 of 36 (5.6 %, 1.5–18.1); held out 11 of 447 overall. Post hoc, the known path harms 0.8–2.5 % of moved notes overall at every gate on either half (none: 29 of 3283 held out, 45 of 3253 fit), but no gate keeps every cell within 2.5 % on both halves; where a gate fails on a half, its worst cell holds 21 to 106 moved notes, at 2.6–5.9 % |
| R3-4 | Is the centred rung a step `metrics` calls improved (H3)? | **No.** With the selected gate (known, *T* = 20) no far vision is improved: 0 of 840 held-out phrases (0–0.46 %) and 0 of 117 real takes (0–3.2 %), at any strength, though some note moves in up to 80 % of phrases (random, σ = 10, straight). Post hoc, moving every note measurably off (no *T*): improved in 0–3.3 % of phrases at σ ≤ 10, 16.7–46.7 % at σ = 20 and 30 straight, 0–10 % under vibrato, 0 of 117 real takes, where the spread falls by a median 3.3–7.6 cents against a bound 2√(*u*₁² + *u*₂²) of 30–187 cents. No rung is ever called worse |

**What this says for squillo.**

- **With a library phrase's written notes**, each note's distance from its
  aim on the singer's own tuning has an honest ± on synthetic phrases to
  σ = 30 and on real straight scales: *u* = the note's settle *u* ⊕ *s*/√*n*ₑ,
  *k* = 2. Not yet under real vibrato (6.4 %). This is F-041's first case,
  per note.
- **Reference-free, it has none**: a singer's own song gets no per-note
  centre with an honest ±, and so no centring rung (`VISION.md` §6: a
  step only if reachable and measured).
- **The centred rung is not a step MT-008 can show.** The spread a
  centring narrows carries a *u* too wide to show the narrowing (the settle
  term again, rounds 1 and 2), so on the measures `metrics` has, centring
  gives no far vision that is "improved". A far vision without held notes
  needs a step measured per note (each moved note measurably off its
  written note, |*d*| > 2*u*, under R3-2's ±), not by the take's spread;
  that is a new measure for `metrics` and a new rule for `coach`, and no
  bar here tested it as the rung's claim.
- **No gate is yet safe enough by B2's per-cell rule**: about 1 % of moved
  notes overall go the wrong way with the written melody, but where a
  gate fails, its worst cell, of 21 to 106 moved notes, reaches 2.6–5.9 %. Squillo F-045 stays open with this
  evidence (deferred to Stage D by squillo R-12, iteration 60).

**Limits.** Synthetic voices (rounds 1 and 2's limits); round 2's error
model, normal per note, no drift; the real check is WORLD re-syntheses of
trained singers, whose truth uses the same centre rule; the harm is judged
at full strength only; B2's cells are small at σ ≥ 20, where the gate moves
few notes. Which part of the free path (segmentation or tuning) costs its
coverage is not measured.

**Audit by squillo R-12 (iteration 60).** Re-run in a clone: `select`,
`rungs`, `report`, `posthoc` and `check` give every committed results
file byte for byte; 47 phrases re-synthesised (one per condition, the
three items revision 1 moved, both extreme voices at σ = 30 with
vibrato) equal the cached rows exactly. No selection, bar or outcome
moves. What it found, stated here rather than re-run:

- *S19.* The timing estimate (48 phrases, 0.50 s each, 14.0 min) was
  first committed with the results (`9083454`), not before the run; the
  sample took the first two jobs per condition, so one library item and
  none of the three wide items revision 1 moved; the README's
  `time 48` is the code's `time 36` with an argument. The run took
  9.7 min, inside the estimate.
- *Revision 1* (`7d4c87f`) came after check C1 had run on generated
  audio and failed, before the timing sample and the full run, not
  "before any run"; it changed only how three library items are placed.
- *Recorded, not asserted:* the 250 `passes` keys in
  `results/round3.json` and the 52 in `results/round3_posthoc.json`.
  They are the bars' outcomes, the results themselves, which may be true
  or false; asserting them would assert the claim under test. The checks
  C1 to C6 are asserted.
- *The checks' reach:* C4 and C5 test the bars' arithmetic on an oracle
  (*d* set to the truth), not through `judge()`, so the per-cell grouping
  and the 20-note minimum are read by hand, not checked, and only on the
  free path's columns; the known path's were read by hand and are
  right. C1's in-range clause cannot fail (`render()` raises first); its
  +1500-cent case is the must-fail. C3's must-fail compares `s` only.
- *The guard* covers `round3.py`, not the modules it imports (`round2.py`,
  `fold_refusal.py`, `run.py`, `infer.py`, `synth.py`, `voice.py`) or
  E-004's items; all were committed and clean at `9083454`.

## Round 4: the provisional tuning, and a tuning from a take's first seconds (squillo iteration 71)

Squillo R-14 §8 scheduled this round for **F-040** (a vibrato wider than
38.3 cents from each onset turns `infer.segment`'s provisional tuning, the
circular mean of all voiced frames, and splits the notes) with **F-056**
(the live pitch line has no tuning lines, since no result says how soon a
tuning fitted to a take's first seconds settles). Code: `round4.py`, whose
docstring holds the conditions, candidates, rules and bars; they were
committed before any run (`122419f`), with two revisions before any run:
`cae7c8c` (revision 1: `assert_vib` read a note's first sample one early,
so the fade condition's must-pass refused round 2's own take) and `5c5ae20`
(revision 2: check c4's bound was 2 cents with no source, and PM failed it
at 2.21; it is now the quantiser's own, 25 cents, half the 50 cents a
correct tuning leaves between a note and a cut; squillo L-057).

**Candidates for the provisional tuning.** P0, the present rule; PM, the
circular mean of each voiced run's 200 ms running median (the smoothing
`infer.segment` already applies); PL, the circular mean of each run's
contour low-passed at 2 Hz (MT-009's contour, E-002 `fold2.py:124-126`).

**Inputs.** Round 2's synthetic phrase generator, copied as `phrase4` and
checked byte-identical to `round2.phrase` (c1), with the vibrato's extent
and onset as parameters: none; 40, 50 and 60 cents from each note's first
sample; 50 cents faded in (round 2's). σ 0, 10 and 20 cents; 14 and 28
notes; 100 phrases a cell, 3000 in all. Round 2's 40 E-002 re-syntheses
(known f0) and its 77 VocalSet originals. MT-003's refusal on.

**Bars, before the run.** A1 honesty: a candidate's MT-007 statement
misses in at most 5 % of every cell, or in no more phrases than P0's. A2:
over the onset cells at 50 and 60 cents, more takes measured than P0, exact
McNemar p < 0.05. A3: no straight cell with fewer measured (McNemar
p < 0.05), and no more misses than P0 on the 40 re-syntheses. B1: the
smallest *t* in {1, 2, 3, 4, 6} s at which the tuning fitted to the first
*t* seconds, frozen, lies within its own 2*u*ₑ of the whole take's in at
least 95 % of the takes with a tuning at *t*, in every cell of at least 20
takes and on the re-syntheses and the originals.

**Checks** (`results/round4_checks.json`), each with a must-pass and a
must-fail case: c1 `phrase4` is round 2's generator (fade and none
byte-identical; onset differs); c2 `assert_vib` refuses a take called what
it is not (three cases) and passes two called rightly; c3 `segment_r` given
P0's tuning is `infer.segment` on every vibrato condition, and on a frame
contour with a 1 Hz ±5-cent wobble gives 14 segments on its own tuning and
28 with every centre on a cut; c4 PM (2.21 cents) and PL (0.92) within 25
cents of a 50-cent onset vibrato contour's tuning, P0 not (48.1, J₀(π) =
−0.30); c5 the coverage test; c6 the McNemar test. All pass.

**Estimate (S19)**, `round4.py time` on the pool of 18 processes: 18
synthetic phrases of the extreme conditions (28 notes, σ 20, 60 cents from
onset; 14 notes, straight) in 8.4 s, 18 real takes in 1.3 s; for 3000 + 117
takes, 1408 s. The run saves each chunk of 300 and resumes.

**The run.** Driven in three foreground calls of 585 s each, the longest
one call may take; each resumed from the chunks saved (`data/cache/r4/`),
so the two chunks a call's limit cut were re-run whole. Every phrase
passed its own assertions (contour in E2..C6, the vibrato as called), and
on every take P0's segments equal `infer.segment`'s (asserted per take).
`results/round4.json`; `checkkeys.py round4.py` with both results files: 0
flags. Shares below are of 100 phrases a cell, Wilson 95 % intervals in
the results file.

**A. The provisional tuning (F-040).** A1 to A3 pass for both PM and PL;
PM is taken (463 against 460 takes measured over A2's cells).

| Rule | Onset 50 and 60 cents, takes measured (A2, of 1200) | Provisional tuning's distance from the truth, median per cell, onset 40–60 | Worst miss of any cell (A1) | Straight cells (A3) | 40 re-syntheses: misses |
| :--- | ---: | :--- | :--- | :--- | :--- |
| P0 | 0 | 36.7–48.2 cents | 2 % (14 notes, σ 20, no vibrato) | — | 0 |
| PM | 463 (McNemar 463 to 0) | 1.9–6.1 cents | 4 % (14 notes, σ 20, onset 40) | none fewer measured | 0 |
| PL | 460 (460 to 0) | 1.6–5.6 cents | 4 % (the same cell) | none fewer measured | 0 |

Per cell, P0 gives no take measured at 50 or 60 cents from the onset (0
of 100 in each of the 12 cells: 24–90 % "at least", the rest "intent
uncertain"), and 0–25 % at 40 cents. PM gives, at σ 0,
77 % (14 notes) and 72 % (28) measured at 50 cents, 57 % and 41 % at 60;
at σ 10, 61 % and 56 % at 50 cents; at σ 20 4–16 %, as without
vibrato (13 % and 9 %). With vibrato faded in (round 2's) and without
vibrato, PM and P0 give the same states within 6 points. **Real takes.**
No real take is measured under any rule, as in round 2 (their *u* keeps
them "at least"). On the 20 vibrato re-syntheses PM leaves 2 intent
uncertain against P0's 5, and on the 39 vibrato originals 14 against 16;
no rule misses on the re-syntheses.

**B. A tuning from the first *t* seconds (F-056).** B1 finds **no *t* up
to 6 s** for P0 or PM: the early tuning's own ± 2*u*ₑ misses the whole
take's tuning in more than 5 % somewhere at every *t*.

| PM, *t* | Cells failing B1 (of 30, and real) | σ 0 and 10, worst miss | σ 20, worst miss | Re-syntheses: miss; median \|Δ\|, 2*u*ₑ | Originals: miss; median \|Δ\|, 2*u*ₑ |
| ---: | :--- | ---: | ---: | :--- | :--- |
| 1 s | 28 | 27.6 % | 50.0 % | 11.8 % (of 17 with a tuning); 8.3, 25.5 cents | 13.0 % (23); 11.8, 26.8 |
| 2 s | 21 | 12.0 % | 30.0 % | 17.1 % (35); 8.8, 23.2 | 14.0 % (57); 8.7, 21.5 |
| 3 s | 14 | 6.0 % | 22.0 % | 13.5 % (37); 8.7, 21.0 | 13.0 % (69); 10.2, 19.9 |
| 4 s | 10 | 4.0 % | 13.0 % | 10.5 % (38); 7.3, 19.9 | 9.6 % (73); 7.8, 20.0 |
| 6 s | 6 | 4.0 % | 6.0 % | 11.1 % (36); 6.9, 18.3 | 11.6 % (69); 8.1, 17.4 |

Under P0 every *t* fails more cells (19 to 30), and its vibrato cells miss
up to 45 %. **Post hoc, labelled:** on the synthetic phrases with σ ≤ 10
under PM, every cell passes from 4 s (worst 4 %), with a median 2*u*ₑ of
4.2–13.4 cents per cell; it is the σ = 20 cells (median 2*u*ₑ 13.3–19.4
cents) and the real takes (19.9 and 20.0) that keep the early tuning's ±
from holding.

**What this says for squillo.** F-040: the provisional tuning taken from
each run's 200 ms running median removes the turn: at 50 and 60 cents from
the onset it lies within a median 1.9–6.1 cents of the truth per cell
instead of 36.7–48.2, and turns no measured take into a miss; squillo's MT-006 may take
it in place of the circular mean of all frames, and the fold names the
rule. On real takes the gain is small (3 and 2 fewer intent uncertain),
because what keeps them "at least" is their spread's *u*, not the turn.
F-056: no tuning fitted to a take's first seconds, frozen, carries an
honest ± within 6 s on every condition: real takes miss 9.6–17.1 % at
every *t*. So the live line keeps no tuning lines, as UI-012 has it; a later
round could try a ± widened by a factor fitted on one half and checked on
the other, or a tuning held only once *u*ₑ is small. **Limits.** One
vibrato rate (5.5 Hz) and sinusoidal vibrato; synthetic voices; real takes
are 40 re-syntheses and 77 originals of trained singers; *t* only to 6 s;
B compares two estimates on nested data, so its misses include the whole
take's own error.

## Fold 4: the provisional tuning into squillo `metrics`, and its fixture (squillo iteration 72)

Squillo iteration 72 folds round 4 (F-040): ADR 0015 step 1's provisional
tuning becomes PM, the circular mean of each bridged voiced run's 200 ms
running median (`round4.provisional`). Code: `fold4.py`, whose docstring
holds the fixture's conditions, rules F1–F3 and the checks of the checks,
committed before any run (`69ff606`; the guard refused the uncommitted
script first). `checkkeys.py fold4.py` alone and with `results/fold4.json`:
0 flags. The run takes 3.5 s.

**The fixture.** `take-vibrato-onset-50c.wav`: fold 2's fourteen-note take
(`fold_refusal.py:393-426`), every note on its semitone of a tuning 23
cents above A4 = 440 Hz, with take-vibrato-in-tune's 5.5 Hz vibrato widened
to *f*ⱼ · (1 + β sin(2π · 5.5 · *t*)), β = 2^(50/1200) − 1 =
0.029302236643492074, full from each note's first sample: +50.0000 and
−51.4871 cents on the sample grid (asserted), 216.41 to 458.95 Hz, inside
E2..C6. 609 600 samples, 2 438 458 bytes, SHA-256
`9bc0ae78112011490b635abeb7031d605358cb32c9b439aaf8eed36df5623bae`.

**Results** (`results/fold4.json`; MT-003's refusal on, 31 frames refused
on the fixture under both rules):

| Rule | Fixture held | F1 under PM | F2 under P0 (must fail) |
| :--- | :--- | :--- | :--- |
| F1, F2 | `take-vibrato-onset-50c.wav` | **measured**, σ̂ 0.037, *u* 1.013, interval −1.989 to 2.063 cents, 14 segments: holds | **at least**, lower end −58.0, upper 91.8, 98 segments (round 1's F-040 count): not measured, as required |

Checks of the checks: "measured and contains 0" fails on
`take-spread-5c.wav` under PM, and "not measured" fails on
`take-vibrato-in-tune.wav` under P0 (measured): both as required.

**F3 failed as written.** Every MT-006, MT-007 and MT-008 scenario check
holds under PM (in tune and vibrato in tune measured containing 0; 5c
containing 5 and not 0; 15c containing 15 and not 5; drift at least with
its lower end in (0, 18.6052]; uncertain; the six compare checks), and 22
of the 24 wav fixtures keep their state. Two do not, and "no state moved"
is false:

| Fixture | P0 | PM |
| :--- | :--- | :--- |
| `fixtures/metrics/held-vibrato.wav` (one 5 s tone, 220 Hz, vibrato −40.28 / +39.37 cents) | measured, σ̂ 0.39 ± 2.05, **15 segments** | intent uncertain, **1 segment** |
| `fixtures/signal/vibrato-220hz-5p5hz.wav` (one 1 s tone, −49.2 / +47.8 cents) | at least, lower end −38.2, **9 segments** | intent uncertain, **1 segment** |

Both are one sustained tone each, with a vibrato wider than the 38.3
cents at which P0 turns (F-040), read from squillo's `fixtures/MANIFEST.md`
after the run. Under P0 each tone was split into 15 and 9 "notes", and
`held-vibrato.wav`'s spread was given as measured, a claim about pitch
accuracy that one note cannot support. Under PM each is one note, and one
note is not enough to tell aimed notes apart (fewer than two notes kept),
so intent uncertain. The rule was wrong, not PM: F3 was written without
reading each fixture's vibrato extent against 38.3 cents (squillo L-058).
No squillo scenario reads `pitch-spread` on either fixture (squillo
iteration 72 searched every spec). The asserts after F3 did not run;
`fold4.json` holds their values, every one true.

**What this says for squillo.** MT-006 states that a vibrato from each
note's onset does not turn the tuning, with this fixture as its scenario,
and ADR 0015 step 1 names PM; `held-vibrato.wav`'s `pitch-spread` is
intent uncertain under the new rule, which no scenario contradicts.

## Round 5: the known-melody spread under MT-003's refusal (squillo iteration 73)

```
uv run python round5.py check          # the checks, each checked (S15) -> results/round5_checks.json
uv run python round5.py time 36 18     # S19 sample on the pool
uv run python round5.py synth 18       # 2040 phrases -> data/cache/r5_synth.pkl (saves every 100, resumes)
uv run python round5.py real           # 40 E-002 re-syntheses, 77 VocalSet originals -> data/cache/r5_real.pkl
uv run python round5.py report         # -> results/round5.json
```

**Estimate (S19)**, committed before the full run: `round5.py time 36 18`,
after the rules commit (`65910cb`), on the pool of 18 processes: 12 of
round 2's slowest phrases (56 notes, σ 0 and 40, straight and vibrato,
three each), 12 onset phrases and 12 library renderings, each to its end,
in 30.0 s, 0.833 s of wall time each; for 2040 phrases, 28.3 minutes (an
upper bound, since most of round 2's phrases are 14 or 28 notes). The run
is driven in foreground calls of under 600 s, each resuming from the rows
saved every 100 phrases.

**Question** (squillo R-14 §8; F-041, F-033 (c), Q-021 part 6). Round 2
(R7, R8) found the spread about a library phrase's written notes,
unwrapped (K), honest to 40 cents and two to three times as powerful as
the take's own wrapped spread, measuring with every frame YIN gave. Does K
stay honest under squillo MT-003's refusal (aperiodicity ≥ 0.02), in which
states may squillo show it, and what exactly is the alignment rule?

**Rules first.** The measure K with its alignment stated step by step,
four candidate state rules, the inputs' conditions, bars B1–B3 and checks
c1–c5 are in `round5.py`'s docstring, committed before any run
(`65910cb`); the estimate after the timing sample, before the full run
(`4330b9c`). No revision.

**The measure K**, stated exactly (`round5.py` docstring, steps 1–9): the
measured cells in order, gaps skipped, each replaced by the median of the
25 cells centred on it (ends padded); the written notes, consecutive
repeats merged; transposition candidates r0 + 100 *k*, *k* = −45 … 45, r0
the contour's circular mean; the monotone path (each cell stays on its
state or moves to the next, first cell on the first state, last on the
last) of least Σ min(|*x* − 100 *s* − *T*|, 300) cents, the first *T* on a
tie and staying on a tie; each state's segment from its first to its last
cell; round 2's centre (whole cycles where the fitted vibrato is at least
25 cents, else the median, over 30–90 %); states under 0.1 s dropped; a
note more than 150 cents from the weighted median deviation a wrong note,
left out; tuning the weighted mean; K the weighted SD with *n*ₑ/(*n*ₑ − 1);
*u*_B = K/√(2(*n*ₑ − 1)) ⊕ the weighted rms settle *u*; no value with
fewer than two notes. **Candidates:** measured when K + 2*u*_B ≤ *X*, else
the lower end only, *X* = ∞, 40, 35, 30 in that order; the first to pass
B1 is selected.

**Inputs.** R: round 2's design under its seeds, the first 40 phrases of
each of its 42 cells (14, 28, 56 notes; σ 0–40; straight or vibrato faded
in), 1680; O: round 4's 50-cent vibrato full from each onset, the first 40
of each of its 6 cells (14, 28 notes; σ 0, 10, 20), 240; L: E-004 fold 2's
30 library items at σ 0 and 20, straight and vibrato, one rendering each,
120 (round 3's renderer); every contour asserted inside E2..C6 by its
generator. Real: round 2's 40 E-002 re-syntheses (truth from round 2's
cache) and 77 VocalSet originals. MT-003's refusal on; 4.82 % of the
synthetic frames YIN measured refused. Python 3.13.14, numpy 2.5.3, scipy
1.18.1.

**The run.** 2040 phrases in three foreground calls under 600 s, each
resuming from the rows saved every 100 (the first two calls' limits cut
the chunks in flight, re-run whole), about 29 minutes in all against the
28.3 estimated; real takes 1 minute.

**Checks** (`results/round5_checks.json`; c1 also over the whole run in
`results/round5.json`):

| Check | Must pass | Must fail | Result |
| :--- | :--- | :--- | :--- |
| c1 K reimplemented equals round 2's cached `known` (*s*, *u*_B) within 10⁻⁹, no refusal | 4 of 4 phrases; the whole run 1680 of 1680 | the next phrase's cached values: 0 of 4; 0 of 1680 | as they must |
| c2 `round2.dtw_T` equals an independent full-matrix programme in *T*, path and cost | 20 of 20 random cases | the reference given one state a semitone off: 0 of 20 equal | as they must |
| c3 the refusal drops exactly the frames at *d*′ ≥ 0.02 | `tone-aperiodic.wav`: 13 refused (E-002 fold F5) | the threshold at 0.2: 0 refused | as they must |
| c4 bar B1 on round 2's cached values | K always measured, σ ≤ 30: worst cell 2.5 % | the wrapped spread always shown measured, σ = 40: worst 52.7 % | as they must |
| c5 the comparison | a phrase against itself: no change | against itself with K raised by three times the bound earlier: improved | as they must |

`checkkeys.py round5.py results/round5.json results/round5_checks.json`
flags six check keys (`must_pass_refused`, `must_fail_threshold_0p2`,
`must_pass_worst_percent`, `must_fail_worst_percent`,
`must_fail_next_phrase`, `must_fail_state_off`). Read by hand: each is
asserted through the local it records (`n02`, `n2`, `wp`, `wf`, `fail`,
`ok_fail`) on the assert line that follows it. *Recorded, not asserted:*
the `passes` keys of B1 (per candidate), B2 and `B3_passes`: they are the
bars' outcomes, the results themselves.

**Results** (`results/round5.json`; Wilson 95 % intervals).

| # | Question | Result |
| :--- | :--- | :--- |
| R5-1 | Is K honest under the refusal (B1)? | **Yes, always measured (*X* = ∞, selected).** In every one of the 52 cells the shown statement excludes σ in at most 5 %: worst R, 14 notes, straight, σ = 25, 2 of 40 (5.0 %, 1.4–16.5), at the bar; σ = 30 and 40 at 14 notes 1 of 40; every other R cell 0; O (onset vibrato) 0 of 40 in all six; L 0 of 30 except σ = 20 straight, 1 of 30 (3.3 %, 0.6–16.7). Without the refusal the same worst cell, 2 of 40. The lower end holds in 2040 of 2040 (99.8–100) and every interval covers the realised spread (2040 of 2040). *X* = 40, 35 and 30 also pass, measuring 1356, 1141 and 899 of 2040 phrases. *u*_B median per cell 3.1–13.6 cents (L: 3.1–9.2; O: 3.7–6.7) |
| R5-2 | False changes (B2)? | **None:** 0 of 140 pairs from one cell in each of the six length × vibrato conditions (0–2.7 %); 0 of 77 halves of VocalSet originals |
| R5-3 | Power, against the wrapped spread on the same phrases | Straight, 20 → 0 cents: K 57.5 / 72.5 / 62.5 % (14, 28, 56 notes) against 25.0 / 42.5 / 27.5 %; 40 → 10: 50.0 / 67.5 / 82.5 % against 0 / 10.0 / 22.5 %. Vibrato faded in, 40 → 10: 17.5–22.5 % against 0; 20 → 0: 0 for both. K never calls worse |
| R5-4 | Real takes (B3) | **Passes:** re-syntheses whose truth found every state, excluded in 0 of 20 straight scales and 0 of 15 vibrato rounds. Every real take is measured under *X* = ∞ (the wrapped spread: none), but with a wide ±: *u*_B median 12.1 (re-synthesized straight scales, K median 19.2), 11.1 and 13.6 (original straight scales and round), 58.7–66.1 under vibrato (K median 39.0–45.5), where 36.5–40.9 % of frames are refused |
| R5-5 | What the alignment finds | Every written state found in 1442 of 1680 R phrases, 234 of 240 O and 118 of 120 L; 1 wrong note in 2040 synthetic phrases; real: every state in 15 of 20 and 4 of 20 re-syntheses (straight, vibrato), 19, 11, 13 and 3 of the originals' four sets; 0–9 wrong notes per set. A state not found leaves the spread honest (R5-1) on fewer notes |

**What this says for squillo.** F-041's lab round is done: the
known-melody spread K, with the alignment stated in `round5.py`'s steps
1–9, stays honest under MT-003's refusal on round 2's design, under a
50-cent vibrato from each onset and on E-004's 30 library items, and on
real re-syntheses; it sees 20 → 0 cents in 57.5–72.5 % of straight
phrases where the wrapped spread sees 25.0–42.5 %, with no false change.
Shown always as measured it passes the bar; so do the caps at 40, 35 and
30 cents. The fold (squillo iteration 74) chooses between them on what
the bar cannot see: always measured gives real vibrato takes a value with
a ± of about 60 cents, an interval far beyond the 40 cents tested, where
*X* = 40 gives them a lower end, as MT-007 does for the wrapped spread.
It needs `runner` to pass the phrase's written notes, `metrics` to name K
as a take measure of a library phrase with these steps, and MT-008's
comparison to apply to it.

**Limits.** Synthetic voices and round 2's error model (normal per note,
no drift); 40 phrases a cell (a cell at the bar, 2 of 40, has an interval
up to 16.5 %); E-004 fold 2's 30 items, not the 39 the slice now ships
(the 9 originals written for held notes are not rendered here); the real
truth is WORLD re-syntheses of trained singers; one vibrato rate. Merging
repeated written notes into one state is the rule as stated, and the
spread of a phrase with repeats is measured on fewer notes.

## Fold 5: the known-melody spread into squillo `metrics`, on its take fixtures (squillo iteration 74)

```
uv run python fold5.py run <dir>   # the two notes fixtures to <dir>; K on squillo's take fixtures -> results/fold5.json
```

Squillo iteration 74 folds round 5 (F-041): `pitch-spread` of a take given a
phrase's written notes is K (`round5.py` steps 1–9, `round5.known`), shown
measured when K + 2*u*_B ≤ 40 cents and as its lower end otherwise (round
5's candidate *X* = 40, chosen in squillo ADR 0015 over *X* = ∞ because
real vibrato takes measured under ∞ carry a ± of about 60 cents, beyond the
40 cents round 2 and round 5 tested). Code: `fold5.py`, whose docstring
holds the inputs' conditions, rules G1–G8 and the checks of the checks
M1–M4, committed before any run (`fold5.py`'s first commit).
`checkkeys.py fold5.py` alone and with `results/fold5.json`: 0 flags. The
run takes 1.5 s. A first import failed before any rule ran (E-002's
`fold.py`, on the path through `round2`, shadowed this experiment's; it is
now loaded by path), and was fixed before the rules commit.

**Inputs.** Squillo's take fixtures, hashes checked against its
`fixtures/MANIFEST.md`: every note *j* on semitone `MELODY[j]` of a tuning
23 cents above A4 = 440 Hz (`fold.py:205-219`, `fold_refusal.py:393-401`),
A3 B3 C♯4 D4 E4 F♯4 G♯4 A4 G♯4 F♯4 E4 D4 C♯4 B3, no two neighbours equal.
Two notes fixtures written by this script, what squillo `runner` passes
(EX-010's pitch names, in order): `notes-a-major-up-down.json` (166 bytes,
SHA-256 `c6ae3201af84d84d38048e35fea57603995a625c4e23f56ced5d62840d543bc2`),
asserted to parse back to `MELODY`, and `notes-a3.json` (30 bytes,
`a02fb1ad63b0dd8a5f2dce679970dd939f14b8803f181f8bd893c0bfa98b5beb`). Each
take's truth is the population sd of its deviations, computed from the
generators' own lists. MT-003's refusal on.

**Results** (`results/fold5.json`; cents):

| Fixture | Truth | State | K | *u*_B | Lower end | Upper end | States found | Rule |
| :--- | ---: | :--- | ---: | ---: | ---: | ---: | :--- | :--- |
| `take-in-tune.wav` | 0 | measured | 0.001 | 1.000 | −1.999 | 2.001 | 14 of 14 | G1 holds |
| `take-spread-5c.wav` | 5 | measured | 5.189 | 1.427 | 2.335 | 8.042 | 14 of 14 | G2 holds |
| `take-spread-15c.wav` | 15 | measured | 15.567 | 3.213 | 9.142 | 21.992 | 14 of 14 | G3 holds |
| `take-drift-60c.wav` | 18.6052 | measured | 19.281 | 3.911 | 11.458 | 27.103 | 14 of 14 | G4 holds |
| `take-uncertain.wav` | 28.7938 | **at least** | — | — | 17.878 | — | 13 of 14 | G5 holds |
| `take-vibrato-in-tune.wav` | 0 | measured | 0.059 | 1.005 | −1.950 | 2.069 | 14 of 14 | G6 holds |
| `take-vibrato-onset-50c.wav` | 0 | measured | 0.037 | 1.013 | −1.989 | 2.063 | 14 of 14 | G6 holds |
| `held-steady.wav` with `notes-a3.json` | — | no value (one note) | — | — | — | — | 1 of 1 | G7 holds |

G8 holds: `take-uncertain` then `take-in-tune` improved (the wrapped spread
gives `take-uncertain` no statement, so MT-007's form cannot call it);
`take-spread-15c` then `take-spread-5c` improved; `take-spread-5c` twice no
change; `take-in-tune` then `take-drift-60c` worse.

**One rule failed as written:** "every fixture's 14 states found, 0 wrong
notes" holds on six of the seven takes and fails on `take-uncertain.wav`,
13 of 14 states found (0 wrong notes). Its deviations reach ±46.4 cents,
so neighbouring notes a tone apart come within 107 cents of each other and
the alignment gives one state no cell; round 5 found every state in 1442 of
1680 of its own phrases (R5-5), so the rule was written against a rate the
experiment had already measured below 100 % (squillo L-059). A state not
found leaves the statement honest on fewer notes (R5-1), as here: the lower
end 17.878 lies below the truth 28.7938. The asserts after it did not run;
`fold5.json` holds the must-fail values, every one as required.

Checks of the checks (`must_fail`): M1, the notes with D4 written as D♯4 on
`take-in-tune.wav`, gives at least, lower end 10.074, so the in-tune rule
fails as it must; M2, `take-uncertain.wav` with no written notes under
MT-007 (round 4's PM), is intent uncertain; M3, `take-in-tune` twice, is
not improved; M4, the D♯4 list does not parse to `MELODY`.

**What this says for squillo.** `metrics` can state K as `pitch-spread`'s
estimate for a take given written notes, with these fixtures as its
scenarios; the take whose aims cannot be told alone gives a lower end with
its written notes, and a later take in tune is then an improvement.
**Limits:** one fixed melody (a major scale up and down) and deterministic
fixtures; the honesty of K across conditions is round 5's, not this fold's.
