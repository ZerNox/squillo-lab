# E-007 — Cold-start test: can a fresh agent name what to build first and write its failing test?

**Status:** running · **Serves:** `squillo/VISION.md` §9 (the first slice,
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

## Result

Not yet run.
