//! squillo `signal` SG-002, scenario *One second gives 125 frames*: the first
//! failing test named by squillo `docs/decisions/0023-the-build-order.md`
//! (*The first failing test*, steps 1 to 4, and *The first test's frame*).
//!
//! It uses only the `signal` crate's public interface. Its own inputs are
//! checked first (the fixture's one manifest row and its SHA-256, then the
//! WAV layout the manifest's *Signal fixtures* paragraph states, then the
//! 128-sample blocks), each check run on a must-pass and a must-fail input
//! before the scenario's assertion (squillo-lab `README.md`, *A test that
//! measures nothing*: C5, C7, C10).
//!
//! Where squillo is (squillo-lab `README.md`, *Tooling*, *Where squillo is*):
//! `SQUILLO_ROOT` when set, else `../squillo` from the lab's root; the lab's
//! root is three folders above this crate's folder
//! (`CARGO_MANIFEST_DIR/../../..`: `test3/` -> `E-007-cold-start/` ->
//! `experiments/` -> lab root).

use sha2::{Digest, Sha256};
use signal::{Stream, BLOCK_LEN};
use std::path::PathBuf;

// ---- The fixture and its manifest (ADR 0023 step 1; PLAN.md §6) ----

/// The fixture SG-002's scenario names (signal spec, SG-002, GIVEN).
const FIXTURE: &str = "fixtures/signal/sine-220hz.wav";
/// The manifest that lists each fixture's one row (PLAN.md §6; fixtures/MANIFEST.md, *Path*).
const MANIFEST: &str = "fixtures/MANIFEST.md";
/// Folders from this crate's folder up to the lab's root (lab README, *Where squillo is*).
const CRATE_DEPTH_BELOW_LAB_ROOT: usize = 3;

// ---- The WAV layout (fixtures/MANIFEST.md, *Signal fixtures*) ----

/// `RIFF`, its 32-bit length, `WAVE` (manifest: "`RIFF`, the 32-bit length ...; `WAVE`").
const RIFF_HEADER_LEN: usize = 4 + 4 + 4;
/// A chunk's header (manifest: "Each chunk is its 4-byte name and 4-byte length").
const CHUNK_HEADER_LEN: usize = 4 + 4;
/// The `fmt ` chunk's body (manifest: "a `fmt ` chunk of 18 bytes").
const FMT_BODY_LEN: usize = 18;
/// The `fact` chunk's body (manifest: "a `fact` chunk of 4 bytes").
const FACT_BODY_LEN: usize = 4;
/// Format tag (manifest: "format tag 3, IEEE float").
const FORMAT_TAG_IEEE_FLOAT: u16 = 3;
/// Channels (manifest: "1 channel").
const CHANNELS: u16 = 1;
/// Sample rate (manifest: "48 000 samples per second"; SG-001).
const SAMPLE_RATE: u32 = 48_000;
/// Bits per sample (manifest: "32 bits per sample").
const BITS_PER_SAMPLE: u16 = 32;
/// Bytes per sample, from the bits per sample above.
const BYTES_PER_SAMPLE: usize = (BITS_PER_SAMPLE / 8) as usize;
/// Extension size (manifest: "extension size 0").
const EXTENSION_SIZE: u16 = 0;
/// Samples in the file (manifest: "a `fact` chunk ... holding the sample count 48 000"; SG-002 GIVEN "48 000 samples").
const SAMPLE_COUNT: usize = 48_000;
/// The `data` chunk's body, from the sample count and bytes per sample.
const DATA_BODY_LEN: usize = SAMPLE_COUNT * BYTES_PER_SAMPLE;
/// Byte offsets, computed from the sizes above ("the offsets follow from these sizes").
const FMT_AT: usize = RIFF_HEADER_LEN;
const FACT_AT: usize = FMT_AT + CHUNK_HEADER_LEN + FMT_BODY_LEN;
const DATA_AT: usize = FACT_AT + CHUNK_HEADER_LEN + FACT_BODY_LEN;
const SAMPLE_0_AT: usize = DATA_AT + CHUNK_HEADER_LEN;
const FILE_LEN: usize = SAMPLE_0_AT + DATA_BODY_LEN;
/// The RIFF length field: the file less `RIFF` and the field itself.
const RIFF_LEN: usize = FILE_LEN - 8;

// The manifest also states its sums; the computed layout must agree with them.
/// Manifest: "a WAV file of exactly 192 058 bytes".
const STATED_FILE_LEN: usize = 192_058;
/// Manifest: "the 32-bit length 192 050".
const STATED_RIFF_LEN: usize = 192_050;
/// Manifest: "`fmt ` at byte 12, `fact` at 38, `data` at 50, sample 0 at 58".
const STATED_OFFSETS: [usize; 4] = [12, 38, 50, 58];
const _: () = assert!(FILE_LEN == STATED_FILE_LEN);
const _: () = assert!(RIFF_LEN == STATED_RIFF_LEN);
const _: () = assert!(FMT_AT == STATED_OFFSETS[0]);
const _: () = assert!(FACT_AT == STATED_OFFSETS[1]);
const _: () = assert!(DATA_AT == STATED_OFFSETS[2]);
const _: () = assert!(SAMPLE_0_AT == STATED_OFFSETS[3]);

// ---- The scenario (signal spec, SG-002, *One second gives 125 frames*) ----

/// THEN "exactly 125 frames result, frame 0 to frame 124".
const EXPECTED_FRAME_COUNT: usize = 125;
/// AND "frame 124 holds samples 47 616 to 47 999 and starts at 992 ms".
const LAST_FRAME_INDEX: u64 = 124;
const LAST_FRAME_FIRST_SAMPLE: u64 = 47_616;
const LAST_FRAME_LAST_SAMPLE: u64 = 47_999;
const LAST_FRAME_START_MS: u64 = 992;

fn squillo_root() -> PathBuf {
    if let Some(root) = std::env::var_os("SQUILLO_ROOT") {
        return PathBuf::from(root);
    }
    let mut lab_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    for _ in 0..CRATE_DEPTH_BELOW_LAB_ROOT {
        lab_root.push("..");
    }
    lab_root.join("..").join("squillo")
}

/// The hashes of every manifest row whose first column is `path`
/// (first column *Path*, second *SHA-256*).
fn manifest_rows<'a>(manifest: &'a str, path: &str) -> Vec<&'a str> {
    manifest
        .lines()
        .map(str::trim)
        .filter(|line| line.starts_with('|'))
        .filter_map(|line| {
            let cells: Vec<&str> = line.split('|').map(str::trim).collect();
            // cells[0] is the empty text before the leading '|'.
            if cells.len() > 2 && cells[1] == path {
                Some(cells[2])
            } else {
                None
            }
        })
        .collect()
}

/// ADR 0023 step 1: exactly one manifest row for the fixture, and the
/// file's SHA-256 equal to that row's.
fn fixture_check(manifest: &str, path: &str, bytes: &[u8]) -> Result<(), String> {
    let rows = manifest_rows(manifest, path);
    if rows.len() != 1 {
        return Err(format!("{path}: {} manifest rows, not exactly one", rows.len()));
    }
    let digest: String = Sha256::digest(bytes).iter().map(|b| format!("{b:02x}")).collect();
    if digest != rows[0] {
        return Err(format!("{path}: SHA-256 {digest} differs from its manifest row {}", rows[0]));
    }
    Ok(())
}

fn u16_at(b: &[u8], at: usize) -> u16 {
    u16::from_le_bytes([b[at], b[at + 1]])
}
fn u32_at(b: &[u8], at: usize) -> u32 {
    u32::from_le_bytes([b[at], b[at + 1], b[at + 2], b[at + 3]])
}

/// ADR 0023 step 2: the layout the manifest's *Signal fixtures* paragraph
/// states, field by field; on success, the `data` chunk's samples in file order.
fn layout_check(b: &[u8]) -> Result<Vec<f32>, String> {
    let fail = |what: &str| Err(format!("layout: {what}"));
    if b.len() != FILE_LEN {
        return fail(&format!("{} bytes, not {FILE_LEN}", b.len()));
    }
    if &b[0..4] != b"RIFF" || u32_at(b, 4) as usize != RIFF_LEN || &b[8..12] != b"WAVE" {
        return fail("RIFF header");
    }
    let f = FMT_AT + CHUNK_HEADER_LEN;
    if &b[FMT_AT..FMT_AT + 4] != b"fmt " || u32_at(b, FMT_AT + 4) as usize != FMT_BODY_LEN {
        return fail("fmt chunk header");
    }
    if u16_at(b, f) != FORMAT_TAG_IEEE_FLOAT {
        return fail("format tag");
    }
    if u16_at(b, f + 2) != CHANNELS {
        return fail("channels");
    }
    if u32_at(b, f + 4) != SAMPLE_RATE {
        return fail("sample rate");
    }
    if u32_at(b, f + 8) as usize != SAMPLE_RATE as usize * CHANNELS as usize * BYTES_PER_SAMPLE {
        return fail("bytes per second");
    }
    if u16_at(b, f + 12) as usize != CHANNELS as usize * BYTES_PER_SAMPLE {
        return fail("block align");
    }
    if u16_at(b, f + 14) != BITS_PER_SAMPLE {
        return fail("bits per sample");
    }
    if u16_at(b, f + 16) != EXTENSION_SIZE {
        return fail("extension size");
    }
    if &b[FACT_AT..FACT_AT + 4] != b"fact"
        || u32_at(b, FACT_AT + 4) as usize != FACT_BODY_LEN
        || u32_at(b, FACT_AT + CHUNK_HEADER_LEN) as usize != SAMPLE_COUNT
    {
        return fail("fact chunk");
    }
    if &b[DATA_AT..DATA_AT + 4] != b"data" || u32_at(b, DATA_AT + 4) as usize != DATA_BODY_LEN {
        return fail("data chunk header");
    }
    Ok(b[SAMPLE_0_AT..]
        .chunks_exact(BYTES_PER_SAMPLE)
        .map(|s| f32::from_le_bytes([s[0], s[1], s[2], s[3]]))
        .collect())
}

/// ADR 0023 step 3 (SG-001): the samples in file order as consecutive
/// 128-sample blocks; a remainder that is not a whole block is refused.
fn blocks_of(samples: &[f32]) -> Result<Vec<[f32; BLOCK_LEN]>, String> {
    let chunks = samples.chunks_exact(BLOCK_LEN);
    if !chunks.remainder().is_empty() {
        return Err(format!("{} samples are not whole blocks of {BLOCK_LEN}", samples.len()));
    }
    Ok(chunks.map(|c| c.try_into().expect("chunks_exact gives whole blocks")).collect())
}

#[test]
fn sg_002_one_second_gives_125_frames() {
    let root = squillo_root();
    let manifest = std::fs::read_to_string(root.join(MANIFEST))
        .unwrap_or_else(|e| panic!("reading {}: {e}", root.join(MANIFEST).display()));
    let bytes = std::fs::read(root.join(FIXTURE))
        .unwrap_or_else(|e| panic!("reading {}: {e}", root.join(FIXTURE).display()));

    // ---- Checks of the checks (C10), each before the scenario ----

    // fixture_check, rows: must pass on the manifest as committed; must fail
    // on the manifest with the fixture's row removed (none) and duplicated
    // (two). The term moved is the count of rows whose first column is the path.
    assert!(fixture_check(&manifest, FIXTURE, &bytes).is_ok(), "must-pass: fixture check");
    let row = manifest
        .lines()
        .find(|l| manifest_rows(l, FIXTURE).len() == 1)
        .expect("the fixture's row line");
    let without_row: String =
        manifest.lines().filter(|l| *l != row).map(|l| format!("{l}\n")).collect();
    let with_two_rows = format!("{manifest}\n{row}\n");
    assert!(fixture_check(&without_row, FIXTURE, &bytes).is_err(), "must-fail: no row");
    assert!(fixture_check(&with_two_rows, FIXTURE, &bytes).is_err(), "must-fail: two rows");
    // fixture_check, digest: must fail on the file with one bit of sample 0
    // flipped. The term moved is the digest's input; the row is unchanged.
    let mut one_bit_changed = bytes.clone();
    one_bit_changed[SAMPLE_0_AT] ^= 1;
    assert!(fixture_check(&manifest, FIXTURE, &one_bit_changed).is_err(), "must-fail: digest");

    // layout_check: must pass on the file; must fail with the format tag set
    // to 1 (integer PCM), the field "format tag 3" reads, and on the file
    // short of its last sample, the term the length check reads.
    assert!(layout_check(&bytes).is_ok(), "must-pass: layout");
    let mut pcm_tag = bytes.clone();
    pcm_tag[FMT_AT + CHUNK_HEADER_LEN..FMT_AT + CHUNK_HEADER_LEN + 2].copy_from_slice(&1u16.to_le_bytes());
    assert!(layout_check(&pcm_tag).is_err(), "must-fail: format tag");
    assert!(layout_check(&bytes[..bytes.len() - BYTES_PER_SAMPLE]).is_err(), "must-fail: length");

    // blocks_of: must pass on the file's samples; must fail on them less one
    // sample, which leaves a remainder of 127, the term it reads.
    let samples = layout_check(&bytes).expect("layout");
    assert!(blocks_of(&samples).is_ok(), "must-pass: blocks");
    assert!(blocks_of(&samples[..samples.len() - 1]).is_err(), "must-fail: blocks");

    // ---- The test's own input checks (ADR 0023 steps 1 to 3) ----
    fixture_check(&manifest, FIXTURE, &bytes).expect("fixture check");
    let samples = layout_check(&bytes).expect("layout check");
    let blocks = blocks_of(&samples).expect("blocks");

    // ---- The scenario ----
    // WHEN it is delivered to `signal` (in file order, 128-sample blocks, SG-001).
    let mut stream = Stream::new();
    for block in &blocks {
        stream.push_block(block);
    }
    let frames = stream.frames();

    // THEN exactly 125 frames result, frame 0 to frame 124.
    assert_eq!(frames.len(), EXPECTED_FRAME_COUNT, "SG-002 THEN: exactly 125 frames");
    for (i, frame) in frames.iter().enumerate() {
        assert_eq!(frame.index, i as u64, "SG-002 THEN: frame 0 to frame 124, in order");
    }
    // AND frame 124 holds samples 47 616 to 47 999 and starts at 992 ms.
    let last = frames[EXPECTED_FRAME_COUNT - 1];
    assert_eq!(last.index, LAST_FRAME_INDEX, "SG-002 AND: frame 124");
    assert_eq!(last.first_sample, LAST_FRAME_FIRST_SAMPLE, "SG-002 AND: first sample 47 616");
    assert_eq!(last.last_sample, LAST_FRAME_LAST_SAMPLE, "SG-002 AND: last sample 47 999");
    assert_eq!(last.start_ms, LAST_FRAME_START_MS, "SG-002 AND: starts at 992 ms");
}
