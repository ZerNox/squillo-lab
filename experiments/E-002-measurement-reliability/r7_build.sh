#!/usr/bin/env bash
# E-002 round 7, step 2: build wasm/ natively and for WASM, plain and with
# SIMD (simd128, which rustfft's wasm_simd feature uses when enabled), as
# E-001 round 2's r2_build.sh. Needs prereqs.sh's Rust, wasm32 target and
# wasm-bindgen-cli 0.2.129.
set -euo pipefail
cd "$(dirname "$0")/wasm"
export PATH="$HOME/.cargo/bin:$PATH"
cargo build --release --bins
cargo build --release --lib --target wasm32-unknown-unknown
wasm-bindgen --target web --out-dir pkg target/wasm32-unknown-unknown/release/e002.wasm
RUSTFLAGS="-C target-feature=+simd128" cargo build --release --lib --target wasm32-unknown-unknown --target-dir target-simd
wasm-bindgen --target web --out-dir pkg-simd target-simd/wasm32-unknown-unknown/release/e002.wasm
ls -l pkg/e002_bg.wasm pkg-simd/e002_bg.wasm
