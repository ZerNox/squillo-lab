# Voice Helix log

Newest first. Date, what was built, what a singer can now do, numbers, next.

## 2026-10-30 · yours, then far

Built: 'Where this can go' in the summary: '▶ yours, then far' loops the take's longest note (0.8 s or more) as sung, then in far vision; `abLoop` takes a target version. A singer hears the far point on their own note in one tap. check.mjs: button, loop, 3 browsers. No new measurement. iOS risk: none new. Next: vowels part 2.

## 2026-10-30 · ring: singer's formant, first measurement

Built: singing power ratio per frame (`spr`, Omori 1996), `aspects.ring`, a 'ring' line in the summary and a progress row, described, not rated; `check/ring-bench.mjs`. A singer now sees how much 2-4 kHz energy their voice carries, take by take. VocalSet (page code, no singer's-formant label exists, so contrasts are proxies): forte vs pp AUC 0.85, pairs 19/20, -18.4 vs -28.1 dB; straight vs breathy AUC 0.82, pairs 16/19, -18.5 vs -26.0 dB; first vs second half r 0.89 (79 clips). Not fully gain-free: at -12 dB the worst clip shifted 5.5 dB (frames gated differently), so small changes between sessions mean little. SPR rises with loudness; the line says so. No live chip. Process: one WebKit run closed its page mid-check (same as earlier reports, cause not found); WebKit alone passed. iOS risk: none new. Next: vowels part 2.

## 2026-10-30 · far vision in the singer's own voice

Built: a fourth version, '▶ far vision': spotless plus even vibrato (the singer's own rate and width when in the trained band, otherwise 5.8 Hz, ±0.45 st) and a ±1.5 dB swell on held notes of 0.8 s or more (`farVib`, `improveTake`, `check/far-bench.mjs`). Version buttons and keys 1-4 now carry on from the same moment. A singer can hear themselves further on and flip between take, halfway, spotless and far mid-phrase. VocalSet straight clips (14 files, 28 far notes, page code, 5.8 Hz/0.45 st asked): read back 5.78 [5.75-6.07] Hz, 0.41 [0.28-0.45] st, on the 9 files with a reading; 5 short-note scale clips gave no reading. 'Still your voice' proxy, not a listener: 1/3-octave long-term spectrum, 500 Hz-8 kHz, take vs far 1.43 dB median [0.38-5.20], vs spotless 1.23 [0.32-4.23], so far adds little beyond spotless. The first band floor (100 Hz) gave 5-11 dB, room noise under f0, so the floor was raised after seeing it. Far vision is pitch and level only: it does not model tone; naturalness unmeasured. iOS risk: none new (a third render lengthens the scan; time on a phone unmeasured). Next: vowels part 2 or singer's formant.

## 2026-10-30 · sung vowel, first benchmark of the formants

Built: `readVowel`/`spanVowel` with centres fitted on sung notes, `check/vowel-bench.mjs`, a live 'vowel' chip, 'sounds like “ee”' in note by note, only when sure. Formants had no measured accuracy until now. VocalSet (2405 notes, 20 singers, 5 vowels, page code): 68.2 ± 4.4 % under 600 Hz (speech centres 61.3 ± 4.8; left-out-singer 67.7 ± 4.5), sure 74.1 ± 5.4 % on 67 % of notes; no reading at 600 Hz and up. Not benchmarked on 0.5 s live windows; the synthetic demo 'ah' reads unsure (speech-table formants). check.mjs: reader, chip, note line, 3 browsers. Process: WebKit hangs intermittently even alone (one 170 s timeout, same code passed in about 50 s; cause not found), so a hung browser gets one retry, timeout 240 s. iOS risk: none new. Tried, not shipped: adding F3 or f0 to the centres, left-out-singer 66.4 / 67.9 / both 66.2 ± 4.7 % vs 67.7, no gain. One live WebKit run in check.mjs exited 1 with no message; rerun alone passed (cause not found). Next: back vowels from the envelope, singer's formant.

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
