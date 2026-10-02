"""E-001 needs-human step: build a blind listening set from your own takes.

    uv run python listen.py take1.wav take2.wav take3.wav

Each take (mono or stereo WAV, any rate, about 10 s) gives six clips: the
original, WORLD (Harvest) with no change, with 50 % and 100 % note-centre
correction and with the wobble removed, and PSOLA with 100 % correction.
Two originals are repeated as a consistency check: 20 clips for three takes.
Clips go to data/cache/listening/ in shuffled order, with ratings.csv to fill
in and key.json (do not open it until the ratings are done). Nothing here is
committed: data/cache/ is ignored, and the takes stay on this machine.

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

VARIANTS = [("original", None, None), ("world_harvest", "id", "world id"),
            ("world_harvest", "c50", "world c50"), ("world_harvest", "c100", "world c100"),
            ("world_harvest", "s100", "world s100"), ("psola", "c100", "psola c100")]


def main(paths):
    out = run.CACHE / "listening"
    out.mkdir(parents=True, exist_ok=True)
    clips = []
    for p in paths:
        x, sr = sf.read(p, dtype="float64", always_2d=True)
        x = x.mean(axis=1)
        g = gcd(sr, run.SR)
        x = resample_poly(x, run.SR // g, sr // g)
        x = 0.5 * x / np.abs(x).max()
        tmp = run.CACHE / "listen_input.wav"
        sf.write(tmp, x, run.SR)
        _, grid = run.load(dict(kind="vocalset", path=str(tmp)))
        analyses = {}
        for method, mod, label in VARIANTS:
            if method == "original":
                y = x
            else:
                a = analyses.setdefault(method, resynth.analyse(method, x))
                y = resynth.synthesize(a, run.request(grid, mod))
            for _ in range(4):  # the -70 LKFS gate is absolute, so one gain step can move blocks across it
                y = y * 10 ** ((bs1770(x) - bs1770(y)) / 20)
            assert abs(bs1770(y) - bs1770(x)) < 0.001, (p, label)
            clips.append((Path(p).name, "original" if mod is None else label, y))
    clips += [c for c in clips if c[1] == "original"][:2]
    top = max(1.0, max(np.abs(c[2]).max() for c in clips))
    clips = [(t, lab, y / top) for t, lab, y in clips]
    order = np.random.default_rng().permutation(len(clips))
    key = {}
    with open(out / "ratings.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["clip", "same_person_as_you_1to5", "natural_1to5", "notes"])
        for k, i in enumerate(order, 1):
            name = f"clip{k:02d}.wav"
            take, label, y = clips[i]
            sf.write(out / name, y, run.SR)
            key[name] = dict(take=take, variant=label)
            w.writerow([name, "", "", ""])
    (out / "key.json").write_text(json.dumps(key, indent=1))
    print(f"{len(clips)} clips in {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
