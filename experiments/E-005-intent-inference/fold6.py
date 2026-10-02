"""E-005 fold 6 (squillo iteration 77, F-072): does a take given a phrase of many written notes
reach MT-014's intent uncertain (fewer than two notes kept), so that squillo `ui` may say, for a
phrase, that too few of its written notes were found? Crude experiment code; adds to fold5.py,
never replaces it.

    uv run python fold6.py run    # -> results/fold6.json

Question: squillo F-072. Under MT-014 (round 5's K, fold 5's X = 40) a take given written notes is
intent uncertain only when fewer than two notes are kept (K6 to K9, ADR 0015). Fold 5 measured that
state on one tone given one written note (G7: held-steady.wav with notes-a3.json, `too few`, 1 of
1 found). No shipped phrase has fewer than five written notes (counted here from squillo
fixtures/slice/phrases/, 39 phrases, 5 to 18 notes), so the state a singer can meet on a phrase is
a take that sings few of many written notes. Does one held tone, given the 14 written notes of
notes-a-major-up-down.json, reach it?

Inputs, conditions read from code and the manifest before any run (S15, C1 to C2):
  - held-steady.wav: `0.5 * sin(2 * pi * 220 * n / 48000)`, a steady 220 Hz (A3) for 5 s
    (squillo fixtures/MANIFEST.md, line of held-steady.wav); hash checked by fold5.load;
  - notes-a-major-up-down.json: fold5.py's list, read from squillo fixtures/metrics/ and asserted
    equal to [fold5.name_of(s) for s in FR.MELODY] (fold5.py: main, `scale`); A3 is its first and
    its only A3 note (MELODY[0] = -12, fold_refusal.py MELODY), no two neighbours equal;
  - take-in-tune.wav with the same notes, the must-fail case: fold 5 G1 measured it with 14 of 14
    found (results/fold5.json rows), so it differs from the must-pass case in the take only.
  - recorded, no bar: held-wobble.wav and held-vibrato.wav with the same notes; held-steady.wav
    with each shipped phrase's written notes (squillo fixtures/slice/phrases/*.json,
    /melody/notes/*/pitch in order, as squillo `runner` RU-014 passes them).

Rule, written and committed before the run (X = 40, MT-003's refusal on, fold5.k_of):
  H1 held-steady.wav given notes-a-major-up-down.json: state `too few` (intent uncertain), with
     fewer than two notes kept (found - wrong < 2).
Check of the check (C10), on an input that differs from H1's in the take:
  M1 take-in-tune.wav given the same notes: H1's predicate must fail.
C13: H1 predicts one outcome on one input, not on every input of a set; the earlier rate it rests
on is fold 5's G7 (1 of 1 one-tone takes `too few`). The shipped-phrase rows carry no bar.
"""

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import glob
import json
import subprocess
import sys
from pathlib import Path

import fold5 as F5

HERE = Path(__file__).parent
OUT = HERE / "results"
SQ = F5.SQ
TOO_FEW = "too few"  # round5.state's name for MT-014's intent uncertain (round5.py: state)
MIN_KEPT = 2  # MT-014: intent uncertain when fewer than two notes are kept (ADR 0015 K9)


def committed_first():
    """C15: refuse to run on an uncommitted edit of this file or of fold5.py, which holds rules."""
    for me in (Path(__file__).name, "fold5.py"):
        a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
        b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", me], cwd=HERE)
        if a.returncode or b.returncode:
            sys.exit(f"{me} is not committed as it stands: commit the rules before running")


def too_few(row):
    return row["state"] == TOO_FEW and row["found"] - row["wrong"] < MIN_KEPT


def main():
    committed_first()
    H = F5.manifest_hashes()
    notes = json.loads((SQ / "fixtures/metrics/notes-a-major-up-down.json").read_text())["notes"]
    assert notes == [F5.name_of(s) for s in F5.FR.MELODY], notes
    assert notes.count("A3") == 1 and notes[0] == "A3"
    steady = F5.load("held-steady.wav", H)
    h1, _ = F5.k_of(steady, notes)
    m1, _ = F5.k_of(F5.load("take-in-tune.wav", H), notes)
    others = {n: F5.k_of(F5.load(n, H), notes)[0] for n in ("held-wobble.wav", "held-vibrato.wav")}
    shipped = {}
    for f in sorted(glob.glob(str(SQ / "fixtures/slice/phrases/*.json"))):
        d = json.loads(Path(f).read_text())
        p = [x["pitch"] for x in d["melody"]["notes"]]
        r, _ = F5.k_of(steady, p)
        r["n_written"] = len(p)
        shipped[d["phrase_id"]] = r
    n_written = [r["n_written"] for r in shipped.values()]
    checks = {"H1_one_tone_of_14_too_few": too_few(h1)}
    must_fail = {"M1_in_tune_not_too_few": not too_few(m1)}
    summary = dict(phrases=len(shipped), written_min=min(n_written), written_max=max(n_written),
                   too_few=sum(too_few(r) for r in shipped.values()),
                   states={s: sum(r["state"] == s for r in shipped.values())
                           for s in (TOO_FEW, "measured", "at least")})
    res = dict(x=F5.X40, notes=notes, h1=h1, m1=m1, held_others=others, shipped=shipped,
               shipped_summary=summary, checks=checks, must_fail=must_fail)
    json.dump(res, open(OUT / "fold6.json", "w"), indent=1, default=float)
    print(json.dumps(dict(h1=h1, m1=m1, held_others=others, shipped_summary=summary,
                          checks=checks, must_fail=must_fail), indent=1, default=float))
    assert checks["H1_one_tone_of_14_too_few"], "H1"
    assert must_fail["M1_in_tune_not_too_few"], "M1"


if __name__ == "__main__":
    {"run": main}[sys.argv[1]](*sys.argv[2:])
