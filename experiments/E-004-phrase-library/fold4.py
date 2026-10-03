"""E-004 fold 4 (squillo iteration 87, F-060): round 6's anthem line written as a squillo item, shipped
with the first slice's set, and the set checked whole.

    uv run python fold4.py <squillo>   # -> results/items/hen-wlad-fy-nhadau.json, the same bytes into squillo
                                       #    fixtures/slice/phrases/, results/fold4.json

squillo Q-042 (iteration 87) decides that the phrase ships, with `published_by` 1861 for both parts:
the later of the two years IMSLP's listing gives the British Library copy read in round 6 (its file
name carries the copy's shelfmark, G.374.(1.); "Isaac Clarke, Ruthen, 1860, 1861"), since the print
states no year and its introduction (July 1860) bounds it only from below. ADR 0005's rules decide
whether it ships; this script checks them, it decides nothing else.

Rules, written and committed before the run (S15, C14 to C16):

  I1 The item. Notes: round 6's reading of record (results/r6-compare.json `record`), asserted equal,
     pitch for pitch and duration for duration, to round 5's extraction of Mutopia 1017
     (results/r5-posthoc-anthem.json `phrase`: pitches, beats). Words: the print's Welsh line as round 6's
     agent and third readings give it (results/r6-reading-agent.json, -third.json `words_welsh`),
     asserted equal to each blind reading once its hyphens are normalised: the hyphen both blind readers
     give in "hên-wlad" read as a space, then the third reading's syllable hyphens removed. Key Eb, meter 3/4 (r6-compare's record and r5's extraction agree,
     asserted). The print gives no metronome mark (Moderato, results/r6-page.json `header_as_printed`)
     and Mutopia's source none (round 5 result 5), so tempo_qpm is the transcription's MIDI default, 60
     (r5's tempo_qpm, asserted), and `source` says so, as ADR 0005 *A field the transcription leaves
     unrecoverable* asks. Genre `anthem`; language `cy`; licence CC-PDM-1.0.
     Contributors: words Evan James, music James James, as the print's header credits them
     (r6-page.json); John Owen (Owain Alaw) is credited with the English words and the accompaniment,
     neither of which is sung in the phrase, so he is not a contributor of either part (ADR 0005: an
     arranger is a contributor of the part they changed); his death year is recorded (I2) and would not
     change a verdict.
  I2 The people (round 3's rule 4). Each death year written is Wikidata's P570 for the person's English
     Wikipedia article ("Evan James", "James James", "John Owen (Owain Alaw)"), and Mutopia's header years
     (r5-posthoc-anthem.json `ly_header`: Ieuan ap Iago 1809-1878, Iago ap Ieuan 1833-1902) agree with it,
     asserted. Must fail (round 3's K4): each person's year against the next person's Wikidata entry
     disagrees, the three years being different.
  I3 Loader and rights (fold.py `load`, `build_rights`, both checked on squillo's fixtures by fold.py and
     re-run here on fold.py's EXPECT_BUILD cases first). The item loads and ships. Must fail, inputs that
     differ in one value: the item with the tune's published_by 1931 is refused at
     /content/provenance/tune/published_by; with the words' contributor died 1926, at
     /content/provenance/words/contributors/0/died.
  I4 The set (fold3.py's S1, S2, S5, S6 on every file in squillo fixtures/slice/ after the item is
     written there, byte for byte results/items/): the loader accepts all, none refused; every phrase
     ships; the offers; CO-005's step exercises, the phrases rule (2) gives two blocks and its pick,
     with fold3's block arithmetic cases re-run. Counts recorded: phrases, by origin, by genre label.
     Prediction, written after reading the item's notes (C12): its written notes give one block (its
     only note of 250 frames or more is the final half note, 2 s at 60 quarters a minute, 250 frames,
     (250 - 124) // 125 = 1), so rule (2)'s count and pick are as before the item (11, fence-line-home,
     results/fold3.json at squillo-lab 5735439 is not re-read: they are recomputed with and without the
     item here, and the prediction is that they are equal).
  I5 SHA-256 of the item, as written in both places.

Crude, disposable lab code: never product code (squillo PLAN.md rule 11).
"""

import copy
import hashlib
import json
import subprocess
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

import fold as F
import fold3 as F3
import run as R

HERE = Path(__file__).parent
RES = HERE / "results"
PID = "hen-wlad-fy-nhadau"

EDITION = ("John Owen (Owain Alaw), Gems of Welsh Melody, first series, [Second Edition.] "
           "(Ruthin: Isaac Clarke), page 18; no year printed, introduction dated July 1860; "
           "1860, 1861 in IMSLP's listing of the British Library copy G.374.(1.), the copy read")
PEOPLE = {"Evan James": ("words", "Ieuan ap Iago (1809-1878)"),
          "James James": ("music", "Iago ap Ieuan (1833-1902)")}
OTHERS = {"John Owen (Owain Alaw)": "English words and accompaniment, not sung in the phrase"}
PUBLISHED_BY = 1861      # squillo Q-042: the later catalogue year of the copy read


def committed_first():
    """C15: refuse to run on an uncommitted edit of this file or of the modules whose rules it reads."""
    for me in (Path(__file__).name, "fold.py", "fold3.py"):
        a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
        b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", me], cwd=HERE)
        if a.returncode or b.returncode:
            sys.exit(f"{me} is not committed as it stands: commit the rules before running")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def people():
    names = list(PEOPLE) + list(OTHERS)
    q = R.qids(names)
    wd = R.claims_years([x for x in q.values() if x], ["P570"])
    return {n: dict(qid=q.get(n), wd_label=wd.get(q.get(n), {}).get("label"),
                    wd_died=wd.get(q.get(n), {}).get("P570", [])) for n in names}


def item(wd):
    rec = json.load(open(RES / "r6-compare.json"))["record"]["notes"]
    r5 = json.load(open(RES / "r5-posthoc-anthem.json"))
    ph = r5["phrase"]
    notes = [{"pitch": n["pitch"], "quarters": F.q(Fraction(n["beats"]).limit_denominator())} for n in rec]
    assert [n["pitch"] for n in notes] == ph["pitches"], "I1 pitches"
    assert [n["quarters"] for n in notes] == ph["beats"], "I1 durations"
    assert (ph["key"], ph["meter"], ph["tempo_qpm"]) == ("Eb", "3/4", 60.0), "I1 key, meter, tempo"
    rd = {k: json.load(open(RES / f"r6-reading-{k}.json"))["words_welsh"] for k in ("agent", "third", "blind")}
    words = rd["agent"]
    norm = lambda t: t.replace("hên-wlad", "hên wlad").replace("-", "")  # noqa: E731
    assert norm(rd["third"]) == words and norm(rd["blind"]) == words, ("I1 words", rd)
    died = {}
    for n, (role, hdr) in PEOPLE.items():
        y = int(hdr.rsplit("-", 1)[1].rstrip(")"))
        assert y in wd[n]["wd_died"], ("I2", n, y, wd[n])
        died[n] = y
    source = ("The first line of verse 1, notes and words, as printed in the edition: " + EDITION +
              ". Its notes match the Mutopia Project's Public Domain transcription of the composer's manuscript "
              "(https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=1017) note for note, squillo-lab E-004 "
              "rounds 5 and 6. The edition gives no metronome mark (Moderato): the tempo is the transcription's "
              "MIDI default. The words keep the print's spelling.")
    part = lambda n: {"contributors": [{"name": n, "role": PEOPLE[n][0], "died": died[n]}],  # noqa: E731
                      "published_by": PUBLISHED_BY, "edition": EDITION}
    return {"format_version": 3, "kind": "phrase", "phrase_id": PID, "title": "Hên Wlad fy Nhadau",
            "instructions": F.instructions("anthem", "public-domain"), "genre": "anthem", "language": "cy",
            "words": words,
            "melody": {"key": "Eb", "meter": "3/4", "tempo_qpm": 60, "notes": notes},
            "content": {"licence": F.PD_LICENCE, "source": source, "origin": "public-domain",
                        "provenance": {"words": part("Evan James"), "tune": part("James James")},
                        "melody_checked_against": (
                            "checked against the first line as printed in the edition named in provenance, read in "
                            "squillo-lab E-004 round 6 (two of three readings agreeing, one of them blind, a reader "
                            "check holding), matched in pitch and rhythm; the notes are Mutopia 1017's transcription "
                            "of the composer's manuscript")}}


def set_checks(squillo, skip=None):
    fx = squillo / "fixtures" / "slice"
    files = sorted((fx / "exercises").glob("*.json")) + sorted((fx / "phrases").glob("*.json"))
    texts = {str(p.relative_to(squillo)): p.read_text(encoding="utf-8") for p in files
             if not (skip and p.name == f"{skip}.json")}
    acc, ref = F.load_together(texts)
    ph = {o["phrase_id"]: o for o in acc.values() if o["kind"] == "phrase"}
    ex = {o["exercise_id"]: o for o in acc.values() if o["kind"] == "exercise"}
    rights = {k: F.build_rights(o) for k, o in ph.items()}

    def pick(subject):
        fit = [o for o in ex.values() if o["subject"] == subject and
               any(e["analyzer_id"] == "steadiness" for e in o["analyzers"])]
        return min(fit, key=lambda o: (len(o["analyzers"]), o["exercise_id"]))["exercise_id"] if fit else None
    blocks = {k: F3.phrase_blocks(o)[0] for k, o in ph.items()}
    fit = sorted((-b, k) for k, b in blocks.items() if b >= F3.BLOCKS_MIN)
    return dict(files=len(texts), accepted=len(acc), refused={k: list(v) for k, v in ref.items()},
                exercises=len(ex), phrases=len(ph),
                origin=dict(Counter(o["content"]["origin"] for o in ph.values())),
                genres=dict(sorted(Counter(o["genre"] for o in ph.values()).items())),
                genre_labels=len({o["genre"] for o in ph.values()}),
                ship=sum(v is None for v in rights.values()), rights_fail={k: v for k, v in rights.items() if v},
                offers=sum(1 if o["subject"] == "own-song" else len(ph) for o in ex.values()),
                step_exercise={s: pick(s) for s in ("own-song", "phrase")},
                phrases_with_two_blocks=len(fit), rule2_phrase=fit[0][1] if fit else None,
                blocks=blocks)


def main(squillo):
    squillo = Path(squillo)
    rep = {}
    wd = people()
    rep["I2_people"] = wd
    names = sorted(PEOPLE)
    ys = {n: int(PEOPLE[n][1].rsplit("-", 1)[1].rstrip(")")) for n in names}
    rep["I2_agree"] = all(ys[n] in wd[n]["wd_died"] for n in names)
    rep["I2_must_fail_next_person"] = not any(ys[a] in wd[b]["wd_died"] for a, b in zip(names, names[1:] + names[:1]))
    rep["I2_others"] = {n: dict(role=r, wd_died=wd[n]["wd_died"]) for n, r in OTHERS.items()}

    o = item(wd)
    text = F.dump(o)
    rep["I1_item"] = o
    # I3: the fixture cases first, then the item and its must-fail copies.
    fx = squillo / "fixtures"
    rep["I3_fixtures"] = all(F.build_rights(F.load((fx / rel).read_text(encoding="utf-8"))) == want
                             for rel, want in F.EXPECT_BUILD.items())
    loaded = F.load(text)
    rep["I3_ships"] = F.build_rights(loaded) is None
    late = copy.deepcopy(o)
    late["content"]["provenance"]["tune"]["published_by"] = 1931
    dead = copy.deepcopy(o)
    dead["content"]["provenance"]["words"]["contributors"][0]["died"] = 1926
    rep["I3_must_fail"] = (F.build_rights(F.load(F.dump(late))) == "/content/provenance/tune/published_by" and
                           F.build_rights(F.load(F.dump(dead))) == "/content/provenance/words/contributors/0/died")
    for k in ("I2_agree", "I2_must_fail_next_person", "I3_fixtures", "I3_ships", "I3_must_fail"):
        assert rep[k] is True, (k, rep[k])

    # I4: written in both places, byte for byte, then the set checked whole, with and without the item.
    (F.OUT / f"{PID}.json").write_text(text, encoding="utf-8")
    dst = squillo / "fixtures" / "slice" / "phrases" / f"{PID}.json"
    dst.write_text(text, encoding="utf-8")
    rep["I4_block_cases"] = all(F3.blocks_of_frames(n) == want for n, want in F3.BLOCK_CASES.items())
    assert rep["I4_block_cases"]
    rep["I4_with"] = s = set_checks(squillo)
    rep["I4_without"] = w = set_checks(squillo, skip=PID)
    rep["I4_item_blocks"] = s["blocks"][PID]
    rep["I4_prediction_rule2_unchanged"] = (s["phrases_with_two_blocks"], s["rule2_phrase"]) == \
        (w["phrases_with_two_blocks"], w["rule2_phrase"])
    assert not s["refused"] and s["accepted"] == s["files"], s["refused"]
    assert not s["rights_fail"] and s["ship"] == s["phrases"], s["rights_fail"]
    assert s["phrases"] == w["phrases"] + 1
    rep["I5_sha256"] = dict(item=sha((F.OUT / f"{PID}.json").read_bytes()), squillo=sha(dst.read_bytes()))
    rep["I5_equal"] = rep["I5_sha256"]["item"] == rep["I5_sha256"]["squillo"]
    assert rep["I5_equal"]
    (RES / "fold4.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in rep.items() if k not in ("I1_item",)}, indent=1, ensure_ascii=False,
                     default=str)[:8000])


if __name__ == "__main__":
    committed_first()
    main(sys.argv[1])
