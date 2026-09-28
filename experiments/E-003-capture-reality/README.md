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
