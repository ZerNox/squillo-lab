#!/usr/bin/env bash
# Removes the music from a recording so only the voice is left, before loading it into the page.
# Usage: ./separate-vocals.sh <song.mp3|m4a|wav> [out-dir]   -> <out-dir>/htdemucs/<name>/vocals.mp3
# Demucs v4 (htdemucs, MIT licence), two stems, on the CPU. Pinned versions: newer torch/torchaudio
# break demucs' audio loading, and numpy 2 breaks torch 2.1. Expect faint music bleed in loud parts.
set -euo pipefail
in="${1:?usage: separate-vocals.sh <audio file> [out-dir]}"; out="${2:-separated}"
uvx --python 3.11 --with torchaudio==2.1.2 --with torch==2.1.2 --with soundfile --with "numpy<2" \
  demucs --two-stems=vocals --mp3 -o "$out" "$in"
find "$out" -name 'vocals.mp3' -newer "$in"
