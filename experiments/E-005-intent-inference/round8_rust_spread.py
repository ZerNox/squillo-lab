"""Round 8: MT-006/MT-007 `pitch-spread` on the shipped Rust crate (`squillo` crates/metrics,
`spread::measure`, through `examples/take_json`) against this lab's reference (round4.measure,
rule PM, as fold 4 ships it) fed the very same pitch cells, frame times k * 384 / 48000.

Inputs: (a) squillo's 14 wav fixtures; (b) 300 synthetic 14-note takes, fold_refusal.take_sample
(MELODY, TUNING 23 cents, notes of 19 200 samples), deviations N(0, sigma) with sigma in
{0, 5, 10, 15, 20, 30} cents, straight or 5.5 Hz vibrato, 25 per cell, seed = take index;
(c) E-002's 159 WORLD re-syntheses of VocalSet (CC BY 4.0), clean and with white noise at 20 dB
against the take's mean power, seeded per take.

Bar, stated before the run: every take gives the same state and the same segments, and every
value, u and lower end agrees within 1e-6 relative.
Usage: uv run python round8_rust_spread.py /path/to/squillo"""
import json
import math
import subprocess
import sys
import tempfile
import zlib
from multiprocessing import Pool
from pathlib import Path

import numpy as np

import run  # before synth (round2's note)
import fold_refusal as FR
import round4 as R4

SQ = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[3] / "squillo"
BIN = SQ / "target/release/examples/take_json"
R2C = Path(__file__).parent.parent / "E-002-measurement-reliability" / "data" / "cache" / "r2"
OUT = Path(__file__).parent / "results" / "round8_rust_spread.json"
HOP_S = 384 / 48_000


def close(a, b):
    return abs(a - b) <= 1e-6 * (1 + abs(b))


def rust(x):
    with tempfile.NamedTemporaryFile(suffix=".f32") as f:
        f.write(np.asarray(x, "<f4").tobytes()); f.flush()
        return json.loads(subprocess.run([str(BIN), f.name], capture_output=True, check=True, text=True).stdout)


def compare(x):
    r = rust(x)
    c = np.array([np.nan if v is None else v for v in r["p"]])
    t = np.arange(len(c)) * HOP_S
    sp, _, _, r0 = R4.measure(c, t, "PM")
    st = FR.state(sp)
    segs = R4.segment_r(c, r0) if r0 is not None else []
    bad = []
    if st != r["spread"][0]:
        bad.append(f"state {st} vs {r['spread'][0]}")
    elif st == "measured" and not (close(r["spread"][1], sp["s"]) and close(r["spread"][2], sp["uB"])):
        bad.append("value")
    elif st == "at least" and not close(r["spread"][1], sp["s"] - 2 * sp["uB"]):
        bad.append("lower")
    if [list(map(int, s)) for s in segs] != r["segments"]:
        bad.append("segments")
    return dict(state=st, segments=len(segs), bad=bad,
                s=float(sp["s"]) if np.isfinite(sp["s"]) else None)


def synth(i):
    sigma = (0, 5, 10, 15, 20, 30)[i % 6]
    vib = (i // 6) % 2 == 1
    rng = np.random.default_rng(i)
    devs = list(rng.normal(0, sigma, 14)) if sigma else [0.0] * 14
    note = 19_200
    n = FR.GAP + 14 * (note + FR.GAP)
    x = np.array([FR.take_sample(k, devs, note, vib) for k in range(n)], np.float32)
    return f"synth-{i}-s{sigma}-{'vib' if vib else 'straight'}", compare(x)


def real(stem):
    z = np.load(R2C / (stem + ".npz"))
    y = z["y"].astype(np.float64)
    rng = np.random.default_rng(zlib.crc32(stem.encode()))
    nz = rng.standard_normal(len(y))
    nz *= math.sqrt(np.mean(y ** 2) / np.mean(nz ** 2) / 10 ** 2.0)
    return stem, dict(clean=compare(y), white20=compare(y + nz))


def fixture(p):
    import soundfile as sf
    x, sr = sf.read(p, dtype="float32")
    return p.name, compare(x[:, 0] if x.ndim > 1 else x)


def main():
    fx = sorted((SQ / "fixtures").rglob("*.wav"))
    with Pool(18) as pool:
        f = dict(pool.map(fixture, fx))
        s = dict(pool.map(synth, range(300)))
        r = dict(pool.map(real, sorted(p.stem for p in R2C.glob("*.npz"))))
    rows = dict(fixtures=f, synthetic=s, **{k: {st: v[k] for st, v in r.items()} for k in ("clean", "white20")})
    summ = {}
    for k, d in rows.items():
        summ[k] = dict(takes=len(d), agree=sum(not v["bad"] for v in d.values()),
                       states={st: sum(v["state"] == st for v in d.values()) for st in ("measured", "at least", "uncertain")},
                       disagree={n: v["bad"] for n, v in d.items() if v["bad"]})
    summ["fixtures_rows"] = f
    OUT.write_text(json.dumps(summ, indent=1))
    print(json.dumps({k: v for k, v in summ.items() if k != "fixtures_rows"}, indent=1))


if __name__ == "__main__":
    main()
