# Experiment index

The questions from `squillo/VISION.md` §12. Status: `open` · `running` · `needs-human` · `answered` · `abandoned`. For squillo's lab rule (`PLAN.md` §5, rev 25), a question is closed once its status is `needs-human` (automated evidence in, only a human step left), `answered` or `abandoned`.

| ID | Question | Vision | Status | Result (one line) |
| :--- | :--- | :--- | :--- | :--- |
| [E-001](experiments/E-001-voice-resynthesis/) | Can a singer's own voice be re-synthesized, improved on one aspect, convincingly and on-device? | §3, §8, §12.1 | running | Round 1, pitch, synthetic and 19 VocalSet singers: WORLD and PSOLA deliver note-centre correction and steadying as requested (achieved/requested 0.98–1.05, per-frame p95 3.0–5.2 cents); envelope moves 0.03–0.71 dB against 3.03 dB within one singer; 0.034–0.29 s per second of audio, native, not WASM; squillo's tracker misreads WORLD's output an octave high on up to 2.8 % of frames. Listening check `needs-human` |
| [E-002](experiments/E-002-measurement-reliability/) | Which vocal aspects can be measured reliably, and with what uncertainty? | §5, §6, §12.2 | running | Round 1, pitch, synthetic: YIN at squillo's frame axis stays within ±3 cents (max 0.03 on pure, 0.98 on harmonic tones) down to 30 dB white-noise SNR and refuses at ≤ 5 dB; range-edge guard band 0.03 cents; moving pitch needs the lag-centre instant (vibrato p95 ≤ 3.8 cents there, ≤ 30 at the window centre); CMND dip predicts error. Real voices open |
| [E-003](experiments/E-003-capture-reality/) | What do real browsers do to the microphone signal, what do they report, and do blocks reach the engine worker intact? | §6, §12.3 | open | — |
| [E-004](experiments/E-004-phrase-library/) | Can 30 short phrases across genres be built from verified public-domain and original material? | §7, §9, §12.5 | open | — |
| [E-005](experiments/E-005-intent-inference/) | Without a reference, can the note a singer aimed for be inferred from their take, well enough to score pitch accuracy with an honest ±? | §3, §5, §12.4 | open | — |
