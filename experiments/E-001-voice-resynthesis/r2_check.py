"""E-001 round 2, step 3: do the Rust pipelines do what round 1's did?
Crude experiment code. `uv run python r2_check.py` reads the native outputs
bench.rs wrote in data/cache/r2/out/ and writes results/r2/check.json.

1. world-rs against pyworld 0.3.5 (the C++ WORLD round 1 used), same input,
   same options: f0 per 5 ms frame (Harvest; DIO plus StoneMask), voicing
   agreement and |difference| in cents where both are voiced; and the c100
   output against pyworld's own c100 output, as an SNR in dB.
2. The change delivered, measured exactly as round 1 (run.track, E-002's
   YIN; achieved = YIN(output) - YIN(input) per frame; error = achieved -
   requested; gross = |error| > 50 cents): achieved/requested by least
   squares on non-gross frames, p95 |error| on non-gross frames, the gross
   share; and the long-term envelope distance (run.mcd, round 1 result 5),
   for every input, method (harvest, dio, psola) and request (c100, s100).

The check is checked first (squillo standing instruction S15): on a case it
must pass, pyworld's own c100 and s100 outputs on the same inputs, it must
give round 1's numbers (achieved/requested within round 1's reported
0.978-1.002 for VocalSet and 0.989-0.999 synthetic, WORLD); on a case it must
fail, each Rust `id` output scored against the c100 request, the
achieved/requested must be near 0, not near 1.
"""

import json
import warnings
from multiprocessing import Pool

import numpy as np
import pyworld as pw

import resynth
import run

warnings.filterwarnings("ignore")
R2 = run.CACHE / "r2"
OUTD = R2 / "out"
GROSS = 50.0
METHODS = ("harvest", "dio", "psola")


def rd(p):
    return np.fromfile(p, dtype="<f8")


def delivered(x, y, fx, tx, shift):
    fy, _ = run.track(y)
    ok = ~np.isnan(fx) & ~np.isnan(fy)
    req = shift(tx[ok])
    ach = run.cents(fy[ok], fx[ok])
    return dict(req=req, ach=ach, n_x=int((~np.isnan(fx)).sum()), n_y=int((~np.isnan(fy)).sum()))


def f0_compare(a, b):
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    both = (a > 0) & (b > 0)
    d = np.abs(run.cents(a[both], b[both])) if both.any() else np.array([0.0])
    return dict(frames=n, voicing_agree=float(((a > 0) == (b > 0)).mean()),
                p99=float(np.percentile(d, 99)), max=float(d.max()), over1=float((d > 1).mean()))


def task(inp):
    name = inp["name"]
    x, grid = run.load(inp)
    xr = rd(R2 / f"{name}.x.f64")
    assert np.array_equal(x, xr), f"{name}: exported input differs from run.load"
    fx, tx = run.track(x)
    ref_env = run.mcep(x) if inp["kind"] == "vocalset" else None
    out = dict(name=name, kind=inp["kind"], equiv={}, rows={}, pass_case={}, fail_case={})
    # 1. world-rs against pyworld
    for m, pm in (("harvest", "world_harvest"), ("dio", "world_dio")):
        a = resynth.analyse(pm, x)
        f_rs = rd(OUTD / f"{name}.{m}.f0.native.f64")
        shift = run.request(grid, "c100")
        y_py = resynth.synthesize(a, shift)
        y_rs = rd(OUTD / f"{name}.{m}.c100.native.f64")
        snr = 10 * np.log10(np.sum(y_py ** 2) / max(np.sum((y_rs - y_py) ** 2), 1e-300))
        out["equiv"][m] = dict(f0=f0_compare(f_rs, a["f0"]), c100_snr_db=float(snr))
        # the check's pass case: pyworld's own outputs, as round 1
        for mod in ("c100", "s100"):
            sh = run.request(grid, mod)
            yp = y_py if mod == "c100" else resynth.synthesize(a, sh)
            d = delivered(x, yp, fx, tx, sh)
            out["pass_case"][f"{m}/{mod}"] = {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in d.items()}
    # 2. the change delivered by the Rust outputs
    for m in METHODS:
        for mod in ("c100", "s100"):
            sh = run.request(grid, mod)
            y = rd(OUTD / f"{name}.{m}.{mod}.native.f64")
            assert len(y) == len(x) and np.isfinite(y).all(), f"{name} {m} {mod}: output length or NaN"
            d = delivered(x, y, fx, tx, sh)
            if inp["kind"] == "synthetic":
                ideal = __import__("voice").render(grid["p"], grid["sung"] + sh(grid["t"]))
                env = run.mcd(run.mcep(y), run.mcep(ideal))
            else:
                env = run.mcd(run.mcep(y), ref_env)
            d["lt_env_db"] = env[1]
            out["rows"][f"{m}/{mod}"] = {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in d.items()}
        # the check's fail case: the unchanged output scored against c100's request
        y0 = rd(OUTD / f"{name}.{m}.id.native.f64")
        d = delivered(x, y0, fx, tx, run.request(grid, "c100"))
        out["fail_case"][m] = {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in d.items()}
    print(name, flush=True)
    return out


def summarise(rs, key):
    req = np.concatenate([r["req"] for r in rs])
    ach = np.concatenate([r["ach"] for r in rs])
    e = np.abs(ach - req)
    fine = e <= GROSS
    return dict(frames=int(len(e)),
                kept=float(sum(r["n_y"] for r in rs) / sum(r["n_x"] for r in rs)),
                achieved_fraction=float((ach[fine] * req[fine]).sum() / (req[fine] ** 2).sum()),
                fine_p95=float(np.percentile(e[fine], 95)), gross=float((~fine).mean()),
                **({"lt_env_median": float(np.median([r["lt_env_db"] for r in rs])),
                    "lt_env_max": float(np.max([r["lt_env_db"] for r in rs]))} if key else {}))


if __name__ == "__main__":
    inputs = run.synthetic_inputs() + run.real_inputs()
    with Pool(10) as pool:
        res = pool.map(task, inputs, chunksize=1)
    s = {"rows": {}, "pass_case": {}, "fail_case": {}, "equiv": {}}
    for kind in ("synthetic", "vocalset"):
        rk = [r for r in res if r["kind"] == kind]
        for m in METHODS:
            for mod in ("c100", "s100"):
                s["rows"][f"{kind}/{m}/{mod}"] = summarise([r["rows"][f"{m}/{mod}"] for r in rk], True)
                if m != "psola":
                    s["pass_case"][f"{kind}/{m}/{mod}"] = summarise([r["pass_case"][f"{m}/{mod}"] for r in rk], False)
            s["fail_case"][f"{kind}/{m}"] = summarise([r["fail_case"][m] for r in rk], False)
        for m in ("harvest", "dio"):
            eq = [r["equiv"][m] for r in rk]
            s["equiv"][f"{kind}/{m}"] = dict(
                voicing_agree_min=min(e["f0"]["voicing_agree"] for e in eq),
                voicing_agree_median=float(np.median([e["f0"]["voicing_agree"] for e in eq])),
                f0_p99_max=max(e["f0"]["p99"] for e in eq), f0_max=max(e["f0"]["max"] for e in eq),
                f0_over1_max=max(e["f0"]["over1"] for e in eq),
                snr_min=min(e["c100_snr_db"] for e in eq),
                snr_median=float(np.median([e["c100_snr_db"] for e in eq])))
    s["per_input_equiv"] = {r["name"]: r["equiv"] for r in res}
    (run.OUT / "r2").mkdir(exist_ok=True)
    (run.OUT / "r2" / "check.json").write_text(json.dumps(s, indent=1))
    print(json.dumps({k: s[k] for k in ("equiv", "pass_case", "fail_case", "rows")}, indent=1))
