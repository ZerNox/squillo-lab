"""Round 11: MT-009..MT-011 on the shipped Rust crate (`squillo` crates/metrics,
`take::measure`) against the lab's reference (r5_trim.finder with trim, fold2.blocks,
fold2.take) fed the very same pitch cells, on the 159 WORLD re-syntheses, clean and
at 20 dB white noise. Bar (stated before the run): every take gives the same held
notes and blocks, the same block rate presence, and every value and u agrees within
1e-6 relative. Usage: uv run python r11_rust_take.py /path/to/squillo"""
import json
import subprocess
import sys
import tempfile
from multiprocessing import Pool
from pathlib import Path

import numpy as np

import fold2 as F2
import r2_run as R
import r2_truth as T
import r5_trim as T5

SQ = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[3] / "squillo"
BIN = SQ / "target/release/examples/take_json"
C = dict(S=0.078, E=0.41, R=0.16)
K = dict(S=1.33, E=1.57, R=2.51)
OUT = Path(__file__).parent / "results" / "r11_rust_take.json"


def close(a, b):
    return abs(a - b) <= 1e-6 * (1 + abs(b))


def one(stem):
    z = np.load(T.R2 / (stem + ".npz"))
    y = z["y"].astype(np.float64)
    ft = T.truth_per_sample(z["f0"], len(z["x"]))
    res = {}
    for cond in ["clean", "white-20"]:
        sig, _ = R.condition(y, ft > 0, stem, cond)
        with tempfile.NamedTemporaryFile(suffix=".f32") as f:
            f.write(np.asarray(sig, "<f4").tobytes()); f.flush()
            r = json.loads(subprocess.run([BIN, f.name], capture_output=True, check=True, text=True).stdout)
        p = np.array([np.nan if v is None else v for v in r["p"]])
        u = np.array([np.inf if v is None else v for v in r["u"]])
        notes = T5.finder(p, u, True)
        bl = []
        for fr, con, acc in notes:
            for b in F2.blocks(con, u[fr], acc, C, True):
                b["first"] = int(fr[0]) + b["b0"]
                bl.append(b)
        bad = []
        if [[int(fr[0]), int(fr[-1])] for fr, _, _ in notes] != r["notes"]:
            bad.append("notes")
        if [b["first"] for b in bl] != [b[0] for b in r["blocks"]]:
            bad.append("blocks")
        else:
            for b, rb in zip(bl, r["blocks"]):
                if not (close(rb[1], b["S"]) and close(rb[2], b["E"])) or (rb[3] is None) != (b["R"] is None) \
                        or (rb[3] is not None and not close(rb[3], b["R"])):
                    bad.append(f"block {b['first']}")
        for k in "SER":
            t = F2.take(bl, k, K[k])
            if (t is None) != (r[k] is None) or (t is not None and not (close(r[k][0], t[0]) and close(r[k][1], t[1]))):
                bad.append(k)
        res[cond] = dict(notes=len(notes), blocks=len(bl), measured={k: r[k] is not None for k in "SER"}, bad=bad)
    return stem, res


def main():
    stems = sorted(p.stem for p in T.R2.glob("*.npz"))
    with Pool(18) as pool:
        res = dict(pool.map(one, stems))
    summ = {}
    for cond in ["clean", "white-20"]:
        rows = [res[s][cond] for s in stems]
        summ[cond] = dict(takes=len(rows), agree=sum(not r["bad"] for r in rows), notes=sum(r["notes"] for r in rows),
                          blocks=sum(r["blocks"] for r in rows),
                          measured={k: sum(r["measured"][k] for r in rows) for k in "SER"},
                          disagree={s: res[s][cond]["bad"] for s in stems if res[s][cond]["bad"]})
    OUT.write_text(json.dumps(summ, indent=1))
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
