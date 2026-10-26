# Voice Helix log

Newest first. Date, what was built, what a singer can now do, numbers, next.

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

## 2026-10-25 · register breaks on glides

Built: a break detector (two 200 ms line fits either side of each moment,
same slope sign ≥ 3 st/s, smooth, ≥ 1.2 st apart) run on every take; breaks
are kept per take, drawn on the profile bar, named in "to work on" with
sirens (Titze 2006), and a suggested key says if the melody crosses one.
A singer who sings a siren now sees where their voice flips. Measured
(`check/break-bench.mjs`, page code): 64/64 synthetic breaks, error median
0.06 st, p90 0.11; 0 false on 96 clean sirens, legato and vibrato takes;
1 in 274 s of real clips. Synthetic only: real passaggi are subtler. iOS
risk: none. Next: guided range finder.

## 2026-10-25 · voice profile and a key for any song

Built: ♪ voice profile: comfortable range (median of each take's 10th-90th
percentile note, ± between takes), full range sung so far, a voice-type guess
from the range centre (said to be a guess), and a key for any song from its
lowest/highest note and key. Each take now also keeps its lowest and highest
held note. A singer can now see their range and pick a key that suits them.
Numbers: none measured (bookkeeping on the take's notes; voice type not
validated). check.mjs: seeded takes read E3-D4, tenor, G3-D5 in G → C (3
browsers). iOS risk: none (no audio). Next: register transitions.

## 2026-10-25 · warm-up from your recent takes

Built: a ☀ warm-up button: a 4-5 step, about 4 min routine (lip trill/straw,
one or two targeted steps, siren) whose middle steps go to the aspects
furthest from the median trained singer over the last 5 takes on the device
(pitch matching, messa di voce, clean starts, easy onsets), each with its
source and a guide tone in the singer's own range (notes' 10th-90th
percentile, now kept per take). A singer can now warm up on what they need
today. Numbers: none new (choice rule reuses the "to work on" yardstick).
check.mjs: seeded takes give onsets then intonation, tone plays (3 browsers).
iOS risk: tone context made in the tap. Next: range and voice profile.

## 2026-10-25 · take first on a phone

Built: at phone width a scanned take moves its play row, timeline, summary
and progress above the live readouts, the 3D gap shrinks from 42 to 22 % of
the screen, the page scrolls to the take, and progress lines span the full
width with the value above. A singer on an iPhone reads their take without
scrolling past the helix. check.mjs asserts the timeline is on screen after
the scan (WebKit iPhone, touch). Numbers: none new. iOS risk: smooth scroll
only. Next: warm-up from the flaws seen most.

