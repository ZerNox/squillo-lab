# E-001 — Voice re-synthesis: the synthesized you

**Status:** needs-human (rounds 1 and 2 answered on automated evidence: the change delivered, round 1; the time in WASM in a browser, round 2; the listening check `needs-human`) · **Serves:** VISION §3 (core idea), §8 (on-device), §12.1

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
estimator. Native code on one machine (WASM in a browser: round 2).

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

### Round 2: WORLD and a PSOLA in WASM, in Chrome and Firefox (squillo iteration 33, 2026-09-28)

**Question.** How long does re-synthesis take on the device tier, WASM in a
browser, rather than native code (round 1, result 7; squillo F-022, ADR
0014)? Does the WASM build compute the same thing as native code and as
round 1's libraries?

**Run** (S19 estimate first: one Harvest pass natively 0.2 s per second of
audio, so the native run over 43 inputs about 5 minutes, each browser run
about 2 minutes):

```
uv run python r2_export.py        # round 1's inputs and requests, as f64 (2 s)
./r2_build.sh                     # native bench, WASM plain and simd128 (1 min)
./wasm/target/release/bench data/cache/r2 > results/r2/native.jsonl   # 3 min
uv run python r2_check.py         # 10 processes, 1 min
npm ci && node r2_run.mjs         # Chrome and Firefox, plain and simd128, 7 min
uv run python r2_report.py
```

Numbers: [`results/r2/summary.md`](results/r2/summary.md) and
`summary.json`, `check.json`, `native.jsonl`, `<browser>-<build>.json`.

**What runs.** The crate in `wasm/` (Rust 1.98.1, `wasm32-unknown-unknown`,
wasm-bindgen 0.2.129, release with LTO), built three ways: native x86-64,
WASM, and WASM with `simd128`. Two pipelines:

- **WORLD** through world-rs 0.1.0 (BSD-3-Clause, a pure-Rust port of the
  C++ library; rustfft 6.4.1, realfft 3.5.0), with round 1's options: f0 by
  Harvest, or DIO plus StoneMask, 60 to 1100 Hz, 5 ms frames; CheapTrick and
  D4C with their defaults; synthesis with the f0 shifted by the request.
- **A crude TD-PSOLA** written here, standing in for Praat, which does not
  build for WASM here: pitch every 10 ms by normalised autocorrelation
  (Boersma 1993's window correction, Praat's voicing 0.45 and silence 0.03
  thresholds, no path search), pitch marks at waveform maxima one period
  apart, two-period Hann grains overlap-added at the shifted period. It is
  not Praat's algorithm.

Stages are separate calls, timed with `performance.now()` in a dedicated
module worker (one thread, as squillo's engine worker), best of three, in
Chrome 154.0.8037.57 and Firefox 156.0, headless on Linux through
Playwright 1.63.0, the page cross-origin isolated (finest timer). Native:
`std::time::Instant`, best of three. Host: Intel Core i7-12700H, nothing
else running. Timing inputs: round 1's eight (three synthetic phrases of
4.05 s; VocalSet f1, f5, f9, m1, m8, 7.8 to 16.8 s); request `c100`.

**Checks** (S15). *Inputs:* `r2_export.py` asserts on what it writes that
every sample is finite with |x| ≤ 1, durations are round 1's, every request
is finite, `id` is zero and `c100`, `s100` are not, and |request| ≤ 50 cents,
except synthetic `s100`, whose RMS of 10 cents is asserted instead: the first
run stopped there, on a wobble of 61.4 cents that round 1 never clips, so the
stated condition was wrong and was corrected, not the input. The exported
samples equal `run.load`'s bit for bit (asserted in `r2_check.py`). *The
check of the check:* round 1's delivered-change measure, run on pyworld's own
outputs (must pass), gives achieved/requested 0.994–0.998 synthetic and
0.978–0.995 VocalSet, inside round 1's reported 0.989–0.999 and 0.978–1.002;
run on each Rust `id` output against the `c100` request (must fail), it gives
−0.013 to 0.019. *Memory:* the analysis's reported size, 3.67 MB per second,
matches 1025 bins × 2 arrays × 200 frames × 8 bytes plus 48 000 samples × 8
bytes, worked by hand.

**Results.**

| # | Question | Result |
| :--- | :--- | :--- |
| 1 | Time per second of audio in the browser, analysis plus one re-synthesis (median over 8 inputs, min–max) | WORLD-DIO: Chrome 0.163 (0.152–0.183), Firefox 0.140 (0.131–0.161). WORLD-Harvest: Chrome 0.382 (0.336–0.400), Firefox 0.362 (0.323–0.385). Crude PSOLA: 0.007 (0.007–0.008) in both. A 10 s take: 1.3–1.8 s with WORLD-DIO, 3.2–4.0 s with Harvest |
| 2 | Each further step from the same analysis | WORLD synthesis alone 0.036–0.039 s per second in the browsers (stage medians), 0.4 s for a 10 s take: the far vision and the next step cost one analysis and two syntheses. In WORLD-DIO the aperiodicity (D4C) is the largest stage, 0.063–0.081 s per second; in Harvest the f0, 0.230–0.240 |
| 3 | WASM against native | The same crate is 1.5–1.9 times slower in WASM (medians per browser and method; per input 1.48–2.09). `simd128` gains 2–7 % on WORLD and nothing on PSOLA. Native world-rs is faster than round 1's pyworld (DIO 0.089 against 0.154 s per second), so the browser's WORLD-DIO is about as fast as round 1's native C++ |
| 4 | Run-to-run | Slowest of three over fastest: median 0.5–4.5 % per environment and method, at most 26.6 %; in 11 of 12 environment-method cells the widest spread is the first repeat's (compilation tiers). A first full browser run, overwritten by this one when the per-repeat record was added, gave medians within 2 % of these (WORLD-DIO: Chrome 0.160, Firefox 0.140; Harvest: 0.384, 0.360) |
| 5 | Same numbers everywhere? | The c100 output is bit-identical across Chrome and Firefox, plain and `simd128` (one hash per input and method over the four). Against native x86-64 it differs by at most 2.7 × 10⁻¹¹ (WORLD-Harvest), 5.8 × 10⁻¹² (DIO) and 1.1 × 10⁻¹⁶ (PSOLA), at output peaks of at least 0.47 |
| 6 | Does world-rs compute what round 1's WORLD did? (all 43 inputs, native) | DIO plus StoneMask: f0 equal to pyworld's on every frame (max difference 0.0 cents). Harvest: voicing agrees on 98.3–100 % of frames per input, and f0 within 1 cent on all but at most 2.3 % of frames (VocalSet f3), whose differences reach octaves; the waveform then diverges (SNR against pyworld's output below 1 dB on 5 of 19 singers, down to −5.3 dB), since a voicing flip shifts every later pulse. The change delivered is round 1's either way: achieved/requested 0.978–0.998, p95 error 3.3–4.6 cents, gross 0.25–2.8 % (round 1, WORLD: 0.978–1.002, p95 3.0–4.6, gross 2.5–2.8 % on VocalSet) |
| 7 | Does the crude PSOLA deliver the change? (all 43 inputs) | Less well than Praat: achieved/requested 0.958–1.041, p95 error 9.5–9.6 cents synthetic and 16.4–17.0 VocalSet (Praat, round 1: 4.2–5.2), gross 0.03–0.6 %, envelope distance median 0.09–0.42 dB (round 1: 0.03–0.47). Its time is a cost class for PSOLA, not a measurement of a PSOLA good enough to ship |
| 8 | Memory | The WORLD analysis holds 3.67 MB per second of audio as f64 (envelope and aperiodicity 1025 bins each at 200 frames per second); the WASM linear memory reached 221 MiB over the run, whose longest take is 16.8 s |

**What this says for squillo.**

- On-device synthesis is feasible on this laptop in both browsers: WORLD-DIO
  analyses and re-synthesizes a 10 s take in under 2 s on one thread, and
  each further step costs about 0.4 s. VISION §8's first slice needs no
  remote compute for pitch steps of this kind on a device like this one.
- Harvest costs 2.3 to 2.6 times DIO in the browser and gained nothing in
  round 1's delivered change (result 1); DIO plus StoneMask is the cheaper
  WORLD front end, and world-rs reproduces it exactly.
- WASM results are the same in both browsers to the bit, and within
  10⁻¹⁰ of native: an engine test can compare browsers exactly and native
  against WASM with a small epsilon, for these algorithms.
- The analysis is large: 37 MB for a 10 s take in f64, before the engine
  keeps anything else. That matters on phones (parked, `docs/later/mobile.md`)
  and for how long a take the slice accepts.

**Limits.** One CPU, a 2022 laptop i7, one thread: a proxy, and an upper
bound for singers' devices; a device *k* times slower per thread takes *k*
times as long, and no such device was measured. Headless browsers on
Linux; no phones, no Safari. The PSOLA is crude and delivers the change less
precisely than Praat, so its time says what a PSOLA costs, not what a good
one costs. world-rs is one person's port, checked here against pyworld on
43 inputs only. Everything in round 1's limits still holds.

**Needs a human** is unchanged: round 1's listening check (15 minutes) is
the one step left for VISION §12.1.

### Round 3 (open)

The listening ratings; vibrato regularisation; amateur voices; why the
tracker misreads WORLD's output (and whether octave protection in the
tracker or H1 restoration in WORLD fixes it); a PSOLA as precise as Praat's
in WASM; memory held as f32; a slower device.
