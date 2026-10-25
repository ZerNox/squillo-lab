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
- Warm-up: about 4 min, steps chosen from the last 5 takes, cited, guide tones.
- Phone: the take comes first after a scan, progress lines full width.
- Take pitch: YIN candidates + Viterbi (0.1 % gross error, synthetic; 98.1 ± 0.7 % RPA on 40 real singers, vocadito).
- Slide style told from unwanted scoops (consistent depth on most notes).
- Voice profile: comfortable and full range, voice-type guess, key for a song, register breaks on glides; a guided range finder (lowest, highest, siren) in about a minute.
- Compare: the last 10 takes' audio kept on the device; play an earlier take, then yours.
- Hosting from main via `voice-helix-publish.yml`; `check/check.mjs` for
  Chrome, Firefox and WebKit iPhone.

## Next

1. **Rating with ground truth**: human-judged takes across styles from openly
   licensed sources only, then a rating that ranks them correctly (see
   `rating/README.md`).
2. **Sharper note edges**: false alarm 17 % on vocadito, mostly within 35 ms of note edges (20 ms hop, long window); a finer hop or edge refinement at take time. Real soprano f0 truth still missing.
3. **On-device vocal separation** (ONNX in WASM) so songs with music load
    without Demucs on a desktop.
4. **Compare the same phrase**: align today's take with an earlier one and A/B phrase by phrase.
