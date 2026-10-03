# E-007 — Cold-start test: can a fresh agent name what to build first and write its failing test?

**Status:** running (tests 1 to 3 run: none passed) · **Serves:** `squillo/VISION.md` §9 (the first slice,
specified end to end so it can be built) · **For:** squillo `PLAN.md` §1
(Phase 0's end), §10 Stage E (the cold-start test), §11 (two passes in
independent fresh sessions); review R-18 §8, iteration 94

## Question

`PLAN.md` §1: Phase 0 ends when a fresh agent, given squillo and
squillo-lab, "can name what to build first and write the first failing test
without asking a question". Stage E (rev 37) makes that a lab iteration:
the session names what to build first, writes that test in squillo-lab,
and logs as a finding each point it had to guess. It passes when it logs
none. This is test 1 of the two §11 needs.

## Rules (committed before the run)

1. **Fresh.** The test is taken by a subagent started in the foreground
   (`run_in_background: false`, squillo S20), which has none of the
   iteration's context. Its whole prompt is [`run/prompt.md`](run/prompt.md),
   verbatim, nothing added.
2. **Only the repositories.** It works on a snapshot made by
   [`run/snapshot.sh`](run/snapshot.sh): squillo at `iteration-93`
   (`c7405e1`) and squillo-lab at `32d4403`, the commit before this
   experiment, as `git archive` gives them, with no `.git` and no E-007
   folder. It cannot read these rules.
3. **What counts.** The test *fails* when one command runs it and it
   reports failure because the product code it tests does not exist; a
   test that does not run, or fails for another reason (a wrong path, a
   broken fixture read), is not the failing test. The subagent's own
   *Guesses* section is the log.
4. **The guesses I add.** After the run, every concrete value and choice in
   its test (each number, path, hash, file layout, interface and tool) is
   traced to a line of the snapshot. One that traces to none, and is not
   in its *Guesses*, is an unlogged guess, recorded in the result and
   logged like the others.
5. **Pass.** The test passes when the subagent's log and rule 4 together
   hold no guess, and the failing test is as rule 3 says. Every guess is
   logged in squillo `docs/process/findings.md` as an `F-nnn`, whatever
   its size; whether it needs a spec change is the finding's, not this
   test's.
6. **Recorded, not judged.** Whether it names what squillo ADR 0023
   names (SG-002's *One second gives 125 frames*, on
   `fixtures/signal/sine-220hz.wav`) is recorded. A different first item
   read from the repositories is not a guess; one the repositories do not
   support is.
7. **Re-run outside the snapshot.** Its test is copied here and run once
   more from this folder against the real repositories, to show the same
   failure.

Checklist items applied (squillo-lab `README.md`): C14 (rules committed
before the run). No number is measured, so C1 to C13 and C15 to C19 do not
apply; there is no results JSON.

## Result (test 1, squillo iteration 94)

**Not passed: the subagent logged 10 guesses; tracing its test (rule 4)
added none.** It named what ADR 0023 names, and its test fails as rule 3
asks.

*Run.* Snapshot by `run/snapshot.sh c7405e1 32d4403`; subagent
(general-purpose, foreground, fresh context) given `run/prompt.md`
verbatim (sha256 `f6470dd7…a274f` of the file as committed); 20 tool
uses, 180 s. Its write to `/tmp/e007/report.md` was refused by the
harness (a subagent may not write report files), so its reply's report
text is saved unchanged as [`results/report.md`](results/report.md). This
is the one departure from the prompt; nothing else was asked of it.

*What to build first* (rule 6): `signal` SG-002's scenario *One second
gives 125 frames* on `fixtures/signal/sine-220hz.wav`, its hash checked
against its `MANIFEST.md` row, 375 blocks of 128, then ADR 0023's order.
It read it in ADR 0023, `docs/architecture.md` §2 and §4, the `signal`
spec, the manifest, `PLAN.md` §1 and §10, and the lab's `README.md`. Same
as ADR 0023.

*The failing test* (rule 3): [`test1/`](test1/), a Rust package
`signal` with an empty stand-in library and one integration test; `cd
test1 && cargo test`. Every precondition passes (the hash read from the
manifest row, the layout field by field, 48 000 samples, 375 blocks, the
scenario's numbers derived from SG-002's definition), then
`assertion left == right failed: number of frames, left: 0, right: 125`
at `tests/sg_002_one_second_gives_125_frames.rs:170`. Re-run here against
the real repositories (rule 7): the same failure, exit 101. With a
throwaway framing (frames appended once 384 samples have arrived) in a
`/tmp` copy, it passes, 1 of 1, so it fails only for want of the product
code; the copy was deleted.

*Rule 4 trace.* Every constant in the test traced to a line of the
snapshot: the layout's 13 values to `fixtures/MANIFEST.md` *Signal
fixtures* (lines 84–90), 384, 8, 125, 47 616, 47 999 and 992 to SG-002,
128 to SG-001, 375 to ADR 0023 step 3, the "abc" vector to FIPS 180-2,
edition 2021 and the `=` pin to E-001's and E-002's `Cargo.toml`. What
traced to none is among its logged guesses (the interface's types, the
path, the crate version, the offsets, the must-fail inputs). **No
unlogged guess.**

*The guesses*, in three kinds (the iteration's reading, not the
subagent's):

| # | Guess (`results/report.md`) | Kind | squillo finding |
| ---: | :--- | :--- | :--- |
| 1 | Rust and `cargo test`, an integration test | the engine's test harness, implied by ADR 0023 ("natively") and architecture §4, not stated | F-077 |
| 2 | One package named `signal`, its file layout | the engine's crates, named by domain but not by package | F-078 |
| 3 | `Signal::new`, `push(&[f32; 128])`, `frames()`, `Frame`'s fields and types | the engine's interface to its tests: no ADR states it | F-079 |
| 4 | Failing means compiling and failing an assertion, with an empty stand-in | ADR 0023's "it fails" leaves a compile error open | F-080 |
| 5 | `sha2 =0.11.0` for the hash | a tool the first test needs, unnamed | F-081 |
| 6 | The expected hash parsed from the manifest row, not the ADR's copy | ADR 0023 step 1 states both | F-082 |
| 7 | squillo at `../../../../squillo`, a `SQUILLO` override | where a lab test finds squillo's fixtures | F-083 |
| 8 | C5, C7 and C10 only; no guard, README or results | the lab checklist's scope for a cold-start test | F-084 |
| 9 | Byte offsets 12, 38, 50, 58 | derivable from the manifest's order and sizes; logged by the subagent, so logged | F-085 |
| 10 | Must-fail inputs: one bit of sample 1000; format tag 1 | C10 requires them, does not choose them | F-086 |

Guesses 1 to 4 are what an implementer decides before any other test;
5 to 7 and 9 are the test's mechanics; 8 and 10 are the lab's process
applied to a test that measures nothing. Which need squillo to state
something, and which are an implementer's free choice that squillo should
say is free, is the fold's to decide (R-19 plans it; `PLAN.md` §10:
"logs as a finding each point it had to guess").

*Limits.* One session, one model (the iteration's own, Opus 5.5), one
prompt. A guess list is a model's self-report: another session may
notice more or fewer points, so a second test (§11) is needed whatever
this one found. The snapshot left out `.git`, so history was not
readable; nothing in the task needs it.

## Review note (squillo R-19, iteration 95)

For test 2 (squillo R-19 §8, iteration 97): squillo `PLAN.md` rev 40
defines a guess as a point the repositories neither settle nor state as
the implementer's free choice, and keeps rule 4's trace of every value
in the test. R-19 fixed F-083 to F-086 (this repository's `README.md`
`a7d1417`; squillo's `fixtures/MANIFEST.md`, the offsets); F-077 to
F-082 are folded into squillo ADR 0023 in iteration 96, before test 2's
snapshot is made.

## Rules for test 2 (squillo iteration 97, committed before the run)

Test 2 is test 1's rules 1 to 7, unchanged, with these differences only
(squillo R-19 §8: "the same prompt and rules as test 1, rule 4's trace
included"):

- **Snapshot.** `run/snapshot.sh a0ffea5 34500bb test2`: squillo at
  `iteration-96` (`a0ffea5`, after test 1's fold into ADR 0023) and this
  repository at `34500bb`, the commit before test 2's rules. The E-007
  folder is still removed. `INDEX.md`'s E-007 row is not: squillo's
  `STATUS.md` and `docs/process/findings.md` name test 1 and its guesses
  at that revision anyway, and hiding one copy of a fact the other
  repository states would hide nothing. The script's old check that the
  INDEX names no E-007 is replaced by a check that the folder is gone.
- **Prompt.** [`run/prompt-test2.md`](run/prompt-test2.md): test 1's
  prompt with `test1/` replaced by `test2/` in step 2, nothing else.
- **Pass** (test 1's rule 5, as squillo `PLAN.md` rev 40 reads it): a
  logged point is a guess unless a line of the snapshot settles it or
  states it as the implementer's free choice. The iteration reads each
  logged point against the snapshot and records which it is, with the
  line; a point that one of them answers is not counted, and is recorded
  as the subagent's over-logging. Every value in the test is still traced
  (rule 4).
- **Fresh session.** A new subagent, started in the foreground with no
  context but the prompt; not the session that ran test 1, and not one
  that has seen this README.

Checklist items applied (squillo-lab `README.md`): C14 (these rules
committed before the run), and *A test that measures nothing* for what
binds the subagent's test.

## Result (test 2, squillo iteration 97)

**Not passed: the subagent logged 4 points; read against the snapshot,
3 are guesses and 1 is settled; tracing its test (rule 4) added none.**
It named what ADR 0023 names, and its test fails as rule 3 and ADR 0023
(*Which failure counts*) ask. Test 1's ten guesses did not recur.

*Run.* Snapshot by `run/snapshot.sh a0ffea5 34500bb test2`; subagent
(general-purpose, foreground, fresh context, the iteration's own model,
Opus 5.5) given `run/prompt-test2.md` verbatim (sha256 `b804231c…58a18`
of the file as committed in `0afe183`); 21 tool uses, 263 s. Its write
to `/tmp/e007/report.md` was refused by the harness again, as in test 1,
so its reply's report text is saved unchanged as
[`results/report-test2.md`](results/report-test2.md).

*What to build first* (rule 6): `signal` SG-002's *One second gives 125
frames* on `fixtures/signal/sine-220hz.wav`, then ADR 0023's order. It
read it in ADR 0023 (*Decision outcome*, the step table, *The first
test's frame*), `PLAN.md` §10, the `signal` spec, the manifest and the
lab's `README.md`. Same as ADR 0023.

*The failing test* (rule 3): [`test2/`](test2/), a Rust package
`signal` whose `src/lib.rs` has the interface ADR 0023 shapes with
nothing behind it (`Stream::new`, `push_block(&[f32; 128])`,
`frames() -> &[Frame]`), and one integration test,
`tests/sg_002.rs`, `sg_002_one_second_gives_125_frames`; `cd test2 &&
cargo test --offline`. Three checks of its inputs run first, each on a
must-pass and a must-fail input (C10): one manifest row names the
fixture (must-fail: the row written twice), the SHA-256 against that row
(must-fail: the last byte's lowest bit flipped), and the layout from the
manifest's stated sizes (must-fail: format tag 1). Then `assertion left
== right failed: THEN exactly 125 frames result, frame 0 to frame 124,
left: 0, right: 125` at `tests/sg_002.rs:192`. Re-run here against the
real repositories (rule 7): the same failure, exit 101. With a throwaway
framing (a frame appended once 384 more samples have arrived) in a
`/tmp` copy, it passes, 1 of 1, so it fails only for want of the product
code; the copy was deleted.

*Rule 4 trace.* Every constant in the test traces to a line of the
snapshot: the fixture's path and 125, 124, 47 616, 47 999 and 992 to
SG-002's scenario (`openspec/specs/signal/spec.md` lines 19 to 23); 128
to SG-001 (line 9); the layout's values (18, 3, 1, 48 000, 32, 0, 4,
48 000, the 4-byte name and length, `RIFF`, `WAVE`, little-endian) to
`fixtures/MANIFEST.md` *Signal fixtures* (lines 84 to 94), the offsets
computed from them; the digest read from the manifest row at run time
(ADR 0023, F-082); `sha2 =0.11.0`, edition 2021, the interface's names
and `u64`, the integration test and its file name stated free by ADR
0023 (*The first test's frame*); the must-fail edits the experiment's
own choice (lab `README.md` C10, lines 81 to 82). What traces to none is
among its logged points (`SQUILLO_ROOT`, the `../../..` anchor, the
one-row check). **No unlogged guess.**

*The logged points*, read against the snapshot (test 2's *Pass* rule):

| # | Point (`results/report-test2.md`) | Reading | squillo finding |
| ---: | :--- | :--- | :--- |
| 1 | An environment variable, named `SQUILLO_ROOT` | **Guess.** *Where squillo is* (lab `README.md` lines 259 to 266) allows "an argument or environment variable" but names neither and does not say the name is free; `cargo test` passes no argument to a test naturally | F-087 |
| 2 | The lab's root found as `CARGO_MANIFEST_DIR/../../..` | **Guess.** The same lines say the default is "resolved from the repository's root, never from the experiment's own folder"; a compiled test with no `.git` has no other anchor than its own folder or the working directory, and the README says neither. The rule as written cannot be met literally by a cargo test | F-088 |
| 3 | Where the must-fail inputs are recorded | **Settled, over-logged.** C10 (lines 81 to 82) records them in the experiment's README, and *A test that measures nothing* (lines 143 to 146) gives that README to the iteration, not the test; the subagent reported them, which is all that falls to it | none |
| 4 | Exactly one manifest row names the fixture, checked with a must-fail | **Guess.** ADR 0023 step 1 says "its row", and no line says a fixture has one row; the guard workflow checks every row's hash and that every file is listed, not that a path is listed once | F-089 |

Guesses 1 and 2 are one paragraph of this repository's `README.md`
written for a script (E-002's `r7_inputs.py`) and read by a compiled
test; 4 is the manifest's. None concerns what a requirement says, and
none is about the engine: the interface, harness, crate, failure and
hash that test 1 had to guess were all read as settled or free.

*Limits.* One session, one model (Opus 5.5, as test 1), one prompt; a
guess list is a self-report, checked by the trace and by reading each
point against the snapshot. The snapshot's squillo names test 1's
guesses (`docs/process/findings.md`, F-077 to F-086), which the subagent
read as background; a real implementer would read them too. The
snapshot has no `.git` (guess 2 depends on it: in a clone, git could
name the root).

*Fold* (squillo iteration 98, Q-046 option A). F-087 and F-088 are
settled in this repository's `README.md`, *Where squillo is*: the
variable is `SQUILLO_ROOT`, an argument still allowed for a script, and
the lab's root is found from the code's own path by a stated depth,
three folders up from a crate such as `test2/`. F-089 is settled in
squillo's `fixtures/MANIFEST.md` (*Path*: one row per fixture) and ADR
0023 step 1 (none or several fail the fixture check). Test 2's own
choices match all three; test 3 (squillo iteration 99) reads them.

## Rules for test 3 (squillo iteration 99, committed before the run)

Test 3 is test 2's rules, unchanged, with these differences only (squillo
R-19 §8, row 99: "If 98 was a fold: test 3"):

- **Snapshot.** `run/snapshot.sh 5da7e4e 58c9aca test3`: squillo at
  `iteration-98` (`5da7e4e`, after test 2's fold into ADR 0023 and the
  manifest) and this repository at `58c9aca` (its *Where squillo is*
  fold), the commit before test 3's rules. The E-007 folder is removed,
  `INDEX.md`'s E-007 row stays, as for test 2.
- **Prompt.** [`run/prompt-test3.md`](run/prompt-test3.md): test 2's
  prompt with `test2/` replaced by `test3/` in step 2, nothing else.
- **Fresh session.** A new subagent, started in the foreground with no
  context but the prompt; not the session that ran test 1 or test 2, and
  not one that has seen this README.
- **What a pass counts for.** If test 3 passes (no guess after reading
  each logged point against the snapshot and tracing every value, test
  2's *Pass* rule), it is the first of the two passes squillo `PLAN.md`
  §11 needs; test 1 and test 2 did not pass, so they count for nothing
  there.

Checklist items applied (squillo-lab `README.md`): C14 (these rules
committed before the run), and *A test that measures nothing* for what
binds the subagent's test.

## Result (test 3, squillo iteration 99)

**Not passed: the subagent logged 2 points; read against the snapshot,
1 is a guess and 1 is settled; tracing its test (rule 4) added none.**
It named what ADR 0023 names, and its test fails as rule 3 and ADR 0023
(*Which failure counts*) ask. None of test 1's ten or test 2's three
guesses recurred. Since it did not pass, §11's two passes are still
both to come.

*Run.* Snapshot by `run/snapshot.sh 5da7e4e 58c9aca test3`, the squillo
part checked byte for byte against `git archive 5da7e4e` after the run
(unchanged); subagent (general-purpose, foreground, fresh context, the
iteration's own model, Opus 5.5) given `run/prompt-test3.md` verbatim
(sha256 `8b78ef0e…d9b1e9d` of the file as committed in `b06153a`); 13
tool uses, 196 s. This time the harness let it write
`/tmp/e007/report.md`, saved unchanged as
[`results/report-test3.md`](results/report-test3.md).

*What to build first* (rule 6): `signal` SG-002's *One second gives 125
frames* on `fixtures/signal/sine-220hz.wav`, then ADR 0023's order. It
read it in ADR 0023 (*Decision outcome*, *The first failing test*, the
order table, *The first test's frame*), `PLAN.md` §1, §3 and §10,
`docs/architecture.md` §4, the `signal` spec, the manifest and the lab's
`README.md` (*Tooling*, *Where squillo is*, *A test that measures
nothing*). Same as ADR 0023.

*The failing test* (rule 3): [`test3/`](test3/), a Rust package
`signal` whose `src/lib.rs` has ADR 0023's interface shape with nothing
behind it (`Stream::new`, `push_block(&[f32; 128])`, `frames() ->
Vec<Frame>`, `Frame`'s index, first and last sample and start in ms as
`u64`), and one integration test, `tests/sg_002.rs`,
`sg_002_one_second_gives_125_frames`; `cd test3 && cargo test`. Checks
of its checks run first (C10): the fixture check on the manifest as
committed (pass), with the row removed and written twice (fail), and
with one bit of sample 0 flipped (fail); the layout check on the file
(pass), with format tag 1 and one sample short (fail); the block split
on 48 000 samples (pass) and 47 999 (fail). The layout's offsets are
computed from the manifest's sizes, and a compile-time assertion holds
them to the manifest's stated 192 058, 192 050, 12, 38, 50 and 58. Then
`assertion left == right failed: SG-002 THEN: exactly 125 frames, left:
0, right: 125` at `tests/sg_002.rs:259`. Re-run here against the real
repositories (rule 7, `cargo test --offline`): the same failure, exit
101. With a throwaway framing (frame *i* holding samples 384*i* to
384*i* + 383 and starting at 8*i* ms, frames counted from the samples
pushed) in a `/tmp` copy, it passes, 1 of 1, so it fails only for want
of the product code; the copy was deleted.

*Rule 4 trace.* Every constant in the test traces to a line of the
snapshot: the fixture's path, 48 000, 125, 124, 47 616, 47 999 and 992
to SG-002 and its scenario (`openspec/specs/signal/spec.md` lines 16 to
23); 128 to SG-001; the manifest's path and the one-row rule to ADR 0023
step 1 and *A fixture's one row*; the layout's values (192 058, 192 050,
`RIFF`, `WAVE`, 18, 3, 1, 48 000, 192 000, 4, 32, 0, the `fact` chunk's
4 and 48 000, the `data` chunk's 192 000, 4-byte names and lengths, no
padding, little-endian, the four offsets) to `fixtures/MANIFEST.md`
*Signal fixtures* (lines 87 to 97); the digest read from the manifest
row at run time, its first column read as the path and its second as
the hash (ADR 0023, F-082, F-089); the depth 3 and `../squillo` to the
lab's *Where squillo is*; `sha2 = "0.11"`, edition 2021, the
interface's names, `u64`, `Vec` returned, an integration test and its
file name stated free by ADR 0023 (*The first test's frame*); the
must-fail edits the experiment's own choice (C10). What traces to none
is its logged point 1. **No unlogged guess.**

*The logged points*, read against the snapshot (test 2's *Pass* rule):

| # | Point (`results/report-test3.md`) | Reading | squillo finding |
| ---: | :--- | :--- | :--- |
| 1 | What a relative `SQUILLO_ROOT` is relative to; it used the value as given, so the working directory | **Guess.** *Where squillo is* (lab `README.md` lines 259 to 274) names the variable and says "the root is found from the code's own path, never from git ... or the working directory", but does not say whether that covers the variable's value; a relative value used as given resolves against the working directory, which the same sentence rules out for the default. No line settles it or says it is free. It changes nothing this run did (the default and an absolute value) | F-090 |
| 2 | Where its must-fail inputs are recorded | **Settled, over-logged**, as test 2's point 3: C10 (lines 81 to 82) records them in the experiment's README, and *A test that measures nothing* (lines 143 to 146) gives that README to the iteration that runs the session; the subagent recorded them in comments and its report, which is all that falls to it. It noted the snapshot has no E-007 README, which the snapshot removes by design (rule 2) | none |

The one guess is again in the lab's *Where squillo is*, at a case (a
relative variable) the iteration-98 fold did not cover; none concerns
a requirement or the engine. Twice now a session has logged where its
must-fail inputs go, though the lines settle it; that is recorded, not
counted.

*Limits.* One session, one model (Opus 5.5, as tests 1 and 2), one
prompt; a guess list is a self-report, checked by the trace and by
reading each point against the snapshot. The snapshot's squillo names
tests 1 and 2 and their guesses (findings F-077 to F-089, ADR 0023's
fold notes), which the subagent cited as background.

## Review note (squillo R-20, iteration 100)

For test 4 (squillo R-20 §8, iteration 101): R-20 fixed F-090 in this
repository's `README.md`, *Where squillo is*: the rule against the
working directory is for the default only; a relative value of
`SQUILLO_ROOT` or a script's argument is read as given, against the
working directory of the process that reads it, and an experiment that
must not depend on where it runs gives an absolute value. R-20 re-ran
test 3's crate against the repositories (`cargo test`, its target in
`/tmp`): it fails on SG-002's THEN, 0 frames of 125, exit 101, as
recorded. Test 4 runs on a new snapshot after R-20, with test 3's
prompt and rules and `test4/` for `test3/`; it is the first of the two
passes `PLAN.md` §11 needs if it logs no guess the snapshot does not
settle or state as free.
