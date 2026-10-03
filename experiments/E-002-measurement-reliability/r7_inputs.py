"""E-002 round 7, step 1 (squillo iteration 92): the inputs and numpy's outputs.

Writes data/cache/r7/in/<name>.f32 (little-endian float32 samples, 48 kHz),
data/cache/r7/in/list.txt and sets.json, and numpy's YIN outputs in the
format the Rust build writes (three float64 arrays per input: f0 in Hz or
NaN, the CMND at the chosen lag, the chosen whole lag or -1) to
data/cache/r7/out/numpy/<variant>/<name>.f64:

- numpy/f64-fft: yin.py in float64, the reference every target is compared with;
- numpy/f32-fft: yin.py in float32, the host path of round 1's result 9.

Inputs (three sets; every input is float32 samples, as squillo ADR 0002
delivers them):

- `fix`: squillo's eleven fixtures/signal/*.wav, byte for byte, each
  SHA-256 checked against squillo's fixtures/MANIFEST.md before use.
- `syn`: round 1's tone generator (run.py `tone`, lines 30-80: additive
  synthesis, peak 0.5, random harmonic phases, harmonics above 20 kHz
  dropped; `add_noise`, white Gaussian at an SNR against the tone's RMS),
  seed 20261003: the 41 semitones E2..C6, pure and saw12 (-12 dB/octave)
  clean, as round 1's result 9, and saw12 at 20 and 10 dB SNR, where round
  1's result 4 shows frames near YIN's threshold.
- `voc`: VocalSet originals as round 2 resampled them to 48 kHz (r2_truth.py
  line 72, resample_poly 160/147; saved float32, line 112), the first take
  in sorted order of each of the 20 singers.

Crude experiment code. `uv run python r7_inputs.py <squillo>`.
"""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).parent
GUARDED = ("r7_inputs.py", "yin.py", "run.py")


def committed_first():
    """S15 (C15): refuse to run on an uncommitted edit of this file or of the modules whose rules it runs."""
    for me in GUARDED:
        a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
        b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", me], cwd=HERE)
        if a.returncode or b.returncode:
            sys.exit(f"{me} is not committed as it stands: commit the rules before running")


if __name__ == "__main__":
    committed_first()

import run  # noqa: E402  round 1's generator (tone, add_noise); importing runs nothing
import yin  # noqa: E402
from yin import SR, HOP, E2, C6  # noqa: E402

CACHE = HERE / "data" / "cache" / "r7"
SEED = 20261003
SNRS = (20.0, 10.0)  # dB; round 1 result 4: 20 dB max error 19.6 cents, 10 dB 1.75 % gross
N_SINGERS = 20  # VocalSet's singers (round 2: 159 takes, 20 singers)


def yin_lag(x, dtype):
    """yin.yin's own loop (yin.py lines 74-97), also returning the whole lag.

    Checked equal to yin.yin, f0 and dmin bit for bit, on every input (check
    `reference_equals_yin_py`)."""
    idx, win = yin.frame_windows(np.asarray(x))
    tau_min = int(np.floor(SR / 3000.0))
    tau_max = int(np.ceil(SR / 63.0)) + 1
    d, dn = yin.cmnd(win, tau_max, dtype)
    f0 = np.full(len(idx), np.nan)
    dmin = np.full(len(idx), np.nan)
    lag = np.full(len(idx), -1.0)
    for k in range(len(idx)):
        row = dn[k]
        below = np.nonzero(row[tau_min:tau_max] < 0.1)[0]
        if len(below) == 0:
            dmin[k] = row[tau_min:tau_max].min()
            continue
        t = tau_min + below[0]
        while t + 1 < tau_max and row[t + 1] < row[t]:
            t += 1
        dmin[k] = row[t]
        lag[k] = t
        if t <= tau_min or t >= tau_max - 1:
            continue
        f0[k] = SR / yin.parabola(d[k].astype(np.float64), t)
    return f0, dmin, lag


def same_bits(a, b):
    """Equal as float64 bit patterns, every NaN taken as one value."""
    a, b = np.asarray(a, np.float64), np.asarray(b, np.float64)
    if a.shape != b.shape:
        return False
    na, nb = np.isnan(a), np.isnan(b)
    return bool(np.array_equal(na, nb) and np.array_equal(a[~na].view(np.uint64), b[~nb].view(np.uint64)))


def manifest_hashes(squillo):
    out = {}
    for line in (squillo / "fixtures" / "MANIFEST.md").read_text().splitlines():
        m = re.match(r"\| (fixtures/signal/\S+\.wav) \| ([0-9a-f]{64}) \|", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def fixtures(squillo):
    want = manifest_hashes(squillo)
    files = sorted((squillo / "fixtures" / "signal").glob("*.wav"))
    assert len(files) == len(want) == 11, (len(files), len(want))
    out = {}
    for p in files:
        rel = f"fixtures/signal/{p.name}"
        raw = p.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == want[rel], f"{rel}: SHA-256 differs from MANIFEST.md"
        bad = bytearray(raw); bad[-1] ^= 1  # C10 must-fail: one sample's last byte changed
        assert hashlib.sha256(bytes(bad)).hexdigest() != want[rel], f"{rel}: must-fail hash matched"
        x, sr = sf.read(p, dtype="float32", always_2d=True)
        info = sf.info(p)
        assert sr == SR and x.shape[1] == 1 and info.subtype == "FLOAT", (rel, sr, x.shape, info.subtype)
        out["fix_" + p.stem] = x[:, 0]
    return out


def synthetic():
    run.rng = np.random.default_rng(SEED)
    out, f0s = {}, {}
    for k, f0 in enumerate(E2 * 2 ** (np.arange(0, 41) / 12)):
        assert E2 * (1 - 1e-12) <= f0 <= C6 * (1 + 1e-12), f0
        for cond in ("pure", "saw12", "saw12_20dB", "saw12_10dB"):
            timbre = cond.split("_")[0]
            x, f = run.tone(timbre, f0)
            assert np.all(f == f0)
            peak = np.max(np.abs(x))
            assert abs(peak - 0.5) <= 4 * np.finfo(float).eps, peak  # render() normalises to 0.5
            if cond.endswith("dB"):
                snr = float(cond.split("_")[1][:-2])
                y = run.add_noise(x, snr)
                n = y - x
                got = 10 * np.log10(np.mean(x ** 2) / np.mean(n ** 2))
                assert abs(got - snr) < 1e-9, (cond, got)  # SNR read from the output, not the parameter
                x = y
            name = f"syn_{cond}_{k:02d}"
            out[name] = x.astype(np.float32)
            f0s[name] = float(f0)
    return out, f0s


def vocalset():
    stems = sorted(p.stem for p in (HERE / "data" / "cache" / "r2").glob("*.npz"))
    first = {}
    for s in stems:
        m = re.match(r"([fm]\d+)_", s)
        if m and m.group(1) not in first:
            first[m.group(1)] = s
    assert len(first) == N_SINGERS, sorted(first)
    out = {}
    for singer, s in sorted(first.items()):
        x = np.load(HERE / "data" / "cache" / "r2" / f"{s}.npz")["x"]
        assert x.dtype == np.float32 and x.ndim == 1 and len(x) > 4 * HOP
        out["voc_" + s] = x
    return out


def main():
    squillo = Path(sys.argv[1])
    sets = {}
    inputs = {}
    for set_name, d in (("fix", fixtures(squillo)),):
        inputs.update(d); sets.update({k: set_name for k in d})
    syn, f0s = synthetic()
    inputs.update(syn); sets.update({k: "syn" for k in syn})
    voc = vocalset()
    inputs.update(voc); sets.update({k: "voc" for k in voc})
    for name, x in inputs.items():
        assert x.dtype == np.float32 and np.all(np.isfinite(x)), name
    (CACHE / "in").mkdir(parents=True, exist_ok=True)
    for name, x in inputs.items():
        x.astype("<f4").tofile(CACHE / "in" / f"{name}.f32")
    (CACHE / "in" / "list.txt").write_text("\n".join(inputs) + "\n")

    # numpy's outputs; the lag-returning copy is checked against yin.yin itself first
    checks = {"reference_equals_yin_py": True, "frames": 0}
    for variant, dtype in (("f64-fft", np.float64), ("f32-fft", np.float32)):
        (CACHE / "out" / "numpy" / variant).mkdir(parents=True, exist_ok=True)
        for name, x in inputs.items():
            f0, dmin, lag = yin_lag(x, dtype)
            _, f0_y, dmin_y = yin.yin(x, dtype=dtype)
            ok = same_bits(f0, f0_y) and same_bits(dmin, dmin_y)
            assert ok, f"{variant} {name}: the lag-returning copy differs from yin.yin"
            checks["frames"] += len(f0)
            np.concatenate([f0, dmin, lag]).astype("<f8").tofile(CACHE / "out" / "numpy" / variant / f"{name}.f64")
    # C10 must-fail for the check above: the copy on one input against yin.yin on another
    a = yin_lag(inputs["fix_sine-220hz"], np.float64)
    _, bf, bd = yin.yin(inputs["fix_sine-c6"], dtype=np.float64)
    assert not (same_bits(a[0], bf) and same_bits(a[1], bd)), "must-fail: different inputs compared equal"
    checks["reference_must_fail_detected"] = True

    meta = {
        "sets": sets, "f0": f0s, "seed": SEED, "snrs_db": SNRS,
        "samples": {k: int(len(v)) for k, v in inputs.items()},
        "numpy": np.__version__, "python": sys.version.split()[0],
        "checks": checks,
    }
    (CACHE / "in" / "sets.json").write_text(json.dumps(meta, indent=1))
    n = {s: sum(1 for v in sets.values() if v == s) for s in ("fix", "syn", "voc")}
    frames = {s: sum(len(inputs[k]) // HOP - 3 for k, v in sets.items() if v == s) for s in n}
    print("inputs", n, "frames", frames, "checks", checks)


if __name__ == "__main__":
    main()
