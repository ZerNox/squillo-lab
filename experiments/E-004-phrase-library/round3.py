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


def order(el, taken=None, skip=()):
    """Rule 3. No eligible piece sets a pending phrase's tune (checked by
    title against round 2's PENDING list by the agent from the metadata:
    none of the 21 does), so the order is the genre rule alone. `taken`
    lists the ids already taken; the order of the rest is recomputed from
    the counts so far, so an excluded piece does not count."""
    g = library_genres()
    for pid in taken or []:
        g[next(r for r in el if r["id"] == pid)["genre"]] += 1
    rest = [r for r in el if r["id"] not in set(taken or []) | set(skip)]
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


# ---------------------------------------------------------------- extract (rules 4-6)

SHARP_KEYS = {"C", "G", "D", "A", "E", "B", "F#", "C#", "Am", "Em", "Bm", "F#m", "C#m", "G#m", "D#m", "A#m"}
SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
FLAT = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
# stop-words for the words' language (reported; decides nothing)
STOP = {"en": {"the", "and", "of", "my", "to", "in", "is", "a", "thy", "o", "with", "on", "all"},
        "de": {"und", "der", "die", "das", "ich", "nicht", "mein", "du", "ein", "mit", "zu", "in", "dem", "den"},
        "fr": {"le", "la", "les", "et", "de", "des", "un", "une", "je", "tu", "mon", "ma", "sur", "dans"},
        "it": {"il", "la", "e", "di", "che", "un", "mio", "per", "non"},
        "la": {"et", "in", "est", "deus", "ad", "venite", "domine"}}


def fetch(url):
    name = "r3/" + url.split("/ftp/")[1].replace("/", "__")
    R2.get_text(url, "mutopia/" + name)
    return CACHE / "mutopia" / name


def fix_text(t):
    try:
        return t.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return t


def read_midi(path):
    """Every track's notes (start, end, pitch) and lyric events (time, text),
    plus tpq and the first key, time and tempo events."""
    import mido
    m = mido.MidiFile(path)
    tracks, meta = [], dict(key=None, meter=None, tempo_us=None)
    for ti, tr in enumerate(m.tracks):
        t, on, notes, lyr = 0, {}, [], []
        for msg in tr:
            t += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                on.setdefault(msg.note, []).append(t)
            elif msg.type in ("note_off", "note_on"):
                if on.get(msg.note):
                    notes.append((on[msg.note].pop(0), t, msg.note))
            elif msg.type == "lyrics":
                txt = fix_text(msg.text).strip()
                if txt and txt not in ("_", "__", "--", " "):
                    lyr.append((t, txt))
            elif msg.type == "key_signature" and meta["key"] is None:
                meta["key"] = msg.key
            elif msg.type == "time_signature" and meta["meter"] is None:
                meta["meter"] = f"{msg.numerator}/{msg.denominator}"
            elif msg.type == "set_tempo" and meta["tempo_us"] is None:
                meta["tempo_us"] = msg.tempo
        tracks.append(dict(index=ti, notes=sorted(notes), lyrics=lyr))
    return tracks, m.ticks_per_beat, meta


def skyline(notes):
    """Rule 5b: an onset is a melody note when the highest note sounding then
    starts then."""
    out = []
    for t in sorted({s for s, _, _ in notes}):
        sounding = [(p, s, e) for s, e, p in notes if s <= t < e]
        if not sounding:
            continue
        p, s, e = max(sounding)
        if s == t:
            out.append((s, e, p))
    return out


def phrase_from(tracks, tpq, meta):
    """Rules 5b-5f on one MIDI file. Returns (phrase dict, None) or (None, reason)."""
    vt = next((t for t in tracks if t["lyrics"]), None)
    if vt is None:
        return None, "5a no lyric events"
    syl_all = vt["lyrics"]
    times = [x[0] for x in syl_all]
    cand = [t for t in tracks if t["notes"]]
    if not cand:
        return None, "5b no note track"
    score = [(sum(1 for x in times if x in {n[0] for n in t["notes"]}), -t["index"], t) for t in cand]
    best = max(score, key=lambda x: x[:2])[2]
    mel = skyline(best["notes"])
    j = next((k for k, (_, txt) in enumerate(syl_all[:20]) if k >= 2 and LINE_END.search(txt)), None)
    if j is None:
        return None, "5c no line end within 20 syllables"
    t0 = syl_all[0][0]
    t_next = syl_all[j + 1][0] if j + 1 < len(syl_all) else None
    t_end_syl = syl_all[j][0]
    ph = []
    for s0, e0, p in mel:
        if s0 < t0:
            continue
        if t_next is not None and s0 >= t_next:
            break
        if ph and s0 > ph[-1][1]:  # a rest between the previous note's end and this onset
            if s0 <= t_end_syl:
                return None, f"5c rest inside the line (before tick {s0})"
            break
        ph.append((s0, e0, p))
    if not ph or ph[0][0] != t0:
        return None, "5b first syllable not on a melody note"
    line = syl_all[:j + 1]
    on = {n[0] for n in ph}
    share = sum(1 for t, _ in line if t in on) / len(line)
    if share < ALIGN_MIN:
        return None, f"5c syllables on melody onsets {share:.2f} < {ALIGN_MIN}"
    beats = [Fraction(ph[i + 1][0] - ph[i][0], tpq) for i in range(len(ph) - 1)] + [Fraction(ph[-1][1] - ph[-1][0], tpq)]
    key = meta["key"] or "C"
    names = SHARP if key in SHARP_KEYS else FLAT
    pitch = [f"{names[p % 12]}{p // 12 - 1}" for _, _, p in ph]
    words = ""
    for _, txt in line:
        words += txt[:-1] if txt.endswith("-") else txt + " "
    qpm = 60e6 / meta["tempo_us"] if meta["tempo_us"] else None
    return dict(track=best["index"], lyric_track=vt["index"], tpq=tpq, ticks=[(a, b, c) for a, b, c in ph],
                midi=[p for _, _, p in ph], pitches=pitch, beats=[str(b) for b in beats],
                melody=" ".join(f"{n}:{float(b)!r}" for n, b in zip(pitch, beats)),
                words=" ".join(words.split()), syllables=[t for _, t in line], syllable_ticks=[t for t, _ in line],
                align_share=share, key=key, meter=meta["meter"], tempo_qpm=qpm), None


def conditions(ph):
    """Rule 5e, computed from what was extracted."""
    qpm = ph["tempo_qpm"]
    secs = [float(Fraction(b)) * 60.0 / qpm for b in ph["beats"]] if qpm else None
    c = dict(notes=len(ph["midi"]), range=max(ph["midi"]) - min(ph["midi"]),
             seconds=sum(secs) if secs else None, shortest_s=min(secs) if secs else None,
             lowest=min(ph["midi"]), highest=max(ph["midi"]))
    fails = []
    if not MIN_NOTES <= c["notes"] <= MAX_NOTES:
        fails.append(f"notes {c['notes']}")
    if c["range"] > MAX_RANGE:
        fails.append(f"range {c['range']}")
    if secs is None:
        fails.append("no tempo")
    else:
        if c["seconds"] > MAX_SECONDS:
            fails.append(f"seconds {c['seconds']:.2f}")
        if c["shortest_s"] < MIN_NOTE_S:
            fails.append(f"shortest {c['shortest_s']:.3f} s")
    if c["lowest"] < E2 or c["highest"] > C6:
        fails.append("outside E2-C6")
    c["fails"] = fails
    return c


def k1_round_trip(ph):
    """K1: the library notation parsed by round 1's `parse` against the
    melody line, by round 1's `compare`, exact at scale 1.0; and its two
    must-fail cases, each input asserted to differ."""
    line = [dict(onsets=[a for a, _, _ in ph["ticks"]], pitches=ph["midi"], tpq=ph["tpq"])]
    mine = R.parse(ph["melody"])

    def exact(m):
        r = R.compare(m, line)
        return bool(r and r["exact_pitch"] and r["rhythm"] and r["rhythm"]["ioi_match"] == r["rhythm"]["ioi_total"]
                    and abs(r["rhythm"]["scale"] - 1.0) <= 1e-9 and r["start"] == 0), r
    n = len(mine)
    ip, ir = min(3, n - 1), min(2, n - 2)
    bad_p = [(p + (1 if i == ip else 0), b) for i, (p, b) in enumerate(mine)]
    bad_r = [(p, b * (2 if i == ir else 1)) for i, (p, b) in enumerate(mine)]
    assert bad_p != mine and bad_r != mine
    ok, r = exact(mine)
    fp, _ = exact(bad_p)
    fr, _ = exact(bad_r)
    # the spelled pitches read back as the MIDI numbers
    spelled = [R.midi(x) for x in ph["pitches"]] == ph["midi"]
    return dict(must_pass=ok and spelled, must_fail_pitch=not fp, must_fail_rhythm=not fr,
                spelled_back=spelled, moved_index=ip, doubled_index=ir)


def k2_words(ph):
    """K2: the line's syllables shifted by one tick must fall below ALIGN_MIN."""
    on = {a for a, _, _ in ph["ticks"]}
    shifted = sum(1 for t in ph["syllable_ticks"] if t + 1 in on) / len(ph["syllable_ticks"])
    return dict(must_pass=ph["align_share"] >= ALIGN_MIN, shifted_share=shifted,
                must_fail=shifted < ALIGN_MIN)


def language(words):
    w = re.findall(r"[a-zà-ÿ]+", words.lower())
    sc = {k: sum(1 for x in w if x in v) for k, v in STOP.items()}
    best = max(sc, key=sc.get)
    return best if sc[best] > 0 else None, sc


def ly_header(paths):
    """The LilyPond file's header fields (rule 4c)."""
    out = {}
    for f in paths:
        t = f.read_bytes().decode("utf-8", "replace")
        m = re.search(r"\\header\s*\{(.*?)\n\s*\}", t, re.S)
        if not m:
            continue
        for k, v in re.findall(r'^\s*([A-Za-z]+)\s*=\s*"((?:[^"\\]|\\.)*)"', m[1], re.M):
            out.setdefault(k, v)
    return out


def names_person(v):
    """A header value names a person when it holds a death-date pair or a
    capitalised word (second attempt: a blank field, and Schumann's
    `arranger = "opus 48, n° 7"`, name no one)."""
    return bool(DATES.search(v) or re.search(r"\b[A-ZÀ-Ý][a-zà-ÿ]+", v))


def header_people(paths, hdr):
    """Rule 4c: the header's translator and arranger fields, and a "tr."
    credit anywhere in the header (second attempt: Mutopia 1366 credits
    its translator inside a \\markup poet field)."""
    out = [(k, hdr[k]) for k in ("translator", "arranger") if hdr.get(k) and names_person(hdr[k])]
    for f in paths:
        t = f.read_bytes().decode("utf-8", "replace")
        m = re.search(r"\\header\s*\{(.*?)\n\s*\}", t, re.S)
        if m:
            for v in re.findall(r'"\s*(?:tr\.|transl(?:ated|ation)? by)\s*([^"]+)"', m[1], re.I):
                out.append(("translator", v.strip()))
    return out


def ly_words(paths, syllables):
    """Rule 5f's joins from the LilyPond source (second attempt: MIDI from
    LilyPond 2.12 on carries no hyphen): find the line's syllables in order
    in the source's tokens, skipping `--`, `__`, `_` and commands, and join
    two syllables where a `--` lies between them. None if not found."""
    norm = lambda x: x.strip('"').replace("_", " ").strip()  # noqa: E731
    want = [norm(x) for x in syllables]
    for f in paths:
        t = f.read_bytes().decode("utf-8", "replace")
        t = re.sub(r"%.*", "", t)
        toks = re.findall(r'"(?:[^"\\]|\\.)*"|--|__|[^\s{}]+', t)
        for i in range(len(toks)):
            k, j, joins, prev_hyph = 0, i, [], False
            while j < len(toks) and k < len(want):
                tok = toks[j]
                if tok == "--":
                    prev_hyph = True
                elif tok in ("__", "_") or tok.startswith("\\"):
                    pass
                elif norm(tok) == want[k] or norm(re.sub(r"\d+\.*$", "", tok)) == want[k]:
                    if k:
                        joins.append(prev_hyph)
                    prev_hyph = False
                    k += 1
                else:
                    break
                j += 1
            if k == len(want):
                w = want[0]
                for x, jn in zip(want[1:], joins):
                    w += x if jn else " " + x
                return " ".join(w.split()), f.name
    return None, None


def head_ok(url):
    """A listed file that the server does not have (second attempt: Aurore's
    MIDI, 404) is unreadable; checked before the retrying download."""
    import urllib.error
    import urllib.request
    try:
        urllib.request.urlopen(urllib.request.Request(url, headers=R.UA, method="HEAD"), timeout=60)
        return True
    except urllib.error.HTTPError as e:
        return e.code not in (404, 410)


def ly_paths(s):
    import io
    import zipfile
    if s["ly"]:
        return [fetch(s["ly"][0])]
    z = zipfile.ZipFile(io.BytesIO(fetch(s["ly_zip"][0]).read_bytes()))
    out = []
    for n in sorted(z.namelist()):
        if n.endswith(".ly"):
            f = CACHE / "mutopia" / "r3" / ("zip__" + n.replace("/", "__"))
            f.write_bytes(z.read(n))
            out.append(f)
    return out


def compile_ly(path, pid):
    """K6's second path: the LilyPond file compiled by LilyPond 2.24.3 after
    convert-ly, a \\midi block added to a \\score that has none."""
    d = CACHE / "ly" / f"r3-{pid}"
    d.mkdir(parents=True, exist_ok=True)
    src = d / "in.ly"
    src.write_bytes(path.read_bytes())
    cly = str(Path(R.LY).parent / "convert-ly")
    subprocess.run([cly, "-e", str(src)], capture_output=True, timeout=120)
    t = src.read_text(errors="replace")
    if "\\midi" not in t:
        t = re.sub(r"\\layout\s*\{", r"\\midi { } \\layout {", t)
        src.write_text(t)
    for old in d.glob("out*.mid*"):
        old.unlink()
    subprocess.run([R.LY, "-s", "-o", str(d / "out"), str(src)], capture_output=True, timeout=300, cwd=d)
    mids = sorted(d.glob("out*.mid*"))
    return mids[0] if mids else None


def wikidata_people(names):
    """Rule 4: Mutopia's death year cross-checked against Wikidata P570."""
    arts = {n: PEOPLE[n] for n in names}
    q = R.qids(list(arts.values()))
    wd = R.claims_years([x for x in q.values() if x], ["P570"])
    out = {}
    for n, a in arts.items():
        qq = q.get(a)
        out[n] = dict(article=a, qid=qq, wd_label=wd.get(qq, {}).get("label") if qq else None,
                      wd_died=wd.get(qq, {}).get("P570", []) if qq else [])
    return out


def agree(rec, ys):
    """Round 1's agreement rule (run.py verify)."""
    return None if (rec is None or not ys) else rec in ys


def k4_probe(names, mut, wd):
    """K4: each person's Mutopia year against the NEXT person's Wikidata
    entry (names sorted), a wrong entry known independently of the check.
    Where the two Mutopia years differ, it must disagree."""
    out = []
    for a, b in zip(names, names[1:] + names[:1]):
        if mut[a] != mut[b] and wd[b]["wd_died"]:
            out.append(dict(person=a, against=b, agrees=agree(mut[a], wd[b]["wd_died"])))
    return out


def extract():
    committed_first()
    sv = {s["id"]: s for s in json.load(open(RES / "r3-survey.json"))}
    scr = json.load(open(RES / "r3-screen.json"))
    rows = {r["id"]: r for r in scr["rows"]}
    el = [rows[i] for i in scr["order"]]
    probe = rights_probe()
    names = sorted({p["name"] for r in el for p in r["composer"] + r["poet"] + r["arranger"] if not p["anonymous"]})
    assert set(names) <= set(PEOPLE), set(names) - set(PEOPLE)
    wd = wikidata_people(names)
    mut = {p["name"]: p["died"] for r in el for p in r["composer"] + r["poet"] + r["arranger"] if not p["anonymous"]}
    k4 = k4_probe(names, mut, wd)
    assert k4 and not any(x["agrees"] for x in k4), k4
    need = TARGET - len(verified_titles())
    taken, out = [], []
    while len(taken) < need:
        seq = order(el, taken, skip=[o["id"] for o in out if not o.get("taken")])
        if not seq:
            break
        pid = seq[0]
        r, s = rows[pid], sv[pid]
        rec = dict(id=pid, title=r["title"], genre=r["genre"], edition=r["edition"], edition_year=r["edition_year"],
                   mutopia=f"https://www.mutopiaproject.org/cgibin/piece-info.cgi?id={pid}")
        out.append(rec)
        # rule 4: people, Wikidata cross-check, the later year used
        ppl = []
        for role in ("composer", "poet", "arranger"):
            for p in r[role]:
                if p["anonymous"]:
                    continue
                w = wd[p["name"]]
                eff = max([p["died"]] + w["wd_died"])
                ppl.append(dict(role=role, name=p["name"], mutopia_died=p["died"], died_eff=eff,
                                agree=agree(p["died"], w["wd_died"]), **w))
        rec["people"] = ppl
        # rule 4c: the LilyPond header's translator and arranger
        lys = ly_paths(s)
        hdr = ly_header(lys)
        rec["ly_header"] = {k: hdr[k] for k in ("title", "composer", "poet", "translator", "arranger", "source",
                                                 "date", "copyright", "mutopiacomposer", "mutopiapoet") if k in hdr}
        for k, v in header_people(lys, hdr):
            if k == "arranger" and any(p["role"] == "arranger" for p in ppl):
                continue
            ds = DATES.search(v)
            if not ds:
                rec["excluded"] = f"4c header {k} '{v}' with no death year"
                break
            ppl.append(dict(role=k, name=v, mutopia_died=int(ds[2] or ds[3]), died_eff=int(ds[2] or ds[3]),
                            agree=None))
        if rec.get("excluded"):
            print(pid, rec["excluded"])
            continue
        parts = [[dict(name=p["name"], died_eff=p["died_eff"]) for p in ppl if p["role"] == role]
                 for role in ("composer", "poet")] + \
                [[dict(name=p["name"], died_eff=p["died_eff"]) for p in ppl if p["role"] not in ("composer", "poet")]]
        parts = [x for i, x in enumerate(parts) if i < 2 or x]
        rec["rights"] = rights(parts, r["edition_year"])
        if not (rec["rights"]["us"] and rec["rights"]["life100"]):
            rec["excluded"] = f"2e after Wikidata {rec['rights']}"
            print(pid, rec["excluded"])
            continue
        # rule 5a: Mutopia's MIDI; else the compiled LilyPond file
        if not s["mid"] or not head_ok(s["mid"][0]):
            rec["excluded"] = "5a the listed MIDI file is not on the server"
            print(pid, rec["excluded"])
            continue
        mpath = fetch(s["mid"][0])
        tracks, tpq, meta = read_midi(mpath)
        rec["midi_source"] = "mutopia"
        if not any(t["lyrics"] for t in tracks):
            cm = compile_ly(lys[0], pid) if len(lys) == 1 else None
            if cm is None:
                rec["excluded"] = "5a no lyric events in Mutopia's MIDI, and the LilyPond file did not compile"
                print(pid, rec["excluded"])
                continue
            tracks, tpq, meta = read_midi(cm)
            rec["midi_source"] = "compiled"
        ph, why = phrase_from(tracks, tpq, meta)
        if ph is None:
            rec["excluded"] = why
            print(pid, why)
            continue
        rec["phrase"] = ph
        w, wf = ly_words(lys, ph["syllables"])
        ph["words_midi"] = ph["words"]
        if w:
            ph["words"], ph["words_from"] = w, wf
        else:
            ph["words_from"] = "midi"
        rec["conditions"] = c = conditions(ph)
        rec["k1"] = k1 = k1_round_trip(ph)
        rec["k2"] = k2 = k2_words(ph)
        rec["language"], rec["language_scores"] = language(ph["words"])
        # K6: the second path, where Mutopia's MIDI was used and the .ly is one file
        k6 = dict(available=False)
        if rec["midi_source"] == "mutopia" and len(lys) == 1:
            cm = compile_ly(lys[0], pid)
            if cm is not None:
                t2, q2, m2 = read_midi(cm)
                ph2, why2 = phrase_from(t2, q2, m2)
                k6 = dict(available=True, excluded_on_second_path=why2)
                if ph2:
                    k6.update(same_pitches=ph2["midi"] == ph["midi"], same_beats=ph2["beats"] == ph["beats"],
                              same_words=ph2["words"] == ph["words"])
        rec["k6"] = k6
        assert k1["must_fail_pitch"] and k1["must_fail_rhythm"], (pid, k1)
        assert k2["must_fail"], (pid, k2)
        if c["fails"]:
            rec["excluded"] = "5e " + "; ".join(c["fails"])
        elif not k1["must_pass"]:
            rec["excluded"] = "K1 round trip failed"
        elif not k2["must_pass"]:
            rec["excluded"] = "K2 alignment"
        else:
            rec["taken"] = True
            taken.append(pid)
        print(pid, r["title"][:30], "|", rec.get("excluded") or "TAKEN", "|", ph["words"][:60], "|", c,
              "| k6", k6)
    res = dict(rights_probe=probe, need=need, taken=taken, tried=[o["id"] for o in out],
               k4_must_fail_cases=len(k4), k4_must_fail_all_fail=not any(x["agrees"] for x in k4),
               k4_probe=k4, pieces=out)
    json.dump(res, open(RES / "r3-extract.json", "w"), indent=1, ensure_ascii=False)
    print("taken", len(taken), "of", need, "tried", len(out))


# ---------------------------------------------------------------- measure (rule 7)

def measure():
    committed_first()
    from multiprocessing import Pool
    ex = json.load(open(RES / "r3-extract.json"))
    e5run = R._load()[0]
    items = [(f"m{p['id']}", p["phrase"]["melody"], p["phrase"]["tempo_qpm"]) for p in ex["pieces"] if p.get("taken")]
    if len(sys.argv) > 2:  # timing sample (S19): the first n items
        items = items[:int(sys.argv[2])]
    jobs, seed = [], 2026100157
    for pid, mel, tempo in items:
        for v in e5run.VOICES:
            for sigma in (0, 20):
                for vib in (0, 1):
                    seed += 1
                    jobs.append((pid, mel, tempo, v, sigma, vib, seed))
    with Pool(18) as p:
        res = p.map(R._one, jobs, chunksize=2)
    name = "r3-measure.json" if len(sys.argv) <= 2 else "r3-measure-sample.json"
    json.dump(res, open(RES / name, "w"), indent=0)
    print(len(res), "renderings")


# ---------------------------------------------------------------- report (rule 8)

def report():
    import numpy as np
    ex = json.load(open(RES / "r3-extract.json"))
    s2 = json.load(open(RES / "r2-summary.json"))
    taken = [p for p in ex["pieces"] if p.get("taken")]
    g = Counter(s2["verified_genres"])
    for p in taken:
        g[p["genre"]] += 1
    lib = []
    for p in taken:
        ph = p["phrase"]
        lib.append(dict(id=f"mutopia-{p['id']}", title=p["title"], genre=p["genre"], language=p["language"],
                        words=ph["words"], key=ph["key"], meter=ph["meter"], tempo_qpm=ph["tempo_qpm"],
                        notes=[dict(pitch=a, beats=b) for a, b in zip(ph["pitches"], ph["beats"])],
                        provenance=dict(edition=p["edition"], edition_year=p["edition_year"],
                                        contributors=[{k: x.get(k) for k in ("role", "name", "died_eff", "article")}
                                                      for x in p["people"]],
                                        transcription=p["mutopia"], licence_of_transcription="Public Domain"),
                        melody_from="the edition (round 3, route (a))", licence="CC-PDM-1.0"))
    json.dump(lib, open(RES / "r3-library.json", "w"), indent=1, ensure_ascii=False)
    meas = None
    if (RES / "r3-measure.json").exists():
        m = json.load(open(RES / "r3-measure.json"))
        meas = {}
        for sigma in (0, 20):
            for vib in (0, 1):
                rows = [x for x in m if x["sigma"] == sigma and x["vib"] == vib]
                k = sum(x["est"]["found"] for x in rows)
                n = sum(x["n_notes"] for x in rows)
                # phrase bootstrap, as round 1 (report.py)
                ids = sorted({x["id"] for x in rows})
                rng = np.random.default_rng(57)
                per = {i: (sum(x["est"]["found"] for x in rows if x["id"] == i),
                           sum(x["n_notes"] for x in rows if x["id"] == i)) for i in ids}
                bs = []
                for _ in range(2000):
                    pick = rng.choice(ids, len(ids))
                    bs.append(sum(per[i][0] for i in pick) / sum(per[i][1] for i in pick))
                meas[f"sigma{sigma}_vib{vib}"] = dict(found=k, notes=n, share=k / n,
                                                      bootstrap95=[float(np.percentile(bs, 2.5)),
                                                                   float(np.percentile(bs, 97.5))])
        meas["per_phrase_vib1_sigma0"] = {i: sum(x["est"]["found"] for x in m if x["id"] == i and x["vib"] == 1 and x["sigma"] == 0) /
                                          sum(x["n_notes"] for x in m if x["id"] == i and x["vib"] == 1 and x["sigma"] == 0)
                                          for i in sorted({x["id"] for x in m})}
    out = dict(tried=len(ex["pieces"]), taken=len(taken), need=ex["need"],
               excluded={p["id"]: p["excluded"] for p in ex["pieces"] if p.get("excluded")},
               k1=dict(run=sum(1 for p in ex["pieces"] if "k1" in p),
                       must_pass=sum(1 for p in ex["pieces"] if p.get("k1", {}).get("must_pass")),
                       must_fail_pitch=sum(1 for p in ex["pieces"] if p.get("k1", {}).get("must_fail_pitch")),
                       must_fail_rhythm=sum(1 for p in ex["pieces"] if p.get("k1", {}).get("must_fail_rhythm"))),
               k2=dict(run=sum(1 for p in ex["pieces"] if "k2" in p),
                       must_pass=sum(1 for p in ex["pieces"] if p.get("k2", {}).get("must_pass")),
                       must_fail=sum(1 for p in ex["pieces"] if p.get("k2", {}).get("must_fail"))),
               k4=dict(people=sum(len(p.get("people", [])) for p in ex["pieces"]),
                       agree=sum(1 for p in ex["pieces"] for x in p.get("people", []) if x.get("agree") is True),
                       disagree=[(p["id"], x["name"], x["mutopia_died"], x.get("wd_died")) for p in ex["pieces"]
                                 for x in p.get("people", []) if x.get("agree") is False],
                       unchecked=[(p["id"], x["name"]) for p in ex["pieces"] for x in p.get("people", [])
                                  if x.get("agree") is None],
                       must_fail_cases=ex["k4_must_fail_cases"], must_fail_all_fail=ex["k4_must_fail_all_fail"]),
               k6={p["id"]: p.get("k6") for p in ex["pieces"] if "k6" in p},
               phrases={p["id"]: dict(title=p["title"], genre=p["genre"], language=p["language"],
                                      words=p["phrase"]["words"], **{k: p["conditions"][k] for k in
                                                                     ("notes", "range", "seconds", "shortest_s")},
                                      midi_source=p["midi_source"]) for p in taken},
               library=20 + len(taken), library_genres=dict(g), library_genre_count=len(g), target=TARGET,
               measure=meas)
    json.dump(out, open(RES / "r3-summary.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in out.items() if k != "phrases"}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    {"survey": survey, "screen": screen, "extract": extract, "measure": measure, "report": report}[sys.argv[1]]()
