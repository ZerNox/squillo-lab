<!-- E-007 test 2 (squillo iteration 97): the subagent's report, saved
unchanged from its reply. Its write to /tmp/e007/report.md was refused by
the harness ("a subagent must return its report as text"), as in test 1. -->

## What to build first

The framing in the `signal` crate: squillo `signal` requirement SG-002, *Frames*. The first failing test is its scenario *One second gives 125 frames*:
- Deliver `fixtures/signal/sine-220hz.wav` (48 000 `f32` samples) to `signal` in 375 consecutive blocks of 128 samples.
- Exactly 125 frames must result, frame 0 to frame 124.
- Frame 124 must hold samples 47 616 to 47 999 and start at 992 ms.

This is step 1 of the build order, which builds the pure Rust crates first, in *Input from* order. After it come the rest of `signal` (SG-003, SG-006, SG-005, SG-004, SG-007, SG-008, SG-001), then `metrics`, and so on.

## Where I read it

- **`squillo/PLAN.md`:**
  - §10, Stage E row: "At R-19: … 91: ADR 0023, the pure crates first, the first test `signal` SG-002's *One second gives 125 frames*".
  - §1 and §11: what the cold-start test is.
- **`squillo/docs/decisions/0023-the-build-order.md`:**
  - *Decision outcome*, steps 1 to 4: the hash from the manifest row, the WAV layout, 375 blocks of 128, the assertions.
  - The step table: step 1 is `signal`, with SG-002 first.
  - *The first test's frame*:
    - Rust, run by `cargo test`, natively.
    - One crate, named `signal`.
    - The test lives in that crate, uses its public interface, and its name holds `sg_002`.
    - The interface's shape.
    - Which failure counts.
    - Any SHA-256 implementation will do.
    - The hash is read from the manifest row when the test runs.
    - Names and types are free.
- **`squillo/openspec/specs/signal/spec.md`:**
  - SG-001: 128-sample `f32` blocks, in file order.
  - SG-002: 384-sample frames, frame *i* starting at `8i` ms, and the scenario.
- **`squillo/fixtures/MANIFEST.md`:**
  - *Signal fixtures*: the byte layout, with offsets 12, 38, 50 and 58.
  - The row for `fixtures/signal/sine-220hz.wav`, which holds its SHA-256.
- **Background:**
  - `squillo/docs/questions/Q-043.md` and `Q-045.md`: the rankings behind the ADR.
  - `squillo/docs/process/findings.md`, F-077 to F-086: test 1's guesses, now settled.
- **`squillo-lab/README.md`:**
  - *Tooling*: Rust stable; the `.gitignore` covers `experiments/*/test*/target/`.
  - *Where squillo is*.
  - Checklist items C5, C7 and C10.
  - *A test that measures nothing*: only C5, C7 and C10 bind, inside the test; it needs no guard, README or results file.

## The test (files, the command that runs it)

All files are in `/tmp/e007/squillo-lab/experiments/E-007-cold-start/test2/`.

- **`Cargo.toml`:**
  - The package is named `signal`, because ADR 0023 names the crate for its domain.
  - Its only dependency is the dev-dependency `sha2 = "=0.11.0"`.
- **`src/lib.rs`:** the interface, with nothing behind it.
  - It has `Stream::new()`, `push_block(&[f32; 128])` and `frames() -> &[Frame]`, where `Frame { index, first_sample, last_sample, start_ms }`.
  - There is no end-of-stream call.
  - The names and types are my free choice under ADR 0023 (F-079).
  - `push_block` does nothing, so `frames()` stays empty.
- **`tests/sg_002.rs`:** the test `sg_002_one_second_gives_125_frames`. It runs in this order:
  1. Finds squillo: `$SQUILLO_ROOT`, or by default `../squillo` from the lab's root.
  2. Reads the fixture's row in `MANIFEST.md` when the test runs.
  3. Runs three checks of its inputs before the scenario. Each runs on an input it must pass and on one it must fail (C10):
     - **Row check:** exactly one manifest row names the fixture. The must-fail input is the manifest with that row written twice, which changes the row count.
     - **SHA-256 check:** the file's digest matches the row. The must-fail input is the file with the last byte's lowest bit flipped, which changes the bytes being hashed.
     - **Layout check:** every field the manifest's *Signal fixtures* paragraph states. Offsets, byte rate, block align and data length are computed from the stated sizes, not typed in again (C5). The must-fail input is the file with format tag 3 changed to 1, which is the field the check compares with 3.
  4. Decodes the 48 000 little-endian `f32` samples and delivers them in 375 blocks of 128.
  5. Asserts the scenario's THEN clause (125 frames, numbered 0 to 124) and its AND clause (frame 124 holds samples 47 616 to 47 999 and starts at 992 ms).
- **`Cargo.lock`:** generated. `target/` is build output, covered by the lab's `.gitignore`.

Every value in the test traces to a line of the repositories:

| Value | Source |
| :--- | :--- |
| The path `fixtures/signal/sine-220hz.wav` | SG-002's scenario |
| 128 | SG-001 |
| 375 | ADR 0023, step 3 |
| 125, 124, 47 616, 47 999, 992 | SG-002's scenario |
| 18, 3, 1, 48 000, 32, 0, 4, 48 000; the 4-byte chunk name and length; `RIFF` and `WAVE` | `MANIFEST.md`, *Signal fixtures* |
| The digest | Read from the `MANIFEST.md` row when the test runs |
| The two must-fail edits | The experiment's own choice (C10), recorded here and in the test's header comment |

Command, run from that folder. `--offline` is there only because `sha2` is already in the local cargo cache:

    cd /tmp/e007/squillo-lab/experiments/E-007-cold-start/test2 && cargo test --offline

Why it fails:
- The test compiles.
- All three input checks pass, and their must-fail cases fail as they should. Those checks run before the scenario, so reaching the scenario assertion at line 192 shows they all passed.
- It then fails on the scenario's own THEN clause, because nothing frames the stream yet: `frames()` returns 0 frames, not 125.

This is the failure ADR 0023 (F-080) says counts.

As a sanity check, I added a five-line framing to a temporary copy inside `E-007-cold-start/`. The same test passed there, and I deleted the copy afterwards.

## Its output (the failing run, verbatim, trimmed to the relevant lines)

```
   Compiling signal v0.0.0 (/tmp/e007/squillo-lab/experiments/E-007-cold-start/test2)
    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.14s
     Running tests/sg_002.rs (target/debug/deps/sg_002-f8d7a0162623b2d1)
running 1 test
test sg_002_one_second_gives_125_frames ... FAILED
---- sg_002_one_second_gives_125_frames stdout ----
thread 'sg_002_one_second_gives_125_frames' (1516323) panicked at tests/sg_002.rs:192:5:
assertion `left == right` failed: THEN exactly 125 frames result, frame 0 to frame 124
  left: 0
 right: 125
test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.01s
error: test failed, to rerun pass `--test sg_002`
```

## Guesses (numbered; or "None")

1. **How the test is told where squillo is, and what that setting is called.**
   - *Needed:* a way for the test to receive squillo's root folder.
   - *Looked:* `squillo-lab/README.md`, *Tooling*, *Where squillo is*. It says "takes squillo's root as an argument or environment variable", but names no variable and does not say the choice is free. ADR 0023 says nothing on it. The earlier lab script that does this (E-002's `r7_inputs.py`) takes a command-line argument, which `cargo test` does not pass naturally.
   - *Chose:* an environment variable, named `SQUILLO_ROOT`.
2. **How to find "the repository's root" for the default path.**
   - *Needed:* the lab's root folder, to resolve the default `../squillo` from it.
   - *Looked:* the same paragraph, which says "resolved from the repository's root, never from the experiment's own folder". Neither snapshot is a git repository (there is no `.git`), so git cannot report the root, and the README does not say how else to find it.
   - *Chose:* three folders up from the crate, `CARGO_MANIFEST_DIR/../../..`. This still starts from the experiment's own folder, which the README's wording may not intend.
3. **Where to record the must-fail inputs.**
   - *Needed:* a place to record them. C10 says the must-fail input is "recorded in its README".
   - *Looked:*
     - `E-007-cold-start/` holds only the empty `test2/`.
     - `INDEX.md` links an E-007 `README.md`, and R-19 cites "a note for test 2 in E-007's README (`34500bb`)", but neither file is in the snapshot.
     - *A test that measures nothing* says the test needs no README of its own, and the iteration writes the experiment's README.
     - I did not write that README in the iteration's place.
   - *Chose:* recorded them, with the field or term each one changes, in the header comment of `tests/sg_002.rs` and in this report. Which inputs to use is free under C10; only where to record them was a guess.
4. **Whether to require exactly one manifest row for the fixture.**
   - *Needed:* what to do if the path matched no row or more than one. ADR 0023 says "its row", in the singular.
   - *Looked:* ADR 0023 step 1 and F-082; `MANIFEST.md`, where the path is the bare first column; and E-002's `manifest_hashes`, which silently keeps the last match.
   - *Chose:* require exactly one row. That makes it a check of the test's input, so under C10 it has a case it must pass and a case it must fail (the row duplicated).

Not guesses:
- **Stated free:**
  - The names and types in the interface.
  - Integration test rather than unit test.
  - The file names.
  - The package at `test2/` with no workspace.
  - Edition 2021.
  - `sha2 =0.11.0`.
  - Reading the WAV by hand.
- **Settled:**
  - Rust, `cargo test`, natively.
  - The crate name `signal`.
  - The test name holding `sg_002`.
  - Which failure counts.
  - The hash read from the manifest row.
  - The offsets, which the manifest states.
  - Which checklist items bind the test.
- **Not my decision:** I committed nothing. The snapshot has no git, and C14 binds the iteration that runs this session, not the test.
