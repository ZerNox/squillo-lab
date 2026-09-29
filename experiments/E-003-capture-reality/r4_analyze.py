"""E-003 round 4 (squillo iteration 53, F-042): frame messages from the
engine worker to the page, one per squillo frame, in Chrome and Firefox.

Rules R0-R3 and checks K0-K3 are in README.md, round 4, and are held here
in code; they were committed before any capture was made (S15, L-047).
Usage: uv run python r4_analyze.py checks   (the checks of the checks only)
       uv run python r4_analyze.py          (checks, then every capture in data/cache/r4)
Writes results/r4/checks.json and results/r4/analysis.json.
"""
import glob
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RAW = HERE / "data/cache/r4"
OUT = HERE / "results/r4"
# R1: squillo SG-002: a frame is 384 samples at 48 000 Hz
FRAME_MS = 384 / 48000 * 1000
SKIP_S = 0.5          # round 1's start-up transient (analyze.py SKIP_S)
KEEPUP_WINDOW_S = 1.0  # R2: the first and the last second of frames compared
REFERENCE = dict(workerLoad=0, pageLoad=0)   # R2: must pass the keep-up bar
OVERLOAD = dict(pageLoad=1.5)                # R2: must fail it


def committed_first():
    """squillo L-047 (S15): refuse to run on an uncommitted edit of this script."""
    here = Path(__file__).resolve()
    r = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", here.name], cwd=here.parent)
    if r.returncode != 0:
        raise SystemExit(f"{here.name} has uncommitted edits: commit its rules first (S15, L-047)")


# ---- the checks, as functions of their inputs ----
def clocks_agree(pings, res):
    """K0: the page's tA <= worker's tW <= page's tB, each within tol = 2 * res
    (one timer step on each side). Returns (ok, worst violation in ms)."""
    tol = 2 * res
    worst = 0.0
    for p in pings:
        worst = max(worst, (p["tA"] - tol) - p["tW"], p["tW"] - (p["tB"] + tol))
    return worst <= 0, worst


def frames_complete(seq, n_posted):
    """C1: the page received frames 0..n_posted-1, each once, in order."""
    return list(seq) == list(range(n_posted))


def blocks_intact(w):
    """C2: round 1's transport check on the block path."""
    return w["lost"] == 0 and w["reordered"] == 0 and w["dup"] == 0


def keeps_up(t_post, lat):
    """C3 (R2): median transport latency over the last second of frames minus
    that over the first second after SKIP_S is at most one frame period."""
    t = (np.asarray(t_post) - t_post[0]) / 1000
    lat = np.asarray(lat)
    first = lat[(t >= SKIP_S) & (t < SKIP_S + KEEPUP_WINDOW_S)]
    last = lat[t >= t[-1] - KEEPUP_WINDOW_S]
    growth = float(np.median(last) - np.median(first))
    return growth <= FRAME_MS, growth


def checks():
    """The checks of the checks, on inputs known independently of them."""
    k = {}
    # K0: must pass on consistent stamps, must fail when the worker's stamp is
    # its own relative clock (a different origin), both from one sample capture
    # if present, else constructed
    good = [dict(tA=100.0, tW=100.05, tB=100.2)]
    shifted = [dict(tA=100.0, tW=100.0 - 50.0, tB=100.2)]
    k["K0_must_pass"] = clocks_agree(good, 0.1)[0]
    k["K0_must_fail"] = not clocks_agree(shifted, 0.1)[0]
    # K1: frames 0..9 must pass; one dropped, one swapped, one repeated must fail
    k["K1_must_pass"] = frames_complete(range(10), 10)
    k["K1_must_fail_drop"] = not frames_complete([0, 1, 2, 4, 5, 6, 7, 8, 9], 10)
    k["K1_must_fail_swap"] = not frames_complete([0, 1, 3, 2, 4, 5, 6, 7, 8, 9], 10)
    k["K1_must_fail_dup"] = not frames_complete([0, 1, 1, 2, 3, 4, 5, 6, 7, 8], 10)
    # K2: the block check must fail on each of its counts
    k["K2_must_pass"] = blocks_intact(dict(lost=0, reordered=0, dup=0))
    k["K2_must_fail"] = all(not blocks_intact(dict(lost=a, reordered=b, dup=c))
                            for a, b, c in [(1, 0, 0), (0, 1, 0), (0, 0, 1)])
    # K3: 12 s of frames; a flat latency must pass, one that grows by 4 ms a
    # frame (a handler of 12 ms per 8 ms frame) must fail
    tp = np.arange(0, 12000, FRAME_MS)
    k["K3_must_pass"] = keeps_up(tp, np.full(len(tp), 0.5))[0]
    k["K3_must_fail"] = not keeps_up(tp, 4.0 * np.arange(len(tp)))[0]
    for key, v in k.items():
        assert v, f"check of the check failed: {key}"
    return k


def pct(x, q):
    return float(np.percentile(x, q)) if len(x) else None


def one(d):
    r = dict(browser=d["browser"], version=d["version"], workerLoad=d["workerLoad"],
             pageLoad=d["pageLoad"], rep=d["rep"])
    if "error" in d or d.get("workerTimeout"):
        r["error"] = d.get("error", "worker timeout")
        return r
    res = d["pageTimerRes"]
    r["timer_res_ms"] = res
    r["clocks_agree"], r["clock_worst_ms"] = clocks_agree(d["pings"], res)
    # K0's must-fail on real data: the worker's own relative clock
    rel = [dict(tA=p["tArel"], tW=p["tWrel"], tB=p["tBrel"]) for p in d["pings"]]
    r["clocks_rel_must_fail"] = not clocks_agree(rel, res)[0]
    w = d["worker"]
    r["blocks"] = w["n"]
    r["frames_posted"] = w["nf"]
    r["frames_at_page"] = len(d["fSeq"])
    r["frames_complete"] = frames_complete(d["fSeq"], w["nf"])
    r["blocks_intact"] = blocks_intact(w)
    r["bad_json"] = d["badJson"]
    post = np.array(d["fPost"]); rb = np.array(d["fBlockRecv"]); rcv = np.array(d["fRecv"])
    lt = rcv - post           # transport: worker post -> page handler
    le = rcv - rb             # engine side: worker receipt of the frame's last block -> page
    t = (post - post[0]) / 1000
    keep = t >= SKIP_S
    for nm, x in (("transport", lt[keep]), ("from_block", le[keep])):
        r[nm] = dict(p50=pct(x, 50), p95=pct(x, 95), p99=pct(x, 99), max=float(x.max()),
                     over_frame=int((x > FRAME_MS).sum()), n=int(len(x)))
    r["keeps_up"], r["growth_ms"] = keeps_up(post, lt)
    r["end_late_ms"] = d["endMs"] - 1000 * d["cfg"]["seconds"]  # the stream's end reaching the page, after its last block was due
    return r


def main():
    committed_first()
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    k = checks()
    (OUT / "checks.json").write_text(json.dumps(k, indent=1))
    if sys.argv[1:] == ["checks"]:
        print(json.dumps(k))
        return
    runs = [one(json.loads(Path(f).read_text())) for f in sorted(glob.glob(str(RAW / "*.json")))]
    ok = [r for r in runs if "error" not in r]
    # asserted checks on every run (C1, C2, K0 and its must-fail on real data)
    for r in ok:
        assert r["clocks_agree"], (r, "K0")
        assert r["clocks_rel_must_fail"], (r, "K0 must-fail on the relative clocks")
        assert r["frames_complete"] and r["bad_json"] == 0, (r, "C1")
        assert r["blocks_intact"], (r, "C2")
    # R2: the keep-up bar must pass on the reference and fail on the overload
    for r in ok:
        if all(r[a] == b for a, b in REFERENCE.items()):
            assert r["keeps_up"], (r, "C3 must pass on the reference")
        if all(r[a] == b for a, b in OVERLOAD.items()):
            assert not r["keeps_up"], (r, "C3 must fail on the overload")
    # R3: per condition, pooled over reps
    cond = {}
    for r in ok:
        key = f'{r["browser"]}/wload{r["workerLoad"]}/pload{r["pageLoad"]}'
        cond.setdefault(key, []).append(r)
    summ = {}
    for key, rs in cond.items():
        summ[key] = dict(
            runs=len(rs), version=rs[0]["version"], timer_res_ms=rs[0]["timer_res_ms"],
            frames=sum(r["frames_at_page"] for r in rs),
            frames_lost_or_out_of_order=sum(0 if r["frames_complete"] else 1 for r in rs),
            keeps_up=[r["keeps_up"] for r in rs], growth_ms=[round(r["growth_ms"], 3) for r in rs],
            transport_p50_max=max(r["transport"]["p50"] for r in rs),
            transport_p99_max=max(r["transport"]["p99"] for r in rs),
            transport_max=max(r["transport"]["max"] for r in rs),
            transport_over_frame=sum(r["transport"]["over_frame"] for r in rs),
            from_block_p50_max=max(r["from_block"]["p50"] for r in rs),
            from_block_p99_max=max(r["from_block"]["p99"] for r in rs),
            from_block_max=max(r["from_block"]["max"] for r in rs),
            from_block_over_frame=sum(r["from_block"]["over_frame"] for r in rs),
            end_late_ms_max=max(r["end_late_ms"] for r in rs),
        )
    res = dict(frame_ms=FRAME_MS, checks=k, runs=runs, conditions=summ,
               errors=[r for r in runs if "error" in r], seconds=round(time.time() - t0, 2))
    (OUT / "analysis.json").write_text(json.dumps(res, indent=1))
    for key, s in summ.items():
        print(key, json.dumps({a: s[a] for a in ("runs", "frames", "keeps_up", "transport_p99_max", "transport_max", "from_block_p99_max", "from_block_max")}))


if __name__ == "__main__":
    main()
