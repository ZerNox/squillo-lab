"""E-001 round 2, step 1: export round 1's inputs and requests for the Rust
build (native and WASM). Crude experiment code.

`uv run python r2_export.py` writes data/cache/r2/: per input <name>.x.f64
(the 48 kHz samples, float64 little-endian) and <name>.<mod>.f64 (the request
in cents at WORLD's frame times k * 5 ms, k = 0 .. floor(n / 240)),
manifest.json, and list.txt (name, samples, timing input 0 or 1). Inputs and
requests are round 1's (run.load, run.request), unchanged:
24 synthetic phrases and 19 VocalSet singers.

Conditions asserted on what is written (squillo standing instruction S15):
every sample finite and |x| <= 1; sample rate 48 kHz; duration within round
1's stated span (synthetic 4.05 s, VocalSet 5.5 to 18.3 s); every request
finite; |request| <= 50 cents except synthetic s100, whose wobble round 1
scales to 10 cents RMS over the whole phrase and does not clip (its RMS is
asserted instead, on the phrase's own samples); `id` identically zero; c100
and s100 not identically zero on any input.
"""

import json
import sys

import numpy as np

import run

MODS = ("id", "c100", "s100")
OUT = run.CACHE / "r2"
FRAME = 0.005
TIMING = ("bass_plain_1", "tenor_plain_1", "soprano_high_plain_1", "m1", "m8", "f1", "f5", "f9")


def check(ok, what):
    if not ok:
        sys.exit(f"S15 condition failed: {what}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    for inp in run.synthetic_inputs() + run.real_inputs():
        x, grid = run.load(inp)
        x = np.ascontiguousarray(x, dtype="<f8")
        dur = len(x) / run.SR
        check(np.isfinite(x).all() and np.abs(x).max() <= 1.0, f"{inp['name']}: samples finite, |x| <= 1")
        lo, hi = (4.05, 4.05) if inp["kind"] == "synthetic" else (5.5, 18.3)
        check(lo - 0.01 <= dur <= hi + 0.05, f"{inp['name']}: duration {dur:.3f} s outside {lo}-{hi}")
        x.tofile(OUT / f"{inp['name']}.x.f64")
        t = np.arange(len(x) // 240 + 1) * FRAME
        for mod in MODS:
            s = np.ascontiguousarray(run.request(grid, mod)(t), dtype="<f8")
            check(np.isfinite(s).all(), f"{inp['name']} {mod}: request finite")
            if inp["kind"] == "synthetic" and mod == "s100":
                rms = np.sqrt(np.mean(run.request(grid, mod)(grid["t"]) ** 2))
                check(abs(rms - 10.0) < 1e-6, f"{inp['name']} s100: RMS {rms} != 10 cents")
            else:
                check(np.abs(s).max() <= 50.0 + 1e-9, f"{inp['name']} {mod}: |request| <= 50")
            check((mod == "id") == (np.abs(s).max() == 0.0), f"{inp['name']} {mod}: zero iff id")
            s.tofile(OUT / f"{inp['name']}.{mod}.f64")
        manifest.append(dict(name=inp["name"], kind=inp["kind"], n=len(x), seconds=dur,
                             frames=len(t), timing=inp["name"] in TIMING))
        print(inp["name"], f"{dur:.2f} s", flush=True)
    check(sum(m["timing"] for m in manifest) == len(TIMING), "every timing input present")
    (OUT / "list.txt").write_text("".join(f"{m['name']} {m['n']} {int(m['timing'])}\n" for m in manifest))
    (OUT / "manifest.json").write_text(json.dumps(dict(sr=run.SR, frame_s=FRAME, mods=MODS, inputs=manifest), indent=1))


if __name__ == "__main__":
    main()
