#!/usr/bin/env bash
# Lab prerequisites, installed for the current user only: no sudo, no system
# packages. Idempotent: each step checks first and installs only what is missing.
# The squillo runner runs this before every iteration, so an iteration that needs
# a new tool adds a step here and commits it, and the next run has the tool.
#
#   ./prereqs.sh           install what is missing
#   ./prereqs.sh --check   report only; exit 1 if anything is missing
set -euo pipefail

CHECK=0
[ "${1:-}" = "--check" ] && CHECK=1
export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
missing=0

# step NAME CHECK-COMMAND INSTALL-COMMAND
step() {
  if bash -c "$2" >/dev/null 2>&1; then
    echo "ok       $1"
  elif [ "$CHECK" = 1 ]; then
    echo "MISSING  $1"; missing=1
  else
    echo "install  $1"
    bash -c "$3"
    bash -c "$2" >/dev/null 2>&1 || { echo "FAILED   $1"; exit 1; }
  fi
}

# Present on the host; the lab relies on them but does not install them.
for c in git node npm python3; do
  command -v "$c" >/dev/null || { echo "MISSING  $c (host tool; ask Joakim)"; missing=1; }
done

step "uv" "command -v uv" \
  "curl -LsSf https://astral.sh/uv/install.sh | sh"

# Rust with the WASM target: E-001's on-device synthesis timing and the engine
# path in the browser (F-022). Minimal profile; rustup leaves shell files alone.
step "rustup" "command -v rustup" \
  "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --no-modify-path"
step "rust stable" "rustc --version" \
  "rustup toolchain install stable --profile minimal && rustup default stable"
step "wasm32-unknown-unknown" "rustup target list --installed | grep -qx wasm32-unknown-unknown" \
  "rustup target add wasm32-unknown-unknown"
# JS bindings for a WASM module; its version must match the crate's wasm-bindgen.
step "wasm-bindgen-cli" "command -v wasm-bindgen" \
  "cargo install --locked wasm-bindgen-cli"

# Playwright's own Chromium, for experiments that pin it (installed Chrome and
# Firefox are used too; see README, Browsers).
step "playwright chromium" "ls -d $HOME/.cache/ms-playwright/chromium-* | grep -q ." \
  "npx --yes playwright install chromium"

[ "$missing" = 0 ] || exit 1
