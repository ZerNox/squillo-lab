<!-- E-007 test 1: the subagent's report, as it returned it in its reply.
     Its write to /tmp/e007/report.md was refused by the harness (subagents
     may not write report files), so the iteration saved the reply's report
     text here unchanged. -->

## What to build first

Build the framing in the `signal` domain, the first of the engine's pure Rust crates. The first failing test is `signal` SG-002, scenario *One second gives 125 frames*:

- Deliver `fixtures/signal/sine-220hz.wav` to `signal`: 48 000 `f32` samples, with its SHA-256 checked first.
- Deliver it in 375 consecutive blocks of 128 samples, in file order.
- Expect exactly 125 frames, frame 0 to frame 124.
- Expect frame 124 to hold samples 47 616 to 47 999 and to start at 992 ms.

The rest follows ADR 0023's order:
1. The rest of `signal`, in this order: SG-003, SG-006, SG-005, SG-004, SG-007, SG-008, then SG-001.
2. Then `metrics`, `exercises`, `analyzers`, `synthesis` and `coach`.
3. Then the WASM boundary, `capture`, `runner` and `ui`.
4. `build` and `security` last.

## Where I read it

- **`squillo/docs/decisions/0023-the-build-order.md`**, *Decision outcome*: it names the first failing test and its four steps (hash check against the manifest row, data-chunk layout, 375 blocks of 128, the assertions), plus the build-order table.
- **`squillo/docs/architecture.md`**:
  - §2: the build-order row.
  - §4: "Rust compiled to WASM, as small single-purpose crates"; "Pure math crates. No browser anywhere in the engine's test path"; *In what order it is built*.
- **`squillo/openspec/specs/signal/spec.md`**:
  - SG-001: mono, 48 kHz, `f32`, blocks of 128, in file order.
  - SG-002: frames of 384 samples, `⌊N/384⌋` frames, frame *i* = samples `384i` to `384i+383`, starting at `8i` ms, and the scenario itself.
- **`squillo/fixtures/MANIFEST.md`**: the *Signal fixtures* paragraph (the exact WAV layout) and the `sine-220hz.wav` row (SHA-256 `a98af9f7…cee59`).
- **`squillo/PLAN.md`** §1 and §10 Stage E: a cold-start test is written in `squillo-lab` and never built on.
- **`squillo-lab/README.md`**: *Tooling* (Rust stable in `~/.cargo`) and the S15 checklist; items C5, C7 and C10 shaped the checks in the test.

## The test (files, the command that runs it)

All files are in `/tmp/e007/squillo-lab/experiments/E-007-cold-start/test1/`:

- **`Cargo.toml`**: package `signal`. Its only dev-dependency is `sha2 = "=0.11.0"`, pinned exactly as E-002 pins its crates.
- **`src/lib.rs`**: an empty stand-in for the `signal` crate's interface:
  - `BLOCK = 128`
  - `Frame { index, first_sample, last_sample, start_ms }`
  - `Signal::new()`
  - `Signal::push(&[f32; 128])`, which does nothing
  - `Signal::frames() -> &[Frame]`
- **`tests/sg_002_one_second_gives_125_frames.rs`**: the test. In order, it:
  1. Reads the expected SHA-256 from the fixture's row in `MANIFEST.md`, rather than retyping it.
  2. Runs checks of its own checks before anything else:
     - SHA-256 on the FIPS "abc" test vector.
     - The hash check passes on the file and fails with one bit flipped.
     - The layout check passes on the file and fails with format tag 1.
  3. Parses the WAV field by field against the manifest's layout.
  4. Asserts 48 000 samples, which make exactly 375 blocks of 128.
  5. Works out the expected values from SG-002's definition and checks them against the scenario's own numbers: 125, 47 616, 47 999 and 992.
  6. Delivers the blocks in file order and asserts the scenario.

Command (it finds squillo at `../../../../squillo`; the `SQUILLO` environment variable overrides that):

    cd /tmp/e007/squillo-lab/experiments/E-007-cold-start/test1 && cargo test

As a check on the test itself, a throwaway copy with a 6-line framing implementation in `push` passed it (1 passed). I deleted that copy. Only the empty stand-in remains.

## Its output (the failing run, verbatim, trimmed to the relevant lines)

    Running tests/sg_002_one_second_gives_125_frames.rs (target/debug/deps/sg_002_one_second_gives_125_frames-2fb2f493a7570a01)

    running 1 test
    test sg_002_one_second_gives_125_frames ... FAILED

    ---- sg_002_one_second_gives_125_frames stdout ----

    thread 'sg_002_one_second_gives_125_frames' (1004289) panicked at tests/sg_002_one_second_gives_125_frames.rs:170:5:
    assertion `left == right` failed: number of frames
      left: 0
     right: 125

    test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.01s

Why it fails: every earlier check passed. The hash matches the manifest row, the layout matches the manifest, there are 48 000 samples in 375 blocks, and the derived values match the scenario. So the failure is the scenario's first THEN: `frames.len() == 125` got 0, because nothing frames a stream yet. That is the reason ADR 0023 itself gives.

## Guesses (numbered; or "None")

1. **Language and test harness.** Needed: what to write the test in and what runs it. Looked: ADR 0023 says "native tests"; `architecture.md` §4 says Rust crates; the lab's *Tooling* lists Rust stable. Chose: Rust, `cargo test`, an integration test under `tests/`. This is strongly implied, but no document says it outright.
2. **Crate name and file layout.** Needed: the package name and where the library and test go. Looked: ADR 0023, `architecture.md`, ADR 0006 and the `signal` spec name the domain `signal` but give no crate name or layout. Chose: one package named `signal`, with `src/lib.rs` and `tests/sg_002_one_second_gives_125_frames.rs`. The test file's name is mine.
3. **The `signal` interface.** Needed: how a test hands blocks to `signal` and reads frames back. Looked: the `signal` spec has requirements but no Design section in the file; ADR 0006 covers the boundary to the page, not the Rust API; ADR 0007. Chose: `Signal::new`, `push(&[f32; 128])`, `frames() -> &[Frame]`, and `Frame { index, first_sample, last_sample (inclusive), start_ms: u64 }`. Frames build up across pushes, and there is no `finish()` call.
4. **What "failing" means.** Needed: whether a compile error counts, or it must fail an assertion. Looked: ADR 0023 says only "it fails because nothing frames a stream yet". Chose: an empty stand-in crate, so the test compiles, its preconditions pass, and it fails on the scenario's assertion.
5. **The SHA-256 tool.** Needed: how to compute the hash. Looked: ADR 0023 step 1 and the lab's *Tooling*; neither names a library. Chose: the `sha2` crate pinned at `=0.11.0`, fetched from crates.io.
6. **Where the expected hash comes from.** Needed: whether to use the hash quoted in the ADR or the one in the manifest row. Looked: ADR 0023 says "against its row in `fixtures/MANIFEST.md`"; lab checklist C5 says never retype a value. Chose: parse the row `| <path> | <sha256> |` when the test runs. The two values are the same today.
7. **Where the squillo repository is.** Needed: the path from the lab test to `squillo/fixtures`. Looked: the lab README implies the two repositories sit side by side; E-003 uses `../../../squillo`. Chose: `CARGO_MANIFEST_DIR/../../../../squillo`. The `SQUILLO` override is my invention.
8. **How much of the lab's S15 checklist applies.** Needed: whether to add a committed-first guard and a rules commit (C14, C15), run `checkkeys.py` (C16, C18), and add a README and `results/`. Looked: those rules are written for Python or Node experiments that write results files. `/tmp/e007/squillo-lab` is not a git repository, so a git guard cannot work, and `checkkeys.py` reads Python. Chose: apply only C5, C7 and C10 inside the test, and write no guard, commit, README or results JSON, because the task limits writes to `test1/` and the report.
9. **Exact byte offsets in the WAV file.** Needed: where each field sits. Looked: the manifest gives the order and sizes of the fields, not their offsets. Chose: offsets from the standard WAV chunk header: `fmt ` at 12, `fact` at 38, `data` at 50, samples from byte 58.
10. **Inputs the checks of checks must fail on.** Needed: which change to make for each check. Looked: lab checklist C10 requires them but does not choose them. Chose: flip the low bit of sample 1000 (byte 58 + 4·1000) for the hash check; set the format tag to 1 for the layout check.
