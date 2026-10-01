"""E-004 round 3 (squillo iteration 57): the library towards 30 by taking a
phrase's notes and words FROM a named public-domain edition (squillo F-044,
route (a)), instead of checking a from-memory melody against one.

    uv run python round3.py survey    # Mutopia's listing for Voice, metadata only -> results/r3-survey.json
    uv run python round3.py screen    # rules 2-3 on that metadata alone            -> results/r3-screen.json
    uv run python round3.py extract   # rules 4-6, checks K1-K5, in order to 30      -> results/r3-extract.json
    uv run python round3.py measure   # E-005's inference on the new phrases        -> results/r3-measure.json
    uv run python round3.py report    #                                             -> results/r3-summary.json, r3-library.json

Crude experiment code. The rules are in the README (*Round 3*) and in the
constants below; they were committed before the survey ran, and `PEOPLE`
(each person's English Wikipedia article, named from the survey's metadata
alone) before any Wikidata, MIDI or LilyPond file was read. A script that
holds rules refuses to run on an uncommitted edit of itself (squillo S15).
"""

import html
import json
import re
import subprocess
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

import round2 as R2
import run as R

HERE = Path(__file__).parent
CACHE = R.CACHE
RES = R.RES
MUT = R2.MUT
YEAR = R.YEAR  # rules as at 2026-01-01, round 1's

# ---------------------------------------------------------------- rules (README, Round 3)

# Rule 1: the survey reads Mutopia's listing for Instrument=Voice, every style.
SURVEY_URL = MUT + "make-table.cgi?startat={}&searchingfor=&Composer=&Instrument=Voice&Style=&collection=&id=&solo=&recent=&timelength=&timeunit=&lilyversion=&preview="
PAGE = 10  # Mutopia lists 10 pieces per page

# Rule 2c: a person cell segment is anonymous when it names no one.
ANON = re.compile(r"^(anon\.?|anonymous|traditional|trad\.?|folk ?song|folksong|unknown)$", re.I)
# a death year in Mutopia's cells: "(1803–1856)", "(1803-1856)", "(d. 1856)", "(?–1856)"
DATES = re.compile(r"\((?:c\.\s*)?(\d{3,4}|\?)?\s*[-–]\s*(?:c\.\s*)?(\d{4})\)|\(d\.\s*(\d{4})\)")

# Rule 3: Mutopia's style, mapped to the library's genre (a label, fixed here).
GENRE = {"Hymn": "hymn", "Folk": "folk", "Gospel": "spiritual", "Song": "song",
         "Popular / Dance": "song", "Renaissance": "early music", "Baroque": "classical",
         "Classical": "classical", "Romantic": "classical"}

# Rule 5e: the phrase's conditions, read from their sources.
MIN_NOTES, MAX_NOTES = 5, 20          # round 1's phrases had 4..13 notes; a line, not a fragment
MAX_RANGE = 16                        # semitones; round 1's widest phrase (results/summary.json)
MAX_SECONDS = 15.0                    # round 1's longest was 13.3 s
MIN_NOTE_S = 0.1                      # E-005 report.py:19, TRANS_S: shorter is a transition
E2, C6 = R.midi("E2"), R.midi("C6")   # squillo ADR 0007's pitch range
LINE_END = re.compile(r"[,.;:!?]['\"’”»)]*$")
ALIGN_MIN = 0.9                       # rule 5b: share of the line's syllables on the melody track's onsets

TARGET = 30                           # VISION.md §9

# Rule 2g, by tune as well as title: an eligible piece setting a verified
# phrase's tune under another title, named by the agent from the metadata
# (added after the first screen listed it, before any file was read; README).
SAME_TUNE = {367: "ocomeallyefaithful"}

# Rule 4: each named person of the 21 eligible pieces (results/r3-screen.json),
# by Mutopia's name, to the English Wikipedia article the agent names from that
# metadata alone, committed before any Wikidata, MIDI or LilyPond file is read.
PEOPLE = {
    "J.M. Neale": "John Mason Neale", "W. W. Phelps": "W. W. Phelps (Mormon)",
    "J. Brahms": "Johannes Brahms", "H. von Schmidt": "Hans Schmidt (poet)",
    "P. Cornelius": "Peter Cornelius", "D. D. Emmett": "Dan Emmett",
    "G. P. Morris": "George Pope Morris", "G. Loder": "George Loder",
    "G. Fauré": "Gabriel Fauré", "T. Gautier": "Théophile Gautier",
    "R. Bussine": "Romain Bussine", "V. Hugo": "Victor Hugo",
    "Armand Silvestre": "Armand Silvestre", "Leconte de Lisle": "Leconte de Lisle",
    "R. Franz": "Robert Franz", "Joseph von Eichendorff": "Joseph von Eichendorff",
    "Friedrich von Bodenstedt": "Friedrich von Bodenstedt", "C. E. Horsley": "Charles Edward Horsley",
    "Paul Gerhardt": "Paul Gerhardt", "J. Hullah": "John Pyke Hullah",
    "A. Procter": "Adelaide Anne Procter", "E. Lalo": "Édouard Lalo",
    "J. B. Lully": "Jean-Baptiste Lully", "P. Quinault": "Philippe Quinault",
    "F. Schubert": "Franz Schubert", "W. Müller": "Wilhelm Müller",
    "R. Schumann": "Robert Schumann", "H. Heine": "Heinrich Heine",
    "J. F. Wade": "John Francis Wade",
}


def committed_first():
    """S15: refuse to run on an uncommitted edit of this file, or before it is committed."""
    me = Path(__file__).name
    a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
    b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", me], cwd=HERE)
    if a.returncode or b.returncode:
        sys.exit(f"{me} is not committed as it stands: commit the rules before running")


# ---------------------------------------------------------------- survey (rule 1)

def cells_of(table_html):
    rows = re.findall(r"<tr>(.*?)</tr>", table_html, re.S)
    out = []
    for r in rows:
        cs = re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)
        out.append([" ".join(html.unescape(re.sub(r"<[^>]+>", " ", c)).split()) for c in cs])
    return out


def survey():
    committed_first()
    out, start = [], 0
    while True:
        page = R2.get_text(SURVEY_URL.format(start), f"mutopia/r3-list-voice-{start}.html")
        tables = re.findall(r'<table class="table-bordered result-table">(.*?)</table>', page, re.S)
        for t in tables:
            rows = cells_of(t)
            pid = re.search(r"piece-info\.cgi\?id=(\d+)", t)
            ly = re.findall(r'href="(https://www\.mutopiaproject\.org/ftp/[^"]+\.ly)"', t)
            lyz = re.findall(r'href="(https://www\.mutopiaproject\.org/ftp/[^"]+-lys\.zip)"', t)
            mid = re.findall(r'href="(https://www\.mutopiaproject\.org/ftp/[^"]+\.midi?)"', t)
            midz = re.findall(r'href="(https://www\.mutopiaproject\.org/ftp/[^"]+-mids\.zip)"', t)
            r0 = rows[0] + [""] * 4
            r1 = (rows[1] if len(rows) > 1 else []) + [""] * 4
            r2 = (rows[2] if len(rows) > 2 else []) + [""] * 4
            # the fourth cell of the first row is Mutopia's Lyricist(s), of the
            # second its Arranger(s), as its piece pages label them (first
            # parsed as "extra" and "poet": corrected after the first screen,
            # from the cached pages, before any file was read; README)
            na = lambda c: "" if c.strip().lower() in ("n/a", "none") else c  # noqa: E731
            out.append(dict(id=int(pid[1]) if pid else None, title=r0[0], composer=r0[1], opus=r0[2],
                            poet=na(r0[3]), instrument=r1[0], date=r1[1], style=r1[2], arranger=na(r1[3]),
                            source=r2[0], licence=r2[1], ly=ly, ly_zip=lyz, mid=mid, mid_zip=midz))
        print(f"startat={start}: {len(tables)} pieces")
        if f"startat={start + PAGE}&" not in page.replace("&amp;", "&"):
            break
        start += PAGE
    json.dump(out, open(RES / "r3-survey.json", "w"), indent=1, ensure_ascii=False)
    print(len(out), "voice pieces listed")


# ---------------------------------------------------------------- screen (rules 2, 3)

def people_in(cell):
    """A person cell -> [(name, died or None, anonymous)]; '' -> []."""
    cell = re.sub(r"^\s*(by|words by|text by|lyrics by)\s+", "", cell, flags=re.I).strip()
    if not cell:
        return []
    # split between people: ' and ', ' & ', ';', and commas that follow a closing date
    parts = re.split(r"\s+(?:and|&)\s+|;\s*|(?<=\))\s*,\s*", cell)
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        m = DATES.search(p)
        name = DATES.sub("", p).strip(" ,")
        died = None
        if m:
            died = int(m[2] or m[3])
        out.append(dict(name=name, died=died, anonymous=bool(ANON.match(name))))
    return out


def edition_year(src):
    """Rule 2d: the latest four-digit year 1450-2029 the source cell names
    (an edition's year; the latest, so a reprint is never dated earlier)."""
    ys = [int(y) for y in re.findall(r"(?<!\d)(1[4-9]\d\d|20[0-2]\d)(?!\d)", src)]
    return max(ys) if ys else None


def rights(parts, pub):
    """Round 1's rules (run.py `passes`, verify) on one edition: every part is
    published by `pub`. Returns us, life70, life100 as round 1 computes them."""
    us = pub is not None and pub <= YEAR - 96
    l70 = R.passes([(ps, pub) for ps in parts], YEAR - 71, YEAR - 71)
    l100 = R.passes([(ps, pub) for ps in parts], YEAR - 101, YEAR - 101)
    return dict(us=us, life70=l70, life100=l100)


def as_parts(people):
    """Named people into round 1's form; anonymous segments drop out, so a
    part of only anonymous segments is an anonymous part (published-by rule)."""
    return [dict(name=p["name"], died_eff=p["died"]) for p in people if not p["anonymous"]]


def screen_one(s, verified_titles):
    why = []
    if s["licence"] != "Public Domain":
        why.append("2a licence " + (s["licence"] or "none"))
    poets = people_in(s["poet"])
    if not poets:
        why.append("2b no words named (poet cell empty)")
    comps = people_in(s["composer"])
    if not comps:
        why.append("2c composer cell empty")
    arrs = people_in(s["arranger"])
    for p in comps + poets + arrs:
        if not p["anonymous"] and p["died"] is None:
            why.append(f"2c no death year: {p['name']}")
    pub = edition_year(s["source"])
    if pub is None:
        why.append("2d no edition year in the source cell")
    r = rights([as_parts(comps), as_parts(poets)] + ([as_parts(arrs)] if as_parts(arrs) else []), pub)
    if not (r["us"] and r["life100"]):
        why.append(f"2e rights us={r['us']} life100={r['life100']} (edition {pub})")
    if not (s["mid"] or s["mid_zip"]) or not (s["ly"] or s["ly_zip"]):
        why.append("2f no MIDI or LilyPond file listed")
    t = re.sub(r"[^a-z]", "", s["title"].lower())
    dup = [v for v in verified_titles if v and (v in t or t in v)]
    if s["id"] in SAME_TUNE:
        dup.append(SAME_TUNE[s["id"]] + " (the same tune)")
    if dup:
        why.append("2g a verified phrase sets it: " + ", ".join(dup))
    return dict(id=s["id"], title=s["title"], style=s["style"], genre=GENRE.get(s["style"], "other"),
                composer=comps, poet=poets, arranger=arrs, edition=s["source"], edition_year=pub, rights=r,
                eligible=not why, why=why)


def rights_probe():
    """Rule 2e's check, run before the screen is trusted (S15): a case that
    must pass and three that must fail, each differing in its input."""
    ok = rights([[dict(name="x", died_eff=1900)], []], 1920)
    late_pub = rights([[dict(name="x", died_eff=1900)], []], 1931)
    late_death = rights([[dict(name="x", died_eff=1926)], []], 1920)
    unknown = rights([[dict(name="x", died_eff=None)], []], 1920)
    anon_late = rights([[], []], 1926)
    res = dict(must_pass=ok["us"] and ok["life100"],
               must_fail_pub_1931=not (late_pub["us"] and late_pub["life100"]),
               must_fail_death_1926=not (late_death["us"] and late_death["life100"]),
               must_fail_death_unknown=not (unknown["us"] and unknown["life100"]),
               must_fail_anonymous_published_1926=not (anon_late["us"] and anon_late["life100"]))
    assert all(res.values()), res
    return res


def verified_titles():
    s2 = json.load(open(RES / "r2-summary.json"))
    r1 = json.load(open(RES / "summary.json"))["survive"]["per_phrase"]
    import library as L
    now = dict(r1)
    now.update({k: v["round2"] for k, v in s2["per_phrase"].items()})
    by = {c["id"]: c for c in L.CANDIDATES + L.ORIGINALS}
    return {k: re.sub(r"[^a-z]", "", by[k]["title"].lower()) for k, v in now.items() if v.startswith("verified")}


def library_genres():
    """The verified library's genres before round 3 (round 2's count)."""
    return Counter(json.load(open(RES / "r2-summary.json"))["verified_genres"])


def order(el, taken=None):
    """Rule 3. No eligible piece sets a pending phrase's tune (checked by
    title against round 2's PENDING list by the agent from the metadata:
    none of the 21 does), so the order is the genre rule alone. `taken`
    lists the ids already taken; the order of the rest is recomputed from
    the counts so far, so an excluded piece does not count."""
    g = library_genres()
    for pid in taken or []:
        g[next(r for r in el if r["id"] == pid)["genre"]] += 1
    rest = [r for r in el if r["id"] not in set(taken or [])]
    seq = []
    while rest:
        r = min(rest, key=lambda r: (g[r["genre"]], r["id"]))
        seq.append(r["id"])
        g[r["genre"]] += 1
        rest.remove(r)
    return seq


def screen():
    committed_first()
    probe = rights_probe()
    vt = verified_titles()
    assert len(vt) == 20, len(vt)
    sv = json.load(open(RES / "r3-survey.json"))
    rows = [screen_one(s, list(vt.values())) for s in sv]
    el = [r for r in rows if r["eligible"]]
    out = dict(rights_probe=probe, listed=len(rows), eligible=len(el), order=order(el),
               reasons=dict(Counter(w.split(" ")[0] for r in rows for w in r["why"])),
               eligible_by_genre=dict(Counter(r["genre"] for r in el)), rows=rows)
    json.dump(out, open(RES / "r3-screen.json", "w"), indent=1, ensure_ascii=False)
    print({k: v for k, v in out.items() if k != "rows"})
    for r in el:
        print(f"  {r['id']:5d} {r['genre']:12s} {r['title'][:40]:40s} {r['edition'][:50]}")


if __name__ == "__main__":
    {"survey": survey, "screen": screen}[sys.argv[1]]()
