"""E-004 round 5 (squillo iteration 81, F-060): an anthem whose notes are
taken from the edition it cites, and public-domain folk phrases, by round 3's
route (a): notes and words taken from a named public-domain edition, as
Mutopia's Public Domain transcription gives them.

Rules: README, *Round 5*. They are committed before the survey runs; the
names the agent gives from the survey's metadata (ANTHEM_OF, PEOPLE5) are
committed before the step that reads them, as round 3 did.

    uv run python round5.py survey    # Mutopia searches and the Folk listing -> results/r5-survey.json
    uv run python round5.py screen    # -> results/r5-screen.json
    uv run python round5.py extract   # -> results/r5-extract.json
    uv run python round5.py measure   # -> results/r5-measure.json
    uv run python round5.py report    # -> results/r5-summary.json, results/r5-library.json
"""

import json
import re
import subprocess
import sys
import urllib.parse
from collections import Counter
from pathlib import Path

import round2 as R2
import round3 as R3
import run as R

HERE = Path(__file__).parent
RES = R.RES
MUT = R2.MUT

# ---------------------------------------------------------------- rules (README, Round 5)

# Rule 1a: Mutopia's search, every instrument and style, for each of these
# terms, every page followed. The terms name national anthems whose words and
# tune could be out of copyright, in the forms their titles take, and the
# word itself. Fixed before the survey; nothing is added after it.
QUERIES = ["anthem", "national", "hymne", "himno", "inno",
           "god save", "marseillaise", "star spangled", "star-spangled", "anacreon",
           "gott erhalte", "kaiserhymne", "deutschland", "heil dir", "wilhelmus",
           "maamme", "vart land", "du gamla", "ja vi elsker", "kong christian",
           "brabanconne", "hail columbia", "my country", "hatikva", "kimigayo",
           "o canada", "hen wlad", "land of my fathers", "liberty", "mazurek",
           "jeszcze polska"]
SEARCH_URL = MUT + ("make-table.cgi?startat={}&searchingfor={}&Composer=&Instrument=&Style=&collection=&id="
                    "&solo=&recent=&timelength=&timeunit=&lilyversion=&preview=")
# Rule 1b: Mutopia's listing for style Folk, every instrument.
FOLK_URL = MUT + ("make-table.cgi?startat={}&searchingfor=&Composer=&Instrument=&Style=Folk&collection=&id="
                  "&solo=&recent=&timelength=&timeunit=&lilyversion=&preview=")
PAGE = R3.PAGE  # 10 pieces a page (round3.py line 40)

# Rule 2 (the names, filled from r5-survey.json's metadata alone and committed
# before `screen` runs): Mutopia id -> the national anthem whose words and
# tune the piece sets, by its title and source. A piece that sets an anthem's
# tune to other words, or arranges it with no words, is not named.
# Named from r5-survey.json (17 pieces found by a query; the rest are the
# Folk listing's): only 1017 sets a national anthem's words and tune. 1098,
# "Polish National Air", is for guitar with no words; 949 is a church
# anthem; the rest are other works the words matched (Sousa's marches,
# Grieg, Bach, Bruckner, Lassus, Burgmüller, Kühnel, Dandrieu, Küffner) or
# Norwegian dances for violin.
ANTHEM_OF = {1017: "Hen Wlad Fy Nhadau"}

# Rule 3c: the 39 items the library ships (results/items, fold 2's 30, and
# results/r4/items, round 4's 9; squillo fixtures/slice/phrases/), by
# normalised title; a piece whose title holds one, or is held in one, is not taken.
ITEMS = [HERE / "results" / "items", HERE / "results" / "r4" / "items"]

# Rule 5 (filled from r5-screen.json's eligible pieces alone and committed
# before `extract` reads Wikidata or any file): Mutopia's name -> English
# Wikipedia article.
# Named from r5-screen.json: its 29 eligible pieces name no person (every
# composer and lyricist cell anonymous, no arranger cell filled).
PEOPLE5 = {}


def committed_first():
    """S15: refuse to run on an uncommitted edit of this file or of the
    round 3 module whose rules it reuses, or before they are committed."""
    for me in (Path(__file__).name, "round3.py", "round2.py", "run.py"):
        a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
        b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", me], cwd=HERE)
        if a.returncode or b.returncode:
            sys.exit(f"{me} is not committed as it stands: commit the rules before running")


def norm(t):
    return re.sub(r"[^a-z]", "", t.lower())


# ---------------------------------------------------------------- survey (rule 1)

def listing(url_of, cache_of):
    """Every page of one Mutopia table, parsed as round 3's survey parses it
    (round3.py lines 113-138), following `startat` until the page has no next."""
    out, start = [], 0
    while True:
        page = R2.get_text(url_of(start), cache_of(start))
        if "Sorry, no matches were found" in page:
            break
        for t in re.findall(r'<table class="table-bordered result-table">(.*?)</table>', page, re.S):
            rows = R3.cells_of(t)
            pid = re.search(r"piece-info\.cgi\?id=(\d+)", t)
            r0 = rows[0] + [""] * 4
            r1 = (rows[1] if len(rows) > 1 else []) + [""] * 4
            r2 = (rows[2] if len(rows) > 2 else []) + [""] * 4
            na = lambda c: "" if c.strip().lower() in ("n/a", "none") else c  # noqa: E731
            out.append(dict(id=int(pid[1]) if pid else None, title=r0[0], composer=r0[1], opus=r0[2],
                            poet=na(r0[3]), instrument=r1[0], date=r1[1], style=r1[2], arranger=na(r1[3]),
                            source=r2[0], licence=r2[1],
                            ly=re.findall(r'href="(https://www\.mutopiaproject\.org/ftp/[^"]+\.ly)"', t),
                            ly_zip=re.findall(r'href="(https://www\.mutopiaproject\.org/ftp/[^"]+-lys\.zip)"', t),
                            mid=re.findall(r'href="(https://www\.mutopiaproject\.org/ftp/[^"]+\.midi?)"', t),
                            mid_zip=re.findall(r'href="(https://www\.mutopiaproject\.org/ftp/[^"]+-mids\.zip)"', t)))
        if f"startat={start + PAGE}&" not in page.replace("&amp;", "&"):
            break
        start += PAGE
    return out


def survey():
    committed_first()
    by = {}
    for q in QUERIES:
        qq = urllib.parse.quote(q)
        got = listing(lambda s: SEARCH_URL.format(s, qq), lambda s: f"mutopia/r5-search-{R.safe(q)}-{s}.html")
        for p in got:
            by.setdefault(p["id"], dict(p, found_by=[]))["found_by"].append(q)
        print(f"{q!r}: {len(got)}")
    folk = listing(lambda s: FOLK_URL.format(s), lambda s: f"mutopia/r5-list-folk-{s}.html")
    for p in folk:
        by.setdefault(p["id"], dict(p, found_by=[]))["found_by"].append("Style=Folk")
    print("folk listing:", len(folk))
    out = sorted(by.values(), key=lambda p: p["id"])
    json.dump(out, open(RES / "r5-survey.json", "w"), indent=1, ensure_ascii=False)
    print(len(out), "pieces")


# ---------------------------------------------------------------- screen (rules 2, 3)

def library_titles():
    return {norm(json.load(open(f))["title"]) for d in ITEMS for f in sorted(d.glob("*.json"))}


def words_rule(s):
    """Rule 3a's one change to round 3's rule 2b: words named, or, where every
    composer segment is anonymous (Traditional), the words taken as
    traditional too, an anonymous part published by the edition."""
    poets = R3.people_in(s["poet"])
    comps = R3.people_in(s["composer"])
    if poets:
        return True, poets
    if comps and all(p["anonymous"] for p in comps):
        return True, [dict(name="Traditional", died=None, anonymous=True)]
    return False, []


def words_probe():
    """Rule 3a's check (S15, C10): a traditional piece with an empty lyricist
    cell must pass; a named composer with an empty lyricist cell must fail;
    the two differ in the composer cell, which the rule reads."""
    base = dict(poet="", composer="Traditional")
    named = dict(poet="", composer="by F. Abt (1819–1885)")
    assert base != named
    res = dict(must_pass_traditional=words_rule(base)[0], must_fail_named_composer=not words_rule(named)[0])
    assert all(res.values()), res
    return res


def screen_one(s, titles):
    """Round 3's rule 2 (round3.py `screen_one`, lines 187-217), with rule 3a
    for words and rule 3c's titles; the anthem or folk label from rule 2."""
    ok, poets = words_rule(s)
    s2 = dict(s, poet=s["poet"] or ("Traditional" if ok else ""))
    r = R3.screen_one(s2, [])
    why = [w for w in r["why"] if not w.startswith("2g")]
    if not ok:
        why = [w for w in why if not w.startswith("2b")] + ["2b no words named, composer named"]
    t = norm(s["title"])
    dup = [v for v in titles if v and (v in t or t in v)]
    if dup:
        why.append("3c the library ships it: " + ", ".join(sorted(dup)))
    kind = "anthem" if s["id"] in ANTHEM_OF else ("folk" if "Style=Folk" in s["found_by"] else None)
    if kind is None:
        why.append("2 neither a named anthem nor Mutopia style Folk")
    return dict(r, genre=kind or r["genre"], anthem=ANTHEM_OF.get(s["id"]), why=why, eligible=not why)


def order(rows):
    """Rule 4: anthems first, the first eligible piece per anthem by lower
    Mutopia id taken first and the rest after it; then folk by lower id."""
    an = sorted([r for r in rows if r["genre"] == "anthem"], key=lambda r: r["id"])
    fo = sorted([r for r in rows if r["genre"] == "folk"], key=lambda r: r["id"])
    return [r["id"] for r in an + fo]


def screen():
    committed_first()
    assert ANTHEM_OF is not None, "name ANTHEM_OF from r5-survey.json and commit it first"
    probe = R3.rights_probe()
    wp = words_probe()
    titles = library_titles()
    assert len(titles) == 39, len(titles)
    sv = json.load(open(RES / "r5-survey.json"))
    assert set(ANTHEM_OF) <= {s["id"] for s in sv}
    rows = [screen_one(s, titles) for s in sv]
    el = [r for r in rows if r["eligible"]]
    out = dict(rights_probe=probe, words_probe=wp, listed=len(rows),
               anthem_named=len(ANTHEM_OF), folk_listed=sum(1 for s in sv if "Style=Folk" in s["found_by"]),
               eligible=len(el), order=order(el),
               reasons=dict(Counter(w.split(" ")[0] for r in rows if r["genre"] in ("anthem", "folk")
                                    for w in r["why"])),
               eligible_by_genre=dict(Counter(r["genre"] for r in el)), rows=rows)
    json.dump(out, open(RES / "r5-screen.json", "w"), indent=1, ensure_ascii=False)
    print({k: v for k, v in out.items() if k != "rows"})
    for r in rows:
        if r["genre"] in ("anthem", "folk"):
            print(f"  {r['id']:5d} {r['genre']:7s} {'OK ' if r['eligible'] else '-- '}{r['title'][:34]:34s} "
                  f"{r['edition'][:40]:40s} {'; '.join(r['why'])[:90]}")


# ---------------------------------------------------------------- extract (rules 5, 6)

def k5_memory(ph, anthem):
    """K5, reported, decides nothing: the phrase against round 1's
    from-memory melody of the same anthem (library.py), by round 1's compare."""
    import library as L
    mem = {"God Save the King": "god-save-the-king", "The Star-Spangled Banner": "star-spangled-banner",
           "La Marseillaise": "la-marseillaise"}.get(anthem)
    if mem is None:
        return None
    cand = next(c for c in L.CANDIDATES if c["id"] == mem)
    line = [dict(onsets=[a for a, _, _ in ph["ticks"]], pitches=ph["midi"], tpq=ph["tpq"])]
    return dict(round1_id=mem, compare=R.compare(R.parse(cand["melody"]), line))


def extract():
    committed_first()
    assert PEOPLE5 is not None, "name PEOPLE5 from r5-screen.json and commit it first"
    sv = {s["id"]: s for s in json.load(open(RES / "r5-survey.json"))}
    scr = json.load(open(RES / "r5-screen.json"))
    rows = {r["id"]: r for r in scr["rows"]}
    el = [rows[i] for i in scr["order"]]
    probe = R3.rights_probe()
    names = sorted({p["name"] for r in el for p in r["composer"] + r["poet"] + r["arranger"] if not p["anonymous"]})
    assert set(names) <= set(PEOPLE5), set(names) - set(PEOPLE5)
    R3.PEOPLE.update(PEOPLE5)
    wd = R3.wikidata_people(names)
    mut = {p["name"]: p["died"] for r in el for p in r["composer"] + r["poet"] + r["arranger"] if not p["anonymous"]}
    k4 = R3.k4_probe(names, mut, wd) if len(names) > 1 else []
    assert not any(x["agrees"] for x in k4), k4
    out, anthems_taken = [], {}
    for r in el:
        pid, s = r["id"], sv[r["id"]]
        rec = dict(id=pid, title=r["title"], genre=r["genre"], anthem=r.get("anthem"), edition=r["edition"],
                   edition_year=r["edition_year"],
                   mutopia=f"https://www.mutopiaproject.org/cgibin/piece-info.cgi?id={pid}")
        out.append(rec)
        if r["genre"] == "anthem" and r["anthem"] in anthems_taken:
            rec["excluded"] = f"4 {r['anthem']} already taken from {anthems_taken[r['anthem']]}"
            continue
        ppl = []
        for role in ("composer", "poet", "arranger"):
            for p in r[role]:
                if p["anonymous"]:
                    continue
                w = wd[p["name"]]
                eff = max([p["died"]] + w["wd_died"])
                ppl.append(dict(role=role, name=p["name"], mutopia_died=p["died"], died_eff=eff,
                                agree=R3.agree(p["died"], w["wd_died"]), **w))
        rec["people"] = ppl
        lys = R3.ly_paths(s)
        hdr = R3.ly_header(lys)
        rec["ly_header"] = {k: hdr[k] for k in ("title", "composer", "poet", "translator", "arranger", "source",
                                                 "date", "copyright", "mutopiacomposer", "mutopiapoet") if k in hdr}
        extra = list(R3.header_people(lys, hdr))
        # rule 5c: where rule 3a took the words as traditional, a poet the
        # header names is a contributor too
        if not R3.people_in(s["poet"]) and hdr.get("poet") and R3.names_person(hdr["poet"]) \
                and not R3.ANON.match(hdr["poet"].strip()):
            extra.append(("poet", hdr["poet"]))
        for k, v in extra:
            if k == "arranger" and any(p["role"] == "arranger" for p in ppl):
                continue
            ds = R3.DATES.search(v)
            if not ds:
                rec["excluded"] = f"5c header {k} '{v}' with no death year"
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
        rec["rights"] = R3.rights(parts, r["edition_year"])
        if not (rec["rights"]["us"] and rec["rights"]["life100"]):
            rec["excluded"] = f"2e after Wikidata {rec['rights']}"
            print(pid, rec["excluded"])
            continue
        if not s["mid"] or not R3.head_ok(s["mid"][0]):
            rec["excluded"] = "6a the listed MIDI file is not on the server"
            print(pid, rec["excluded"])
            continue
        tracks, tpq, meta = R3.read_midi(R3.fetch(s["mid"][0]))
        rec["midi_source"] = "mutopia"
        if not any(t["lyrics"] for t in tracks):
            cm = R3.compile_ly(lys[0], pid) if len(lys) == 1 else None
            if cm is None:
                rec["excluded"] = ("6a no lyric events in Mutopia's MIDI, and the source is not one file"
                                   if len(lys) != 1 else
                                   "6a no lyric events in Mutopia's MIDI, and its compiled source gave no MIDI")
                print(pid, rec["excluded"])
                continue
            tracks, tpq, meta = R3.read_midi(cm)
            rec["midi_source"] = "compiled"
        ph, why = R3.phrase_from(tracks, tpq, meta)
        if ph is None:
            rec["excluded"] = why
            print(pid, why)
            continue
        rec["phrase"] = ph
        w, wf = R3.ly_words(lys, ph["syllables"])
        ph["words_midi"] = ph["words"]
        if w:
            ph["words"], ph["words_from"] = w, wf
        else:
            ph["words_from"] = "midi"
        rec["conditions"] = c = R3.conditions(ph)
        rec["k1"] = k1 = R3.k1_round_trip(ph)
        rec["k2"] = k2 = R3.k2_words(ph)
        rec["language"], rec["language_scores"] = R3.language(ph["words"])
        k6 = dict(available=False)
        if rec["midi_source"] == "mutopia" and len(lys) == 1:
            cm = R3.compile_ly(lys[0], pid)
            if cm is not None:
                t2, q2, m2 = R3.read_midi(cm)
                ph2, why2 = R3.phrase_from(t2, q2, m2)
                k6 = dict(available=True, excluded_on_second_path=why2)
                if ph2:
                    k6.update(same_pitches=ph2["midi"] == ph["midi"], same_beats=ph2["beats"] == ph["beats"],
                              same_syllables=ph2["syllables"] == ph["syllables"])
        rec["k6"] = k6
        rec["k5"] = k5_memory(ph, r.get("anthem")) if r["genre"] == "anthem" else None
        assert k1["must_fail_pitch"] and k1["must_fail_rhythm"], (pid, k1)
        assert k2["must_fail"], (pid, k2)
        if c["fails"]:
            rec["excluded"] = "6e " + "; ".join(c["fails"])
        elif not k1["must_pass"]:
            rec["excluded"] = "K1 round trip failed"
        elif not k2["must_pass"]:
            rec["excluded"] = "K2 alignment"
        else:
            rec["taken"] = True
            if r["genre"] == "anthem":
                anthems_taken[r["anthem"]] = pid
        print(pid, r["title"][:30], "|", rec.get("excluded") or "TAKEN", "|", ph["words"][:60], "| k6", k6)
    res = dict(rights_probe=probe, taken=[o["id"] for o in out if o.get("taken")], tried=[o["id"] for o in out],
               k4_must_fail_cases=len(k4), k4_must_fail_all_fail=not any(x["agrees"] for x in k4),
               k4_probe=k4, pieces=out)
    json.dump(res, open(RES / "r5-extract.json", "w"), indent=1, ensure_ascii=False)
    print("taken", len(res["taken"]), "tried", len(out))


# ---------------------------------------------------------------- post hoc, counted apart

def posthoc_anthem():
    """Written after the screen, before it runs (README, *Round 5*, post
    hoc): Hen Wlad Fy Nhadau (1017), the one anthem named, fails rule 3 for
    no year in its source cell (the National Library of Wales, a
    manuscript). Rule 6's extraction and K1, K2, K6 run on it with no
    rights verdict, so the fold can judge it with its phrase in hand.
    Counted apart; it is never taken by this round."""
    committed_first()
    s = {p["id"]: p for p in json.load(open(RES / "r5-survey.json"))}[1017]
    lys = R3.ly_paths(s)
    hdr = R3.ly_header(lys)
    rec = dict(id=1017, title=s["title"], counted="apart, post hoc; no rights verdict", source_cell=s["source"],
               ly_header={k: hdr[k] for k in ("title", "composer", "poet", "translator", "arranger", "source",
                                              "date", "copyright", "mutopiacomposer", "mutopiapoet") if k in hdr},
               header_people=list(R3.header_people(lys, hdr)))
    tracks, tpq, meta = R3.read_midi(R3.fetch(s["mid"][0]))
    rec["midi_source"] = "mutopia"
    if not any(t["lyrics"] for t in tracks):
        cm = R3.compile_ly(lys[0], 1017) if len(lys) == 1 else None
        rec["midi_source"] = "compiled" if cm else None
        if cm:
            tracks, tpq, meta = R3.read_midi(cm)
    ph, why = R3.phrase_from(tracks, tpq, meta) if rec["midi_source"] else (None, "6a no lyric events")
    rec["excluded_by_rule_6"] = why
    if ph:
        w, wf = R3.ly_words(lys, ph["syllables"])
        ph["words_midi"] = ph["words"]
        if w:
            ph["words"], ph["words_from"] = w, wf
        rec["phrase"] = ph
        rec["conditions"] = R3.conditions(ph)
        rec["k1"] = k1 = R3.k1_round_trip(ph)
        rec["k2"] = k2 = R3.k2_words(ph)
        assert k1["must_fail_pitch"] and k1["must_fail_rhythm"], k1
        assert k2["must_fail"], k2
        rec["passes_rule_6_and_checks"] = not rec["conditions"]["fails"] and k1["must_pass"] and k2["must_pass"]
    json.dump(rec, open(RES / "r5-posthoc-anthem.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in rec.items() if k != "phrase"}, ensure_ascii=False)[:1500])
    if ph:
        print(ph["words"], ph["melody"], ph["key"], ph["meter"], ph["tempo_qpm"])


# ---------------------------------------------------------------- measure, report (rules 7, 8)

def measure():
    committed_first()
    from multiprocessing import Pool
    ex = json.load(open(RES / "r5-extract.json"))
    e5run = R._load()[0]
    items = [(f"m{p['id']}", p["phrase"]["melody"], p["phrase"]["tempo_qpm"]) for p in ex["pieces"] if p.get("taken")]
    jobs, seed = [], 2026100281
    for pid, mel, tempo in items:
        for v in e5run.VOICES:
            for sigma in (0, 20):
                for vib in (0, 1):
                    seed += 1
                    jobs.append((pid, mel, tempo, v, sigma, vib, seed))
    with Pool(18) as p:
        res = p.map(R._one, jobs, chunksize=2)
    json.dump(res, open(RES / "r5-measure.json", "w"), indent=0)
    print(len(res), "renderings")


def report():
    ex = json.load(open(RES / "r5-extract.json"))
    scr = json.load(open(RES / "r5-screen.json"))
    taken = [p for p in ex["pieces"] if p.get("taken")]
    lib = []
    for p in taken:
        ph = p["phrase"]
        lib.append(dict(id=f"mutopia-{p['id']}", title=p["title"], genre=p["genre"], anthem=p.get("anthem"),
                        language=p["language"], words=ph["words"], key=ph["key"], meter=ph["meter"],
                        tempo_qpm=ph["tempo_qpm"],
                        notes=[dict(pitch=a, beats=b) for a, b in zip(ph["pitches"], ph["beats"])],
                        provenance=dict(edition=p["edition"], edition_year=p["edition_year"],
                                        contributors=[{k: x.get(k) for k in ("role", "name", "died_eff", "article")}
                                                      for x in p["people"]],
                                        transcription=p["mutopia"], licence_of_transcription="Public Domain"),
                        melody_from="the edition (round 5, route (a))", licence="CC-PDM-1.0"))
    json.dump(lib, open(RES / "r5-library.json", "w"), indent=1, ensure_ascii=False)
    meas = None
    if (RES / "r5-measure.json").exists():
        m = json.load(open(RES / "r5-measure.json"))
        meas = {}
        for sigma in (0, 20):
            for vib in (0, 1):
                rows = [x for x in m if x["sigma"] == sigma and x["vib"] == vib]
                meas[f"sigma{sigma}_vib{vib}"] = dict(found=sum(x["est"]["found"] for x in rows),
                                                      notes=sum(x["n_notes"] for x in rows))
        meas["per_phrase"] = {i: dict(found=sum(x["est"]["found"] for x in m if x["id"] == i),
                                      notes=sum(x["n_notes"] for x in m if x["id"] == i))
                              for i in sorted({x["id"] for x in m})}
    out = dict(listed=scr["listed"], anthem_named=scr["anthem_named"], folk_listed=scr["folk_listed"],
               eligible=scr["eligible"], eligible_by_genre=scr["eligible_by_genre"], reasons=scr["reasons"],
               tried=len(ex["pieces"]), taken=len(taken), taken_by_genre=dict(Counter(p["genre"] for p in taken)),
               excluded={p["id"]: p["excluded"] for p in ex["pieces"] if p.get("excluded")},
               k1=dict(run=sum(1 for p in ex["pieces"] if "k1" in p),
                       must_pass=sum(1 for p in ex["pieces"] if p.get("k1", {}).get("must_pass"))),
               k4=dict(people=sum(len(p.get("people", [])) for p in ex["pieces"]),
                       agree=sum(1 for p in ex["pieces"] for x in p.get("people", []) if x.get("agree") is True),
                       disagree=[(p["id"], x["name"], x["mutopia_died"], x.get("wd_died")) for p in ex["pieces"]
                                 for x in p.get("people", []) if x.get("agree") is False],
                       must_fail_cases=ex["k4_must_fail_cases"]),
               k5={p["id"]: p.get("k5") for p in taken if p.get("k5")},
               k6={p["id"]: p.get("k6") for p in taken},
               measure=meas, library_after=39 + len(taken))
    json.dump(out, open(RES / "r5-summary.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in out.items() if k not in ("k6",)}, ensure_ascii=False, indent=1)[:4000])


if __name__ == "__main__":
    {"survey": survey, "screen": screen, "extract": extract, "measure": measure, "report": report,
     "posthoc_anthem": posthoc_anthem}[sys.argv[1]]()
