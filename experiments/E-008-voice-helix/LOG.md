# Voice Helix log

Newest first. Date, what was built, what a singer can now do, numbers, next.

## 2026-10-31 · noisy rooms

Built: `roomFloor`, `roomSnr`, noise-compensated Viterbi (only under 14 dB voice over floor), a room line under Went well; `check/noise-bench.mjs`. A singer in a room with a fan or hum keeps most of their notes and is told when the room makes the numbers rougher. vocadito 40 clips, page code, RPA before → after: pink 10 dB 89.2 → 93.0, 5 dB 68.9 → 85.4 (FA 1.0 → 4.0), 0 dB 18.3 → 63.0; hum 10 dB 82.7 → 88.2; talk-like 5 dB 73.4 → 73.6, no gain; clean unchanged, 97.6 ± 0.7, FA 12.8. Room read within about 2 dB on steady noise, 10-13 dB high on talk-like noise, so the line names steady noise only. Settings tuned on these clips; added noise and simulated roll-off, no real phone or room; live tracker unchanged. iOS risk: none new. Next: same compensation on the live tracker, or talk-like noise.

## 2026-10-31 · Lane reads through vibrato

Built: on vibrato `laneRead` averages whole cycles of the last 0.7 s, ± from how far they differ; a singer with vibrato gets a steady note reading, not a swinging one. Lane bench, page code, synthetic, ±0.5 st, 4.5-7 Hz, 450 reads: median 2.2 ¢, max 4.8, ± 4, truth inside 97.1 % (0.4 s median at 5.5 Hz: 6.3, 23.2, ± 24). Real vibrato unmeasured. iOS risk: none new. Next: timing or tone, part 2.

## 2026-10-31 · Lane: a view to read while singing

Built: fifth view, Lane, reused from the failed attempt `wip/daily-20261031T022828`: the last 8 s as a flat line on a semitone grid, held note large with cents and ±, target note marked. A singer can read pitch at arm's length, on a phone too, without the 3D scene. `check/lane-bench.mjs`, page code, synthetic, 900 reads: straight median 0.4, max 1.1 ¢, truth inside ± 100 %; vibrato ±0.5 st median 6.3, max 23.2, ± 24, inside 96.9 %. No real-voice figure. check.mjs: lane reading, three browsers. iOS risk: none new. Next: Lane window of whole vibrato cycles, to tighten the ±.

## 2026-10-30 · repeated notes closed; vowels heard

Tried, not shipped: splitting `segNotes` at spectral change (`henv`, ±100 ms, thresholds 4-10 dB, gap 0.12/0.2 s), vocadito 40 clips, page code: COnP 68.0-74.2 vs 74.2 ± 2.7, COnPOff never above 60.2. `segNotes` already matches the second annotator (74.0), so the roadmap item is closed. Built: 'Vowels heard' under Went well, sure notes only, from 5 notes; a singer sees which vowels the take used. No new measurement. iOS risk: none new. Next: timing part 2 or tone part 2.

## 2026-10-30 · vowels from the harmonic envelope

Built: `harmEnv` (harmonic levels at 14 log points, 250-4500 Hz, each frame), `envVowel` (LDA, tilt removed, plus f0) behind `spanVowel`; formant picks stay as fallback; `check/vowel-dump.mjs`, `check/vowel-fit.mjs`. The live chip and note by note now name a vowel far more often and rightly, back vowels most. VocalSet, 2354 notes, 20 singers, page code, left-out singer: 78.5 ± 4.5 % vs 67.7 ± 4.5; o 64, u 72 (LDA on formants alone: 55, 57); sure 85.2 ± 4.7 % on 74 % of notes (was 74.1 on 67). Kept tilt scored 82.5 but 76 under a ±3 dB/oct slope, so removed: a phone mic's slope is unmeasured otherwise. 0.5 s window 82.1 ± 5.1 (fitted on same notes, optimistic). One recording chain, five vowels; other mics and languages unmeasured. iOS risk: none new. Live WebKit: passed on the 5th try (two full runs and one lone run hung, as in earlier reports; a local lone run hung too, same intermittent hang); Chrome, Firefox live pass. Next: repeated-note splits by spectral change, using `henv`.

## 2026-10-30 · sing it again

Built: under the furthest-off note in the summary, '🎙 sing it again': hear that note tuned in your own voice, sing 4 s, read it against the same note (`tryRead`: longest note, median ¢, ± over 0.25 s blocks, 3 ¢ floor), tries listed with 'x ¢ closer than in the take' only beyond the ±. A singer can now fix a note on the spot and see it. Pitch matching (Hutchins & Peretz 2012). `check/drill-bench.mjs`, page code: synthetic (5 voices A2-E5, offsets ±60 ¢, scoop, noise) straight SD 1.5 ¢, max 3.8, truth inside ± 29/30, median ± 3.0; vibrato ±0.5 st bias -1.5, SD 2.1, max 6.5, 30/30, median ± 9.9. VocalSet, 20 long tones resampled by -40 and +25 ¢ (same take, so this is shift recovery, not a true-pitch figure): SD 0.9 ¢, max 2.4, 40/40. check.mjs: stubbed mic with a note 10 ¢ sharp reads 10 ± 3, 3 browsers. Tries are not stored. iOS risk: the tuned note plays with the mic open, which can route quieter on a real iPhone; unmeasured. WebKit hung again in two lone runs and passed in the next two (same code). Next: repeated-note splits, vowels part 2.

## 2026-10-30 · repeated notes: level dips tried, not shipped

Splitting `segNotes` notes at level dips, vocadito 40 clips, page code, no dip vs dip 3/4/6/8/10/14 dB: COnP F 74.2 vs 72.9/73.4/73.5/73.8/73.9/74.0 (± 2.7); recall rises at most 2.2 points, precision falls up to 5.7; COnPOff peaks at 60.7 vs 60.1, inside the ±. Nothing shipped, page unchanged. Next: vowels part 2.

## 2026-10-30 · notes as a person would mark them

Built: `segNotes` (optimal partitioning of each voiced run, 7-frame median, penalty 4, notes from 60 ms) for the timeline, note by note, best notes and timing; `check/notes-bench.mjs`. First note-level benchmark: the old splitter found 806 of 2237 hand-marked notes. vocadito, 40 clips, page code, A1 as truth, F ± 1.96 SE: COnP 36.7 ± 5.3 → 74.2 ± 2.7 %, COn 36.9 → 82.7 ± 2.2, COnPOff 26.6 → 60.1 ± 3.5; second annotator against A1: 74.0 ± 2.9 / 81.7 ± 2.1 / 64.2 ± 4.0. Penalty and 40 ms lag were chosen on these clips (odd/even folds 72.7/72.5 with near-final settings), so slightly optimistic. Vibrato: VocalSet vibrato arpeggios median 9 notes (old 9), scales 18 (old 17); synthetic ±1 st at 5.5 Hz one note, ±1.5 st at 4 Hz splits to 3. Timing now uses these onsets: legato floor 31 → 12 ms, gapped 10 → 6, false pulse 0/40; vocadito pulse page 5, truth 7, both 3 (weak as before). A singer gets every note in a quick phrase, not just long ones. Intonation, stability and drift stay on `takeNotes`: their calibration is unchanged. Note score history mixes old and new lists. iOS risk: none new. Tried, not shipped: key drift on `segNotes` (notes 0.2 s or more): vocadito page vs truth SD 62 ¢ against 41 now; short notes bring more grid ambiguity. Process: WebKit hung intermittently again, on the unchanged page too (control run); outer timeouts under about 600 s cut off check.mjs's own retries. Next: vowels part 2, repeated-note splits.

## 2026-10-30 · yours, then far

Built: 'Where this can go' in the summary: '▶ yours, then far' loops the take's longest note (0.8 s or more) as sung, then in far vision; `abLoop` takes a target version. A singer hears the far point on their own note in one tap. check.mjs: button, loop, 3 browsers. No new measurement. iOS risk: none new. Next: vowels part 2.

## 2026-10-30 · ring: singer's formant, first measurement

Built: singing power ratio per frame (`spr`, Omori 1996), `aspects.ring`, a 'ring' line in the summary and a progress row, described, not rated; `check/ring-bench.mjs`. A singer now sees how much 2-4 kHz energy their voice carries, take by take. VocalSet (page code, no singer's-formant label exists, so contrasts are proxies): forte vs pp AUC 0.85, pairs 19/20, -18.4 vs -28.1 dB; straight vs breathy AUC 0.82, pairs 16/19, -18.5 vs -26.0 dB; first vs second half r 0.89 (79 clips). Not fully gain-free: at -12 dB the worst clip shifted 5.5 dB (frames gated differently), so small changes between sessions mean little. SPR rises with loudness; the line says so. No live chip. Process: one WebKit run closed its page mid-check (same as earlier reports, cause not found); WebKit alone passed. iOS risk: none new. Next: vowels part 2.
