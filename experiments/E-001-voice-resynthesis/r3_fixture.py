"""E-001 round 3, a fixture for squillo's SY-008 (iteration 67): a request for a take too quiet
to level. Crude experiment code.

    uv run python r3_fixture.py <squillo>/fixtures   # writes synthesis/request-silence-1s.json

Conditions, written before generating (S15), each asserted on what is read or written:
- the take is squillo's `fixtures/signal/silence.wav`, read as it is committed: 48 000 samples,
  every one 0.0, so 125 frames of 384 (SG-002) and no frame whose pitch `metrics` measures
  (f1_fold.measure gives none);
- under ITU-R BS.1770-4 (round 3's `blocks`, `lk`) no 400 ms block of it lies above the absolute
  gate of -70 LKFS, so its integrated loudness is undefined;
- the request: 125 entries, every one `null` (no change on a frame with no measured pitch, SY-002),
  written as f1_fold writes every request (`request_json`: json.dumps, two-space indent, one
  trailing newline).
"""
import hashlib
import sys
from pathlib import Path

import numpy as np

import f1_fold
from r3_loudness import blocks, lk

fix = Path(sys.argv[1])
x = f1_fold.read_wav(fix / "signal" / "silence.wav")
assert len(x) == 48_000 and not np.any(x), "silence.wav: 48 000 zero samples"
n = len(x) // 384
assert n == 125
c, _, _, _ = f1_fold.measure(x)
assert not np.isfinite(c).any(), "no measured frame"
with np.errstate(divide="ignore"):
    assert not np.any(lk(blocks(x)) > -70.0), "no block above the absolute gate"
b = f1_fold.request_json([None] * n)
(fix / "synthesis" / "request-silence-1s.json").write_bytes(b)
print(dict(entries=n, blocks=len(blocks(x)), bytes=len(b), sha256=hashlib.sha256(b).hexdigest()))
