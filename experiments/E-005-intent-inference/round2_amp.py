"""E-005 round 2: the fitted vibrato amplitude on the settle window, straight and vibrato
notes, synthetic (36 phrases each, 14 notes, sigma 10) and VocalSet (77 takes), to set
round2.A_VIB. Frames voiced and glitch-guarded as settle_cycles. -> results/round2_amp.json.
Crude experiment code."""
import json
import numpy as np, round2 as R, run, math, soundfile as sf
from scipy.signal import resample_poly
from multiprocessing import Pool

def amps(cents, t, segs):
    out = []
    for a, b in segs:
        L = b - a
        if L * R.HOP_S < R.TRANS_S: continue
        lo, hi = a + int(0.3 * L), a + max(int(0.9 * L), int(0.3 * L) + 1)
        x, tt = cents[lo:hi], t[lo:hi]
        ok = ~np.isnan(x)
        if len(x) == 0 or ok.mean() < R.VOICED_MIN: continue
        x, tt = x[ok], tt[ok]
        g = np.abs(x - np.median(x)) <= R.GLITCH
        x, tt = x[g], tt[g]
        r = R.fit_rate(x, tt)
        if r is None: continue
        f = r[0]
        X = np.column_stack([np.ones(len(x)), np.sin(2*np.pi*f*tt), np.cos(2*np.pi*f*tt)])
        c = np.linalg.lstsq(X, x, rcond=None)[0]
        out.append(math.hypot(c[1], c[2]))
    return out

def syn(args):
    v, vib, seed = args
    x, tr = R.phrase(v, "major", 10, vib, 14, seed)
    t, c, _ = run.track(x)
    return vib, amps(c, t, R.est_segments(c))

def real(p):
    x, sr = sf.read(p, dtype="float64")
    x = resample_poly(x, 48000 // math.gcd(48000, sr), sr // math.gcd(48000, sr))
    t, c, _ = run.track(x.astype(np.float32))
    return ("vibrato" in p.name), amps(c, t, R.est_segments(c))

if __name__ == "__main__":
    jobs = [(R.run.VOICES[k % 6], vib, 777000 + k + 1000 * vib) for vib in (0, 1) for k in range(36)]
    names = [l.strip().split("/")[-1] for l in open("data/vocalset-files.txt") if l.strip()]
    with Pool(18) as p:
        S = p.map(syn, jobs)
        Rl = p.map(real, [R.CACHE / n for n in names])
    out = {}
    for lab, res in (("synthetic", S), ("VocalSet", Rl)):
        for v in (0, 1):
            a = np.concatenate([np.array(x) for vv, x in res if vv == v])
            out[f"{lab} {'vibrato' if v else 'straight'}"] = dict(
                notes=len(a), p5_25_50_75_95=[round(float(q), 1) for q in np.percentile(a, [5, 25, 50, 75, 95])],
                share_at_or_above_A_VIB=round(float(np.mean(a >= R.A_VIB)), 3))
    json.dump(out, open(R.OUT / "round2_amp.json", "w"), indent=1)
    print(json.dumps(out, indent=1))
