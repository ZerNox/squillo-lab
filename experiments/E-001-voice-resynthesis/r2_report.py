"""E-001 round 2, step 5: summarise the timings and the check into
results/r2/summary.json and results/r2/summary.md. `uv run python r2_report.py`.
Crude experiment code."""

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
R2 = HERE / "results" / "r2"
METHODS = ("harvest", "dio", "psola")
ROUND1 = {"harvest": "world_harvest", "dio": "world_dio", "psola": "psola"}
STAGES = {"harvest": ("f0 (Harvest)", "envelope (CheapTrick)", "aperiodicity (D4C)", "synthesis"),
          "dio": ("f0 (DIO + StoneMask)", "envelope (CheapTrick)", "aperiodicity (D4C)", "synthesis"),
          "psola": ("pitch", "marks", "-", "overlap-add")}

envs = {"native": [json.loads(ln) for ln in (R2 / "native.jsonl").read_text().splitlines()]}
meta = {}
for b in ("chrome", "firefox"):
    for pkg in ("pkg", "pkg-simd"):
        d = json.loads((R2 / f"{b}-{pkg}.json").read_text())
        key = f"{b}{'-simd' if pkg == 'pkg-simd' else ''}"
        envs[key] = d["rows"]
        meta[key] = dict(version=d["version"], isolated=d["crossOriginIsolated"],
                         threads=d["hardwareConcurrency"], reps=d["reps"], wall_s=d["wall_s"])
round1 = json.loads((HERE / "results" / "timing.json").read_text())["rows"]
check = json.loads((R2 / "check.json").read_text())

out = {"meta": meta, "per_s": {}, "stages_median": {}, "ratio_to_native": {}, "numerics": {}, "memory": {}}
inputs = [r["input"] for r in envs["native"] if r["method"] == "dio"]
for env, rows in envs.items():
    for m in METHODS:
        rs = {r["input"]: r for r in rows if r["method"] == m}
        assert sorted(rs) == sorted(inputs), (env, m)
        tot = np.array([sum(rs[i]["stages_s"]) / rs[i]["seconds"] for i in inputs])
        out["per_s"][f"{env}/{m}"] = dict(median=float(np.median(tot)), min=float(tot.min()), max=float(tot.max()))
        out["stages_median"][f"{env}/{m}"] = [float(np.median([rs[i]["stages_s"][k] / rs[i]["seconds"] for i in inputs]))
                                              for k in range(4)]
        if env != "native":
            nat = {r["input"]: r for r in envs["native"] if r["method"] == m}
            ratio = np.array([sum(rs[i]["stages_s"]) / sum(nat[i]["stages_s"]) for i in inputs])
            out["ratio_to_native"][f"{env}/{m}"] = dict(median=float(np.median(ratio)), min=float(ratio.min()),
                                                        max=float(ratio.max()))
            out["numerics"][f"{env}/{m}"] = dict(
                bit_identical_to_native=sum(rs[i]["vs_native"]["bit_identical"] for i in inputs),
                max_abs_diff=max(rs[i]["vs_native"]["max_abs_diff"] for i in inputs),
                min_native_peak=min(rs[i]["vs_native"]["native_peak"] for i in inputs))
            out["memory"][env] = max(r["wasm_memory_bytes"] for r in rows)
            # run-to-run: each repeat's total against the best, per input
            spread = np.array([max(rs[i]["reps_total_s"]) / min(rs[i]["reps_total_s"]) - 1 for i in inputs])
            first = np.array([rs[i]["reps_total_s"][0] / min(rs[i]["reps_total_s"]) - 1 for i in inputs])
            out.setdefault("repeat_spread", {})[f"{env}/{m}"] = dict(
                median=float(np.median(spread)), max=float(spread.max()), first_over_best_max=float(first.max()))
            if m != "psola":
                out.setdefault("analysis_bytes_per_s", {})[f"{env}/{m}"] = float(
                    np.median([rs[i]["analysis_bytes"] / rs[i]["seconds"] for i in inputs]))
for m in METHODS:
    r1 = [r for r in round1 if r["method"] == ROUND1[m]]
    tot = np.array([r["analyse_per_s"] + r["synth_per_s"] for r in r1])
    out["per_s"][f"round1-native/{m}"] = dict(median=float(np.median(tot)), min=float(tot.min()), max=float(tot.max()))
hashes = {}
for env, rows in envs.items():
    if env != "native":
        for r in rows:
            hashes.setdefault((r["input"], r["method"]), set()).add(r["c100_hash"])
out["numerics"]["hash_sets_over_4_wasm_envs"] = sorted({len(v) for v in hashes.values()})
secs = {r["input"]: r["seconds"] for r in envs["native"] if r["method"] == "dio"}
out["inputs"] = secs
(R2 / "summary.json").write_text(json.dumps(out, indent=1))

L = ["# E-001 round 2: WORLD and a crude PSOLA in WASM", "",
     f"Inputs: {len(inputs)} ({', '.join(f'{i} {secs[i]:.2f} s' for i in inputs)}); one thread; best of 3.",
     "Browsers: " + "; ".join(f"{k} {v['version']}, cross-origin isolated {v['isolated']}" for k, v in meta.items()), "",
     "## Seconds of processing per second of audio (analysis + one c100 re-synthesis)", "",
     "| Environment | " + " | ".join(f"{m} median (min-max)" for m in METHODS) + " |",
     "| :--- | " + " | ".join("---:" for _ in METHODS) + " |"]
for env in ["round1-native", "native"] + [e for e in envs if e != "native"]:
    L.append(f"| {env} | " + " | ".join(
        "{median:.3f} ({min:.3f}-{max:.3f})".format(**out["per_s"][f"{env}/{m}"]) for m in METHODS) + " |")
L += ["", "`round1-native`: pyworld (C++ WORLD) and Praat through parselmouth, round 1's `timing.json`.",
      "`native`: this crate (world-rs and the crude PSOLA) as x86-64 native code.", "",
      "## Stage medians, s per s of audio", ""]
for env in envs:
    for m in METHODS:
        L.append(f"- {env} {m}: " + ", ".join(f"{n} {v:.3f}" for n, v in zip(STAGES[m], out["stages_median"][f"{env}/{m}"]) if n != "-"))
L += ["", "## WASM time / native time, per input", ""]
for k, v in out["ratio_to_native"].items():
    L.append(f"- {k}: median {v['median']:.2f} ({v['min']:.2f}-{v['max']:.2f})")
L += ["", "## Repeats: (slowest / fastest of 3) - 1, per input; and the first repeat over the best", ""]
for k, v in out["repeat_spread"].items():
    L.append(f"- {k}: median {v['median']:.3f}, max {v['max']:.3f}; first over best, max {v['first_over_best_max']:.3f}")
L += ["", "## Bytes the WORLD analysis holds (samples, f0, envelope, aperiodicity; f64), per second of audio, median", ""]
for k, v in out["analysis_bytes_per_s"].items():
    L.append(f"- {k}: {v / 1e6:.2f} MB/s")
L += ["", "## Numerics", ""]
for k, v in out["numerics"].items():
    L.append(f"- {k}: {v}")
L += ["", "## WASM linear memory, high-water mark over the run (MiB)", ""]
for k, v in out["memory"].items():
    L.append(f"- {k}: {v / 2**20:.0f}")
L += ["", "## Check (r2_check.py, native outputs, all 43 inputs)", "", "```", json.dumps(
    {k: check[k] for k in ("equiv", "pass_case", "fail_case", "rows")}, indent=1), "```"]
(R2 / "summary.md").write_text("\n".join(L) + "\n")
print("\n".join(L[:40]))
