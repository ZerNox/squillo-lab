#!/usr/bin/env bash
# Adds generated coach clips to the page: ./add-clips.sh <folder with <pose>.mp4 files>
# Strips the sound, crops to 3:4 portrait at 480x640, compresses to H.264 for
# iPhone and every browser, plus a VP9 WebM fallback, writes page/coach/<pose>.{mp4,webm} and lists the
# poses in COACH_CLIPS in page/index.html. Then commit and push to main.
set -euo pipefail
src="${1:?usage: add-clips.sh <folder>}"
here="$(cd "$(dirname "$0")" && pwd)"
out="$here/../page/coach"
page="$here/../page/index.html"
mkdir -p "$out"
for pose in idle belly breath yawn point lift jaw nose; do
  f=$(ls "$src"/"$pose".* 2>/dev/null | head -1 || true)
  [ -n "$f" ] || continue
  ffmpeg -hide_banner -loglevel error -y -i "$f" -an -t 8 \
    -vf "crop='min(iw,ih*3/4)':'min(ih,iw*4/3)',scale=480:640,fps=24,format=yuv420p" \
    -c:v libx264 -profile:v main -crf 27 -preset slow -movflags +faststart "$out/$pose.mp4"
  # VP9 copy for browsers without H.264 (Linux WebKit, some Chromium builds); iPhones use the MP4.
  ffmpeg -hide_banner -loglevel error -y -i "$out/$pose.mp4" -an -c:v libvpx-vp9 -crf 38 -b:v 0 -row-mt 1 "$out/$pose.webm"
  echo "added $pose ($(du -k "$out/$pose.mp4" | cut -f1) KB)"
done
poses=$(cd "$out" && ls *.mp4 2>/dev/null | sed 's/\.mp4$//' | sed "s/.*/'&'/" | paste -sd, -)
sed -i "s/^const COACH_CLIPS=\[[^]]*\];/const COACH_CLIPS=[$poses];/" "$page"
grep -n '^const COACH_CLIPS=' "$page"
