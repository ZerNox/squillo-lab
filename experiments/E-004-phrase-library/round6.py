"""E-004 round 6 (squillo iteration 86, F-060): Hen Wlad Fy Nhadau's first
line read in a dated edition, John Owen's *Gems of Welsh Melody* (Isaac
Clarke, Ruthin, 1860), and compared with Mutopia 1017's 12 notes.

Rules: README, *Round 6*. They are committed before anything is fetched;
the page, and every reading, are committed before `compare` runs.

    uv run python round6.py fetch      # the scan, its pages named by OCR -> results/r6-fetch.json
    uv run python round6.py render     # the reader check's two scores -> /tmp/r6-check/score-{A,B}.png
    uv run python round6.py compare    # -> results/r6-compare.json
"""

import hashlib
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

import round2 as R2
import run as R

HERE = Path(__file__).parent
RES = R.RES
CACHE = HERE / "data" / "cache" / "r6"
READ = Path("/tmp/r6-read")  # the page images a reader is given, outside both repos (rule 4)
CHECK = Path("/tmp/r6-check")  # the reader check's scores, apart from the pages (rule 5)
UA = {"User-Agent": "squillo-lab/0.1 (E-004 research; one request per file)"}

# ---------------------------------------------------------------- rules (README, Round 6)

# Rule 1: the reference, named before any page is read. First the scan IMSLP
# lists (British Library, G.374, both series, Isaac Clarke 1860, 1861; IMSLP
# revision 4109419, file sha1 below, read through its API 2026-10-03); if it is
# not served as a PDF, the Internet Archive item `gems-of-welsh-melody` (dated
# 1860, both series, its own file list's md5). Never both compared, never the
# better of the two (S16).
IMSLP_URL = ("https://imslp.org/images/5/5f/PMLP1075353-Digital_Store_G.374.-1.-_Gems_of_Welsh_Melody."
             "_A_Selection_of_popular_Welsh_Songs-_with_English_and_Welsh_words.pdf")
IMSLP_SHA1 = "5d0165ca64a8b2a32114559f3f04793601531895"
IA_ID = "gems-of-welsh-melody"
IA_FILE = "Gems of Welsh Melody.pdf"

# Rule 2: the page is the first in the scan's order whose OCR text names the
# song (this pattern), confirmed by its printed title on the image.
SONG_RE = re.compile(r"hen\s*wlad|land\s+of\s+my\s+fathers", re.I)
TITLE_PAGES = 6     # rule 6: the first pages rendered for the title page and its year
DPI = 200

# Rule 5: the reader check's two scores. (i) Mutopia 1017's 12 notes as
# round 5 extracted them; (ii) the same with one pitch moved (index 5, Ab4 to
# Bb4) and one bar's rhythm changed (indices 1-3, 1 1 1 to 1/2 1/2 2), so that
# it differs from (i) in what a reader of the page must see. No title, no
# words, no tempo. Which is which is not told to the reader.
CHECK_ALTER_PITCH = (5, "Bb4")
CHECK_ALTER_BEATS = {1: 0.5, 2: 0.5, 3: 2.0}

# Rule 7: the comparison is round 1's `compare` (run.py line 348): pitch exact
# (every interval, transposition removed), rhythm exact (every inter-onset
# interval within 2 % after one overall scale).


def committed_first():
    """S15: refuse to run on an uncommitted edit of this file or of the
    modules whose rules it reuses, or before they are committed."""
    for me in (Path(__file__).name, "round2.py", "run.py"):
        a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
        b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", me], cwd=HERE)
        if a.returncode or b.returncode:
            sys.exit(f"{me} is not committed as it stands: commit the rules before running")


# ---------------------------------------------------------------- notes

STEP = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi_of(name):
    m = re.fullmatch(r"([A-G])(bb|b|##|#|x)?(-?\d)", name)
    assert m, name
    acc = {"bb": -2, "b": -1, None: 0, "#": 1, "##": 2, "x": 2}[m.group(2)]
    return 12 * (int(m.group(3)) + 1) + STEP[m.group(1)] + acc


def as_track(notes, tpq=384):
    """A reading (pitch names, beats in quarter notes) as one track for compare."""
    on, t = [], 0.0
    for n in notes:
        on.append(round(t * tpq))
        t += float(n["beats"])
    return dict(pitches=[midi_of(n["pitch"]) for n in notes], onsets=on, tpq=tpq)


def as_mine(notes):
    return [(midi_of(n["pitch"]), float(n["beats"])) for n in notes]


def mutopia_notes():
    """Rule 3: Mutopia 1017's first line as round 5 extracted it (r5-posthoc-anthem.json)."""
    ph = json.load(open(RES / "r5-posthoc-anthem.json"))["phrase"]
    from fractions import Fraction
    return [dict(pitch=p, beats=float(Fraction(b))) for p, b in zip(ph["pitches"], ph["beats"])]


def same(a, b):
    """Two readings agree note for note: same count, same sounding pitch, same beats."""
    return len(a) == len(b) and all(midi_of(x["pitch"]) == midi_of(y["pitch"]) and
                                    abs(float(x["beats"]) - float(y["beats"])) < 1e-9 for x, y in zip(a, b))


def match(reading, ref):
    """Rule 7: round 1's compare of a reading against the reference's one track."""
    r = R.compare(as_mine(reading), [as_track(ref)])
    rhythm = bool(r and r["exact_pitch"] and r["rhythm"] and r["rhythm"]["ioi_match"] == r["rhythm"]["ioi_total"])
    return dict(compare=r, exact_pitch=bool(r and r["exact_pitch"]), exact_rhythm=rhythm,
                same_count=len(reading) == len(ref), match=rhythm and len(reading) == len(ref))


# ---------------------------------------------------------------- fetch (rules 1, 2, 6)

def get(url, dest, headers=UA):
    if not dest.exists():
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=600) as r:
            ctype = r.headers.get("Content-Type", "")
            data = r.read()
        dest.write_bytes(data)
        (dest.parent / (dest.name + ".ctype")).write_text(ctype)
    return dest.read_bytes(), (dest.parent / (dest.name + ".ctype")).read_text()


def fetch():
    committed_first()
    CACHE.mkdir(parents=True, exist_ok=True)
    out = dict(read_on=None)
    # Rule 1: IMSLP's scan first. Served means a PDF whose sha1 is the one IMSLP's API gives.
    data, ctype = get(IMSLP_URL, CACHE / "imslp.bin", {**UA, "Cookie": "imslpdisclaimeraccepted=yes"})
    sha1 = hashlib.sha1(data).hexdigest()
    out["imslp"] = dict(url=IMSLP_URL, content_type=ctype, bytes=len(data), sha1=sha1,
                        served=data[:5] == b"%PDF-" and sha1 == IMSLP_SHA1)
    if out["imslp"]["served"]:
        pdf, ref = CACHE / "imslp.bin", dict(source="imslp", sha1=sha1)
    else:
        meta = json.loads(get(f"https://archive.org/metadata/{IA_ID}", CACHE / "ia-meta.json")[0])
        f = next(x for x in meta["files"] if x["name"] == IA_FILE)
        data, ctype = get(f"https://archive.org/download/{IA_ID}/{urllib.request.quote(IA_FILE)}",
                          CACHE / "ia.pdf")
        md5 = hashlib.md5(data).hexdigest()
        assert md5 == f["md5"], (md5, f["md5"])
        pdf = CACHE / "ia.pdf"
        ref = dict(source="internet archive", item=IA_ID, file=IA_FILE, md5=md5, bytes=len(data),
                   sha256=hashlib.sha256(data).hexdigest(),
                   item_meta={k: meta["metadata"].get(k) for k in ("title", "date", "creator", "uploader",
                                                                    "publicdate", "scanner", "contributor")})
    out["reference"] = ref
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    n = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    out["pages"] = n
    hits = []
    for p in range(1, n + 1):
        t = subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), str(pdf), "-"],
                           capture_output=True, text=True).stdout
        if SONG_RE.search(t):
            hits.append(dict(page=p, text_head=" ".join(t.split())[:300]))
    out["song_pages_by_ocr"] = hits
    READ.mkdir(parents=True, exist_ok=True)
    rendered = []
    for p in sorted({h["page"] for h in hits} | {h["page"] + 1 for h in hits} | set(range(1, TITLE_PAGES + 1))):
        if p > n:
            continue
        stem = READ / f"page-{p:03d}"
        subprocess.run(["pdftoppm", "-r", str(DPI), "-f", str(p), "-l", str(p), "-png", "-singlefile",
                        str(pdf), str(stem)], check=True)
        rendered.append(dict(page=p, png=str(stem) + ".png",
                             sha256=hashlib.sha256(Path(str(stem) + ".png").read_bytes()).hexdigest()))
    out["rendered"] = rendered
    out["tools"] = dict(pdfinfo=subprocess.run(["pdfinfo", "-v"], capture_output=True, text=True).stderr.split("\n")[0])
    json.dump(out, open(RES / "r6-fetch.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False)[:3000])


# ---------------------------------------------------------------- render (rule 5)

LY_NOTE = {"C": "c", "D": "d", "E": "e", "F": "f", "G": "g", "A": "a", "B": "b"}
LY_DUR = {0.5: "8", 1.0: "4", 1.5: "4.", 2.0: "2", 3.0: "2."}


def ly_pitch(name):
    m = re.fullmatch(r"([A-G])(b|#)?(\d)", name)
    acc = {"b": "es", "#": "is", None: ""}[m.group(2)]
    if m.group(1) in "EA" and acc == "es":
        acc = "s"
    octv = int(m.group(3)) - 3
    return LY_NOTE[m.group(1)] + acc + ("'" * octv if octv > 0 else "," * -octv)


def check_scores():
    base = mutopia_notes()
    alt = [dict(n) for n in base]
    alt[CHECK_ALTER_PITCH[0]]["pitch"] = CHECK_ALTER_PITCH[1]
    for i, b in CHECK_ALTER_BEATS.items():
        alt[i]["beats"] = b
    assert not same(base, alt) and sum(n["beats"] for n in alt) == sum(n["beats"] for n in base)
    return dict(i=base, ii=alt)


def render():
    committed_first()
    CHECK.mkdir(parents=True, exist_ok=True)
    out = {}
    # The order shown to the reader: score A is (ii), score B is (i), fixed here.
    for label, key in (("A", "ii"), ("B", "i")):
        notes = check_scores()[key]
        body = " ".join(ly_pitch(n["pitch"]) + LY_DUR[n["beats"]] for n in notes)
        ly = ('\\version "2.24.0"\n\\header { tagline = ##f }\n\\paper { indent = 0 }\n'
              '{ \\key es \\major \\time 3/4 \\partial 4 ' + body + ' r4 \\bar "|." }\n')
        src = CACHE / f"check-{label}.ly"
        CACHE.mkdir(parents=True, exist_ok=True)
        src.write_text(ly)
        subprocess.run([R.LY, "--png", "-dresolution=150", "-o", str(CHECK / f"score-{label}"), str(src)],
                       check=True, capture_output=True, timeout=300)
        out[label] = dict(is_=key, notes=notes, png=str(CHECK / f"score-{label}.png"))
    json.dump(out, open(RES / "r6-check-scores.json", "w"), indent=1)
    print(json.dumps(out, indent=1)[:2000])


# ---------------------------------------------------------------- compare (rules 3, 4, 5, 7, 8)

def compare():
    committed_first()
    ref = mutopia_notes()
    # C10: the comparison's own check, run and asserted before any reading is compared.
    sc = R2.self_check([as_track(ref)])
    assert sc["must_pass"] and sc["must_fail_pitch"] and sc["must_fail_rhythm"]
    # and rule 4's agreement test: must pass on Mutopia's notes against themselves, must fail
    # against the reader check's score (ii), which differs in one pitch and one bar's rhythm.
    agree_check = dict(must_pass=same(ref, ref), must_fail=not same(ref, check_scores()["ii"]))
    assert all(agree_check.values())
    blind = json.load(open(RES / "r6-reading-blind.json"))
    agent = json.load(open(RES / "r6-reading-agent.json"))
    chk = json.load(open(RES / "r6-reader-check.json"))
    truth = check_scores()
    # Rule 5: the reader check, exact on both scores, and score (ii) read as differing from (i).
    reader_check = dict(
        must_pass_i=same(chk["B"]["notes"], truth["i"]),
        must_read_ii=same(chk["A"]["notes"], truth["ii"]),
        must_fail_ii_vs_mutopia=not match(chk["A"]["notes"], ref)["match"])
    reader_check["holds"] = all(reader_check.values())
    readings = dict(blind=blind["notes"], agent=agent["notes"])
    third = json.load(open(RES / "r6-reading-third.json")) if (RES / "r6-reading-third.json").exists() else None
    agree = same(readings["blind"], readings["agent"])
    if agree:
        record, how = readings["blind"], "blind and agent readings agree"
    elif third is None:
        record, how = None, "readings disagree; third reading required (rule 4) and absent"
    elif same(third["notes"], readings["blind"]):
        record, how = readings["blind"], "third reading agrees with the blind reading"
    elif same(third["notes"], readings["agent"]):
        record, how = readings["agent"], "third reading agrees with the agent reading"
    else:
        record, how = None, "no two readings agree"
    out = dict(self_check=sc, agree_check=agree_check, reader_check=reader_check, readings_agree=agree, reading_of_record=how,
               reference=dict(source="Mutopia 1017 as extracted in round 5", notes=ref),
               per_reading={k: match(v, ref) for k, v in readings.items()})
    if third:
        out["per_reading"]["third"] = match(third["notes"], ref)
    if record:
        m = match(record, ref)
        out["record"] = dict(notes=record, **m)
        out["note_diff"] = [dict(i=i, edition=a["pitch"] + ":" + str(a["beats"]),
                                 mutopia=b["pitch"] + ":" + str(b["beats"]))
                            for i, (a, b) in enumerate(zip(record, ref))
                            if midi_of(a["pitch"]) - midi_of(record[0]["pitch"]) !=
                            midi_of(b["pitch"]) - midi_of(ref[0]["pitch"]) or a["beats"] != b["beats"]]
    # Rule 8: the verdict.
    out["verdict"] = ("match" if record and reader_check["holds"] and out["record"]["match"] else
                      "no reading of record" if not record else
                      "reader check failed" if not reader_check["holds"] else "mismatch")
    json.dump(out, open(RES / "r6-compare.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in out.items() if k != "reference"}, indent=1, ensure_ascii=False)[:4000])


if __name__ == "__main__":
    {"fetch": fetch, "render": render, "compare": compare}[sys.argv[1]]()
