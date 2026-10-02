"""E-005 fold 5 (squillo iteration 74, F-041): round 5's known-melody spread K into squillo
`metrics`, on squillo's own take fixtures. Crude experiment code; adds to round5.py and
fold_refusal.py, never replaces them.

    uv run python fold5.py run <dir>   # writes the two notes fixtures to <dir>, measures K on
                                       # squillo's take fixtures -> results/fold5.json

Question: squillo iteration 74 makes `pitch-spread` of a take given a phrase's written notes
the spread about those notes, K (round5.py steps 1-9, `round5.known`), shown measured when
K + 2 u_B <= 40 cents and as its lower end otherwise (round 5's candidate X = 40, the largest
spread round 2 tested; squillo ADR 0015 chooses it over X = inf). What do squillo's existing
take fixtures give under it, with their written notes, so that its scenarios hold?

Inputs, conditions read from code before any run (S15):
  - the take fixtures fold.py and fold_refusal.py wrote (fold.py:205-219, fold_refusal.py:393-401,
    fold4.py): every note j on semitone MELODY[j] (relative to A4 = 440 Hz) of a tuning 23
    cents above A4, plus deviation d_j; MELODY = A3 B3 C#4 D4 E4 F#4 G#4 A4 G#4 F#4 E4 D4 C#4 B3,
    no two neighbours equal, so no state is merged; read here from squillo's fixtures/, hashes
    checked against squillo's fixtures/MANIFEST.md;
  - notes-a-major-up-down.json: {"notes": [the 14 pitch names above]}, what squillo `runner`
    passes for such a phrase (EX-010's scientific pitch notation, in order); written by this
    script from FR.MELODY, and asserted to parse back to it;
  - notes-a3.json: {"notes": ["A3"]}, one written note, measured on held-steady.wav (one tone at
    220 Hz, A3).
  The truth of each take is the population sd of its d_j, computed from fold.py's and
  fold_refusal.py's DEVS on the exact lists, never retyped.

Rules, written and committed before the run (X = 40, MT-003's refusal on):
  G1 take-in-tune: measured, K - 2u_B <= 0.
  G2 take-spread-5c: measured, holds its truth (5), excludes 0.
  G3 take-spread-15c: measured, holds its truth (15), excludes its 5-cent sibling's truth.
  G4 take-drift-60c: measured (K about one tuning counts a drift as spread), holds its truth
     (18.6052), excludes 0.
  G5 take-uncertain (intent uncertain without written notes, MT-007): at least, its lower end
     in (0, truth]: the written notes give a statement where the take alone gives none.
  G6 take-vibrato-in-tune and take-vibrato-onset-50c: measured, K - 2u_B <= 0.
  G7 held-steady.wav with notes-a3.json: no value (fewer than two notes).
  G8 compare (round5.compare at X = 40, MT-008's form): take-uncertain then take-in-tune
     improved; take-spread-15c then take-spread-5c improved; take-spread-5c twice no change;
     take-in-tune then take-drift-60c worse.
  Every fixture's 14 states found, 0 wrong notes (G1-G6).
Checks of the checks, each on an input that differs from its must-pass case:
  M1 the notes with D4 written a semitone high (D#4, the fourth note) on take-in-tune: "measured
     and K - 2u_B <= 0" must fail (that note lies 100 cents from its aim, under the 150 of a
     wrong note, so it is spread);
  M2 take-uncertain with no written notes, MT-007's wrapped estimate (fold_refusal.measure under
     round 4's PM, as squillo MT-006 now divides the take): "a value or a lower end" must fail
     (intent uncertain);
  M3 "improved" on take-in-tune then take-in-tune must fail;
  M4 the pitch-name parser: the D#4 list must not parse to MELODY.
"""

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

import run  # before synth (round2's note)
import round2 as R2
import fold_refusal as FR
import round4 as R4
import round5 as R5

HERE = Path(__file__).parent


def _own(name):
    """This experiment's module by path: E-002's fold.py, on sys.path through round2, shadows ours."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("e005_" + name, HERE / (name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


F1 = _own("fold")  # fold.py:205-219, the first take fixtures' deviations
OUT = HERE / "results"
SQ = HERE.parents[2] / "squillo"
X40 = R5.XS[1]  # 40 cents, round 5's cap at the largest spread round 2 tested (round5.py XS)
assert X40 == 40.0
TRUTH = {  # population sd of each fixture's deviations, from the generators' own lists
    "take-in-tune.wav": F1.DEVS["take-in-tune.wav"],
    "take-spread-5c.wav": F1.DEVS["take-spread-5c.wav"],
    "take-drift-60c.wav": F1.DEVS["take-drift-60c.wav"],
    "take-uncertain.wav": F1.DEVS["take-uncertain.wav"],
    "take-spread-15c.wav": FR.DEV15,
    "take-vibrato-in-tune.wav": [0.0] * len(FR.MELODY),
    "take-vibrato-onset-50c.wav": [0.0] * len(FR.MELODY),
}
TRUTH = {k: float(np.std(v)) for k, v in TRUTH.items()}  # population sd (ddof 0), as MANIFEST states
assert F1.MELODY == FR.MELODY
NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def committed_first():
    """S15: refuse to run on an uncommitted edit of this file, or before it is committed."""
    me = Path(__file__).name
    a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
    b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", me], cwd=HERE)
    if a.returncode or b.returncode:
        sys.exit(f"{me} is not committed as it stands: commit the rules before running")


def name_of(semi):
    """Semitones from A4 -> scientific pitch notation (sharps)."""
    midi = 69 + semi
    return f"{NAMES[midi % 12]}{midi // 12 - 1}"


def parse(p):
    """EX-010's pitch -> semitones from A4: letter, optional # or b, one octave digit; C4 = -9."""
    m = re.fullmatch(r"([A-G])(#|b)?([0-9])", p)
    assert m, p
    pc = PC[m[1]] + {"#": 1, "b": -1, None: 0}[m[2]]
    return 12 * (int(m[3]) + 1) + pc - 69


def manifest_hashes():
    h = {}
    for line in (SQ / "fixtures" / "MANIFEST.md").read_text().splitlines():
        c = [x.strip() for x in line.split("|")]
        if len(c) > 3 and c[1].endswith(".wav"):
            h[c[1]] = c[2]
    return h


def write_json(path, obj):
    blob = (json.dumps(obj, indent=2) + "\n").encode()
    path.write_bytes(blob)
    return dict(sha256=hashlib.sha256(blob).hexdigest(), bytes=len(blob))


def load(name, hashes):
    import soundfile as sf
    rel = ("fixtures/metrics/" + name) if name.startswith("take-") or name.startswith("held-") else name
    p = SQ / rel
    assert hashlib.sha256(p.read_bytes()).hexdigest() == hashes[rel], rel
    x, sr = sf.read(p, dtype="float32")
    assert sr == FR.SR, (rel, sr)
    if x.ndim > 1:
        x = x[:, 0]
    return x


def k_of(x, notes):
    t, c, _, n_ref = FR.track(x)
    states, _ = R2.merge_repeats([parse(p) for p in notes])
    sp, _ = R5.known(c, t, states)
    st = R5.state(sp, X40)
    fin = math.isfinite(sp["s"])
    row = dict(state=st, s=sp["s"] if fin else None, uB=sp["uB"] if fin else None,
               lower=sp["s"] - 2 * sp["uB"] if fin else None, upper=sp["s"] + 2 * sp["uB"] if fin else None,
               states=sp["states"], found=sp["found"], wrong=sp["wrong"], refused=n_ref)
    return row, sp


def holds(r, v):
    return r["state"] == "measured" and r["lower"] <= v <= r["upper"]


def main(outdir="/tmp/e005-fold5"):
    committed_first()
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    scale = [name_of(s) for s in FR.MELODY]
    assert [parse(p) for p in scale] == FR.MELODY
    off = list(scale)
    off[3] = name_of(FR.MELODY[3] + 1)
    fx = {"notes-a-major-up-down.json": write_json(out / "notes-a-major-up-down.json", {"notes": scale}),
          "notes-a3.json": write_json(out / "notes-a3.json", {"notes": ["A3"]})}
    assert name_of(-12) == "A3" and parse("C4") == -9 and parse("A4") == 0
    H = manifest_hashes()
    rows, SP = {}, {}
    for name in TRUTH:
        rows[name], SP[name] = k_of(load(name, H), scale)
        rows[name]["truth"] = TRUTH[name]
    one, _ = k_of(load("held-steady.wav", H), ["A3"])
    off_row, _ = k_of(load("take-in-tune.wav", H), off)
    xu = load("take-uncertain.wav", H)
    t, c, _, _ = FR.track(xu)
    wsp, _, _, _ = R4.measure(c, t, "PM")
    wrapped_unc = FR.state(wsp)
    r = rows
    checks = {
        "G1_in_tune": r["take-in-tune.wav"]["state"] == "measured" and r["take-in-tune.wav"]["lower"] <= 0,
        "G2_spread_5": holds(r["take-spread-5c.wav"], TRUTH["take-spread-5c.wav"])
        and not holds(r["take-spread-5c.wav"], 0.0),
        "G3_spread_15": holds(r["take-spread-15c.wav"], TRUTH["take-spread-15c.wav"])
        and not holds(r["take-spread-15c.wav"], TRUTH["take-spread-5c.wav"]),
        "G4_drift": holds(r["take-drift-60c.wav"], TRUTH["take-drift-60c.wav"])
        and not holds(r["take-drift-60c.wav"], 0.0),
        "G5_uncertain_at_least": r["take-uncertain.wav"]["state"] == "at least"
        and 0 < r["take-uncertain.wav"]["lower"] <= TRUTH["take-uncertain.wav"],
        "G6_vibrato_in_tune": r["take-vibrato-in-tune.wav"]["state"] == "measured"
        and r["take-vibrato-in-tune.wav"]["lower"] <= 0,
        "G6_vibrato_onset": r["take-vibrato-onset-50c.wav"]["state"] == "measured"
        and r["take-vibrato-onset-50c.wav"]["lower"] <= 0,
        "G7_one_note_no_value": one["state"] == "too few",
        "G8_uncertain_to_in_tune_improved": R5.compare(SP["take-uncertain.wav"], SP["take-in-tune.wav"], X40) == 1,
        "G8_15_to_5_improved": R5.compare(SP["take-spread-15c.wav"], SP["take-spread-5c.wav"], X40) == 1,
        "G8_5_to_5_no_change": R5.compare(SP["take-spread-5c.wav"], SP["take-spread-5c.wav"], X40) == 0,
        "G8_in_tune_to_drift_worse": R5.compare(SP["take-in-tune.wav"], SP["take-drift-60c.wav"], X40) == -1,
        "G_all_states_found_no_wrong": all(r[n]["found"] == r[n]["states"] == 14 and r[n]["wrong"] == 0 for n in r),
    }
    must_fail = {
        "M1_off_note_fails_in_tune_rule": not (off_row["state"] == "measured" and off_row["lower"] <= 0),
        "M2_wrapped_uncertain_gives_nothing": wrapped_unc == "uncertain",
        "M3_in_tune_twice_not_improved": R5.compare(SP["take-in-tune.wav"], SP["take-in-tune.wav"], X40) != 1,
        "M4_off_list_does_not_parse_to_melody": [parse(p) for p in off] != FR.MELODY,
    }
    res = dict(x=X40, fixtures=fx, notes=scale, notes_off=off, rows=rows, one_note=one, off_note=off_row,
               wrapped_take_uncertain=wrapped_unc, checks=checks, must_fail=must_fail)
    json.dump(res, open(OUT / "fold5.json", "w"), indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))
    for k in ("G1_in_tune", "G2_spread_5", "G3_spread_15", "G4_drift", "G5_uncertain_at_least",
              "G6_vibrato_in_tune", "G6_vibrato_onset", "G7_one_note_no_value",
              "G8_uncertain_to_in_tune_improved", "G8_15_to_5_improved", "G8_5_to_5_no_change",
              "G8_in_tune_to_drift_worse", "G_all_states_found_no_wrong"):
        assert checks[k], k
    for k in ("M1_off_note_fails_in_tune_rule", "M2_wrapped_uncertain_gives_nothing",
              "M3_in_tune_twice_not_improved", "M4_off_list_does_not_parse_to_melody"):
        assert must_fail[k], k


if __name__ == "__main__":
    {"run": main}[sys.argv[1]](*sys.argv[2:])
