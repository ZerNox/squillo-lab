# Voice Helix log

Newest first. Date, what was built, what a singer can now do, numbers, next.

## 2026-11-05 · vibrato by day; no-WebGL fix

Built: each live long note's vibrato rate and width (`laneVib`) is kept with the rest; the Lane's list adds "faster / slower vibrato" and "wider / narrower vibrato than your M from the last two weeks" (described, never marked better; floors 0.3 Hz, 20 %) and two more 14-day charts. `check/lane-days-bench.mjs` (page code, synthetic 5.0/5.8 Hz, 0.25/0.5 st, 5 % cycle jitter, five voices): read 5.00/5.79 Hz, 0.24/0.48 st; false change 0/400, steps 400/400, wrong way 0, no leak between rate and width (real cycle spread unmeasured). Firefox on this machine lost WebGL: the page threw and the frame loop never started, so the Lane, HUD and score were dead without WebGL; fixed (3D part skipped, 2D always runs). check.mjs: vibrato days. Chrome, Firefox (no WebGL), WebKit iPhone. Next: o/u vowels, or noise part 3.

## 2026-11-04 · swells by day; a low-band cue tried

Built: each live long note's swell width (`laneSwell`, dB) is kept with its wobble, start and ending; the Lane's list adds "Today's N long notes wider swells than / narrower than / level with your M from the last two weeks" (mean, 95 %, 3 dB floor, higher is better) and a fourth 14-day chart. `check/lane-days-bench.mjs` (page code, synthetic swells 0/8/16 dB, five voices): same-level false change 0/400, each step said 400/400, wrong way 0 (real note-to-note spread unmeasured). check.mjs: wider/level, kept width, dB chart; Chrome, Firefox, WebKit iPhone. Noise part 3 tried: a low-band energy share (below 1.5 kHz) gating live candidates left clean FA at 8.3 % (0.6) / 8.1 % (0.8) while RPA fell 94.0 → 93.3 / 91.2: the false alarms are not breaths or fricatives, not shipped. Next: o/u vowels, or noise part 3 at note edges.

## 2026-11-04 · starts and endings by day

Built: `laneTrend(list,now,k)` now reads starts and endings too (plain mean, interval floored at 0, linear axis); the Lane's list draws three 14-day charts (wobble, starts, endings), each with dots, 95 % bars and a screen-reader label. No new measurement (readings from lane-days-bench). check.mjs: a day without endings drops from that chart only. Chrome, Firefox, WebKit iPhone. Next: noise part 3, or o/u vowels.

## 2026-11-04 · long-note wobble by day

Built: `laneTrend`/`laneTrendSvg`: the Lane's list opens with a 14-day chart of live long-note wobble, one dot per day with 3+ notes (geometric mean) and its 95 % bar (same t as laneDays), log axis, today in teal, read out by screen readers. No new measurement (readings from lane-days-bench). check.mjs: day buckets, intervals, no chart under 2 days; day-bucketed checks pinned to noon (a midnight run flaked WebKit once). Chrome, Firefox, WebKit iPhone. Next: noise part 3, or o/u vowels.

## 2026-11-03 · starts and endings across days

Built: the long-note store also keeps each note's start and ending (|cents| from the note, as the Lane reads them), and the list adds "Today's N long notes cleaner starts / held better than your M from the last two weeks", mean with 95 % interval, 8 ¢ floor, same t rule. `check/lane-days-bench.mjs` (page laneStart/laneEnd, synthetic slides and falls 0/40/80 ¢, five voices): same level false change 0-5/400, wrong way 0; 0 vs 80 ¢ said 386/400 starts, 399/400 endings; 0 vs 40 ¢ 75 and 316/400 (the start reader sees a fraction of a 0.12 s slide). check.mjs: held better / level; Chrome, Firefox, WebKit iPhone. Next: noise part 3, or o/u vowels.

## 2026-11-03 · long notes across days

Built: `laneDays`/`laneKeep`: every live long note's wobble is kept on the device (`helix.lanenotes.v1`, 400 newest, in my data's copy, merge and delete); the Lane's list opens with "Today's 6 long notes steadier than your 14 from the last two weeks: wobble 1.2 ¢ (1.0-1.4) vs 2.0 ¢ (…)", or level / less steady, said only beyond 15 % and both intervals (t on the smaller side), 3 notes a side. `check/lane-days-bench.mjs` (page code, live laneSteady on synthetic notes, five voices): same wobble false change 7-11/400 day pairs (a plain 1.96 gave 31-39, dropped), half the wobble 388-400/400, wrong way 0. Real voices vary more note to note: unmeasured. check.mjs: level/steadier/silent and the line; Chrome, Firefox, WebKit iPhone. Next: noise part 3, or o/u vowels.

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

