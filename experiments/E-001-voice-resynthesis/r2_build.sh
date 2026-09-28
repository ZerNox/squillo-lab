#!/usr/bin/env bash
# E-001 round 2, step 2: build the Rust crate natively and for WASM, plain and
# with SIMD (simd128, which rustfft uses when enabled). Needs prereqs.sh's Rust,
# wasm32-unknown-unknown target and wasm-bindgen-cli 0.2.129.
set -euo pipefail
cd "$(dirname "$0")/wasm"
export PATH="$HOME/.cargo/bin:$PATH"
cargo build --release --bin bench
cargo build --release --lib --target wasm32-unknown-unknown
wasm-bindgen --target web --out-dir pkg target/wasm32-unknown-unknown/release/e001.wasm
RUSTFLAGS="-C target-feature=+simd128" cargo build --release --lib --target wasm32-unknown-unknown --target-dir target-simd
wasm-bindgen --target web --out-dir pkg-simd target-simd/wasm32-unknown-unknown/release/e001.wasm
ls -l pkg/e001_bg.wasm pkg-simd/e001_bg.wasm
