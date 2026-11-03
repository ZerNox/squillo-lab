# Voice Helix log

Newest first. Date, what was built, what a singer can now do, numbers, next.

## 2026-11-03 · next step for endings

Built: `improveTake(…,'endings')` moves the last 0.26 s of each long note half way back to the note (fading tail carried 4 frames), the rest as sung; `nextKindOf` picks it when the summary names note endings, starts are not leading and tuning is under 20 ¢; 'Your next step' names it with ▶ yours, then next step on the note that moved most. `check/next-end-bench.mjs` (page code, synthetic 50 takes, 5 voices): -80 ¢ fall -36.8 → -25.5 ¢ (render alone -46.4), -40: -19.1 → -12.6, +40: 17.0 → 12.5, level unchanged; picked 10/10 at -80, 0 on level. Without the tail carry the render read back no change (-37.1), fixed. check.mjs: falling take reads -42 → -26 ¢, rule picks endings; Chrome, Firefox, WebKit iPhone. No real-voice figure. Next: noise part 3.

## 2026-11-03 · next step for starts

Found: the next step only ever moved tuning, so a singer whose main habit is scooping into notes heard a step that did not touch it. Built: `improveTake(…,'starts')` makes each scoop's rise half as deep (frames under the settled pitch in a run's first 0.3 s), the rest as sung; `nextKindOf` picks it when scoops are on 25 %+ of notes (not a slide style) and tuning is under 20 ¢; the summary's 'Your next step' names it with ▶ yours, then next step on a scooped note. `check/next-start-bench.mjs` (page code, synthetic 30 takes, 5 voices): 3 st scoops 0.50 → 0.00 scoops per note, render alone 0.50 [0.25-0.50], tuning 16.3 → 18.5 ¢; 1.8 st scoops are under the scan's line, read 0 before and after. check.mjs: a scooped take reads fewer scoops after the render, rule picks starts, not on clean or off-tune takes; Chrome, Firefox, WebKit iPhone. No real-voice figure; the readback is all-or-nothing at the 1.5 st line. Next: noise part 3.

## 2026-11-02 · note endings, heard held

Found: spotless kept about two thirds of a sag at a note's end (its 250 ms median and the last voiced frame), so an A/B would not have let the singer hear the difference. Built: spotless holds the last 0.26 s of a long run at the pitch before it, and carries it 4 frames past the last voiced frame; the note-endings point in the summary names the note that moved furthest and offers "▶ yours, then held". `check/tailfix-bench.mjs` (page code, synthetic): -80 ¢ take -37.1 → spotless -3.3 ¢, -40: -19.1 → 0.3, +40: 17.0 → 1.1, level unchanged; picked note right way 30/30. check.mjs: picked note and held render; Chrome, Firefox, WebKit iPhone. No real-voice figure. Next: noise part 3.

## 2026-11-02 · note starts, live in the Lane

Built: `laneStart`: 0.45 s into a note the Lane says "landed right on the note" or "came in 60 ¢ under, then found it · ±8", so a scoop is named while the note still sounds (endings were named only after). `check/lane-start-bench.mjs` (page code, live frames, synthetic): level said 0/80, wrong way 0/480, straight ±80 ¢ said 80/80, 'landed' never on a moved start; vibrato starts said 50/240; first try (mean of the start, its own spread as ±) never said a straight scoop, replaced. check.mjs: scooped, level and too-early notes; Chrome, Firefox, WebKit iPhone. No real-voice figure. Next: noise part 3.

## 2026-11-02 · warm-up for the described points

Found: the warm-up chose steps only from the rated aspects (tuning, steadiness, starts), so a singer whose takes kept naming note endings, key drift, clarity or rhythm got no step for them. Built: a point named in at least 2 of the last 5 takes (or the only take) fills a free targeted slot: 'Hold to the end' (Titze & Verdolini Abbott 2012), 'Keep the key' (Howard 2007), 'Straw, then open' (Titze 2006), 'Clap, then sing' with a click guide (Repp 2005); the intro says how often it was named. check.mjs: seeded histories pick the right steps, none without names; Chrome, Firefox, WebKit iPhone. No accuracy claim (choice rule only). Next: noise part 3.

## 2026-11-02 · note endings, live in the Lane

Built: `laneEnd`: when a held note (0.5 s+) stops, the Lane names its ending for 4 s, "held to the end" or "fell 40 ¢ as you let go · ±12", so the singer hears about a sag on the very note, not only after the take. `check/lane-end-bench.mjs` (page code, live frames, synthetic): level said 0/40, wrong way 0/240, -80 ¢ said 27/40 (vibrato 7/20), reads about half the move. check.mjs: falling, level and still-sounding notes; Chrome, Firefox, WebKit iPhone. No real-voice figure. Next: noise part 3.

## 2026-11-02 · note endings over takes

Built: note endings (¢ off at the ends of long notes, either way) kept with each take: a progress line with its band, the week lines, and 'since your last take' when it was the point named; shown, not rated. check.mjs: 12 seeded takes from 40 to 7 ¢ read 'better', the row exists, not rated; Chrome, Firefox, WebKit iPhone. No new accuracy claim (per-take reading as below). Next: noise part 3.

## 2026-11-02 · note endings

Found: nothing read whether pitch sags (or lifts) as a long note is let go, a common habit the singer cannot hear in the moment. Built: `takeTail`: per note of 0.5 s or more, the last 0.18 s against the body, take mean ± 1.96 SE; the summary praises "held their pitch to the end" or names the sag with ± and an exercise (stop the air, not the note, over the drone; messa di voce; Titze & Verdolini Abbott 2012), saying a fall-off may be style. `check/tail-bench.mjs`: synthetic 0.2 s falls read about 0.46 of the move; -80 ¢ said 10/10, level 0/10 false and praised 10/10, wrong way 0/60; vocadito page vs hand f0 -2.7 ¢ (SD 9.7), says 3 of 20, hand 2, 0 opposite (8-note gate set on those clips). check.mjs: a falling and a held 10-note take; Chrome, Firefox, WebKit iPhone. Next: noise part 3, or note endings live and in the progress lines once real use shows it is said often enough.

## 2026-11-02 · save audio on a phone: the share sheet

Found: on iOS Safari a blob download opens a preview, not a saved file (named as a risk last run). Built: on a touch screen where `navigator.canShare({files})` holds, ⤓ hands the same WAV to the share sheet (Files, Voice Memos, a message); closing the sheet says "not saved", any other share error falls back to the download; desktops download as before. check.mjs, with share stubbed: the shared file decodes to the playing version's length, close and fallback paths; Chrome, Firefox, WebKit iPhone. iOS risk: the real share sheet is not reachable headless; the WAV is built synchronously inside the click so the gesture holds. Next: noise part 3, or register (falsetto vs chest) once labelled clips are on hand (none locally).

## 2026-11-02 · save audio

Found: a singer could hear their take, next step, spotless and far vision only inside the page. Built: ⤓ save audio writes the version last played, at the chosen speed (WSOLA), as a 16-bit mono WAV made in the page, never uploaded. check.mjs: the saved file decodes back to the same length and sample rate as the playing version, named `voice-helix-<date>-<version>.wav`; Chrome, Firefox, WebKit. Register classifier inside a take considered and left: no falsetto-labelled clips on hand. iOS risk: Safari shows a download sheet for blob links rather than saving silently; not tried on a phone. Next: noise part 3, or register (falsetto vs chest) from VocalSet labels.

