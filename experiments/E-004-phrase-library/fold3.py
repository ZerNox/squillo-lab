"""E-004 fold 3 (squillo iteration 62, F-061 and F-062 (a)): the set the first slice ships, checked whole.

    uv run python fold.py <squillo> --ship   # first: writes the 30 into squillo fixtures/slice/phrases/
    uv run python fold3.py <squillo>         # -> results/fold3.json

Rules, written and committed before the run (S15, S19):

  T  F-062 (a). Where each round 3 item's tempo comes from, read from the transcription's LilyPond source
     (data/cache/ly/r3-<id>/in.ly, the file round 3 read): comments removed, every \\midi { ... } block cut
     out by brace matching; a \\tempo with a metronome value ("<unit> = <n>") left in the rest is
     `printed`; one only inside a \\midi block is `midi-setting`; none is `default` (LilyPond's 60, a
     tempo word alone giving no value). Asserted: `default` is exactly fold.py's R3_NO_MARK and
     `midi-setting` exactly R3_MIDI_SETTING; for `printed` and `midi-setting` the value, in quarter notes
     a minute (a dotted unit counts 1.5 of its note), equals the item's tempo_qpm. Cross-check, recorded
     and asserted: page 1 of the compiled out.pdf, as pdftotext gives it, holds "= <n>" for every
     `printed` item and for no other. Must pass and must fail: the reader on three short texts written
     here, one of each kind.
  S  F-061. The set squillo ships is every file in fixtures/slice/exercises/ and fixtures/slice/phrases/:
     S1 fold.py's loader (EX-001 to EX-011, itself checked on squillo's fixtures by fold.py) accepts
        all of them loaded together, none refused; must fail: the set plus a copy of one phrase under
        another file name, both refused under EX-004;
     S2 every phrase passes fold.py's rights rules (BU-008); its fixture cases re-run here;
     S3 the licences used are recorded (BU-007's list check is the build's; ADR 0022 records CC-PDM-1.0
        as current on SPDX 3.29.0, and a LicenseRef- passes);
     S4 BU-009 and AN-002: each analyzer_id an exercise names is declared once and has one widget in
        fixtures/build/id-declarations.json's case first-slice, and its parameters are {}; must fail:
        fixtures/exercises/own-song-exercise.json (ids no analyzer declares) and
        fixtures/build/steadiness-parameter.json (a parameter);
     S5 RU-001: what the runner offers (an own-song exercise once, a phrase exercise on each phrase);
     S6 CO-005: for each subject, the accepted exercise listing `steadiness` with the fewest analyzers,
        then the least exercise_id; and rule (2): the blocks MT-009 would give each phrase if each written
        note were sung as one held note lasting its written duration at the phrase's tempo, 125 frames a
        second (8 ms frames, ADR 0007): a note of N whole frames is held when N >= 250 and gives
        (N - 124) // 125 blocks. The phrase rule (2) picks: the most blocks, at least two, then the least
        phrase_id. Must pass and must fail on the blocks' arithmetic: 249 frames 0, 250 1, 373 1, 374 2,
        known from MT-009's text by hand;
     S7 the SHA-256 of every file in the set, and of fixtures/exercises/edition-phrase.json; each phrase
        byte for byte results/items/<id>.json.

Crude, disposable lab code: never product code (squillo PLAN.md rule 11).
"""

import hashlib
import json
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import fold as F

HERE = Path(__file__).parent
RES = HERE / "results"
LY = HERE / "data" / "cache" / "ly"

FPS = 125                       # frames a second: 384-sample frames at 48 kHz (ADR 0007, 8 ms)
HELD_MIN, TRIM, BLOCK = 250, 62, 125   # MT-009: a held note >= 250 frames; 62 off each end; 1 s blocks
BLOCKS_MIN = 2                  # CO-005 rule (2): at least two blocks

# ---------------------------------------------------------------- T: where a tempo comes from

TEMPO_VALUE = re.compile(r"\\tempo\b[^\n=]*?(\d+)(\.?)\s*=\s*(\d+)")


def strip_comments(t):
    t = re.sub(r"%\{.*?%\}", "", t, flags=re.S)
    return re.sub(r"%[^\n]*", "", t)


def cut_midi(t):
    """(text without any \\midi block, [each \\midi block's text])."""
    rest, blocks, i = [], [], 0
    for m in re.finditer(r"\\midi\s*\{", t):
        if m.start() < i:
            continue
        depth, j = 1, m.end()
        while depth:
            depth += {"{": 1, "}": -1}.get(t[j], 0)
            j += 1
        rest.append(t[i:m.start()])
        blocks.append(t[m.start():j])
        i = j
    rest.append(t[i:])
    return "".join(rest), blocks


def qpm(unit, dot, n):
    return Fraction(int(n)) * Fraction(4, int(unit)) * (Fraction(3, 2) if dot else 1)


def tempo_origin(text):
    rest, blocks = cut_midi(strip_comments(text))
    m = TEMPO_VALUE.search(rest)
    if m:
        return "printed", qpm(*m.groups()), m.group(3)
    for b in blocks:
        m = TEMPO_VALUE.search(b)
        if m:
            return "midi-setting", qpm(*m.groups()), m.group(3)
    return "default", Fraction(60), None


T_CASES = {  # written here, each kind known by construction
    "printed": ('\\score { \\relative c\' { \\tempo "Andante" 4 = 84 c4 d e f } \\layout { } \\midi { } }',
                "printed", Fraction(84)),
    "midi-setting": ("\\score { \\relative c' { c4 d e f } \\layout { } \\midi { \\tempo 4. = 60 } }",
                     "midi-setting", Fraction(90)),
    "default": ('% \\tempo 4 = 99\n\\score { \\relative c\' { \\tempo "Langsam" c4 d } \\midi { } }',
                "default", Fraction(60)),
}

# ---------------------------------------------------------------- S6: blocks from written notes


def blocks_of_frames(n):
    return (n - 2 * TRIM) // BLOCK if n >= HELD_MIN else 0


def phrase_blocks(o):
    m = o["melody"]
    out = []
    for note in m["notes"]:
        secs = Fraction(note["quarters"]) * 60 / m["tempo_qpm"]
        out.append(blocks_of_frames(int(secs * FPS)))   # whole frames within the note (floor)
    return sum(out), out


BLOCK_CASES = {249: 0, 250: 1, 373: 1, 374: 2}

# ---------------------------------------------------------------- main


def committed_first():
    """S15: refuse to run on an uncommitted edit of this file or of fold.py, whose rules it reads."""
    for me in (Path(__file__).name, "fold.py"):
        a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
        b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", me], cwd=HERE)
        if a.returncode or b.returncode:
            sys.exit(f"{me} is not committed as it stands: commit the rules before running")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(squillo):
    squillo = Path(squillo)
    fx = squillo / "fixtures"
    rep = {}

    # T: the reader on its own cases first.
    rep["T_cases"] = {k: dict(zip(("origin", "qpm"), tempo_origin(t)[:2])) == dict(origin=o, qpm=q)
                      for k, (t, o, q) in T_CASES.items()}
    rep["T_must_fail"] = tempo_origin(T_CASES["printed"][0])[0] != "midi-setting" and \
        tempo_origin(T_CASES["midi-setting"][0])[0] != "printed"
    assert all(rep["T_cases"].values()) and rep["T_must_fail"], rep
    r3 = json.load(open(RES / "r3-library.json"))
    per = {}
    for p in r3:
        num = p["id"].split("-")[1]
        origin, q, n = tempo_origin((LY / f"r3-{num}" / "in.ly").read_text(encoding="utf-8", errors="replace"))
        item = json.loads((F.OUT / f"{F.slug(p['title'])}.json").read_text(encoding="utf-8"))
        pdf = subprocess.run(["pdftotext", "-l", "1", str(LY / f"r3-{num}" / "out.pdf"), "-"],
                             capture_output=True, text=True).stdout
        per[p["id"]] = dict(phrase_id=item["phrase_id"], origin=origin, value=n, qpm=str(q),
                            item_qpm=item["melody"]["tempo_qpm"], qpm_equal=(q == item["melody"]["tempo_qpm"]),
                            pdf_shows_value=bool(n and re.search(rf"=\s*{n}\b", pdf)),
                            source_says=("default" if "MIDI default" in item["content"]["source"] else
                                         "midi-setting" if "MIDI setting" in item["content"]["source"] else None))
    rep["T_per_item"] = per
    rep["T_default_is_R3_NO_MARK"] = {k for k, v in per.items() if v["origin"] == "default"} == F.R3_NO_MARK
    rep["T_midi_setting_is_R3_MIDI_SETTING"] = \
        {k for k, v in per.items() if v["origin"] == "midi-setting"} == F.R3_MIDI_SETTING
    rep["T_qpm_equal"] = all(v["qpm_equal"] for v in per.values())
    rep["T_pdf_agrees"] = all(v["pdf_shows_value"] == (v["origin"] == "printed") for v in per.values())
    rep["T_source_says"] = all(v["source_says"] == (None if v["origin"] == "printed" else v["origin"])
                               for v in per.values())
    rep["T_counts"] = {o: sorted(v["phrase_id"] for v in per.values() if v["origin"] == o)
                       for o in ("printed", "midi-setting", "default")}

    # S1: the loader on the whole set.
    files = sorted((fx / "slice" / "exercises").glob("*.json")) + sorted((fx / "slice" / "phrases").glob("*.json"))
    texts = {str(p.relative_to(squillo)): p.read_text(encoding="utf-8") for p in files}
    acc, ref = F.load_together(texts)
    rep["S1"] = dict(files=len(texts), accepted=len(acc), refused={k: list(v) for k, v in ref.items()},
                     exercises=sum(o["kind"] == "exercise" for o in acc.values()),
                     phrases=sum(o["kind"] == "phrase" for o in acc.values()))
    dup = dict(texts)
    first = next(k for k in texts if "/phrases/" in k)
    dup["copy-of-" + first.split("/")[-1]] = texts[first]
    _, ref2 = F.load_together(dup)
    rep["S1_must_fail"] = ref2 == {first: ("EX-004", "/phrase_id"), "copy-of-" + first.split("/")[-1]: ("EX-004", "/phrase_id")}

    # S2: rights, with fold.py's fixture cases re-run here first.
    rep["S2_fixtures"] = all(F.build_rights(F.load((fx / rel).read_text(encoding="utf-8"))) == want
                             for rel, want in F.EXPECT_BUILD.items())
    fails = {k: F.build_rights(o) for k, o in acc.items() if o["kind"] == "phrase"}
    rep["S2"] = dict(phrases=len(fails), ship=sum(v is None for v in fails.values()),
                     fail={k: v for k, v in fails.items() if v})

    # S3: the licences used.
    lic = {}
    for o in acc.values():
        key = f"{o['kind']}/{o['content'].get('origin', '-')}"
        lic.setdefault(key, set()).add(o["content"]["licence"])
    rep["S3"] = {k: sorted(v) for k, v in sorted(lic.items())}

    # S4: analyzer ids and parameters against the first slice's declarations.
    decl = json.load(open(fx / "build" / "id-declarations.json"))["cases"]["first-slice"]

    def bu009(o):
        bad = []
        for i, e in enumerate(o["analyzers"]):
            if decl["analyzers"].count(e["analyzer_id"]) != 1 or decl["widgets"].count(e["analyzer_id"]) != 1:
                bad.append(e["analyzer_id"])
            elif e["parameters"] != {}:
                bad.append(f"/analyzers/{i}/parameters")
        return bad
    rep["S4"] = {k: bu009(o) for k, o in acc.items() if o["kind"] == "exercise"}
    rep["S4_must_fail"] = (bu009(F.load((fx / "exercises" / "own-song-exercise.json").read_text())) ==
                           ["fixture-analyzer-a", "fixture-analyzer-b"] and
                           bu009(F.load((fx / "build" / "steadiness-parameter.json").read_text())) ==
                           ["/analyzers/0/parameters"])

    # S5: what the runner offers.
    ex = {o["exercise_id"]: o for o in acc.values() if o["kind"] == "exercise"}
    ph = {o["phrase_id"]: o for o in acc.values() if o["kind"] == "phrase"}
    rep["S5"] = dict(own_song=sorted(k for k, o in ex.items() if o["subject"] == "own-song"),
                     phrase=sorted(k for k, o in ex.items() if o["subject"] == "phrase"),
                     offers=sum(1 if o["subject"] == "own-song" else len(ph) for o in ex.values()))

    # S6: CO-005's choices.
    def pick(subject):
        fit = [o for o in ex.values() if o["subject"] == subject and
               any(e["analyzer_id"] == "steadiness" for e in o["analyzers"])]
        return min(fit, key=lambda o: (len(o["analyzers"]), o["exercise_id"]))["exercise_id"] if fit else None
    rep["S6_block_cases"] = {n: blocks_of_frames(n) == want for n, want in BLOCK_CASES.items()}
    rep["S6_block_must_fail"] = blocks_of_frames(249) != 1 and blocks_of_frames(373) != 2
    blocks = {k: phrase_blocks(o) for k, o in ph.items()}
    fit = sorted((-b, k) for k, (b, _) in blocks.items() if b >= BLOCKS_MIN)
    rep["S6"] = dict(step_exercise={s: pick(s) for s in ("own-song", "phrase")},
                     phrases_with_two_blocks=len(fit), rule2_phrase=fit[0][1] if fit else None,
                     blocks={k: dict(total=b, per_note=[x for x in pn if x]) for k, (b, pn) in sorted(blocks.items())},
                     longest_note_s={k: str(max(Fraction(n["quarters"]) * 60 / o["melody"]["tempo_qpm"]
                                                for n in o["melody"]["notes"])) for k, o in sorted(ph.items())})

    # S7: hashes, and the phrases byte for byte the fold's items.
    rep["S7"] = {k: sha(squillo / k) for k in sorted(texts)}
    rep["S7"]["fixtures/exercises/edition-phrase.json"] = sha(fx / "exercises" / "edition-phrase.json")
    rep["S7_phrases_equal_items"] = all((squillo / k).read_bytes() == (F.OUT / Path(k).name).read_bytes()
                                        for k in texts if "/phrases/" in k)
    rep["S7_edition_equal_item"] = (fx / "exercises" / "edition-phrase.json").read_bytes() == \
        (F.OUT / "the-spirit-of-god.json").read_bytes()

    # Every key naming a check is asserted (S15).
    for k in ("T_default_is_R3_NO_MARK", "T_midi_setting_is_R3_MIDI_SETTING", "T_qpm_equal", "T_pdf_agrees",
              "T_source_says", "S1_must_fail", "S2_fixtures", "S4_must_fail", "S6_block_must_fail",
              "S7_phrases_equal_items", "S7_edition_equal_item"):
        assert rep[k] is True, (k, rep[k])
    assert all(rep["S6_block_cases"].values()), rep["S6_block_cases"]
    assert not rep["S1"]["refused"] and rep["S1"]["accepted"] == rep["S1"]["files"], rep["S1"]
    assert not rep["S2"]["fail"], rep["S2"]
    assert not any(rep["S4"].values()), rep["S4"]
    (RES / "fold3.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str) + "\n",
                                    encoding="utf-8")
    print(json.dumps({k: v for k, v in rep.items() if k not in ("T_per_item", "S7")}, indent=1,
                     ensure_ascii=False, default=str)[:6000])


if __name__ == "__main__":
    committed_first()
    main(sys.argv[1])
