//! squillo `signal` SG-002, scenario *One second gives 125 frames*: the first
//! failing test of squillo ADR 0023 (*Decision outcome*, steps 1 to 4).
//!
//! Where squillo is (squillo-lab `README.md`, *Tooling*, *Where squillo is*):
//! the environment variable `SQUILLO_ROOT`, defaulting to `../squillo`
//! resolved from this lab repository's root, which is three folders above
//! this crate (`experiments/E-007-cold-start/test2`).
//!
//! Checks of the test's own inputs (squillo-lab `README.md`, *A test that
//! measures nothing*: C5, C7, C10), each run on a must-pass and a must-fail
//! input before the scenario's assertion:
//!
//! - the fixture's row in the manifest: exactly one row names it. Must-fail
//!   input: the manifest text with that row appended a second time; the term
//!   it moves is the count of rows the check compares with 1.
//! - the fixture's SHA-256 against its row in squillo `fixtures/MANIFEST.md`,
//!   read when the test runs (ADR 0023 step 1, F-082). Must-fail input: the
//!   fixture's bytes with the last byte's lowest bit flipped. The term it
//!   moves is the hashed message; SHA-256 (FIPS 180-4) digests every byte,
//!   so a one-bit change gives a different digest and the comparison fails.
//! - the WAV layout the manifest's *Signal fixtures* paragraph states (ADR
//!   0023 step 2). Must-fail input: the fixture's bytes with the `fmt `
//!   format tag set from 3 (IEEE float) to 1 (integer PCM). The term it moves
//!   is the format tag field the check compares with the manifest's 3.

use sha2::{Digest, Sha256};
use signal::{Stream, BLOCK_LEN};
use std::path::{Path, PathBuf};

// --- The fixture (SG-002's scenario, GIVEN) --------------------------------
/// SG-002 scenario *One second gives 125 frames*, GIVEN.
const FIXTURE: &str = "fixtures/signal/sine-220hz.wav";

// --- The layout: squillo `fixtures/MANIFEST.md`, *Signal fixtures* ---------
/// "a `fmt ` chunk of 18 bytes".
const FMT_BODY_BYTES: u32 = 18;
/// "format tag 3, IEEE float".
const FORMAT_TAG_IEEE_FLOAT: u16 = 3;
/// "1 channel".
const CHANNELS: u16 = 1;
/// "48 000 samples per second".
const SAMPLE_RATE: u32 = 48_000;
/// "32 bits per sample".
const BITS_PER_SAMPLE: u16 = 32;
/// "extension size 0".
const EXTENSION_SIZE: u16 = 0;
/// "a `fact` chunk of 4 bytes".
const FACT_BODY_BYTES: u32 = 4;
/// "holding the sample count 48 000" (also: "48 000 `f32` samples").
const SAMPLE_COUNT: u32 = 48_000;
/// "Each chunk is its 4-byte name and 4-byte length, then its body".
const CHUNK_HEADER_BYTES: usize = 4 + 4;
/// "`RIFF`, the 32-bit length ...; `WAVE`": the bytes before the first chunk.
const RIFF_HEADER_BYTES: usize = 4 + 4 + 4;

// --- SG-002 (squillo `openspec/specs/signal/spec.md`) ----------------------
/// Scenario THEN: "exactly 125 frames result, frame 0 to frame 124".
const SCENARIO_FRAMES: usize = 125;
/// Scenario AND: "frame 124 holds samples 47 616 to 47 999 and starts at 992 ms".
const SCENARIO_LAST_INDEX: u64 = 124;
const SCENARIO_LAST_FIRST_SAMPLE: u64 = 47_616;
const SCENARIO_LAST_LAST_SAMPLE: u64 = 47_999;
const SCENARIO_LAST_START_MS: u64 = 992;

fn squillo_root() -> PathBuf {
    if let Some(p) = std::env::var_os("SQUILLO_ROOT") {
        return PathBuf::from(p);
    }
    // This crate is <lab>/experiments/E-007-cold-start/test2.
    let lab = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("..")
        .join("..");
    lab.join("..").join("squillo")
}

/// The SHA-256 cells of every row of `fixtures/MANIFEST.md` whose first
/// column is the fixture's path, written bare (the manifest's own note).
fn manifest_rows(manifest: &str, fixture: &str) -> Vec<String> {
    manifest
        .lines()
        .filter_map(|line| {
            let cells: Vec<&str> = line.split('|').map(str::trim).collect();
            // "| path | sha | ... |" splits into ["", path, sha, ...].
            (cells.len() > 3 && cells[1] == fixture).then(|| cells[2].to_string())
        })
        .collect()
}

fn sha256_hex(bytes: &[u8]) -> String {
    Sha256::digest(bytes)
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect()
}

/// The hash check (ADR 0023 step 1).
fn hash_matches(bytes: &[u8], expected: &str) -> bool {
    sha256_hex(bytes) == expected
}

fn u16_at(b: &[u8], at: usize) -> u16 {
    u16::from_le_bytes(b[at..at + 2].try_into().unwrap())
}
fn u32_at(b: &[u8], at: usize) -> u32 {
    u32::from_le_bytes(b[at..at + 4].try_into().unwrap())
}

/// The layout check (ADR 0023 step 2, the manifest's *Signal fixtures*).
/// Returns the byte range of the `data` chunk's samples, or why it failed.
fn check_layout(b: &[u8]) -> Result<std::ops::Range<usize>, String> {
    // Every size and offset below is computed from the manifest's stated
    // sizes (C5), never retyped.
    let bytes_per_sample = (BITS_PER_SAMPLE / 8) as u32;
    let block_align = CHANNELS as u32 * bytes_per_sample;
    let byte_rate = SAMPLE_RATE * block_align;
    let data_body = SAMPLE_COUNT * block_align;
    let fmt_at = RIFF_HEADER_BYTES;
    let fact_at = fmt_at + CHUNK_HEADER_BYTES + FMT_BODY_BYTES as usize;
    let data_at = fact_at + CHUNK_HEADER_BYTES + FACT_BODY_BYTES as usize;
    let samples_at = data_at + CHUNK_HEADER_BYTES;
    let total = samples_at + data_body as usize;
    let riff_len = (total - CHUNK_HEADER_BYTES) as u32;

    let want = |ok: bool, what: &str| if ok { Ok(()) } else { Err(what.to_string()) };
    want(b.len() == total, "file length")?;
    want(&b[0..4] == b"RIFF", "RIFF")?;
    want(u32_at(b, 4) == riff_len, "RIFF length")?;
    want(&b[8..12] == b"WAVE", "WAVE")?;
    want(&b[fmt_at..fmt_at + 4] == b"fmt ", "fmt name")?;
    want(u32_at(b, fmt_at + 4) == FMT_BODY_BYTES, "fmt length")?;
    let f = fmt_at + CHUNK_HEADER_BYTES;
    want(u16_at(b, f) == FORMAT_TAG_IEEE_FLOAT, "format tag")?;
    want(u16_at(b, f + 2) == CHANNELS, "channels")?;
    want(u32_at(b, f + 4) == SAMPLE_RATE, "sample rate")?;
    want(u32_at(b, f + 8) == byte_rate, "byte rate")?;
    want(u16_at(b, f + 12) as u32 == block_align, "block align")?;
    want(u16_at(b, f + 14) == BITS_PER_SAMPLE, "bits per sample")?;
    want(u16_at(b, f + 16) == EXTENSION_SIZE, "extension size")?;
    want(&b[fact_at..fact_at + 4] == b"fact", "fact name")?;
    want(u32_at(b, fact_at + 4) == FACT_BODY_BYTES, "fact length")?;
    want(u32_at(b, fact_at + CHUNK_HEADER_BYTES) == SAMPLE_COUNT, "fact sample count")?;
    want(&b[data_at..data_at + 4] == b"data", "data name")?;
    want(u32_at(b, data_at + 4) == data_body, "data length")?;
    Ok(samples_at..total)
}

#[test]
fn sg_002_one_second_gives_125_frames() {
    let squillo = squillo_root();
    let manifest = std::fs::read_to_string(squillo.join("fixtures/MANIFEST.md"))
        .expect("read fixtures/MANIFEST.md");
    let bytes = std::fs::read(squillo.join(FIXTURE)).expect("read the fixture");

    // Each check of the test's inputs runs on its must-pass and its must-fail
    // input (C10) before the scenario.
    // The row check: exactly one row names the fixture. Must-fail input: the
    // manifest with that row written twice (the term moved: the row count).
    let rows = manifest_rows(&manifest, FIXTURE);
    assert_eq!(rows.len(), 1, "row check: must-pass input");
    let doubled = format!("{manifest}\n| {FIXTURE} | {} | x | x |\n", rows[0]);
    assert_ne!(manifest_rows(&doubled, FIXTURE).len(), 1, "row check: must-fail input");
    let expected_sha = rows[0].clone();

    let mut flipped = bytes.clone();
    *flipped.last_mut().unwrap() ^= 1;
    assert!(hash_matches(&bytes, &expected_sha), "hash check: must-pass input");
    assert!(!hash_matches(&flipped, &expected_sha), "hash check: must-fail input");

    let mut pcm = bytes.clone();
    let tag_at = RIFF_HEADER_BYTES + CHUNK_HEADER_BYTES;
    pcm[tag_at..tag_at + 2].copy_from_slice(&1u16.to_le_bytes());
    let samples = check_layout(&bytes).expect("layout check: must-pass input");
    assert!(check_layout(&pcm).is_err(), "layout check: must-fail input");

    // ADR 0023 step 2: the 48 000 f32 samples, little-endian, in file order.
    let samples: Vec<f32> = bytes[samples]
        .chunks_exact(4)
        .map(|c| f32::from_le_bytes(c.try_into().unwrap()))
        .collect();

    // ADR 0023 step 3: deliver them in file order, 375 blocks of 128 (SG-001).
    // 48 000 samples (the layout check) are 375 whole blocks of 128.
    let blocks = samples.chunks_exact(BLOCK_LEN);
    let mut stream = Stream::new();
    for block in blocks {
        stream.push_block(block.try_into().unwrap());
    }

    // ADR 0023 step 4, the scenario's THEN and AND.
    let frames = stream.frames();
    assert_eq!(
        frames.len(),
        SCENARIO_FRAMES,
        "THEN exactly 125 frames result, frame 0 to frame 124"
    );
    for (i, f) in frames.iter().enumerate() {
        assert_eq!(f.index, i as u64, "frames numbered 0 to 124 in order");
    }
    let f = frames[SCENARIO_FRAMES - 1];
    assert_eq!(
        (f.index, f.first_sample, f.last_sample, f.start_ms),
        (
            SCENARIO_LAST_INDEX,
            SCENARIO_LAST_FIRST_SAMPLE,
            SCENARIO_LAST_LAST_SAMPLE,
            SCENARIO_LAST_START_MS
        ),
        "AND frame 124 holds samples 47 616 to 47 999 and starts at 992 ms"
    );
}
