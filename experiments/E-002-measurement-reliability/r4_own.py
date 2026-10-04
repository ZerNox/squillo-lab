"""E-002 round 4, needs-human step: the ring ratio between separate takes of one scale
(squillo iteration 49). VocalSet holds no second take of the same material, so round 4's
rendition term tau came from the halves of one take. Crude experiment code.

    uv run python r4_own.py same1.wav same2.wav ring1.wav

same1, same2: the same one-octave scale on "ah", sung the same way twice. ring1: the same
scale again with a brighter, more ringing tone. Three takes since 2026-10-04 (four, with a
second ringing take, was too repetitive to sing; Joakim): one no-change pair and two change
pairs. Any sample rate; channels are
averaged. Writes results/own_r4.json (numbers only, never audio). Each pair is compared as
r4_ring.compare does, on whole takes, with the ± fitted on round 4's clean no-change pairs,
both folds pooled (r4_ring.fit over every pair): called changed beyond 2 u.
"""

import json
import pickle
import sys
from math import gcd

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

import r4_ring as R


def load(path):
    x, sr = sf.read(path, always_2d=True)
    x = x.mean(1)
    if sr != R.SR:
        g = gcd(R.SR, sr)
        x = resample_poly(x, R.SR // g, sr // g)
    return x


def model():
    D = pickle.loads(R.OCC.read_bytes())
    pairs = []
    for s in sorted(D):
        a, sp = D[s]["clean"], D[s]["split"]
        p = R.compare(R.side(a, 0, sp), R.side(a, 1, sp))
        if p:
            pairs.append(p)
    return R.fit(pairs)


def main(paths, out=R.OUT / "own_r4.json"):
    names = ["same1", "same2", "ring1"]
    takes = {n: R.analyse_signal(load(p)) for n, p in zip(names, paths)}
    m = model()
    res = dict(model=dict(sigma_w_dB=m[0], tau_dB=m[1]),
               takes={n: dict(occurrences=len(t["occ"]), notes=sorted({o["note"] for o in t["occ"]})) for n, t in takes.items()})
    for a, b, kind in (("same1", "same2", "no change"), ("same1", "ring1", "change"),
                       ("same2", "ring1", "change")):
        p = R.compare(R.side(takes[a]), R.side(takes[b]))
        res[f"{b} - {a}"] = (dict(kind=kind, comparable=False) if p is None else
                             dict(kind=kind, comparable=True, k=p["k"], D_dB=p["D"],
                                  two_u_dB=float(2 * np.sqrt(m[1] ** 2 + m[0] ** 2 / p["k"])),
                                  called_changed=bool(R.called(p, m))))
        r = res[f"{b} - {a}"]  # in plain words, for the page
        r["says"] = ("could not compare these two" if not r["comparable"] else
                     ("measured a change in tone" if r["called_changed"] else "measured no change in tone") +
                     (", as expected" if r["called_changed"] == (kind == "change") else ", not what was expected"))
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:4])
