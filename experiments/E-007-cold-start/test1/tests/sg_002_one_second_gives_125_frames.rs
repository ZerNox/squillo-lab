//! squillo ADR 0023's first failing test: `signal` SG-002, scenario
//! *One second gives 125 frames* (openspec/specs/signal/spec.md).
//!
//!   GIVEN fixtures/signal/sine-220hz.wav, 48 000 samples
//!   WHEN  it is delivered to `signal`
//!   THEN  exactly 125 frames result, frame 0 to frame 124
//!   AND   frame 124 holds samples 47 616 to 47 999 and starts at 992 ms
//!
//! ADR 0023's steps: (1) check the fixture's SHA-256 against its row in
//! fixtures/MANIFEST.md; (2) take its 48 000 f32 samples from the `data`
//! chunk, laid out as the manifest's *Signal fixtures* paragraph states;
//! (3) deliver them in file order in 375 blocks of 128 (SG-001); (4) assert.
//!
//! The lab's S15 checklist: every check below is run first on a case it
//! must pass and on one it must fail (C10), before the scenario's assertion.

use sha2::{Digest, Sha256};
use signal::{Signal, BLOCK};
use std::path::PathBuf;

const FIXTURE: &str = "fixtures/signal/sine-220hz.wav";

// SG-002: frames of 384 samples, 8 ms at 48 000 Hz.
const FRAME_SAMPLES: usize = 384; // SG-002 "frames of 384 samples"
const FRAME_MS: u64 = 8; // SG-002 "Frame i ... SHALL start at 8i ms"

// The scenario's own numbers, as the spec writes them.
const SCENARIO_FRAMES: usize = 125; // SG-002 scenario "exactly 125 frames"
const SCENARIO_LAST_FIRST: usize = 47_616; // SG-002 scenario "samples 47 616 to"
const SCENARIO_LAST_LAST: usize = 47_999; // SG-002 scenario "to 47 999"
const SCENARIO_LAST_START_MS: u64 = 992; // SG-002 scenario "starts at 992 ms"

// fixtures/MANIFEST.md, *Signal fixtures* (iteration 14): the WAV layout.
const WAV_BYTES: usize = 192_058; // "exactly 192 058 bytes"
const RIFF_LEN: u32 = 192_050; // "the 32-bit length 192 050"
const FMT_LEN: u32 = 18; // "a `fmt ` chunk of 18 bytes"
const FORMAT_TAG: u16 = 3; // "format tag 3, IEEE float"
const CHANNELS: u16 = 1; // "1 channel"
const RATE: u32 = 48_000; // "48 000 samples per second"
const BYTE_RATE: u32 = 192_000; // "192 000 bytes per second"
const BLOCK_ALIGN: u16 = 4; // "block align 4"
const BITS: u16 = 32; // "32 bits per sample"
const EXT_SIZE: u16 = 0; // "extension size 0"
const FACT_LEN: u32 = 4; // "a `fact` chunk of 4 bytes"
const SAMPLES: u32 = 48_000; // "holding the sample count 48 000"
const DATA_LEN: u32 = 192_000; // "a `data` chunk of 192 000 bytes"

fn squillo_root() -> PathBuf {
    // The two repositories sit side by side (squillo-lab README: `squillo`
    // holds the specification); SQUILLO overrides.
    match std::env::var_os("SQUILLO") {
        Some(p) => PathBuf::from(p),
        None => PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../../../squillo"),
    }
}

/// The SHA-256 the manifest's row for `path` gives, read by the row's own
/// form: `| <path> | <sha256> | ...`. Never retyped (lab checklist C5).
fn manifest_sha256(manifest: &str, path: &str) -> String {
    let rows: Vec<&str> = manifest
        .lines()
        .filter(|l| {
            let cells: Vec<&str> = l.split('|').map(str::trim).collect();
            cells.len() > 2 && cells[1] == path
        })
        .collect();
    assert_eq!(rows.len(), 1, "manifest must hold exactly one row for {path}");
    let hash = rows[0].split('|').map(str::trim).nth(2).unwrap().to_string();
    assert!(
        hash.len() == 64 && hash.bytes().all(|b| b.is_ascii_hexdigit()),
        "manifest row for {path} holds no SHA-256: {hash:?}"
    );
    hash
}

fn sha256_hex(bytes: &[u8]) -> String {
    Sha256::digest(bytes).iter().map(|b| format!("{b:02x}")).collect()
}

fn hash_ok(bytes: &[u8], expected: &str) -> bool {
    sha256_hex(bytes) == expected
}

fn u16_at(b: &[u8], i: usize) -> u16 {
    u16::from_le_bytes([b[i], b[i + 1]])
}
fn u32_at(b: &[u8], i: usize) -> u32 {
    u32::from_le_bytes([b[i], b[i + 1], b[i + 2], b[i + 3]])
}

/// The manifest's layout, field by field, in its order; the samples, or
/// the first field that differs.
fn read_samples(b: &[u8]) -> Result<Vec<f32>, String> {
    let want = |ok: bool, what: &str| if ok { Ok(()) } else { Err(what.to_string()) };
    want(b.len() == WAV_BYTES, "file length")?;
    want(&b[0..4] == b"RIFF", "RIFF")?;
    want(u32_at(b, 4) == RIFF_LEN, "RIFF length")?;
    want(&b[8..12] == b"WAVE", "WAVE")?;
    want(&b[12..16] == b"fmt ", "fmt id")?;
    want(u32_at(b, 16) == FMT_LEN, "fmt length")?;
    want(u16_at(b, 20) == FORMAT_TAG, "format tag")?;
    want(u16_at(b, 22) == CHANNELS, "channels")?;
    want(u32_at(b, 24) == RATE, "sample rate")?;
    want(u32_at(b, 28) == BYTE_RATE, "byte rate")?;
    want(u16_at(b, 32) == BLOCK_ALIGN, "block align")?;
    want(u16_at(b, 34) == BITS, "bits per sample")?;
    want(u16_at(b, 36) == EXT_SIZE, "extension size")?;
    want(&b[38..42] == b"fact", "fact id")?;
    want(u32_at(b, 42) == FACT_LEN, "fact length")?;
    want(u32_at(b, 46) == SAMPLES, "fact sample count")?;
    want(&b[50..54] == b"data", "data id")?;
    want(u32_at(b, 54) == DATA_LEN, "data length")?;
    let data = &b[58..];
    want(data.len() == DATA_LEN as usize, "data bytes present")?;
    Ok(data
        .chunks_exact(4)
        .map(|c| f32::from_le_bytes([c[0], c[1], c[2], c[3]]))
        .collect())
}

#[test]
fn sg_002_one_second_gives_125_frames() {
    let root = squillo_root();
    let manifest = std::fs::read_to_string(root.join("fixtures/MANIFEST.md"))
        .expect("read squillo fixtures/MANIFEST.md");
    let bytes = std::fs::read(root.join(FIXTURE)).expect("read the fixture");
    let expected_hash = manifest_sha256(&manifest, FIXTURE);

    // --- Checks of the checks (C10), before the scenario. ---------------
    // SHA-256 itself, on FIPS 180-2's "abc" vector.
    assert!(hash_ok(
        b"abc",
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    ));
    // Hash check: must pass on the file; must fail on the file with one
    // bit of one sample flipped (the input the check reads differs).
    let mut flipped = bytes.clone();
    flipped[58 + 4 * 1000] ^= 1;
    assert!(hash_ok(&bytes, &expected_hash), "fixture's SHA-256 differs from its manifest row");
    assert!(!hash_ok(&flipped, &expected_hash));
    // Layout check: must pass on the file; must fail with format tag 1 (PCM).
    let mut pcm = bytes.clone();
    pcm[20] = 1;
    assert!(read_samples(&pcm).is_err());
    let samples = read_samples(&bytes).expect("fixture layout as the manifest states");
    assert_eq!(samples.len(), SAMPLES as usize);

    // Blocks: the samples divide into whole 128-sample blocks (SG-001).
    assert_eq!(samples.len() % BLOCK, 0);
    let blocks = samples.len() / BLOCK;
    assert_eq!(blocks, 375); // ADR 0023 step 3: "375 consecutive blocks"

    // Expected values computed from SG-002's definition on this input (C7),
    // and matched to the numbers the scenario writes.
    let n_frames = samples.len() / FRAME_SAMPLES; // floor(N / 384)
    let last = n_frames - 1;
    assert_eq!(n_frames, SCENARIO_FRAMES);
    assert_eq!(FRAME_SAMPLES * last, SCENARIO_LAST_FIRST);
    assert_eq!(FRAME_SAMPLES * last + FRAME_SAMPLES - 1, SCENARIO_LAST_LAST);
    assert_eq!(FRAME_MS * last as u64, SCENARIO_LAST_START_MS);

    // --- WHEN it is delivered to `signal`, in file order. ----------------
    let mut s = Signal::new();
    for block in samples.chunks_exact(BLOCK) {
        s.push(block.try_into().unwrap());
    }
    let frames = s.frames();

    // --- THEN exactly 125 frames result, frame 0 to frame 124. -----------
    assert_eq!(frames.len(), SCENARIO_FRAMES, "number of frames");
    for (i, f) in frames.iter().enumerate() {
        assert_eq!(f.index, i, "frames are frame 0 to frame {last}, in order");
    }
    // --- AND frame 124 holds samples 47 616 to 47 999, starts at 992 ms. -
    let f = &frames[last];
    assert_eq!(f.index, last);
    assert_eq!(f.first_sample, SCENARIO_LAST_FIRST);
    assert_eq!(f.last_sample, SCENARIO_LAST_LAST);
    assert_eq!(f.start_ms, SCENARIO_LAST_START_MS);
}
