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
take picks one (pYIN, Mauch & Dixon 2014, simplified: dip + 0.15 per octave
below the highest candidate + 0.035 per semitone jumped, unvoiced 0.45,
voicing switch 0.25). Measured with the page's code (`check/pitch-bench.mjs`,
held-out seed 4242, 29 328 voiced frames, 5 voice types from bass 82 Hz to
soprano 880 Hz × clean, breathy, weak fundamental, ±100 ¢ vibrato,
untrained drift): gross error (>50 ¢) 1.4 % live → 0.4 % take, octave
errors 0.8 % → 0.4 %, missed voiced frames 0.0 % → 0.2 %, RPA 99.4 %;
worst cell after: soprano breathy, 4.8 % octave-low (with 0.3 per octave, used until 2026-10-25: 0.1 % gross, RPA 99.6 %). On real voices (`check/vocadito-bench.mjs`, page code, vocadito: Bittner et al. 2021, 40 a cappella excerpts, 29 singers, 7 languages, hand-corrected f0, CC BY 4.0, https://zenodo.org/records/5578807, not shipped): raw pitch accuracy (voiced, within 50 ¢) 98.1 ± 0.7 % (± 1.96 SE over clips; pooled 98.1 %), chroma 98.4 %, voicing recall 98.9 %, false alarm 17.1 ± 3.5 %, overall 93.2 ± 1.2 %; voices centred below A3 97.8 ± 1.4 %, above 98.4 ± 0.7 %. With the earlier 0.3 per octave: 94.8 ± 2.4 %, low voices 91.8 ± 5.1 % (worst clip 58 %, a low voice read an octave or a twelfth high); 0.1 gives 98.3 % but 7.1 % octave-low on synthetic breathy sopranos, 0 breaks synthetic (RPA 93.8 %), so 0.15. Screen lag (2026-10-26): a 'screen lag' chip shows, while singing, the measured time from each 512-sample audio chunk reaching the page to the next paint of the helix that uses it, plus half the pitch window (about 14 ms at 48 kHz, where the pitch belongs), plus the mic's latency when the browser reports it (getSettings().latency; otherwise '+ mic'): median and p90 over the last 150 frames. Measured by check.mjs on the live synthetic demo, headless: Chrome 18 ms (p90 19), Firefox 25 (31), WebKit iPhone size 24 (28). Not included: the audio device's input buffer when unreported, and the display's own scan-out (up to one frame, ~16 ms). Note-edge trim (2026-10-26): the first and last 2 frames of each voiced run are unvoiced when their level on a short window (2 periods, ≥ 10 ms, centred where the pitch belongs) is below 0.2 × the run's median: false alarm 17.1 → 12.8 ± 2.9 %, overall 93.2 → 94.3 ± 1.0 %, RPA 98.1 → 97.6 ± 0.7 % (low 97.3 ± 1.4, high 97.8 ± 0.7), voicing recall 98.4 %; 0.1/4 frames: FA 15.0, OA 93.8; 0.25/3: FA 11.6, RPA 97.3; 0.4/3: FA 10.1, RPA 96.2. The figures above are before the trim. vocadito's voices centre at B2-F4: sopranos are tested on synthetic voices only. 72 % of false alarms lie within 35 ms of an annotated sung frame (note edges); gates on HNR, CMND or level trade as much RPA as they remove false alarms (overall within ±1 pt), so none is used. A lag sweep peaks at 0 ms, so frame times line up. Unvoiced cost 0.3 / 0.45 / 0.6 / 0.8 gives overall 90.0 / 91.1 / 90.8 / 90.3 % (at 0.3 per octave): 0.45 stays. The take summary states this figure.
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
the same moment spotless, 1 s (padded 0.4 s, capped at 4 s), until clicked again. ◀ note / note ▶ (or ← →) plays one held note at a time (padded 0.15 s) in the version last played, outlines it on the bar and says its cents off, wobble and onset. ⟲ loop phrase (or L) loops the phrase around the playhead or the note stepped to (voiced stretches joined across short gaps, up to 8 s), in the version and speed last chosen, until pressed again. ⚑ mark (or M) drops a flag where the take is playing; flags are kept per take on the device (localStorage), a click plays from 1 s before, a double-click removes it. A speed menu (1×, 0.75×, 0.5×) slows the take, halfway,
spotless and the A/B loop without changing pitch (WSOLA, 40 ms grains, ±8 ms
search). Measured by the page's own scan on three steady synthetic voices
(110/220/440 Hz) slowed to 0.5×: median 0.7 ¢, 90th percentile 1.1 ¢ from the
true pitch (`check.mjs`, 2026-10-25); with 5.5 Hz ±40 ¢ vibrato the tracker
reads 31 ¢ median slowed against 29 ¢ at 1× (the tracker's own lag on vibrato).
A 32 s take takes 0.8-1.3 s to slow, once per version and speed. Each scored take's summary is kept on the device
(localStorage, last 500, never sent; "forget my takes" clears it), with its
steadiest long note and longest note held within 10 ¢; "went well" names a personal
best only when it beats every earlier take by more than one note's noise (1 ¢, 0.3 s). The card
ends with a practice streak (days in a row, minutes sung, milestones) and progress lines per aspect and overall: a dot per take, the mean of
the last 5 takes, and a band of ±1.96 standard errors between takes; it says
"better" or "worse" only when the last 5 differ from the 5 before by more
than both bands together (`squillo` ADR 0025). "▶ same phrase" finds the phrase around the current note (◀ ▶) in the earlier take picked beside "▶ earlier take" (subsequence DTW on the pitch contour, any key) and plays it, then today's: on vocadito (CC BY 4.0), the page's code finds 95.0 ± 3.9 % of 120 phrases (mean 5.1 s) in the same clip slowed to 0.8× with noise, and accepts a phrase from a different clip 3.3 ± 3.2 % of the time (`check/phrase-bench.mjs`; a proxy for a re-sung take, which will match less well). It then says how the phrase's held notes measured then and today (cents off, wobble, each ±1.96 SE over its notes; better or worse only beyond both ±). Picking "all N kept takes" plays every version found, oldest first, then today's, each with its cents off. "☀ warm-up" builds an about 4 min routine from those takes: lip trill or straw glides (Titze 2006), one or two steps for the aspects furthest from the median trained singer over the last 5 takes (pitch matching, Hutchins & Peretz 2012; messa di voce, Titze et al. 1999; clean starts; easy onsets), then a siren, each with a guide tone in the singer's own range (10th-90th percentile of their notes); with no takes, a general routine at A3-E4. "♪ voice profile" shows the comfortable range (median over takes of each take's 10th and 90th percentile note, ± 1.96 SE between takes) and the full range (lowest and highest held note in any take) on a bar, a voice-type guess from the range centre alone (tessitura centres after McKinney 1994; not validated, timbre and register breaks are not used), and a key for any song: type the melody's lowest and highest note (and its key) and it is shifted so its centre sits on the comfortable centre, with whether it then fits and whether it crosses the singer's register break. Register breaks: on a glide, a line is fitted to the 200 ms of pitch before and after each moment; both sloping the same way at ≥ 3 st/s, each within 0.25 st RMS, and disagreeing by ≥ 1.2 st is a break (`check/break-bench.mjs`, page code, synthetic sirens at four voice heights with a 2-4 st jump and a tilt change: 64/64 breaks found, pitch error median 0.06 st, p90 0.11 st; 0 false breaks on 32 clean sirens, 32 vibrato legato scales, 32 vibrato-heavy sustained notes; 1 break flagged in 274 s of 16 real clips without sirens). Vibrato in the take summary (2026-10-26): long notes (0.8 s or more, voiced runs cut at note changes) have a quadratic taken out, and the first autocorrelation peak of 0.4 or more at 3-8.5 Hz gives the rate, with extent = 1.41 × SD (peak, st); the summary says "Vibrato on n of N long notes: rate ± 1.96 SE Hz, ±extent st" against the 5.5-6.5 Hz of trained singers (Prame 1994). Measured (`check/vibrato-bench.mjs`, page code): 120 synthetic 2 s notes over bass to child, breath noise, rate 4-8 Hz with ±5 % cycle jitter, extent 0.15-1.5 st, half sliding 0.6 st: take means within 0.11 Hz and 0.03 st of truth for every voice, 89-100 % of vibrato notes found per voice (16-18 of 18), 0 of 30 straight notes called vibrato. VocalSet (CC BY 4.0) "Caro mio ben": vibrato versions 5.30 ± 0.10 Hz ±1.00 st (woman), 4.99 ± 0.07 Hz ±0.81 st (man); the "straight" versions still show vibrato on 5 of 9 / 5 of 8 notes (±0.45 / ±0.70 st), and the scale "straight" clips 0 of 4 / 0 of 3: no truth labels per note, so whether those straight-aria notes waver is unverified. The live vibrato chip (Hz · st) runs the same estimator on the last 1.2 s of the current note (since its last note change): on the synthetic notes, rate error median 0.04 Hz, p90 0.11 (was 0.07 / 0.13 with the earlier 1.2 s zero count, which read legato steps in the straight aria as about 4 Hz vibrato), extent 3 % low, 0 of 30 straight notes flagged. Vibrato evenness (2026-10-26): upward zero crossings of the detrended pitch (hysteresis ±0.3 SD) mark cycles; the coefficient of variation of cycle rate and of cycle half peak-to-trough over a note (3 cycles or more), averaged over vibrato notes, ± 1.96 SE. Measured (`check/vibrato-bench.mjs`, page code, synthetic uniform jitter): rate CV true 2.9 / 8.7 / 17.3 % read 3.1 ± 0.3 / 7.5 ± 0.9 / 15.3 ± 1.5 %; extent CV true 0 / 11.5 / 23.1 % read 2.3 ± 0.4 / 12.2 ± 1.1 / 22.9 ± 1.9 %. VocalSet Caro mio ben, vibrato: rate CV 11.9 / 11.3 %, extent 23 / 29 % (woman / man); the summary calls ≤ 12 % and ≤ 30 % 'as even as' those singers (a reference from two singers, not a norm). "▶ earlier take" plays any of the last 10 scored takes, whose audio is kept in this browser (IndexedDB, 22.05 kHz 16-bit, never sent), picked by date and note score, to hear the change against ▶ your take. The profile's range finder fills it in about a minute: three mic steps (slide down to the lowest note and hold, slide up to the highest and hold, a siren on “ng”), each tracked like a take; the lowest and highest held notes are the extreme medians of 0.3 s voiced windows staying within 2 st, breaks come from the siren; kept apart from takes (`check/range-bench.mjs`, page code, 30 synthetic voices with vibrato, breath noise and a fry tail: lowest-note error median 0.11 st, p90 0.16; highest median 0.19 st, p90 1.36, tops above the tracker's 1100 Hz ceiling read low; 95 % within 1 st; siren breaks 60/60). Breaks seen go into the take's "to work on" with siren exercises, and into the profile bar. On playback of any version the coaching panel switches to
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
