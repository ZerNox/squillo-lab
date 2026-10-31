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

Drone: ♪ drone (D) holds a soft unison tone on the target note. Leak into the mic, Lane reading, synthetic (`check/drone-bench.mjs`): -18 dB max 2.5 ¢, -12 dB max 4.8 ¢, -6 dB max 13 ¢; an octave below flips the reading, so unison only. Real speaker leak unmeasured; no training gain claimed.

Capture: AudioWorklet (ScriptProcessor fallback) at raw settings
(`echoCancellation`, `noiseSuppression`, `autoGainControl` all false, as
E-003 found browsers honour). Analysis: a Web Worker at a fixed 20 ms hop
(YIN with a continuity witness, LPC order 2+fs/1000 at 12 kHz, 4096-point
FFT with a 2 s room profile subtracted). The live level gate sits at 1.5× the calibrated room level (`check/live-noise-bench.mjs`, vocadito 40 clips, page code, live RPA: pink 10 dB 83.6 ± 3.7, 5 dB 64.0 ± 3.7, hum 10 dB 78.9 ± 3.7, was 47.5, 6.0, 39.9; clean 91.0 ± 3.5, FA 14.9 ± 3.2 with the voicing limit at 0.3, rising with the noise's share; synthetic HNR 0 dB notes go unread in quiet; added noise, no real room). Takes get their own pitch track:
every frame keeps up to 8 YIN candidates and a Viterbi path over the whole
take picks one (pYIN, Mauch & Dixon 2014, simplified: dip + 0.15 per octave
below the highest candidate + 0.035 per semitone jumped, unvoiced 0.45,
voicing switch 0.25). Measured with the page's code (`check/pitch-bench.mjs`,
held-out seed 4242, 29 328 voiced frames, 5 voice types from bass 82 Hz to
soprano 880 Hz × clean, breathy, weak fundamental, ±100 ¢ vibrato,
untrained drift): gross error (>50 ¢) 1.4 % live → 0.4 % take, octave
errors 0.8 % → 0.4 %, missed voiced frames 0.0 % → 0.2 %, RPA 99.4 %;
worst cell after: soprano breathy, 4.8 % octave-low (with 0.3 per octave, used until 2026-10-25: 0.1 % gross, RPA 99.6 %). On real voices (`check/vocadito-bench.mjs`, page code, vocadito: Bittner et al. 2021, 40 a cappella excerpts, 29 singers, 7 languages, hand-corrected f0, CC BY 4.0, https://zenodo.org/records/5578807, not shipped): raw pitch accuracy (voiced, within 50 ¢) 98.1 ± 0.7 % (± 1.96 SE over clips; pooled 98.1 %), chroma 98.4 %, voicing recall 98.9 %, false alarm 17.1 ± 3.5 %, overall 93.2 ± 1.2 %; voices centred below A3 97.8 ± 1.4 %, above 98.4 ± 0.7 %. With the earlier 0.3 per octave: 94.8 ± 2.4 %, low voices 91.8 ± 5.1 % (worst clip 58 %, a low voice read an octave or a twelfth high); 0.1 gives 98.3 % but 7.1 % octave-low on synthetic breathy sopranos, 0 breaks synthetic (RPA 93.8 %), so 0.15. This week vs last week (2026-10-26): under the progress lines, each aspect's mean over the takes of the last 7 days against the 7 days before (2 takes or more in each), each ± 1.96 SE between takes; 'better' or 'worse' only when the means differ by more than both intervals together, else 'level within the noise'; better aspects are named first. Screen lag (2026-10-26): a 'screen lag' chip shows, while singing, the measured time from each 512-sample audio chunk reaching the page to the next paint of the helix that uses it, plus half the pitch window (about 14 ms at 48 kHz, where the pitch belongs), plus the mic's latency when the browser reports it (getSettings().latency; otherwise '+ mic'): median and p90 over the last 150 frames. Measured by check.mjs on the live synthetic demo, headless: Chrome 18 ms (p90 19), Firefox 25 (31), WebKit iPhone size 24 (28). Not included: the audio device's input buffer when unreported, and the display's own scan-out (up to one frame, ~16 ms). Breathiness (2026-10-27): CPP, cepstral peak prominence (Hillenbrand et al. 1994), per frame from the 4096-point log spectrum, band 0 to a quarter of the sample rate, floored 90 dB under its peak (so MP3/AAC's empty top band does not move it): the cepstrum's peak within ±8 % of the pitch period above the line fitted over 1/1100-1/60 s, smoothed (0.3). Measured (`check/breath-bench.mjs`, page code, VocalSet scales sung breathy and straight by all 20 singers on five vowels, 194 clips, CC BY 4.0, not shipped): clip medians breathy 22.5 ± 0.6 dB, straight 27.0 ± 0.5 (women 20.8 / 25.9, men 23.8 / 27.8); AUC 0.90; the breathy clip reads lower than the same singer's straight clip on the same vowel in 98.9 ± 2.1 % of 94 pairs. The same clips through 80 kbit/s MP3: AUC 0.91, pairs 98.9 %, all about 1.3 dB lower. The earlier CMND-based HNR gave AUC 0.57 (pairs 57 %) and the old 'breathy' cue fired on 0 % of breathy frames (AUC 0.36); the cue now fires below 23 dB: on 42 ± 6 % of breathy frames, 10 ± 3 % of straight, AUC 0.83 (MP3: 53 / 16 %). The live 'clarity (CPP)' chip, the 'voice clarity' progress line (not rated: microphone and room move it) and the take summary use it: ≥ 24.5 dB is praised as a clear tone, < 23 dB over 3 s or more of singing becomes a point to work on with straw phonation (Titze 2006), unless breathy is the style. Absolute CPP depends on this implementation; it is not Praat's scale. Note-edge trim (2026-10-26): the first and last 2 frames of each voiced run are unvoiced when their level on a short window (2 periods, ≥ 10 ms, centred where the pitch belongs) is below 0.2 × the run's median: false alarm 17.1 → 12.8 ± 2.9 %, overall 93.2 → 94.3 ± 1.0 %, RPA 98.1 → 97.6 ± 0.7 % (low 97.3 ± 1.4, high 97.8 ± 0.7), voicing recall 98.4 %; 0.1/4 frames: FA 15.0, OA 93.8; 0.25/3: FA 11.6, RPA 97.3; 0.4/3: FA 10.1, RPA 96.2. The figures above are before the trim. vocadito's voices centre at B2-F4: sopranos are tested on synthetic voices only. 72 % of false alarms lie within 35 ms of an annotated sung frame (note edges); gates on HNR, CMND or level trade as much RPA as they remove false alarms (overall within ±1 pt), so none is used. A lag sweep peaks at 0 ms, so frame times line up. Unvoiced cost 0.3 / 0.45 / 0.6 / 0.8 gives overall 90.0 / 91.1 / 90.8 / 90.3 % (at 0.3 per octave): 0.45 stays. The take summary states this figure. Noisy rooms (2026-10-31, `check/noise-bench.mjs`, page code, vocadito 40 clips with noise added; ± 1.96 SE over clips): noise lifts YIN's dip by its share of the frame's power, so voiced frames were rejected. `roomFloor` takes the 3rd percentile level of pitchless frames; below 14 dB voice over floor the Viterbi takes that share off the dip and also weighs candidates up to 0.8. Settings chosen on these clips, so slightly optimistic. RPA before → after: pink 10 dB 89.2 ± 2.8 → 93.0 ± 1.9, pink 5 dB 68.9 ± 4.4 → 85.4 ± 2.9 (false alarm 1.0 → 4.0), pink 0 dB 18.3 ± 1.8 → 63.0 ± 3.9, 50 Hz hum 10 dB 82.7 ± 4.0 → 88.2 ± 3.5; talk-like noise (pink with 4 Hz swings), 5 dB 73.4 ± 2.8 → 73.6 ± 2.8, no real gain. Clean unchanged: 97.6 ± 0.7, FA 12.8 ± 2.9. At pink 20 dB 97.2 ± 0.8, at 15 dB 95.3 ± 1.3. Pitch on frames kept moves little: clip median shift p50 1.7 ¢ at pink 5 dB, max 5.6; 11.6 at 0 dB. Phone-mic roll-off, no noise: high-pass 200 Hz 95.5 ± 1.3, 300 Hz 91.8 ± 2.4 (filter simulated, no real phone measured). The summary's room line reads voice over floor: steady noise read within about 2 dB (true 10: 8-12; 5: 6-8; 0: 3-5), clean clips read 15 dB or more; talk-like noise reads about 10-13 dB too high (true 5: 12-20), so the line names steady noise only. The live tracker is unchanged. Tone colour and the retired pressed cue (2026-10-27, `check/press-bench.mjs`, page code, VocalSet scales belt, straight and breathy, 20 singers, five vowels, 294 clips): spectral tilt (100 Hz-4 kHz, dB/oct) clip medians belt +0.45 ± 0.32, straight -1.29 ± 0.23, breathy -2.39 ± 0.24; belt brighter than straight AUC 0.81, same-singer-vowel pairs 92.6 ± 5.3 % of 94. The live chip names it (bright, belt-like > -0.4; soft, airy < -1.85; else balanced) as a description, never a flaw. Since 2026-10-29 each take also gets its median tilt: a went-well line naming the colour, a table row, and progress and week lines that say brighter or softer, never better or worse (not rated). The old 'pressed / strained' cue (H1-H2 < -3 dB, HNR > 12) fired on 18 % of belt and of straight frames alike (AUC 0.53) and uncorrected H1-H2 does not separate them (AUC 0.54), so the cue is retired and H1-H2 is shown uncoloured; belt is a proxy for effort, not pressed phonation, and no openly licensed pressed-voice labels were found.
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
take to spotless). The summary and progress lines also carry ring, the singing power ratio (Omori 1996; `check/ring-bench.mjs`, VocalSet, proxy contrasts: forte vs pp AUC 0.85, pairs 19/20; straight vs breathy AUC 0.82; up to 5.5 dB shift at -12 dB gain).
A fourth version, "far vision", is spotless plus even vibrato and a ±1.5 dB swell
on held notes of 0.8 s or more (`check/far-bench.mjs`, 14 VocalSet straight clips:
5.8 Hz, ±0.45 st asked, 5.78 Hz, ±0.41 st read back, on the 9 with a reading;
spectrum proxy 1.43 dB from the take, spotless 1.23; a proxy, not a listener).
Version buttons and keys 1-4 carry on from the same moment.
The bar is a performance timeline: a sliding line of the
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
best only when it beats every earlier take by more than one note's noise (1 ¢, 0.3 s), and says "your last three long notes were each steadier than any long note last week" when all three beat the 7 days before today by that margin. The card
ends with a practice streak (days in a row, minutes sung, milestones) and progress lines per aspect and overall: a dot per take, the mean of
the last 5 takes, and a band of ±1.96 standard errors between takes; it says
"better" or "worse" only when the last 5 differ from the 5 before by more
than both bands together (`squillo` ADR 0025). "▶ same phrase" finds the phrase around the current note (◀ ▶) in the earlier take picked beside "▶ earlier take" (subsequence DTW on the pitch contour, any key) and plays it, then today's: on vocadito (CC BY 4.0), the page's code finds 95.0 ± 3.9 % of 120 phrases (mean 5.1 s) in the same clip slowed to 0.8× with noise, and accepts a phrase from a different clip 3.3 ± 3.2 % of the time (`check/phrase-bench.mjs`; a proxy for a re-sung take, which will match less well). It then says how the phrase's held notes measured then and today (cents off, wobble, each ±1.96 SE over its notes; better or worse only beyond both ±). Picking "all N kept takes" plays every version found, oldest first, then today's, each with its cents off. "☀ warm-up" builds an about 4 min routine from those takes: lip trill or straw glides (Titze 2006), one or two steps for the aspects furthest from the median trained singer over the last 5 takes (pitch matching, Hutchins & Peretz 2012; messa di voce, Titze et al. 1999; clean starts; easy onsets), then a siren, each with a guide tone in the singer's own range (10th-90th percentile of their notes); with no takes, a general routine at A3-E4. "♪ voice profile" shows the comfortable range (median over takes of each take's 10th and 90th percentile note, ± 1.96 SE between takes) and the full range (lowest and highest held note in any take) on a bar, a voice-type guess from the range centre alone (tessitura centres after McKinney 1994; not validated, timbre and register breaks are not used), and a key for any song: type the melody's lowest and highest note (and its key) and it is shifted so its centre sits on the comfortable centre, with whether it then fits and whether it crosses the singer's register break. Register breaks: on a glide, a line is fitted to the 200 ms of pitch before and after each moment; both sloping the same way at ≥ 3 st/s, each within 0.25 st RMS, and disagreeing by ≥ 1.2 st is a break (`check/break-bench.mjs`, page code, synthetic sirens at four voice heights with a 2-4 st jump and a tilt change: 64/64 breaks found, pitch error median 0.06 st, p90 0.11 st; 0 false breaks on 32 clean sirens, 32 vibrato legato scales, 32 vibrato-heavy sustained notes; 1 break flagged in 274 s of 16 real clips without sirens). Vibrato in the take summary (2026-10-26): long notes (0.8 s or more, voiced runs cut at note changes) have a quadratic taken out, and the first autocorrelation peak of 0.4 or more at 3-8.5 Hz gives the rate, with extent = 1.41 × SD (peak, st); the summary says "Vibrato on n of N long notes: rate ± 1.96 SE Hz, ±extent st" against the 5.5-6.5 Hz of trained singers (Prame 1994). Measured (`check/vibrato-bench.mjs`, page code): 120 synthetic 2 s notes over bass to child, breath noise, rate 4-8 Hz with ±5 % cycle jitter, extent 0.15-1.5 st, half sliding 0.6 st: take means within 0.11 Hz and 0.03 st of truth for every voice, 89-100 % of vibrato notes found per voice (16-18 of 18), 0 of 30 straight notes called vibrato. VocalSet (CC BY 4.0) "Caro mio ben": vibrato versions 5.30 ± 0.10 Hz ±1.00 st (woman), 4.99 ± 0.07 Hz ±0.81 st (man); the "straight" versions still show vibrato on 5 of 9 / 5 of 8 notes (±0.45 / ±0.70 st), and the scale "straight" clips 0 of 4 / 0 of 3: no truth labels per note, so whether those straight-aria notes waver is unverified. The live vibrato chip (Hz · st) runs the same estimator on the last 1.2 s of the current note (since its last note change): on the synthetic notes, rate error median 0.04 Hz, p90 0.11 (was 0.07 / 0.13 with the earlier 1.2 s zero count, which read legato steps in the straight aria as about 4 Hz vibrato), extent 3 % low, 0 of 30 straight notes flagged. Vibrato evenness (2026-10-26): upward zero crossings of the detrended pitch (hysteresis ±0.3 SD) mark cycles; the coefficient of variation of cycle rate and of cycle half peak-to-trough over a note (3 cycles or more), averaged over vibrato notes, ± 1.96 SE. Measured (`check/vibrato-bench.mjs`, page code, synthetic uniform jitter): rate CV true 2.9 / 8.7 / 17.3 % read 3.1 ± 0.3 / 7.5 ± 0.9 / 15.3 ± 1.5 %; extent CV true 0 / 11.5 / 23.1 % read 2.3 ± 0.4 / 12.2 ± 1.1 / 22.9 ± 1.9 %. VocalSet Caro mio ben, vibrato: rate CV 11.9 / 11.3 %, extent 23 / 29 % (woman / man); the reference is now all 20 VocalSet singers (2026-10-29, `check/vibeven-bench.mjs`, page code, 250 vibrato clips: scales, arpeggios, Caro/Dona/Row excerpts; 233 with 3+ cycles per note; per-singer means): rate CV median 13.6 % (p25-p75 10.3-15.2, p90 18.1, mean 12.4 ± 1.5), width CV median 22.1 % (19.6-27.0, p90 28.9, mean 22.6 ± 1.9); arpeggios evener (9.5 / 19.0), excerpts less (15.7 / 25.4). The summary says ≤ 14 % and ≤ 22 % is 'as even as or evener than half' of them, ≤ 18 % and ≤ 29 % 'within the range', and above that gives the siren or messa di voce exercise (a reference from trained singers, not a norm). The take summary puts sound next to its words (2026-10-30): "▶ hear it" by the best note (highest note score, ★) plays it from the take; the furthest-off held note (0.4 s or longer, 20 ¢ or more off the take's grid) leads "to work on" with "▶ yours, then tuned", the A/B loop with spotless at that note. "▶ earlier take" plays any of the last 10 scored takes, whose audio is kept in this browser (IndexedDB, 22.05 kHz 16-bit, never sent), picked by date and note score, to hear the change against ▶ your take. The profile's range finder fills it in about a minute: three mic steps (slide down to the lowest note and hold, slide up to the highest and hold, a siren on “ng”), each tracked like a take; the lowest and highest held notes are the extreme medians of 0.3 s voiced windows staying within 2 st, breaks come from the siren; kept apart from takes (`check/range-bench.mjs`, page code, 30 synthetic voices with vibrato, breath noise and a fry tail: lowest-note error median 0.11 st, p90 0.16; highest median 0.19 st, p90 1.36, tops above the tracker's 1100 Hz ceiling read low; 95 % within 1 st; siren breaks 60/60). Breaks seen go into the take's "to work on" with siren exercises, and into the profile bar. On playback of any version the coaching panel switches to
the flaw 1.5 s before each spot and praises each starred note as it passes. The drawn figure is the coach. A filmed
coach is a feature toggle, off by default: with `?coach=video` in the URL it
plays `page/coach/<pose>.mp4` silently for each exercise that has a clip
(prompts and the import script in `coach/`). An Elo rating against a
reference pool is a second toggle, `?rating=1`, experimental: see
`rating/README.md` for why it is off. To analyse a song with music, remove the
music first with `tools/separate-vocals.sh` (Demucs).

Without looking: "say note" (N key) speaks the held note and its cents off

Lane: a fifth view for reading while singing. The last 8 s as a flat line on a semitone grid, and the held note in big letters with cents and ± (`laneRead`: median of the last 0.4 s of the same note, on vibrato the mean of the whole cycles in the last 0.7 s, ± from how far they differ, 3 ¢ floor). `check/lane-bench.mjs`, page code, synthetic, 5 voices 110-660 Hz, offsets -60..45 ¢: straight median error 0.4 ¢, max 1.1, truth inside ± 100 %; vibrato ±0.5 st, 4.5-7 Hz, median 2.2 ¢, max 4.8, median ± 4, truth inside ± 97.1 %. Live frames only, no real-voice figure.
(or off the target note) through a polite live region, so a screen reader
(VoiceOver, NVDA, TalkBack) says it while you sing: once a note is held
0.4 s, again when it changes or every 4 s; ±10 ¢ is called in tune. `?` lists
the keys. Use headphones with a mic, or the reader's voice reaches the tracker.

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

Dynamics (`check/dyn-bench.mjs`, page code `takeDynamics`, VocalSet long tones on "a", 20 singers, 80 clips, CC BY 4.0, not shipped): swell within a held tone (p95 - p5 of the 100 ms-smoothed level) reads messa di voce 21.1 ± 2.6 dB (median 19.3, p10 14.5), straight 9.6 ± 2.1 (median 7.3, p90 13.9), pp 9.7, forte 10.3; messa above straight AUC 0.93, same-singer pairs 20/20; forte minus pp level 8.6 ± 3.6 dB, louder in 17/20. The take summary describes dynamics (swell within long notes, span soft to loud) and calls a swell of 14.5 dB or more a real messa di voce; it is a description, not rated, and gain-free (only level differences). Each take also stores its largest swell; a 'swell (dynamics)' progress line and week line say more swell or flatter, never better or worse, and takes without a 1 s note store none.

**Sung vowel, envelope reader** (`envVowel`, `check/vowel-dump.mjs` then `check/vowel-fit.mjs`, page code, VocalSet CC BY 4.0, 2354 notes under 600 Hz, 20 singers, chance 20 %): LDA on the harmonic levels at 14 points 250-4500 Hz with the tilt removed, plus f0. Left-out-singer 78.5 ± 4.5 % (formant centres 67.7 ± 4.5); a 86.8, e 81.7, i 88.2, o 64.0, u 72.3; 88.5 under 200 Hz, 68.1 ± 11.9 at 400-600 Hz. 'Sure' (log-odds margin 1): 85.2 ± 4.7 % on 74 % of notes. With tilt kept the table scored 82.5 but fell to 76 under a ±3 dB/octave mic slope, so tilt is removed. 0.5 s live window, table fitted on the same notes (optimistic): 82.1 ± 5.1 %, whole notes on the same footing 81.5 ± 4.4. All one recording chain and five vowels: other mics and languages unmeasured. The paragraph below is the formant reader, now only the fallback.

**Sung vowel** (`readVowel`, `spanVowel`; `check/vowel-bench.mjs`, page code, VocalSet CC BY 4.0, 2405 notes of scales and arpeggios, 20 singers, 5 vowels, chance 20 %): 68.2 ± 4.4 % per note under 600 Hz (speech-table centres 61.3 ± 4.8 %; leave-one-singer-out 67.7 ± 4.5 %, so the centres are not overfitted), 73.0 ± 8.6 % under 200 Hz, 63.8 ± 11.6 % at 400-600 Hz, no reading at 600 Hz and up (30 % there). Shown only when 'sure' (runner-up 0.1 log units further off): 74.1 ± 5.4 % on 67 % of notes. Live chip 'vowel' and the note-by-note line; a best guess, not a score. Real-time 0.5 s windows were not benchmarked separately; the figure is per note.

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

Notes (2026-10-30, `check/notes-bench.mjs`, page code, vocadito, A1 as truth): `segNotes`, optimal partitioning of voiced runs, gives note F COnP 74.2 ± 2.7 %, COn 82.7 ± 2.2, COnPOff 60.1 ± 3.5 (second annotator 74.0 / 81.7 / 64.2; `takeNotes` 36.7 / 36.9 / 26.6), tuned on the same clips. The note list and timing use it; intonation and stability stay on `takeNotes`. Timing figures below predate it (legato floor now 12 ms, gapped 6, false pulse 0/40). Timing (2026-10-30): `takeTiming` (page code) fits note starts to the steady pulse explaining them best, with a moving tempo, and reports spread (ms ±) and tempo change. `check/timing-bench.mjs`, synthetic: spread median 18/23/38/64 ms for jitter 0/15/30/60 (floor 10 gapped, 31 legato), change error SD 1.0-2.6 %, false pulse 0/20 on free rhythm, pulse missed in 11/30 at 60 ms. vocadito (CC BY 4.0): page and annotated onsets agree on a pulse in only 3 clips (9 page, 7 annotated), so it is described and on a progress line, not rated.

'▶ hear it with your pulse' plays the take with a soft click on that fitted pulse.

Key drift (2026-10-30): `takeDrift` (page code) takes the held notes after a 0.22 s pitch average, unwraps each note's offset from the semitone grid against a running reference, and fits a duration-weighted line over time: drift = slope × span, ± 1.96 SE; 8 notes over 8 s or more. Measured (`check/drift-bench.mjs`): synthetic 16-note scale melodies, five voice types, per-note intonation N(0, 12 ¢), half with ±0.5 st vibrato, known drift -100..+60 ¢ over about 20 s: 90/90 measured, error +1.4 ± 3.3 ¢ (SD 15.8, p90 |error| 16 ¢), truth inside the ± on 81/90; zero drift read beyond its ± on 1/15. On vocadito (40 real a cappella clips, CC BY 4.0), page pitch against the hand-corrected f0 through the same code: 37 clips measured, difference -6 ± 13 ¢ (SD 41, p90 61); of 14 clips whose truth drifts beyond its ±, the page agrees in sign on 11. Truth drift across vocadito: median |drift| 18 ¢, p90 60 ¢, 18/37 flat. So on real voices it is coarse: the summary praises 'held your key' only when the whole ± stays within 20 ¢, and names key drift as a point to work on (singing over a drone, Howard 2007) only at 30 ¢ or more beyond its ±. Not on the progress lines yet. Each take also stores its drift size (|cents|) for a 'key drift' progress line and week line (lower is better, shown but not rated, given the 41 ¢ real-voice agreement).

**Match and measure** (`matchGo`, `matchStats`, 2026-10-31): the warm-up's pitch steps play five tones and read each sung reply with `tryRead`, plus landing time and overall lean; sessions kept in `helix.match.v1`. `check/match-bench.mjs`, page code, synthetic: landing error worst 55 ms straight, 75 ms vibrato; 40 sessions, truth inside ± 40/40; one note of 200 (830 Hz) read 498 ¢ off. Real voices unmeasured.

**Sing it again** (`tryRead`, `drillGo`): the summary's furthest-off note can be re-sung at once against that note tuned, read in ¢ with ±. Page code (`check/drill-bench.mjs`): synthetic SD 1.5 ¢ straight, 2.1 ¢ with vibrato, truth inside ± 59/60; VocalSet long tones with a known resampling shift SD 0.9 ¢, 40/40 (shift recovery on the same take, not true pitch).
