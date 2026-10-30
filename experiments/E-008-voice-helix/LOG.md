# Voice Helix log

Newest first. Date, what was built, what a singer can now do, numbers, next.

## 2026-10-30 · key drift on the progress line

Built: each take stores |key drift| (`takeDrift`, synthetic SD 16 ¢, vocadito SD 41 ¢); a 'key drift' row in the take table, a progress line with band and a week line, lower is better, shown but not rated (excluded from the rating and warm-up, given the coarse real-voice agreement). Takes too short for a drift store none and the line skips them. A singer working with a drone now sees whether their tuning holds better over weeks. check.mjs: 12 seeded takes (two without drift), 70 to 15 ¢, read 'better than the takes before', not in RATED, 3 browsers. No new measurement. iOS risk: none (localStorage). Next: real-voice drift agreement (note matching) or edge onsets.

## 2026-10-30 · key drift per take

Built: `takeDrift` (notes after a 0.22 s pitch average, offsets unwrapped against a running reference, weighted line over time, ± 1.96 SE) and `check/drift-bench.mjs`. Synthetic known drifts (90 melodies, 5 voice types, half with vibrato): error +1.4 ± 3.3 ¢, SD 15.8, truth inside ± 81/90. vocadito, page vs hand-corrected f0 through the same code: SD 41 ¢, sign agrees on 11/14 truly drifting clips: coarse on real voices, so the wording is conservative. A singer now hears 'you held your key' (whole ± within 20 ¢) or 'your tuning sank 45 ± 20 ¢ over 30 s' with a drone exercise (Howard 2007). check.mjs: -60 ¢ synthetic reads -54, level reads 0, both wordings, 3 browsers. iOS risk: none new. Next: drift on the progress line; tighten real-voice agreement (note matching).

## 2026-10-29 · swell on the progress line

Built: each take stores its largest within-note swell (`takeDynamics`, the measure benchmarked at messa vs straight AUC 0.93); a 'swell (dynamics)' row in the take table, a progress line with band, and a week line, all saying more swell / flatter, never better or worse (not rated, like tone colour). Takes without a 1 s note store no swell, so the line skips them instead of reading 0. A singer practising messa di voce now sees whether their swells grow over weeks. check.mjs: 12 seeded takes (two without swell) read 'more swell than the takes before', no better/worse, not in RATED, 3 browsers. No new measurement. iOS risk: none (localStorage). Next: edge onsets (finer hop) or tone part 2.

## 2026-10-29 · dynamics per take (messa di voce measured)

Built: `takeDynamics` (level over long notes, 100 ms smoothed; swell p95-p5 within a note, span soft to loud across notes, gain-free) and `check/dyn-bench.mjs` (page code, VocalSet long tones on "a", 20 singers, 80 clips, CC BY 4.0, not shipped): messa di voce swell 21.1 ± 2.6 dB (median 19.3, p10 14.5), straight 9.6 ± 2.1 (median 7.3, p90 13.9); messa vs straight AUC 0.93, pairs 20/20; forte - pp 8.6 ± 3.6 dB. The take summary now says how a singer's level moved, names a swell of 14.5 dB or more a real messa di voce, else suggests one; described, not rated. check.mjs: synthetic swell/level/soft tones (swell 17.9 dB, span 10.0), both wordings, 3 browsers. iOS risk: none new. Next: dynamics on the progress line, or edge onsets.

## 2026-10-29 · vibrato evenness against 20 trained singers

Built: `check/vibeven-bench.mjs` (page code, every VocalSet vibrato clip: scales, arpeggios, three excerpts; 250 clips, 20 singers, CC BY 4.0, not shipped). Per-singer rate CV median 13.6 % (p90 18.1, mean 12.4 ± 1.5), width CV 22.1 % (p90 28.9, mean 22.6 ± 1.9); arpeggios evener (9.5 / 19.0) than excerpts (15.7 / 25.4). The take summary's evenness line now has three tiers on that reference (evener than half / within the range / an exercise beyond the 90th percentile) instead of a two-singer Caro mio ben cut. check.mjs: all three tiers' wording, 3 browsers. iOS risk: none new. Next: edge onsets or tone part 2.

## 2026-10-29 · say my note (eyes-free)

Built: a "say note" toggle (button, N key) that puts the held note and its cents (vs the target note if set, else the nearest note; ±10 ¢ = in tune) into a polite aria-live region, once a note is held 0.4 s, again on change or every 4 s; a `?` key list (Esc closes); the helix canvas is labelled. A blind singer, or anyone singing with eyes closed, now hears their pitch from their screen reader. check.mjs: N on, live region reads e.g. "A3, 20 cents sharp" within 2 s of the demo, ? opens/closes the list, 3 browsers. Not measured: screen-reader speech timing itself (no reader headless). iOS risk: VoiceOver's voice from the speaker reaches the mic; README says use headphones. Next: edge onsets or tone part 2.

## 2026-10-29 · tone colour per take

Built: each take's median spectral tilt (page code, sung frames) as a 'tone colour' aspect: a went-well line naming the colour (bright, belt-like / balanced / soft, airy) against VocalSet's belt +0.5, straight -1.3, breathy -2.4 dB/oct; a row in the take table; a progress line and a week line that say brighter/softer, never better/worse (not rated). Numbers are the clip-median ones from `check/press-bench.mjs` (belt vs straight AUC 0.81, pairs 92.6 ± 5.3 %), the same median the take uses. check.mjs: the tone line appears on both breath demos, 3 browsers. iOS risk: as for CPP, WebKit-decoded MP3 may shift tilt slightly (-1.28 vs -1.36 Chrome on m2). Next: edge onsets or tone part 2 (formant-corrected H1-H2).

## 2026-10-27 · pressed cue retired, tone colour measured

Built: `check/press-bench.mjs` (page code, VocalSet scales belt/straight/breathy, 20 singers, 294 clips). Found: the 'pressed / strained' cue fired on 18 % of belt and straight frames alike (AUC 0.53), uncorrected H1-H2 AUC 0.54: a coin toss shown as a flaw. Retired it (chip and demo gone) and uncoloured H1-H2; the tilt chip, which coloured almost every voice 'warn', now names a tone colour (bright, belt-like / balanced / soft, airy) as a description. Tilt: belt +0.45 ± 0.32, straight -1.29 ± 0.23, breathy -2.39 ± 0.24 dB/oct; belt brighter than straight AUC 0.81, pairs 92.6 ± 5.3 %. A singer who belts is no longer told they strain. iOS risk: none new. Next: tone colour per take in the summary and progress, or edge onsets.

## 2026-10-27 · breathiness, measured (CPP)

Built: CPP (cepstral peak prominence) per frame in the worker; the 'breathy' cue, a live 'clarity (CPP)' chip, a 'voice clarity' progress line and the take summary (praise ≥ 24.5 dB, straw-phonation point < 23 dB) use it. Found first: the old HNR-based breathy cue never fired on VocalSet's breathy scales (AUC 0.36). Numbers (`check/breath-bench.mjs`, 194 VocalSet clips, 20 singers): CPP breathy 22.5 ± 0.6 vs straight 27.0 ± 0.5 dB, AUC 0.90, same-singer pairs 98.9 ± 2.1 %; cue AUC 0.83. Fixed from the failed first attempt: MP3's empty band above 16 kHz cut a straight demo's CPP by 3 dB; CPP now over 0 to sr/4 with a 90 dB floor, and the same clips at 80 kbit/s MP3 read AUC 0.91 (1.3 dB lower overall). Also: check.mjs now runs each browser in its own process (WebKit hung after Chrome and Firefox in one). iOS risk: WebKit on Linux decodes the m2 straight MP3 demo 4.6 dB lower in CPP than Chrome/Firefox (23.9 vs 28.5; the polished take agrees, 21.9 vs 21.8); live mic input is not decoded, but loaded MP3/AAC files on iPhone may read lower. One extra 2048-point FFT per frame. Next: H1-H2/tilt validated on belt vs breathy (pressed cue), or edge onsets.

## 2026-10-26 · this week vs last week

Built: under the progress lines, "This week vs last week (n takes vs m)": every aspect's mean ± 1.96 SE for the last 7 days against the 7 before, better/worse only beyond both intervals, better aspects named first. A singer now hears week-scale progress honestly, not just take-to-take. Tried first: a neighbour-relative note-edge trim on vocadito (R 0.2: FA 12.7, OA 94.3; R 0.3: FA 12.2, RPA 97.2, OA 94.2): no net gain, not shipped. check.mjs: seeded weeks read overall better, others level, 3 browsers. iOS risk: none (localStorage only). Next: rating truth or level-envelope onsets.

## 2026-10-26 · screen lag, measured

Built: a "screen lag" chip in the live rail: per frame, audio chunk arrival → next helix paint + half the pitch window (+ mic latency when the browser reports it, else "+ mic"), median and p90. A singer can now see how far behind their voice the helix is, instead of it being assumed. Numbers (check.mjs, live demo, headless): Chrome 18 ms (p90 19), Firefox 25 (31), WebKit 24 (28). iOS risk: real iPhone input buffering is unreported by Safari, so the chip says "+ mic" there. Next: edge onsets or rating truth.

