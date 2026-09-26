"""E-004 round 1: verify, check and measure the candidate phrase library.

    uv run python run.py verify    # rights rules + Wikidata dates -> results/verify.json
    uv run python run.py scores    # melodies against Wikipedia scores -> results/scores.json
    uv run python run.py measure   # E-005 intent inference on each phrase -> results/measure.json
    uv run python report.py        # -> results/summary.json, library.json, SOURCES.md

Crude experiment code. Network reads (Wikipedia, Wikidata) are cached under
data/cache/ and never committed; the page revision ids used are recorded in
the results, so a later run can refetch the same revisions.

Rights rules, evaluated as at 2026-01-01 (squillo iteration 23):
  us       text and tune each first published in or before 1930: the US term
           for works published 1930 ran out at the end of 2025 (17 U.S.C.
           304, 95 years from publication).
  life70   every named author, composer, translator and arranger died in or
           before 1955; an anonymous part published in or before 1955. The
           EU and UK term (Directive 2006/116/EC art. 1; CDPA 1988 s. 12),
           and Sweden's (URL 43 §).
  life100  as life70 with 1925: Mexico's life + 100 (Ley Federal del Derecho
           de Autor, art. 29), the longest general term in force.
A phrase is publishable here when it passes `us` and `life70`; it may carry
the Public Domain Mark (free of known restrictions worldwide) only when it
also passes `life100`.
"""

import json
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

import numpy as np

import library as L

HERE = Path(__file__).parent
CACHE = HERE / "data" / "cache"
RES = HERE / "results"
UA = {"User-Agent": "squillo-lab-E004/0.1 (research experiment; https://github.com/ZerNox/squillo-lab)"}
YEAR = 2026

# English Wikipedia article per candidate, for the Wikidata publication check
ARTICLES = {
    "amazing-grace": "Amazing Grace", "old-hundredth": "Old 100th",
    "holy-holy-holy": "Holy, Holy, Holy! Lord God Almighty", "abide-with-me": "Abide with Me",
    "jesus-loves-me": "Jesus Loves Me", "swing-low": "Swing Low, Sweet Chariot",
    "silent-night": "Silent Night", "joy-to-the-world": "Joy to the World",
    "o-come-all-ye-faithful": "O Come, All Ye Faithful", "hark-the-herald": "Hark! The Herald Angels Sing",
    "god-rest-ye-merry": "God Rest You Merry, Gentlemen", "jingle-bells": "Jingle Bells",
    "deck-the-halls": "Deck the Halls", "in-the-bleak-midwinter": "In the Bleak Midwinter",
    "twinkle": "Twinkle, Twinkle, Little Star", "row-your-boat": "Row, Row, Row Your Boat",
    "frere-jacques": "Frère Jacques", "auld-lang-syne": "Auld Lang Syne",
    "my-bonnie": "My Bonnie Lies over the Ocean", "danny-boy": "Danny Boy", "aura-lea": "Aura Lea",
    "clementine": "Oh My Darling, Clementine", "yankee-doodle": "Yankee Doodle",
    "greensleeves": "Greensleeves", "god-save-the-king": "God Save the King",
    "star-spangled-banner": "The Star-Spangled Banner", "la-marseillaise": "La Marseillaise",
    "ode-to-joy": "Ode to Joy", "brahms-lullaby": "Wiegenlied (Brahms)",
    "la-donna-e-mobile": "La donna è mobile", "habanera": "Habanera (aria)",
}

# ---------------------------------------------------------------- melody

NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi(p):
    m = re.fullmatch(r"([A-G])([#b]?)(-?\d)", p)
    n = NOTE[m[1]] + {"#": 1, "b": -1, "": 0}[m[2]]
    return 12 * (int(m[3]) + 1) + n


def parse(mel):
    out = []
    for tok in mel.split():
        p, b = tok.split(":")
        out.append((midi(p), float(b)))
    return out


# ---------------------------------------------------------------- network

def get_json(url, cache_name):
    f = CACHE / cache_name
    if f.exists():
        return json.loads(f.read_text())
    for i in range(6):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(d))
            time.sleep(1.0)
            return d
        except Exception as e:  # 429s: back off
            print("retry", url[:80], e, file=sys.stderr)
            time.sleep(10 * (i + 1))
    raise RuntimeError(url)


def api(lang, **kw):
    kw.update(format="json", formatversion=2)
    return f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(kw)


def safe(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", s)


def h(chunk):
    import hashlib
    return hashlib.sha1("|".join(chunk).encode()).hexdigest()[:16]


def qids(titles, lang="en"):
    """enwiki title -> Wikidata QID (following redirects)."""
    out = {}
    titles = sorted(set(titles))
    for k in range(0, len(titles), 40):
        chunk = titles[k:k + 40]
        d = get_json(api(lang, action="query", prop="pageprops", ppprop="wikibase_item",
                         titles="|".join(chunk), redirects=1),
                     f"wd/qids-{lang}-{h(chunk)}.json")
        norm = {x["from"]: x["to"] for x in d["query"].get("normalized", [])}
        redir = {x["from"]: x["to"] for x in d["query"].get("redirects", [])}
        pages = {p["title"]: p.get("pageprops", {}).get("wikibase_item") for p in d["query"]["pages"]}
        for t in chunk:
            u = norm.get(t, t)
            u = redir.get(u, u)
            out[t] = pages.get(u)
    return out


def claims_years(qs, props):
    """QID -> {prop: [years]} from Wikidata."""
    out = {}
    qs = sorted(q for q in set(qs) if q)
    for k in range(0, len(qs), 40):
        chunk = qs[k:k + 40]
        d = get_json("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
            dict(action="wbgetentities", ids="|".join(chunk), props="claims|labels", languages="en",
                 format="json")), f"wd/claims-{h(chunk)}.json")
        for q, e in d["entities"].items():
            yrs = {}
            for p in props:
                ys = []
                for c in e.get("claims", {}).get(p, []):
                    v = c["mainsnak"].get("datavalue", {}).get("value")
                    if isinstance(v, dict) and "time" in v:
                        m = re.match(r"([+-]\d+)-", v["time"])
                        ys.append(int(m[1]))
                yrs[p] = ys
            yrs["label"] = e.get("labels", {}).get("en", {}).get("value")
            out[q] = yrs
    return out


# ---------------------------------------------------------------- verify

def passes(parts, cutoff_death, cutoff_anon):
    """parts: [(people, published_by)]; every person died <= cutoff_death,
    an anonymous part published <= cutoff_anon. Unknown fails."""
    for people, pub in parts:
        if not people:
            if pub is None or pub > cutoff_anon:
                return False
        for p in people:
            if p["died_eff"] is None or p["died_eff"] > cutoff_death:
                return False
    return True


def verify():
    people = [p for c in L.CANDIDATES for p in c["text_by"] + c["tune_by"]]
    people += [p for t in L.TRAPS for p in t["by"]]
    q = qids([p["wiki"] for p in people])
    wd = claims_years(q.values(), ["P570", "P569"])
    qa = qids(ARTICLES.values())
    wda = claims_years(qa.values(), ["P577", "P571"])

    def enrich(p):
        qq = q.get(p["wiki"])
        ys = wd.get(qq, {}).get("P570", []) if qq else []
        rec = p["died"]
        agree = None if (rec is None or not ys) else (rec in ys)
        cands = [y for y in ([rec] if rec is not None else []) + ys]
        return dict(p, qid=qq, wd_label=wd.get(qq, {}).get("label") if qq else None,
                    wd_died=ys, agree=agree, died_eff=max(cands) if cands else None)

    out = []
    for c in L.CANDIDATES:
        tb = [enrich(p) for p in c["text_by"]]
        ub = [enrich(p) for p in c["tune_by"]]
        parts = [(tb, c["text_published_by"]), (ub, c["tune_published_by"])]
        pubs = [c["text_published_by"], c["tune_published_by"]]
        us = all(p is not None and p <= YEAR - 96 for p in pubs)
        l70 = passes(parts, YEAR - 71, YEAR - 71)
        l100 = passes(parts, YEAR - 101, YEAR - 101)
        art = ARTICLES.get(c["id"])
        aq = qa.get(art)
        wpub = sorted(wda.get(aq, {}).get("P577", []) + wda.get(aq, {}).get("P571", [])) if aq else []
        ours = min(p for p in pubs if p is not None)
        out.append(dict(id=c["id"], kind="public-domain", genre=c["genre"], text_by=tb, tune_by=ub,
                        text_published_by=c["text_published_by"], tune_published_by=c["tune_published_by"],
                        us=us, life70=l70, life100=l100, publishable=us and l70, pdm=us and l70 and l100,
                        article=art, article_qid=aq, wd_pub_years=wpub,
                        # a Wikidata year later than our upper bound for the
                        # earliest part is a conflict only if every Wikidata
                        # year is later (the item may date a later version)
                        wd_pub_conflict=(bool(wpub) and min(wpub) > max(p for p in pubs if p is not None))))
        del ours
    for o in L.ORIGINALS:
        out.append(dict(id=o["id"], kind="original", genre=o["genre"], us=True, life70=True, life100=True,
                        publishable=True, pdm=False))
    traps = []
    for t in L.TRAPS:
        by = [enrich(p) for p in t["by"]]
        parts = [(by, t["published_by"])]
        us = t["published_by"] is not None and t["published_by"] <= YEAR - 96
        l70 = passes(parts, YEAR - 71, YEAR - 71)
        l100 = passes(parts, YEAR - 101, YEAR - 101)
        traps.append(dict(id=t["id"], title=t["title"], by=by, published_by=t["published_by"],
                          us=us, life70=l70, life100=l100, rejected=not (us and l70)))
    RES.mkdir(exist_ok=True)
    json.dump(dict(candidates=out, traps=traps, as_at=f"{YEAR}-01-01"),
              open(RES / "verify.json", "w"), indent=1, ensure_ascii=False)
    n = Counter((r["kind"], r["publishable"]) for r in out)
    print("publishable:", dict(n), "traps rejected:", sum(t["rejected"] for t in traps), "/", len(traps))
    for r in out:
        for p in r.get("text_by", []) + r.get("tune_by", []):
            if p["agree"] is not True:
                print("  date check:", r["id"], p["wiki"], p["died"], p["wd_died"], p["qid"], p["wd_label"])
        if r.get("wd_pub_conflict"):
            print("  pub conflict:", r["id"], r["text_published_by"], r["tune_published_by"], r["wd_pub_years"])


# ---------------------------------------------------------------- scores

LY = str(__import__("lilypond").executable())


def wikitext(lang, title):
    d = get_json(api(lang, action="query", prop="revisions", rvprop="content|ids", rvslots="main",
                     titles=title, redirects=1), f"wiki/{lang}-{safe(title)}.json")
    p = d["query"]["pages"][0]
    r = p["revisions"][0]
    return p["title"], r["revid"], r["slots"]["main"]["content"]


MIDI_CTX = ('\\context { \\Staff \\remove "Staff_performer" } '
            '\\context { \\Voice \\consists "Staff_performer" }')  # one MIDI track per voice


def close_score(body, blk):
    """Insert an output block before the brace that closes each \\score."""
    out, i = [], 0
    for m in re.finditer(r"\\score\s*\{", body):
        if m.start() < i:
            continue
        depth, j = 1, m.end()
        while j < len(body) and depth:
            depth += {"{": 1, "}": -1}.get(body[j], 0)
            j += 1
        out.append(body[i:j - 1] + "\n" + blk + "\n}")
        i = j
    return "".join(out) + body[i:]


def to_midi(src, attrs, name):
    """Compile a Wikipedia <score> body (LilyPond, or ABC through LilyPond's
    abc2ly) to MIDI with one track per voice; returns (path, attempt)."""
    d = CACHE / "ly"
    d.mkdir(parents=True, exist_ok=True)
    raw = 'raw="1"' in attrs or re.search(r"\braw\b", attrs) is not None
    if "abc" in attrs.lower():
        f = d / f"{name}.abc"
        f.write_text(src.strip() + "\n")
        subprocess.run([str(Path(LY).parent / "abc2ly"), "-o", str(d / f"{name}.abc.ly"), str(f)],
                       capture_output=True, timeout=120)
        if not (d / f"{name}.abc.ly").exists():
            return None, None
        src, raw = (d / f"{name}.abc.ly").read_text(), True
    body = src
    midi_blk = "\\midi { " + MIDI_CTX + " }"
    attempts = []
    if not raw and "\\score" not in body:
        attempts.append("\\score {\n" + body + "\n\\layout { }\n" + midi_blk + "\n}\n")
    if "\\midi" in body:
        attempts.append(re.sub(r"\\midi\s*\{", lambda m: "\\midi { " + MIDI_CTX, body))
    else:
        if re.search(r"\\layout\s*\{", body):
            attempts.append(re.sub(r"\\layout\s*\{", lambda m: midi_blk + " \\layout {", body))
        else:
            attempts.append(close_score(body, midi_blk))
        attempts.append("\\score {\n" + body + "\n\\layout { }\n" + midi_blk + "\n}\n")
    for k, a in enumerate(attempts):
        f = d / f"{name}-{k}.ly"
        f.write_text(a)
        for old in d.glob(f"{name}-{k}*.mid*"):
            old.unlink()
        subprocess.run([LY, "-s", "-o", str(d / f"{name}-{k}"), str(f)], capture_output=True, timeout=120)
        mids = sorted(d.glob(f"{name}-{k}*.mid*"))
        if mids:
            return mids[0], k
    return None, None


def midi_tracks(path):
    import mido
    m = mido.MidiFile(path)
    tracks = []
    for tr in m.tracks:
        t, on, notes = 0, {}, []
        for msg in tr:
            t += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                on.setdefault(msg.note, []).append(t)
            elif msg.type in ("note_off", "note_on"):
                if on.get(msg.note):
                    s = on[msg.note].pop(0)
                    notes.append((s, t, msg.note))
        if not notes:
            continue
        # one line per track: highest pitch at each onset
        by_on = {}
        for s, e, n in notes:
            if s not in by_on or n > by_on[s][1]:
                by_on[s] = (e, n)
        seq = [(s, by_on[s][0], by_on[s][1]) for s in sorted(by_on)]
        tracks.append(dict(onsets=[x[0] for x in seq], pitches=[x[2] for x in seq],
                           tpq=m.ticks_per_beat))
    return tracks


def lev(a, b):
    D = np.arange(len(b) + 1, dtype=int)
    for i in range(1, len(a) + 1):
        prev, D[0] = D[0], i
        for j in range(1, len(b) + 1):
            cur = min(D[j] + 1, D[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
            prev, D[j] = D[j], cur
    return int(D[-1])


def compare(mine, tracks):
    """Best placement of my phrase in any track: interval matches, pitch
    edit distance (transposition removed), and rhythm when pitches match."""
    mp = [p for p, _ in mine]
    mb = [b for _, b in mine]
    mi = np.diff(mp)
    best = None
    for ti, tr in enumerate(tracks):
        sp, so = tr["pitches"], tr["onsets"]
        for j in range(len(sp)):
            w = sp[j:j + len(mp)]
            if len(w) < 2:
                continue
            si = np.diff(w)
            k = min(len(si), len(mi))
            im = int(np.sum(si[:k] == mi[:k])) + 0
            tshift = sp[j] - mp[0]
            ed = min(lev([p + tshift for p in mp], sp[j:j + len(mp) + d]) for d in (-1, 0, 1, 2)
                     if len(mp) + d > 0)
            cand = (len(mi) - im if len(w) == len(mp) else len(mi) + 1, ed, ti, j)
            if best is None or cand[:2] < best[0][:2]:
                best = (cand, tshift)
    if best is None:
        return None
    (miss, ed, ti, j), tshift = best
    tr = tracks[ti]
    exact = miss == 0
    rhythm = None
    if exact and j + len(mp) <= len(tr["onsets"]):
        so = np.array(tr["onsets"][j:j + len(mp)], float) / tr["tpq"]
        ioi_s = np.diff(so)
        ioi_m = np.array(mb[:-1])
        # compare inter-onset intervals up to one overall factor (the score may
        # write in halves where I wrote quarters): least-squares scale
        scale = float(np.dot(ioi_s, ioi_m) / np.dot(ioi_m, ioi_m))
        ok = np.abs(ioi_s - scale * ioi_m) <= 1e-6 + 0.02 * scale * ioi_m
        rhythm = dict(scale=scale, ioi_match=int(ok.sum()), ioi_total=len(ok))
    return dict(track=ti, start=j, transpose=int(tshift), interval_miss=int(miss),
                intervals=len(mi), pitch_edit=int(ed), exact_pitch=bool(exact), rhythm=rhythm,
                context=tr["pitches"][max(0, j - 2):j + len(mp) + 2])


def scores():
    out = []
    for c in L.CANDIDATES:
        if not c["score"]:
            continue
        lang, title, idx = c["score"]
        real, revid, w = wikitext(lang, title)
        blocks = re.findall(r"<score([^>]*)>(.*?)</score>", w, re.S)
        rec = dict(id=c["id"], lang=lang, article=real, revid=revid, blocks=len(blocks),
                   seen_before=c["seen_before"])
        tried = []
        # the block named in library.py (an article may hold several settings)
        for bi, (attrs, src) in ([(idx, blocks[idx])] if idx < len(blocks) else []):
            mid, how = to_midi(src, attrs, f'{c["id"]}-b{bi}')
            if mid is None:
                tried.append(dict(block=bi, error="lilypond failed"))
                continue
            tracks = midi_tracks(mid)
            r = compare(parse(c["melody"]), tracks) if tracks else None
            tried.append(dict(block=bi, compile_attempt=how, tracks=len(tracks), result=r))
        ok = [t for t in tried if t.get("result")]
        if not ok:
            rec["error"] = "no block compiled to a melody"
            rec["tried"] = tried
            out.append(rec)
            print(c["id"], rec["error"])
            continue
        best = min(ok, key=lambda t: (t["result"]["interval_miss"], t["result"]["pitch_edit"]))
        rec.update(best, blocks_compiled=len(ok))
        out.append(rec)
        r = rec["result"]
        print(f'{c["id"]:24s} block={best["block"]} tracks={best["tracks"]} miss={r["interval_miss"]}/{r["intervals"]} '
              f'edit={r["pitch_edit"]} rhythm={r["rhythm"]}')
    json.dump(out, open(RES / "scores.json", "w"), indent=1, ensure_ascii=False)


# ---------------------------------------------------------------- measure

def _load():
    """E-005's modules, loaded by path (their names clash with this file's)."""
    global _ctx
    if _ctx is None:
        import importlib.util
        e005 = HERE.parent / "E-005-intent-inference"
        sys.path.insert(0, str(e005))
        sys.path.insert(0, str(HERE.parent / "E-002-measurement-reliability"))

        def load(name, f):
            spec = importlib.util.spec_from_file_location(name, e005 / f)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            return m
        e5run = load("e005_run", "run.py")  # track, evaluate, note_frames, oracle_from
        e5rep = load("e005_report", "report.py")  # attribution, TRANS_S
        import synth as e5syn  # E-005's synth.py (contour; E-001's voice)
        from scipy.signal import butter, sosfiltfilt
        _ctx = (e5run, e5rep, e5syn, e5syn.voice, butter, sosfiltfilt)
    return _ctx


_ctx = None


def measure():
    """Sing each phrase with E-005's synthetic voice and infer intent."""
    from multiprocessing import Pool
    e5run = _load()[0]
    jobs = []
    seed = 2026092623
    items = [(c["id"], c["melody"], c["tempo"]) for c in L.CANDIDATES + L.ORIGINALS]
    for pid, mel, tempo in items:
        for v in e5run.VOICES:
            for sigma in (0, 20):
                for vib in (0, 1):
                    seed += 1
                    jobs.append((pid, mel, tempo, v, sigma, vib, seed))
    with Pool(18) as p:
        res = p.map(_one, jobs, chunksize=2)
    json.dump(res, open(RES / "measure.json", "w"), indent=0)
    print(len(res), "renderings")


def _one(job):
    e5run, e5rep, e5syn, voice, butter, sosfiltfilt = _load()
    pid, mel, tempo, v, sigma, vib, seed = job
    notes_m = parse(mel)
    sex, base = voice.VOICES[v]
    rng = np.random.default_rng(seed)
    semis = np.array([m - 69 for m, _ in notes_m], float)  # re A4
    # transpose into the voice: phrase mean on the voice's base + 5 semitones,
    # then by octaves back inside E-005's bounds (<= min(12, base + 17), >= -27)
    semis += np.round(base + 5 - semis.mean())
    while semis.max() > min(12, base + 17):
        semis -= 12
    while semis.min() < -27:
        semis += 12
    durs = np.array([b for _, b in notes_m]) * 60.0 / tempo
    starts = np.concatenate([[0.0], np.cumsum(durs)[:-1]]) + 0.1
    T = starts[-1] + durs[-1] + 0.1
    n = int(round(T * voice.SR))
    t = np.arange(n) / voice.SR
    G = rng.uniform(-50, 50)
    e = rng.normal(0, sigma, len(semis))
    sung = e5syn.contour(100.0 * semis + e, starts, n) + G
    idx = np.clip(np.searchsorted(starts, t, "right") - 1, 0, None)
    since = t - starts[idx]
    depth = rng.uniform(30, 100, len(semis)) * (rng.random(len(semis)) < 0.5)
    sung -= depth[idx] * np.exp(-np.maximum(since, 0) / 0.06)
    if vib:
        sung += 50.0 * np.clip((since - 0.15) / 0.1, 0, 1) * np.sin(2 * np.pi * 5.5 * t)
    sos = butter(2, [1.0, 6.0], btype="band", fs=voice.SR, output="sos")
    w = sosfiltfilt(sos, rng.standard_normal(n))
    sung += 10.0 * w / np.sqrt(np.mean(w ** 2))
    amp = np.ones(n)
    amp[t < 0.1] = 0
    amp[t > T - 0.1] = 0
    amp = np.convolve(amp, np.ones(960) / 960, mode="same")
    x = voice.render(dict(sex=sex, n=n, amp=amp, noise_seed=seed + 1000), sung).astype(np.float32)
    tt, cents, dmin = e5run.track(x)
    nof, mid = e5run.note_frames(tt, starts, durs)
    r = e5run.evaluate(tt, cents, nof, mid, e5run.oracle_from(nof))
    item = dict(res=r, nof=nof, mid=mid)
    true = semis.astype(int)
    out = dict(id=pid, voice=v, sigma=sigma, vib=vib, n_notes=len(semis),
               lo=int(true.min()), hi=int(true.max()),
               short=int(np.sum(durs < e5rep.TRANS_S)))
    for key in (("est", "global", "chromatic"), ("oracle", "global", "chromatic")):
        calls, ok, modal = e5rep.attribution(item, key, true)
        # E-005's "found": the aimed note recovered, relative to the take's own tuning
        out["_".join(key[:1])] = dict(found=int(ok.sum()), called=int(sum(c[0] is not None for c in calls)),
                                      missed=[int(i) for i in np.where(~ok)[0]])
    return out


if __name__ == "__main__":
    {"verify": verify, "scores": scores, "measure": measure}[sys.argv[1]]()
