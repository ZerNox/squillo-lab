# Voice Helix roadmap

The main product track since 2026-10-25. The mission is the runner's
(`~/.config/squillo/daily-mission.md`); this file is the plan. One line per
run-sized increment; reorder freely and say why in `LOG.md`.

## Done (to 2026-10-25)

- Live flaws: pitch helix, vocal tract, spectral terrain; nine flaw chips with
  a drawn coach and cues; demos (synthetic and 14 VocalSet clips), two
  public-domain Amazing Grace references.
- Takes: record up to 60 s or load a recording up to 6 min; cut to the
  singing (silence, talk, applause); spots scanned offline; coach cues on
  playback; "halfway" and "spotless" resyntheses (TD-PSOLA).
- Performance timeline: 10 s note-score line against the trained median,
  notes on/close/off, best notes starred and praised, click to play from there.
- Take summary: went well, then one or two things to work on, each with an
  exercise. Elo rating built but off (`?rating=1`): invalid across styles.
- Progress lines across takes, kept on the device (localStorage), with band.
- A/B at a spot: click a note or spot, hear yours then spotless, looped.
- Slow down to 0.75× or 0.5× without changing pitch (WSOLA), A/B included.
- Loop a phrase: ⟲ (L) loops the phrase around the playhead, any version and speed.
- Note by note: ◀ / ▶ or ← → plays one note at a time with its numbers; ⚑ mark (M) flags moments, kept per take.
- Warm-up: about 4 min, steps chosen from the last 5 takes, cited, guide tones.
- Phone: the take comes first after a scan, progress lines full width.
- Take pitch: YIN candidates + Viterbi (0.1 % gross error, synthetic; 97.4 ± 0.8 % RPA, false alarm 12.9 % on 40 real singers, vocadito; note edges trimmed on a short window).
- Vibrato rate and extent per take with ± (synthetic means within 0.11 Hz, 0.03 st; `check/vibrato-bench.mjs`); live chip on the same estimator; evenness (cycle-to-cycle CV, within ~2 points on synthetic jitter), judged against all 20 VocalSet singers.
- Slide style told from unwanted scoops (consistent depth on most notes).
- Voice profile: comfortable and full range, voice-type guess, key for a song, register breaks on glides; a guided range finder (lowest, highest, siren) in about a minute.
- Compare: the last 10 takes' audio kept on the device; play an earlier take, then yours; ▶ same phrase finds the current phrase in it (DTW, any key; 95 % found on a vocadito proxy), then vs today in numbers with ±, or every kept version of the phrase in a row.
- Personal bests in the summary: steadiest long note, longest in-tune note, against all kept takes, claimed only beyond one note's noise.
- Practice streak, days and minutes sung, milestones, under the progress lines.
- This week vs last week: each aspect's mean ± per week, better/worse only beyond both intervals.
- Screen lag measured live (audio to paint + half pitch window): 18-25 ms median headless, shown as a chip.
- Breathiness from CPP: live chip, cue, take summary, progress line (VocalSet 20 singers: AUC 0.90 WAV / 0.91 MP3 80k, same-singer pairs 98.9 %; old HNR cue was below chance).
- Tone colour from tilt (belt vs straight AUC 0.81, VocalSet); pressed cue retired (was at chance, AUC 0.53); tone colour per take in summary, progress and week lines, described not rated.
- Dynamics per take: swell within long notes and span soft to loud (messa di voce vs straight AUC 0.93, VocalSet), described; swell on the progress and week lines.
- Key drift per take: tuning slide over the take with ± (synthetic SD 16 ¢; vocadito agreement SD 41 ¢), praised or a drone exercise; on the progress and week lines.
- Hear it from the summary: ▶ best note, ▶ furthest-off note then tuned.
- "Your last three long notes were steadier than any last week" in the summary, beyond one note's noise.
- Timing without a click: pulse found from note starts, rhythm spread ± and tempo change in the summary, rhythm spread progress line (synthetic jitter read within about 20 ms, change SD 1-3 %, false pulse 0/40 on free melodies, 4 % on random onsets; 5 of 7 vocadito clips both annotators pulse).
- Hear it with your pulse: the take with a soft click on the singer's own fitted pulse.
- Sung vowel: 'vowels heard' in the summary; live chip and note by note, only when sure, from the harmonic envelope (VocalSet left-out singer: 85 ± 5 % on 74 % of notes, 78.5 ± 4.5 % overall, none at 600 Hz and up).
- Far vision: spotless plus even vibrato and a gentle swell on long notes (VocalSet read-back 5.78 Hz, 0.41 st for 5.8, 0.45 asked); versions switch at the same moment, keys 1-4; '▶ yours, then far' on the longest note.
- Ring (singing power ratio): summary and progress line, described not rated (VocalSet forte vs pp AUC 0.85, pairs 19/20; proxies, no direct label).
- Eyes-free: "say note" (N) speaks the held note and cents via a live region; `?` lists the keys.
- Note segmentation: optimal partitioning, vocadito COnP F 74.2 ± 2.7 % (old 36.7, second annotator 74.0); timing legato floor 12 ms.
- Sing it again: hear the furthest-off note tuned, sing it, read against that note with ± (synthetic SD 1.5-2.1 ¢, truth inside ± 59/60).
- Lane: flat 8 s pitch line, held note large with cents and ± (synthetic straight max 1.1 ¢; vibrato max 4.8 ¢, truth inside ± 97 %).
- Noisy rooms: take pitch holds in steady noise (vocadito, pink 5 dB RPA 68.9 → 85.4, clean unchanged), room line in the summary.
- Drone: ♪ drone (D) on the target note to sing against; unison only (synthetic leak at -12 dB: max 4.8 ¢; octave below flips the reading).
- Live in noise: gate at 1.5× the calibrated room (vocadito, pink 5 dB RPA 6.0 → 64.0, 10 dB 47.5 → 83.6); voicing limit scales with noise, a gate under the recent peak and a two-frame run (clean FA 24.1 → 6.5).
- Match and measure: warm-up's pitch steps hear five tones, sing each, read in ¢ with ± and landing time; sessions kept and compared (synthetic landing within about 75 ms; real voices unmeasured).
- Swell and measure: the warm-up's messa di voce hears one swell, reads width, peak place, pitch stillness and pull with level, with ±; kept and compared (synthetic width within 1.2 dB, truth inside ± 160/160).
- Siren and measure: the warm-up's siren read for span, drop-outs and register jumps (synthetic range within 0.46 st, breaks 0/20 clean, 20/20 jumped).
- High notes: take pitch to 1400 Hz; straight notes from E5 up no longer read at a fraction of the note (synthetic C5-E6 100 %, was 0-63 % on straight tones from E5; vocadito 97.4 ± 0.8).
- My data: save a copy of progress, bring it back after a wipe (merged, nothing lost), delete everything including audio.
- On the device: opens with no network if asked (my data), no third-party request (fonts self-hosted), home-screen install (real outage reopens in all three browsers; `check/offline-check.mjs`).
- Live subharmonic guard: breathy HNR 5 dB read right 49.7 → 99.7 %; vocadito live clean OA 91.8, pink 10 dB OA 88.9.
- Accessibility audit: axe-core 0 violations (WCAG 2 A/AA, best practice) on start, take, warm-up, profile, my data in Chrome and WebKit; contrast, keyboard reach, landmark, headings fixed; gated in check.mjs; spots by keyboard (shift ← →).
- Creak: described in the summary from 200 Hz up (VocalSet fry 33/42, controls 1/49, tuned on the same clips).
- Focus across takes: 'Since your last take' reads the points last named against the singer's own takes with a prediction interval (VocalSet: false change 0-7.5 %, wrong way 0/125, half of large changes read level); 'Today's focus' on opening.
- Tuning across the range: high notes under or over the low ones with ±, silent unless sure (synthetic 40 ¢ said 20/20, level 0/10; vocadito said 5 of 36, 0 opposite, gates tuned on those clips).
- WebKit hang: AudioWorklet added to a running context deadlocked Linux WebKit (5 of 20); set up suspended, 0 of 66; `check/hang-probe.mjs`.
- Next step: tuning alone moved half way, button, key 5 and summary A/B (read back: synthetic 17.4 → 8.7 ¢, VocalSet 15.8 → 10.2 ¢); steadiness and starts dropped, not beyond the render's floor.
- Sing the phrase: hear the phrase tuned, sing it, read note by note at any tempo or key (synthetic median 0.1 ¢ straight, 6.0 vibrato; vocadito shift proxy median 3.0, p90 20.2 ¢; other melody wrongly accepted 5/30, 10/30 without the gate, same stream); tries kept and compared across days (synthetic 80 pairs: false change 0-1, cut errors said closer 48-53); a note's timing named against the singer's own pace (250 ms 35/50, false 0/43; vocadito same singing 4/128).
- Live Viterbi with one frame's lag (vocadito clean RPA 90.6 → 94.3, FA 6.5 → 8.8, OA 91.8 → 93.2; pink 10 dB OA 88.9 → 90.4; +20 ms on the lag chip).
- Today's session: from a day's second take, best notes with ▶, better/level/further vs earlier takes, one point for next time (VocalSet false change 1/440 sessions; finds 13-29 % of a clarity change, wrong way 0).
- Moments you marked: the newest 6 marks from kept earlier takes, ▶ and ✕, in the summary.
- Whole span: take and live read A1-E6 on five spectra, floor 60 → 46 Hz (synthetic 100 % in every cell, A1 was 0 %; vocadito unchanged within ±, live hum 10 dB OA -1).
- Phone: take controls in two swipeable rows, score line on the first screen.
- Scale of a take: named in the summary from 30 notes when 90 % sure (synthetic 98-100 % right; vocadito said on 2/40, no key labels); aiming off notes from the key tried, dropped (0/624 restored on vocadito).
- Save audio: ⤓ the version last played, at the chosen speed, as a WAV on the device; the share sheet on phones.
- Same phrase seen: found versions drawn over each other in today's key, synced to playback.
- Note endings: long notes falling or rising as they are let go, in the summary with ± and an exercise, praised when held, on the progress and week lines and in 'since your last take' (synthetic -80 ¢ said 10/10, level 0/10 false; vocadito page vs hand f0 SD 9.7 ¢, 0 opposite).
- Live note endings: the Lane says 'held to the end' or 'fell N ¢ as you let go' after each long note (synthetic level said 0/40, wrong way 0/240, -80 ¢ 27/40).
- Hear the ending held: '▶ yours, then held' on the note that fell furthest; spotless now holds endings (synthetic -80 ¢ fall: take -37 → spotless -3 ¢).
- Live note starts: the Lane says 'landed right on the note' or 'came in N ¢ under' 0.45 s into each note (synthetic level said 0/80, wrong way 0/480, ±80 ¢ straight 80/80).
- Warm-up also targets note endings, key drift, clarity and rhythm when takes keep naming them (2 of the last 5).
- Next step for starts: when scoops lead and tuning is near the trained median, the next step makes each scoop half as deep (synthetic 3 st: 0.50 → 0.00 scoops per note, render alone 0.50).
- Next step for endings: when note endings are named, each long note's ending comes half way back (synthetic -80 ¢: -37 → -26 ¢, render alone -46).
- Live vibrato: the Lane names each long note's rate, width and evenness, or 'held straight' (synthetic: straight 40/40, rate max 0.04 Hz off, even 40/40, jittered uneven 15/40).
- Live swell: the Lane names each long note's swell in dB with ± and peak place, or 'held level' (synthetic: truth inside ± 138/150, peak place 90/90, messa claim 0 at 14 dB and under).
- Live steadiness: the Lane names each long note's wobble and 'your steadiest' this sitting or across kept takes (synthetic: live = take within 0.2 ¢, false best 0/144, right 17/18).
- Eyes-free recap: with say note on, each long note's Lane lines are read once as one sentence after it stops.
- Long notes this sitting: the Lane's after-note lines kept as a list beside it (8 newest).
- Long notes across days: today's live long-note wobble vs the last two weeks, with intervals (synthetic false change 2-3 %, half the wobble 97-100 %); starts and endings too (false 0-1 %, 0 vs 80 ¢ 97-100 %); swell width too (synthetic false 0/400, 8 dB steps 400/400); wobble, starts and endings by day drawn over 14 days with 95 % bars; vibrato rate and width too, described not rated (synthetic false 0/400, steps 400/400).
- No WebGL: the 2D Lane, HUD, score and takes keep running (Firefox here lost WebGL 2026-11-05).
- Vowels, part 3a: envelope × log f0 terms in the vowel table (VocalSet left-out singer 78.4 → 81.8 %, o 63 → 71 %, sure 87.5 % on 78 %).; live 0.5 s window re-measured (83.0 → 88.1 %, chip "7 in 8 right").
- Warm-up from live long notes: a worse wobble, start or ending on the newest Lane day adds its step (synthetic false 3/400, wobble ×2 393/400, endings 355/400).
- Live singing keeps the streak: Lane days count as days sung; long notes held live shown beside kept minutes. Milestones for live long notes (10 to 5000), lifetime count kept apart from the 400-note list.
- Steadiest by note: the Lane's list names the steadiest and least steady note of two weeks, beyond an extreme-widened interval (synthetic false 3/400, ×2 named 360/400).
- Hear it again: ▶ on each live long note replays it from a 30 s in-memory mic ring (never stored); '▶ then tuned' on notes 15 ¢ or more off. '▶ steadiest, then this' A/Bs any note against the sitting's steadiest. '▶ all in order' plays the sitting's kept notes oldest first. '▶ ½×' plays a note at half speed, pitch kept. '▶ then held' replays a note whose ending fell or rose with it lifted back (synthetic -80 → -1.4 ¢). '▶ then landed' replays a note that came in under or over with its start moved onto the note. '▶ all fixed' does tuning, start and ending at once (synthetic: 0.0 / 0.0 / -2.0 ¢). ⤓ saves a note as a WAV on the device. '▶ then level' holds a mid-note wander level (2026-11-07).
- Range by week: the voice profile's 8-week chart of full and comfortable span; a new top or bottom named only a semitone or more past before.
- Hosting from main via `voice-helix-publish.yml`; `check/check.mjs` for
  Chrome, Firefox and WebKit iPhone.

## Next

0. **Noise, part 3**: live false alarms (clean FA 8.8 % with live Viterbi; gates and a centred level cue only trade RPA for FA; talk-like noise slightly worse with it; HNR 0 dB breathy notes unread); take pitch in talk-like noise no gain, talk-like room reads high, the line says talk is not counted; live note-edge level trim tried 2026-11-03, trades again (FA 8.3 → 7.5, RPA 94.0 → 93.6); a low-band (<1.5 kHz) energy share gate 2026-11-04 left FA flat (8.3 → 8.1) and cost RPA (→ 91.2): not breaths/fricatives (steady noise reads right: pink 10 dB 10/10/11, hum 10 dB 9/9/10, 14 clips, 2026-11-01).
0. **Timing, part 3**: page finds 5 of the 7 clips both vocadito annotators pulse, 4 % false on random onsets; real truth is thin (annotators share only 7 of 40).
0. **Key drift, part 2**: better real-voice agreement (vocadito SD 41 ¢ vs synthetic 16); local/global circular unwraps tried 2026-10-30, no gain (39-91 ¢): needs a different truth or note-level approach. `segNotes` input: SD 62 ¢, worse.
0. **Vowels, part 3**: o/u still weakest (71/75 % after the f0 terms, left-out singer); try other mics or languages if an open labelled set exists.
1. **Rating with ground truth**: human-judged takes across styles from openly
   licensed sources only, then a rating that ranks them correctly (see
   `rating/README.md`).
2. **Sharper note edges, part 2**: false alarm 12.9 % on vocadito; threshold/width sweeps of the trim only trade RPA for FA (OA 94.3-94.4), so it needs a finer hop at edges or level-envelope onsets. Real soprano f0 truth still missing, and matters more now: the high-note gain is synthetic only. A neighbour-relative trim (R 0.2/0.3) also only trades: FA 12.7/12.2, OA 94.3/94.2 (2026-10-26).
3. **On-device vocal separation** (ONNX in WASM) so songs with music load
    without Demucs on a desktop.
4. **Vibrato, part 3**: per-note truth if any exists (the 20-singer evenness reference is done).
5. **Tone, part 2**: formant-corrected H1-H2 re-tested; a pressed cue only if openly licensed pressed-voice labels turn up.
6. **Same phrase, part 3**: measure the matcher on real re-sung takes (an openly licensed set with repeated renditions of one melody) instead of the slowed-clip proxy.
7. **Next step, part 3**: clean starts on real voices (no scoop-labelled open set yet); a real-voice steadiness render above the 0.3 ¢ floor.
8. **Sing the phrase, part 3**: a test on really re-sung phrases, fewer other melodies accepted (5/30), rhythm as a cue once real re-sung timing can be measured.
