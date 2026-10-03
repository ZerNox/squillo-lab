//! Stand-in for squillo's `signal` crate (openspec/specs/signal/spec.md).
//! Only the interface the first test needs; nothing frames a stream yet,
//! which is why squillo ADR 0023's first test fails.

/// Samples per block, as capture delivers them (SG-001, ADR 0002).
pub const BLOCK: usize = 128;

/// One frame of the stream (SG-002).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Frame {
    /// Frame index, counting from 0.
    pub index: usize,
    /// Index of the frame's first sample in the stream.
    pub first_sample: usize,
    /// Index of the frame's last sample in the stream (inclusive).
    pub last_sample: usize,
    /// The frame's start, in whole milliseconds from the stream's first sample.
    pub start_ms: u64,
}

/// One run's stream (SG-001: one stream of samples per run).
#[derive(Debug, Default)]
pub struct Signal {
    frames: Vec<Frame>,
}

impl Signal {
    pub fn new() -> Self {
        Self::default()
    }

    /// Deliver the next 128-sample block, in stream order.
    pub fn push(&mut self, _block: &[f32; BLOCK]) {
        // Not built: nothing frames a stream yet.
    }

    /// Every whole frame the samples delivered so far make.
    pub fn frames(&self) -> &[Frame] {
        &self.frames
    }
}
