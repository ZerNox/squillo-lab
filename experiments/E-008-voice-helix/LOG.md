# Voice Helix log

Newest first. Date, what was built, what a singer can now do, numbers, next.

## 2026-11-01 · spots by keyboard

Built: shift ← → steps through the spots to work on, A/B with spotless as a click does, spoken through the live region ('Shaky pitch at 0:12, spot 3 of 10' style); in the `?` list; a check.mjs test. Its test exposed a real bug: two fast A/B starts both played, one looping unstoppably and feeding the analyser (it broke the siren reading); a token in `abLoop` now lets the newest win. No accuracy measured. Touch still taps the bar. iOS risk: none new. Next: Key drift part 2.

## 2026-11-01 · accessibility measured and fixed

Found with axe-core 4.14 (page's real states: start, scanned take, warm-up, voice profile, my data; Chrome, WebKit iPhone size): secondary text at 3.49:1 contrast on the phone (14-31 elements per state), live readings and summary unreachable by keyboard, no main landmark, headings skipping a level, an empty table header. Built: secondary text brighter, hint and legend on a panel so they read over the terrain, readings and summary focusable with a ring, `main`, h2 headings, note labels hidden from screen readers, the take message announced as a status. `check/a11y-audit.mjs`: 0 violations of WCAG 2 A/AA and best-practice rules in those states; check.mjs now fails on any WCAG violation on a scanned take. Limits: axe finds only part of what a screen-reader user meets and cannot judge text over the canvas; no real VoiceOver run; spots on the timeline were pointer-only, fixed in the entry above. A full check run lost WebKit once ('browser closed', under my 595 s outer limit), then WebKit passed alone in 147 s; cause unproven, the known hang not ruled out. iOS risk: `backdrop-filter` unprefixed on older Safari only loses the blur, background stays. Next: Key drift part 2.

## 2026-10-31 · offline worker made opt-in

Found after shipping: live WebKit runs stalled at the first tap. Service worker on vs blocked, live: 5 of 6 hung vs 0 of 6; without `clients.claim` still 1 of 6, cause not found. So the worker no longer starts by itself: 'keep for no network' under my data starts it, for the next open, and a worker registered in the hour it was automatic is removed on load. Normal visits have none. The hang may be Linux WebKit only; pressing the button on a real iPhone is unverified. Claims in the entry below about automatic keeping are replaced by this. Next: find the hang, Key drift part 2.

## 2026-10-31 · breathy notes no longer read an octave or more low, live

Explained the 25.0 → 49.7 % rise from the last entry: all frames were voiced, but most breathy notes locked onto a subharmonic from the first frame (330 Hz read 110, 523 Hz read 105) and the continuity hint held them; waiting for two frames only dodged some locks. Built: live, a shorter period dividing the chosen one wins when its dip is within `LN.E` 0.05; takes unchanged (offline path, pitch bench identical). Page code: breathy HNR 5 dB read right 49.7 → 99.7 %; vocadito 40 clips live, clean RPA 89.7 ± 1.6 → 90.6 ± 1.3, OA 91.1 → 91.8 ± 1.0, FA 6.5 unchanged; pink 10 dB RPA 80.9 ± 2.8 → 84.5 ± 2.5, OA 86.4 → 88.9 ± 1.7, which wins back the two-frame cost. E chosen on these clips (0.1 gave pink RPA 83.7, OA 88.3), so slightly optimistic. No synthetic live gross-error figure: pitch-bench runs offline only. iOS risk: none new. Next: Key drift part 2.

## 2026-10-31 · on the device: no network needed, no third party

Found: every load asked Google for fonts while the page said 'sent nowhere', and the page was gone without a network. Built: fonts served from `page/font/` (OFL, `SOURCES.md`), so check.mjs now fails on any request off the site; `sw.js` keeps the page, clips, fonts and icons (network first, 4 s, then the copy); manifest and icons for the home screen; under my data, an add button where the browser offers one, or Share, Add to Home Screen on iOS, with the warning that the home-screen app starts empty, so carry a copy over. Real outage, server shut (`check/offline-check.mjs`): Chrome, Firefox and WebKit iPhone size reopen the page, all 26 files kept, a new tab in 276/484/566 ms on localhost. No accuracy claimed. Local WebKit passed 150 s on the final page after two hangs of 295 and 590 s (no failed assertion; the known random hang, cause not found, this change not ruled out). WebKit: Playwright's setOffline breaks navigation, hence the separate script. iOS risks, unverified on a real iPhone: mic and the file save inside a home-screen app; separate storage and the 7-day rule are as WebKit documents them. Next: Key drift part 2.

## 2026-10-31 · fewer live ghost notes, part 3

Built: live, a frame counts as a note only when the frame before agrees within a semitone (`LN.M` 2); one-frame blips no longer draw. Page code, live, vocadito 40 clips: clean FA 11.0 ± 2.2 → 6.5 ± 1.4, RPA 90.9 ± 3.5 → 89.7 ± 1.6, OA 90.3 → 91.1 ± 1.3; pink 10 dB FA 5.3 → 2.6, RPA 83.6 → 80.9, OA 87.4 → 86.4 ± 2.0 (a real cost in noise, within its band). Note starts draw one hop (20 ms) later. M 3 and up lost more than it gained (clean RPA 84.4 at 3, 74.7 at 5, on 14 clips). M chosen on these clips. Take pitch unchanged (low 97.3, high 97.4). Breathy live bench at HNR 5 dB read 25.0 → 49.7 %, a rise this gate should not cause, not explained; do not rely on it. iOS risk: none new. Next: Key drift part 2.

## 2026-10-31 · my data: a copy, and a real delete

Found: progress lived only in the browser, and Safari can clear script storage after 7 days away from a site not on the home screen, so a holiday could erase the progress line; 'forget my takes' deleted at one tap yet left kept audio, marks and warm-up readings behind. Built: ⛁ my data (reachable with no takes, so restore works after a wipe): counts what is kept, save a copy (one JSON file, no audio), bring one back (merges by date, existing records win, markup refused, 5 MB limit), delete everything including audio after a second tap; `navigator.storage.persist` asked on saving; a line under progress from 5 takes when no copy exists or the last is over 14 days old. check.mjs does a real download, delete, file input and repeat import in all three browsers; retries now print why. No accuracy measured: none claimed. iOS risk: 'copy saved' shows when the download starts, before Safari's Files prompt, so a cancelled save still reads saved; the file flow is unverified on a real iPhone. Next: Key drift part 2 or live false alarms.

## 2026-10-31 · no pulse said in words

Built: the summary's rhythm row says 'free timing, no steady pulse' or 'too few notes to find a pulse' instead of a bare dash; a check.mjs test. No new measurement. Local WebKit hangs at random steps (twice this run, no failed assertion): run `--only` per browser with a 290 s timeout. Next: Key drift part 2 or live false alarms.

## 2026-10-31 · pulse found through a stray note

Found: the two vocadito annotators disagree on a pulse as much as the page does (7 and 14 clips, 7 shared), and one stray or missed note start hid a real pulse; the old limit also passed 38/400 random onset sets (the earlier 0/20 and 0/40 hid that). Built: `pulseFit` decides on the closest 90 % of note starts (`PULSE_MAX` 0.11, was 0.15 on all), reported spread stays on all starts; `check/timing-bench.mjs` now scores against the clips both annotators pulse; a check.mjs test. A singer with a steady beat and a stray note gets their rhythm read instead of 'free timing'. Page code: of 7 clips both annotators pulse, found at their step 5 (was 3); random onsets 17/400 false (was 38). Synthetic: jitter 15/30 ms found 60/60, 60 ms 34/60, spread within 3 ms, free melodies 0/40. Tuned on the same clips with only 7 positives: indicative. Next: Key drift part 2 or live false alarms.
