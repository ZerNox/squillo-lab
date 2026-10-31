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
- Live in noise: gate at 1.5× the calibrated room (vocadito, pink 5 dB RPA 6.0 → 64.0, 10 dB 47.5 → 83.6); voicing limit scales with noise, and a gate under the recent peak (clean FA 24.1 → 11.0).
- Match and measure: warm-up's pitch steps hear five tones, sing each, read in ¢ with ± and landing time; sessions kept and compared (synthetic landing within about 75 ms; real voices unmeasured).
- Swell and measure: the warm-up's messa di voce hears one swell, reads width, peak place, pitch stillness and pull with level, with ±; kept and compared (synthetic width within 1.2 dB, truth inside ± 160/160).
- Siren and measure: the warm-up's siren read for span, drop-outs and register jumps (synthetic range within 0.46 st, breaks 0/20 clean, 20/20 jumped).
- High notes: take pitch to 1400 Hz; straight notes from E5 up no longer read at a fraction of the note (synthetic C5-E6 100 %, was 0-63 % on straight tones from E5; vocadito 97.4 ± 0.8).
- Hosting from main via `voice-helix-publish.yml`; `check/check.mjs` for
  Chrome, Firefox and WebKit iPhone.

## Next

0. **Noise, part 3**: live false alarms (clean FA 11.0 %, no Viterbi live; HNR 0 dB breathy notes unread); take pitch in talk-like noise no gain, room read 10-13 dB high.
0. **Timing, part 3**: page finds 5 of the 7 clips both vocadito annotators pulse, 4 % false on random onsets; real truth is thin (annotators share only 7 of 40).
0. **Key drift, part 2**: better real-voice agreement (vocadito SD 41 ¢ vs synthetic 16); local/global circular unwraps tried 2026-10-30, no gain (39-91 ¢): needs a different truth or note-level approach. `segNotes` input: SD 62 ¢, worse.
0. **Vowels, part 3**: o/u still weakest (64/72 %, left-out singer); try other mics or languages if an open labelled set exists.
1. **Rating with ground truth**: human-judged takes across styles from openly
   licensed sources only, then a rating that ranks them correctly (see
   `rating/README.md`).
2. **Sharper note edges, part 2**: false alarm 12.9 % on vocadito; threshold/width sweeps of the trim only trade RPA for FA (OA 94.3-94.4), so it needs a finer hop at edges or level-envelope onsets. Real soprano f0 truth still missing, and matters more now: the high-note gain is synthetic only. A neighbour-relative trim (R 0.2/0.3) also only trades: FA 12.7/12.2, OA 94.3/94.2 (2026-10-26).
3. **On-device vocal separation** (ONNX in WASM) so songs with music load
    without Demucs on a desktop.
4. **Vibrato, part 3**: per-note truth if any exists (the 20-singer evenness reference is done).
5. **Tone, part 2**: formant-corrected H1-H2 re-tested; a pressed cue only if openly licensed pressed-voice labels turn up.
6. **Same phrase, part 3**: measure the matcher on real re-sung takes (an openly licensed set with repeated renditions of one melody) instead of the slowed-clip proxy.
