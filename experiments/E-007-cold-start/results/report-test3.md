## What to build first

The `signal` crate's framing: squillo `signal` requirement SG-002 (*Frames*, 384-sample / 8 ms frames), scenario *One second gives 125 frames*. The first test reads `fixtures/signal/sine-220hz.wav` and checks its SHA-256 against its one row in `fixtures/MANIFEST.md`. It then checks the WAV layout and takes the 48 000 `f32` samples. It sends them to `signal` in 375 blocks of 128 samples, and asserts exactly 125 frames, frame 0 to frame 124, with frame 124 holding samples 47 616 to 47 999 and starting at 992 ms. This is step 1 of the build order, which goes `signal`, `metrics`, `exercises`, `analyzers`, `synthesis`, `coach`, then the WASM boundary, `capture`, `runner`, `ui`, and finally `build` with `security`.

## Where I read it

- `squillo/docs/decisions/0023-the-build-order.md`:
  - *Decision outcome*, *The first failing test*, steps 1 to 4, and the order table.
  - *The first test's frame*: Rust under native `cargo test`; a library crate named `signal`; the test in that crate, using only its public interface, with `sg_002` in its name; the shape of the interface; which failure counts; SHA-256 implementation free; the hash read from the manifest row when the test runs; exactly one manifest row; where squillo is from a lab test.
- `squillo/PLAN.md`: §1 (Phase 0's end condition), §3 (one crate per Rust row), §10 Stage E (what a cold-start test is).
- `squillo/docs/architecture.md` §4: "In what order it is built", and no browser in the engine's test path.
- `squillo/openspec/specs/signal/spec.md`: SG-001 (mono, 48 kHz, `f32`, consecutive 128-sample blocks) and SG-002 (the scenario's text).
- `squillo/fixtures/MANIFEST.md`: the *Path* and *SHA-256* rules, the one-row rule, the *Signal fixtures* paragraph (byte layout and offsets), and the `sine-220hz.wav` row.
- `squillo-lab/README.md`:
  - *Tooling*: Rust stable, `.gitignore` already covering `experiments/*/test*/target/`, and *Where squillo is* (`SQUILLO_ROOT`, else `../squillo` from the lab root, which is `CARGO_MANIFEST_DIR/../../..`).
  - *A test that measures nothing*: C5, C7 and C10 bind the test's checks of its own inputs; C1-C4, C11-C13 and C15-C19 do not apply; no guard, README or results file for the test itself.
- `squillo-lab/INDEX.md`, E-007 row: tests 1 and 2 and the guesses they logged.

## The test (files, the command that runs it)

Files, all under `/tmp/e007/squillo-lab/experiments/E-007-cold-start/test3/`:

- `Cargo.toml`: package `signal`, edition 2021. Its one dev-dependency is `sha2 = "0.11"`, used for SHA-256 (FIPS 180-4).
- `src/lib.rs`: the `signal` crate's public interface with nothing behind it:
  - `Stream::new()`
  - `Stream::push_block(&mut self, &[f32; 128])`, which does nothing
  - `Stream::frames(&self) -> Vec<Frame>`, which returns an empty vector
  - `Frame { index, first_sample, last_sample, start_ms }` (all `u64`)
  - `BLOCK_LEN = 128`
- `tests/sg_002.rs`: the test `sg_002_one_second_gives_125_frames`. It runs in this order:
  1. **Finds squillo's root.** `SQUILLO_ROOT` if set, else `CARGO_MANIFEST_DIR/../../../../squillo`. That is the lab root, three folders up, then `../squillo`.
  2. **Checks its own checks before the scenario (C10).**
     - `fixture_check` must pass on the committed manifest and file. It must fail when the fixture's row is removed (no row), when the row is duplicated (two rows), and when one bit of sample 0 is flipped (digest).
     - `layout_check` must pass on the file. It must fail when the format tag is set to 1 and when the file is one sample short.
     - `blocks_of` must pass on the 48 000 samples and must fail on 47 999 (a remainder of 127).
     - Each must-fail input changes the one value the check reads (row count, digest input, format tag, length, remainder).
  3. **Checks its inputs (ADR 0023 steps 1-3).**
     - Hash: compared with the manifest row, read when the test runs. No copy of the hash is in the test.
     - Layout: every field the manifest states. The offsets are computed from the chunk sizes as named constants, each citing its manifest phrase (C5). A compile-time assertion checks that they agree with the manifest's stated 192 058 / 192 050 / 12 / 38 / 50 / 58.
     - Blocks: the samples become 375 blocks of 128.
  4. **Runs the scenario.** Sends the blocks in file order and asserts the THEN and AND clauses.

Command:

    cd /tmp/e007/squillo-lab/experiments/E-007-cold-start/test3 && cargo test

## Its output (the failing run, verbatim, trimmed to the relevant lines)

    $ cargo test
         Running tests/sg_002.rs (target/debug/deps/sg_002-f8d7a0162623b2d1)

    running 1 test
    test sg_002_one_second_gives_125_frames ... FAILED

    ---- sg_002_one_second_gives_125_frames stdout ----

    thread 'sg_002_one_second_gives_125_frames' (1536094) panicked at tests/sg_002.rs:259:5:
    assertion `left == right` failed: SG-002 THEN: exactly 125 frames
      left: 0
     right: 125

    test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.02s

**Why it fails.** It compiles against the crate's interface with nothing behind it. Every check of its own checks passes, and so do the fixture checks: line 259 is the scenario's THEN assertion, which comes after all of them. Nothing frames the stream yet, so `frames()` returns 0 frames where SG-002 requires 125. This is the failure ADR 0023 counts (*Which failure counts*, F-080).

The output is the same with `SQUILLO_ROOT=/tmp/e007/squillo` set.

To show the assertion is not empty, I swapped in a throwaway framing (frame *i* = samples 384*i*..384*i*+383, starting at 8*i* ms) for a moment. The test then passed (`1 passed`). I restored the stub straight away, and the run above is from the restored stub.

## Guesses (numbered; or "None")

1. **What a relative `SQUILLO_ROOT` is relative to.**
   - Needed: the lab README says to take squillo's root from `SQUILLO_ROOT` when it is set, but not how to read a relative value.
   - Looked in: `squillo-lab/README.md` *Where squillo is*, and ADR 0023's *Where the fixtures are* row.
   - Chose: use the value as given. A relative value then resolves against the test process's working directory, which `cargo test` sets to the crate folder `test3/`.
   - Effect: none on this run, which used the default and an absolute value.
2. **Where to record the must-fail inputs I chose.**
   - Needed: checklist C10 says the choice is "recorded in its README with the term it moves". But *A test that measures nothing* says the test needs no README of its own, and the experiment's README is written by the iteration that runs the session. `experiments/E-007-cold-start/README.md` does not exist in the snapshot, though `INDEX.md` links the folder.
   - Looked in: `squillo-lab/README.md` (C10, C14, *A test that measures nothing*), `squillo-lab/INDEX.md`, and the E-007 folder.
   - Chose: record each must-fail input and the value it changes in comments beside the check in `tests/sg_002.rs`, and in this report's *The test* section. I wrote no README.

Nothing else was left to guess. These points were decided or explicitly left free by the repositories, and I chose within them:
- Interface names and integer types (free, F-079).
- `sha2` 0.11 (free, F-081).
- Edition 2021 (free, F-078).
- How the manifest row is parsed (free, F-089; I read column 1 as the path and column 2 as the hash).
- The test as an integration test in `tests/` (free, F-077).
- Which must-fail inputs to use (the experiment's own choice under C10's rules).
- The crate folder `test3/` (given by the task).
