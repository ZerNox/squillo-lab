//! `signal` (squillo `openspec/specs/signal/spec.md`): divides one run's
//! capture stream into frames (SG-001, SG-002).
//!
//! The interface's shape is squillo ADR 0023's (*The first test's frame*,
//! F-079): a value for one run's stream; a call that takes the next block of
//! 128 `f32` samples, in order; and, after any block, every whole frame so
//! far, each with its index, its first and last sample's index and its start
//! in milliseconds. Every name and type here is the implementer's free choice.
//!
//! Nothing is behind the interface yet: this is the state in which the first
//! failing test is written (ADR 0023, *Which failure counts*, F-080).

/// Samples in one capture block (SG-001; ADR 0002).
pub const BLOCK_LEN: usize = 128;

/// One frame of the stream (SG-002).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Frame {
    /// Frame index, counting from 0.
    pub index: u64,
    /// Index of the frame's first sample in the stream.
    pub first_sample: u64,
    /// Index of the frame's last sample in the stream.
    pub last_sample: u64,
    /// The frame's start, in milliseconds after the stream's first sample.
    pub start_ms: u64,
}

/// One run's stream (SG-001: one stream per run).
#[derive(Debug, Default)]
pub struct Stream {}

impl Stream {
    /// A new, empty stream for one run.
    pub fn new() -> Self {
        Stream {}
    }

    /// Takes the next block of 128 samples, in stream order (SG-001).
    pub fn push_block(&mut self, _block: &[f32; BLOCK_LEN]) {}

    /// Every whole frame so far, in index order (SG-002).
    pub fn frames(&self) -> Vec<Frame> {
        Vec::new()
    }
}
