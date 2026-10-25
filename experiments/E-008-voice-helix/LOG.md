# Voice Helix log

Newest first. Date, what was built, what a singer can now do, numbers, next.

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
