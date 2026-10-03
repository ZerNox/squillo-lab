"""E-002 round 7, step 4 (squillo iteration 92): the numeric epsilon across targets.

Reads data/cache/r7/out/<target>/<variant>/<name>.f64 (r7_inputs.py, the
native build, r7_run.mjs) and writes results/r7.json. Every check of a check
runs, and stops the run if it fails, before any hypothesis's outcome is
computed (C10). The rules below were committed before any output existed
(C14); the script refuses to run on an uncommitted edit (C15).

Crude experiment code. `uv run python r7_analyse.py`.
"""

import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
GUARDED = ("r7_analyse.py", "r7_inputs.py")


def committed_first():
    """S15 (C15): refuse to run on an uncommitted edit of this file or of the modules whose rules it runs."""
    for me in GUARDED:
        a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
        b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", me], cwd=HERE)
        if a.returncode or b.returncode:
            sys.exit(f"{me} is not committed as it stands: commit the rules before running")


if __name__ == "__main__":
    committed_first()

from r7_inputs import same_bits  # noqa: E402
from yin import HOP, E2, C6  # noqa: E402

CACHE = HERE / "data" / "cache" / "r7"
OUT = HERE / "results" / "r7.json"

# ---------------------------------------------------------------- rules
VARIANTS = ("f64-direct", "f32-direct", "f64-fft", "f32-fft")
DIRECT = ("f64-direct", "f32-direct")
BROWSER_TARGETS = ("chrome-pkg", "chrome-pkg-simd", "firefox-pkg", "firefox-pkg-simd")
RUST_TARGETS = ("native",) + BROWSER_TARGETS
REFERENCE = ("numpy", "f64-fft")  # yin.py in float64: the reference every output is compared with
NUMPY_F32 = ("numpy", "f32-fft")  # yin.py in float32: round 1 result 9's host path
SETS = ("fix", "syn", "voc")
LAG_MIN, LAG_MAX = 16, 763  # yin.py yin(): floor(48000/3000), ceil(48000/63)+1; a chosen lag lies in [16, 762]
FOUND_THRESHOLD = 0.1  # squillo ADR 0007 (iteration 38): YIN's CMND threshold
REFUSE_APERIODICITY = 0.02  # squillo metrics MT-003, ADR 0004: refused at 0.02 or above (E-002 @ 51f3964)
ACCEPT_MARGIN_CENTS = 3.0  # squillo ADR 0007, Range: accepted within E2..C6 widened by 3 cents
# f64 rounding of 1200 log2(a/b) at a/b near 1: a few units of float64's epsilon in the ratio,
# times 1200 / ln 2 cents per unit of relative difference; 16 units is generous for log2's
# own error (<= 1 ulp) and the division's (0.5 ulp).
CENTS_F64_TOL = 1200 / math.log(2) * 16 * np.finfo(np.float64).eps

HYPOTHESES = {
    "H1": "For each build (pkg, pkg-simd) and each variant, Chrome's and Firefox's outputs are bit-identical "
          "(f0, CMND at the lag, lag) on every frame of every input. Basis: WebAssembly's numeric operations "
          "are IEEE 754 round-to-nearest and deterministic except NaN payloads (WebAssembly Core Specification "
          "2.0, 4.3.3); E-001 round 2 found its outputs bit-identical across both browsers on every input.",
    "H2": "For the direct variants (f64-direct, f32-direct), every browser build's output is bit-identical to "
          "the native build's on every frame. Basis: the direct path uses only +, -, *, / and comparisons, "
          "Rust neither contracts to fused multiply-add nor reassociates floating point, and it calls no libm "
          "function and no runtime-dispatched SIMD; E-001 round 2's native-to-WASM difference (2.7e-11) came "
          "through WORLD's libm calls and rustfft's paths, which the direct path does not use.",
    "H3": "No bar (reported): per target and variant, the largest difference in cents from numpy's float64 "
          "on frames where both chose the same lag, and the counts of frames whose decisions differ (a period "
          "found, the lag chosen, metrics' acceptance). Round 1 result 9 measured numpy float32 against float64 "
          "at 0.0082 cents on clean tones; no rate for noisy or real input exists, so no bar is set (C13).",
}


# ---------------------------------------------------------------- reading and comparing
def load(target, variant, name, nf):
    p = CACHE / "out" / target / variant / f"{name}.f64"
    a = np.fromfile(p, dtype="<f8")
    return a


def split(a, nf):
    return a[:nf], a[nf:2 * nf], a[2 * nf:]


def well_formed(a, nf):
    """3 nf values; every lag -1 or a whole number in [LAG_MIN, LAG_MAX); f0 NaN exactly where no period
    was taken, which includes every lag of -1."""
    if len(a) != 3 * nf:
        return False
    f0, dp, lag = split(a, nf)
    ok_lag = np.all((lag == -1) | ((lag >= LAG_MIN) & (lag < LAG_MAX) & (lag == np.round(lag))))
    return bool(ok_lag and np.all(np.isnan(f0[lag == -1])) and np.all(np.isfinite(dp)))


def cents_abs(a, b):
    return np.abs(1200.0 * np.log2(a / b))


def accepted(f0, dp):
    lo = E2 * 2 ** (-ACCEPT_MARGIN_CENTS / 1200)
    hi = C6 * 2 ** (ACCEPT_MARGIN_CENTS / 1200)
    with np.errstate(invalid="ignore"):
        return (f0 >= lo) & (f0 <= hi) & (dp < REFUSE_APERIODICITY)


def compare(x, y):
    """x, y: (f0, dp, lag) over the same frames. x is the reference."""
    f0x, dpx, lagx = x
    f0y, dpy, lagy = y
    fx, fy = ~np.isnan(f0x), ~np.isnan(f0y)
    found_mismatch = fx != fy
    both_lag = (lagx >= 0) & (lagy >= 0)
    lag_mismatch = both_lag & (lagx != lagy)
    same = fx & fy & (lagx == lagy)
    c = cents_abs(f0y[same], f0x[same])
    ddp = np.abs(dpy[same] - dpx[same])
    acc_flip = accepted(f0x, dpx) != accepted(f0y, dpy)
    lag_flip_cents = cents_abs(f0y[fx & fy & (lagx != lagy)], f0x[fx & fy & (lagx != lagy)])
    return {
        "frames": int(len(f0x)),
        "found_mismatch": int(found_mismatch.sum()),
        "lag_mismatch": int(lag_mismatch.sum()),
        "same_lag_frames": int(same.sum()),
        "max_abs_cents": float(c.max()) if len(c) else None,
        "p99_abs_cents": float(np.percentile(c, 99)) if len(c) else None,
        "max_abs_aperiodicity": float(ddp.max()) if len(ddp) else None,
        "accept_flips": int(acc_flip.sum()),
        "lag_flip_cents_min": float(lag_flip_cents.min()) if len(lag_flip_cents) else None,
        "lag_flip_cents_max": float(lag_flip_cents.max()) if len(lag_flip_cents) else None,
        # how close the reference stood to the rule a flipped frame crossed
        "found_mismatch_ref_dp_from_threshold_max": float(np.max(np.abs(dpx[found_mismatch] - FOUND_THRESHOLD)))
        if found_mismatch.any() else None,
        "accept_flip_ref_dp_from_refusal_max": float(np.max(np.abs(dpx[acc_flip & fx & fy & (lagx == lagy)] - REFUSE_APERIODICITY)))
        if (acc_flip & fx & fy & (lagx == lagy)).any() else None,
    }


def merge(parts):
    """Pool per-input comparisons: counts add, maxima take the max; p99 is recomputed elsewhere."""
    out = {}
    for k in parts[0]:
        vals = [p[k] for p in parts if p[k] is not None]
        if k in ("frames", "found_mismatch", "lag_mismatch", "same_lag_frames", "accept_flips"):
            out[k] = int(sum(vals))
        elif k.endswith("_min"):
            out[k] = min(vals) if vals else None
        elif k.startswith("p99"):
            continue
        else:
            out[k] = max(vals) if vals else None
    return out


def main():
    meta = json.loads((CACHE / "in" / "sets.json").read_text())
    names = (CACHE / "in" / "list.txt").read_text().split()
    nf = {n: meta["samples"][n] // HOP - 3 for n in names}
    outputs = [REFERENCE, NUMPY_F32] + [(t, v) for t in RUST_TARGETS for v in VARIANTS]
    checks = {}

    # ---- checks of the checks, all before any outcome (C10)
    # K1 completeness and form, on every output; must-fail: a real output with its last value dropped
    data = {}
    bad = []
    for o in outputs:
        for n in names:
            p = CACHE / "out" / o[0] / o[1] / f"{n}.f64"
            if not p.exists():
                bad.append(("missing", o, n)); continue
            a = load(o[0], o[1], n, nf[n])
            if not well_formed(a, nf[n]):
                bad.append(("malformed", o, n)); continue
            data[(o, n)] = split(a, nf[n])
    checks["complete_check"] = not bad
    assert checks["complete_check"], bad[:5]
    a0 = load(*REFERENCE, names[0], nf[names[0]])
    checks["complete_must_fail_detected"] = not well_formed(a0[:-1], nf[names[0]])
    assert checks["complete_must_fail_detected"]

    # K2 compare(): must-pass on the reference against itself; must-fail with every f0 raised by
    # 1 cent (max must be 1 cent within float64's rounding) and one found frame made NaN
    ref_v = data[(REFERENCE, "fix_sine-220hz")]
    r = compare(ref_v, ref_v)
    checks["compare_self_check"] = (r["max_abs_cents"] == 0.0 and r["found_mismatch"] == 0
                                    and r["lag_mismatch"] == 0 and r["accept_flips"] == 0)
    assert checks["compare_self_check"], r
    up = (ref_v[0] * 2 ** (1 / 1200), ref_v[1], ref_v[2])
    r = compare(ref_v, up)
    checks["compare_must_fail_cents"] = abs(r["max_abs_cents"] - 1.0) <= CENTS_F64_TOL
    assert checks["compare_must_fail_cents"], r
    k = int(np.flatnonzero(~np.isnan(ref_v[0]))[0])
    holed = (ref_v[0].copy(), ref_v[1], ref_v[2])
    holed[0][k] = np.nan
    r = compare(ref_v, holed)
    checks["compare_must_fail_found"] = r["found_mismatch"] == 1
    assert checks["compare_must_fail_found"], r

    # K3 same_bits(): must-pass on an output and itself, must-fail with one value one ulp away
    checks["bits_self_check"] = same_bits(ref_v[0], ref_v[0])
    assert checks["bits_self_check"]
    nudged = ref_v[0].copy()
    nudged[k] = np.nextafter(nudged[k], np.inf)
    checks["bits_must_fail_detected"] = not same_bits(ref_v[0], nudged)
    assert checks["bits_must_fail_detected"]

    # K4 fidelity: the Rust port chooses yin.py's lag on every frame of squillo's fixtures, in both
    # float64 variants, natively; must-fail: its lags on one fixture against numpy's on another
    fix = [n for n in names if meta["sets"][n] == "fix"]
    fid = {v: all(np.array_equal(data[(("native", v), n)][2], data[(REFERENCE, n)][2]) for n in fix)
           for v in ("f64-direct", "f64-fft")}
    checks["fidelity_check"] = all(fid.values())
    assert checks["fidelity_check"], fid
    checks["fidelity_must_fail_detected"] = not np.array_equal(
        data[(("native", "f64-fft"), "fix_sine-220hz")][2], data[(REFERENCE, "fix_sine-c6")][2])
    assert checks["fidelity_must_fail_detected"]

    # ---- outcomes
    def identical(o1, o2):
        return all(same_bits(data[(o1, n)][i], data[(o2, n)][i]) for n in names for i in range(3))

    h1 = {f"{pkg}/{v}": identical((f"chrome-{pkg}", v), (f"firefox-{pkg}", v))
          for pkg in ("pkg", "pkg-simd") for v in VARIANTS}
    h2 = {f"{t}/{v}": identical(("native", v), (t, v)) for t in BROWSER_TARGETS for v in DIRECT}
    # every pair of Rust targets, every variant: identical or not (beyond H1 and H2)
    pairs = {}
    for v in VARIANTS:
        for i, t1 in enumerate(RUST_TARGETS):
            for t2 in RUST_TARGETS[i + 1:]:
                pairs[f"{t1}~{t2}/{v}"] = identical((t1, v), (t2, v))

    def table(x_of, y_of):
        out = {}
        for s in SETS + ("all",):
            ns = [n for n in names if s == "all" or meta["sets"][n] == s]
            parts = [compare(x_of(n), y_of(n)) for n in ns]
            row = merge(parts)
            cs = []
            for n in ns:
                x, y = x_of(n), y_of(n)
                same = ~np.isnan(x[0]) & ~np.isnan(y[0]) & (x[2] == y[2])
                cs.append(cents_abs(y[0][same], x[0][same]))
            c = np.concatenate(cs)
            row["p99_abs_cents"] = float(np.percentile(c, 99)) if len(c) else None
            row["inputs"] = len(ns)
            out[s] = row
        return out

    epsilon = {}
    for o in [NUMPY_F32] + [(t, v) for t in RUST_TARGETS for v in VARIANTS]:
        epsilon[f"{o[0]}/{o[1]}"] = table(lambda n: data[(REFERENCE, n)], lambda n, o=o: data[(o, n)])
    # across targets, same variant: each browser build against native
    across = {}
    for v in VARIANTS:
        for t in BROWSER_TARGETS:
            across[f"{t}~native/{v}"] = table(lambda n, v=v: data[(("native", v), n)], lambda n, t=t, v=v: data[((t, v), n)])

    timing = {}
    for t in RUST_TARGETS:
        p = CACHE / "out" / t / "timing.json"
        tj = json.loads(p.read_text())
        tv = tj.get("timing", tj)
        timing[t] = {v: {"s": tv[v]["s"], "audio_s": tv[v]["audio_s"], "s_per_audio_s": tv[v]["s"] / tv[v]["audio_s"]}
                     for v in VARIANTS}
        if "version" in tj:
            timing[t]["browser_version"] = tj["version"]

    frames = {s: int(sum(nf[n] for n in names if meta["sets"][n] == s)) for s in SETS}
    res = {
        "conditions": {
            "inputs": {s: sum(1 for n in names if meta["sets"][n] == s) for s in SETS},
            "frames": frames, "frames_all": int(sum(frames.values())),
            "seed": meta["seed"], "snrs_db": meta["snrs_db"], "numpy": meta["numpy"], "python": meta["python"],
            "rustc": subprocess.run(["rustc", "--version"], capture_output=True, text=True).stdout.strip(),
            "wasm_bindgen": subprocess.run(["wasm-bindgen", "--version"], capture_output=True, text=True).stdout.strip(),
            "browsers": {t: timing[t].get("browser_version") for t in BROWSER_TARGETS},
            "rules": {"found_threshold": FOUND_THRESHOLD, "refuse_aperiodicity": REFUSE_APERIODICITY,
                      "accept_margin_cents": ACCEPT_MARGIN_CENTS, "cents_f64_tol": CENTS_F64_TOL},
            "inputs_checks": meta["checks"],
        },
        "checks": checks,
        "hypotheses": HYPOTHESES,
        "H1": {"holds": all(h1.values()), "by_build_variant": h1},
        "H2": {"holds": all(h2.values()), "by_target_variant": h2},
        "identical_pairs": pairs,
        "epsilon_vs_numpy_f64": epsilon,
        "across_targets_vs_native": across,
        "timing": timing,
    }
    OUT.write_text(json.dumps(res, indent=1))
    print("checks", checks)
    print("H1", res["H1"]["holds"], "H2", res["H2"]["holds"])
    for k, v in epsilon.items():
        a = v["all"]
        print(f"{k:28s} max {a['max_abs_cents']:.3g} p99 {a['p99_abs_cents']:.3g} found_mm {a['found_mismatch']} "
              f"lag_mm {a['lag_mismatch']} acc_flips {a['accept_flips']} of {a['frames']}")


if __name__ == "__main__":
    main()
