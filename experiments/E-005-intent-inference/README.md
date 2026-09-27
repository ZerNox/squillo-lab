# E-005 — Intent inference: pitch accuracy without a reference

**Status:** running (round 1 done and folded into squillo `metrics`, iteration 27; round 2 automated; one `needs-human` step) · **Serves:** VISION §3 (every song is your cover), §5 (reference-free), §6, §12.4

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

**Round 2 (automated).** A settle estimate over whole vibrato cycles; a
per-note ± whose reference term follows the circular estimate (coverage
at σ = 20); a heavier-tailed error model for the flag, fitted on VocalSet
and checked on held-out singers; takes longer than 14 notes; and a
glide-aware segmentation.

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
