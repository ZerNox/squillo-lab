"""E-003 round 2 (squillo iteration 47): the inputs, E-002's long-tone
re-syntheses under two conditions, as 16-bit WAVs for Chrome's fake
microphone. Crude experiment code. Rules in the README, *Round 2*, rule 1.

    uv run --project ../E-002-measurement-reliability python r2_gen.py   # data/cache/r2/in/*.wav, results/r2/inputs.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).parent
E002 = HERE.parent / "E-002-measurement-reliability"
sys.path.insert(0, str(E002))
import r2_truth as T  # noqa: E402
import r2_run as RR  # noqa: E402  (condition(): E-002 r2_run.py lines 97-119)

IN = HERE / "data/cache/r2/in"
OUT = HERE / "results/r2"
SETS = ("long_straight", "long_forte", "long_pp", "long_messa")
CONDS = ("clean", "white-20")
LEVEL_DBFS = -26.0  # ITU-T P.56 nominal active speech level for test signals
PAD = 48_000        # 1.0 s of digital silence before and after
SR = 48_000


def takes():
    return sorted(p.stem for p in T.files() if any(s in p.stem for s in SETS))


def make(stem, cond):
    z = np.load(T.R2 / f"{stem}.npz")
    y, f0 = z["y"].astype(np.float64), z["f0"]
    ft = T.truth_per_sample(f0, len(y))
    voiced = ft > 0
    sig, info = RR.condition(y, voiced, stem, cond)
    g = 10 ** (LEVEL_DBFS / 20) / np.sqrt(np.mean(y[voiced] ** 2))
    x = np.concatenate([np.zeros(PAD), g * sig, np.zeros(PAD)])
    path = IN / f"{stem}.{cond}.wav"
    sf.write(path, x, SR, subtype="PCM_16")
    r, sr = sf.read(path, dtype="float64")
    # rule 1's conditions, asserted on the file as read back
    assert sr == SR and len(r) == len(x)
    step = 1 / 32768
    assert np.abs(r - x).max() <= step, np.abs(r - x).max()
    peak = float(np.abs(r).max())
    assert peak < 1.0, peak
    assert not r[:PAD].any() and not r[-PAD:].any()
    vpad = np.concatenate([np.zeros(PAD, bool), voiced, np.zeros(PAD, bool)])
    clean = np.concatenate([np.zeros(PAD), g * y, np.zeros(PAD)])
    lvl = 20 * np.log10(np.sqrt(np.mean(r[vpad] ** 2))) if cond == "clean" else \
        20 * np.log10(np.sqrt(np.mean(clean[vpad] ** 2)))
    assert abs(lvl - LEVEL_DBFS) <= 0.05, lvl
    out = dict(stem=stem, cond=cond, set=T.set_of(stem), singer=T.singer_of(stem), seconds=len(r) / SR,
               peak=peak, voiced_rms_dbfs=float(lvl), gain=float(g), **info)
    if cond != "clean":
        nz = r - clean  # the noise as written, 16-bit rounding included
        snr = 10 * np.log10(np.mean(clean[vpad] ** 2) / np.mean(nz[PAD:-PAD] ** 2))
        assert abs(snr - 20.0) <= 0.05, snr
        out["snr_file"] = float(snr)
    # the truth, padded to the file: f0 per sample, 0 = unvoiced
    np.save(IN / f"{stem}.truth.npy", np.concatenate([np.zeros(PAD), ft, np.zeros(PAD)]).astype(np.float32))
    return out


def main():
    IN.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    ts = takes()
    assert len(ts) == 80, len(ts)
    rows = [make(s, c) for s in ts for c in CONDS]
    (OUT / "inputs.json").write_text(json.dumps(dict(
        level_dbfs=LEVEL_DBFS, pad_samples=PAD, takes=len(ts), files=len(rows),
        seconds_total=sum(r["seconds"] for r in rows),
        peak_max=max(r["peak"] for r in rows),
        snr_file_range=[min(r["snr_file"] for r in rows if "snr_file" in r), max(r["snr_file"] for r in rows if "snr_file" in r)],
        rows=rows), indent=1))
    print(len(rows), "files", round(sum(r["seconds"] for r in rows)), "s; peak max", max(r["peak"] for r in rows))
    (IN / "list.txt").write_text("\n".join(f"{r['stem']} {r['cond']} {r['set']} {r['seconds']:.4f}" for r in rows) + "\n")


if __name__ == "__main__":
    main()
