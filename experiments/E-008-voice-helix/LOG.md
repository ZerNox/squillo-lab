# Voice Helix log

Newest first. Date, what was built, what a singer can now do, numbers, next.

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

## 2026-10-25 · pitch tracker for takes (pYIN-style Viterbi)

Built: takes are tracked with YIN candidates per frame and a Viterbi path over
the whole take; take audio now reaches the worker in 5 ms chunks (it was
43 ms, so frame pairs saw the same audio). A singer's notes, scoops and
spots now come from a pitch track that does not flip octaves on a breathy
voice. Measured (`check/pitch-bench.mjs`, page code, held-out seed, 29 328
frames, 25 voice×condition cells): gross error 10.9 % (old chunking) →
1.4 % (live tracker) → 0.1 % (Viterbi); octave 0.8 → 0.1 %; missed voiced
0.3 %. Noisy 600 Hz tone in check.mjs: live 0 %, take 81 % right. Slide bench
unchanged (120/120). iOS risk: none (offline maths). Next: phone layout.

## 2026-10-25 · slide style vs unwanted scoop

Built: each onset's slide is measured from the take (settled pitch less the
first 60 ms); two thirds or more of notes slid into by the same depth (±20 %)
is a style: praised, not marked down, no scoop spots. A pop or soul singer is
no longer told to fix their style. Measured (`check/slide-bench.mjs`, page
code): 119/120 synthetic phrases classified right; 0/16 real clips called a
style. iOS risk: none (offline maths only). Next: pitch tracker (pYIN+Viterbi).

## 2026-10-25 · slow down without changing pitch

Built: speed menu 1×/0.75×/0.5× for take, halfway, spotless and A/B (WSOLA).
A singer can now hear a fast run or a scoop at half speed, same pitch.
Measured with the page's code: 0.5× keeps steady pitch to 0.7 ¢ median,
1.1 ¢ p90 (3 synthetic voices); 0.8-1.3 s to slow a 32 s take. iOS risk:
the stretch runs on the main thread (UI pauses ~1 s on a phone). check.mjs
now retries WebKit twice. Next: style-aware onsets.

## 2026-10-25 · A/B at a spot

Built: a click on any note or coach spot on the timeline loops your note,
then the same moment spotless. A singer can now hear exactly what the fix
sounds like, back to back. Checked in three browsers (loop running after a
tap). iOS risk: none new (same context path as take playback). Next: slow
down without changing pitch.

## 2026-10-25 · progress across takes

Built: each scored take's summary is kept on the device; the take card ends
with a progress line per aspect and overall (dots per take, mean of the last
5, 95 % band from the spread between takes, "better/worse" only beyond both
bands). A singer can now see whether they are improving over days. Checked
in Chrome, Firefox, WebKit iPhone with 7 seeded takes. Numbers: none new
(display of existing measures). Process: stray WebKit processes from a
cut run make `setInputFiles` time out; kill them before re-checking. Next:
A/B at a spot.

## 2026-10-25

Talk and applause cut from takes; performance timeline; check script for three browsers; helix made the main track.
