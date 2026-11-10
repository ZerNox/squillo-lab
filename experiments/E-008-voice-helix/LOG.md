# Voice Helix log

Newest first. Date, what was built, what a singer can now do, numbers, next.

## 2026-11-10 · key from a recording: octave errors no longer set the span

Built: `songSpan` keeps only the cluster of held semitones with the most time (a gap over 8 semitones splits), so a run of octave-up or octave-down pitch errors no longer stretches the span. A singer's suggested key from a recording now matches the hand annotation as often as two annotators match each other. Measured (`check/span-song-bench.mjs`, vocadito 40, vs A1): lowest exact 80 → 83 ± 12 %, highest 80 → 88 ± 10 %, shift exact 70 → 85 ± 11 %, within one 83 → 98 ± 5 % (annotators 88, 95); gap swept 4/6/8 on the same clips (6, 8 tie), so slightly optimistic. check.mjs: a 0.6 s octave-error D6 added to the synthetic melody, still G3-D5. Next: tone depth (formant-corrected H1-H2).

## 2026-11-10 · key from a recording

Built: the voice profile's 'Key for a song' gets '♪ from a recording': pick a sung or hummed recording of the melody, the page reads it on the device (take pitch, note segmentation), fills lowest and highest (semitones held 0.25 s or more in total, so a stray note does not set the span) and suggests the key. A singer no longer has to know the melody's notes to get a key that suits them. check.mjs: synthetic G3-D5 melody with a 0.1 s stray A5 reads G3-D5, down 7 to C. Real voices (vocadito 40, vs annotator A1's notes): lowest and highest exact 80 ± 12 % each (second annotator 83, 80), key shift exact 70 ± 14 %, within one 83 % (annotators 88, 95). Next: tone depth, or a sturdier shift (median of the held notes).

## 2026-11-10 · vibrato and measure

Built: an 'Even vibrato' warm-up step, added when the Lane's live long notes of two weeks (5+ with vibrato) have a median rate outside 4.5-7 Hz or width outside ±0.25-0.6 st; ▶ guide tone plays a 5.8 Hz ±0.45 st model to sing along with (King & Horii 1993); '♪ vibrato and measure' holds 8 s and reads rate ±, width and evenness with the page's `vibPiece`, kept (`helix.vibm.v1`), compared to the last 5 only beyond both ±, charted on the progress panel. A singer with a fast, tight bleat gets a daily minute on it and sees it move. check.mjs: synthetic 5.5 Hz ±0.45 st read within 0.15 Hz / 0.06 st, 'even', second try 'as even'; Lane at 7.8 Hz adds the step, 5.8 Hz does not. Next: tone depth (formant-corrected H1-H2) or the noise FA track.

## 2026-11-09 · warm-up steps on the progress panel

Built: under the progress lines, 'Warm-up, measured steps': pitch match, swell stillness, weak-vowel drift, vowel starts and siren span, each a small chart of the last 12 tries with ± bars and 'last 3 vs the 5 before: better / worse / level within the noise' (± in quadrature, claim only beyond both). A singer sees whether the daily warm-up is moving anything without opening each step. No new measurement. check.mjs: seeded falling match reads better, flat vowel drift level, single siren try no row. Next: a different track (vibrato or tone depth).

## 2026-11-09 · starts step: chart over the last tries

Built: under the '♪ starts and measure' result, a small chart of how far starts on that vowel were off over the last 10 tries, today last (dot ± bar, that try's "ah" as a tick; aria-label lists the numbers). A singer sees whether their scoop into "ee" is shrinking across days at a glance. No new measurement (same ± as the line). check.mjs: no chart after one try, two dots after two. Next: the starts and vowel trends on the progress lines.

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

