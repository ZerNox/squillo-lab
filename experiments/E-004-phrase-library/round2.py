"""E-004 round 2 (squillo iteration 41): the 18 pending melodies against a
second, independent transcription named in advance (squillo F-026, S16).

    uv run python round2.py survey   # which sources exist, metadata only -> results/r2-survey.json
    uv run python round2.py check    # each phrase against the reference named in REFS -> results/r2-check.json, r2-rule2.json
    uv run python round2.py report   # -> results/r2-summary.json

Crude experiment code. `survey` never compiles or compares a note: it lists,
for each pending phrase, the Mutopia Project pieces its fixed queries find
(title, instrument, source, licence) and, for a fixed list of Wikipedia
language editions linked from the English article, each <score> block's
section heading, the text just before it and any LilyPond title. The
reference for each phrase is then named in `REFS` from that metadata alone,
by the rule in the README, and committed before `check` runs.

The melodies are round 1's (`library.py`), unchanged; nothing is corrected.
No note of any reference enters `library.py`.
"""

import html
import json
import re
import sys
import urllib.parse
from pathlib import Path

import numpy as np

import library as L
import run as R

HERE = Path(__file__).parent
CACHE = R.CACHE
RES = R.RES

PENDING = ["old-hundredth", "abide-with-me", "jesus-loves-me", "swing-low", "jingle-bells",
           "deck-the-halls", "in-the-bleak-midwinter", "auld-lang-syne", "my-bonnie", "danny-boy",
           "aura-lea", "yankee-doodle", "god-save-the-king", "star-spangled-banner",
           "la-marseillaise", "brahms-lullaby", "la-donna-e-mobile", "habanera"]

# fixed before the survey: Mutopia title queries per phrase, and the language
# editions searched, in the order the rule takes them
MUTOPIA_Q = {
    "old-hundredth": ["old 100", "hundredth"], "abide-with-me": ["eventide", "abide"],
    "jesus-loves-me": ["jesus loves"], "swing-low": ["swing low", "chariot"],
    "jingle-bells": ["jingle"], "deck-the-halls": ["deck the", "nos galan"],
    "in-the-bleak-midwinter": ["cranham", "bleak"], "auld-lang-syne": ["auld"],
    "my-bonnie": ["bonnie"], "danny-boy": ["londonderry", "danny"], "aura-lea": ["aura"],
    "yankee-doodle": ["yankee"], "god-save-the-king": ["god save", "king"],
    "star-spangled-banner": ["star spangled", "anacreon"], "la-marseillaise": ["marseillaise"],
    "brahms-lullaby": ["wiegenlied"], "la-donna-e-mobile": ["donna", "rigoletto"],
    "habanera": ["habanera", "carmen"],
}
LANGS = ["de", "fr", "es", "it", "nl", "sv", "pl", "pt", "ru", "uk", "cs", "fi", "da", "no", "ja", "zh"]
MUT = "https://www.mutopiaproject.org/cgibin/"

# Named from results/r2-survey.json's metadata alone, by the README's rule 2,
# and committed before `check` ran. ("mutopia", piece id, MIDI file[, member
# of a zip]) or ("wiki", lang, article, block index), with the reason.
REFS = {
    "old-hundredth": (("mutopia", 194, "Old100-orig.mid"),
                      "two Mutopia SATB settings; 194 transcribes the Genevan Psalter 1551, the cited edition "
                      "(90 is Dowland's 1612 harmonisation)"),
    "abide-with-me": (("mutopia", 1241, "eventide.mid"), "Mutopia EVENTIDE, Monk, SATB"),
    "in-the-bleak-midwinter": (("mutopia", 1233, "cranham.mid"), "Mutopia CRANHAM, Holst, SATB"),
    "auld-lang-syne": (("wiki", "de", "Auld Lang Syne", 0),
                       "Mutopia's only hit is Horetzky's guitar arrangement (excluded); de block 0 under "
                       "'Melodie', first verse and refrain after the National Library of Scotland"),
    "god-save-the-king": (("wiki", "it", "God Save the King", 0),
                          "no Mutopia setting of the tune (hits are other pieces; AUSTRIA is Haydn's); it "
                          "block 0, a) Thesaurus musicus 1744, the first block setting the tune"),
    "star-spangled-banner": (("wiki", "it", "The Star-Spangled Banner", 0),
                             "no Mutopia hit; it block 0, a) Blands c. 1790, the Anacreontic Song, the "
                             "first block setting the tune"),
    "la-marseillaise": (("wiki", "it", "La Marsigliese", 0),
                        "no Mutopia hit; it block 0, a) Dannbach 1792, the first block setting the tune"),
    "brahms-lullaby": (("mutopia", 1037, "Wiegenlied-mids.zip"),
                       "Mutopia 1037, Brahms Op. 49 No. 4, voice and piano (1040 is Schubert's, 887 Ries', "
                       "632 and 1710 other pieces)"),
    "la-donna-e-mobile": (("wiki", "de", "La donna è mobile", 0),
                          "no Mutopia setting (hits are other pieces); de block 0 under 'Musik'"),
}
# No reference, and why (the phrase stays pending):
NO_REF = {
    "jesus-loves-me": "no Mutopia hit, no score in the 16 editions",
    "swing-low": "no Mutopia hit, no score in the 16 editions",
    "jingle-bells": "no Mutopia hit, no score in the 16 editions",
    "deck-the-halls": "no Mutopia hit, no score in the 16 editions",
    "my-bonnie": "no Mutopia hit, no score in the 16 editions",
    "danny-boy": "no Mutopia hit, no score in the 16 editions",
    "aura-lea": "no Mutopia hit; fr block 0 is the English article's block, a copy (rule 2)",
    "yankee-doodle": "no Mutopia hit, no score in the 16 editions",
    "habanera": "Mutopia's only hit is the Carmen prelude for piano (excluded); no score in the 16 editions",
}


def get_text(url, cache_name):
    f = CACHE / cache_name
    if f.exists():
        return f.read_bytes().decode("utf-8", "replace")
    import time
    import urllib.request
    for i in range(6):
        try:
            t = urllib.request.urlopen(urllib.request.Request(url, headers=R.UA), timeout=60).read()
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(t)
            time.sleep(1.0)
            return t.decode("utf-8", "replace")
        except Exception as e:
            print("retry", url[:80], e, file=sys.stderr)
            time.sleep(10 * (i + 1))
    raise RuntimeError(url)


def get_bytes(url, cache_name):
    get_text(url, cache_name)
    return (CACHE / cache_name).read_bytes()


def lines_of(page):
    t = re.sub(r"<script.*?</script>", "", page, flags=re.S)
    t = html.unescape(re.sub(r"<[^>]+>", "\n", t))
    return [x.strip() for x in t.split("\n") if x.strip()]


def mutopia_piece(pid):
    page = get_text(MUT + f"piece-info.cgi?id={pid}", f"mutopia/piece-{pid}.html")
    ls = lines_of(page)
    info = dict(id=pid, heading=ls[0] if ls else None)
    for key in ("Instrument(s):", "Style:", "Source:", "Copyright:", "Date of composition:",
                "Music ID Number:", "Meter:"):
        if key in ls:
            info[key.rstrip(":").lower()] = ls[ls.index(key) + 1]
    info["files"] = sorted(set(re.findall(r'href="(https://www\.mutopiaproject\.org/ftp/[^"]+)"', page)))
    return info


def mutopia_search(q):
    page = get_text(MUT + "make-table.cgi?searchingfor=" + urllib.parse.quote(q),
                    f"mutopia/search-{R.safe(q)}.html")
    return sorted(set(int(x) for x in re.findall(r"piece-info\.cgi\?id=(\d+)", page)))


def langlinks(title):
    d = R.get_json(R.api("en", action="query", prop="langlinks", lllimit="max", titles=title,
                         redirects=1), f"wiki/langlinks-{R.safe(title)}.json")
    return {x["lang"]: x["title"] for x in d["query"]["pages"][0].get("langlinks", [])}


def block_context(w):
    """Metadata for each <score> block: heading, preceding text, LilyPond title."""
    out = []
    for m in re.finditer(r"<score([^>]*)>(.*?)</score>", w, re.S):
        before = w[:m.start()]
        heads = re.findall(r"^=+\s*(.*?)\s*=+\s*$", before, re.M)
        prev = re.sub(r"<[^>]+>|\[\[(?:[^|\]]*\|)?([^\]]*)\]\]|'{2,}|\{\{[^}]*\}\}", r"\1", before[-400:])
        title = re.search(r'\btitle\s*=\s*"([^"]*)"', m[2])
        piece = re.search(r'\bpiece\s*=\s*"([^"]*)"', m[2])
        cap = re.search(r"</score>\s*(?:<br\s*/?>)?\s*([^\n<]{0,160})", w[m.start():m.end() + 200])
        out.append(dict(attrs=m[1].strip(), heading=heads[-1] if heads else None,
                        before=" ".join(prev.split())[-200:], ly_title=title[1] if title else None,
                        ly_piece=piece[1] if piece else None,
                        after=" ".join(cap[1].split()) if cap else None,
                        abc="abc" in m[1].lower(), chars=len(m[2])))
    return out


def norm_src(s):
    return re.sub(r"\s+", "", s)


def survey():
    by_id = {c["id"]: c for c in L.CANDIDATES}
    out = {}
    for pid in PENDING:
        c = by_id[pid]
        rec = dict(id=pid, title=c["title"], en_article=R.ARTICLES[pid], mutopia=[], wiki=[])
        seen = set()
        for q in MUTOPIA_Q[pid]:
            for mid in mutopia_search(q):
                if mid not in seen:
                    seen.add(mid)
                    rec["mutopia"].append(dict(query=q, **mutopia_piece(mid)))
        real, revid, w_en = R.wikitext("en", R.ARTICLES[pid])
        en_srcs = {norm_src(s) for _, s in re.findall(r"<score([^>]*)>(.*?)</score>", w_en, re.S)}
        rec["en"] = dict(article=real, revid=revid, blocks=len(en_srcs))
        ll = langlinks(R.ARTICLES[pid])
        for lang in LANGS:
            if lang not in ll:
                continue
            real, revid, w = R.wikitext(lang, ll[lang])
            blocks = block_context(w)
            srcs = [s for _, s in re.findall(r"<score([^>]*)>(.*?)</score>", w, re.S)]
            for b, s in zip(blocks, srcs):
                b["same_as_en_block"] = norm_src(s) in en_srcs
            rec["wiki"].append(dict(lang=lang, article=real, revid=revid, blocks=blocks))
        out[pid] = rec
        print(f"{pid:24s} mutopia={len(rec['mutopia'])} "
              + " ".join(f"{x['lang']}:{len(x['blocks'])}" for x in rec["wiki"] if x["blocks"]))
    json.dump(out, open(RES / "r2-survey.json", "w"), indent=1, ensure_ascii=False)


# ---------------------------------------------------------------- check

def ref_tracks(ref, pid):
    """The named reference as MIDI tracks, plus a record of what was read."""
    import io
    import zipfile
    if ref[0] == "mutopia":
        _, mid, fname = ref
        info = mutopia_piece(mid)
        url = next(u for u in info["files"] if u.endswith("/" + fname))
        data = get_bytes(url, f"mutopia/{mid}-{fname}")
        paths = []
        if fname.endswith(".zip"):
            z = zipfile.ZipFile(io.BytesIO(data))
            for n in sorted(z.namelist()):
                if n.lower().endswith((".mid", ".midi")):
                    f = CACHE / "mutopia" / f"{mid}-{Path(n).name}"
                    f.write_bytes(z.read(n))
                    paths.append(f)
        else:
            paths = [CACHE / "mutopia" / f"{mid}-{fname}"]
        tracks = [t for f in paths for t in R.midi_tracks(f)]
        return tracks, dict(source="mutopia", piece=mid, url=url, members=[p.name for p in paths],
                            mutopia_id=info.get("music id number"), edition=info.get("source"),
                            licence=info.get("copyright"))
    _, lang, title, bi = ref
    real, revid, w = R.wikitext(lang, title)
    blocks = re.findall(r"<score([^>]*)>(.*?)</score>", w, re.S)
    attrs, src = blocks[bi]
    mid, how = R.to_midi(src, attrs, f"r2-{pid}-{lang}-b{bi}")
    tracks = R.midi_tracks(mid) if mid else []
    return tracks, dict(source="wiki", lang=lang, article=real, revid=revid, block=bi,
                        compile_attempt=how, compiled=mid is not None)


def self_check(tracks):
    """S15: the reference's own first eight notes must pass; one pitch moved
    a semitone must fail on pitch; one duration doubled must fail on rhythm.
    Revised in squillo iteration 47 (F-050 b): the moved note and the doubled
    duration are taken at indices that exist (3 and 2, or the last note of a
    shorter voice), each must-fail input is asserted to differ from the
    must-pass one, and a voice of fewer than two notes is too short to check
    (its must-pass case fails, so its phrase stays pending as before)."""
    tr = max(tracks, key=lambda t: len(t["pitches"]))
    n = min(8, len(tr["pitches"]) - 1)
    on = np.array(tr["onsets"][:n + 1], float) / tr["tpq"]
    mine = [(tr["pitches"][i], float(on[i + 1] - on[i])) for i in range(n)]
    ok = R.compare(mine, tracks)
    ip, ir = min(3, n - 1), min(2, n - 1)
    bad_p = [(p + (1 if i == ip else 0), b) for i, (p, b) in enumerate(mine)]
    bad_r = [(p, b * (2 if i == ir else 1)) for i, (p, b) in enumerate(mine)]
    differs = n >= 1 and bad_p != mine and bad_r != mine
    rp, rr = R.compare(bad_p, tracks), R.compare(bad_r, tracks)

    def rhythm_ok(r):
        return bool(r and r["exact_pitch"] and r["rhythm"] and r["rhythm"]["ioi_match"] == r["rhythm"]["ioi_total"])
    return dict(notes=n, too_short=n < 2, must_fail_inputs_differ=differs, moved_index=ip, doubled_index=ir,
                must_pass=rhythm_ok(ok) and n >= 2,
                must_fail_pitch=differs and not (rp and rp["exact_pitch"]),
                must_fail_rhythm=differs and not rhythm_ok(rr))


def rule2_check(pid, ref, survey):
    """Rule 2's mechanical part, checked on the survey's metadata (squillo
    iteration 47, F-050 b). A Mutopia reference must be a piece the phrase's
    own queries found, and its named file one of that piece's files; a
    Wikipedia reference must be a block the survey lists for that phrase and
    language, and not a copy of an English block. Which block sets the tune is
    read from headings by the agent, so it is not checked here; the earlier
    languages' non-copy blocks that rule 2 passed over are reported."""
    rec = survey[pid]
    if ref[0] == "mutopia":
        _, mid, fname = ref
        piece = next((m for m in rec["mutopia"] if m["id"] == mid), None)
        ok = piece is not None and any(u.endswith("/" + fname) for u in piece["files"])
        return dict(ok=ok, found_by_own_query=piece is not None)
    _, lang, title, bi = ref
    ed = next((w for w in rec["wiki"] if w["lang"] == lang), None)
    blocks = ed["blocks"] if ed else []
    ok = ed is not None and 0 <= bi < len(blocks) and not blocks[bi]["same_as_en_block"]
    earlier = [dict(lang=w["lang"], block=i, heading=b["heading"])
               for w in rec["wiki"] if LANGS.index(w["lang"]) < LANGS.index(lang)
               for i, b in enumerate(w["blocks"]) if not b["same_as_en_block"]]
    return dict(ok=ok, block_listed=ed is not None and 0 <= bi < len(blocks),
                copy=bool(ed and 0 <= bi < len(blocks) and blocks[bi]["same_as_en_block"]),
                earlier_non_copy_blocks=earlier)


def rule2_no_ref_check(pid, survey):
    """A phrase left without a reference: "no score in the 16 editions" must
    mean the survey lists no block; "a copy" must mean every block is one."""
    rec, why = survey[pid], NO_REF[pid]
    blocks = [b for w in rec["wiki"] for b in w["blocks"]]
    if "no score in the 16 editions" in why:
        return dict(ok=not blocks, blocks=len(blocks))
    if "copy" in why:
        return dict(ok=bool(blocks) and all(b["same_as_en_block"] for b in blocks), blocks=len(blocks))
    # squillo iteration 57 (F-054 b): a reason that names no block claim is
    # not checked by anything, so it fails (it used to return ok=True)
    return dict(ok=False, blocks=len(blocks), note="reason names no block claim")


def rule2_all():
    """Rule 2 checked on every named reference and every phrase without one,
    after the check itself passes the references as named and fails three
    references that break it (each differs in the reference read)."""
    survey = json.load(open(RES / "r2-survey.json"))
    must_fail = {
        "copied block (aura-lea fr 0)": ("aura-lea", ("wiki", "fr", "Aura Lea", 0)),
        "piece not found by the phrase's queries (abide-with-me, Mutopia 194)":
            ("abide-with-me", ("mutopia", 194, "Old100-orig.mid")),
        "block not listed (la-donna-e-mobile de 1)": ("la-donna-e-mobile", ("wiki", "de", "La donna è mobile", 1)),
    }
    fail_res = {k: rule2_check(pid, ref, survey)["ok"] for k, (pid, ref) in must_fail.items()}
    named = {pid: rule2_check(pid, REFS[pid][0], survey) for pid in REFS}
    none = {pid: rule2_no_ref_check(pid, survey) for pid in NO_REF}
    # the no-reference check's own must-fail: a phrase with a non-copy block called "no score"
    NO_REF["_probe"] = "no score in the 16 editions"
    survey["_probe"] = survey["la-donna-e-mobile"]
    probe = rule2_no_ref_check("_probe", survey)["ok"]
    # and (squillo iteration 57, F-054 b) a reason naming no block claim, which
    # must fail now that that branch can
    NO_REF["_probe"] = "no reference, for a reason naming no block claim"
    probe_unclaimed = rule2_no_ref_check("_probe", survey)["ok"]
    del NO_REF["_probe"], survey["_probe"]
    out = dict(must_fail=fail_res, must_fail_no_ref_la_donna_called_no_score=probe,
               must_fail_no_ref_reason_names_no_claim=probe_unclaimed,
               named=named, no_reference=none,
               all_named_pass=all(v["ok"] for v in named.values()),
               all_no_ref_pass=all(v["ok"] for v in none.values()),
               check_fails_when_it_must=not any(fail_res.values()) and not probe and not probe_unclaimed)
    assert out["check_fails_when_it_must"], out
    # squillo iteration 57 (F-054 b): recorded and now asserted
    assert out["all_named_pass"], out["named"]
    assert out["all_no_ref_pass"], out["no_reference"]
    return out


def check():
    by_id = {c["id"]: c for c in L.CANDIDATES}
    r2 = rule2_all()
    json.dump(r2, open(RES / "r2-rule2.json", "w"), indent=1, ensure_ascii=False)
    print("rule 2:", {k: r2[k] for k in ("must_fail", "must_fail_no_ref_la_donna_called_no_score",
                                          "must_fail_no_ref_reason_names_no_claim", "all_named_pass", "all_no_ref_pass")})
    r1 = json.load(open(RES / "summary.json"))["survive"]["per_phrase"]
    out = []
    for pid in PENDING:
        rec = dict(id=pid, round1=r1[pid])
        if pid in NO_REF:
            rec.update(reference=None, reason=NO_REF[pid], verdict="pending-no-reference")
            out.append(rec)
            print(f"{pid:24s} no reference")
            continue
        ref, why = REFS[pid]
        tracks, info = ref_tracks(ref, pid)
        rec.update(reference=info, why=why, tracks=len(tracks))
        if not tracks:
            rec["verdict"] = "pending-reference-unreadable"
            out.append(rec)
            print(f"{pid:24s} unreadable")
            continue
        rec["self_check"] = sc = self_check(tracks)
        if not (sc["must_pass"] and sc["must_fail_pitch"] and sc["must_fail_rhythm"]):
            # S15: a check that fails its own cases is no check; the phrase stays pending
            rec["verdict"] = "pending-check-failed"
            out.append(rec)
            print(f"{pid:24s} check failed its own cases: {sc}")
            continue
        r = R.compare(R.parse(by_id[pid]["melody"]), tracks)
        rec["result"] = r
        pitch = bool(r and r["exact_pitch"])
        rhythm = bool(pitch and r["rhythm"] and r["rhythm"]["ioi_match"] == r["rhythm"]["ioi_total"])
        if pitch and rhythm:
            rec["verdict"] = "verified-2" if r1[pid] == "melody-unchecked" else "verified-variant"
        else:
            rec["verdict"] = "pending-pitch-differs" if not pitch else "pending-rhythm-differs"
        out.append(rec)
        print(f"{pid:24s} {rec['verdict']:24s} miss={r and r['interval_miss']}/{r and r['intervals']} "
              f"edit={r and r['pitch_edit']} rhythm={r and r['rhythm']} self={rec['self_check']}")
    json.dump(out, open(RES / "r2-check.json", "w"), indent=1, ensure_ascii=False)


# ---------------------------------------------------------------- report

def report():
    chk = json.load(open(RES / "r2-check.json"))
    ver = {c["id"]: c for c in json.load(open(RES / "verify.json"))["candidates"]}
    r1 = json.load(open(RES / "summary.json"))["survive"]
    by_id = {c["id"]: c for c in L.CANDIDATES + L.ORIGINALS}
    now = dict(r1["per_phrase"])
    for c in chk:
        now[c["id"]] = c["verdict"]
    verified = [k for k, v in now.items() if v.startswith("verified")]
    pd = [k for k in verified if ver[k]["kind"] == "public-domain"]
    ship = [k for k in verified if ver[k]["kind"] != "public-domain" or (ver[k]["us"] and ver[k]["life100"])]
    from collections import Counter
    out = dict(
        pending=len(chk),
        references_named=sum(1 for c in chk if c["reference"]),
        no_reference=[c["id"] for c in chk if not c["reference"]],
        check_failed=[c["id"] for c in chk if c["verdict"] == "pending-check-failed"],
        checks_self=dict(run=sum(1 for c in chk if "self_check" in c),
                         all_three_hold=sum(1 for c in chk if "self_check" in c and all(
                             c["self_check"][k] for k in ("must_pass", "must_fail_pitch", "must_fail_rhythm")))),
        verdicts=dict(Counter(c["verdict"] for c in chk)),
        per_phrase={c["id"]: dict(round1=c["round1"], round2=c["verdict"],
                                  reference=c["reference"] and {k: c["reference"].get(k) for k in (
                                      "source", "piece", "edition", "licence", "lang", "article", "revid", "block")},
                                  result=c.get("result") and {k: c["result"][k] for k in (
                                      "interval_miss", "intervals", "pitch_edit", "exact_pitch", "rhythm")})
                    for c in chk},
        verified=len(verified), verified_public_domain=len(pd), verified_original=len(verified) - len(pd),
        verified_variant=[k for k, v in now.items() if v == "verified-variant"],
        verified_shippable_us_life100=len(ship),
        verified_genres=dict(Counter(by_id[k]["genre"] for k in verified)),
        verified_genre_count=len({by_id[k]["genre"] for k in verified}),
        target=30,
    )
    json.dump(out, open(RES / "r2-summary.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in out.items() if k != "per_phrase"}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    {"survey": survey, "check": check, "report": report}[sys.argv[1]]()
