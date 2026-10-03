#!/usr/bin/env bash
# E-007: make the cold-start snapshot. Both repositories as committed at
# the given revisions, with no .git and no E-007 folder, so the subagent
# sees neither this experiment's rules nor history beyond the files.
set -euo pipefail
SQ_REV=${1:?squillo revision}; LAB_REV=${2:?squillo-lab revision}  # $3: test folder, default test1
HERE=$(cd "$(dirname "$0")/../../.." && pwd)        # squillo-lab
SQ=$(cd "$HERE/../squillo" && pwd)
rm -rf /tmp/e007 && mkdir -p /tmp/e007/squillo /tmp/e007/squillo-lab
git -C "$SQ" archive "$SQ_REV" | tar -x -C /tmp/e007/squillo
git -C "$HERE" archive "$LAB_REV" | tar -x -C /tmp/e007/squillo-lab
rm -rf /tmp/e007/squillo-lab/experiments/E-007-cold-start
# Test 1's lab revision predates E-007, so its INDEX could not name it.
# From test 2 the INDEX row (a one-line result) stays, as squillo's
# STATUS.md and findings name test 1 too; the rules and test1/ are gone.
[ -d /tmp/e007/squillo-lab/experiments/E-007-cold-start ] && { echo "E-007 folder left"; exit 1; }
TEST=${3:-test1}
mkdir -p /tmp/e007/squillo-lab/experiments/E-007-cold-start/$TEST
echo "snapshot: squillo $(git -C "$SQ" rev-parse "$SQ_REV"), squillo-lab $(git -C "$HERE" rev-parse "$LAB_REV")"
