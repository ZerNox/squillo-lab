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
- Slide style told from unwanted scoops (consistent depth on most notes).
- Hosting from main via `voice-helix-publish.yml`; `check/check.mjs` for
  Chrome, Firefox and WebKit iPhone.

## Next

1. **Pitch tracker**: replace the prototype YIN with pYIN-style candidates and
   Viterbi for takes (offline, no delay limit); measure against VocalSet and
   E-002's benchmark before and after.
2. **Phone layout of the take view**: timeline, summary and coach readable at
   iPhone size without scrolling past the helix.
3. **Warm-up**: a short guided routine from the flaws seen most in recent takes.
4. **Range and voice profile** from the takes kept on the device.
5. **Rating with ground truth**: human-judged takes across styles from openly
   licensed sources only, then a rating that ranks them correctly (see
   `rating/README.md`).
6. **On-device vocal separation** (ONNX in WASM) so songs with music load
    without Demucs on a desktop.
