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
FFT with a 2 s room profile subtracted). Takes get their own pitch track:
every frame keeps up to 8 YIN candidates and a Viterbi path over the whole
take picks one (pYIN, Mauch & Dixon 2014, simplified: dip + 0.3 per octave
below the highest candidate + 0.035 per semitone jumped, unvoiced 0.45,
voicing switch 0.25). Measured with the page's code (`check/pitch-bench.mjs`,
held-out seed 4242, 29 328 voiced frames, 5 voice types from bass 82 Hz to
soprano 880 Hz × clean, breathy, weak fundamental, ±100 ¢ vibrato,
untrained drift): gross error (>50 ¢) 1.4 % live → 0.1 % take, octave
errors 0.8 % → 0.1 %, missed voiced frames 0.0 % → 0.3 %, median error
1.5-7.4 ¢ per cell; worst cell after: soprano breathy, 5.2 % missed.
Before this, takes were fed in 43 ms chunks, so pairs of frames saw the
same audio: 10.9 % gross error on the same benchmark (seed 11). Synthetic
voices only; real-voice ground truth (VocalSet has none for f0) is open. Eight flaw detectors with
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
went well (a slide style, two thirds or more of the notes slid into by the
same depth within 20 %, is praised as a style and not marked down) and one or two things to work on. On a phone the scanned take comes first (play row, bar,
summary, progress) and the page scrolls to it. Two resyntheses by
pitch-synchronous overlap-add, tone, words and timing untouched: "spotless"
(250 ms running median inside each voiced run, the start of each note held
at its settled pitch, snapped to the grid) and "halfway" (half way from the
take to spotless). The bar is a performance timeline: a sliding line of the
note score over the last 10 s (60 % cents off the grid, 25 % wobble, 15 %
clean start; dashes mark the median trained singer, about 0.8; the line
breaks where 10 s hold under 1 s of held notes), each held note coloured on /
close / off, a star on up to 8 best notes, and the coach's spots underneath;
the card names the strongest and weakest 10 s stretch, and a click on the bar
plays from there; a click on a note or a spot loops it A/B, 0.5× keeps the pitch: your note, 0.5 s,
the same moment spotless, 1 s (padded 0.4 s, capped at 4 s), until clicked again. A speed menu (1×, 0.75×, 0.5×) slows the take, halfway,
spotless and the A/B loop without changing pitch (WSOLA, 40 ms grains, ±8 ms
search). Measured by the page's own scan on three steady synthetic voices
(110/220/440 Hz) slowed to 0.5×: median 0.7 ¢, 90th percentile 1.1 ¢ from the
true pitch (`check.mjs`, 2026-10-25); with 5.5 Hz ±40 ¢ vibrato the tracker
reads 31 ¢ median slowed against 29 ¢ at 1× (the tracker's own lag on vibrato).
A 32 s take takes 0.8-1.3 s to slow, once per version and speed. Each scored take's summary is kept on the device
(localStorage, last 500, never sent; "forget my takes" clears it) and the card
ends with progress lines per aspect and overall: a dot per take, the mean of
the last 5 takes, and a band of ±1.96 standard errors between takes; it says
"better" or "worse" only when the last 5 differ from the 5 before by more
than both bands together (`squillo` ADR 0025). On playback of any version the coaching panel switches to
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

Slide style vs unwanted scoop, measured with the page's own code
(`check/slide-bench.mjs`, headless Chrome, 2026-10-25): synthetic 12-note
phrases at 110, 196 and 330 Hz, 10 per class and voice. Classified right:
style (every note slid into by one depth, ±10 %) 30/30, unwanted (2-5 random
scoops) 30/30, many (6-9 scoops of random depth) 29/30, clean 30/30;
slides found 359/360, 103/103, 228/229. None of the 14 VocalSet clips or
the two references is called a style (they hold 0-9 slides each, a weak
test of false alarms). Real pop or soul slides vary more than ±10 % in
depth; recall on them is unmeasured (no openly licensed annotated set).

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

`running`: the main product track since 2026-10-25 (Joakim: "helix is the main
thing right now and what we want to evolve"). Plan in `ROADMAP.md`, log in
`LOG.md`.

## Run

```
python3 -m http.server --directory page 8000
```

then open <http://localhost:8000/>. Chrome and Firefox allow the microphone
on `localhost` without HTTPS. Or push to `main`: the workflow
`.github/workflows/voice-helix-publish.yml` publishes `page/` to GitHub Pages.

## Check

```
cd check && npm install && node check.mjs http://localhost:8000/
```

Chrome, Firefox and WebKit at an iPhone 15's size and touch: the page loads
without errors, the public-domain reference clip loads as the take, the
timeline, summary and progress lines (over seven seeded earlier takes) appear, a tap on the timeline plays from there, a tap on a spot loops it A/B and
"spotless" plays. After a push, `node check.mjs https://zernox.github.io/squillo-lab/
--wait $(sha256sum ../page/index.html | cut -d' ' -f1)` waits for the deploy
and checks the live site. Add `--headed` to watch it in maximized windows on this machine's
display (with sound; `--slow 300` slows each step, `--hold 10` keeps each window
open 10 s at the end). Headless runs are muted. Screenshots land in `--out` (default
`/tmp/voice-helix-check`).
