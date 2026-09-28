"""E-001 fold 2 (squillo iteration 43, F-043 k and m): the rung compared sample
by sample in Chrome and Firefox, and fold 1's run repeated. Crude experiment code.

    node f2_run.mjs                    # data/cache/f2/<browser>/p<pass>/<input>.<request>.f64|.f32
    uv run python f2_compare.py        # results/f2/compare.json

Fold 1 (iteration 37) called the rung the same in both browsers from equal
32-bit FNV-1a hashes (f1_page/worker.js:11-16), which R-08 found is an
inference, not a comparison (F-043 k). Here every pair of the four copies of
each rung (two browsers, two passes) is compared sample by sample, as f64 and
as f32, by numpy array equality of the raw bytes read as float arrays.

Rules, written before the run:
- Same: equal length and every sample bitwise equal (the bytes equal).
- The comparison is checked (S15): it must pass a copy with itself, and must
  fail a copy with one sample's lowest mantissa bit flipped (a difference of
  one ulp, the least there is) and the native x86-64 output, which fold 1
  found differs by at most 3.5e-12 to 4.9e-10 (results/f1/fold.json
  `browsers.*.rows[].vs_native.max_abs_diff`).
- The FNV-1a hash of each copy (f1_page/worker.js:11-16, reimplemented) must
  equal fold 1's recorded hash for the same input and request, so this run
  is the same computation as fold 1's.
- Each browser's f32 output must be its f64 output rounded to f32.
- Added in squillo iteration 47 (F-050 c): the last two were recorded and
  not asserted. Both are now asserted on every rung, and each is checked
  first (S15): it must pass the first rung's Chrome copy as read, and must
  fail the same copy with one sample's lowest mantissa bit flipped (the f32
  file for the rounding check, the f64 bytes for the hash check), an input
  that differs from the must-pass case by one ulp.
- Time: first rung (the faster pass's analysis plus the slowest request's
  faster synthesis, as f1_fold.py's summary) compared with fold 1's, the
  relative difference reported per browser and input.
"""
import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
CACHE = HERE / "data/cache"
F1 = HERE / "results/f1"
OUT = HERE / "results/f2"
BROWSERS = ("chrome", "firefox")


def check(ok, what):
    if not ok:
        sys.exit(f"CHECK FAILED: {what}")


def fnv1a(b: bytes) -> str:
    h = 0x811C9DC5
    for x in b:
        h ^= x
        h = (h * 0x01000193) & 0xFFFFFFFF
    return format(h, "x")


def same(a: np.ndarray, b: np.ndarray) -> bool:
    return a.shape == b.shape and a.tobytes() == b.tobytes()


def main():
    rungs = []
    for line in (CACHE / "f1/list.txt").read_text().split("\n"):
        if line.strip():
            name, *reqs = line.split()
            rungs += [(name, r) for r in reqs]
    f1 = {b: json.loads((F1 / f"{b}.json").read_text()) for b in BROWSERS}
    f2 = {b: json.loads((OUT / f"{b}.json").read_text()) for b in BROWSERS}
    R = {"versions": {b: f2[b]["version"] for b in BROWSERS}, "check_of_check": {}, "rungs": {}, "time": {}}

    # the check of the check, on the first rung's Chrome pass 0 copy
    n0, r0 = rungs[0]
    a = np.fromfile(CACHE / f"f2/chrome/p0/{n0}.{r0}.f64", "<f8")
    flip = a.copy()
    flip.view("<u8")[len(a) // 2] ^= 1
    nat = np.fromfile(CACHE / f"f1/out/{n0}.{r0}.native.f64", "<f8")
    R["check_of_check"] = dict(
        with_itself=same(a, a.copy()),
        one_ulp_flipped=same(a, flip), one_ulp_abs_diff=float(abs(flip - a).max()),
        native=same(a, nat), native_max_abs_diff=float(abs(nat - a).max()),
        fnv_changes_on_flip=fnv1a(a.tobytes()) != fnv1a(flip.tobytes()))
    c = R["check_of_check"]
    check(c["with_itself"], "comparison passes a copy with itself")
    check(not c["one_ulp_flipped"] and c["one_ulp_abs_diff"] > 0, "comparison fails a one-ulp change")
    check(not c["native"], "comparison fails the native output")

    # F-050 (c): the rounding and fold 1 hash checks, each checked on a case it
    # must pass and one it must fail, which differs from it by one ulp
    f1h0 = {h for b in BROWSERS for row in f1[b]["rows"]
            if row["input"] == n0 and row["request"] == r0 for h in row["f64_hashes"]}
    a32 = np.fromfile(CACHE / f"f2/chrome/p0/{n0}.{r0}.f32", "<f4")
    flip32 = a32.copy()
    flip32.view("<u4")[len(a32) // 2] ^= 1
    c.update(
        rounding_passes_as_read=same(a32, a.astype("<f4")),
        rounding_fails_one_ulp_f32=not same(flip32, a.astype("<f4")),
        f32_flip_differs_in_input=not same(flip32, a32),
        fold1_hash_passes_as_read={fnv1a(a.tobytes())} <= f1h0,
        fold1_hash_fails_one_ulp={fnv1a(flip.tobytes())}.isdisjoint(f1h0),
        f64_flip_differs_in_input=not same(flip, a))
    for k in ("rounding_passes_as_read", "rounding_fails_one_ulp_f32", "f32_flip_differs_in_input",
              "fold1_hash_passes_as_read", "fold1_hash_fails_one_ulp", "f64_flip_differs_in_input"):
        check(c[k], k)

    for name, req in rungs:
        e = {}
        for kind, dt in (("f64", "<f8"), ("f32", "<f4")):
            copies = {f"{b} p{p}": np.fromfile(CACHE / f"f2/{b}/p{p}/{name}.{req}.{kind}", dt)
                      for b in BROWSERS for p in (0, 1)}
            for k, v in copies.items():
                check(np.isfinite(v).all(), f"{name} {req} {k} {kind} finite")
            pairs = {f"{x} = {y}": same(copies[x], copies[y]) for x, y in combinations(copies, 2)}
            e[kind] = dict(samples=len(copies["chrome p0"]), pairs=pairs, all_same=all(pairs.values()))
            if kind == "f64":
                e["f32_is_f64_rounded"] = all(
                    same(copies_f32, v.astype("<f4")) for copies_f32, v in
                    ((np.fromfile(CACHE / f"f2/{k.split()[0]}/{k.split()[1]}/{name}.{req}.f32", "<f4"), v)
                     for k, v in copies.items()))
                hashes = {fnv1a(v.tobytes()) for v in copies.values()}
                f1h = {h for b in BROWSERS for row in f1[b]["rows"]
                       if row["input"] == name and row["request"] == req for h in row["f64_hashes"]}
                e["fnv_f64"] = sorted(hashes)
                e["matches_fold1_hash"] = hashes == f1h
                check(e["f32_is_f64_rounded"], f"{name} {req} f32 is f64 rounded")
                check(e["matches_fold1_hash"], f"{name} {req} matches fold 1's hash")
                nat = np.fromfile(CACHE / f"f1/out/{name}.{req}.native.f64", "<f8")
                e["native_max_abs_diff"] = float(abs(nat - copies["chrome p0"]).max())
        R["rungs"][f"{name} {req}"] = e

    for b in BROWSERS:
        for name in dict(rungs):
            rows1 = [r for r in f1[b]["rows"] if r["input"] == name]
            rows2 = [r for r in f2[b]["rows"] if r["input"] == name]
            sec = rows1[0]["seconds"]
            fr1 = (min(rows1[0]["analysis_s"]) + max(min(r["synth_s"]) for r in rows1)) / sec
            an2 = min(r["analysis_s"] for r in rows2)
            fr2 = (an2 + max(min(r["synth_s"] for r in rows2 if r["request"] == q) for q in {r["request"] for r in rows2})) / sec
            R["time"][f"{b} {name}"] = dict(fold1_first_rung_s_per_s=fr1, fold2_first_rung_s_per_s=fr2,
                                           relative_diff=(fr2 - fr1) / fr1)
    R["summary"] = dict(
        all_same_f64=all(e["f64"]["all_same"] for e in R["rungs"].values()),
        all_same_f32=all(e["f32"]["all_same"] for e in R["rungs"].values()),
        f32_is_f64_rounded=all(e["f32_is_f64_rounded"] for e in R["rungs"].values()),
        all_match_fold1_hash=all(e["matches_fold1_hash"] for e in R["rungs"].values()),
        native_max_abs_diff=max(e["native_max_abs_diff"] for e in R["rungs"].values()),
        samples_compared_per_pair=sum(e["f64"]["samples"] for e in R["rungs"].values()),
        time_relative_diff_range=[min(t["relative_diff"] for t in R["time"].values()),
                                  max(t["relative_diff"] for t in R["time"].values())])
    (OUT / "compare.json").write_text(json.dumps(R, indent=1))
    print(json.dumps({k: R[k] for k in ("versions", "check_of_check", "summary", "time")}, indent=1))


if __name__ == "__main__":
    main()
