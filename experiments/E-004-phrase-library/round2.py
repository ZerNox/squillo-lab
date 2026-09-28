"""E-004 round 2 (squillo iteration 41): the 18 pending melodies against a
second, independent transcription named in advance (squillo F-026, S16).

    uv run python round2.py survey   # which sources exist, metadata only -> results/r2-survey.json
    uv run python round2.py check    # each phrase against the reference named in REFS -> results/r2-check.json
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
        return f.read_text()
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


if __name__ == "__main__":
    {"survey": survey}[sys.argv[1]]()
