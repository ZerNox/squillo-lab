# Voice Helix log

Newest first. Date, what was built, what a singer can now do, numbers, next.

## 2026-11-06 · steadiest by note

Built: `laneByNote`: the Lane's list adds "By note, last two weeks: steadiest on C4 … least steady on E4 …", each note against the others pooled, with ± and an interval widened for picking an extreme. `check/lane-days-bench.mjs` (page code, synthetic live wobbles, 400 trials): false name 3/400 when alike; one note ×2 wobble named 360/400, ×½ 385/400. check.mjs: one note silent, alike silent, C4 named. Chrome, Firefox, WebKit iPhone. Next: o/u vowels, or noise part 3.

## 2026-11-06 · live long-note milestones

Built: a lifetime count of live long notes (`laneCount`, `helix.lanecount.v1`; the kept list stops at 400) with milestones at 10, 50, 100, 250, 500, 1000, 2500, 5000: the streak line says "N long notes held live (milestone: M), next: K", and the Lane's list announces "Milestone: your Mth long note held live" (status region) when one is crossed. The count travels in the my-data copy (restore keeps the larger) and is wiped with everything. No new measurement. check.mjs: 9 → 10 crosses once, 11 not, count 11 in backup and line. Chrome, Firefox, WebKit iPhone. Next: o/u vowels, or noise part 3.

## 2026-11-06 · live singing keeps the streak

Built: `streakInfo` counts a day with live long notes in the Lane as a day sung, so singing without recording keeps the streak; the line adds "N long notes held live" (minutes shown apart, never added to kept-take minutes) and now also heads the Lane's long-note list. No new measurement. check.mjs: lane-only days make a 4-day streak, take minutes unchanged. Chrome, Firefox, WebKit iPhone. Next: o/u vowels, or noise part 3.

## 2026-11-06 · warm-up from live long notes

Built: `warmLane`: the warm-up also reads the Lane's kept long notes; when the newest day with long notes (last 7 days) was less steady, started or ended further off than the singer's earlier two weeks (laneDays, same floors and intervals), it adds messa di voce, clean starts or hold to the end, says why, and works with no takes at all. `check/lane-days-bench.mjs` (page code, synthetic, 400 trials each): step added falsely 3/400 when all three level; wobble doubled 393/400 all right aspect; endings 80 vs 40 ¢ 362/400, 355 right aspect. check.mjs: added, level silent, no-takes text. Chrome, Firefox, WebKit iPhone. Next: o/u vowels, or noise part 3.

## 2026-11-05 · range by week

Built: `rangeWeeks`/`rangeWeeksSvg`: the voice profile draws the last 8 weeks, one bar per week for the full span held (takes and range finds) with the comfortable span inside, read out by screen readers; it says when the last two weeks' top or bottom held note moved a semitone or more past everything earlier (range finder 95 % within 1 st, range-bench), and never calls a quieter fortnight a shrink. No new measurement. check.mjs: up 3 st named, level and lower not, one week silent. Chrome, Firefox, WebKit iPhone. Next: o/u vowels, or noise part 3.

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

