# E-008 · Voice Helix: a live three-view voice visualisation on a singer's own device

## Question

Can a singer see their voice's flaws, live, in a way that tells them what to
change, on their own device, from the raw microphone, with nothing leaving the
page? And which of the measures that drive it survive contact with real voices?

## Vision section served

§5 (which aspects can be measured and shown), §6 (capture on the device),
§8 (everything runs on the singer's device).

## What the page is

One HTML file, no dependencies, WebGL2 and Web Audio. Served at
<https://zernox.github.io/squillo-lab/> so that `getUserMedia` runs under
HTTPS (browsers refuse it, or ask differently, on `file://`).
Pages serves the `gh-pages` branch; `.github/workflows/voice-helix-publish.yml`
copies `page/` to its root on every push to `main` that changes the page.
Edit the page on `main` only.

Three stations in one scene, the camera flies between them:

| View | Encodes | Shows |
| :--- | :--- | :--- |
| Pitch helix | angle = pitch class, height = octave, radius = time (12 s) | steadiness, vibrato, scooped onsets, monotone, fry; copper ghost = target note |
| Vocal tract tube | radius profile from LPC formants F1/F2 along a glottis-to-lips path | vowel shape against a target vowel; nasal port glows when A1−P0 is low; floor chart = F1×F2 vowel space |
| Resonance terrain | log-frequency spectrogram as a lit landscape | harmonic ridges, breathiness (noise floor as haze), spectral tilt, harmonic comb at k·f0 |

Capture: AudioWorklet (ScriptProcessor fallback) at raw settings
(`echoCancellation`, `noiseSuppression`, `autoGainControl` all false, as
E-003 found browsers honour). Analysis: a Web Worker at a fixed 20 ms hop
(YIN with a continuity witness, LPC order 2+fs/1000 at 12 kHz, 4096-point
FFT with a 2 s room profile subtracted). Eight flaw detectors with
hysteresis, each paired with one exercise. Session replay with a scrubber.
Two reference-clip slots (`page/ref/polished.mp3`, `page/ref/rough.mp3`,
loaded if present; else chosen by the singer) scored offline and compared
with the singer's last 30 s. The published pair is the first verse of
"Amazing Grace" from two public-domain recordings (`page/ref/SOURCES.md`).

Takes and the coach: "record take" keeps up to 60 s of whatever feeds the
analysis (mic, a demo); "Recording" loads a file of up to 6 min as the take.
The take is cut where the singing stops (silence before and after, pauses
over 2 s shortened to 0.8 s) and where it is not singing (talk, applause, a
jury: 5 s windows whose voiced stretches are short syllables, not held
notes; leading, trailing and inner stretches of 15 s or more are cut), then
scanned offline: spots where a flaw held
(scoops one by one, a scoop being a continuous slide up, not a short note),
marked on a bar, and a summary over the whole take (intonation on the take's
own semitone grid, steadiness inside held notes, slides into notes, tone
clarity), each set against the median conservatory-trained singer, with what
went well and one or two things to work on. Two resyntheses by
pitch-synchronous overlap-add, tone, words and timing untouched: "spotless"
(250 ms running median inside each voiced run, the start of each note held
at its settled pitch, snapped to the grid) and "halfway" (half way from the
take to spotless). The bar is a performance timeline: a sliding line of the
note score over the last 10 s (60 % cents off the grid, 25 % wobble, 15 %
clean start; dashes mark the median trained singer, about 0.8; the line
breaks where 10 s hold under 1 s of held notes), each held note coloured on /
close / off, a star on up to 8 best notes, and the coach's spots underneath;
the card names the strongest and weakest 10 s stretch, and a click on the bar
plays from there. On playback of any version the coaching panel switches to
the flaw 1.5 s before each spot and praises each starred note as it passes. The drawn figure is the coach. A filmed
coach is a feature toggle, off by default: with `?coach=video` in the URL it
plays `page/coach/<pose>.mp4` silently for each exercise that has a clip
(prompts and the import script in `coach/`). An Elo rating against a
reference pool is a second toggle, `?rating=1`, experimental: see
`rating/README.md` for why it is off. To analyse a song with music, remove the
music first with `tools/separate-vocals.sh` (Demucs).

Real-voice demos: 14 VocalSet clips (CC BY 4.0, `page/demo/SOURCES.md`),
one woman and one man each singing the same scale straight, breathy, in vocal
fry, belted and with vibrato, plus "Caro mio ben" straight and with vibrato.

Measured on the rough "Amazing Grace" reference recorded as a 20 s take
(Chrome / Firefox / WebKit, 2026-10-24): scooped onsets per 10 s 2.0 / 2.0 /
2.5 in the take, 0 / 0.5 / 0 in the first "improved you" (since replaced by halfway and spotless); pitch roughness 63 /
70 / 64 ¢ against 40 / 65 / 58 ¢; time flagged shaky 35 / 39 / 39 % against
30 / 26 / 32 %. The resynthesis costs about 2.5 dB of harmonics-to-noise
(18.6 to 16.3 dB in Chrome): it adds a little roughness of its own.

## Hypothesis

A singer who sees the ribbon straighten, the haze sink, or the tube change
shape can act on a flaw faster than from a number. The page is the
instrument for testing that; this experiment does not yet test it.

## Protocol

Not run. What the page has had so far is engineering checks, not an
experiment:

- Headless Chromium (SwiftShader, fake capture device): each of the nine
  synthetic demo voices lights only its own flaw chip; the two healthy ones
  light none. A 220 Hz clip through the fake microphone reads 219.9 Hz
  after calibration.
- The flaw thresholds are hand-set on those synthetic voices (formant-
  filtered sawtooth). None is validated on real singers. The pitch tracker
  here is a prototype YIN, not squillo's measured one (E-002); its
  refusal and continuity rules are not the ones E-002 characterised.

A protocol that would answer the question: ten takes per flaw from real
singers, each flaw labelled by a listener blind to the page, then the
page's per-second flaw state against the labels, with a bar per flaw and
a must-fail case per check (README C1–C10).

## Result

None yet.

## Status

`open`.

## Run

```
python3 -m http.server --directory page 8000
```

then open <http://localhost:8000/>. Chrome and Firefox allow the microphone
on `localhost` without HTTPS. Or push to `main`: the workflow
`.github/workflows/voice-helix-publish.yml` publishes `page/` to GitHub Pages.
