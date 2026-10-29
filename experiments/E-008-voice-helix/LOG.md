# Voice Helix log

Newest first. Date, what was built, what a singer can now do, numbers, next.

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

## 2026-10-26 · loop a phrase

Built: ⟲ loop phrase (L key) next to the playback buttons: loops the phrase around where the take is playing, or the note stepped to (same phrase finder as "same phrase"), padded 0.2/0.3 s, in the version (yours, halfway, spotless) and speed last chosen, seamless via loopStart/loopEnd; pressed state for screen readers. A singer can now drill one phrase, sing along with the spotless version at 0.5×. check.mjs: loop under 8.6 s, pressed, stops on a second tap, 3 browsers. iOS risk: none new (context created in the click path, no new APIs). Next: edge onsets or rating truth.

## 2026-10-26 · practice streak and milestones

Built: under the progress lines, "n days in a row · d days sung · m min of singing kept · milestone · next", from the kept takes' local dates; a streak still counts until midnight and says "sing today to keep it". Counts only, never a score. check.mjs: 7 seeded days + today read "8 days in a row" in 3 browsers; 3 days without today keeps 3. iOS risk: none. Next: edge onsets or rating truth.

## 2026-10-26 · personal bests

Built: the take summary's "went well" names personal bests over long notes (held ≥ 1 s), against every earlier take kept on the device: the steadiest note (least wobble) and the longest note held within 10 ¢, with the time to find it. A new best is claimed only when it beats all earlier takes by more than one note's reading noise (1 ¢, 0.3 s) and after 2 earlier takes; within 1 ¢ it says "matches your best". Old history records have no bests and are skipped. check.mjs: new best, and a match, in 3 browsers. iOS risk: none new (localStorage only). Next: edge onsets or rating truth.

## 2026-10-26 · vibrato evenness

Built: the take summary adds "Vibrato evenness: rate varies x ± % and width y ± % cycle to cycle", compared with the VocalSet trained singers on Caro mio ben (rate ~11 %, width 23-29 %), with an exercise (slow sirens, messa di voce) when less even. Cycles from zero crossings of the detrended pitch with hysteresis. Numbers (`check/vibrato-bench.mjs`, page code): rate CV true 2.9/8.7/17.3 % read 3.1/7.5/15.3 % (± ≤ 1.5); extent CV true 0/11.5/23.1 % read 2.3/12.2/22.9 %. check.mjs: pure 6 Hz take reads even in 3 browsers. iOS risk: none new. Next: edge onsets or rating truth.

## 2026-10-26 · live vibrato chip on the take estimator

Built: the vibrato chip while singing now uses the take's estimator (note-change cuts, detrend, autocorrelation) on the last 1.2 s of the current note, so legato steps no longer show as vibrato. Numbers (`check/vibrato-bench.mjs`): per-note rate error median 0.07 → 0.04 Hz, p90 0.13 → 0.11; 0/30 straight notes flagged; take figures unchanged. iOS risk: a little more work per frame (about 60 frames × 14 lags), small. Next: vibrato regularity.

