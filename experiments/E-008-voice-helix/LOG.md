# Voice Helix log

Newest first. Date, what was built, what a singer can now do, numbers, next.

## 2026-10-31 · fewer false notes live

Built: live voicing limit 0.3 in a quiet room, rising with the noise's share of the frame (`LN.V`, `LN.K`, was 0.65); `check/breathy-live-bench.mjs`. A singer's live line shows fewer ghost notes in gaps and breaths. vocadito 40 clips, page code, live: clean FA 24.1 → 14.9 ± 3.2, RPA 89.5 → 91.0 ± 3.5, OA 85.2 → 89.1 ± 2.8; pink 10 dB OA 87.3 → 87.4, FA 5.3 same; hum 10 dB OA 84.8 same. Cost: synthetic very breathy note in a quiet room, HNR 0 dB, read 32 → 0 % of frames (HNR 5 dB 25 % same, 10 dB and up 100 %); real extreme breathy voices unmeasured. Limit tuned on 10 of the clips. Local WebKit hung twice in full runs, passed alone first try; live WebKit passed on the 4th lone run (known intermittent hang), Chrome and Firefox first try. iOS risk: none new. Next: Timing part 2.

## 2026-10-31 · live pitch in noisy rooms

Built: the live level gate drops from 3× to 1.5× the calibrated room level (`LN.G`); `check/live-noise-bench.mjs`, a live gate check in check.mjs. A singer in a room with a fan or hum now keeps their pitch line live; before, the gate shut out most singing below 10 dB over the room. vocadito 40 clips, page code, live mode, 2 s calibration, no Viterbi, RPA before → after (FA after): pink 10 dB 47.5 → 83.6 (5.3), 5 dB 6.0 → 64.0 (1.5), 0 dB 0.1 → 21.7; hum 10 dB 39.9 → 78.9 (3.8); talk-like 10 dB 62.1 → 80.1, 5 dB 16.2 → 55.3; pink 20 dB OA 89.3 both, FA 9.5 → 14.7; clean unchanged, RPA 89.5 ± 4.4, FA 24.1 ± 4.7. Raising YIN's dip limits by the noise share (tried on 10 clips, 1.3×): pink 5 dB OA 79 vs 73, but 20 dB OA 83 vs 90, not shipped. Gate chosen on 10 of these clips, so slightly optimistic; added noise, no real room. Clean FA of 24 % is the live tracker's own weakness. iOS risk: none new. Next: live false alarms in quiet, or Timing part 2.

## 2026-10-31 · drone to sing against

Built: ♪ drone (D) by the target note: a soft held tone on the target, follows it; with no target it takes the held note, else A3. A singer can hear the tone and hold against it, with the Lane giving cents. `check/drone-bench.mjs`, page code, synthetic, 5 voices, ±10-40 ¢, leak into the mic vs the voice, reading error median/max: -18 dB 0.3/1.4 ¢ straight, 0.5/2.5 vibrato; -12 dB 0.9/4.8, 1.6/4.4; -6 dB 5.2/13, 5.5/12.7 (pulled toward the drone). An octave-below drone read 1200 ¢ off from -20 dB, so unison only. Real leak on phone speakers unmeasured; the button's title advises headphones. Drone studies found are on instrumentalists and show weak or mixed effects (Warnet et al., wind players, no effect on intonation), none on singers, so the page claims no training gain. check.mjs: starts, retunes, stops, 3 browsers. iOS risk: a second AudioContext beside the mic; may route quieter or to the earpiece. Next: noise part 2 on the live tracker.

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
