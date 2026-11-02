# Voice Helix log

Newest first. Date, what was built, what a singer can now do, numbers, next.

## 2026-11-02 · the whole span, take and live

Found: `check/span-bench.mjs` (page code, both paths, A1-E6, plain, vibrato, breathy, thin, phone high-pass, 3 notes per cell) read 100 % from C2 up, and 0 % at A1: the floor stopped at 60 Hz, so a low bass was silent. Built: `F0MIN` 46 Hz, A1 now 100 % on both. Vocadito 40 clips: take RPA 97.4 → 97.3, FA 12.9 → 13.1, OA 94.1 → 94.0; live clean OA 93.2 same, FA 8.8 → 8.3; pink 10 dB same; hum 10 dB OA 87.2 → 86.2, hum 0 42.5 → 42.0. All within ±. Lag chip about +2.5 ms at 48 kHz. Synthetic only under C2; CPP still floors at 60 Hz. iOS risk: yin about 30 % more worker CPU per frame, not measured on a phone. Next: noise part 3, or experience.

## 2026-11-01 · moments you marked, from earlier takes

Found: a ⚑ was kept per take but could only be reached on its own take's bar, so the next take orphaned it. Built: 'Moments you marked' in the summary: the newest 6 marks whose audio is still kept (last 10 takes), ▶ from 1 s before, ✕ to remove. No accuracy claim, nothing measured beyond the check. Marks on takes past the last 10 stay in my data but do not list. iOS risk: as compare. Next: first to last take of a day on real re-sung data, if an open set turns up; else noise part 3.

## 2026-11-01 · today's session

Found: the summary read one take; the mission says every session, and nothing spoke for a day's singing. Built: 'Today's session' from the second take of a day: takes and minutes, today's steadiest and longest in-tune notes with ▶ from kept audio, better / level / further against up to 10 earlier takes, one point for next time with its exercise. Decided: Welch's t at 99 % with the aspect's tol as a floor, since up to 7 aspects are tested per session; described aspects stay out. `check/session-bench.mjs`, page code, VocalSet straight clips dealt into today and earlier: false change 1/440 sessions = 0.2 % (0.0-1.3), 11 singers, draws share clips and same-day takes are likely more alike than these; normal draws one aspect 1.7 % (1.3-2.1). Power is low: clarity breathy → straight better 35/120, reverse worse 16/120, wrong way 0. Quiet by design. A NaN limit on overall made it always claim; seen in the rendered text, fixed, now gated. Notes before this version have no `lt`, so no ▶. iOS risk: ▶ awaits IndexedDB after resume, as compare does. Next: a real-voice view of first to last take in a day.

## 2026-11-01 · live trellis: short-level cost, no change

`check/live-noise-bench.mjs`, 14 vocadito clips, clean: a voiced cost when the centred 2-period level falls under T × frame level. Off: OA 93.5, FA 9.5; P 1, T 0.5: 93.6, 9.3; P 0.5, T 0.8: 93.5, 8.6, RPA 94.4. Pink 10 dB unmoved. Same trade again, reverted. Live ghost frames are not worth more cue-hunting on this data; next run moves to experience.

## 2026-11-01 · live pitch: Viterbi with one frame's lag

Found: live used gates only, which missed sung frames; every gate sweep only traded RPA for FA. Built: the take's trellis run forward in the worker (`lagVit`, `LN.C`), each frame deciding the frame one hop back; pitch keeps its own time and the lag chip adds the 20 ms. Reference clips keep the gates. `check/live-noise-bench.mjs`, page code, vocadito 40 clips, gates → shipped: clean RPA 90.6 → 94.3, FA 6.5 → 8.8, OA 91.8 → 93.2 (± 1.0-1.9); pink 10 dB OA 88.9 → 90.4; pink 5 76.8 → 79.6; hum 10 85.8 → 87.2; speech 10 87.4 → 87.0, speech 5 71.9 → 71.0, FA up about 1 point. Sweep on 14 clips, clean OA/FA: lag 0, U 0.45 93.4/14.0; U 0.28 91.3/10.6; lag 1, U 0.28 93.5/9.5; lag 2 93.7/9.6. Chosen lag 1, U 0.28: lag 0 doubles ghosts, lag 2 pays 20 ms for nothing. Cost: more ghost frames than the gates, 20 ms lag, slightly worse in talk. Breathy HNR 5 dB 100 %, HNR 0 still unread; lane unchanged (max 1.1 / 4.8 ¢). iOS risk: slightly more worker CPU per frame, not measured on a phone. Next: edge FA, using the take's trim on the live path.

## 2026-11-01 · sing the phrase: which note came late

Found: the phrase read only pitch. Built: note starts against the singer's own pace, the note that stands out named in ms, or praise when all fall within 40 ms. Reference is the heard phrase read by the same aligner: against segmented edges, identical singing was falsely named 28/68. Threshold 120 ms named 150 ms moves 82/99, false 11/128 on vocadito; 200 ms (shipped) 16/99, 250 ms 35/50, synthetic false 0/43, vocadito false 4/128. Chosen for few false calls: a wrong 'you were late' costs trust. Vocadito is the same singing shifted, so re-sung false calls are unmeasured. iOS risk: one more read before the result shows on long phrases. Next: noise part 3 or real re-sung data.

## 2026-11-01 · sing the phrase: kept across days, fewer wrong melodies

Found: phrase tries vanished at reload, and another melody could read as the phrase. Built: tries kept by the phrase's steps, in my data, and a later day says closer, level or further with ±. Half the phrase's notes must now sit within 60 ¢ of its own level. `check/sing-bench.mjs`, page code: other melody accepted 10/30 → 5/30 on one random stream (corrected: the first figure here, 5/31 → 3/30, compared different streams; 3-5/30 across streams); vocadito shift proxy 205 → 202/240, median 3.0, p90 20.2 ¢, 98 % inside ±. A 60 % gate gave 1/30 but 180/240, so 50 % was chosen. Synthetic 80 pairs across days: same errors closer 0, further 1; errors cut to 40 % closer 53, level 27, further 0. Duration ratios separated well on synthetic, left out: no real re-sung timing to test them on, and rubato would pay. Key from steps alone, so another tune with the same steps shares a history. No new iOS risk beyond sing the phrase. Next: live Viterbi lookahead, or noise part 3.

## 2026-11-01 · live false alarms: centred level cue, no change

`check/live-noise-bench.mjs`, page code, 14 vocadito clips, clean; a short level window where the pitch belongs, against the long one (the live twin of the take's edge trim). T off: RPA 90.9, FA 6.8, OA 91.8; 0.2: 90.8, 6.5, 91.8; 0.35: 90.2, 5.1, 91.9; 0.5: 89.2, 3.6, 91.7 (each ± about 2). Pink 10 dB unmoved. Same trade as the gates, so reverted. Left to try: Viterbi with short lookahead, which costs latency.

## 2026-11-01 · sing the phrase

Found: only one note could be re-sung and read; singers practise phrases. Built: 🎙 sing phrase (P): the phrase around the current note, tuned, in their own voice; they sing it; each note reads ¢ with ±, at any tempo or key, against the take. Decided: read against full tuning, as the target is what they hear. `check/sing-bench.mjs`, page code: see README; synthetic 470/470 notes, median 0.1 ¢ straight, 6.0 vibrato (p90 16.4), ± covers 99-100 %; key moves 74/80; other melody wrongly accepted 5/31, a known weak spot; vocadito shift proxy accepted 205/240, median 3.0, p90 22.4 ¢, 97 % inside ±. No truly re-sung phrase measured. iOS risk: as sing it again, mic and playback in one tap; loudspeaker bleed stops before capture. Next: live voicing cue.

