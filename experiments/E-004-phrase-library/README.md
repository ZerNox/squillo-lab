# E-004 — A publishable phrase library

**Status:** needs-human (rounds 1–3 automated evidence in; a listening check remains for round 1's from-memory melodies and the originals) · **Serves:** VISION §7 (the guided library), §9 (first slice), §12.5

## Question

Can about 30 short sung phrases (a lyric line plus melody, at most a few
seconds each) across at least five genres be assembled entirely from verified
public-domain and original material, each with a recorded source and licence?

## Hypothesis

Yes. Hymns, Bible songs, folk and traditional songs and several national
anthems are out of copyright in text and melody. Original phrases fill the
genres public domain covers poorly (pop, rock, jazz). Arrangements and modern
translations are the traps.

## Protocol

1. Candidate sources, each verified: author and composer death dates or
   publication dates, and the specific edition used (arrangements and
   translations carry their own copyright).
2. For each phrase: text, melody (note sequence and rhythm), genre, vocal
   range, and source with licence rationale.
3. Fill uncovered genres with original phrases written for squillo (licence:
   the project's own).
4. Output: `results/library.json` plus `results/SOURCES.md`, ready to become
   squillo phrase items under ADR 0005 as revised in squillo iteration 22
   (`format_version` 2): one phrase per file with exactly `phrase_id`,
   `title`, `instructions` and `content` (an SPDX licence expression and a
   source). Words, melody, genre and range are not yet members; this
   experiment says which of them a verified phrase must record, and
   squillo's next revision of ADR 0005 adds them. (Done: squillo iteration
   29 folded this result into ADR 0005, `format_version` 3, and `exercises`
   EX-010 and EX-011; see *Folded* below.)

A note on copyright: short excerpts are **not** exempt. There is no
"30-second rule"; lyrics and melodies are protected however short the
reproduction, when used systematically in a product.

## Round 1 (squillo iteration 23)

```
uv run python run.py verify    # rights rules + Wikidata dates   -> results/verify.json
uv run python run.py scores    # melodies against Wikipedia scores -> results/scores.json
uv run python run.py measure   # E-005 intent inference per phrase -> results/measure.json
uv run python report.py        # -> results/summary.json, library.json, SOURCES.md
uv run python listen.py        # needs-human: WAVs + results/listen.csv to fill in
```

Tools: Python 3 via `uv` (`uv.lock`), LilyPond 2.24.3 from PyPI's `lilypond`
wheel, mido 1.3. Pitch and inference are E-005's code, unchanged
(`squillo-lab E-005 @ 38deb75`: E-002's YIN at ADR 0007's frame axis,
E-001's synthetic voice). Wikipedia and Wikidata were read on 2026-09-26
through their public APIs; the Wikipedia revision of every score used is in
`results/scores.json`.

**Candidates** (`library.py`). 31 public-domain phrases in seven genres
(hymn 5, spiritual 1, carol 8, children's 3, folk 7, anthem 3, classical 4),
each the first line of words and tune. Each part names its authors,
translators and arrangers with a death year, a year by which it was
certainly published, and the edition. There are also seven originals written
for squillo (pop, rock, jazz, blues, soul, country, musical theatre). Nine
**traps** are recorded by title and dates only, with no words and no notes:
songs that look free but are not, not verifiably, or whose familiar form is
later work. The agent wrote every melody from memory before opening any
comparison score. Three had already been seen during the survey of which
articles carry scores (Amazing Grace, Silent Night, Joy to the World), and
they are reported apart. Nothing was corrected after the comparison
(`CORRECTIONS` is empty). The only change made after it was to two score
pointers, both to the range figure in an infobox: La donna è mobile's
article has no melody score, and Habanera's melody is its third block.
Every comparison uses the block `library.py` names. A first pass took the
best-matching block, and for In the Bleak Midwinter that was Darke's
setting, not Holst's; squillo L-027 records it.

**Rights rules** (`run.py`, as at 2026-01-01):

- `us`: text and tune first published by 1930 (17 U.S.C. 304, 95 years).
- `life70`: every named contributor died by 1955, and every anonymous part
  was published by 1955. This is the EU and UK term (Directive 2006/116/EC
  art. 1; CDPA 1988 s. 12) and Sweden's (URL 43 §).
- `life100`: the same with 1925. This is Mexico's life + 100 (LFDA art. 29),
  the longest general term in force.

A phrase is **publishable** when it passes `us` and `life70`. It may carry
the SPDX identifier `CC-PDM-1.0` (Public Domain Mark: free of known
restrictions worldwide; in SPDX License List 3.29.0) only when it also
passes `life100`. An unknown date fails. Death years are cross-checked
against Wikidata (P570), through each person's English Wikipedia article.
Where the two disagree, the later year is used. Publication years are
cross-checked against the song's Wikidata item (P577, P571).

**Melody check** (`run.py scores`). Each Wikipedia article with a `<score>`
has its block compiled with LilyPond to MIDI, one track per voice. The
agent's phrase is aligned to it with the transposition removed, and scored on
pitch intervals, pitch edit distance, and inter-onset intervals up to one
overall factor. A tolerance of 2 % absorbs MIDI tick rounding. Wikipedia's
transcriptions (CC BY-SA) are used only as this independent check: no note
of theirs enters `library.py`.

**Measurability** (`run.py measure`). Each phrase is sung by E-001's
synthetic voice in six voice types (bass to high soprano), transposed into
each voice. It is sung with per-note error sd 0 or 20 cents, and with no
vibrato or 5.5 Hz ±50 cents vibrato. Scoops, wobble and the singer's own
tuning (±50 cents) are as in E-005. That gives 912 renderings. E-005's
inference is run on each (estimated segmentation, the take's own tuning,
nearest semitone), and each note's aimed pitch is scored found or not by
E-005's `attribution`.

**Input check** (squillo standing instruction S15). The voice, and its
spectral check against VocalSet, are E-005's, unchanged (E-005 README,
*Input check*). Every rendered note lies from F♯2 to A5, inside ADR 0007's
E2–C6. No note is shorter than E-005's 100 ms transition limit (the
shortest is 125 ms). The truth, note boundaries and aimed notes, is known by
construction.

## Result

| # | Question | Result (conditions; uncertainty) |
| ---: | :--- | :--- |
| 1 | Do the rights rules reject the traps? | **9 of 9 rejected.** St. Louis Blues and All Things Bright and Beautiful (to ROYAL OAK) pass `us` and fail only `life70`. Happy Birthday and the partisan Bella ciao pass `life70` and fail only `us`. So neither rule alone is enough |
| 2 | How many public-domain candidates pass? | **30 of 31 publishable** (`us` and `life70`). The one failure is Clementine: the author "Percy Montrose" has no verifiable death year. **28 of 31** also pass `life100` and may carry `CC-PDM-1.0`. In the Bleak Midwinter (Holst, d. 1934) and Danny Boy (Weatherly, d. 1929) are free in the US and under life + 70, not under life + 100 |
| 3 | Do the recorded dates hold? | Of 51 people, 49 death years agree with Wikidata. 1 disagrees: W. H. Monk, recorded 1889, Wikidata 1899; English Wikipedia gives 1889, and neither year changes a verdict. 1 has no entry (Montrose). Publication: 27 of 28 songs with a Wikidata date are consistent with the recorded upper bound. The exception is Joy to the World, whose Wikidata item, described as the 1719 hymn, carries a 1994 publication date: a Wikidata error |
| 4 | Is a from-memory melody right? | Against an independent transcription (20 phrases had one): pitch exact for **16 of 20**, 80 % (Wilson 95 % 58–92 %). For the 17 not seen before: **13 of 17**, 76 % (53–90 %). Intervals right: 134 of 149, 90 % (84–94 %). Rhythm exact, given exact pitch: **12 of 16**, 75 % (51–90 %). Wrong in pitch: In the Bleak Midwinter, Auld Lang Syne (a variant: Wikipedia's version has F F F where the agent wrote F E F), Danny Boy, Habanera. Wrong in rhythm: Old Hundredth, My Bonnie, Aura Lea, Brahms' Lullaby |
| 5 | How many phrases survive every check? | **19 verified**: 12 public-domain (rights pass; pitch and rhythm match an independent transcription) and 7 originals, across **12 genres**. The verified public-domain phrases are hymn 2, carol 5, children's 3, folk 1 and classical 1; the originals are pop, rock, jazz, blues, soul, country and musical theatre. Another **18** pass on rights, but no independent transcription has confirmed their melody: 10 have no score, 4 are wrong in pitch, 4 in rhythm. **0 anthems are verified**, because none of the three has a Wikipedia score |
| 6 | Can intent be inferred on these phrases? | E-005's method finds the aimed note for **100 %** of 2004 notes with no error and no vibrato. With vibrato: **97.6 %** (phrase bootstrap 95 % 95.5–99.3 %). At 20 cents per-note spread: **96.8 %** (95.6–97.7 %). Both: **93.1 %** (91.4–94.5 %). With true note boundaries, vibrato costs nothing (100 %), so the loss is segmentation. Held notes lose most: under vibrato with no error, 100 % of notes under 0.3 s are found, but 92.9 % of notes of 1 s or more. Worst phrases (vibrato, no error): Swing Low 69 %, Abide with Me 78 %, In the Bleak Midwinter 83 % |
| 7 | Are the phrases short and singable? | 38 phrases: 1.6 to 13.3 s at their tempo (median 5.3 s), range 3 to 16 semitones (median 9); 36 of 38 within an octave |

**Answer to §12.5, round 1: yes.** The 30 is reachable, and the rights side
is automatic and reliable: two rules together reject every trap, and death
dates hold against an independent source. The weak step is the melody. A
phrase written from memory is wrong in pitch about one time in four, and
wrong in rhythm about as often. So a library item is **verified only when its
notes have been checked against an independent transcription or the cited
edition**. Round 1 verifies 19. Two routes reach 30: check the 18 phrases
whose rights pass against their editions, or write more originals. The
originals carry no rights risk, but their resemblance to existing songs is
checked only by a listener (below).

**What a verified phrase must record** (for squillo's next revision of
ADR 0005). Words and their language. The melody as notes and durations, with
tempo, meter and key, because range and duration derive from it and are not
stored. Genre. And content provenance **per part** (words, tune,
translation, arrangement): each contributor with a death year, a
published-by year, and the edition. With these, the build can re-run the
rights rules the way it checks SPDX identifiers today. Also the independent
transcription the melody was checked against. The licence is `CC-PDM-1.0`
only when `life100` passes. Otherwise the item needs a `LicenseRef-` saying
where it is free, or it stays out. Originals are `LicenseRef-squillo-adr-0008`
until squillo ADR 0008 chooses a licence.

**For measurement** (`VISION.md` §12.4): library phrases are easier than
E-005's random melodies (96.8 % against E-005's 92.3 % at 20 cents), because
their notes are longer and fewer. The one caution is for phrases chosen for
vibrato: long held notes under wide vibrato are where segmentation splits a
note (E-005's molto-vibrato finding, seen here per phrase).

**Limits.**

- The rights rules are a model, not legal advice. They leave out war-time
  extensions (France), the rule of the shorter term, typographical rights in
  editions (a transcription copies no edition's layout), and moral rights.
  None of these changes a verdict in this set as at 2026, and a lawyer or
  Joakim should read them before release.
- Publication dates are upper bounds from the named editions. They are
  checked against Wikidata only where it has a date.
- Wikipedia's transcription is one version. A mismatch can be the article's
  variant (Auld Lang Syne), and a match confirms the familiar form, not the
  cited edition.
- The originals' resemblance to copyrighted songs has not been checked
  automatically: no corpus of copyrighted melodies can lawfully be used here.
- Measurability is on a synthetic voice only (E-005's conditions).

**Next.** A round 2, not needed to answer the question, would check the 18
pending melodies against an edition scan or a second licensed transcription
(for example the Mutopia Project's LilyPond sources), and add a verified
anthem.

## Folded (squillo iteration 29)

squillo's ADR 0005, revised in iteration 29 (Q-017), takes the record
above: `format_version` 3, a phrase with `genre`, `language`, `words` and
`melody` (notes as objects with scientific pitch and exact fractional
durations), and, for a public-domain phrase, `provenance` per part (words,
tune) and `melody_checked_against`. The squillo build is to re-run the
rules as at 2026-01-01, and squillo ships a public-domain phrase only when
it passes `us` and `life100` (which implies `life70`) under `CC-PDM-1.0`.
Recomputed from `results/verify.json` at this commit: `us` and `life100`
pass 28 of 31 candidates and reject 9 of 9 traps. So In the Bleak Midwinter
and Danny Boy, free under `life70` only, stay out, and their
`LicenseRef-public-domain-us-life70` in `library.json` is not used. A
throwaway check in `/tmp`, run in squillo iteration 29 and not committed,
wrote the 19 verified phrases in that format: 19 of 19 load and pass.

## Round 2 (squillo iteration 41): a second transcription

**Question.** Of the 18 phrases that pass the rights rules with their
melody unconfirmed, how many match a second, independent transcription,
named in advance (squillo F-026, standing instruction S16)? This moves the
verified count towards `VISION.md` §9's 30 without a listener.

**Rules, written before the survey ran.**

1. *Survey, metadata only* (`round2.py survey`). For each pending phrase:
   the Mutopia Project pieces found by fixed title queries (`MUTOPIA_Q`),
   with instrument, source and licence; and, in 16 Wikipedia language
   editions in a fixed order (`LANGS`: de, fr, es, it, nl, sv, pl, pt, ru,
   uk, cs, fi, da, no, ja, zh) linked from the English article, each
   `<score>` block's heading, the text around it and any LilyPond title.
   Nothing is compiled or compared.
2. *Naming the reference* (`REFS` in `round2.py`), from that metadata
   alone, and committed before `check` runs. In order of preference:
   a Mutopia piece that sets this tune for voice (an instrumental
   arrangement is excluded), since it transcribes a named printed edition;
   else the first language in `LANGS` whose article has a block that, by
   its heading, caption or title, sets this tune's melody, and in it the
   first such block. A block whose source equals, whitespace removed, a
   block of the English article is a copy and is skipped. A phrase with no
   such source has no reference and stays pending.
3. *Comparison* (`round2.py check`): round 1's `compare`, unchanged. Pitch
   exact (every interval, transposition removed) and rhythm exact (every
   inter-onset interval within 2 % after one overall scale) against the
   named reference, in any voice of it. Mutopia's own MIDI file is used
   where it has one; a Wikipedia block is compiled with LilyPond as in
   round 1.
4. *Verdict.* `verified-2`: exact in pitch and rhythm against the second
   reference, and round 1 had no reference. `verified-variant`: the same,
   where round 1's reference disagreed; the phrase then matches one
   independent version and not another, both recorded. Both count as
   verified, since round 1's bar is a match with an independent
   transcription; the variants are reported apart so squillo can hold them
   out. Anything else stays pending, with its reason.
5. *Checking the check* (S15). On every reference: the first eight notes
   of its longest voice must pass (first written as "of the voice
   matched", which is not known before comparing); the same with one pitch moved a
   semitone must fail on pitch; with one duration doubled must fail on
   rhythm.
6. *What counts towards 30.* squillo ships a public-domain phrase only when
   it passes `us` and `life100` (ADR 0005, iteration 29). The count is
   reported under that rule, and under round 1's `us` and `life70`.

The rules and `round2.py survey` were committed first (`squillo-lab`
e59ea63), then the survey's output and `REFS`, named from it
(b16e9e5), and only then was `check` written and run.

```
uv run python round2.py survey   # 5.5 min: 235 requests (28 Mutopia searches, 28 piece pages, 179 Wikipedia reads), 1 s apart, each cached -> results/r2-survey.json
uv run python round2.py check    # 10 s -> results/r2-check.json
uv run python round2.py report   # -> results/r2-summary.json
```

The survey was not timed before it ran, as S19 asks; it is a count of
requests times their spacing, and it caches each request, so it resumes
(squillo L-039). Wikipedia revisions used are in `r2-survey.json` and
`r2-check.json`; Mutopia files were read on 2026-09-28. Tools as round 1.

**References named** (`REFS`, with the reason for each). 9 of the 18
have one: 4 from Mutopia (Old 100th from its Genevan Psalter 1551 edition,
EVENTIDE, CRANHAM, all SATB, and Brahms Op. 49 No. 4 for voice and piano,
all Public Domain) and 5 from other Wikipedias (Auld Lang Syne and La
donna è mobile, de block 0; God Save the King, The Star-Spangled Banner
and La Marseillaise, it block 0). 9 have none: 7 have no Mutopia hit and
no score in the 16 editions, Habanera's only Mutopia hit is the Carmen
prelude for piano, and Aura Lea's only other score (fr) is a copy of the
English block. Mutopia's other hits were other pieces or instrumental
arrangements.

**Checking the check** (rule 5). On 8 of 9 references all three cases
behave: the reference's own first eight notes pass, one pitch moved a
semitone fails, one duration doubled fails. On the ninth, La donna è
mobile's de block 0, the must-pass case fails: the block is the aria's
range figure (two notes), not its melody, which its heading and table did
not show. A reference that fails its own must-pass case is no check, so
that phrase stays pending (`pending-check-failed`); this consequence of
rule 5 was written into `check` after its first run showed the failure,
and it changes no other verdict.

**Checks made able to fail (squillo iteration 47, F-050 b).** R-09
found that rule 5's must-fail cases moved the pitch at index 3 and doubled
the duration at index 2 of La donna's one-note list, which changed
nothing, and that rule 2 had no case at all. Now: the moved and doubled
notes are taken at an index that exists (3 and 2, or the last note), each
must-fail input is asserted to differ from the must-pass one, and a voice
of fewer than two notes is too short to check (its must-pass case fails).
Rule 2's mechanical part is checked (`rule2_check`, `results/r2-rule2.json`):
a Mutopia reference must be a piece its phrase's own queries found, with
the named file among the piece's files; a Wikipedia reference must be a
block the survey lists for that phrase and language, and not a copy of an
English block; a phrase left with no reference for "no score in the 16
editions" must have no block, and one left for "a copy" only copies. The
check refuses three references that break it (Aura Lea's copied fr block,
Mutopia 194 named for Abide with Me, a de block 1 La donna's article does
not have) and a phrase with a block called "no score", and passes all 9
named references and all 9 phrases without one. Which block sets the tune
is read from its heading and is not checked by code; for every named
Wikipedia reference, no earlier language in `LANGS` has a block that is
not a copy, so the first-language order of rule 2 is not in question.
Every verdict, `r2-check.json` outside `self_check`, and `r2-summary.json`
are unchanged.

**Recorded checks asserted (squillo iteration 57, F-054 b).** R-10 found
that `all_named_pass` and `all_no_ref_pass` were written to
`r2-rule2.json` and never asserted, and that `rule2_no_ref_check` returned
`ok=True` for a reason naming no block claim, a branch that could not
fail. Now both keys are asserted in `rule2_all`, that branch returns
`ok=False`, and a new must-fail probe (a phrase whose reason names no block
claim, `must_fail_no_ref_reason_names_no_claim`) fails as it must. Re-run:
every value of `r2-rule2.json`, `r2-check.json` and `r2-summary.json` is
unchanged; the one new key is the probe's `false`. In `r2-check.json`,
`self_check`'s `must_pass`, `must_fail_pitch` and `must_fail_rhythm` are
recorded, not asserted, by design: a reference failing them is not an
error but a verdict (`pending-check-failed`, La donna è mobile).

## Round 2 result

| # | Question | Result (conditions; uncertainty) |
| ---: | :--- | :--- |
| 1 | How many pending phrases have a second, independent reference? | **9 of 18** named from metadata; **8** usable (La donna è mobile's is a range figure). 9 have none in Mutopia or 16 Wikipedias |
| 2 | How many match it in pitch and rhythm? | **1 of 8**: Abide with Me against Mutopia's EVENTIDE, 9 of 9 intervals and 9 of 9 inter-onset intervals at scale 1.0. Its round 1 status was *melody unchecked*, so it is `verified-2`; no `verified-variant` |
| 3 | Where round 1 found a mismatch, does the second reference side with the phrase? | **0 of 4.** In the Bleak Midwinter (Mutopia CRANHAM: 2 of 5 intervals wrong) and Auld Lang Syne (de: 2 of 7) differ in pitch again; Old 100th (Mutopia, Genevan 1551: pitch exact, 4 of 7 inter-onset intervals at scale 2.0) and Brahms' Lullaby (Mutopia: pitch exact, 0 of 5 at scale 0.85, as against the English block) differ in rhythm again. Two independent transcriptions against the phrase each time: these are the agent's errors, or a variant neither source prints |
| 4 | The anthems? | **0 of 3 verified.** God Save the King (2 of 5 intervals wrong), The Star-Spangled Banner (4 of 11) and La Marseillaise (3 of 8) differ from the it article's first block. In each, that block is the earliest printed form, and it is the edition `library.py` cites or its near neighbour: Thesaurus Musicus 1744 (cited), Dannbach, the Strasbourg printer, 1792 (cited: Strasbourg 1792), and Blands' c. 1790 Anacreontic Song (cited: Smith's, by 1778). The article says the modern form differs from these (the anthem's first bar; the Star-Spangled Banner's arpeggiated opening). So each phrase writes a later form than the edition its provenance cites: a provenance error the build's rights check would not see, whatever the phrase's accuracy against the modern form |
| 5 | The library now | **20 verified**: 13 public-domain and 7 originals, across the same **12 genres** (hymn now 3). All 20 pass squillo's shipping rule (`us` and `life100`) as well as round 1's. 10 short of `VISION.md` §9's 30. Still pending: 17 (9 without a reference, 1 with an unusable one, 7 that differ) |

**Answer.** A second transcription named in advance moves one phrase,
not the eighteen F-026 hoped for. Half the pending phrases have no
second machine-readable score in Mutopia or 16 Wikipedias, and where
there is one it confirms round 1's four mismatches rather than
overturning them. So the from-memory route is spent: checking cannot
reach 30. Two routes remain, both outside this round. (a) Take a
phrase's notes **from** a public-domain edition instead of checking
memory against it: Mutopia's Genevan Psalter 1551 (Old 100th) and
Brahms (Op. 49 No. 4) are marked Public Domain, and the melody is then
the cited edition by construction. (b) Write more originals, whose only
open check is a listener's (below). For the anthems, the cited edition and
the melody written must agree: either the phrase cites the later edition
whose form it writes (for the Star-Spangled Banner, perhaps the 1918
standard the it article prints, if its rights pass) and is checked
against that, in a new round counted apart as a second attempt, or its
notes are taken from the early edition it cites, by route (a).

**Limits.** Mutopia's EVENTIDE and CRANHAM give cyberhymnal.org as their
source, not a printed edition. A match confirms the version the reference
prints, not the edition `library.py` cites. Rule 2 took the first block,
which in the Italian anthem articles is the oldest edition; that is the
cited edition for two of the three, so the rule's choice and the
provenance agree there. The two
references of the four round 1 mismatches were not compared with each
other.

## Round 3 (squillo iteration 57): notes and words from the edition

**Question.** Round 2 showed that checking from-memory melodies cannot
reach `VISION.md` §9's 30. If a phrase's notes **and** words are taken
from a named public-domain edition, so that the melody is the cited edition
by construction (squillo F-044, route (a)), how many such phrases pass
round 1's rights rules and squillo's shipping rule (`us` and `life100`),
and does the library reach 30 across genres?

**Source.** The Mutopia Project: LilyPond transcriptions of named printed
editions, each with its own licence. A transcription marked Public Domain
by its typesetter adds no rights of its own; one under CC BY or CC BY-SA
would, so only Public Domain ones are used.

**Rules, written and committed before the survey ran** (`round3.py`).

1. *Survey, metadata only* (`survey`). Every page of Mutopia's listing for
   instrument Voice, every style, 10 pieces a page, following the listing
   until it ends. Per piece, the listing's cells: title, composer, opus,
   instrument, date, style, lyricist, arranger, source (the edition),
   licence, and the file links. No file is downloaded. (Correction, made
   after the first screen and before any file was read: the code first
   took the arranger cell for the poet and missed the lyricist cell; the
   piece pages' labels, read for 516, 526 and 640, fixed it, and the screen
   was re-run on the cached pages. "n/a" names no one.)
2. *Screen, mechanical, from that metadata alone* (`screen`). A piece is
   eligible when: (a) its licence is Public Domain; (b) the lyricist cell
   names someone, so the edition has words; (c) every named composer,
   lyricist and arranger has a death year in Mutopia's cells (anonymous and traditional parts need
   none); (d) the source cell names a year, the edition's (the latest
   four-digit year it names), taken as the published-by year of every part,
   since the edition prints both; (e) round 1's rules pass on that, `us`
   (the edition by 1930) and `life100` (every named person died by 1925, an
   anonymous part published by 1925), squillo's shipping rule; (f) it has a
   MIDI and a LilyPond file; (g) neither its title nor its tune is one of
   the 20 verified phrases' (the tune named by the agent from the
   metadata; added after the first screen listed Adeste Fideles, Mutopia
   367, which sets the verified O Come, All Ye Faithful's tune with its
   Latin words, and before any file was read). The rights rule is first run on one case it must pass and four
   it must fail (an edition of 1931, a death in 1926, an unknown death, an
   anonymous part published 1926), each differing in its input.
3. *Order.* Phrases round 2 left pending come first, in its `PENDING`
   order, if an eligible piece sets their tune (named from the metadata).
   Then the rest, one at a time: the piece whose genre (Mutopia's style,
   mapped by `GENRE`) has fewest phrases in the library so far, ties by
   lower Mutopia id. Each phrase taken counts towards its genre before the
   next is chosen.
4. *People* (`PEOPLE`). Before any Wikidata, MIDI or LilyPond file is
   read, the agent names, from the survey's metadata alone, the English
   Wikipedia article of every named person of the eligible pieces it may
   reach, and commits it. Death years are then cross-checked against
   Wikidata (P570) as in round 1; where the two disagree the later year is
   used, and the rights rules re-run on it. A person with no article keeps
   Mutopia's year, reported as unchecked. (c) The LilyPond file's own
   header is also read: a translator or arranger it names is a contributor
   too, needing a death year, or the piece is excluded.
5. *Extraction* (`extract`), in rule 3's order, until 10 phrases pass
   (20 + 10 = 30) or the list ends. A piece that fails any step is
   excluded with its reason, and the next is taken.
   (a) Mutopia's own MIDI file, made by its LilyPond from the edition's
   transcription; if it holds no lyric events, the LilyPond file compiled
   with LilyPond 2.24.3 after `convert-ly`, a `\midi` block added where a
   score has none. No lyric events either way: excluded.
   (b) Verse 1 is the first track holding lyric events. The melody track
   is the note track on whose onsets most of verse 1's syllables fall
   (ties: the earlier track). The melody is that track's top line: an
   onset is a melody note when the highest note sounding then starts then.
   (c) The line: from verse 1's first syllable to the first syllable, the
   third or later, whose text ends in punctuation (`,.;:!?`); the phrase
   is every melody note from the first syllable's onset to before the next
   syllable's onset, ending at that line-end syllable's note and the notes
   that continue its syllable. A rest (a gap between one melody note's end
   and the next onset) inside the line, or no line end within 20
   syllables: excluded. At least 90 % of the line's syllables must fall on
   melody onsets (`ALIGN_MIN`).
   (d) Durations in quarter notes, exact fractions of the MIDI file's
   ticks: inter-onset intervals, and the last note's own written length.
   Key, meter and tempo from the file's first key-signature, time-signature
   and tempo events. Pitch spelled from the key signature (sharps for a
   sharp or no key, flats for a flat key).
   (e) Conditions on the phrase (S15), each asserted on what was
   extracted: 5 to 20 notes; range at most 16 semitones (round 1's widest);
   at most 15 s at the file's tempo (round 1's longest, 13.3 s); no note
   shorter than 0.1 s (E-005 `report.py:19`, `TRANS_S`); every pitch within
   E2–C6 (squillo ADR 0007). A phrase failing one is excluded.
   (f) Words: verse 1's syllables of the line, joined where a syllable ends
   in a hyphen.
6. *Checks (S15), each on a case it must pass and one it must fail.*
   K1, the round trip: the phrase written in library notation and parsed by
   round 1's `parse` matches the melody track by round 1's `compare`, exact
   in pitch and in every inter-onset interval at scale 1.0; one pitch moved
   a semitone must fail on pitch, one duration doubled on rhythm, each
   input asserted to differ. K2, the words: the line's syllables shifted by
   one tick must fall below `ALIGN_MIN`. K3, the rights rule: rule 2's
   probe. K4, the people: each person's Mutopia year compared with the
   next person's Wikidata entry (names sorted), a wrong entry, must
   disagree wherever the two Mutopia years differ. K5, an independent
   transcription: where round 1 or 2 compared the same tune against
   Wikipedia or Mutopia, the extracted phrase is compared with that
   reference too and the outcome reported; it decides nothing, since an
   edition can differ from a later transcription. K6, a second path:
   where Mutopia's MIDI was used and its LilyPond source is one file, the
   source compiled with LilyPond 2.24.3 after `convert-ly` and the same
   rules re-run on it; whether the pitches, durations and words agree is
   reported, and decides nothing (tested first on Old 100th, 194, which is
   not eligible: all 125 notes agree).
   *Language*: the words' language is guessed from stop-words, reported
   only.

   *Second attempt.* The first `extract` run stopped at Aurore (1829),
   whose listed MIDI file the server does not have (404), after six
   retries. It had also shown four code defects, none in the rules: a
   blank `arranger = " "` (Lalo 587, Horsley 1366) and Schumann's
   `arranger = "opus 48, n° 7"` (309) were taken as naming an arranger
   with no death year, and excluded; a translator credited inside a
   `\markup` poet field (Horsley 1366: Catherine Winkworth, 1827–1878) was
   missed; and LilyPond 2.12 and later write MIDI lyrics without hyphens,
   so words split inside a word ("The tem pest"). Fixed in code: a header
   value names a person only if it holds a death-date pair or a
   capitalised word; a "tr." credit anywhere in the header is a
   translator; a listed file the server reports missing excludes its
   piece; and the words are joined where the LilyPond source puts `--`
   between the line's syllables (found in order in the source's tokens,
   a token's LilyPond duration stripped), MIDI's hyphens only where the
   source does not hold the line; a syllable whose own text ends in a
   hyphen ("Veux- tu") keeps it and joins. K6 compares the two paths'
   syllables, not the joined words (its first form compared one path's
   MIDI joins with the other's source joins). The whole of `extract` was then re-run
   from the start, so rule 3's order chose again from the beginning.

   *Time (S19).* The survey: 39 listing pages at 1 s, 71 s. `extract`: at
   most 20 pieces, two downloads each at 1 s and a compile of 2–10 s, so
   under 5 minutes; `measure` is timed on a sample before it runs.
7. *Measurability* (`measure`): round 1's `measure`, unchanged (E-005's
   synthetic voice, six voice types, per-note error sd 0 or 20 cents,
   vibrato off or on), on the new phrases.
8. *Count* (`report`): the library is round 2's 20 verified phrases plus
   round 3's; reported by genre, and under squillo's shipping rule.

```
uv run python round3.py survey     # 71 s: 39 listing pages, 1 s apart, cached -> results/r3-survey.json
uv run python round3.py screen     # -> results/r3-screen.json
uv run python round3.py extract    # about 5 min, cached reads -> results/r3-extract.json
uv run python round3.py measure    # 63 s on 18 processes (sample: 48 renderings in 18 s) -> results/r3-measure.json
uv run python round3.py report     # -> results/r3-summary.json, results/r3-library.json
```

Mutopia and Wikidata were read on 2026-10-01. Tools as round 1, and
LilyPond 2.24.3's `convert-ly`.

## Round 3 result

| # | Question | Result (conditions; uncertainty) |
| ---: | :--- | :--- |
| 1 | How many of Mutopia's voice pieces pass rule 2 on metadata alone? | **20 of 389** (one more, Adeste Fideles, sets a verified tune). A piece can fail several rules: licence not Public Domain 133, no lyricist named 212, a person with no death year 136, no edition year 224, rights (`us` and `life100`) 294. The rights rule's probe: must-pass 1 of 1, must-fail 4 of 4 |
| 2 | How many of those give a phrase that passes rules 4–6? | Rule 3's order tried **20** to take **10**, the number short of 30. The 10 excluded: no lyric events readable 4 (Oh! Boatman, Haste! and Armide: Mutopia's MIDI has none and the source did not compile; All My Heart This Night Rejoices and Es hat die Rose sich beklagt: none on either path), the listed MIDI not on the server 2 (Aurore, Fleur jetée), a rest inside the first line 2 (Gute Nacht!, Les Djinns), a first line of 4 notes 2 (Ich grolle nicht, Ein Ton). No phrase failed a range, length, short-note or pitch-range condition |
| 3 | Do the checks hold? | K1 (round trip): must-pass 12 of 12, must-fail on pitch 12 of 12 and on rhythm 12 of 12 (asserted). K2 (words): 12 of 12 aligned, at least 90 % of the line's syllables on melody onsets; shifted one tick, 12 of 12 fall below (asserted). K4 (people): 40 person entries; 36 agree with Wikidata; 2 disagree, both Robert Franz (Mutopia 1862, Wikidata 1892; the later year used, no verdict changed, neither piece taken); 2 unchecked (Hans Schmidt, Sapphische Ode's poet: no article under the name committed, so Mutopia's 1923 alone carries its `life100` pass; Catherine Winkworth, a header credit); the 27 must-fail pairings all disagree (asserted). K6 (the source compiled again): on 8 pieces where it ran, pitches, durations and syllables agree 8 of 8; it did not run on 4 (three whose phrase already came from the compiled source, and Les roses d'Ispahan, whose compile gave no MIDI). Recorded, not asserted: K1's and K2's `must_pass`, which are verdicts (a failure excludes the piece), and K6, which decides nothing. K5: no tried piece sets a tune round 1 or 2 compared, so it has no case |
| 4 | The 10 phrases | The Storm (Hullah, Procter; song), Après un rêve (Fauré, Bussine), Good King Wenceslas (Neale; listed as song by Mutopia's style), Einsamkeit (Schubert, Müller), Sapphische Ode (Brahms, Schmidt), The Spirit of God (Phelps; hymn), L'Esclave (Lalo, Gautier), Les matelots (Fauré, Gautier), Les roses d'Ispahan (Fauré, Leconte de Lisle), Le pays des rêves (Fauré, Silvestre). Editions dated 1844 to 1916. English 3, French 5, German 2. 7 to 18 notes, range 5 to 12 semitones, 4.0 to 13.5 s at the file's tempo, shortest note 0.25 s. All pass `us`, `life70` and `life100`; Mutopia's transcription of each is Public Domain |
| 5 | Can intent be inferred on them? (round 1's `measure`, unchanged; 240 renderings, 714 notes per condition) | No error, no vibrato: **714 of 714**. Vibrato: **99.7 %** (phrase bootstrap 95 % 99.0–100). 20 cents per-note error: **96.4 %** (94.5–97.9). Both: **92.0 %** (89.3–94.5). Round 1's phrases: 100, 97.6, 96.8 and 93.1 %. The one phrase under 100 % with vibrato alone is Les matelots, 95.2 % |
| 6 | The library now | **30**: 23 public-domain (13 verified against a transcription in rounds 1–2, 10 taken from their edition here) and 7 originals, under **13 genre labels**: classical 8, carol 5, hymn 4, children's 3, song 2, folk 1, and the 7 originals' one each. All 23 public-domain phrases pass squillo's shipping rule (`us` and `life100`) |

**Answer.** Yes: taking notes and words from a named public-domain
edition reaches `VISION.md` §9's 30 phrases with no listener and no
from-memory melody. Each new phrase is its edition's first line, with
the edition, its year and every contributor recorded. The route's cost
is balance. Mutopia's Public Domain voice pieces with a dated edition
and named, dead-by-1925 contributors are mostly 19th-century art songs.
So 7 of the 10 are French or German art songs (5 and 2; corrected by squillo R-12, iteration 60: 6 missed *Einsamkeit*, read by hand as German), 4 of them by Fauré, and
"classical" now holds 8 of the 30. The genre spread squillo wants (pop,
rock, jazz and the rest) still rests on one original each.

**Limits.**

- A phrase is the edition's notes as Mutopia's volunteers transcribed
  them. K6 shows the MIDI is the transcription's, not that the
  transcription is the print's. No tried piece had an independent
  transcription to compare with (K5).
- MIDI has no spelling of accidentals. Pitch names follow the key
  signature: sharps in sharp keys and C, flats in flat keys. So
  L'Esclave writes A♯4 (in D), and Le pays des rêves writes B4 and E4
  in G♭, where the print may write B♭, C♭ and F♭. The pitches are exact;
  the spelling may not be the edition's.
- Tempo is the MIDI file's. Four sources state no metronome mark (The
  Storm, Les matelots; Après un rêve and Einsamkeit give only a word),
  so their 60 quarter notes a minute is LilyPond's default, not the
  edition's. Seconds and the 0.1 s condition are at that tempo.
- Words are the transcription's syllables of verse 1. L'Esclave reads
  "peutêtre": its source writes `peut -- être`, a syllable break, so the
  hyphen of "peut-être" is not recoverable by rule. The words' language
  was guessed from stop-words for 8 of 10. Good King Wenceslas (English)
  and Einsamkeit (German) had too few stop-words and were read by hand.
- Genre is Mutopia's style, mapped by a fixed table. Good King Wenceslas
  is a carol that Mutopia lists as a song.
- One `life100` pass, Sapphische Ode's, rests on Mutopia's death year
  for Hans Schmidt (1923) alone.
- The rights rules are round 1's model, with round 1's limits.

## Fold 2 (squillo iteration 58): the 30 as item files

**Question.** Do the library's 30 phrases (round 1's 19 verified, round
2's Abide with Me, round 3's 10) load as squillo `exercises` items
(`format_version` 3, squillo ADR 0005), and would the build ship each
under ADR 0005's rights and licence rules (`build` BU-008)? Iteration 29
checked the first 19 the same way in `/tmp`, uncommitted; this fold is
committed so that squillo can cite it.

**Rules** (`fold.py`, its head, written before the first run).

- *Writing.* Round 1 and 2 items from `results/library.json`: the notes'
  decimal durations as exact fractions; each part's `edition` from the
  `source` text's `Words:` and `Tune:` clauses (`as the text` copies the
  words'); Abide with Me's `melody_checked_against` names round 2's
  reference, Mutopia 1241. Round 3 items from `results/r3-library.json`:
  a composer or arranger is a tune contributor, a poet a words
  contributor; both parts' `published_by` is the edition's year, and
  their `edition` the edition with its Mutopia transcription; the tempo
  is the MIDI file's rounded to a whole number, asserted within one
  microsecond per quarter note of it (|q − round(q)| ≤ q²/6·10⁷), since a
  MIDI tempo is whole microseconds; `melody_checked_against` says the
  notes were **taken from** the transcription, **not checked against an
  independent one**; the two languages read by hand (round 3's limits)
  are set; one word is corrected, each correction listed with its reason
  (L'Esclave's `peut -- être`, the syllable break round 3 could not join
  by rule); a source that states no metronome mark says so in `source`.
  `instructions` are squillo's own text, one template per genre noun.
  `phrase_id` is round 1's, or the title folded to ASCII kebab-case.
- *L, the loader.* A crude reading of `exercises` EX-001 to EX-011,
  first run on **every** file in squillo's `fixtures/exercises/` against
  the outcome its scenario states: 6 accepted (must pass), 22 refused,
  each under its stated requirement at its stated pointer, and the
  EX-004 pair refused both ways round (must fail); from squillo
  iteration 58, 7 accepted, with `edition-phrase.json` (below).
- *B, the rights rules.* `us` (every part published by 1930), `life100`
  (every contributor dead by 1925, an anonymous part published by 1925)
  and the licence (`CC-PDM-1.0`, or `LicenseRef-squillo-adr-0008` for an
  original), first run on squillo's BU-008 fixtures: 1 must pass, 5 must
  fail at their stated pointers.
- *R, round trips.* The written `amazing-grace` equals squillo's
  `fixtures/exercises/public-domain-phrase.json` member for member, and
  with one pitch moved does not (must fail); every item's notes equal its
  round's record exactly, pitch and duration.
- *C, conditions.* Round 3's rule 5(e) recomputed from each item: 5–20
  notes, range ≤ 16 semitones, ≤ 15 s, no note under 0.1 s, E2–C6; must
  fail: The Storm at a tenth of its tempo. Added after the first run,
  with the tempo bound's must-fail case (68.01 against 68); neither
  changed a rule or an output.

```
uv run python fold.py <squillo>   # under 1 s -> results/items/*.json, results/fold2.json
```

**Result** (`results/fold2.json`).

| # | Check | Result |
| ---: | :--- | :--- |
| 1 | L on squillo's fixtures | 30 of 30 cases as their scenarios state (6 must pass, 24 must fail, the EX-004 pair in both orders); 31 of 31 once squillo added `edition-phrase.json` (7 must pass), below |
| 2 | B on squillo's fixtures | 6 of 6 (1 must pass, 5 must fail at their pointers) |
| 3 | The 30, loaded together | **30 of 30 accepted**, no identifier shared |
| 4 | The 30 under the rights rules | **30 of 30 would ship**: 23 public-domain under `CC-PDM-1.0`, 7 originals under `LicenseRef-squillo-adr-0008` |
| 5 | Round trips | `amazing-grace` equals the squillo fixture (must-fail differs); 30 of 30 items' notes exact |
| 6 | Conditions | 30 of 30 within, and the must-fail case fails: 6 to 18 notes, range 4 to 14 semitones, 3.75 to 13.5 s, shortest note 0.1875 s, MIDI 55 to 77 (G3 to F5) |
| 7 | The library | 30: 23 public-domain, 7 original; 13 genres (classical 8, carol 5, hymn 4, children 3, song 2, and blues, country, folk, jazz, musical-theatre, pop, rock, soul 1 each); English 21, French 6, German 3. Four tempos are the transcription's default, the edition giving no mark (`apres-un-reve`, `einsamkeit`, `les-matelots`, `the-storm`); one word corrected (`l-esclave`) |

The fixture squillo takes for a phrase taken from its edition is
`results/items/the-spirit-of-god.json`, byte for byte. Once squillo
committed it as `fixtures/exercises/edition-phrase.json` (iteration 58,
EX-011's new scenario), it was added to L's expected outcomes as a must
pass and the fold re-run: L 31 of 31 (7 must pass), the fixture equal
to the item byte for byte (`R_edition_fixture_bytes_equal`), every other
value unchanged.

**Limits.** The loader and rules are this script's reading of squillo's
specs, checked on squillo's own fixtures, not an implementation. Round
3's limits stand: the notes are the transcription's, the spelling of
accidentals follows the key signature, and Sapphische Ode's `life100`
pass rests on Mutopia's year for its poet alone.

**Audit by squillo R-12 (iteration 60).** The rules and the results were
committed in the same second (`f5ea2be`, `fa22caf`), after a first run
that the *C* bullet discloses; `fold.py` had no guard against running
uncommitted, and of its check keys only L and B on the fixtures were
asserted (S15). Fixed in a rules commit before the re-run: `fold.py`
refuses to run uncommitted (checked: it refused before that commit),
asserts every check key, L and B on the 30, the notes' round trip and
C, and adds three must-fail cases that differ in the input the check
reads: the notes' comparison with one pitch moved
(`R_notes_must_fail`), the edition fixture against the item with one
byte changed (`R_edition_fixture_must_fail`), and C's own predicate on
The Storm slowed tenfold and with a note above C6
(`C_within_must_fail`). Re-run: every item byte for byte unchanged,
every earlier value unchanged, the three new keys true. Recorded and
asserted, but unable to show the run: `tempo_bound_must_fail` evaluates
the bound's formula on literals (68.01 against 68). The must-pass case
`edition-phrase.json` adds no evidence of its own: it is this fold's
`the-spirit-of-god.json`, already accepted in row 3. Not changed:
three items' tempos (The Spirit of God 112, L'Esclave 90, Sapphische
Ode 68) are the transcription's MIDI setting, not a printed mark, and
their `source` does not say so (squillo F-062).

## Needs a human

15 minutes, headphones, no microphone.

1. `cd experiments/E-004-phrase-library && uv run python listen.py`. This
   writes 25 WAVs to `data/listen/`: the 18 phrases whose melody round 1
   did not confirm (round 2 has since confirmed Abide with Me; a verdict on
   it still checks the check), and the 7 originals. Each opens with four clicks at its tempo.
2. Play each once or twice. In `results/listen.csv`, set `verdict`:
   - For a public-domain phrase: `right`, `wrong` (with `first_wrong_note`,
     counting from 1) or `unknown`, if you do not know the tune.
   - For an original: `new`, or `familiar`, with the song it recalls in
     `reminds_me_of`.
3. Commit `results/listen.csv`. The WAVs are ignored by git; never commit a
   recording of anyone.

A `right` confirms only the familiar form. It is not proof that the cited
edition matches, and round 2 checks that.
