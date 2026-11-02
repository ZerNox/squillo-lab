# Voice Helix log

Newest first. Date, what was built, what a singer can now do, numbers, next.

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

## 2026-11-02 · same phrase, seen as well as heard

Found: ▶ same phrase played the versions and gave numbers, but a singer could not see where they differ. Built: the found versions drawn over each other under the take: earlier dashed, today solid, in today's key by the matcher's half-step shift, each stretched to the same width, note names at the side, the sounding one bold with a playhead, a text alternative with median distance from today. Under the score line on a phone, so the first screen stays 177 px. check.mjs: a copy moved up 2 st returns shift -2 and lands on today's line (gap 0 st); Chrome, Firefox, WebKit. Linear stretch, so timing differences inside a phrase show as sideways offset; no new accuracy claim. iOS risk: canvas redraw per frame during playback, not measured on a phone. Next: noise part 3 or register transitions inside a take.

## 2026-11-02 · the scale of a take; aiming notes from the key, dropped

Tried: a note over 30 ¢ off, nearest a semitone outside the take's scale, read against the scale neighbour instead, so a 70 ¢ flat note is not called 30 ¢ sharp of the wrong one. `check/key-bench.mjs` (first form in git only as numbers here): Krumhansl-Kessler correlation at 90 % resample agreement, sure on 1-3 % of synthetic takes, 40-63 % right; scale by held time, 40-note takes sure 32 %, off notes aimed right 18.9 %, 0 plain notes moved; vocadito sure on 3/40 clips, 0/624 pushed notes restored, key held under pushes 57.5 %. Too rarely sure on real short melodies, so not shipped. Kept: 'Your notes fit the scale of G major / E minor' in the summary, from 30 notes at 90 % sure, no tonic claimed. Synthetic random walks, 600 takes each: 40 notes said 330, right 324 = 98.2 %; 60 notes said 462, right 462. Vocadito (no key labels, about 15 s clips): said on 2/40, agrees with annotator notes 2/2, so mostly silent on short takes. No iOS risk: note arithmetic only, 200 resamples at summary time. Next: noise part 3.

## 2026-11-02 · clarity follows the low notes

Found: CPP searched only to 60 Hz, so the newly read 55 Hz note had CPP 0, a false 'breathy'. Built: peak search to 46 Hz, baseline fit left alone (widening it moved 65 Hz by 4 dB and would have voided the VocalSet cue). Sawtooth 65, 82, 110 Hz read 26.6, 30.6, 31.2 before and after; 55 Hz 0 → 33.2, high from the extrapolated fit, so clear but not comparable under 65 Hz. Synthetic only. Next: noise part 3.

## 2026-11-02 · phone: score line on the first screen

Found: after a take, 15 controls wrapped to five rows on iPhone, and the score line started 270 px down. Built: under 720 px, two swipeable rows, right edge fading to show there is more; status text moved out of the row. Row top to score line 177 px (screenshot, iPhone 15 size), gated in check.mjs; every control still reachable, desktop unchanged. Cost: phrase and note tools need a swipe. iOS risk: mask with momentum scroll on a real phone, unseen. Next: noise part 3.

