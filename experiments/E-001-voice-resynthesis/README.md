# E-001 — Voice re-synthesis: the synthesized you

**Status:** running (round 1 answered on automated evidence; listening check `needs-human`) · **Serves:** VISION §3 (core idea), §8 (on-device), §12.1

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

### Round 1: pitch corrected and steadied, WORLD and PSOLA (squillo iteration 18, 2026-09-25)

**Run:** `uv sync && uv run python fetch.py $(cat data/vocalset-files.txt) &&
uv run python run.py && uv run python timing.py && uv run python report.py`,
then `uv run python diag_gross.py` and `uv run python diag_h1.py` for the
follow-ups. `run.py` took about 18 minutes with 10 processes on the machine
below. Full tables: [`results/summary.md`](results/summary.md); numbers:
`results/summary.json`, `timing.json`, `gross.json`, `h1.json`. The per-frame
data (`data/cache/raw.json`, 44 MB) is not committed; `run.py` rebuilds it.

**Inputs.** (a) 24 synthetic sung phrases (`voice.py`): six voice types from
A2 to E5 (bass, baritone, tenor, mezzo, soprano, high soprano), with and
without vibrato (5.5 Hz, ±40 cents), two seeds each; a nine-note scale
fragment, 4.05 s, 48 kHz. Additive source-filter synthesis with a fixed /a/
envelope; the intended contour and every error are known by construction:
a per-note offset uniform in ±50 cents, a 60-cent onset scoop, and a 1–6 Hz
wobble of 10 cents RMS. (b) 19 VocalSet singers (9 female, 10 male; every
singer with the file), straight-tone scales on /a/, 5.5 to 18.3 s, 44.1 kHz
resampled to 48 kHz (`data/SOURCES.md`, CC BY 4.0).

**Input check** (squillo standing instruction S15). The CheapTrick
long-term envelope, relative to its maximum, at 4.9 and 6.5 kHz: synthetic
baritone −43 and −56 dB; VocalSet f1, f2, f3 −56 and −46, −55 and −48, −47
and −41 dB. Without the higher-pole correction the synthetic voice read −57
and −81 dB and WORLD's unchanged re-synthesis 9.6 dB from its reference; the
envelope distance is limited to 80 Hz–8 kHz because above 20 kHz the synthetic
input has no energy.

**Requests** in cents, applied by each method to its own f0 track, nothing
else changed: `id` none (analysis and re-synthesis only); `c25`, `c50`,
`c100`: 25, 50, 100 % of the note-centre offset from the intended note
removed; `s50`, `s100`: 50, 100 % of the wobble about the note centre
removed. Synthetic: offset and wobble known. VocalSet: note centre a 250 ms
running median of Harvest's f0, intended note the nearest equal-tempered
note (A4 = 440 Hz), wobble the rest, clipped to ±50 cents (a crude intent;
E-005 owns intent). RMS request: `c100` 33 cents synthetic, 24 VocalSet;
`s100` 10 and 18 cents.

**Methods.** WORLD (Morise, Yokomori and Ozawa 2016) through pyworld 0.3.5:
f0 from Harvest (`world_harvest`) or DIO plus StoneMask (`world_dio`),
CheapTrick envelope, D4C aperiodicity, 5 ms frames. PSOLA: Praat 6.1.38 through
parselmouth 0.4.7, Manipulation (10 ms, 60–1100 Hz), PitchTier shifted,
overlap-add. Python 3.13.14, numpy 2.5.3, scipy 1.18.1.

**Measures.** Pitch on squillo's frame axis with E-002's YIN
(`squillo-lab E-002 @ 00bf2e9`, threshold 0.1, E2–C6 widened by 3 cents),
each frame's pitch at YIN's lag centre (E-002 result 5). *Achieved* =
YIN(output) − YIN(input) per frame; *error* = achieved − requested. *Gross*:
|error| > 50 cents. Envelope distance: CheapTrick envelope in dB at 40
mel-spaced frequencies from 80 Hz to 8 kHz, gain-normalised RMS difference,
against the ideal (synthetic: the same synthesizer rendering the requested
contour) or the input (VocalSet). ΔHNR: Praat cross-correlation harmonicity
of output minus reference. Intervals are 95 %: bootstrap over inputs for p95,
Wilson for shares.

**Results.**

| # | Question | Result |
| :--- | :--- | :--- |
| 1 | Is the requested pitch change delivered? | Yes, by all three methods, for every correction and steadying request. Achieved/requested (least squares, non-gross frames): WORLD 0.989–0.999 synthetic and 0.978–1.002 VocalSet; PSOLA 0.997–1.003 and 0.981–1.046 |
| 2 | Per-frame error of the change (non-gross frames) | Median 0.5–0.9 cents WORLD, 1.0–1.2 PSOLA. p95: WORLD 3.0–3.8 synthetic and 4.0–4.6 VocalSet; PSOLA 4.7–5.2 and 4.2–5.0. These include YIN's own error twice (input and output); YIN on the ideal render errs p95 2.5–2.7 cents against the true contour |
| 3 | Error of the output against the requested contour (synthetic, non-gross) | p95: `world_dio` 3.8–4.0 cents, `world_harvest` 5.0–5.3, PSOLA 7.1–7.4; the ideal render 2.5–2.7 |
| 4 | Gross frames | WORLD: 2.5–2.8 % of frames on VocalSet (14 of 19 singers), whatever the request, `id` included; on synthetic input only the two soprano types (f0 from 294 Hz), 0.25–2.8 % of all synthetic frames. PSOLA: 0.01 % synthetic, 0.08–0.18 % VocalSet. Follow-up (`gross.json`, `id`, DIO): of 587 gross VocalSet frames, 585 are upward and 327 within 100 cents of an octave up; WORLD's own f0 there was voiced in all 587 and an octave off the input's in only 2. So squillo's tracker reads WORLD's **output** an octave high where WORLD's analysis was right. WORLD lowers H1 relative to H2 by a median 0.5 (tenor) to 3.3 dB (high soprano) (`h1.json`), a weaker fundamental, which is consistent with this but not shown to cause it |
| 5 | Does the envelope (a proxy for timbre and identity) survive? | Long-term envelope distance, median over inputs: WORLD 0.66–0.71 dB (max 1.65), PSOLA 0.03–0.47 dB (max 0.79), growing with the correction's size. **Scale**, on the unmodified VocalSet inputs: one singer's first half of the scale against the second, median 3.03 dB (max 4.67); two singers of the same sex, median 7.60 dB, minimum 4.07 (83 pairs). Every output lies well inside one singer's own variation. Per-frame distance 0.4–1.8 dB |
| 6 | Artefacts, by harmonicity | WORLD raises HNR by 0.1–3.9 dB (more periodic than the input, most for steadying and on synthetic input); PSOLA lowers it by 1.4–2.7 dB (rougher) |
| 7 | Time per second of audio, one process, native code on a 12th Gen Intel Core i7-12700H, best of three, 8 inputs | `world_harvest` 0.29 s/s (analysis 0.26, re-synthesis 0.03); `world_dio` 0.15 (0.12, 0.03); PSOLA 0.034 (0.025, 0.009). Max over inputs 0.31, 0.17, 0.041. A 10 s take: 1.5 s with WORLD-DIO, 0.3 s with PSOLA. **Not WASM, not a browser** |
| 8 | What synthesis must hold (squillo F-016) | WORLD re-synthesizes from per-frame parameters: at 48 kHz, 200 frames per second of an envelope and an aperiodicity of 1025 bins each (CheapTrick's FFT size 2048 at pyworld's default floor), 1.6 MB per second in float32, against 0.19 MB per second for the samples themselves. PSOLA needs the samples and pitch marks. Both need the whole take before synthesis, and both return audio |

**What this says for squillo.**

- Pitch-only steps of the size a singer needs (note centres up to 50 cents,
  wobble of 10 to 18 cents RMS) are delivered as requested, to within the
  measurement's own resolution, by two classical methods, with the envelope
  kept far inside one singer's own variation. On a laptop CPU in native code
  this takes well under real time. Whether it sounds like the singer, and
  natural, is **not** answered: that needs a listener (below).
- Honesty (VISION §6): re-tracking the synthesized audio is not a sound way
  to state how far the next step is. The tracker misreads WORLD's output an
  octave high on up to 2.8 % of frames; the synthesized contour is known by
  construction and is what a step's distance should be computed from.
- F-016: synthesis needs the take's samples kept in the engine for the run
  (the parameters are eight times larger than the samples), and a path that
  returns audio to the page.
- Neither method wins outright. PSOLA is four to nine times cheaper, keeps
  the envelope closer and misreads less, but errs more against the requested
  contour and adds roughness; WORLD tracks the contour more closely and
  sounds smoother by HNR. The listening check decides between them.

**Limits.** Synthetic voices have a fixed formant envelope, no jitter,
shimmer or breathiness beyond −30 dB aspiration, and a crude higher-pole
correction. VocalSet is studio recordings of trained singers, straight-tone
scales on one vowel; no amateur voices, no songs, no rooms. Vibrato
regularisation, tone and resonance changes and neural vocoders are not
tested. The envelope distance is a proxy computed with WORLD's own
estimator. Native code on one machine: WASM in a browser is unmeasured.

**Needs a human (15 minutes).** The question "convincingly" (VISION §12.1)
needs a listener, and the listener should be the singer.

1. Record three takes of about 10 s each on any microphone, in a quiet room:
   a slow scale on "ah"; a few lines of a public-domain or self-written
   melody; one sustained note (5 minutes).
2. `uv run python listen.py take1.wav take2.wav take3.wav` builds 20 shuffled
   clips in `data/cache/listening/`: for each take the original, WORLD with
   no change, 50 % and 100 % correction and steadying, and PSOLA with 100 %
   correction, plus two repeated originals (1 minute).
3. Listen once to each clip and fill in `ratings.csv`: *same person as you*
   1–5 and *natural* 1–5 (8 minutes). Only then open `key.json`.
4. Commit `ratings.csv` and `key.json` only, never the audio (1 minute).

### Round 2 (open)

The listening ratings; vibrato regularisation; the same pipeline in WASM in
a browser; amateur voices; why the tracker misreads WORLD's output (and
whether octave protection in the tracker or H1 restoration in WORLD fixes
it).
