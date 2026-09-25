"""E-001 round 1 follow-up: where do WORLD's gross frames fall?
`uv run python diag_gross.py` writes results/gross.json."""
import json
import numpy as np
import pyworld as pw
import resynth
import run

out = {}
for inp in run.real_inputs() + [i for i in run.synthetic_inputs() if i["voice"].startswith("soprano")]:
    x, grid = run.load(inp)
    fx, tx = run.track(x)
    for m in ("world_dio", "psola"):
        a = resynth.analyse(m, x)
        y = resynth.synthesize(a, run.request(grid, "id"))
        fy, _ = run.track(y)
        ok = ~np.isnan(fx) & ~np.isnan(fy)
        e = run.cents(fy, fx)
        g = ok & (np.abs(e) > 50)
        rec = dict(frames=int(ok.sum()), gross=int(g.sum()))
        if g.any():
            rec["near_octave"] = int((np.abs(np.abs(e[g]) - 1200) < 100).sum())
            rec["sign_down"] = int((e[g] < 0).sum())
            # distance (frames) to the nearest frame where the input's pitch jumps > 50 cents
            c = run.cents(fx, 440.0)
            jump = np.nonzero(np.abs(np.diff(c)) > 50)[0]
            gi = np.nonzero(g)[0]
            d = np.array([np.abs(jump - i).min() if len(jump) else 999 for i in gi])
            rec["within_3_frames_of_input_jump"] = int((d <= 3).sum())
            if m == "world_dio":
                # was WORLD's own f0 unvoiced or octave-off at those instants?
                t = tx[gi]
                f0w = np.interp(t, a["t"], a["f0"])
                fin = fx[gi]
                rec["world_f0_unvoiced"] = int((f0w == 0).sum())
                with np.errstate(all="ignore"):
                    rec["world_f0_octave_off"] = int((np.abs(np.abs(run.cents(f0w, fin)) - 1200) < 100).sum())
        out[f"{inp['name']}/{m}"] = rec
tot = {}
for k, r in out.items():
    m = k.split("/")[1]
    src = "synthetic" if "_" in k.split("/")[0] else "vocalset"
    t = tot.setdefault(f"{src}/{m}", {})
    for kk, v in r.items():
        t[kk] = t.get(kk, 0) + v
(run.OUT / "gross.json").write_text(json.dumps(dict(total=tot, per_input=out), indent=1))
print(json.dumps(tot, indent=1))
