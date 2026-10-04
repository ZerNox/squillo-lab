"""E-001 needs-human step: build a blind A/B listening set from your own takes.

    uv run python listen.py take1.wav take2.wav take3.wav

Eight pairs. Each pair is one take's original and one processed version of
it, in random order; the listener answers only "which is the untouched
recording: A, B or can't tell". Rating one's own voice 1-5 for *same person*
and *natural* over 20 clips proved close to impossible (Joakim, 2026-10-04),
and a forced choice is the easier and stronger question: if the singer
cannot pick the original, the processing is convincing (VISION 12.1).

The pairs (PAIRS below): WORLD (Harvest) with no change and with 100 %
note-centre correction on all three takes, PSOLA with 100 % correction on
take 2, and WORLD with the correction exaggerated to 300 % on take 2 (every
note pushed past its centre). The last is the control: it should be heard,
so a listener who also "can't tell" it was not hearing differences at all.
The first set (2026-09-29) used 50 % and 100 % correction and steadying as
1-5 ratings; on a singer within about 10 to 30 cents of the notes those
changes were below what one hears.

Clips go to data/cache/listening/ as pairNN-a.wav and pairNN-b.wav, with
ratings.csv to fill in and key.json (do not open it until the answers are
done). Nothing here is committed: data/cache/ is ignored, and the takes stay
on this machine.

Every clip is levelled to its take's integrated loudness (ITU-R BS.1770-4, round 3's
`r3_loudness.bs1770`), since round 3 found WORLD's output 1.1-4.8 LU louder than its input
on real voices, enough to tell the clips apart, or to prefer one, by loudness alone
(squillo F-063, iteration 66). If a levelled clip would exceed full scale, every clip is
scaled down by the same factor, so their levels stay equal. The gain is applied until the
levels agree within 0.001 LU: BS.1770's absolute gate does not move with the gain, so one
step can leave a clip short (0.045 LU on a VocalSet take).
"""

import csv
import json
import sys
from math import gcd
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

import resynth
import run
from r3_loudness import bs1770

# (take index, method, mod, label): the processed side of each pair
PAIRS = [(i, "world_harvest", "id", "world id") for i in range(3)] + \
        [(i, "world_harvest", "c100", "world c100") for i in range(3)] + \
        [(1, "psola", "c100", "psola c100"), (1, "world_harvest", "c300", "world c300 (control)")]


def request(grid, mod):
    """run.request, plus the listening set's large changes: c300 is -3 times
    the note-centre offset, up200 a constant +200 cents."""
    if mod == "c300":
        s = -3.0 * grid["offset"]
    elif mod == "up200":
        s = np.full_like(grid["t"], 200.0)
    else:
        return run.request(grid, mod)
    return lambda tt: np.interp(tt, grid["t"], s)


def main(paths):
    out = run.CACHE / "listening"
    out.mkdir(parents=True, exist_ok=True)
    for old in list(out.glob("clip*.wav")) + list(out.glob("pair*.wav")):
        old.unlink()
    takes, grids, analyses = [], [], {}
    for p in paths:
        x, sr = sf.read(p, dtype="float64", always_2d=True)
        x = x.mean(axis=1)
        g = gcd(sr, run.SR)
        x = resample_poly(x, run.SR // g, sr // g)
        x = 0.5 * x / np.abs(x).max()
        tmp = run.CACHE / "listen_input.wav"
        sf.write(tmp, x, run.SR)
        _, grid = run.load(dict(kind="vocalset", path=str(tmp)))
        takes.append(x)
        grids.append(grid)
    pairs = []
    for i, method, mod, label in PAIRS:
        x = takes[i]
        a = analyses.setdefault((i, method), resynth.analyse(method, x))
        y = resynth.synthesize(a, request(grids[i], mod))
        for _ in range(4):  # the -70 LKFS gate is absolute, so one gain step can move blocks across it
            y = y * 10 ** ((bs1770(x) - bs1770(y)) / 20)
        assert abs(bs1770(y) - bs1770(x)) < 0.001, (paths[i], label)
        pairs.append((Path(paths[i]).name, label, x, y))
    top = max(1.0, max(max(np.abs(x).max(), np.abs(y).max()) for _, _, x, y in pairs))
    rng = np.random.default_rng()
    key = {}
    with open(out / "ratings.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pair", "untouched_is", "notes"])
        for k, i in enumerate(rng.permutation(len(pairs)), 1):
            take, label, x, y = pairs[i]
            real = "A" if rng.random() < 0.5 else "B"
            a, b = (x, y) if real == "A" else (y, x)
            sf.write(out / f"pair{k:02d}-a.wav", a / top, run.SR)
            sf.write(out / f"pair{k:02d}-b.wav", b / top, run.SR)
            key[f"pair{k:02d}"] = dict(take=take, variant=label, untouched_is=real)
            w.writerow([f"pair{k:02d}", "", ""])
    (out / "key.json").write_text(json.dumps(key, indent=1))
    print(f"{len(pairs)} pairs in {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
