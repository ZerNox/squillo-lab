"""E-004 fold 2 (squillo iteration 58): the library's 30 phrases written as squillo item files.

    uv run python fold.py <squillo>      # -> results/items/*.json, results/fold2.json

Writes round 1's 19 verified phrases and round 2's Abide with Me from results/library.json, and
round 3's 10 from results/r3-library.json, as squillo `exercises` format_version 3 items (squillo
ADR 0005), then checks them:

  L  a crude loader of squillo's `exercises` EX-001 to EX-011, itself checked first on every file in
     squillo's fixtures/exercises/ against the outcome each scenario states (must pass and must fail);
  B  ADR 0005's rights and licence rules as `build` BU-008 states them, checked first on squillo's
     fixtures for each failing rule (must fail) and on public-domain-phrase.json (must pass);
  R  round trip: each item's notes against the round's own record, exact; amazing-grace's item
     against squillo's fixtures/exercises/public-domain-phrase.json, member for member;
  C  each phrase's conditions from round 3's rule 5(e), recomputed from the item.

Crude, disposable lab code: never product code (squillo PLAN.md rule 11).
"""

import json
import re
import sys
import unicodedata
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).parent
RES = HERE / "results"
OUT = RES / "items"

# ---------------------------------------------------------------- rules, written before the run

# Round 1's status names for a phrase whose melody matched a transcription; round 2's for its one.
VERIFIED = {"verified-public-domain", "verified-original"}
ROUND2_VERIFIED = "abide-with-me"

# A phrase's instructions: squillo's own text, one template per genre noun (public-domain-phrase.json's
# "Sing the first line of the hymn, ..." is the hymn case). An original is a line written for squillo.
NOUN = {"hymn": "hymn", "carol": "carol"}
def instructions(genre, origin):
    if origin == "original":
        return "Sing the line, unaccompanied, at a steady pace."
    return f"Sing the first line of the {NOUN.get(genre, 'song')}, unaccompanied, at a steady pace."

# Round 3: language read by hand where the stop-word guess had too few words (README, round 3 limits).
R3_LANGUAGE = {"mutopia-905": "en", "mutopia-373": "de"}

# Round 3: corrections to the extracted words, each with its reason. Only a hyphen inside a word that
# the transcription's syllable break hides (README, round 3 limits: `peut -- être`).
R3_WORDS = {"mutopia-587": ("Captive et peutêtre oubliée,", "Captive et peut-être oubliée,",
                            "the source writes `peut -- être`, a syllable break inside the French word peut-être")}

# Round 3: the sources that state no metronome mark, so the tempo is LilyPond's default (README).
R3_NO_MARK = {"mutopia-607", "mutopia-648", "mutopia-368", "mutopia-373"}

# Round 3: which part a Mutopia role belongs to.
R3_PART = {"composer": "tune", "arranger": "tune", "poet": "words", "lyricist": "words", "translator": "words"}

# Round 3's conditions (round3.py rule 5(e)), recomputed here from each item.
COND = dict(notes=(5, 20), range_max=16, seconds_max=15.0, shortest_min=0.1, low="E2", high="C6")

# ADR 0005's rights rules as at 2026-01-01, as squillo `build` BU-008 states them.
US_LAST, LIFE100_LAST = 1930, 1925
PD_LICENCE, ORIGINAL_LICENCE = "CC-PDM-1.0", "LicenseRef-squillo-adr-0008"

# What each squillo fixture's scenario states the loader does: None accepts, else (requirement, pointer).
# From squillo openspec/specs/exercises/spec.md, read for this fold; pairs loaded together are below.
EXPECT = {
    "own-song-exercise.json": None, "phrase-exercise.json": None, "phrase.json": None,
    "public-domain-phrase.json": None, "unlisted-licence.json": None, "late-publication.json": None,
    # added in squillo iteration 58 with EX-011's new scenario: this fold's the-spirit-of-god.json, byte for byte
    "edition-phrase.json": None,
    "malformed.json": ("EX-001", ""), "unknown-kind.json": ("EX-001", "/kind"),
    "format-1-track.json": ("EX-002", "/format_version"), "format-2-phrase.json": ("EX-002", "/format_version"),
    "bad-exercise-id.json": ("EX-003", "/exercise_id"), "bad-phrase-id.json": ("EX-003", "/phrase_id"),
    "no-analyzers.json": ("EX-005", "/analyzers"), "duplicate-analyzer.json": ("EX-005", "/analyzers/1/analyzer_id"),
    "phrase-with-analyzers.json": ("EX-006", "/analyzers"), "unknown-member.json": ("EX-006", "/tempo"),
    "duplicate-member-name.json": ("EX-006", "/title"), "missing-licence.json": ("EX-006", "/content/licence"),
    "invalid-licence.json": ("EX-007", "/content/licence"), "unknown-subject.json": ("EX-009", "/subject"),
    "bad-pitch.json": ("EX-010", "/melody/notes/2/pitch"), "bad-duration.json": ("EX-010", "/melody/notes/0/quarters"),
    "bad-language.json": ("EX-010", "/language"), "bad-genre.json": ("EX-010", "/genre"),
    "original-with-provenance.json": ("EX-006", "/content/provenance"),
    "missing-provenance.json": ("EX-006", "/content/provenance"), "unknown-origin.json": ("EX-011", "/content/origin"),
    "bad-death-year.json": ("EX-011", "/content/provenance/words/contributors/0/died"),
}
EXPECT_TOGETHER = [("own-song-exercise.json", "duplicate-exercise-id.json", "EX-004", "/exercise_id")]
# build BU-008's scenarios: file -> None (ships) or the pointer it fails at.
EXPECT_BUILD = {
    "exercises/public-domain-phrase.json": None,
    "exercises/late-publication.json": "/content/provenance/tune/published_by",
    "build/late-death.json": "/content/provenance/words/contributors/0/died",
    "build/anonymous-after-1925.json": "/content/provenance/tune/published_by",
    "build/public-domain-other-licence.json": "/content/licence",
    "build/original-other-licence.json": "/content/licence",
}

# ---------------------------------------------------------------- the loader (EX-001 to EX-011)

class Refused(Exception):
    def __init__(self, req, ptr):
        super().__init__(f"{req} at {ptr!r}")
        self.req, self.ptr = req, ptr

KEBAB = re.compile(r"[a-z][a-z0-9]*(-[a-z0-9]+)*\Z")
KEY = re.compile(r"[A-G][#b]?m?\Z")
METER = re.compile(r"[1-9][0-9]*/(1|2|4|8|16|32)\Z")
PITCH = re.compile(r"[A-G][#b]?[0-9]\Z")
QUARTERS = re.compile(r"[1-9][0-9]*(/[1-9][0-9]*)?\Z")
IDSTRING = re.compile(r"[A-Za-z0-9.\-]+\Z")
# RFC 5646 §2.1, well-formed only: langtag, privateuse, grandfathered (irregular and regular).
_LANG = r"(?:[A-Za-z]{2,3}(?:-[A-Za-z]{3}){0,3}|[A-Za-z]{4}|[A-Za-z]{5,8})"
_LANGTAG = (rf"{_LANG}(?:-[A-Za-z]{{4}})?(?:-(?:[A-Za-z]{{2}}|[0-9]{{3}}))?"
            r"(?:-(?:[A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3}))*"
            r"(?:-[0-9A-WY-Za-wy-z](?:-[A-Za-z0-9]{2,8})+)*(?:-[xX](?:-[A-Za-z0-9]{1,8})+)?")
_PRIVATE = r"[xX](?:-[A-Za-z0-9]{1,8})+"
_GRANDFATHERED = ("en-GB-oed|i-ami|i-bnn|i-default|i-enochian|i-hak|i-klingon|i-lux|i-mingo|i-navajo|i-pwn|"
                  "i-tao|i-tay|i-tsu|sgn-BE-FR|sgn-BE-NL|sgn-CH-DE|art-lojban|cel-gaulish|no-bok|no-nyn|"
                  "zh-guoyu|zh-hakka|zh-min|zh-min-nan|zh-xiang")
LANGUAGE = re.compile(rf"(?:{_LANGTAG}|{_PRIVATE}|(?:{_GRANDFATHERED}))\Z", re.IGNORECASE)

def spdx_ok(s):
    """SPDX 2.3 Annex D grammar: ids as idstring, operators AND, OR, WITH (case-sensitive), parentheses."""
    toks = re.findall(r"\(|\)|[^\s()]+", s)
    if not toks or "".join(toks) != re.sub(r"\s+", "", s):
        return False
    pos = 0
    def simple():
        nonlocal pos
        if pos >= len(toks):
            return False
        t = toks[pos]
        if t in ("AND", "OR", "WITH", "(", ")"):
            return False
        t = t[:-1] if t.endswith("+") else t
        if t.startswith("DocumentRef-"):
            if ":" not in t:
                return False
            a, b = t.split(":", 1)
            ok = IDSTRING.match(a[12:]) and b.startswith("LicenseRef-") and IDSTRING.match(b[11:])
        elif t.startswith("LicenseRef-"):
            ok = IDSTRING.match(t[11:])
        else:
            ok = IDSTRING.match(t)
        pos += 1
        return bool(ok)
    def term():
        nonlocal pos
        if pos < len(toks) and toks[pos] == "(":
            pos += 1
            if not expr() or pos >= len(toks) or toks[pos] != ")":
                return False
            pos += 1
            return True
        if not simple():
            return False
        if pos < len(toks) and toks[pos] == "WITH":
            pos += 1
            if pos >= len(toks) or not IDSTRING.match(toks[pos]):
                return False
            pos += 1
        return True
    def expr():
        nonlocal pos
        if not term():
            return False
        while pos < len(toks) and toks[pos] in ("AND", "OR"):
            pos += 1
            if not term():
                return False
        return True
    return expr() and pos == len(toks)

def _pairs(pairs):
    seen = set()
    for k, _ in pairs:
        if k in seen:
            raise _Dup(k)
        seen.add(k)
    return dict(pairs)

class _Dup(Exception):
    pass

def _dup_pointer(text):
    """The JSON Pointer of the first repeated member, in document order."""
    raw = json.JSONDecoder(object_pairs_hook=lambda p: ("obj", p)).decode(text)
    def walk(o, ptr):
        if isinstance(o, tuple) and o[0] == "obj":
            seen = set()
            for k, _ in o[1]:
                if k in seen:
                    return f"{ptr}/{k}"
                seen.add(k)
            for k, v in o[1]:
                r = walk(v, f"{ptr}/{k}")
                if r:
                    return r
        elif isinstance(o, list):
            for i, v in enumerate(o):
                r = walk(v, f"{ptr}/{i}")
                if r:
                    return r
        return None
    return walk(raw, "") or ""

def exact(o, ptr, members):
    if not isinstance(o, dict):
        raise Refused("EX-006", ptr)
    for k in o:
        if k not in members:
            raise Refused("EX-006", f"{ptr}/{k}")
    for k in members:
        if k not in o:
            raise Refused("EX-006", f"{ptr}/{k}")

def nonempty(o, key, ptr, req):
    if not isinstance(o[key], str) or not o[key]:
        raise Refused(req, f"{ptr}/{key}")

def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)

EXERCISE = ["format_version", "kind", "exercise_id", "title", "instructions", "subject", "analyzers", "content"]
PHRASE = ["format_version", "kind", "phrase_id", "title", "instructions", "genre", "language", "words", "melody", "content"]

def load(text):
    """One file's text -> its item, or raise Refused. Integers are kept apart from floats: a JSON number
    with a fraction or exponent part is parsed as float, so `is_int` is 'no fraction or exponent'."""
    try:
        o = json.loads(text, object_pairs_hook=_pairs)
    except _Dup:
        raise Refused("EX-006", _dup_pointer(text))
    except ValueError:
        raise Refused("EX-001", "")
    if not isinstance(o, dict):
        raise Refused("EX-001", "")
    if o.get("format_version") != 3 or not is_int(o.get("format_version")):
        raise Refused("EX-002", "/format_version")
    kind = o.get("kind")
    if kind not in ("exercise", "phrase"):
        raise Refused("EX-001", "/kind")
    exact(o, "", EXERCISE if kind == "exercise" else PHRASE)
    c = o["content"]
    if kind == "exercise":
        exact(c, "/content", ["licence", "source"])
    else:
        if not isinstance(c, dict):
            raise Refused("EX-006", "/content")
        origin = c.get("origin")
        if origin == "original":
            exact(c, "/content", ["licence", "source", "origin"])
        elif origin == "public-domain":
            exact(c, "/content", ["licence", "source", "origin", "provenance", "melody_checked_against"])
            exact(c["provenance"], "/content/provenance", ["words", "tune"])
            for part in ("words", "tune"):
                p = c["provenance"][part]
                pp = f"/content/provenance/{part}"
                exact(p, pp, ["contributors", "published_by", "edition"])
                if not isinstance(p["contributors"], list):
                    raise Refused("EX-011", f"{pp}/contributors")
                for i, who in enumerate(p["contributors"]):
                    exact(who, f"{pp}/contributors/{i}", ["name", "role", "died"])
        else:
            for k in c:
                if k not in ("licence", "source", "origin", "provenance", "melody_checked_against"):
                    raise Refused("EX-006", f"/content/{k}")
            raise Refused("EX-011", "/content/origin")
        if kind == "phrase":
            exact(o["melody"], "/melody", ["key", "meter", "tempo_qpm", "notes"])
            if isinstance(o["melody"]["notes"], list):
                for i, n in enumerate(o["melody"]["notes"]):
                    exact(n, f"/melody/notes/{i}", ["pitch", "quarters"])
    if kind == "exercise":
        if "analyzers" in o and isinstance(o["analyzers"], list):
            for i, a in enumerate(o["analyzers"]):
                exact(a, f"/analyzers/{i}", ["analyzer_id", "parameters"])
    # EX-001: title and instructions
    for k in ("title", "instructions"):
        nonempty(o, k, "", "EX-001")
    idk = "exercise_id" if kind == "exercise" else "phrase_id"
    if not isinstance(o[idk], str) or not KEBAB.match(o[idk]):
        raise Refused("EX-003", f"/{idk}")
    if kind == "exercise":
        if o["subject"] not in ("own-song", "phrase"):
            raise Refused("EX-009", "/subject")
        a = o["analyzers"]
        if not isinstance(a, list) or not a:
            raise Refused("EX-005", "/analyzers")
        seen = set()
        for i, e in enumerate(a):
            if not isinstance(e["analyzer_id"], str) or not KEBAB.match(e["analyzer_id"]):
                raise Refused("EX-005", f"/analyzers/{i}/analyzer_id")
            if not isinstance(e["parameters"], dict):
                raise Refused("EX-005", f"/analyzers/{i}/parameters")
            if e["analyzer_id"] in seen:
                raise Refused("EX-005", f"/analyzers/{i}/analyzer_id")
            seen.add(e["analyzer_id"])
    else:
        if not isinstance(o["words"], str) or not o["words"]:
            raise Refused("EX-010", "/words")
        if not isinstance(o["language"], str) or not LANGUAGE.match(o["language"]):
            raise Refused("EX-010", "/language")
        if not isinstance(o["genre"], str) or not KEBAB.match(o["genre"]):
            raise Refused("EX-010", "/genre")
        m = o["melody"]
        if not isinstance(m["key"], str) or not KEY.match(m["key"]):
            raise Refused("EX-010", "/melody/key")
        if not isinstance(m["meter"], str) or not METER.match(m["meter"]):
            raise Refused("EX-010", "/melody/meter")
        if not is_int(m["tempo_qpm"]) or m["tempo_qpm"] <= 0:
            raise Refused("EX-010", "/melody/tempo_qpm")
        if not isinstance(m["notes"], list) or not m["notes"]:
            raise Refused("EX-010", "/melody/notes")
        for i, n in enumerate(m["notes"]):
            if not isinstance(n["pitch"], str) or not PITCH.match(n["pitch"]):
                raise Refused("EX-010", f"/melody/notes/{i}/pitch")
            if not isinstance(n["quarters"], str) or not QUARTERS.match(n["quarters"]):
                raise Refused("EX-010", f"/melody/notes/{i}/quarters")
    nonempty(c, "source", "/content", "EX-007")
    if not isinstance(c["licence"], str) or not spdx_ok(c["licence"]):
        raise Refused("EX-007", "/content/licence")
    if kind == "phrase" and c["origin"] == "public-domain":
        for part in ("words", "tune"):
            p = c["provenance"][part]
            pp = f"/content/provenance/{part}"
            for i, who in enumerate(p["contributors"]):
                for k in ("name", "role"):
                    if not isinstance(who[k], str) or not who[k]:
                        raise Refused("EX-011", f"{pp}/contributors/{i}/{k}")
                if not is_int(who["died"]):
                    raise Refused("EX-011", f"{pp}/contributors/{i}/died")
            if not is_int(p["published_by"]):
                raise Refused("EX-011", f"{pp}/published_by")
            if not isinstance(p["edition"], str) or not p["edition"]:
                raise Refused("EX-011", f"{pp}/edition")
        if not isinstance(c["melody_checked_against"], str) or not c["melody_checked_against"]:
            raise Refused("EX-011", "/content/melody_checked_against")
    return o

def load_together(texts):
    """EX-004: names loaded together; every file sharing an identifier within a kind is refused."""
    out, refused = {}, {}
    for name, t in texts.items():
        try:
            out[name] = load(t)
        except Refused as r:
            refused[name] = (r.req, r.ptr)
    for kind, idk in (("exercise", "exercise_id"), ("phrase", "phrase_id")):
        by = {}
        for name, o in out.items():
            if o["kind"] == kind:
                by.setdefault(o[idk], []).append(name)
        for names in by.values():
            if len(names) > 1:
                for n in names:
                    refused[n] = ("EX-004", f"/{idk}")
    return {n: o for n, o in out.items() if n not in refused}, refused

# ---------------------------------------------------------------- the build's rights rules (BU-008)

def build_rights(o):
    """None if the phrase may ship, else the pointer of the first value that fails, in BU-008's order."""
    c = o["content"]
    if c["origin"] == "original":
        return None if c["licence"] == ORIGINAL_LICENCE else "/content/licence"
    for part in ("words", "tune"):
        p = c["provenance"][part]
        if p["published_by"] > US_LAST:
            return f"/content/provenance/{part}/published_by"
    for part in ("words", "tune"):
        p = c["provenance"][part]
        for i, who in enumerate(p["contributors"]):
            if who["died"] > LIFE100_LAST:
                return f"/content/provenance/{part}/contributors/{i}/died"
        if not p["contributors"] and p["published_by"] > LIFE100_LAST:
            return f"/content/provenance/{part}/published_by"
    if c["licence"] != PD_LICENCE:
        return "/content/licence"
    return None

# ---------------------------------------------------------------- writing the items

def q(dec):
    f = Fraction(Decimal(dec)) if not isinstance(dec, Fraction) else dec
    assert f > 0
    return str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"

def r1_notes(s):
    out = []
    for tok in s.split():
        p, d = tok.split(":")
        out.append({"pitch": p, "quarters": q(d)})
    return out

def r1_editions(source):
    m = re.fullmatch(r"Words: (.+?)\. Tune: (.+?)\. Melody line transcribed for squillo\.", source)
    assert m, source
    words, tune = m.group(1), m.group(2)
    return words, (words if tune == "as the text" else tune)

def r1_item(p, ref2):
    c = p["content"]
    origin = "original" if p["status"] == "verified-original" else "public-domain"
    item = {"format_version": 3, "kind": "phrase", "phrase_id": p["phrase_id"], "title": p["title"],
            "instructions": instructions(p["genre"], origin), "genre": p["genre"].replace(" ", "-"),
            "language": p["language"], "words": p["words"],
            "melody": {"key": p["melody"]["key"], "meter": p["melody"]["meter"],
                       "tempo_qpm": p["melody"]["tempo_qpm"], "notes": r1_notes(p["melody"]["notes"])}}
    content = {"licence": c["licence"], "source": c["source"], "origin": origin}
    if origin == "public-domain":
        we, te = r1_editions(c["source"])
        r = c["rights"]
        content["provenance"] = {
            part: {"contributors": [{"name": b["name"], "role": b["role"], "died": b["died"]} for b in r[key]["by"]],
                   "published_by": r[key]["published_by"], "edition": ed}
            for part, key, ed in (("words", "text", we), ("tune", "tune", te))}
        if p["phrase_id"] == ROUND2_VERIFIED:
            content["melody_checked_against"] = (f"Mutopia piece {ref2['piece']}, the Public Domain transcription "
                                                 f"of {ref2['edition']} (E-004 round 2, matched in pitch and rhythm)")
        else:
            content["melody_checked_against"] = c["melody_checked_against"]["transcription"]
    item["content"] = content
    return item

def slug(title):
    t = unicodedata.normalize("NFKD", title.replace("\u2019", "-")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")

def r3_item(p):
    pid = p["id"]
    pv = p["provenance"]
    qpm = round(p["tempo_qpm"])
    # A MIDI tempo is a whole number of microseconds per quarter note, so the file's qpm is the edition's
    # whole-number mark up to one microsecond: |qpm_file - qpm| <= qpm^2 / 6e7 (d(6e7/x)/dx at one us).
    assert abs(p["tempo_qpm"] - qpm) <= qpm * qpm / 6e7, (pid, p["tempo_qpm"])
    words = p["words"]
    if pid in R3_WORDS:
        was, now, _ = R3_WORDS[pid]
        assert words == was, (pid, words)
        words = now
    language = p["language"] or R3_LANGUAGE[pid]
    parts = {"words": [], "tune": []}
    for who in pv["contributors"]:
        parts[R3_PART[who["role"]]].append({"name": who["name"], "role": who["role"], "died": who["died_eff"]})
    edition = f"{pv['edition']}, as transcribed in {pv['transcription']}"
    mark = (" The edition gives no metronome mark: the tempo is the transcription's MIDI default."
            if pid in R3_NO_MARK else "")
    fix = ""
    if pid in R3_WORDS:
        fix = f" Words corrected from the extracted \"{R3_WORDS[pid][0]}\": {R3_WORDS[pid][2]}."
    source = (f"Notes and words of the first line taken from the edition: {pv['edition']}, in the Mutopia Project's "
              f"Public Domain transcription ({pv['transcription']}), squillo-lab E-004 round 3.{mark}{fix}")
    item = {"format_version": 3, "kind": "phrase", "phrase_id": slug(p["title"]), "title": p["title"],
            "instructions": instructions(p["genre"], "public-domain"), "genre": p["genre"],
            "language": language, "words": words,
            "melody": {"key": p["key"], "meter": p["meter"], "tempo_qpm": qpm,
                       "notes": [{"pitch": n["pitch"], "quarters": q(Fraction(n["beats"]))} for n in p["notes"]]},
            "content": {"licence": p["licence"], "source": source, "origin": "public-domain",
                        "provenance": {part: {"contributors": parts[part], "published_by": pv["edition_year"],
                                              "edition": edition} for part in ("words", "tune")},
                        "melody_checked_against": (f"taken from {pv['transcription']}, the transcription of the "
                                                   f"edition, not checked against an independent one (E-004 round 3)")}}
    return item

# ---------------------------------------------------------------- conditions (round 3 rule 5(e))

STEP = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
def midi(p):
    m = re.fullmatch(r"([A-G])([#b]?)([0-9])", p)
    return 12 * (int(m.group(3)) + 1) + STEP[m.group(1)] + {"": 0, "#": 1, "b": -1}[m.group(2)]

def conditions(o):
    m = o["melody"]
    ps = [midi(n["pitch"]) for n in m["notes"]]
    secs = [float(Fraction(n["quarters"])) * 60.0 / m["tempo_qpm"] for n in m["notes"]]
    return dict(notes=len(ps), range=max(ps) - min(ps), seconds=round(sum(secs), 3),
                shortest_s=round(min(secs), 4), low=min(ps), high=max(ps))

# ---------------------------------------------------------------- main

def dump(o):
    return json.dumps(o, indent=2, ensure_ascii=False) + "\n"

def main(squillo):
    squillo = Path(squillo)
    fx = squillo / "fixtures"
    report = {}

    # L: the loader on squillo's own fixtures first (must pass and must fail, each known from the spec).
    texts = {p.name: p.read_text(encoding="utf-8") for p in sorted((fx / "exercises").glob("*.json"))}
    assert set(texts) == set(EXPECT) | {b for _, b, _, _ in EXPECT_TOGETHER}, sorted(set(texts) ^ set(EXPECT))
    lchk = {}
    for name, want in EXPECT.items():
        try:
            load(texts[name])
            got = None
        except Refused as r:
            got = (r.req, r.ptr)
        lchk[name] = dict(want=want, got=got, ok=got == want)
    for a, b, req, ptr in EXPECT_TOGETHER:
        for order in ((a, b), (b, a)):
            acc, ref = load_together({n: texts[n] for n in order})
            ok = not acc and ref == {a: (req, ptr), b: (req, ptr)}
            lchk[f"{order[0]}+{order[1]}"] = dict(want=[req, ptr], got={k: list(v) for k, v in ref.items()}, ok=ok)
    report["L_fixtures"] = dict(cases=len(lchk), must_pass=sum(v["want"] is None for v in lchk.values()),
                                ok=sum(v["ok"] for v in lchk.values()),
                                failed={k: v for k, v in lchk.items() if not v["ok"]})
    assert not report["L_fixtures"]["failed"], report["L_fixtures"]["failed"]

    # B: the rights rules on squillo's build fixtures (must pass 1, must fail 5).
    bchk = {}
    for rel, want in EXPECT_BUILD.items():
        got = build_rights(load((fx / rel).read_text(encoding="utf-8")))
        bchk[rel] = dict(want=want, got=got, ok=got == want)
    report["B_fixtures"] = dict(cases=len(bchk), ok=sum(v["ok"] for v in bchk.values()),
                                failed={k: v for k, v in bchk.items() if not v["ok"]})
    assert not report["B_fixtures"]["failed"], report["B_fixtures"]["failed"]

    # Write the 30.
    lib = json.load(open(RES / "library.json"))["items"]
    ref2 = json.load(open(RES / "r2-summary.json"))["per_phrase"][ROUND2_VERIFIED]["reference"]
    r1 = [p for p in lib if p["status"] in VERIFIED or p["phrase_id"] == ROUND2_VERIFIED]
    r3 = json.load(open(RES / "r3-library.json"))
    items = [(1 if p["phrase_id"] != ROUND2_VERIFIED else 2, r1_item(p, ref2)) for p in r1] + [(3, r3_item(p)) for p in r3]
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.json"):
        old.unlink()
    for _, o in items:
        (OUT / f"{o['phrase_id']}.json").write_text(dump(o), encoding="utf-8")

    # L and B on the 30, loaded together from their files.
    acc, ref = load_together({p.name: p.read_text(encoding="utf-8") for p in sorted(OUT.glob("*.json"))})
    report["L_items"] = dict(files=len(acc) + len(ref), accepted=len(acc), refused={k: list(v) for k, v in ref.items()})
    fails = {n: build_rights(o) for n, o in acc.items()}
    report["B_items"] = dict(ship=sum(v is None for v in fails.values()), fail={k: v for k, v in fails.items() if v})

    # R: round trips. amazing-grace against squillo's fixture; each item's notes against its round's record.
    pdp = json.loads(texts["public-domain-phrase.json"])
    ag = next(o for _, o in items if o["phrase_id"] == "amazing-grace")
    report["R_fixture_amazing_grace_equal"] = ag == pdp
    # must fail: the same comparison with one note moved a semitone
    ag2 = json.loads(json.dumps(ag)); ag2["melody"]["notes"][0]["pitch"] = "D#4"
    report["R_fixture_must_fail"] = ag2 != pdp
    ep = fx / "exercises" / "edition-phrase.json"
    report["R_edition_fixture_bytes_equal"] = ep.read_bytes() == (OUT / "the-spirit-of-god.json").read_bytes()
    rt = []
    for rnd, o in items:
        if rnd == 3:
            src = next(p for p in r3 if slug(p["title"]) == o["phrase_id"])
            want = [(n["pitch"], Fraction(n["beats"])) for n in src["notes"]]
        else:
            src = next(p for p in r1 if p["phrase_id"] == o["phrase_id"])
            want = [(t.split(":")[0], Fraction(Decimal(t.split(":")[1]))) for t in src["melody"]["notes"].split()]
        got = [(n["pitch"], Fraction(n["quarters"])) for n in o["melody"]["notes"]]
        rt.append(got == want)
    report["R_notes_exact"] = dict(items=len(rt), equal=sum(rt))

    # C: conditions, and the count.
    lo, hi = midi(COND["low"]), midi(COND["high"])
    cond = {o["phrase_id"]: conditions(o) for _, o in items}
    report["C"] = dict(
        within=sum(COND["notes"][0] <= c["notes"] <= COND["notes"][1] and c["range"] <= COND["range_max"]
                   and c["seconds"] <= COND["seconds_max"] and c["shortest_s"] >= COND["shortest_min"]
                   and lo <= c["low"] and c["high"] <= hi for c in cond.values()),
        per_item=cond)
    # must fail: the same conditions on The Storm at a tenth of its tempo (too long, and notes no shorter)
    slow = json.loads(json.dumps(next(o for _, o in items if o["phrase_id"] == "the-storm")))
    slow["melody"]["tempo_qpm"] = 6
    report["C_must_fail"] = conditions(slow)["seconds"] > COND["seconds_max"]
    # must fail: the tempo bound on a file tempo a hundredth of a quarter note per minute off 68
    report["tempo_bound_must_fail"] = not (abs(68.01 - 68) <= 68 * 68 / 6e7)
    by = {}
    for rnd, o in items:
        by.setdefault(o["genre"], []).append(o["phrase_id"])
    report["count"] = dict(
        items=len(items), public_domain=sum(o["content"]["origin"] == "public-domain" for _, o in items),
        original=sum(o["content"]["origin"] == "original" for _, o in items),
        by_round={r: sum(x == r for x, _ in items) for r in (1, 2, 3)},
        genres=len(by), by_genre={g: len(v) for g, v in sorted(by.items(), key=lambda kv: (-len(kv[1]), kv[0]))},
        languages={l: sum(o["language"] == l for _, o in items) for l in sorted({o["language"] for _, o in items})},
        no_metronome_mark=sorted(slug(p["title"]) for p in r3 if p["id"] in R3_NO_MARK),
        words_corrected={slug(p["title"]): R3_WORDS[p["id"]][2] for p in r3 if p["id"] in R3_WORDS})
    (RES / "fold2.json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "C"}, indent=1, ensure_ascii=False))
    print("C within:", report["C"]["within"], "of", len(cond))

if __name__ == "__main__":
    main(sys.argv[1])
