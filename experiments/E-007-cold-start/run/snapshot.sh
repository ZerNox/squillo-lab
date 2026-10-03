#!/usr/bin/env bash
# E-007: make the cold-start snapshot. Both repositories as committed at
# the given revisions, with no .git and no E-007 folder, so the subagent
# sees neither this experiment's rules nor history beyond the files.
set -euo pipefail
SQ_REV=${1:?squillo revision}; LAB_REV=${2:?squillo-lab revision}
HERE=$(cd "$(dirname "$0")/../../.." && pwd)        # squillo-lab
SQ=$(cd "$HERE/../squillo" && pwd)
rm -rf /tmp/e007 && mkdir -p /tmp/e007/squillo /tmp/e007/squillo-lab
git -C "$SQ" archive "$SQ_REV" | tar -x -C /tmp/e007/squillo
git -C "$HERE" archive "$LAB_REV" | tar -x -C /tmp/e007/squillo-lab
rm -rf /tmp/e007/squillo-lab/experiments/E-007-cold-start
grep -n 'E-007' /tmp/e007/squillo-lab/INDEX.md && { echo "INDEX names E-007"; exit 1; } || true
mkdir -p /tmp/e007/squillo-lab/experiments/E-007-cold-start
echo "snapshot: squillo $(git -C "$SQ" rev-parse "$SQ_REV"), squillo-lab $(git -C "$HERE" rev-parse "$LAB_REV")"
