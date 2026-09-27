# E-003 round 1: summary

Browsers: Chrome 154.0.8037.57 (Playwright, channel `chrome`), Firefox 156.0 (snap; Playwright over WebDriver BiDi, channel `moz-firefox`). Headless, on Linux (Ubuntu, PipeWire), i7-12700H. Fake capture only: Chrome's `--use-file-for-fake-audio-capture` with the probe WAV, Firefox's `media.navigator.streams.fake` (a 1 kHz tone). Ranges are over 3 runs of 12 s per condition.

## 1. Readback (S-001)

| Browser | Request | `echoCancellation` | `noiseSuppression` | `autoGainControl` | `channelCount` | `sampleRate` | Other |
| :--- | :--- | :--- | :--- | :--- | ---: | ---: | :--- |
| chrome (fake file 44100 Hz) | raw (ADR 0002) | `false` | `false` | `false` | `2` | `44100` | `applyConstraints` exact mono: OverconstrainedError: Cannot satisfy constraints; `getUserMedia` exact mono: channelCount 2; capabilities: echoCancellation [true, false, "remote-only"], autoGainControl [true, false], sampleRate {"max": 48000, "min": 44100}, channelCount {"max": 2, "min": 1} |
| chrome (fake file 44100 Hz) | default (`audio: true`) | `true` | `true` | `true` | `1` | `48000` | after `applyConstraints` raw: EC True NS True AGC True |
| chrome (fake file 48000 Hz) | raw (ADR 0002) | `false` | `false` | `false` | `2` | `44100` | `applyConstraints` exact mono: OverconstrainedError: Cannot satisfy constraints; `getUserMedia` exact mono: channelCount 2; capabilities: echoCancellation [true, false, "remote-only"], autoGainControl [true, false], sampleRate {"max": 48000, "min": 44100}, channelCount {"max": 2, "min": 1} |
| chrome (fake file 48000 Hz) | default (`audio: true`) | `true` | `true` | `true` | `1` | `48000` | after `applyConstraints` raw: EC True NS True AGC True |
| firefox | raw (ADR 0002) | `false` | `false` | `false` | `1` | not reported | `applyConstraints` exact mono: channelCount 1; `getUserMedia` exact mono: channelCount 1; capabilities: echoCancellation [false], autoGainControl [false], channelCount {"max": 1, "min": 1} |
| firefox | default (`audio: true`) | `false` | `false` | `false` | `1` | not reported | after `applyConstraints` raw: EC False NS False AGC False |

## 2. Signal: what arrives at the worker (S-002)

Measured against an ideal converter: the source loop itself at the same rate, else its exact band-limited (FFT) resampling. *Steps*: lag changes over 1 sample between 0.1 s windows, negative where samples were inserted into the capture, positive where dropped; *drift*: steady rate difference outside steps. Tone rows: 0.4 s of each of 110, 220, 440, 880 Hz; the worst over tones and runs. *Ideal SNR*: the window's energy over its residual after least-squares gain and fractional lag.

| Browser | Path | Source → context (Hz) | Bit-exact windows | Steps per run (samples) | Drift (ppm) | Tone error (cents) | Tone THD+N (dB) | Ripple 80 Hz–8 kHz (dB) | Ripple 8–20 kHz (dB) | Alias / image (dB) | Ideal SNR, median (dB) | Ideal SNR, sweep < 8 kHz, min (dB) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| chrome | fake microphone | 44100 → 44100 | 0 of 179 (fraction of exact samples 0.50) | none; none; none | -0.0 to 0.0 | max abs 4.2e-06 | -85.9 | 0.000 | 0.000 | — | 96.0 to 96.2 | 96.2 |
| chrome | fake microphone | 44100 → 48000 | — (rates differ) | none; none; none; none; none; none; none; none; none; none; none; none; none; none; none | -0.0 | max abs 4.2e-06 | -86.3 to -86.2 | 0.001 | 0.003 | image -75.6 | 77.8 to 79.7 | 86.7 to 87.1 |
| chrome | fake microphone | 48000 → 44100 | — (rates differ) | -102; -102; -102 | -0.0 to 0.0 | max abs 1.6e-06 | -87.2 to -86.5 | 0.133 | 0.298 | alias -84.1 | 80.4 to 82.4 | 88.5 to 88.7 |
| chrome | fake microphone | 48000 → 48000 | — (rates differ) | -480, -111; -111; -111; -111; -111; -111; -111; -111; -111; -111; -111; -111; -111; -111; -111 | -0.0 to 0.0 | max abs 1.6e-06 | -87.2 to -86.5 | 0.133 | 0.301 | — | 75.8 to 77.5 | 84.1 to 84.8 |
| chrome | track from a second context | 44100 → 48000 | — (rates differ) | none; none; -480 | -0.0 to 0.0 | max abs 4.2e-06 | -86.4 to -86.3 | 0.001 | 0.003 | image -75.6 | 77.9 | 87.7 |
| chrome | track from a second context | 48000 → 44100 | — (rates differ) | -441; -441; -441 | 0.0 | max abs 2e-06 | -87.3 to -86.5 | 0.001 | 0.003 | alias -84.1 | 91.3 to 92.6 | 85.7 to 86.6 |
| chrome | track from a second context | 48000 → 48000 | 183 of 183 | none; none; none | -0.0 to 0.0 | max abs 1.6e-06 | -86.2 to -85.9 | 0.000 | 0.000 | — | 110.8 to 112.5 | 111.0 to 112.5 |
| firefox | fake microphone (1 kHz tone) | 48000 (graph) → 44100 | — | phase deviation max 0.00 to 43.01 samples | — | 0.000 to 0.098 | -70.8 to -8.1 | — | — | — | — | — |
| firefox | fake microphone (1 kHz tone) | 48000 (graph) → 48000 | — | phase deviation max 0.00 samples | — | -0.000 to 0.000 | -75.9 | — | — | — | — | — |
| firefox | track from a second context | 44100 → 48000 | — (rates differ) | +3.8, +5.0, -1.3; -4.2, -29, -1.1, -1.1, -1.1, -1.1, -15; +7.2 | -25.4 to 2.9 | max abs 0.27 | -65.0 to -64.9 | 0.012 to 0.023 | 2.021 to 2.048 | image -16.0 to -15.5 | 19.5 to 29.4 | 15.3 to 21.9 |
| firefox | track from a second context | 48000 → 44100 | — (rates differ) | -9.8, -3.9, -35, +2.5; -11, -4.3, +4.1, -39, +2.4; -11, -5.2, -65, +1.1 | -13.2 to -7.1 | max abs 0.94 | -78.4 to -73.5 | 0.046 to 0.048 | 2.706 to 2.710 | alias -17.0 to -16.2 | 15.4 to 20.1 | 10.1 to 12.5 |
| firefox | track from a second context | 48000 → 48000 | 181 of 181 | none; none; none | -0.0 to 0.0 | max abs 1.6e-06 | -86.2 to -85.9 | 0.000 | 0.000 | — | 110.6 to 115.8 | 111.7 to 113.6 |

## 3. Transport: worklet to worker, one message per 128-sample block (S-003)

*Load*: CPU time the worker burns per block, as a fraction of the block period (2.667 ms at 48 kHz); *utilisation*: the service time actually measured over the period. *Arrival lag*: arrival time minus the block's audio time, less the smallest such value in the run. *Behind at end*: how far the worker's finished work trailed the audio when capture stopped.

| Browser | Path | Context (Hz) | Load | Utilisation | Blocks | Lost | Reordered | Quanta skipped | Arrival lag p50 / p99 / max (ms) | Behind at end (ms) | Timer resolution (ms) |
| :--- | :--- | ---: | ---: | :--- | :--- | ---: | ---: | ---: | :--- | :--- | :--- |
| chrome | mic 44100 | 44100 | 0.00 | 0.00 | 4132 to 4133 | 0 | 0 | 0 | 11.1 to 11.4 / 19.9 to 20.0 / 20.8 to 21.6 | 7 to 9 | 0.100 |
| chrome | mic 44100 | 48000 | 0.00 | 0.00 | 4500 | 0 | 0 | 0 | 4.5 to 5.3 / 8.8 to 9.1 / 9.0 to 9.7 | 1 | 0.100 |
| chrome | mic 44100 | 48000 | 0.50 | 0.52 to 0.53 | 4500 | 0 | 0 | 0 | 2.4 to 2.5 / 4.6 to 4.8 / 4.8 to 5.0 | 0 to 1 | 0.100 |
| chrome | mic 44100 | 48000 | 0.75 | 0.75 | 4500 | 0 | 0 | 0 | 1.5 to 1.6 / 2.8 to 2.9 / 3.0 to 5.7 | 0 to 1 | 0.100 |
| chrome | mic 44100 | 48000 | 0.90 | 0.94 | 4500 | 0 | 0 | 0 | 0.8 to 1.0 / 1.3 to 1.5 / 1.6 to 4.6 | 1 | 0.100 |
| chrome | mic 44100 | 48000 | 1.50 | 1.50 | 4500 to 4504 | 0 | 0 | 0 | 3002.4 to 3003.2 / 5943.0 to 5944.8 / 6003.0 to 6004.8 | 6003 to 6005 | 0.100 |
| chrome | mic 48000 | 44100 | 0.00 | 0.00 | 4133 | 0 | 0 | 0 | 11.1 to 11.5 / 19.9 to 20.3 / 21.1 to 21.3 | 6 to 7 | 0.100 |
| chrome | mic 48000 | 48000 | 0.00 | 0.00 | 4500 to 4504 | 0 | 0 | 0 | 4.6 to 6.3 / 8.9 to 20.5 / 9.1 to 29.0 | 1 | 0.100 |
| chrome | mic 48000 | 48000 | 0.50 | 0.53 | 4500 | 0 | 0 | 0 | 2.6 to 2.7 / 4.4 to 7.7 / 6.5 to 37.6 | 0 to 1 | 0.100 |
| chrome | mic 48000 | 48000 | 0.75 | 0.75 | 4500 | 0 | 0 | 0 | 1.4 to 1.5 / 2.6 to 2.9 / 2.8 to 19.1 | 0 | 0.100 |
| chrome | mic 48000 | 48000 | 0.90 | 0.94 | 4500 | 0 | 0 | 0 | 0.8 to 0.9 / 1.4 to 35.4 / 1.6 to 42.6 | 0 to 1 | 0.100 |
| chrome | mic 48000 | 48000 | 1.50 | 1.50 | 4500 | 0 | 0 | 0 | 3000.1 to 3003.4 / 5940.3 to 5943.9 / 6000.3 to 6004.0 | 6000 to 6004 | 0.100 |
| chrome | stream 44100 | 48000 | 0.00 | 0.00 | 4500 | 0 | 0 | 0 | 4.4 to 4.7 / 8.7 to 8.9 / 8.9 to 9.3 | 0 to 1 | 0.100 |
| chrome | stream 48000 | 44100 | 0.00 | 0.00 | 4133 | 0 | 0 | 0 | 11.1 to 11.5 / 19.7 to 20.2 / 20.9 to 21.3 | 7 | 0.100 |
| chrome | stream 48000 | 48000 | 0.00 | 0.00 | 4500 | 0 | 0 | 0 | 4.6 to 5.3 / 8.7 to 8.9 / 9.0 to 11.5 | 0 to 1 | 0.100 |
| firefox | mic  | 44100 | 0.00 | 0.00 | 4230 to 4282 | 0 | 0 | 0 | 6.5 to 6.6 / 12.0 to 12.2 / 12.8 to 13.9 | 2 to 4 | 1.000 |
| firefox | mic  | 48000 | 0.00 | 0.00 | 4624 to 4696 | 0 | 0 | 0 | 5.3 to 5.7 / 10.3 to 10.7 / 11.0 to 11.3 | 2 | 1.000 |
| firefox | mic  | 48000 | 0.50 | 0.75 | 4540 to 4696 | 0 | 0 | 0 | 2.3 to 2.7 / 4.3 / 5.3 to 6.0 | 1 to 2 | 1.000 |
| firefox | mic  | 48000 | 0.75 | 0.75 | 4516 to 4692 | 0 | 0 | 0 | 2.3 to 2.7 / 4.3 to 4.7 / 5.0 to 6.3 | 1 to 2 | 1.000 |
| firefox | mic  | 48000 | 0.90 | 1.12 | 4528 to 4532 | 0 | 0 | 0 | 754.5 to 757.2 / 1493.9 to 1497.2 / 1509.0 to 1512.3 | 1509 to 1512 | 1.000 |
| firefox | mic  | 48000 | 1.50 | 1.50 | 4532 | 0 | 0 | 0 | 3020.7 to 3021.7 / 5980.9 to 5981.9 / 6041.3 to 6042.3 | 6041 to 6042 | 1.000 |
| firefox | stream 44100 | 48000 | 0.00 | 0.00 | 4616 to 4700 | 0 | 0 | 0 | 5.7 to 6.0 / 10.7 to 11.0 / 11.3 to 12.7 | 2 | 1.000 |
| firefox | stream 48000 | 44100 | 0.00 | 0.00 | 4248 to 4285 | 0 | 0 | 0 | 6.3 to 7.1 / 11.8 to 12.7 / 12.8 to 14.9 | 3 to 4 | 1.000 |
| firefox | stream 48000 | 48000 | 0.00 | 0.00 | 4696 to 4700 | 0 | 0 | 0 | 5.3 to 5.5 / 10.0 to 10.3 / 11.0 to 12.3 | 1 to 2 | 1.000 |
