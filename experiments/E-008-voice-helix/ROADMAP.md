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
- Take pitch: YIN candidates + Viterbi (0.1 % gross error, synthetic; 97.6 ± 0.7 % RPA, false alarm 12.8 % on 40 real singers, vocadito; note edges trimmed on a short window).
- Vibrato rate and extent per take with ± (synthetic means within 0.11 Hz, 0.03 st; `check/vibrato-bench.mjs`); live chip on the same estimator; evenness (cycle-to-cycle CV, within ~2 points on synthetic jitter).
- Slide style told from unwanted scoops (consistent depth on most notes).
- Voice profile: comfortable and full range, voice-type guess, key for a song, register breaks on glides; a guided range finder (lowest, highest, siren) in about a minute.
- Compare: the last 10 takes' audio kept on the device; play an earlier take, then yours; ▶ same phrase finds the current phrase in it (DTW, any key; 95 % found on a vocadito proxy), then vs today in numbers with ±, or every kept version of the phrase in a row.
- Personal bests in the summary: steadiest long note, longest in-tune note, against all kept takes, claimed only beyond one note's noise.
- Practice streak, days and minutes sung, milestones, under the progress lines.
- Screen lag measured live (audio to paint + half pitch window): 18-25 ms median headless, shown as a chip.
- Hosting from main via `voice-helix-publish.yml`; `check/check.mjs` for
  Chrome, Firefox and WebKit iPhone.

## Next

1. **Rating with ground truth**: human-judged takes across styles from openly
   licensed sources only, then a rating that ranks them correctly (see
   `rating/README.md`).
2. **Sharper note edges, part 2**: false alarm 12.8 % on vocadito; threshold/width sweeps of the trim only trade RPA for FA (OA 94.3-94.4), so it needs a finer hop at edges or level-envelope onsets. Real soprano f0 truth still missing.
3. **On-device vocal separation** (ONNX in WASM) so songs with music load
    without Demucs on a desktop.
4. **Vibrato, part 3**: evenness reference from more than two singers (all VocalSet vibrato clips), and per-note truth if any exists.
5. **Same phrase, part 3**: measure the matcher on real re-sung takes (an openly licensed set with repeated renditions of one melody) instead of the slowed-clip proxy.
