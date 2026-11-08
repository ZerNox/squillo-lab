# Voice Helix log

Newest first. Date, what was built, what a singer can now do, numbers, next.

## 2026-11-08 · hear what got better this sitting

Built: each note the 'Getting better this sitting' line names gets '▶ G4: first, then latest', playing the sitting's first try and then the newest one still in the 30 s ring. A singer told that G4 got steadier can now hear the change. No new measurement (same Bonferroni line). check.mjs asserts the button on a steadier sitting and none on a level one. Next: u and 400-600 Hz vowels, or a finer-hop edge search.

## 2026-11-08 · eyes-free: the sitting's try-by-try line spoken

Built: `recapSay`: with say note on, the after-note recap also reads "Getting better this sitting, try by try: G4 steadier…" once, whenever that line changes. A singer with eyes closed or on a screen reader hears what is improving across repeated notes. Same Bonferroni test, no new measurement. Also tried: f0-banded vowel tables (cut 250-350 Hz): 83-84 %, 400-600 Hz 63-65 %, no gain, not shipped. Next: u and 400-600 Hz vowels, or a finer-hop edge search.

## 2026-11-08 · vowels: o read right 72 → 80 %

Built: `envVowel` now also weighs each envelope level by log(f0/250)², and the note's LPC F1 and F2 (re-fitted table, `check/vowel-fit.mjs`). A singer on "oh" sees the vowel chip, note-by-note line and 'vowels heard' get it right more often, and the chip is sure more often. Measured (VocalSet 20 singers, 2431 notes, page dump, left-out singer): 81.8 ± 4.1 → 84.0 ± 4.2 %, paired +2.3 ± 2.0, 14/20 better; o 72 → 80, u 75 → 76; sure 87.7 % on 84 % of notes (was 78 %); live 0.5 s window 88.1 → 89.7 %, sure on 47 → 51 %. Next: u and 400-600 Hz (66 %), or a finer-hop edge search.

## 2026-11-08 · this sitting, try by try, in one line

Built: `sittingTries`/`olsTrend`: above the Lane's list, "Getting better this sitting, try by try: G4 steadier, cleaner starts · A4 closer to the note" (or "Slipping: …"), from every pitch with 4+ tries. A singer sees at a glance what is improving across all the notes they repeat. Per-note tests over 12 cells falsely claimed something in 31 % of level sittings; fixed with an unweighted t line (± as residual floor) and a Bonferroni factor. Measured (`check/tries-bench.mjs`, 3 notes × 4 aspects, 400 sittings): all level 0/400, hidden spread 4-18/400, halved wobble named 23/400 (4 tries), 161/400 (6). Next: o/u vowels, or a finer-hop edge search.

## 2026-11-08 · tuning of one note, try by try

Built: `LTRYT`: each live long note now also keeps a ± on its tuning (spread of four quarter medians, floor 1 ¢), and the Lane's list shows "tuning of G4: 40 · 28 · 15 · 4 ¢ off the note, closer try by try (−Δ ± e)" with the same weighted trend. A singer working on one note's pitch sees it come in within a sitting; wobble, starts, endings and tuning all read try by try. Measured (`check/tries-bench.mjs`, synthetic, ± 1-6 ¢, hidden spread 3 ¢): level said 2-10 %, in tune 1-3/400, wrong way 0/400, halved 34-89 %. Next: o/u vowels, or a finer-hop edge search.

## 2026-11-08 · endings of one note, try by try

Built: `LTRYE`: the Lane's list also shows a pitch's endings this sitting, "endings of G4: 70 · 50 · 25 · 5 ¢ moved, held better try by try (−Δ ± e)", same weighted trend on |¢ moved as you let go| with the ending's ±. A singer working on holding to the end sees it settle within a sitting; tuning steadiness, starts and endings now all read try by try. Measured (`check/tries-bench.mjs`, synthetic, ± 6-15 ¢): level said 2-8 %, held endings 1/400, wrong way ≤ 1/400, halved 32-71 %. Next: o/u vowels, or a finer-hop edge search.

## 2026-11-08 · starts of one note, try by try

Built: `LTRYS`/`triesOne`: the Lane's list also shows a pitch's starts this sitting, "starts of G4: 60 · 40 · 20 · 5 ¢ off, cleaner try by try (−Δ ± e)", same weighted trend on |¢ off| with the start's ±. A singer working on clean onsets sees them settle within a sitting. Measured (`check/tries-bench.mjs`, synthetic, ± 6-15 ¢): level said 3-9 %, on-the-note starts 0-1/400, wrong way ≤ 1/400, halved 23-51 %. Next: o/u vowels, or a finer-hop edge search.

## 2026-11-08 · tries of one note, and an interior gate measured

Built: `LTRY`/`triesTrend`/`triesLine`: every live long note's wobble ± kept per pitch this sitting (numbers, memory); from the third try the newest reads "tries of G4: 9.0 · 6.1 · 3.2 ¢", from the fourth "steadier/less steady try by try (−Δ ± e ¢)" or "level across N tries" (weighted line, t interval when scatter exceeds the ±). A singer repeating one note sees whether it settles over the sitting. Measured (`check/tries-bench.mjs`, synthetic 400 per row): level falsely called 16-29/400 at 4-6 tries, wrong way ≤ 1/400, halved found 61-84 %. Depth tried first: take-pitch false alarms on vocadito (re-downloaded, baseline RPA 97.3, FA 13.1, OA 94.0): 60 % of FAs are inside voiced runs in 60-400 ms truth gaps; interior level-dip trims (run median, local max, plus YIN dip) all trade, best OA 94.7 at RPA 96.5; not shipped. Next: o/u vowels, or a finer-hop edge/onset search.

## 2026-11-08 · first try, then this

Built: `LFIRST`/`firstBtn`/`firstVs`: the first long note of each pitch this sitting is copied from the 30 s ring (memory only); each later try of that note gets "▶ first try, then this" (A/B through the steadiest player) and a line "steadier / less steady than your first G4", said only when the wobble difference is beyond both notes' ± combined, else "level with your first". A singer repeating one note hears and reads whether it is getting steadier within the sitting. Measured: check.mjs synthetic wobbles 9 → 3 ± 1 ¢ said steadier, 9 → 8.5 level, A/B plays both clips in full (Chrome, Firefox, WebKit iPhone). No new estimator (the Lane's wobble ±). iOS risk as before. Next: o/u vowels, or noise part 3.

## 2026-11-08 · hear a live long note as the next step

Built: `nextParts`/`nextNoteBtn`: a live long note whose tuning, start or ending was named gets "▶ next step" on the Lane's list: the note, then the same samples with each part moved half way to the note (`farRamp` with the parts halved, nothing added), so the reachable step sits beside the far vision. Memory only. Measured: synthetic A3 30 ¢ sharp, coming in 80 ¢ under, rendered offline: body 30 → 15.0 ¢, start -80 → -40.1 ¢ from the body (Chrome, Firefox, WebKit iPhone). Proxy only (pure tone). iOS risk as before (playback during mic stream). Next: o/u vowels, or noise part 3.

## 2026-11-07 · hear a live long note as the far vision

Built: `farParts`/`farRamp`/`farNoteBtn`: a live long note (1.4 s+) with two or more of: off the semitone, came in under/over, ending fell/rose, held straight, held level (one of the last two needed) gets "▶ far vision" on the Lane's list: the note, then the same samples in one rate curve (tuning × start × ending × the far vision's 5.8 Hz ±0.45 st vibrato, phase in output time) plus the 9 dB swell gain. Memory only. Measured: synthetic straight, level A3 30 ¢ sharp rendered offline: median 29 → 5.4 ¢, vibPiece 5.82 Hz, 0.43 st, swell 0.0 → 9.0 dB (Chrome, Firefox, WebKit iPhone). Proxy only (pure tone). iOS risk as before (playback during mic stream). Next: o/u vowels (needs VocalSet fetched), or noise part 3.

## 2026-11-07 · hear a thin live vibrato widened

Built: `laneNarrow` now also takes vibrato thinner than ±0.25 st (rate found): "▶ wider vibrato" on the Lane's list replays the note, then the same samples with each swing scaled up to the far vision's ±0.45 st by the same rate curve. Memory only. Measured: synthetic 5.5 Hz ±0.15 st A3 rendered offline, `vibPiece` read-back 0.149 → 0.450-0.453 st, 5.54 Hz (Chrome, Firefox, WebKit iPhone). Proxy only (pure tone). iOS risk as before (playback during mic stream). Next: o/u vowels, or noise part 3.

