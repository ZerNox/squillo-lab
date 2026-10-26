# Voice Helix log

Newest first. Date, what was built, what a singer can now do, numbers, next.

## 2026-10-26 · live vibrato chip on the take estimator

Built: the vibrato chip while singing now uses the take's estimator (note-change cuts, detrend, autocorrelation) on the last 1.2 s of the current note, so legato steps no longer show as vibrato. Numbers (`check/vibrato-bench.mjs`): per-note rate error median 0.07 → 0.04 Hz, p90 0.13 → 0.11; 0/30 straight notes flagged; take figures unchanged. iOS risk: a little more work per frame (about 60 frames × 14 lags), small. Next: vibrato regularity.

## 2026-10-26 · vibrato rate and extent, measured

Built: the take summary says "Vibrato on n of N long notes: rate ± Hz, ±extent st" against trained singers' 5.5-6.5 Hz (Prame 1994), or praises a plain straight line. Estimated from the take's pitch (note-change cuts, quadratic detrend, first autocorrelation peak). Found while building: the live chip's 1.2 s zero count, run over a take, read legato note steps in a straight aria as 4 Hz vibrato. Numbers (`check/vibrato-bench.mjs`, page code): synthetic take means within 0.11 Hz / 0.03 st over 5 voice types, 0/30 straight notes flagged; VocalSet Caro vibrato 5.3 / 5.0 Hz. check.mjs: 6 Hz ±0.5 st take reads 6.0 Hz, 5 of 5 notes. iOS risk: none new. Next: live chip on the same estimator.

## 2026-10-26 · same phrase across all kept takes

Built: the earlier-take picker has "all N kept takes"; ▶ same phrase then
finds the phrase in each kept take (up to 10), plays the versions found
oldest first and today's last, and lists each version's cents off (± 1.96 SE)
plus first-vs-today. A singer can now hear one line's history in one go.
Numbers: matcher as above (95.0 ± 3.9 % found, proxy). check.mjs: 2 of 2
found in 3 browsers. iOS risk: tracking 10 stored takes can take several
seconds on a phone (progress shown). Next: rating truth, or edge onsets.

## 2026-10-26 · same phrase in numbers

Built: ▶ same phrase now also says how the phrase's held notes measured then
vs today: mean |cents off| and wobble, each ± 1.96 SE over its notes, and
scoops; "better"/"worse" only when the means differ by more than both ±.
Found while building: the same audio re-read at 22.05 kHz gave 16 vs 11 ¢ on
WebKit, so a fixed 5 ¢ threshold would have claimed a change that was noise.
check.mjs: same audio → "within the ±" in 3 browsers. iOS risk: none new.
Next: phrase across all kept takes.

## 2026-10-26 · same phrase, then and now

Built: ▶ same phrase plays the phrase around the current note as sung in the
picked earlier take, then today's. The phrase is found by subsequence DTW on
the pitch contour at transpositions ±6 st, rejected above 0.4 st mean cost.
Measured (page code, `check/phrase-bench.mjs`, vocadito proxy: same clip at
0.8× + noise): 95.0 ± 3.9 % of 120 phrases found, impostors accepted 3.3 ±
3.2 %. Bug fixed: earlier takes were stored silent (OfflineAudioContext render
of an already-played buffer gave zeros in Chrome); toPcm now resamples by hand.
Edge-trim sweep (E 0.2-0.3, EN 2-4): OA flat 94.3-94.4, not changed. iOS risk:
DTW on a 6 min take is ~0.5 s on the main thread. Next: phrase across all takes.

## 2026-10-26 · mark moments

Built: ⚑ mark button and M key drop a flag on the take bar where the take is
playing (or at the note just stepped to); flags are kept per take in
localStorage (last 50 takes), a click plays from 1 s before, a double-click
removes. A singer can now flag "that bit" while listening and come straight
back to it, today or later. Numbers: none (playback). check.mjs: mark lands on
the playing note, is stored, and plays, in 3 browsers. iOS risk: double-tap to
remove may zoom on some iOS settings (touch-action untested on device).
Next: compare the same phrase across takes, or rating truth.

## 2026-10-26 · sharper note edges

Built: `trimEdges`: the first and last 2 frames of each voiced run are
unvoiced when a short window (2 periods, ≥ 10 ms) centred where the pitch
belongs is below 0.2 × the run's median level (the 40 ms window heard the
note after it ended). Measured (page code, vocadito): false alarm 17.1 →
12.8 ± 2.9 %, overall 93.2 → 94.3 ± 1.0 %, RPA 98.1 → 97.6 ± 0.7 %; range
bench unchanged. Notes on the bar and in note-by-note now stop where the
singer stopped. iOS risk: none. Next: finer hop at edges, or rating truth.

## 2026-10-26 · note by note

Built: ◀ note / note ▶ buttons and ← → keys step through a take's held
notes; each plays alone (padded 0.15 s) in the version last played (take,
halfway, spotless, at the chosen speed), is outlined on the bar, and its
numbers are read out (cents off, wobble, scoop or clean start, ★). A singer
can now walk a phrase note by note and hear exactly which note slipped.
Numbers: none (playback). check.mjs: steps, bounds and key in 3 browsers.
iOS risk: none (same play path as ▶ your take). Next: sharper note edges.

## 2026-10-25 · pitch on real low voices: 94.8 → 98.1 %

Built: the take tracker's octave prior halved (0.3 → 0.15 per octave below
the highest candidate): on vocadito low voices were read an octave or a
twelfth high. Measured (page code): vocadito RPA 98.1 ± 0.7 % (was 94.8 ±
2.4), low voices 97.8 ± 1.4 (was 91.8 ± 5.1), overall 93.2 %; synthetic
99.4 % (was 99.6; breathy soprano 4.8 % octave-low). Range, break, slide
benches unchanged. False alarms (17 %) sit at note edges; gates did not
help. On the VocalSet m2 demos the old prior took a spurious 632 Hz candidate
over a clean 164 Hz one; restricting the prior to good candidates added only
0.1 pt, not kept. A low voice's take now shows its real notes. Next: edges.

## 2026-10-25 · pitch measured on real singers

Built: `check/vocadito-bench.mjs` runs the page's take tracker on vocadito
(40 a cappella excerpts, 29 singers, f0 hand-corrected, CC BY 4.0), and the
take summary now says how sure the pitch is. Measured: RPA 94.8 ± 2.4 %,
voicing recall 97.5 %, false alarm 16.6 ± 3.4 %, overall 91.1 %; low voices
91.8 ± 5.1 %, high 97.0 ± 1.5 %. Unvoiced-cost sweep kept 0.45. A singer
can now read how far to trust the pitch on a real voice. iOS risk: none.
Next: cut false alarms (breaths, consonants) and fix low male voices.

## 2026-10-25 · compare with an earlier take

Built: each scored take's audio is kept in IndexedDB (22.05 kHz 16-bit, last
10, never sent); a picker with date and note score and "▶ earlier take" plays
one, then ▶ your take gives today's. A singer can hear last week next to
today. Numbers: none (storage and playback). check.mjs: a stored take plays in
3 browsers. iOS risk: Safari may evict IndexedDB after 7 days unused (picker
then just shrinks). Next: align the same phrase across takes.

## 2026-10-25 · guided range finder

Built: a range finder in the ♪ voice profile: three mic steps (slide to the
lowest note and hold, slide to the highest and hold, a siren on “ng”), each
tracked like a take; lowest/highest = extreme medians of 0.3 s voiced windows
within 2 st; breaks from the siren. Kept apart from takes (progress untouched);
the profile works from range finds alone. A singer can map their range in a
minute without waiting for takes. Measured (`check/range-bench.mjs`, page code,
30 synthetic voices with vibrato, breath, fry tail): lowest error median 0.11 st
(p90 0.16), highest 0.19 st (p90 1.36: tops over 1100 Hz are cut by the
tracker), 95 % within 1 st, breaks 60/60. iOS risk: mic opened from the tap as
the Mic button does. Next: rating ground truth or compare takes.

