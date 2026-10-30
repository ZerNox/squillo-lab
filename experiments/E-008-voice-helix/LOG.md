# Voice Helix log

Newest first. Date, what was built, what a singer can now do, numbers, next.

## 2026-10-30 · sung vowel, first benchmark of the formants

Built: `readVowel`/`spanVowel` with centres fitted on sung notes, `check/vowel-bench.mjs`, a live 'vowel' chip, 'sounds like “ee”' in note by note, only when sure. Formants had no measured accuracy until now. VocalSet (2405 notes, 20 singers, 5 vowels, page code): 68.2 ± 4.4 % under 600 Hz (speech centres 61.3 ± 4.8; left-out-singer 67.7 ± 4.5), sure 74.1 ± 5.4 % on 67 % of notes; no reading at 600 Hz and up. Not benchmarked on 0.5 s live windows; the synthetic demo 'ah' reads unsure (speech-table formants). check.mjs: reader, chip, note line, 3 browsers. Process: WebKit hangs intermittently even alone (one 170 s timeout, same code passed in about 50 s; cause not found), so a hung browser gets one retry, timeout 240 s. iOS risk: none new. Next: back vowels, singer's formant.

## 2026-10-30 · hear it with your pulse

Built: on a take with a found pulse, '▶ hear it with your pulse' plays the take with a soft click on the singer's own fitted pulse (every second step when under 0.3 s), following their tempo; clicks skip the analysis path and stop with playback. A singer now hears where they sat ahead or behind, with no metronome at the time of singing. check.mjs: button, click oscillator, stop, 3 browsers. No new measurement. Process: full three-browser runs hung starting WebKit after Firefox three times this run though each browser passes alone (WebKit 44 s, Firefox 52 s), cause not found; verified browser by browser. iOS risk: clicks run on the already resumed context; 'ended' listener needs Safari 14.1+. Next: legato onset floor.

## 2026-10-30 · timing and rhythm, no click needed

Built: `pulseFit`/`takeTiming` (finds the steady pulse behind the note starts, following a moving tempo; spread in ms ±, tempo change %) and `check/timing-bench.mjs`. Synthetic (120 pulsed melodies, 5 voices, page code): spread reads 18/23/38/64 ms median for jitter 0/15/30/60 (floor 10 ms gapped, 31 ms legato), tempo change error SD 1.0-2.6 %, pulse found 29/30, 30/30, 29/30, 19/30; false pulse 0/20 free-rhythm controls at threshold 0.15 (5/20 at 0.17). vocadito: weak: pulse in 9 clips by page, 7 by annotated onsets, 3 by both, so 'free timing' is worded softly and rhythm is not rated. Tried raw-pitch legato onset crossing: no gain, removed. A singer now hears 'steady rhythm' with ms ±, or 'you slowed 12 %' with a metronome exercise (Repp 2005), and sees a rhythm spread progress line. iOS risk: none new. Next: legato onset floor (level-envelope onsets, shared with note edges item), real-voice pulse agreement.

## 2026-10-30 · steadier than any last week

Built: `lastWeekLine` in the take summary's "went well": when the take's last three long notes (≥ 1 s) each wobble less than the steadiest long note of every take kept from the 7 days before today (by more than the 1 ¢ a single note reads to, 2+ such takes), it says so with the numbers, e.g. "Your last three long notes (2.0, 2.4, 2.8 ¢ wobble) were each steadier than any long note in your 2 takes from the week before today (best 4.0 ¢)". The mission's own example of feedback a singer can feel, now live. check.mjs: seeded week (and a 20-day-old take ignored), claim and no-claim cases, 3 browsers. No new measurement (wobble is the personal-best reading). iOS risk: none (localStorage). Next: edge onsets or tone part 2.

## 2026-10-30 · hear it from the summary

Built: "▶ hear it" by the best note in "went well" (plays it from the take) and the furthest-off held note (≥ 0.4 s, ≥ 20 ¢) leading "to work on" with "▶ yours, then tuned" (A/B loop with spotless). A singer now hears the note the words are about, theirs next to the tuned version, in one click. check.mjs: both buttons tapped (a note forced 40 ¢ off for the second), 3 browsers. Negative result, not shipped: key drift unwrapping against a ±3/5/8 s local circular mean or a global circular fit gave vocadito SD 63/39/39/91 ¢ vs 41 now; the agreement limit is note-level ambiguity on loose real intonation (offsets near ±50 ¢), not the unwrap rule. `drift-bench.mjs` takes 0 melodies to skip synthetic. iOS risk: none new (playback through the existing paths). Next: edge onsets or tone part 2.

## 2026-10-30 · key drift on the progress line

Built: each take stores |key drift| (`takeDrift`, synthetic SD 16 ¢, vocadito SD 41 ¢); a 'key drift' row in the take table, a progress line with band and a week line, lower is better, shown but not rated (excluded from the rating and warm-up, given the coarse real-voice agreement). Takes too short for a drift store none and the line skips them. A singer working with a drone now sees whether their tuning holds better over weeks. check.mjs: 12 seeded takes (two without drift), 70 to 15 ¢, read 'better than the takes before', not in RATED, 3 browsers. No new measurement. iOS risk: none (localStorage). Next: real-voice drift agreement (note matching) or edge onsets.

## 2026-10-30 · key drift per take

Built: `takeDrift` (notes after a 0.22 s pitch average, offsets unwrapped against a running reference, weighted line over time, ± 1.96 SE) and `check/drift-bench.mjs`. Synthetic known drifts (90 melodies, 5 voice types, half with vibrato): error +1.4 ± 3.3 ¢, SD 15.8, truth inside ± 81/90. vocadito, page vs hand-corrected f0 through the same code: SD 41 ¢, sign agrees on 11/14 truly drifting clips: coarse on real voices, so the wording is conservative. A singer now hears 'you held your key' (whole ± within 20 ¢) or 'your tuning sank 45 ± 20 ¢ over 30 s' with a drone exercise (Howard 2007). check.mjs: -60 ¢ synthetic reads -54, level reads 0, both wordings, 3 browsers. iOS risk: none new. Next: drift on the progress line; tighten real-voice agreement (note matching).

## 2026-10-29 · swell on the progress line

Built: each take stores its largest within-note swell (`takeDynamics`, the measure benchmarked at messa vs straight AUC 0.93); a 'swell (dynamics)' row in the take table, a progress line with band, and a week line, all saying more swell / flatter, never better or worse (not rated, like tone colour). Takes without a 1 s note store no swell, so the line skips them instead of reading 0. A singer practising messa di voce now sees whether their swells grow over weeks. check.mjs: 12 seeded takes (two without swell) read 'more swell than the takes before', no better/worse, not in RATED, 3 browsers. No new measurement. iOS risk: none (localStorage). Next: edge onsets (finer hop) or tone part 2.

## 2026-10-29 · dynamics per take (messa di voce measured)

Built: `takeDynamics` (level over long notes, 100 ms smoothed; swell p95-p5 within a note, span soft to loud across notes, gain-free) and `check/dyn-bench.mjs` (page code, VocalSet long tones on "a", 20 singers, 80 clips, CC BY 4.0, not shipped): messa di voce swell 21.1 ± 2.6 dB (median 19.3, p10 14.5), straight 9.6 ± 2.1 (median 7.3, p90 13.9); messa vs straight AUC 0.93, pairs 20/20; forte - pp 8.6 ± 3.6 dB. The take summary now says how a singer's level moved, names a swell of 14.5 dB or more a real messa di voce, else suggests one; described, not rated. check.mjs: synthetic swell/level/soft tones (swell 17.9 dB, span 10.0), both wordings, 3 browsers. iOS risk: none new. Next: dynamics on the progress line, or edge onsets.

## 2026-10-29 · vibrato evenness against 20 trained singers

Built: `check/vibeven-bench.mjs` (page code, every VocalSet vibrato clip: scales, arpeggios, three excerpts; 250 clips, 20 singers, CC BY 4.0, not shipped). Per-singer rate CV median 13.6 % (p90 18.1, mean 12.4 ± 1.5), width CV 22.1 % (p90 28.9, mean 22.6 ± 1.9); arpeggios evener (9.5 / 19.0) than excerpts (15.7 / 25.4). The take summary's evenness line now has three tiers on that reference (evener than half / within the range / an exercise beyond the 90th percentile) instead of a two-singer Caro mio ben cut. check.mjs: all three tiers' wording, 3 browsers. iOS risk: none new. Next: edge onsets or tone part 2.

