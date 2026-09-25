"""E-001 round 1 follow-up: level of harmonic 1 relative to harmonic 2, input
against WORLD (DIO) output, per input, over steady frames. Writes results/h1.json."""
import json
import numpy as np
import resynth
import run

def h1h2(x, f0, t):
    out = []
    n = 4096
    win = np.hanning(n)
    for ti, fi in zip(t, f0):
        s = int(ti * run.SR) - n // 2
        if fi <= 0 or s < 0 or s + n > len(x):
            continue
        X = np.abs(np.fft.rfft(x[s:s + n] * win))
        fr = np.fft.rfftfreq(n, 1 / run.SR)
        def peak(f):
            m = (fr > f * 0.9) & (fr < f * 1.1)
            return X[m].max()
        out.append(20 * np.log10(peak(fi) / peak(2 * fi)))
    return np.array(out)

res = {}
for inp in [i for i in run.synthetic_inputs() if i["voice"] in ("soprano", "soprano_high", "tenor") and not i["vib"]] + \
        [i for i in run.real_inputs() if i["name"] in ("f1", "f2", "f9", "m2", "m8")]:
    x, grid = run.load(inp)
    a = resynth.analyse("world_dio", x)
    y = resynth.synthesize(a, run.request(grid, "id"))
    t, f0 = a["t"][::20], a["f0"][::20]
    hx, hy = h1h2(x, f0, t), h1h2(y, f0, t)
    res[inp["name"]] = dict(median_f0=float(np.median(f0[f0 > 0])), h1h2_in=float(np.median(hx)),
                            h1h2_out=float(np.median(hy)), drop_median=float(np.median(hx - hy)),
                            drop_p90=float(np.percentile(hx - hy, 90)))
(run.OUT / "h1.json").write_text(json.dumps(res, indent=1))
for k, v in res.items():
    print(k, {kk: round(vv, 1) for kk, vv in v.items()})
