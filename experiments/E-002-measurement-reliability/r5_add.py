"""E-002 round 5, the 40th phrase (squillo iteration 87, F-060's fold): E-004 fold 4 ships
hen-wlad-fy-nhadau, so round 5's T4 counts on the shipped phrases' renderings (MT-009's reason, ADR
0004, ADR 0022) are extended by its 24 renderings, made and measured exactly as round 5 made and
measured the 39's. Crude experiment code; adds to r5_trim.py, never replaces it.

    uv run python r5_add.py run <squillo>   # -> data/cache/r5_add/<seed>.json, results/r5_add.json

Rules, written and committed before the run (S15, C14 to C16):

  A0 Reproduction, check of the procedure (C10). `measure(job)` below is r5_trim.py `one` without its
     comparison with round 4's cache (the new item has none): E-004 r4_held.one renders, r5_trim's
     spy_blocks finds both finders' held notes, and each written note of 250 frames or more is found when
     a held note covers one of its frames. Must pass: on the first two of round 5's jobs (r5_trim.jobs,
     seeds SEED0 + 1, + 2, rebuilt here), `measure` equals round 5's saved rows (data/cache/r5/<seed>.json) in held notes,
     blocks and written held notes under both finders. Must fail: the first job's row against the second
     seed's saved row differs (the input differs: another voice).
  A1 The jobs: the item read from squillo fixtures/slice/phrases/hen-wlad-fy-nhadau.json, r4_held's
     voices, sigma 0 and 20, vibrato off and on, as r4_held.jobs makes them, 24 renderings; seeds continue
     round 4's (SEED0 + 937 to SEED0 + 960, after its 936), none of which round 4 or 5 used (asserted: no
     cached file under either seed).
  A2 Recorded, no bar: written held notes and lost under both finders on the 24; renderings with at least
     two blocks; and the 40 phrases' totals, round 5's 39 (results/r5_trim.json r4.<finder>.all_items,
     read) plus these, with Wilson 95 % intervals computed here (r5_trim.wilson).
     Prediction, written after reading the item's notes (C12): its one written held note is the final
     half note (250 frames at 60 quarters a minute, one block), so no rendering gives two blocks, and the
     phrase is not one that CO-005 rule (2) gives two blocks (E-004 fold 4, I4).

Crude, disposable lab code: never product code (squillo PLAN.md rule 11).
"""
import json
import subprocess
import sys
import time
from fractions import Fraction
from multiprocessing import get_context
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
PID = "hen-wlad-fy-nhadau"
OUT = HERE / "results" / "r5_add.json"
ADD_CACHE = HERE / "data" / "cache" / "r5_add"


def committed_first():
    for me in ("r5_add.py", "r5_trim.py", "fold2.py", "fold3_ladder.py", "r2_analyse.py",
               "../E-004-phrase-library/r4_held.py"):
        a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
        b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", me], cwd=HERE)
        if a.returncode or b.returncode:
            sys.exit(f"{me} is not committed as it stands: commit the rules before running")


if __name__ == "__main__":
    committed_first()
    CMD, SQ = sys.argv[1], Path(sys.argv[2])
    sys.argv = sys.argv[:1] + [str(SQ)]   # fold3_ladder, imported by r5_trim, reads sys.argv[1]

import r5_trim as T  # noqa: E402


def measure(job):
    R = T.r4()
    r = R.one(job)
    c = R.ctx()
    idx = T.STASH["idx"]
    mel = job[1]
    durs = [Fraction(n["quarters"]) * 60 / mel["tempo_qpm"] for n in mel["notes"]]
    starts = np.concatenate([[0.0], np.cumsum([float(d) for d in durs])[:-1]]) + 0.1
    t = c["e5run"].HOP * (idx + 1) / 48000 - c["e5run"].LAG_S
    out = dict(id=job[0], voice=job[2], sigma=job[3], vib=job[4], seed=job[5], seconds=r["seconds"])
    for name in ("cur", "tr"):
        held = [(int(idx[fr[0]]), int(idx[fr[-1]])) for fr, _, _ in T.STASH[name]]
        blocks = [len(c["A"].block_measures(con)) for _, con, _ in T.STASH[name]]
        notes = []
        for k, d in enumerate(durs):
            if int(d * 125) < 250:
                continue
            fr = np.nonzero((t >= starts[k]) & (t < starts[k] + float(d)))[0]
            found = any(h[0] <= idx[i] <= h[1] for h in held for i in fr)
            notes.append(dict(note=k, found=bool(found)))
        out[name] = dict(held=held, blocks=blocks, total_blocks=int(sum(blocks)), written_held=notes)
    assert out["cur"]["blocks"] == r["blocks"]
    return json.loads(json.dumps(out))


def same(a, b):
    return all(a[n][k] == b[n][k] for n in ("cur", "tr") for k in ("held", "blocks", "written_held"))


def main():
    R = T.r4()
    rep = {}
    # r5_trim.jobs's first two (it asserts 30 shipped phrases besides round 4's 9, so after fold 4 it is
    # rebuilt here): round 4's first item, its first voice, sigma 0, vibrato off then on
    first = json.loads(sorted(R.ITEMS_OUT.glob("*.json"))[0].read_text(encoding="utf-8"))
    v0 = R.ctx()["e5run"].VOICES[0]
    js = [(first["phrase_id"], first["melody"], v0, 0, vib, R.SEED0 + 1 + vib) for vib in (0, 1)]
    saved = [json.loads((T.CACHE / f"{j[5]}.json").read_text()) for j in js[:2]]
    got = [measure(j) for j in js[:2]]
    rep["A0_must_pass"] = same(got[0], saved[0]) and same(got[1], saved[1])
    rep["A0_must_fail"] = not same(got[0], saved[1])
    assert rep["A0_must_pass"] and rep["A0_must_fail"], rep

    o = json.loads((SQ / "fixtures/slice/phrases" / f"{PID}.json").read_text(encoding="utf-8"))
    jobs, seed = [], R.SEED0 + 936
    for v in R.ctx()["e5run"].VOICES:
        for sigma in (0, 20):
            for vib in (0, 1):
                seed += 1
                assert not (R.CACHE / f"{seed}.json").exists() and not (T.CACHE / f"{seed}.json").exists(), seed
                jobs.append((PID, o["melody"], v, sigma, vib, seed))
    assert len(jobs) == 24
    ADD_CACHE.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with get_context("fork").Pool(12) as p:
        rows = p.map(measure, jobs, chunksize=1)
    for r in rows:
        (ADD_CACHE / f"{r['seed']}.json").write_text(json.dumps(r) + "\n")
    rep["seconds"] = round(time.time() - t0, 1)
    old = json.loads((HERE / "results" / "r5_trim.json").read_text())["r4"]
    for name in ("cur", "tr"):
        ns = [n for r in rows for n in r[name]["written_held"]]
        lost = sum(not n["found"] for n in ns)
        b = np.array([r[name]["total_blocks"] for r in rows])
        allw = old[name]["all_items"]["written"] + len(ns)
        alll = old[name]["all_items"]["lost"] + lost
        rep[name] = dict(written=len(ns), lost=lost, two_blocks=int((b >= 2).sum()), renderings=len(rows),
                         min_blocks=int(b.min()), max_blocks=int(b.max()),
                         forty=dict(written=allw, lost=alll, lost_wilson95=T.wilson(alll, allw)))
    rep["prediction_no_two_blocks"] = rep["tr"]["two_blocks"] == 0
    OUT.write_text(json.dumps(rep, indent=1) + "\n")
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    {"run": main}[CMD]()
