"""E-001 round 1: processing time per second of audio, one process, no
other load. `uv run python timing.py` writes results/timing.json.

Native code on the host CPU (pyworld's C, Praat's C++ through parselmouth),
not WASM in a browser. Each input: analysis once, then one re-synthesis with
the c100 request; best of three runs.
"""

import json
import os
import platform
import time

os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np  # noqa: E402

import resynth  # noqa: E402
import run  # noqa: E402

inputs = [i for i in run.synthetic_inputs() if i["name"] in
          ("bass_plain_1", "tenor_plain_1", "soprano_high_plain_1")] + \
         [i for i in run.real_inputs() if i["name"] in ("m1", "m8", "f1", "f5", "f9")]
cpu = next((ln.split(":", 1)[1].strip() for ln in open("/proc/cpuinfo") if ln.startswith("model name")),
           platform.machine())
out = {"cpu": cpu, "rows": []}
for inp in inputs:
    x, grid = run.load(inp)
    shift = run.request(grid, "c100")
    dur = len(x) / run.SR
    for m in resynth.METHODS:
        best = (np.inf, np.inf)
        for _ in range(3):
            t0 = time.perf_counter()
            a = resynth.analyse(m, x)
            t1 = time.perf_counter()
            resynth.synthesize(a, shift)
            t2 = time.perf_counter()
            best = (min(best[0], t1 - t0), min(best[1], t2 - t1))
        row = dict(input=inp["name"], method=m, seconds=dur,
                   analyse_per_s=best[0] / dur, synth_per_s=best[1] / dur)
        out["rows"].append(row)
        print(row, flush=True)
(run.OUT / "timing.json").write_text(json.dumps(out, indent=1))
