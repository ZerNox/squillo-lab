# E-007 — Cold-start test: can a fresh agent name what to build first and write its failing test?

**Status:** running (test 1 of 2 run: not passed) · **Serves:** `squillo/VISION.md` §9 (the first slice,
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
