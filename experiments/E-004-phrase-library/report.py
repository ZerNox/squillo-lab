"""E-004 round 1: summarise verify, scores and measure.

    uv run python report.py   # -> results/summary.json, results/library.json, results/SOURCES.md

Crude experiment code.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

import library as L
from run import parse

HERE = Path(__file__).parent
RES = HERE / "results"


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(100 * (c - h), 1), round(100 * (c + h), 1))


def pct(k, n):
    return dict(k=k, n=n, pct=round(100 * k / n, 1) if n else None, ci95=wilson(k, n))


def main():
    ver = json.load(open(RES / "verify.json"))
    sco = {r["id"]: r for r in json.load(open(RES / "scores.json"))}
    mea = json.load(open(RES / "measure.json"))
    cands = {c["id"]: c for c in L.CANDIDATES}
    origs = {o["id"]: o for o in L.ORIGINALS}
    V = {r["id"]: r for r in ver["candidates"]}

    # ---- rights
    pd = [r for r in ver["candidates"] if r["kind"] == "public-domain"]
    people = {}
    for r in pd:
        for p in r["text_by"] + r["tune_by"]:
            people[p["wiki"]] = p
    for t in ver["traps"]:
        for p in t["by"]:
            people[p["wiki"]] = p
    agree = Counter("agree" if p["agree"] else ("no wikidata date" if p["agree"] is None else "disagree")
                    for p in people.values())
    rights = dict(
        as_at=ver["as_at"],
        pd_candidates=len(pd),
        pass_us=sum(r["us"] for r in pd), pass_life70=sum(r["life70"] for r in pd),
        pass_life100=sum(r["life100"] for r in pd),
        publishable=sum(r["publishable"] for r in pd), pdm_eligible=sum(r["pdm"] for r in pd),
        fail=[r["id"] for r in pd if not r["publishable"]],
        life70_not_life100=[r["id"] for r in pd if r["publishable"] and not r["life100"]],
        traps=len(ver["traps"]), traps_rejected=sum(t["rejected"] for t in ver["traps"]),
        trap_rules={t["id"]: dict(us=t["us"], life70=t["life70"], life100=t["life100"]) for t in ver["traps"]},
        people=len(people), people_dates=dict(agree),
        disagreements=[dict(wiki=p["wiki"], recorded=p["died"], wikidata=p["wd_died"])
                       for p in people.values() if p["agree"] is False],
        no_wikidata_date=[p["wiki"] for p in people.values() if p["agree"] is None],
        pub_conflicts=[dict(id=r["id"], ours=[r["text_published_by"], r["tune_published_by"]],
                            wikidata=r["wd_pub_years"], qid=r["article_qid"]) for r in pd if r["wd_pub_conflict"]],
        articles_with_wd_pub=sum(bool(r["wd_pub_years"]) for r in pd),
    )

    # ---- melody against an independent transcription
    checked = [i for i in cands if i in sco and "result" in sco[i]]
    exact = [i for i in checked if sco[i]["result"]["exact_pitch"]]
    unseen = [i for i in checked if not cands[i]["seen_before"]]
    rhythm_ok = [i for i in exact if sco[i]["result"]["rhythm"]
                 and sco[i]["result"]["rhythm"]["ioi_match"] == sco[i]["result"]["rhythm"]["ioi_total"]]
    ints_total = sum(sco[i]["result"]["intervals"] for i in checked)
    ints_miss = sum(min(sco[i]["result"]["interval_miss"], sco[i]["result"]["intervals"]) for i in checked)
    melody = dict(
        candidates_with_score=len([c for c in cands.values() if c["score"]]),
        checked=len(checked), pitch_exact=pct(len(exact), len(checked)),
        pitch_exact_unseen=pct(len([i for i in unseen if i in exact]), len(unseen)),
        intervals_right=pct(ints_total - ints_miss, ints_total),
        rhythm_exact_given_pitch=pct(len(rhythm_ok), len(exact)),
        mismatched=[dict(id=i, miss=sco[i]["result"]["interval_miss"], of=sco[i]["result"]["intervals"],
                         edit=sco[i]["result"]["pitch_edit"]) for i in checked if i not in exact],
        rhythm_differs=[dict(id=i, **sco[i]["result"]["rhythm"]) for i in exact if i not in rhythm_ok],
        no_score=[i for i in cands if i not in checked],
        revisions={i: dict(lang=sco[i]["lang"], article=sco[i]["article"], revid=sco[i]["revid"],
                           block=sco[i].get("block")) for i in sco},
    )

    # ---- intent inference on the phrases (E-005's method)
    agg = defaultdict(lambda: [0, 0])
    byphrase = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for x in mea:
        for s in ("est", "oracle"):
            agg[(s, x["sigma"], x["vib"])][0] += x[s]["found"]
            agg[(s, x["sigma"], x["vib"])][1] += x["n_notes"]
        byphrase[x["id"]][(x["sigma"], x["vib"])][0] += x["est"]["found"]
        byphrase[x["id"]][(x["sigma"], x["vib"])][1] += x["n_notes"]
    rng = np.random.default_rng(23)
    ids = sorted(byphrase)
    inference = {}
    for (s, sig, vib), (k, n) in sorted(agg.items()):
        # bootstrap over phrases: notes within a phrase are not independent
        per = np.array([[byphrase[i][(sig, vib)][0], byphrase[i][(sig, vib)][1]] for i in ids]) if s == "est" else None
        ci = None
        if per is not None:
            bs = []
            for _ in range(2000):
                j = rng.integers(0, len(ids), len(ids))
                bs.append(per[j, 0].sum() / per[j, 1].sum())
            ci = [round(100 * float(np.percentile(bs, 2.5)), 1), round(100 * float(np.percentile(bs, 97.5)), 1)]
        inference[f"{s} sigma={sig} vibrato={'5.5Hz +-50c' if vib else 'none'}"] = dict(
            found=k, notes=n, pct=round(100 * k / n, 1), ci95_phrase_bootstrap=ci)
    durs = {i: [b * 60 / (cands.get(i) or origs.get(i))["tempo"]
                for _, b in parse((cands.get(i) or origs.get(i))["melody"])] for i in ids}
    by_len = {}
    for sig in (0, 20):
        allx, miss = [], []
        for x in mea:
            if x["vib"] == 1 and x["sigma"] == sig:
                d = durs[x["id"]]
                allx += d
                miss += [d[i] for i in x["est"]["missed"]]
        allx, miss = np.array(allx), np.array(miss)
        for lo, hi in ((0, .3), (.3, .6), (.6, 1.0), (1.0, 9)):
            a = int(np.sum((allx >= lo) & (allx < hi)))
            m = int(np.sum((miss >= lo) & (miss < hi)))
            by_len[f"sigma={sig} vibrato, note {lo}-{hi} s"] = dict(notes=a, found=a - m,
                                                                     pct=round(100 * (a - m) / a, 1))
    worst = sorted(((round(100 * v[(0, 1)][0] / v[(0, 1)][1], 1), i) for i, v in byphrase.items()))[:5]

    # ---- phrase properties
    props = {}
    for i in ids:
        c = cands.get(i) or origs.get(i)
        m = parse(c["melody"])
        ps = [p for p, _ in m]
        props[i] = dict(notes=len(m), range_semitones=max(ps) - min(ps),
                        seconds=round(sum(b for _, b in m) * 60 / c["tempo"], 2),
                        shortest_ms=round(1000 * min(durs[i])), longest_ms=round(1000 * max(durs[i])))

    # ---- what survives
    def status(i):
        if i in origs:
            return "verified-original"
        r = V[i]
        if not r["publishable"]:
            return "rights-fail"
        if i not in checked:
            return "melody-unchecked"
        if i not in exact:
            return "melody-mismatch"
        if i not in rhythm_ok:
            return "rhythm-differs"
        return "verified-public-domain"
    st = {i: status(i) for i in list(cands) + list(origs)}
    verified = [i for i, s in st.items() if s.startswith("verified")]
    genres = Counter((cands.get(i) or origs.get(i))["genre"] for i in verified)
    survive = dict(
        target=30, candidates=len(st), status=dict(Counter(st.values())),
        verified=len(verified), verified_public_domain=sum(s == "verified-public-domain" for s in st.values()),
        verified_original=sum(s == "verified-original" for s in st.values()),
        verified_genres=dict(genres), verified_genre_count=len(genres),
        rights_verified_melody_pending=[i for i, s in st.items() if s in ("melody-unchecked", "melody-mismatch", "rhythm-differs")],
        per_phrase=st,
    )
    ranges = [p["range_semitones"] for p in props.values()]
    secs = [p["seconds"] for p in props.values()]
    summary = dict(rights=rights, melody=melody, inference=inference, inference_by_note_length=by_len,
                   inference_worst_vibrato_sigma0=worst, survive=survive,
                   phrases=dict(range_semitones=dict(min=min(ranges), median=float(np.median(ranges)), max=max(ranges)),
                                seconds=dict(min=min(secs), median=float(np.median(secs)), max=max(secs)),
                                octave_or_less=sum(r <= 12 for r in ranges), n=len(ranges)),
                   properties=props)
    json.dump(summary, open(RES / "summary.json", "w"), indent=1, ensure_ascii=False)

    # ---- library.json: every candidate in the shape round 1 recommends
    lib = []
    for i, c in list(cands.items()) + list(origs.items()):
        item = dict(phrase_id=i, title=c["title"], genre=c["genre"], language=c["lang"], words=c["text"],
                    melody=dict(key=c["key"], meter=c["meter"], tempo_qpm=c["tempo"], notes=c["melody"]),
                    status=st[i])
        if i in origs:
            item["content"] = dict(licence="LicenseRef-squillo-adr-0008",
                                   source="Written for squillo in squillo iteration 23 (squillo-lab E-004 round 1); words and melody new")
        else:
            r = V[i]
            item["content"] = dict(
                licence="CC-PDM-1.0" if r["pdm"] else ("LicenseRef-public-domain-us-life70" if r["publishable"] else None),
                source=f'Words: {c["text_source"]}. Tune: {c["tune_source"]}. Melody line transcribed for squillo.',
                rights=dict(text=dict(by=[dict(name=p["wiki"], died=p["died_eff"], role=p["role"]) for p in r["text_by"]],
                                      published_by=c["text_published_by"]),
                            tune=dict(by=[dict(name=p["wiki"], died=p["died_eff"], role=p["role"]) for p in r["tune_by"]],
                                      published_by=c["tune_published_by"]),
                            us=r["us"], life70=r["life70"], life100=r["life100"]),
                melody_checked_against=(dict(transcription=f'{sco[i]["lang"]}.wikipedia.org "{sco[i]["article"]}" revision {sco[i]["revid"]}, score {sco[i].get("block")}',
                                             pitch="match" if i in exact else "mismatch",
                                             rhythm=("match" if i in rhythm_ok else "differs") if i in exact else None)
                                        if i in checked else None))
        lib.append(item)
    json.dump(dict(as_at=ver["as_at"], items=lib), open(RES / "library.json", "w"), indent=1, ensure_ascii=False)

    # ---- SOURCES.md
    lines = ["# E-004 round 1: sources and rights, per candidate", "",
             f"Rights as at {ver['as_at']} (rules in `run.py`). `us`: text and tune published by 1930. "
             "`life70`: every named contributor died by 1955, anonymous parts published by 1955. "
             "`life100`: the same with 1925. Status: see `summary.json`, *survive*.", "",
             "| Phrase | Genre | Words | Tune | us | life70 | life100 | Status |",
             "| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- |"]
    yn = lambda b: "yes" if b else "**no**"  # noqa: E731
    for i, c in cands.items():
        r = V[i]
        who = lambda ps: "; ".join(f'{p["wiki"]} (d. {p["died_eff"] if p["died_eff"] else "?"})' for p in ps) or "anonymous"  # noqa: E731
        lines.append(f'| {c["title"]} | {c["genre"]} | {who(r["text_by"])}, by {c["text_published_by"]}: {c["text_source"]} '
                     f'| {who(r["tune_by"])}, by {c["tune_published_by"]}: {c["tune_source"]} '
                     f'| {yn(r["us"])} | {yn(r["life70"])} | {yn(r["life100"])} | {st[i]} |')
    for i, o in origs.items():
        lines.append(f'| {o["title"]} | {o["genre"]} | original, squillo | original, squillo | yes | yes | n/a | {st[i]} |')
    lines += ["", "## Traps (title and dates only; every one must be rejected)", "",
              "| Trap | Why | us | life70 | life100 | Rejected |", "| :--- | :--- | :---: | :---: | :---: | :---: |"]
    for t, tt in zip(ver["traps"], L.TRAPS):
        lines.append(f'| {t["title"]} | {tt["why"]} | {yn(t["us"])} | {yn(t["life70"])} | {yn(t["life100"])} | {"yes" if t["rejected"] else "**NO**"} |')
    lines += ["", "Death years cross-checked against Wikidata (P570) through each person's English Wikipedia "
              "article; the later year is used when the two disagree. Wikipedia and Wikidata pages are read, "
              "never copied: Wikipedia's score transcriptions (CC BY-SA) serve only as the independent check in "
              "`run.py scores`, and no note of theirs enters `library.py`.", ""]
    (RES / "SOURCES.md").write_text("\n".join(lines))

    print(json.dumps(dict(rights={k: rights[k] for k in ("pd_candidates", "publishable", "pdm_eligible", "traps_rejected", "people_dates")},
                          melody={k: melody[k] for k in ("checked", "pitch_exact", "pitch_exact_unseen", "intervals_right", "rhythm_exact_given_pitch")},
                          survive={k: survive[k] for k in ("verified", "verified_public_domain", "verified_original", "verified_genre_count", "status")},
                          inference=inference, by_len=by_len, worst=worst,
                          phrases=summary["phrases"]), indent=1))


if __name__ == "__main__":
    main()
