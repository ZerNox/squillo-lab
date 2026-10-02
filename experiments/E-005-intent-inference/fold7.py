"""E-005 fold 7 (squillo iteration 84, F-073): round 7's least share of written notes kept, F = 0.75,
into squillo MT-014, on squillo's take fixtures. Crude experiment code; adds to fold5.py and
fold6.py, never replaces them.

    uv run python fold7.py run <dir>   # writes notes-a-major-up-down-up.json to <dir>, measures
                                       # squillo's take fixtures under the share rule -> results/fold7.json

Question: squillo iteration 84 adds to MT-014 that a take given a phrase's written notes is intent
uncertain also when the notes kept (found - wrong) are fewer than F of the written states (the
written notes, consecutive repeats merged), F = 0.75: round 7's selection, the only candidate that
passed B1 and B5 (results/round7.json `selected`, read here, never retyped). Do squillo's existing
MT-014 scenarios keep their outcomes under it, and which fixtures show the rule where MT-014 as it
stood (F = 0) gives a value?

Inputs, conditions read from code and results before any rule (S15 C1, C2, C12):
  - the take fixtures of fold 5 with notes-a-major-up-down.json (14 written notes, 14 states): fold 5
    found 14 of 14 on six and 13 of 14 on take-uncertain.wav, 0 wrong (results/fold5.json `rows`),
    so each keeps at least 13/14 > F of its states; held-steady.wav with notes-a3.json, 1 of 1
    found, too few by MT-014's two notes (results/fold5.json `one_note`);
  - held-wobble.wav (0.5 Hz, -20.90 to +20.65 cents about 220 Hz, squillo fixtures/MANIFEST.md) with
    the 14 notes: measured on 2 of 14 found under F = 0 (results/fold6.json `held_others`), and
    2 < F * 14 = 10.5: the change is expected to move it (C12);
  - notes-a-major-up-down-up.json, written here: the 14 notes, then the first six again
    (FR.MELODY + FR.MELODY[:6]: ... C#4 B3, A3 B3 C#4 D4 E4 F#4), 20 notes, no two neighbours
    equal (asserted), so 20 states; take-in-tune.wav (the 14 notes sung, fold 5 G1: 14 of 14
    found) given these 20 is a take that sings the first 14 of a 20-note phrase, 0.70 of it,
    round 7's partial take in its simplest form. Expected to move under F = 0.75 (14 < 15) and
    not under F = 0.5 (14 >= 10), so its scenario tells round 7's two nearest candidates apart.

Rules, written and committed before the run (X = 40, MT-003's refusal on, fold5.k_of, then the share):
  G0 every fold 5 row (7 take fixtures, the 14 notes) and held-steady.wav with notes-a3.json keep
     under the share rule the state fold5.k_of gives them (the share rule moves none of them).
  H1 held-wobble.wav with the 14 notes: intent uncertain under the share rule, with a value under
     F = 0 (MT-014 as it stood).
  H2 take-in-tune.wav with notes-a-major-up-down-up.json: intent uncertain under the share rule,
     its notes kept at least 0.5 of its states and at least two (so F = 0.5 and F = 0 would give a
     value).
Checks of the checks (C10), each on an input that differs from its must-pass case in the input the
check reads:
  M0 G0's predicate (state unchanged by the share) must fail on held-wobble.wav with the 14 notes:
     the take differs; its kept 2 is under F * 14 (fold 6), the term the predicate reads.
  M1 H1's predicate (too few under the share) must fail on take-in-tune.wav with the 14 notes: the
     take differs; 14 kept of 14 states (fold 5 G1).
  M2 H2's predicate (too few under the share, kept >= 0.5 of states) must fail on take-in-tune.wav
     with the 14 notes: the written notes differ, 14 states instead of 20, the term that decides.
  M3 H2's second clause (kept >= 0.5 of states) must fail on held-steady.wav with the 14 notes:
     1 kept of 14 (fold 6 H1).
C13: each rule predicts one outcome on named inputs whose kept counts were read above; G0's inputs
all keep at least 13 of 14.
"""

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

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
SHARE = json.loads((OUT / "round7.json").read_text())["selected"]  # round 7's selection (R7-3)
NEAREST = 0.5  # round 7's next candidate below SHARE (round7.py FS), the one H2 must tell apart
MODS = ["fold7.py", "fold5.py", "round5.py", "round2.py", "fold_refusal.py"]


def committed_first():
    """C15: refuse to run on an uncommitted edit of this file or of a module holding its rules."""
    me = Path(__file__).name
    a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
    b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", *MODS], cwd=HERE)
    if a.returncode or b.returncode:
        sys.exit(f"{me} or a module it reads is not committed as it stands: commit the rules before running")


def kept(row):
    return row["found"] - row["wrong"]


def shared(row, f):
    """MT-014's state with a least share f of written states kept on top of its two notes."""
    if row["state"] != TOO_FEW and kept(row) < f * row["states"]:
        return TOO_FEW
    return row["state"]


def too_few_shared(row):
    return shared(row, SHARE) == TOO_FEW


def h2_pred(row):
    return too_few_shared(row) and kept(row) >= max(MIN_KEPT, NEAREST * row["states"])


def main(outdir="/tmp/e005-fold7"):
    committed_first()
    assert SHARE == 0.75, SHARE
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    H = F5.manifest_hashes()
    notes = json.loads((SQ / "fixtures/metrics/notes-a-major-up-down.json").read_text())["notes"]
    assert notes == [F5.name_of(s) for s in F5.FR.MELODY], notes
    one = json.loads((SQ / "fixtures/metrics/notes-a3.json").read_text())["notes"]
    assert one == ["A3"], one
    up_semi = list(F5.FR.MELODY) + list(F5.FR.MELODY[:6])
    assert all(a != b for a, b in zip(up_semi, up_semi[1:])), up_semi
    up = [F5.name_of(s) for s in up_semi]
    assert [F5.parse(p) for p in up] == up_semi and len(up) == 20
    fx = F5.write_json(out / "notes-a-major-up-down-up.json", {"notes": up})

    takes = ["take-in-tune.wav", "take-spread-5c.wav", "take-drift-60c.wav", "take-uncertain.wav",
             "take-spread-15c.wav", "take-vibrato-in-tune.wav", "take-vibrato-onset-50c.wav"]
    rows = {t: F5.k_of(F5.load(t, H), notes)[0] for t in takes}
    steady = F5.load("held-steady.wav", H)
    rows["held-steady.wav|notes-a3"] = F5.k_of(steady, one)[0]
    wobble, _ = F5.k_of(F5.load("held-wobble.wav", H), notes)
    in_tune_up, _ = F5.k_of(F5.load("take-in-tune.wav", H), up)
    steady14, _ = F5.k_of(steady, notes)
    recorded = {"held-vibrato.wav|14": F5.k_of(F5.load("held-vibrato.wav", H), notes)[0],
                "held-steady.wav|20": F5.k_of(steady, up)[0],
                "held-wobble.wav|20": F5.k_of(F5.load("held-wobble.wav", H), up)[0]}
    for r in [*rows.values(), wobble, in_tune_up, steady14, *recorded.values()]:
        r["kept"] = kept(r)
        r["share"] = kept(r) / r["states"]
        r["state_shared"] = shared(r, SHARE)
        r["state_nearest"] = shared(r, NEAREST)

    # checks of the checks first (C10), before any rule's outcome
    must_fail = {
        "M0_wobble_state_moved": shared(wobble, SHARE) != wobble["state"],
        "M1_in_tune_14_not_too_few": not too_few_shared(rows["take-in-tune.wav"]),
        "M2_in_tune_14_not_h2": not h2_pred(rows["take-in-tune.wav"]),
        "M3_steady_14_keeps_under_half": not (kept(steady14) >= max(MIN_KEPT, NEAREST * steady14["states"])),
    }
    assert all(must_fail.values()), "a check of a check did not fail as it must"

    checks = {
        "G0_states_unchanged": all(shared(r, SHARE) == r["state"] for r in rows.values()),
        "H1_wobble_too_few_shared": too_few_shared(wobble) and wobble["state"] != TOO_FEW,
        "H2_part_of_phrase_too_few_shared": h2_pred(in_tune_up),
    }
    res = dict(x=F5.X40, share=SHARE, nearest=NEAREST, fixtures={"notes-a-major-up-down-up.json": fx},
               notes_up=up, rows=rows, wobble=wobble, in_tune_up=in_tune_up, steady14=steady14,
               recorded=recorded, checks=checks, must_fail=must_fail)
    json.dump(res, open(OUT / "fold7.json", "w"), indent=1, default=float)
    print(json.dumps(dict(fixtures=res["fixtures"], wobble=wobble, in_tune_up=in_tune_up,
                          recorded=recorded, checks=checks, must_fail=must_fail), indent=1, default=float))
    assert checks["G0_states_unchanged"], "G0"
    assert checks["H1_wobble_too_few_shared"], "H1"
    assert checks["H2_part_of_phrase_too_few_shared"], "H2"


if __name__ == "__main__":
    {"run": main}[sys.argv[1]](*sys.argv[2:])
