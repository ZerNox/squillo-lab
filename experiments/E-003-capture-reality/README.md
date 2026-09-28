# E-003 — Capture reality in browsers

**Status:** needs-human (round 1 automated, fake devices; the real-microphone step is left) · **Serves:** VISION §6 (honesty), §12.3 · Absorbs squillo S-001, S-002 and S-003

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

## Round 1 as run (squillo iteration 26)

**Conditions.** Chrome 154.0.8037.57 (Playwright, channel `chrome`) and
Firefox 156.0 (snap; Playwright over WebDriver BiDi, channel `moz-firefox`),
headless, on Linux (Ubuntu, PipeWire), i7-12700H, 2026-09-27. No real
microphone: Chrome's `--use-file-for-fake-audio-capture` plays the probe WAV
as its microphone; Firefox's `media.navigator.streams.fake` gives a 1 kHz
tone. A second path, *stream*, plays the probe from an `AudioBufferSource`
in one context into a `MediaStreamDestination`, and captures that track in a
context at another rate; it tests the browsers' own rate conversion with a
known input in both browsers. `page/tap.js` is ADR 0006's capture worklet
(one message per 128-sample quantum, buffer transferred);
`page/engine.js` stands in for the engine worker and burns a set CPU time
per block. 24 conditions, 3 runs of 12 s each, 72 runs, 321 762 blocks.

**The probe** (`gen.py`, S15): one 8 s loop, the same at 48 000 and
44 100 Hz: digital silence; an exponential sweep 50 Hz–20 kHz; pure tones
110, 220, 440 and 880 Hz (inside ADR 0007's E2–C6); a tone above the lower
rate's Nyquist (23 kHz at 48 kHz) or one whose image falls inside the higher
rate's band (21 kHz at 44.1 kHz); white noise band-limited to 20 kHz, RMS
0.05. 16-bit, peak 8192. `gen.py` asserts each condition on its output and
writes the measured values to `results/probe_checks.json` (tones within
0.005 Hz of nominal; noise RMS 0.04998; noise energy above 20.5 kHz −83.3
and −85.4 dB; silence exactly zero).

**Analysis** (`analyze.py`, `report.py`). Each capture is aligned to the
looped probe: at the same rate against the probe itself, at another rate
against its exact band-limited (FFT) resampling, i.e. an ideal converter.
0.1 s windows over the aperiodic parts (sweep above 1 kHz, noise) give the
lag to a hundredth of a sample. A change of lag over one sample between
windows is a *step*: negative where samples were inserted into the capture,
positive where dropped. Each step is bracketed by the tracked windows either
side, in capture time and in the loop's own time. Tones are fitted by least
squares for frequency, level and THD+N. Tables: `results/summary.md`; per
run: `results/runs.json`; readbacks: `results/raw/`. Raw captures stay in
`data/cache/` (not committed; `node run.mjs` remakes them).

## Result

Round 1 answers S-001, S-002 and S-003 for the browsers' own pipelines on
fake devices. What a real microphone, driver and room do is the
`needs-human` step below.

1. **Readback (S-001).** Asked for ADR 0002's raw request, both browsers
   report `echoCancellation`, `noiseSuppression` and `autoGainControl` as
   `false`. Firefox's fake device can do no processing (its capabilities
   list only `false`), so its answer is trivially true here. Chrome's is
   not: with a plain `audio: true` request it turns all three on, and
   `applyConstraints` with the raw request afterwards leaves all three on
   in the readback. Only the request made at `getUserMedia` takes effect.
2. **Channel count.** Chrome ignores `channelCount: 1` as an ideal
   constraint and reports and delivers 2 channels; `applyConstraints` with
   `channelCount: {exact: 1}` fails with `OverconstrainedError`, and
   `getUserMedia` with the same exact constraint succeeds and still reports
   2. The two channels were identical in every block of all 45 Chrome runs.
   Firefox reports and delivers 1. Under ADR 0002, which marks a take *not
   raw* when the read-back channel count differs from the request, every
   Chrome take here would be marked not raw on channel count alone.
3. **Rate readback.** Chrome reports `sampleRate` (44 100 for the raw
   request on both fake files, 48 000 for the default request: the fake
   device switches rate with the processing). Firefox reports neither
   `sampleRate` nor `latency`.
4. **Rate mismatch is accepted (S-002).** Neither browser throws when a
   track is connected to a context at another rate, in either direction
   (Chrome 154, Firefox 156), so ADR 0002's refusal on a throw never fires
   in these releases.
5. **Chrome converts transparently in the voice band.** On every
   cross-rate path (fake device at 44.1 kHz into a 48 kHz context, and the
   stream path in both directions; 21 runs): tone frequency within
   4.3 × 10⁻⁶ cents and level within 0.0002 dB of the probe's, no drift
   (0.0 ppm), ripple at most 0.001 dB over 80 Hz–8 kHz and 0.003 dB over
   8–20 kHz, residual against an
   ideal converter over sweep windows below 8 kHz at least 85.7 dB down;
   the 23 kHz tone aliases at −84.1 dB, the 21 kHz tone's image is at
   −75.6 dB. At equal rates the stream path is bit-exact (183 of 183
   windows); the fake device's own int16 path at 44.1 kHz is not
   (residual −96 dB, 16-bit quantisation). Silence stays digital zero on
   every path: nothing adds noise or dither.
6. **Chrome inserts 10 ms of samples, rarely.** In 2 of the 36 Chrome runs
   into a 48 kHz context, 480 samples (10 ms) were inserted once, 1.85–1.95
   s after capture began, and never later; both brackets (loop time
   1.73–1.87 and 1.83–1.97 s) are clear of any loop point. In all 3 stream
   runs from 48 kHz into a 44.1 kHz context, 441 samples (10 ms) were
   inserted once in a 7.4 s bracket between 2.1 and 9.5 s with no tracked
   window inside, whose loop time wraps (2.12 → 1.51 s) through the stream
   source's own loop point (`page/probe.js`, `src.loop = true`). By S17
   those 3 are the input path's until a run without a loop clears them, so
   Chrome is shown to insert in **2 of 45** runs, not 5 (corrected at
   squillo R-06, iteration 30; the first write-up counted all 5). No sample
   was dropped in any Chrome run. For
   pitch a 10 ms insertion is a discontinuity, not a frequency error; for
   anything timed across it (vibrato rate, note durations) it is 10 ms.
7. **Not the browser: the fake file's loop.** In all 18 fake-microphone
   runs on the 48 kHz file (the device then running at 44.1 kHz),
   102 device samples (−111 at 48 kHz, −102 at 44.1 kHz) were inserted in
   the bracket that holds the file's loop point (loop time 7.73–1.53 s),
   and nowhere else; with the 44.1 kHz file, none. This is Chrome's fake
   file reader resampling at its end of file, not capture; those runs'
   ripple (0.13 dB below 8 kHz) is likewise the reader's, and they are not
   used for item 5.
8. **Firefox bridges a rate mismatch with drift correction, and it costs
   pitch.** When the context's rate differs from the track's (stream path,
   both directions; fake microphone into a 44.1 kHz context), Firefox does
   not convert at a fixed ratio. The time base wanders: net −85 to +8
   samples over a run, steps up to 65 samples between tracked windows
   (−1.14 samples per 0.15 s, 160 ppm, through one stretch; −65 samples
   over 4.25 s, 350 ppm, in another). Tone frequency
   errs by up to 0.94 cents (48 → 44.1 kHz) and 0.27 cents (44.1 → 48 kHz)
   over 0.4 s tones, 4 tones × 3 runs each; the residual against an ideal
   converter below 8 kHz is only 10–22 dB down, from the timing wander, not
   noise; ripple 8–20 kHz 2.0–2.7 dB; alias and image only 16–17 dB down
   (above 20 kHz, outside the voice band). One of the 3 fake-microphone runs
   into a 44.1 kHz context had a discontinuity (the 1 kHz tone's phase off
   by 43 samples; THD+N −8 dB over its first 2 s). At equal rates Firefox is
   bit-exact on the stream path (181 of 181 windows) and exact on the fake
   microphone (1000.000 Hz, phase steady to 0.00 samples, 15 runs). Because
   Firefox reports no track rate (item 3), squillo cannot see from the
   readback when this path is taken.
9. **Transport is lossless (S-003).** Across 72 runs and 321 762 blocks,
   no block was lost, reordered or duplicated, and no render quantum was
   skipped (the worklet's `currentFrame` advanced by exactly 128 every
   time). With no loss in 321 762 blocks, the loss rate per block is below
   9.3 × 10⁻⁶ at 95 % confidence (rule of three). This holds with the
   worker loaded at 50 %, 75 %, 90 % and 150 % of the block period.
10. **Load shows as backlog, not loss.** At utilisation up to 0.94 the
    worker ends at most 9 ms (Chrome) or 4 ms (Firefox) behind the audio,
    and the p99 arrival lag is 1.3–35 ms (Chrome) and 4.3–12.7 ms
    (Firefox). At 150 % the queue grows as queueing predicts, 6.0 s behind
    after 12 s in both browsers, and still nothing is lost. Firefox's
    worker clock ticks in 1 ms steps, which coarsens its timings and made
    the nominal 90 % load run at 112 %: 1.51 s behind after 12 s. The
    engine's budget is therefore on average throughput, with memory for
    the backlog, not on each block's deadline.

**Hypothesis.** Partly held. Both browsers report all three flags
(on fake devices). Rate conversion is transparent for pitch in Chrome
(under 10⁻⁵ cents) but not in Firefox's drift-corrected bridge (up to
0.94 cents, a third of `signal`'s ±3-cent tolerance). Neither browser
refused a mismatch, and Chrome ignores the mono request.

**Uncertainty and limits.** Fake devices only, headless, one Linux
machine, one release of each browser; three runs per condition. Whether a
real device's graph runs at another rate than a 48 kHz context in Firefox,
and so takes item 8's path, is not measured here; nor is processing below
the browser (OS, driver, firmware), which `getSettings()` cannot see (ADR
0002). Safari and Edge are not testable on this machine. Items 6 and 8 are
counts from 3 to 36 runs; their rates are not estimated beyond that.

## For squillo

Folded in squillo iteration 32 (F-027): ADR 0002 revised through Q-018,
ADR 0006 keeps one message per block, and the new `capture` spec
(CA-001 to CA-008) tests on the fixtures below. What browser processing
does to a measure is unmeasured (squillo F-034, a candidate round 2).

- ADR 0002: request raw at `getUserMedia`, never by `applyConstraints`
  later (item 1). The channel-count readback rule marks every Chrome take
  not raw (item 2); a rule that checks the channels' content (identical
  channels are mono) would not. The rate refusal never fires (item 4).
  Firefox's bridge (item 8) is invisible to the readback; the default
  `AudioContext` rate, recorded by the `needs-human` page, is a candidate
  signal for it.
- ADR 0006: one message per block loses nothing here; the risk is a
  backlog when the engine is slower than real time (items 9, 10), so
  S-003's fallback (ring buffer or batching) is not needed on this
  evidence.
- `signal`, `metrics`: a take may contain one 10 ms insertion (item 6),
  and in Firefox up to 0.94 cents of pitch error from the bridge (item 8).

## Fixtures for squillo `capture` (squillo iteration 32)

`fixtures.py` writes the twelve capture traces squillo's first `capture`
spec names (`squillo/fixtures/capture/`, F-027's fold): `uv run python
fixtures.py ../../../squillo/fixtures/capture`, under a second. Five
readbacks are round 1's own records with `deviceId` and `groupId` removed
(Chrome raw at a 44.1 kHz track into a 48 kHz context; Firefox raw, no
track rate; a Firefox stream track that reports no flag at all; Chrome's
readback with no processing constraints, context rate written as 48 000;
Chrome into a 44.1 kHz context). Seven are constructed block and event
traces on the Chrome raw readback: two channels that differ, with samples
beyond [−1, 1]; the singer's stop; the track ended; the track muted; the
context suspended; one render quantum skipped; the engine worker failing.
The trace format is described in `squillo/fixtures/MANIFEST.md`.

Checks (S15), in `results/fixtures.json`: 8 checks of the checks, each on
a case it must pass and one it must fail (the tier rule on Chrome's
recorded raw and default readbacks, one flag missing, voice isolation on;
the gap rule on consecutive and skipped quanta; f32 exactness on 0.75 and
0.1); 100 conditions asserted on the fixtures as written (no device
identifier, each derived readback equal to its record, 128 samples per
channel, every sample exact in `f32`, the channels differ, one quantum
skipped where intended and none elsewhere); and a toy model of the spec's
requirements on every fixture, against outcomes written from the
scenarios before it ran: 12 of 12 agree. The model is a check, not a
design: crude and never built on.

**Iteration 43** (squillo F-039, `capture` CA-010). A thirteenth trace,
`events-start-after-load.json`: the singer's-stop trace preceded by
`page-loaded` and `singer-start`. The model now opens nothing before a
`singer-start` where a trace has one (the twelve earlier traces have none
and start at once, as before) and records the release at the singer's
stop or an end of input. Four more checks of the checks (a block before
the start caught, none after it; released at the stop, not while the run
goes on), 12 in all; 113 conditions; 13 of 13 outcomes as the scenarios
state, `events-track-ended.json` now also expected released. The twelve
earlier files regenerate byte for byte.

**Iteration 46** (squillo F-049, `capture` CA-005, CA-009). When can the
processing notice be given, now that the microphone opens only in the
singer's start (CA-010)? Round 1's `page/probe.js` reads the track's
settings (line 60) before it creates the audio context (line 62) and
connects the tap (line 80), so in all 72 runs of `results/runs.json` the
readback existed before any block could be rendered; 63 of them hold a
non-empty readback and a tap record, the 9 Firefox stream tracks an empty
one. A fourteenth trace, `events-start-processed.json`:
`events-start-after-load.json`'s events under
`readback-chrome-processed.json`'s readback (asserted equal to both, and
not raw). The model now records its notices: the capture condition at
`page-loaded`, before anything opens (at the trace's start where a trace
has no load), and, for a take that is not raw, the processing notice in
the singer's start, with the number of blocks delivered at that moment.
The expected outcomes were committed before the model ran (`33b22cb`,
L-041): the processed start trace gives the condition at the load and the
processing notice before its first block; the raw one the condition only.
Four more checks of the checks, 16 in all: the processing notice before
the first block on Chrome's recorded default readback; none on its raw
readback, the must-fail case differing in its input; the condition at the
load, and at the trace's start where there is no load. A mutant that gives
the notice one block late fails the first of them (run by hand, not kept).
127 conditions; 14 of 14 outcomes as the scenarios state. The thirteen
earlier files regenerate byte for byte.

## Round 2: what browser processing does to the measures (squillo iteration 47)

**Question** (squillo F-034 (a), R-09's focus for iteration 47). When a take
is captured *not raw*, with the browser's echo cancellation, noise
suppression and automatic gain control on, how far are squillo's measures
moved, and by how much would their ± have to widen to stay honest? Round 1
found that Chrome's fake microphone reports all three flags on for a plain
request; a pilot in this iteration (one E-002 re-synthesis, 8 s) found it
also applies them: the plain request's capture was 8.7 times the raw one's
level and reached full scale. So the question can be asked of Chrome
without a microphone. Serves `VISION.md` §6 (never fake precision), §12.2,
§12.3.

**Rules, written and committed before the run** (S15; `r2_gen.py`,
`r2_run.mjs`, `r2_measures.py` hold them in code).

1. *Inputs* (`r2_gen.py`). The 80 long-tone takes of E-002 round 2 (sets
   LT-straight, LT-forte, LT-pp, LT-messa, 20 VocalSet singers; WORLD
   re-syntheses with a known f0, `E-002 r2_truth.py`), because held notes,
   which the take measures need, are found in them. Each under two input
   conditions, read from E-002's code (`r2_run.py` `condition()`, lines
   97–119, its seed per file and condition): *clean*, and *white-20*,
   white noise at 20 dB SNR over the voiced samples. Each is scaled so that
   the clean voice's RMS over its voiced samples (truth f0 > 0) is −26 dBFS,
   the nominal active speech level of ITU-T P.56 test signals, and padded
   with 1.0 s of digital silence before and after; 48 kHz, 16-bit PCM, as
   round 1's probe. Asserted on each written file, read back: peak below
   full scale; the voiced RMS within 0.05 dB of −26 dBFS; the SNR within
   0.05 dB of 20 (the 16-bit rounding moves it); the pads exactly zero; the
   read-back samples within one 16-bit step of the float signal.
2. *Captures* (`r2_run.mjs`, `page/r2.js`). Chrome 154, headless, the WAV
   as `--use-file-for-fake-audio-capture`, round 1's capture path (the
   `tap.js` worklet, one message per block, `engine.js` at load 0), a
   48 kHz context, captured for the WAV's length plus 0.5 s. Requests: *raw*
   (the three flags off, as ADR 0002) and *default* (a plain `audio: true`,
   all three on) on every input; *ec*, *ns* and *agc* (one flag on, two
   off) on the 20 LT-straight takes under both conditions. The readback
   (`getSettings()`) is kept per capture. Firefox is not run: its fake
   device is a 1 kHz tone, not a file.
3. *Alignment* (`r2_measures.py`). The capture's first channel is aligned to
   its input WAV by the lag of the cross-correlation's peak over the whole
   overlap, then the lag is re-measured in each 1 s window with enough
   energy; a window whose lag differs from the whole's by more than one
   sample is an anomaly, recorded with its position in the input (S17: the
   file's start and end are its loop points). A capture with an anomaly is
   kept for the per-frame measures only in its windows at the whole's lag,
   and left out of the take measures. Samples the capture does not cover
   (the start the fake device played before the worklet connected) have no
   frames.

   *3a, revised after the timing sample (S19: 16 captures, 4 takes, raw and
   default, clean and white-20) and before the full run.* As first written,
   the per-window test cannot tell processing from a timing fault: in the
   sample every usable raw window sat at the whole lag (0 of 89 shifted), but
   processed windows shifted by 1 to 4 samples (the processing's phase),
   and single windows of steady tones jumped by whole pitch periods (173
   and 362 samples), where a steady tone's cross-correlation has a peak
   every period. An inserted or lost block shifts every later window. So
   now: a window is *usable* when the capture correlates with it at 0.8 or
   more at its own lag; an *anomaly* is a usable window shifted from the
   whole lag by 64 samples or more (half a 128-sample render quantum, the
   least a block fault moves) whose next usable window has the same shift
   within 2 samples. A capture with an anomaly is left out of both
   analyses and counted with the anomaly's position. A shift under 64
   samples moves the truth by under 1.4 ms; the truth moves a median 0.47
   cents per 0.5 ms (p95 3.0) at Harvest's 1 ms steps over the 80 takes.
   Checks: the input against itself, no anomaly; the input through a
   first-order allpass (a 3-sample group delay, as processing's phase), no
   anomaly; 480 zero samples inserted at 5 s, anomalies found, all in the
   stretch before 5 s that sits at the other lag (the whole lag is the
   longer part's).
4. *Measures*, on the aligned capture and, as the reference, on the input
   WAV itself (*direct*), with squillo's pipeline as E-002 fold 2 has it:
   YIN at squillo's frame axis (`E-002 yin.py`), MT-003's *u* table
   (`E-002 results/fold2.json` `measures.spec.table`), the held notes found
   from the measured contour (`fold2.py` `held_notes`), and the take
   measures steadiness, vibrato extent and vibrato rate with their take ±
   (`blocks`, `take`, with `measures.spec` *c* and κ). Per frame: a frame is
   valid by E-002's rule (`r2_run.py` `frame_truth`: every truth sample of
   its window voiced, inside E2..C6, moving at most 200 cents), its truth at
   SG-007's instant; reported per request and input: the share of valid
   frames accepted (a pitch and a finite *u*), the p95 of |error| over
   accepted valid frames, and the coverage of ±2*u*. Per take: each
   measure's value and ± on the capture and on the direct input, and on
   the truth contour over the same frames where every frame is valid.
5. *What processing does.* Per request and input, against direct on the
   same input and frames: (a) the change in accepted share and in coverage;
   (b) the **per-frame widening factor** *w*: the least *w* (on a 0.01 grid
   from 1) for which the capture's coverage of ±2*w u* reaches direct's
   coverage of ±2*u* on the same input; (c) per take measure, the share of
   takes whose capture value differs from direct's by more than direct's
   ±2*u*, and the least factor *w*_take by which the capture's ± must be
   multiplied so that it covers the truth on as many takes as direct's
   does; (d) the share of takes measured on direct that the capture leaves
   unmeasured, and the reverse. Uncertainty: 95 % percentile intervals from
   1000 bootstrap resamples of the 20 singers.
6. *Bars, written before the run.* The **reference condition that must
   pass**: raw against direct, per frame, a coverage within 1 point of
   direct's and *w* = 1.00; per take, no take measure moved beyond direct's
   ±2*u* on more than 5 % of takes. If raw fails, the capture path itself
   moves the measures; that is reported, and processing is then compared
   with raw instead. **Processing widens** a measure when the lower end of
   *w*'s interval (or *w*_take's) is above 1.00. A factor is reported for
   squillo only with its interval, and only from the requests the readback
   can name (ADR 0002: the readback says which flags were on).
7. *Checks of the checks* (run before the captures, on inputs that differ
   from the must-pass ones). Alignment: the input WAV aligned to itself
   must give lag 0 and no anomaly; the same WAV with 480 samples (10 ms, as
   round 1's insertion) of zeros inserted 5 s in must give an anomaly
   there. The widening factor: direct against itself must give *w* = 1.00;
   direct's errors multiplied by three against direct's own *u* must give
   *w* above 1. The take comparison: direct against itself must move no
   take; direct against the same input with a 60-cent 5 Hz sine added to
   its measured contour must move vibrato extent on at least one take.
   (First written with 20 cents, and run before this rule was committed:
   on `f1_long_straight_a` it moved extent from 32.1 to 37.4 cents, inside
   direct's ±7.4, as it must, since extents add in quadrature,
   √(32.1² + 20²) ≈ 37.8; so 20 cents was not a case the check must fail.
   At 60 cents the expected extent is √(32.1² + 60²) ≈ 68, a move of about
   36 cents.)

**Time** (S19, measured on the pool before the full run). 440 captures:
raw and default on 160 inputs, and ec, ns, agc on the 40 LT-straight
inputs; 5815 s of capture in all (each WAV's length plus 0.5 s). The
sample, 16 captures of the full run's own jobs (231.9 s of capture), took
60 s of wall time at 4 parallel browsers, 0.26 s of wall per second of
capture, so the full run is about 25 min, run in steps of 150 jobs, each
resuming from the captures already written. The analysis, one process per
capture on a pool of 16, is timed on the sample below.

```
uv run --project ../E-002-measurement-reliability python r2_gen.py            # 7 s: 160 WAVs and truths -> data/cache/r2/in, results/r2/inputs.json
uv run --project ../E-002-measurement-reliability python r2_measures.py checks  # 5 s: rule 7 -> results/r2/checks.json
node r2_run.mjs --jobs 4 --only 150    # then --only 300, then without --only: about 25 min in all -> data/cache/r2/cap
uv run --project ../E-002-measurement-reliability python r2_measures.py         # -> results/r2/analysis.json
```

## Needs a human (15 minutes)

Real microphones, drivers and rooms, which fake devices cannot show.

1. `uv run python gen.py` (makes `data/cache/tone440.wav`), `npm ci`,
   `node serve.mjs`; copy `tone440.wav` to a phone (3 minutes).
2. Open `http://localhost:8003/` in Chrome with the laptop's own
   microphone, press *Start*, stay quiet for 10 s, then play the tone from
   the phone about 30 cm away until the page says done; two files download.
   Repeat in Firefox (6 minutes).
3. `uv run python human.py e003-human-chrome.json e003-human-firefox.json`
   writes `results/human-<browser>.json`: readback, default context rate,
   channel count, blocks lost, noise floor, the tone's frequency error in
   cents and its phase steadiness (2 minutes).
4. Commit `results/human-*.json`, never the `.f32` audio (1 minute).
