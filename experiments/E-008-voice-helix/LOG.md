# Voice Helix log

Newest first. Date, what was built, what a singer can now do, numbers, next.

## 2026-11-07 · hear a live long note held level

Built: `laneDrift`/`levelRamp`: a live long note that wanders 15 ¢ or more in its middle (0.2 s mean of its frames against its median, so vibrato mostly averages out) gets "▶ then level" on the Lane's list: the note from the 30 s ring, then the same samples with the rate curve that holds the middle level. Start, ending and vibrato are kept. Memory only. Measured: a synthetic 2 s A3 with 5 Hz ±20 ¢ vibrato and a 40 ¢ sag in the middle, rendered offline and read back by zero crossings over 0.4 s: the middle sits 37 → 5.3 ¢ from its start and end (Chrome, Firefox, WebKit iPhone). This is a proxy only: one sag shape, no real voice. check.mjs: the button shows only on the wandering note. iOS risk as before (playback during mic stream). Next: o/u vowels (needs VocalSet fetched), or noise part 3.

## 2026-11-07 · hear a live long note all fixed

Built: `fixParts`/`fixRamp`: a live long note with two or more of: 15 ¢+ off the semitone, a start the Lane said came in under/over, an ending it said fell/rose, gets "▶ all fixed" on the Lane's list: the note from the 30 s ring, then the same samples in one rate curve (tuning factor throughout, times the landRamp start and holdRamp ending shapes, timed at the tuned rate), so the singer hears the whole note as it could be, in their own voice. Memory only. Measured: a synthetic A3 note 30 ¢ sharp, coming in and ending 80 ¢ below its body (-50 ¢ from A3), rendered offline and read back by zero crossings: start 0.0, body 0.0, ending -2.0 ¢ (Chrome, WebKit iPhone) / -2.2 ¢ (Firefox) from A3; proxy only (one shape, no real voice). check.mjs: button only on the note with 2+ faults. iOS risk as before (playback during mic stream). Next: o/u vowels, or noise part 3.

## 2026-11-07 · hear a live long note landed

Built: `landRamp`: a live long note whose start the Lane said came in under or over gets "▶ then landed" on the Lane's list: the note from the 30 s ring, then the same samples at 2^(-c/1200) rate through the first 0.25 s, easing back to 1 by 0.4 s, so the start sits on the note. Memory only. Measured: a synthetic 220 Hz note starting 80 ¢ under for 0.1 s, rendered offline through `landRamp` and read back by zero crossings, starts +0.1 ¢ (Chrome, WebKit) / -0.3 ¢ (Firefox) from the body; proxy only (one scoop shape, no real voice). check.mjs: button only on the scooped note. iOS risk as before (playback during mic stream). Next: o/u vowels, or noise part 3.

## 2026-11-07 · hear a live long note held to the end

Built: `holdRamp`: a live long note whose ending the Lane named as falling or rising gets "▶ then held" on the Lane's list: the note from the 30 s ring, then the same samples with the playback rate ramped by -c ¢ over its last 0.45 s, so the ending is lifted back to the body's pitch. Memory only. Measured: a synthetic 220 Hz note falling 80 ¢ in its last 0.18 s, rendered offline through `holdRamp` and read back by zero crossings, ends -1.4 ¢ (Chrome, WebKit) / -1.2 ¢ (Firefox) from the body; proxy only (one fall shape, no real-voice check). check.mjs: button only on the fallen note; MUTE now leaves OfflineAudioContext alone. iOS risk as before (playback during mic stream). Next: o/u vowels, or noise part 3.

## 2026-11-06 · keep a live long note

Built: `saveLive`: each live long note on the Lane's list gets ⤓, which saves that note from the 30 s in-memory ring as a 16-bit WAV on the device (share sheet on phones, download elsewhere); nothing is kept unless the singer saves it. No new measurement. check.mjs: button shown, WAV exactly 44 + 2 bytes per sample of the clip. Chrome, Firefox, WebKit iPhone. iOS risk: navigator.share with a file needs the click's activation (called synchronously in it). Next: o/u vowels, or noise part 3.

## 2026-11-06 · hear a live long note slowly

Built: each live long note on the Lane's list gets "▶ ½×": the note from the 30 s in-memory ring at half speed, pitch kept (the take's WSOLA slow-down), so a singer hears how a start or ending moved. Memory only. No new measurement (WSOLA pitch kept within 0.7 ¢ median, check.mjs). check.mjs: button shown, output exactly twice the clip. Chrome, Firefox, WebKit iPhone. iOS risk as before (playback during mic stream). Next: o/u vowels, or noise part 3.

## 2026-11-06 · hear the sitting in order

Built: `hearAll`: with two or more live long notes still in the 30 s ring, the Lane's list shows "▶ all in order", which plays them oldest first, 0.4 s apart, so a singer hears how the sitting went; recaps heard back are kept off the list as before. Memory only. No new measurement. check.mjs: button shown, three clips queued at their full lengths in order. Chrome, Firefox, WebKit iPhone. iOS risk as before (playback during mic stream). Next: o/u vowels, or noise part 3.

## 2026-11-06 · hear your steadiest, then this

Built: `LBEST`/`keepBest`/`bestBtn`: when a live long note is logged with lower wobble than any before it this sitting, its clip is copied out of the 30 s ring (memory only, never stored); every other note on the Lane's list gets "▶ steadiest, then this": the steadiest note, a 0.4 s gap, then this one, wobbles named in the label. No new measurement (Lane steadiness: live = take within 0.2 ¢). check.mjs: best kept and replaced by a steadier one, button on the others only, both clips play at full length. Chrome, Firefox, WebKit iPhone. iOS risk as before (playback during mic stream). Next: o/u vowels, or noise part 3.

## 2026-11-06 · hear a live long note tuned

Built: each live long note on the Lane's list now shows how far its frame median sat from the nearest semitone; at 15 ¢ or more it gets "▶ then tuned": the note from the 30 s in-memory ring, then the same samples at 2^(-c/1200) speed, moved onto the note (length changes under 3 %). Same pitch frames as the Lane (synthetic straight max 1.1 ¢, vibrato 4.8 ¢); the frame median itself not separately benchmarked. check.mjs: 40 ¢ sharp gets the button and label, 5 ¢ does not, playback rate exact. Chrome, Firefox, WebKit iPhone. iOS risk as before (playback during mic stream). Next: o/u vowels, or noise part 3.

## 2026-11-06 · hear a live long note again

Built: `liveTap`/`liveClip`/`hearLive`: the last 30 s of microphone audio kept in memory only; each long note on the Lane's list gets ▶ that replays that note (0.15 s padding), "gone" once overwritten; recaps heard back while it plays are kept off the list so the speaker cannot add fake notes. No new measurement. check.mjs: synthetic ring, clip ends within 2 samples, muted recap dropped, gone after 32 s. Chrome, Firefox, WebKit iPhone. iOS risk: playback during a live mic stream uses the same AudioContext (resumed in the click); echo cancellation may duck it. Next: o/u vowels, or noise part 3.

## 2026-11-06 · steadiest by note

Built: `laneByNote`: the Lane's list adds "By note, last two weeks: steadiest on C4 … least steady on E4 …", each note against the others pooled, with ± and an interval widened for picking an extreme. `check/lane-days-bench.mjs` (page code, synthetic live wobbles, 400 trials): false name 3/400 when alike; one note ×2 wobble named 360/400, ×½ 385/400. check.mjs: one note silent, alike silent, C4 named. Chrome, Firefox, WebKit iPhone. Next: o/u vowels, or noise part 3.

