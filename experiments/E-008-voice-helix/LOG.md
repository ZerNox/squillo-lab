# Voice Helix log

Newest first. Date, what was built, what a singer can now do, numbers, next.

## 2026-11-03 · live vowel chip re-measured

Built: `check/vowel-live-bench.mjs` runs the page's `spanVowel` on the live chip's 0.5 s window (ending at the middle, three quarters and end of each note) on VocalSet (CC BY 4.0, 1136 notes, 20 singers). With this morning's f0 terms: 83.0 ± 5.3 → 88.1 ± 3.9 %, 'sure' 90.0 → 92.8 % on 47 % of windows (table fitted on these singers: optimistic). The chip now says 'best guess, 7 in 8 right' (left-out-singer sure figure), was '5 in 6'. check.mjs checks the claim; Chrome, Firefox, WebKit iPhone. Next: noise part 3, or o/u.

## 2026-11-03 · vowels read better at every pitch

Built: the sung-vowel table (`envVowel`, `check/vowel-fit.mjs`) adds each envelope level times log(f0/250), so the reader follows how a vowel's envelope shifts with pitch. VocalSet (CC BY 4.0, 2327 notes under 600 Hz, page dump, left-out singer): 78.4 ± 4.6 → 81.8 ± 4.0 %, paired +3.4 ± 1.6 points (14/20 singers better); o 63 → 71 %, u 74 → 75; 'sure' 87.5 % on 78 % of notes (was 85.9 on 73). Tried and dropped: formants added (80.6), envelope deltas (78.7). check.mjs: tilt still ignored at 450 Hz; Chrome, Firefox, WebKit iPhone. Live 0.5 s window not re-measured. Next: noise part 3 or live-window vowel bench.

## 2026-11-03 · long notes this sitting

Built: `logRecap`: every long note's after-note readings (start, ending, vibrato, steadiness, swell) also go on a "Long notes this sitting" list beside the Lane (below it on a phone), newest first, 8 kept, with note name and length, personal bests in green, readable by screen readers; the 4 s Lane lines no longer vanish for good. check.mjs: one line per note, shown in the Lane; Chrome, Firefox, WebKit iPhone. No new accuracy claim. Also tried (noise part 3): the take's note-edge trim run live with one hop of look-ahead (`check/live-noise-bench.mjs`, vocadito 40 clean): level 0.2 FA 8.3 → 7.5, RPA 94.0 → 93.6, OA 93.2 flat; 0.3 FA 6.9, RPA 92.9, OA 93.0: trades again, not shipped. Next: noise part 3 needs a non-level cue.

## 2026-11-03 · after-note recap, eyes free

Built: `noteRecap`: with say note (N) on, 0.3 s after a long note stops, the live region reads "Last note: landed right on the note; held to the end; vibrato 5.6 Hz ±0.2 …; swell 19 dB …" once, in or out of the Lane, so a singer with eyes closed or a screen reader gets every after-note line the Lane shows (it was aria-hidden). check.mjs: recap after stop, none while sounding or at 0.1 s; Chrome, Firefox, WebKit iPhone. No new accuracy claim (the lane readers' benches). Risk: speech through speakers reaches the mic, as say note already did; headphones advised. Next: noise part 3.

## 2026-11-03 · live swell in the Lane

Built: `laneSwell`: when a note of 1 s or more stops, the Lane says "swell 19 dB ±2, peak near the middle, a real messa di voce" or "held level", so a singer practising messa di voce hears the width and shape of each swell as they sing it. `check/lane-swell-bench.mjs` (page code, live frames, synthetic 150 notes, 5 voices): error mean within 0.9 dB (max 3.1), truth inside ± 138/150, peak place 90/90, live = take within 0.5 dB; 'messa di voce' 28/30 at 20 dB, 0 at 14 and under. The first ± (frame noise only) held 9/30 at 20 dB; 8 % of width added. check.mjs: swell and level; Chrome, Firefox, WebKit iPhone. No real-voice figure. Next: noise part 3.

## 2026-11-03 · steadiest on this device, live

Built: the Lane's steadiness line also says "steadier than any long note in your N kept takes (best X ¢)" when a long note beats the steadiest long note of every kept take by more than 1 ¢ and its ± (the summary's personal-best rule, 2 kept takes at least), so a personal best is felt on the note itself. check.mjs: said with 3 takes, not with 1, not on a 4 ¢ note against a 4 ¢ best; Chrome, Firefox, WebKit iPhone. No new accuracy claim (wobble as the entry below). Next: noise part 3.

## 2026-11-03 · live steadiness in the Lane

Built: `laneSteady`: when a note of 1 s or more stops, the Lane says "steadiness 1.3 ¢ wobble · ±0.5", and "your steadiest of N long notes" in green when it beats this sitting's best beyond 1 ¢ and both ±, so a singer working on steadiness feels progress note by note. `check/lane-steady-bench.mjs` (page code, live frames, synthetic 120 notes, 5 voices): wobble SD 0/4/8/16 ¢ reads 0.1/0.7/1.3/2.6 ¢ (vibrato 0.5/0.7/1.5/2.8), live = take within 0.2 ¢; 'steadiest' false 0/144, right 17/18. check.mjs: named, best, not best, silent while sounding; Chrome, Firefox, WebKit iPhone. No real-voice figure. Next: noise part 3.

## 2026-11-03 · live vibrato in the Lane

Built: `laneVib`: when a note of 1 s or more stops, the Lane says "vibrato 5.6 Hz ±0.2 · 0.45 st wide, even" or "held straight, no vibrato" for 4 s, the take's estimator on the live frames, so a singer working on vibrato hears about each note as they sing, not only after the take. `check/lane-vib-bench.mjs` (page code, live frames, synthetic 120 notes, 5 voices): straight 40/40 straight, never vibrato; even vibrato rate max 0.04 Hz, width 0.03 st off, truth inside ± 37/40, even 40/40; ±30 % cycle jitter uneven 15/40. check.mjs: vibrato and straight notes; Chrome, Firefox, WebKit iPhone. No real-voice figure. Next: noise part 3.

## 2026-11-03 · next step for endings

Built: `improveTake(…,'endings')` moves the last 0.26 s of each long note half way back to the note (fading tail carried 4 frames), the rest as sung; `nextKindOf` picks it when the summary names note endings, starts are not leading and tuning is under 20 ¢; 'Your next step' names it with ▶ yours, then next step on the note that moved most. `check/next-end-bench.mjs` (page code, synthetic 50 takes, 5 voices): -80 ¢ fall -36.8 → -25.5 ¢ (render alone -46.4), -40: -19.1 → -12.6, +40: 17.0 → 12.5, level unchanged; picked 10/10 at -80, 0 on level. Without the tail carry the render read back no change (-37.1), fixed. check.mjs: falling take reads -42 → -26 ¢, rule picks endings; Chrome, Firefox, WebKit iPhone. No real-voice figure. Next: noise part 3.

## 2026-11-03 · next step for starts

Found: the next step only ever moved tuning, so a singer whose main habit is scooping into notes heard a step that did not touch it. Built: `improveTake(…,'starts')` makes each scoop's rise half as deep (frames under the settled pitch in a run's first 0.3 s), the rest as sung; `nextKindOf` picks it when scoops are on 25 %+ of notes (not a slide style) and tuning is under 20 ¢; the summary's 'Your next step' names it with ▶ yours, then next step on a scooped note. `check/next-start-bench.mjs` (page code, synthetic 30 takes, 5 voices): 3 st scoops 0.50 → 0.00 scoops per note, render alone 0.50 [0.25-0.50], tuning 16.3 → 18.5 ¢; 1.8 st scoops are under the scan's line, read 0 before and after. check.mjs: a scooped take reads fewer scoops after the render, rule picks starts, not on clean or off-tune takes; Chrome, Firefox, WebKit iPhone. No real-voice figure; the readback is all-or-nothing at the 1.5 st line. Next: noise part 3.

## 2026-11-02 · note endings, heard held

Found: spotless kept about two thirds of a sag at a note's end (its 250 ms median and the last voiced frame), so an A/B would not have let the singer hear the difference. Built: spotless holds the last 0.26 s of a long run at the pitch before it, and carries it 4 frames past the last voiced frame; the note-endings point in the summary names the note that moved furthest and offers "▶ yours, then held". `check/tailfix-bench.mjs` (page code, synthetic): -80 ¢ take -37.1 → spotless -3.3 ¢, -40: -19.1 → 0.3, +40: 17.0 → 1.1, level unchanged; picked note right way 30/30. check.mjs: picked note and held render; Chrome, Firefox, WebKit iPhone. No real-voice figure. Next: noise part 3.

