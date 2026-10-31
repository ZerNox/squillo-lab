# Voice Helix log

Newest first. Date, what was built, what a singer can now do, numbers, next.

## 2026-10-31 · high notes read right

Found by the match bench: from E5 up, straight notes read at a half or a third of the note, and nothing above about 1 kHz was searched. Octave folding had hidden the halves. Built: YIN searches to 1400 Hz (`F0MAX`), dips valued at sub-sample lag, candidates ranked with the Viterbi's lag cost so the true period stays in the top 8; `check/high-bench.mjs`, a check.mjs test. A soprano or child holding a high straight note now gets the right note. Page code, synthetic, C5-E6, four voice settings, frames within 50 ¢: 100 % everywhere; before, plain E5 63, G♯5 50, A♯5 38, C6-E6 0. vocadito 40 clips: RPA 97.6 ± 0.7 → 97.4 ± 0.8, FA 12.8 → 12.9, OA 94.3 → 94.1, low 97.3 same, high 97.8 → 97.4 (voices stop near F4, so a small cost and no direct test of the gain). Noise: pink 0 dB 63.0 → 64.0, hum 10 dB 88.2 same, speech 5 dB 73.6 → 73.3. Live bench unchanged (clean RPA 91.0, FA 15.0); live high straight notes unmeasured. iOS risk: none new. Next: real high-voice truth, or Timing part 2.

## 2026-10-31 · match and measure in the warm-up

Built: ♪ match and measure on the warm-up's Pitch matching and Clean starts steps (`matchGo`, `matchStats`, landing time in `tryRead`), `check/match-bench.mjs`. A singer hears five tones, sings each, and gets each note in ¢ with ±, how many landed, any overall flat or sharp lean, how fast they settled, the last sessions compared (better or worse only beyond both intervals) and a line of sessions, kept on the device. The warm-up used to listen to nothing. Page code, synthetic, 5 voices: landing error worst 55 ms straight, 75 ms vibrato, for scoops 0-400 ms, so the page rounds to 50 ms and says 'at once' under 80 ms. 40 sessions, 200 notes: truth inside ± 40/40, mean ± 17.8 ¢; SD 15.6 ¢ comes from one note at 830 Hz read 498 ¢ off, the other 199 within 12 ¢. Real voices unmeasured. Speaker tone stops before the capture, so no leak. iOS risk: as Sing it again, mic mode may route the tone quieter or to the earpiece. Next: Timing part 2.

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

