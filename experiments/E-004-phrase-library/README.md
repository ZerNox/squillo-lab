# E-004 — A publishable phrase library

**Status:** needs-human (round 1 automated evidence in; a listening check remains) · **Serves:** VISION §7 (the guided library), §9 (first slice), §12.5

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

## Needs a human

15 minutes, headphones, no microphone.

1. `cd experiments/E-004-phrase-library && uv run python listen.py`. This
   writes 25 WAVs to `data/listen/`: the 18 phrases whose melody is not yet
   confirmed, and the 7 originals. Each opens with four clicks at its tempo.
2. Play each once or twice. In `results/listen.csv`, set `verdict`:
   - For a public-domain phrase: `right`, `wrong` (with `first_wrong_note`,
     counting from 1) or `unknown`, if you do not know the tune.
   - For an original: `new`, or `familiar`, with the song it recalls in
     `reminds_me_of`.
3. Commit `results/listen.csv`. The WAVs are ignored by git; never commit a
   recording of anyone.

A `right` confirms only the familiar form. It is not proof that the cited
edition matches, and round 2 checks that.
