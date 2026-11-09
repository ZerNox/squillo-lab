# Voice Helix log

Newest first. Date, what was built, what a singer can now do, numbers, next.

## 2026-11-09 · starts and measure on the roughest-start vowel

Built: the 'Clean starts on a vowel' step gets '♪ starts and measure': ten timed starts at one guide note (five on the vowel, five on "ah"), each read by the Lane's own `laneStart`; the vowel is named rougher or cleaner than "ah" only past both ± combined, and against the last five on the same vowel (`helix.stm.v1`, in my data). A singer hears whether their scoop on "ee" is really the vowel, and whether it is shrinking day to day. Synthetic check (all three browsers): starts gliding from 80 ¢ under read 56-60 ± 3 ¢, straight "ah" 0 ± 3 ¢. Next: a chart of starts over tries, like the vowel step.

## 2026-11-09 · warm-up: clean starts on the roughest-start vowel

Built: when the Lane's by-vowel starts line names a roughest-start vowel, the warm-up adds 'Clean starts on a vowel' (five starts on it, five on “ah”; pitch-matching source) with the reason shown, and its match-and-measure tones. A singer who scoops into “ee” gets a daily minute on exactly that. Same test, no new measurement (synthetic false 5/400 starts). check.mjs asserts the step and its absence when starts are alike. Next: read the vowel-start step back per vowel, like the vowel step.

## 2026-11-09 · starts and endings by vowel

Built: the Lane's list adds "By vowel, starts / endings, last two weeks: roughest starts on “ee”: …" with the by-vowel test (floor 8 ¢). A singer sees which vowel they scoop into or let fall off. Measured (`check/lane-days-bench.mjs`, page reads of synthetic slides, 12.4 % labels wrong): all alike, a claim 5/400 starts, 0/400 endings; one vowel at 2× slide named 98/400 starts, 175/400 endings. check.mjs asserts the starts line. Next: a warm-up onset step on the roughest-start vowel.

## 2026-11-09 · vowel step: drift over the last tries

Built: under the '♪ vowels and measure' result, a small chart of drift on that vowel over the last 10 tries, today last (dot ± bar, "ah" of each try as a tick; aria-label lists the numbers). A singer sees their weak vowel's steadiness trend at a glance, not only "steadier than last time". No new measurement (same drift ± as the line). check.mjs: no chart after one try, two dots after two. Next: per-vowel starts/endings.

## 2026-11-09 · vowel step kept across days

Built: each '♪ vowels and measure' result is kept on the device (`helix.vowm.v1`, in my data's save/restore/delete), and the line now adds "Steadier / Less steady / As steady as your last N times on “ee”" (mean ± of up to 5 earlier tries on the same vowel, change named only beyond both ±, the swell step's rule). A singer sees whether their weak vowel is getting steadier day to day. check.mjs runs the synthetic step twice: second read "as steady", 2 kept. Next: per-vowel starts/endings, or the vowel trend on the progress lines.

## 2026-11-09 · warm-up: vowels and measure

Built: the sustained-vowel step gets '♪ vowels and measure': 15 s at a guide note, "ah" / the least steady vowel / "ah", 5 s each. The page reads each part's drift (SD of 0.5 s pitch means, ± 95 %), says whether the vowel was less steady than the "ah" on either side (only when the gap is larger than both ± combined), and whether it was heard as that vowel (`spanVowel` when sure, 87.6 % on whole notes). A singer gets their weakest vowel's steadiness measured against their own "ah" in the same minute. Synthetic check (all three browsers): a middle part wobbling ±30 ¢ at 0.6 Hz reads 20 ± 12 ¢ against 0 ¢ for "ah", and is named. Next: keep vowel-step results across days, like the swell step.

## 2026-11-09 · warm-up: a sustained-vowel step on the least steady vowel

Built: when the Lane's two-week by-vowel line names a least steady vowel, the warm-up adds 'Sustained vowel' (ah, that vowel, ah; Titze & Verdolini Abbott 2012) with the reason shown. A singer whose "ee" wobbles gets a daily minute on it. Same test, no new measurement (synthetic false 7/400). check.mjs asserts the step and its absence when vowels are alike. Next: per-vowel starts/endings, or the vowel step read back like the swell step.

## 2026-11-09 · steadiest and least steady vowel, two weeks

Built: each live long note now keeps its vowel (when sure), and the Lane's list adds "By vowel, last two weeks: least steady on “ee”: 9.1 ¢ (…) vs 3.0 ¢" with the same extreme-widened test as the by-note line. A singer sees which vowel to give their steadiness work. Measured (`check/lane-days-bench.mjs`, synthetic live wobble, labels 12.4 % wrong as on VocalSet whole notes): all vowels alike, a claim 7/400; one vowel at 2× wobble named 238/400. check.mjs asserts the line and the stored vowel. Next: per-vowel starts/endings, or a warm-up vowel step from it.

## 2026-11-08 · the vowel of each live long note

Built: the Lane's list now says which vowel each long note (0.5 s or more) was sung on, "G4 1.2 s on “ah”", only when `envVowel` is sure over the whole note. A singer working on one vowel sees which notes were heard as it. Number used: whole notes on the live footing 87.6 ± 3.9 % (README, VocalSet). Also tried for u/o (page dump, left-out singer, base 84.0): ridge 0.01 84.2, F1/F2 × log f0 82.8-83.1, cubic f0 term 83.3-83.8: no gain, not shipped; the LDA looks saturated on these features. check.mjs asserts the label and that short notes get none. Next: a different vowel feature (cepstral envelope), or a finer-hop edge search.

## 2026-11-08 · phone: the Lane's list readable over the Lane

Built: on phones the Lane is fixed full-screen and its list of long notes scrolled over it, so text ran through the big note readout and the pitch line (seen on the iPhone screenshot). The list now sits on its own opaque panel above the readout. A singer scrolling the list on an iPhone reads it cleanly. No new measurement; check.mjs asserts panel order and opacity on touch. Chrome failed once on an element screenshot detached mid-render (unrelated, passed on rerun). Next: u and 400-600 Hz vowels, or a finer-hop edge search.

## 2026-11-08 · hear what got better this sitting

Built: each note the 'Getting better this sitting' line names gets '▶ G4: first, then latest', playing the sitting's first try and then the newest one still in the 30 s ring. A singer told that G4 got steadier can now hear the change. No new measurement (same Bonferroni line). check.mjs asserts the button on a steadier sitting and none on a level one. Next: u and 400-600 Hz vowels, or a finer-hop edge search.

## 2026-11-08 · eyes-free: the sitting's try-by-try line spoken

Built: `recapSay`: with say note on, the after-note recap also reads "Getting better this sitting, try by try: G4 steadier…" once, whenever that line changes. A singer with eyes closed or on a screen reader hears what is improving across repeated notes. Same Bonferroni test, no new measurement. Also tried: f0-banded vowel tables (cut 250-350 Hz): 83-84 %, 400-600 Hz 63-65 %, no gain, not shipped. Next: u and 400-600 Hz vowels, or a finer-hop edge search.

## 2026-11-08 · vowels: o read right 72 → 80 %

Built: `envVowel` now also weighs each envelope level by log(f0/250)², and the note's LPC F1 and F2 (re-fitted table, `check/vowel-fit.mjs`). A singer on "oh" sees the vowel chip, note-by-note line and 'vowels heard' get it right more often, and the chip is sure more often. Measured (VocalSet 20 singers, 2431 notes, page dump, left-out singer): 81.8 ± 4.1 → 84.0 ± 4.2 %, paired +2.3 ± 2.0, 14/20 better; o 72 → 80, u 75 → 76; sure 87.7 % on 84 % of notes (was 78 %); live 0.5 s window 88.1 → 89.7 %, sure on 47 → 51 %. Next: u and 400-600 Hz (66 %), or a finer-hop edge search.

