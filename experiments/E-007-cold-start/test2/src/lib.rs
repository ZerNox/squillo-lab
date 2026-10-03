//! `signal`: the interface ADR 0023 (*The first test's frame*, F-079) gives
//! SG-002's test, with nothing behind it yet. Its shape is decided by
//! ADR 0023; every name and type here is free (ADR 0023, F-079).
//!
//! - one value per run's stream (SG-001: one stream per run): [`Stream`];
//! - a call that takes the next block of 128 `f32` samples, in order:
//!   [`Stream::push_block`];
//! - after any block, every whole frame so far, each with its index, its
//!   first and last sample, and its start in milliseconds: [`Stream::frames`].
//!
//! Nothing frames the stream yet, so `frames` stays empty: the test compiles,
//! and fails on the scenario's own clause (ADR 0023, F-080).

/// Samples per block as capture delivers them (SG-001, ADR 0002).
pub const BLOCK_LEN: usize = 128;

/// One whole frame of the stream (SG-002).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Frame {
    /// Frame index *i*, counting from 0.
    pub index: u64,
    /// Index of the frame's first sample in the stream.
    pub first_sample: u64,
    /// Index of the frame's last sample in the stream.
    pub last_sample: u64,
    /// The frame's start, in milliseconds after the stream's first sample.
    pub start_ms: u64,
}

/// One run's stream of samples (SG-001).
#[derive(Debug, Default)]
pub struct Stream {
    frames: Vec<Frame>,
}

impl Stream {
    /// A new, empty stream.
    pub fn new() -> Self {
        Self::default()
    }

    /// Delivers the next block of 128 samples, in stream order.
    pub fn push_block(&mut self, _block: &[f32; BLOCK_LEN]) {
        // Not built: nothing frames the stream yet (ADR 0023).
    }

    /// Every whole frame delivered so far, in order.
    pub fn frames(&self) -> &[Frame] {
        &self.frames
    }
}
