# Voice Helix log

Newest first. Date, what was built, what a singer can now do, numbers, next.

## 2026-11-07 · hear a wide live vibrato narrowed

Built: `laneNarrow`/`narrowBtn`: a live long note (1.4 s+) with vibrato wider than ±0.6 st gets "▶ narrower vibrato" on the Lane's list: the note from the 30 s ring, then the same samples with a rate curve (via `levelRamp`) scaling each 0.02 s swing about its 0.2 s mean to the far vision's ±0.45 st. Memory only. Measured: synthetic 5.5 Hz ±1.0 st A3 rendered offline, `vibPiece` read-back 0.975 → 0.413-0.416 st, 5.53 Hz (Chrome, Firefox, WebKit iPhone). Proxy only (pure tone; frames assumed aligned with the ring, tracker latency untested). iOS risk as before (playback during mic stream). Next: o/u vowels, or noise part 3.

## 2026-11-07 · hear a level live note with a swell

Built: `swellRamp`/`swellBtn`: a live long note (1.4 s+) the Lane read as "held level" (swell + its ± under 6 dB) gets "▶ with a swell": the note from the 30 s ring, then the same samples with a gain curve rising 9 dB from its ends to its middle (raised sine in dB), so a singer hears their own note as a messa di voce. Memory only. Measured: a level synthetic A3 rendered offline, level read in 20 ms frames (5-95 %): 0.17 → 9.0 dB, peak at 0.56 of the note (Chrome, Firefox, WebKit iPhone). Proxy only (pure tone; a real swell also brightens the tone, which a gain curve does not). iOS risk as before (playback during mic stream). Next: o/u vowels, or noise part 3.

## 2026-11-07 · hear a straight live note with vibrato

Built: `vibRamp`/`vibBtn`: a live long note (1.4 s+) the Lane called "held straight" gets "▶ with vibrato": the note from the 30 s ring, then the same samples with a rate curve adding the far vision's vibrato (5.8 Hz, ±0.45 st, faded in 0.3 s into the note and out before the ending), so a singer who holds straight hears where vibrato could take their own voice. Memory only. Measured: a straight synthetic A3 rendered offline, pitch read every 10 ms and given to `vibPiece` (the take's estimator): 5.80-5.81 Hz, 0.416-0.423 st for 5.8 / 0.45 asked (Chrome, Firefox, WebKit iPhone); before: no vibrato. Proxy only (pure tone, no real voice). iOS risk as before (playback during mic stream). Next: o/u vowels, or noise part 3.

## 2026-11-07 · hear a live long note held level

Built: `laneDrift`/`levelRamp`: a live long note that wanders 15 ¢ or more in its middle (0.2 s mean of its frames against its median, so vibrato mostly averages out) gets "▶ then level" on the Lane's list: the note from the 30 s ring, then the same samples with the rate curve that holds the middle level. Start, ending and vibrato are kept. Memory only. Measured: a synthetic 2 s A3 with 5 Hz ±20 ¢ vibrato and a 40 ¢ sag in the middle, rendered offline and read back by zero crossings over 0.4 s: the middle sits 37 → 5.3 ¢ from its start and end (Chrome, Firefox, WebKit iPhone). This is a proxy only: one sag shape, no real voice. check.mjs: the button shows only on the wandering note. iOS risk as before (playback during mic stream). Next: o/u vowels (needs VocalSet fetched), or noise part 3.

## 2026-11-07 · hear a live long note all fixed

Built: `fixParts`/`fixRamp`: a live long note with two or more of: 15 ¢+ off the semitone, a start the Lane said came in under/over, an ending it said fell/rose, gets "▶ all fixed" on the Lane's list: the note from the 30 s ring, then the same samples in one rate curve (tuning factor throughout, times the landRamp start and holdRamp ending shapes, timed at the tuned rate), so the singer hears the whole note as it could be, in their own voice. Memory only. Measured: a synthetic A3 note 30 ¢ sharp, coming in and ending 80 ¢ below its body (-50 ¢ from A3), rendered offline and read back by zero crossings: start 0.0, body 0.0, ending -2.0 ¢ (Chrome, WebKit iPhone) / -2.2 ¢ (Firefox) from A3; proxy only (one shape, no real voice). check.mjs: button only on the note with 2+ faults. iOS risk as before (playback during mic stream). Next: o/u vowels, or noise part 3.

## 2026-11-07 · hear a live long note landed

Built: `landRamp`: a live long note whose start the Lane said came in under or over gets "▶ then landed" on the Lane's list: the note from the 30 s ring, then the same samples at 2^(-c/1200) rate through the first 0.25 s, easing back to 1 by 0.4 s, so the start sits on the note. Memory only. Measured: a synthetic 220 Hz note starting 80 ¢ under for 0.1 s, rendered offline through `landRamp` and read back by zero crossings, starts +0.1 ¢ (Chrome, WebKit) / -0.3 ¢ (Firefox) from the body; proxy only (one scoop shape, no real voice). check.mjs: button only on the scooped note. iOS risk as before (playback during mic stream). Next: o/u vowels, or noise part 3.

## 2026-11-07 · hear a live long note held to the end

Built: `holdRamp`: a live long note whose ending the Lane named as falling or rising gets "▶ then held" on the Lane's list: the note from the 30 s ring, then the same samples with the playback rate ramped by -c ¢ over its last 0.45 s, so the ending is lifted back to the body's pitch. Memory only. Measured: a synthetic 220 Hz note falling 80 ¢ in its last 0.18 s, rendered offline through `holdRamp` and read back by zero crossings, ends -1.4 ¢ (Chrome, WebKit) / -1.2 ¢ (Firefox) from the body; proxy only (one fall shape, no real-voice check). check.mjs: button only on the fallen note; MUTE now leaves OfflineAudioContext alone. iOS risk as before (playback during mic stream). Next: o/u vowels, or noise part 3.
