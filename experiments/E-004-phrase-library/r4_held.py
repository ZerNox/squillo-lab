"""E-004 round 4 (squillo iteration 68, F-065 with F-060's thin genres): originals written for held notes.

    uv run python r4_held.py write <squillo>   # the 9 items -> results/r4/items/, results/r4/write.json
    uv run python r4_held.py sample            # S19: time a sample of renderings at the pool -> results/r4/sample.json
    uv run python r4_held.py run               # every rendering, saved as it goes -> data/cache/r4/*.json
    uv run python r4_held.py analyse           # -> results/r4/held.json

Question. squillo F-065: at their written tempo 28 of the 30 phrases the first slice ships hold no note long
enough for MT-009's `steadiness` (`squillo-lab E-004 @ f9ea297`, fold3.json S6), and VISION.md §7 names
vowel and scale exercises, which the library lacks. F-060: pop, rock, jazz, blues, soul, country and musical
theatre rest on one original each. Can originals written for held notes, a sustained vowel, a slow scale
and one more line in each thin genre, (a) give CO-005 rule (2) at least two blocks each from their written
notes, while loading with the 34 the slice ships and passing the rights rules and round 3's conditions, and
(b) give MT-009 at least two blocks when sung, measured from the contour alone on a synthetic voice?

Rules, written and committed before any run (S15, S19). Every rule below is asserted in code.

  W  Writing. The 9 items below (ITEMS) are written for squillo in iteration 68, words and melodies new.
     Each is written as fold.py writes an original (format_version 3, instructions from fold.instructions,
     licence fold.ORIGINAL_LICENCE, content exactly licence, source, origin) and asserted, on what was
     written, to:
     W1 load with every file of squillo's fixtures/slice/ together under fold.load_together, none refused;
        must fail: the set plus one new item under a second file name, both copies refused under EX-004;
     W2 pass fold.build_rights; must fail: one new item with the public-domain licence, refused at
        /content/licence;
     W3 lie within round 3's conditions, fold.COND (rule 5(e): 5-20 notes, range <= 16 semitones,
        <= 15 s, no note under 0.1 s, E2-C6), by fold.conditions and the predicate fold.py's C uses,
        restated here as `within` from fold.py lines 603-606; must fail: an item slowed tenfold;
     W4 give CO-005 rule (2) at least BLOCKS_MIN = 2 blocks from its written notes, by fold3.phrase_blocks
        (each written note one held note of its written duration at the tempo, whole 8 ms frames, a note of
        N frames >= 250 giving (N - 124) // 125 blocks); fold3's own cases 249 -> 0, 250 -> 1, 373 -> 1,
        374 -> 2 re-run here first; must fail: each item at three times its tempo, whose every note then
        falls under 250 frames, so no note is held (asserted per item, so the case differs from the
        must-pass in the input). Revision 1, after the first `write` stopped here before any rendering:
        the committed case was twice the tempo, under which an item with two held notes keeps one block
        on each, two in all (held-ah: 576 frames halved to 288 gives 1 block, twice), so the case could
        not fail as stated; the items are unchanged.
     W5 each held note (>= 374 frames written) is at least HELD_MARGIN = 62 frames longer than the
        least note giving its blocks, so that a transition's half (the 2 Hz cut, below) cannot alone cost
        it a block. 62 is MT-009's own trim at each end (fold3.TRIM), chosen as a margin before any run;
        it has no other source, and (b) below tests whether it was enough.
     W6 a novelty screen, recorded, not asserted (no lawful corpus of copyrighted melodies exists here,
        round 1's limit): for each new item, the longest run of consecutive pitch intervals it shares
        with any of the 30 phrases and with any other new item, and which. The vocalises are scales and
        arpeggios by design. Only a listener can say whether a line recalls a song (the needs-human step).

  M  Measured blocks. Every new item and every one of the 30 phrases in squillo's fixtures/slice/phrases/
     is sung by E-005's synthetic voice exactly as E-004 round 1 sang the library (run.py `_one`,
     lines 472-506: 6 voices x per-note spread sigma 0 and 20 cents x vibrato off and on (50 cents,
     5.5 Hz, from 0.15 s into each note) x one seed; a global offset within +-50 cents, a scoop on half
     the notes of 30-100 cents decaying in 60 ms, a 10 cent 1-6 Hz wander), with one change: the
     transposition keeps the sung notes between -25 and +10 semitones of A4 (round 1: -27 and
     min(12, base + 17), lines 482-485), so that every sample of the true contour, offsets included,
     lies within E2-C6 (ADR 0007), which is asserted on each rendering's true contour (S15) and stops
     the run if it fails. 39 items x 24 renderings = 936.
     Each rendering is tracked by E-002's yin (squillo SG), each frame accepted when it has a pitch and
     MT-003's u, the table squillo uses (E-002 fold2.json measures.spec.table, refused from the bin
     its table marks infinite), and its held notes and blocks are found by E-002 fold2.py `held_notes`
     and r2_analyse `block_measures`, the code MT-009 cites (`squillo-lab E-002 @ 51f3964`).
     Checks of the check, before any rendering: squillo's fixtures/metrics/held-steady.wav must give one
     held note, frames 3 to 624, and 3 blocks (MT-009's scenario); fixtures/signal/sine-220hz.wav must
     give none (its scenario); the bar below passes the first and fails the second.
     Bar B (per item): MT-009 gives at least 2 blocks on every one of its 24 renderings.
     Predictions, written before the run: B holds for all 9 new items; on the 30, B holds for
     le-pays-des-reves and abide-with-me (rule (2) gives 3 and 2) and fails for every phrase rule (2)
     gives 0 blocks; measured blocks differ from rule (2)'s count, both ways (repeated written pitches
     merge into one held note; transitions shorten one).
     Also recorded per item: rule (2)'s blocks, the measured blocks (min, median, max), and E-005's
     attribution of aimed notes (round 1's `found`, estimate and global chromatic), as round 1 did.

Crude, disposable lab code: never product code (squillo PLAN.md rule 11).
"""

import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from fractions import Fraction
from multiprocessing import Pool
from pathlib import Path

import numpy as np

import fold as F
import fold3 as F3

HERE = Path(__file__).parent
RES = HERE / "results" / "r4"
ITEMS_OUT = RES / "items"
CACHE = HERE / "data" / "cache" / "r4"
E002 = HERE.parent / "E-002-measurement-reliability"
E005 = HERE.parent / "E-005-intent-inference"

BLOCKS_MIN = F3.BLOCKS_MIN
HELD_MARGIN = F3.TRIM                       # W5: 62 frames
TWO_BLOCKS = 2 * F3.TRIM + 2 * F3.BLOCK     # 374: the least whole frames giving two blocks
LOW_SEMI, HIGH_SEMI = -25, 10               # M: transposition bounds, semitones re A4
E2_CENTS, C6_CENTS = -2900.0, 1500.0        # ADR 0007's range, cents re A4
POOL = 18
SEED0 = 2026100268

SOURCE = "Written for squillo in squillo iteration 68 (squillo-lab E-004 round 4), for held notes; words and melody new"

# W: the 9 originals. Notes as "pitch:quarters"; one syllable to a note.
ITEMS = [
    dict(id="held-ah", title="Held Ah", genre="vocalise", language="zxx", words="Ah",
         key="C", meter="4/4", tempo=52, notes="C4:1 E4:1 G4:4 E4:1 C4:4"),
    dict(id="slow-scale-ah", title="Slow Scale on Ah", genre="vocalise", language="zxx", words="Ah",
         key="C", meter="4/4", tempo=52, notes="C4:1/2 D4:1/2 E4:1/2 F4:1/2 G4:4 F4:1/2 E4:1/2 D4:1/2 C4:4"),
    dict(id="halfway-home", title="Halfway Home", genre="pop", language="en",
         words="We were halfway home when the night came down",
         key="G", meter="4/4", tempo=96, notes="B3:1/2 D4:1/2 E4:1/2 D4:1/2 G4:6 E4:1/2 D4:1/2 B3:1 A3:1/2 B3:6"),
    dict(id="engine-roar", title="Engine Roar", genre="rock", language="en",
         words="Turn the key and let the engine roar",
         key="Em", meter="4/4", tempo=100, notes="E4:1/2 E4:1/2 G4:1 E4:1/2 D4:1/2 E4:1/2 G4:1/2 A4:1/2 B4:8"),
    dict(id="late-train", title="Late Train", genre="jazz", language="en",
         words="Late train, slow rain, I'm counting every mile",
         key="Bb", meter="4/4", tempo=80, notes="F4:1 D4:1 G4:1 Eb4:1 F4:1/2 G4:1/2 A4:1/2 Bb4:1/2 C5:1/2 D5:6"),
    dict(id="dusty-road", title="Dusty Road", genre="blues", language="en",
         words="I been walking this old dusty road",
         key="C", meter="4/4", tempo=64, notes="C4:1/2 Eb4:1/2 F4:1 Gb4:1/2 F4:1/2 Eb4:1 C4:1/2 Bb3:1/2 C4:6"),
    dict(id="let-the-morning-wait", title="Let the Morning Wait", genre="soul", language="en",
         words="Let the morning wait for us",
         key="Eb", meter="4/4", tempo=66, notes="Eb4:1/2 F4:1/2 G4:1 Bb4:1 C5:4 Bb4:1/2 G4:4"),
    dict(id="fence-line-home", title="Fence Line Home", genre="country", language="en",
         words="Walking the fence line home",
         key="D", meter="4/4", tempo=80, notes="A3:1/2 D4:1/2 E4:1/2 F#4:1 A4:6 D4:6"),
    dict(id="when-the-curtain-falls", title="When the Curtain Falls", genre="musical-theatre", language="en",
         words="When the curtain falls I'll sing",
         key="F", meter="4/4", tempo=66, notes="C4:1/2 F4:1/2 G4:1 A4:1 C5:4 Bb4:1/2 A4:5"),
]


def item_of(d):
    return {"format_version": 3, "kind": "phrase", "phrase_id": d["id"], "title": d["title"],
            "instructions": F.instructions(d["genre"], "original"), "genre": d["genre"],
            "language": d["language"], "words": d["words"],
            "melody": {"key": d["key"], "meter": d["meter"], "tempo_qpm": d["tempo"],
                       "notes": [{"pitch": t.split(":")[0], "quarters": F.q(Fraction(t.split(":")[1]))}
                                 for t in d["notes"].split()]},
            "content": {"licence": F.ORIGINAL_LICENCE, "source": SOURCE, "origin": "original"}}


def within(c):  # fold.py lines 603-606, the same predicate
    lo, hi = F.midi(F.COND["low"]), F.midi(F.COND["high"])
    return (F.COND["notes"][0] <= c["notes"] <= F.COND["notes"][1] and c["range"] <= F.COND["range_max"]
            and c["seconds"] <= F.COND["seconds_max"] and c["shortest_s"] >= F.COND["shortest_min"]
            and lo <= c["low"] and c["high"] <= hi)


def note_frames(o):
    m = o["melody"]
    return [int(Fraction(n["quarters"]) * 60 / m["tempo_qpm"] * F3.FPS) for n in m["notes"]]


def intervals(o):
    p = [F.midi(n["pitch"]) for n in o["melody"]["notes"]]
    return [b - a for a, b in zip(p, p[1:])]


def longest_shared(a, b):
    best = 0
    for i in range(len(a)):
        for j in range(len(b)):
            k = 0
            while i + k < len(a) and j + k < len(b) and a[i + k] == b[j + k]:
                k += 1
            best = max(best, k)
    return best


def committed_first():
    """S15: refuse to run on an uncommitted edit of this file or of the modules whose rules it reads."""
    for me in (Path(__file__).name, "fold.py", "fold3.py"):
        a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
        b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", me], cwd=HERE)
        if a.returncode or b.returncode:
            sys.exit(f"{me} is not committed as it stands: commit the rules before running")


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------- W


def write(squillo):
    squillo = Path(squillo)
    rep = {}
    items = [item_of(d) for d in ITEMS]
    ITEMS_OUT.mkdir(parents=True, exist_ok=True)
    for old in ITEMS_OUT.glob("*.json"):
        old.unlink()
    for o in items:
        (ITEMS_OUT / f"{o['phrase_id']}.json").write_text(F.dump(o), encoding="utf-8")
    new = {f"r4/{p.name}": p.read_text(encoding="utf-8") for p in sorted(ITEMS_OUT.glob("*.json"))}
    sl = squillo / "fixtures" / "slice"
    slice_texts = {str(p.relative_to(squillo)): p.read_text(encoding="utf-8")
                   for p in sorted(sl.glob("*/*.json"))}
    rep["slice_files"] = len(slice_texts)

    # W1
    acc, ref = F.load_together({**slice_texts, **new})
    rep["W1"] = dict(files=len(slice_texts) + len(new), accepted=len(acc), refused={k: list(v) for k, v in ref.items()})
    first = next(iter(new))
    acc2, ref2 = F.load_together({**slice_texts, **new, "r4/copy.json": new[first]})
    rep["W1_must_fail"] = ref2 == {first: ("EX-004", "/phrase_id"), "r4/copy.json": ("EX-004", "/phrase_id")}

    # W2
    rep["W2"] = {o["phrase_id"]: F.build_rights(o) for o in items}
    bad = json.loads(json.dumps(items[0]))
    bad["content"]["licence"] = F.PD_LICENCE
    rep["W2_must_fail"] = F.build_rights(bad) == "/content/licence"

    # W3
    cond = {o["phrase_id"]: F.conditions(o) for o in items}
    rep["W3"] = {k: dict(c, within=within(c)) for k, c in cond.items()}
    slow = []
    for o in items:
        s = json.loads(json.dumps(o))
        s["melody"]["tempo_qpm"] = o["melody"]["tempo_qpm"] // 10
        slow.append(not within(F.conditions(s)))
    rep["W3_must_fail"] = all(slow)

    # W4, W5
    rep["W4_block_cases"] = {n: F3.blocks_of_frames(n) == want for n, want in F3.BLOCK_CASES.items()}
    w4, w4f, w5 = {}, [], {}
    for o in items:
        total, per = F3.phrase_blocks(o)
        fr = note_frames(o)
        w4[o["phrase_id"]] = dict(blocks=total, per_note=per, frames=fr,
                                  seconds=str(sum(Fraction(n["quarters"]) for n in o["melody"]["notes"])
                                              * 60 / o["melody"]["tempo_qpm"]))
        fast = json.loads(json.dumps(o))
        fast["melody"]["tempo_qpm"] = 3 * o["melody"]["tempo_qpm"]
        w4f.append(F3.phrase_blocks(fast)[0] < BLOCKS_MIN)
        w5[o["phrase_id"]] = [dict(frames=n, blocks=F3.blocks_of_frames(n),
                                   over_least=n - (2 * F3.TRIM + F3.BLOCK * F3.blocks_of_frames(n)))
                              for n in fr if n >= TWO_BLOCKS]
    rep["W4"] = w4
    rep["W4_must_fail"] = all(w4f)
    rep["W5"] = w5

    # W6: novelty screen, recorded, not asserted
    old = {}
    for p in sorted((sl / "phrases").glob("*.json")):
        o = json.loads(p.read_text(encoding="utf-8"))
        old[o["phrase_id"]] = intervals(o)
    w6 = {}
    for o in items:
        iv = intervals(o)
        vs_old = max(((longest_shared(iv, v), k) for k, v in old.items()))
        vs_new = max(((longest_shared(iv, intervals(x)), x["phrase_id"]) for x in items if x is not o))
        w6[o["phrase_id"]] = dict(intervals=len(iv), vs_30=dict(longest=vs_old[0], with_=vs_old[1]),
                                  vs_new=dict(longest=vs_new[0], with_=vs_new[1]))
    rep["W6_novelty_screen"] = w6
    rep["sha256"] = {k: sha(v.encode("utf-8")) for k, v in new.items()}

    # Every key naming a check is asserted (S15).
    assert all(rep["W4_block_cases"].values()), rep["W4_block_cases"]
    for k in ("W1_must_fail", "W2_must_fail", "W3_must_fail", "W4_must_fail"):
        assert rep[k] is True, (k, rep[k])
    assert not rep["W1"]["refused"] and rep["W1"]["accepted"] == rep["W1"]["files"] == len(slice_texts) + 9, rep["W1"]
    assert not any(rep["W2"].values()), rep["W2"]
    assert all(c["within"] for c in rep["W3"].values()), rep["W3"]
    assert all(v["blocks"] >= BLOCKS_MIN for v in w4.values()), w4
    assert all(h["over_least"] >= HELD_MARGIN for v in w5.values() for h in v), w5
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "write.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in rep.items() if k not in ("W3", "W4", "W5")}, indent=1, ensure_ascii=False, default=str))


# ---------------------------------------------------------------- M

_ctx = None


def ctx():
    global _ctx
    if _ctx is None:
        sys.path.insert(0, str(E005))
        sys.path.insert(0, str(E002))

        def load(name, path):
            spec = importlib.util.spec_from_file_location(name, path)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            return m
        e5run = load("e005_run", E005 / "run.py")
        e5rep = load("e005_report", E005 / "report.py")
        import synth as e5syn
        import yin
        argv, sys.argv = sys.argv, sys.argv[:1]   # fold2 reads sys.argv[1] at import as an output folder
        fold2 = load("e002_fold2", E002 / "fold2.py")
        sys.argv = argv
        A = fold2.A
        table = np.array([np.inf if x is None else x for x in
                          json.load(open(E002 / "results" / "fold2.json"))["measures"]["spec"]["table"]])
        _ctx = dict(e5run=e5run, e5rep=e5rep, e5syn=e5syn, voice=e5syn.voice, yin=yin, fold2=fold2, A=A,
                    table=table)
    return _ctx


def held_blocks(x):
    """MT-009 on a signal: (held notes as (first, last) frame, blocks per held note)."""
    c = ctx()
    yin, A, fold2 = c["yin"], c["A"], c["fold2"]
    idx, f, dip = yin.yin(x)
    f = yin.in_range(f, 3.0)
    u = np.where(np.isnan(f), np.inf, A.u_of(np.nan_to_num(dip, nan=1.0), c["table"]))
    p = fold2.cents(f)
    notes = fold2.held_notes(p, u)
    return [(int(idx[fr[0]]), int(idx[fr[-1]])) for fr, _, _ in notes], [len(A.block_measures(con)) for _, con, _ in notes]


def check_finder(squillo):
    import soundfile as sf
    squillo = Path(squillo)
    out = {}
    x, sr = sf.read(squillo / "fixtures" / "metrics" / "held-steady.wav", dtype="float64")
    assert sr == 48000
    h, b = held_blocks(x)
    out["steady"] = dict(held=h, blocks=b)
    x, sr = sf.read(squillo / "fixtures" / "signal" / "sine-220hz.wav", dtype="float64")
    h2, b2 = held_blocks(x)
    out["sine_1s"] = dict(held=h2, blocks=b2)
    out["finder_must_pass"] = h == [(3, 624)] and b == [3]
    out["finder_must_fail"] = h2 == [] and b2 == []
    out["bar_must_pass"] = sum(b) >= BLOCKS_MIN
    out["bar_must_fail"] = not sum(b2) >= BLOCKS_MIN
    for k in ("finder_must_pass", "finder_must_fail", "bar_must_pass", "bar_must_fail"):
        assert out[k] is True, (k, out)
    return out


def jobs(squillo):
    squillo = Path(squillo)
    its = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(ITEMS_OUT.glob("*.json"))]
    its += [json.loads(p.read_text(encoding="utf-8")) for p in sorted((squillo / "fixtures" / "slice" / "phrases").glob("*.json"))]
    assert len(its) == 39, len(its)
    out, seed = [], SEED0
    voices = ctx()["e5run"].VOICES
    for o in its:
        for v in voices:
            for sigma in (0, 20):
                for vib in (0, 1):
                    seed += 1
                    out.append((o["phrase_id"], o["melody"], v, sigma, vib, seed))
    return out


def one(job):
    c = ctx()
    e5run, e5rep, e5syn, voice = c["e5run"], c["e5rep"], c["e5syn"], c["voice"]
    from scipy.signal import butter, sosfiltfilt
    pid, mel, v, sigma, vib, seed = job
    t0 = time.time()
    sex, base = voice.VOICES[v]
    rng = np.random.default_rng(seed)
    semis = np.array([F.midi(n["pitch"]) - 69 for n in mel["notes"]], float)
    semis += np.round(base + 5 - semis.mean())
    while semis.max() > HIGH_SEMI:
        semis -= 12
    while semis.min() < LOW_SEMI:
        semis += 12
    assert semis.max() <= HIGH_SEMI, (pid, v, semis)   # a range over 35 semitones would fail here
    durs = np.array([float(Fraction(n["quarters"])) for n in mel["notes"]]) * 60.0 / mel["tempo_qpm"]
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
    lo, hi = float(sung.min()), float(sung.max())
    assert E2_CENTS <= lo and hi <= C6_CENTS, (pid, v, sigma, vib, lo, hi)   # S15: on the output, stops the run
    amp = np.ones(n)
    amp[t < 0.1] = 0
    amp[t > T - 0.1] = 0
    amp = np.convolve(amp, np.ones(960) / 960, mode="same")
    x = voice.render(dict(sex=sex, n=n, amp=amp, noise_seed=seed + 1000), sung).astype(np.float32)
    held, blocks = held_blocks(x.astype(np.float64))
    tt, cents, dmin = e5run.track(x)
    nof, mid = e5run.note_frames(tt, starts, durs)
    r = e5run.evaluate(tt, cents, nof, mid, e5run.oracle_from(nof))
    calls, ok, _ = e5rep.attribution(dict(res=r, nof=nof, mid=mid), ("est", "global", "chromatic"), semis.astype(int))
    return dict(id=pid, voice=v, sigma=sigma, vib=vib, seed=seed, cents_min=lo, cents_max=hi,
                held=held, blocks=blocks, total_blocks=int(sum(blocks)), notes=len(semis), found=int(ok.sum()),
                seconds=time.time() - t0)


def run_all(js):
    CACHE.mkdir(parents=True, exist_ok=True)
    todo = [j for j in js if not (CACHE / f"{j[5]}.json").exists()]
    print(len(js) - len(todo), "cached,", len(todo), "to run", flush=True)
    t0 = time.time()
    with Pool(POOL) as p:
        for k, r in enumerate(p.imap_unordered(one, todo, chunksize=1), 1):
            (CACHE / f"{r['seed']}.json").write_text(json.dumps(r) + "\n")
            if k % 50 == 0:
                print(k, "done", round(time.time() - t0), "s", flush=True)
    return time.time() - t0


def sample(squillo):
    """S19: the longest and shortest items, every voice extreme, vibrato and spread on and off."""
    js = jobs(squillo)
    secs = {}
    for o in [json.loads(p.read_text(encoding="utf-8")) for p in ITEMS_OUT.glob("*.json")] + \
             [json.loads(p.read_text(encoding="utf-8")) for p in (Path(squillo) / "fixtures/slice/phrases").glob("*.json")]:
        secs[o["phrase_id"]] = F.conditions(o)["seconds"]
    longest, shortest = max(secs, key=secs.get), min(secs, key=secs.get)
    pick = [j for j in js if j[0] in (longest, shortest, "held-ah", "ode-to-joy") and j[2] in ("bass", "soprano_high")]
    t0 = time.time()
    with Pool(POOL) as p:
        res = p.map(one, pick, chunksize=1)
    wall = time.time() - t0
    total_audio = sum(secs[j[0]] + 0.2 for j in js)
    sample_audio = sum(secs[j[0]] + 0.2 for j in pick)
    est = wall * total_audio / sample_audio
    out = dict(items=sorted({j[0] for j in pick}), renderings=len(pick), wall_s=wall, sample_audio_s=sample_audio,
               total_audio_s=total_audio, estimate_s=est, per_rendering_s=[r["seconds"] for r in res])
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "sample.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


def analyse(squillo):
    squillo = Path(squillo)
    rep = dict(finder=check_finder(squillo))
    js = jobs(squillo)
    rows = [json.loads((CACHE / f"{j[5]}.json").read_text()) for j in js]
    assert len(rows) == 936 and all(r["seed"] == j[5] for r, j in zip(rows, js))
    written = {}
    for p in list(ITEMS_OUT.glob("*.json")) + list((squillo / "fixtures/slice/phrases").glob("*.json")):
        o = json.loads(p.read_text(encoding="utf-8"))
        written[o["phrase_id"]] = F3.phrase_blocks(o)[0]
    new = [d["id"] for d in ITEMS]
    per = {}
    for pid in sorted(written):
        rs = [r for r in rows if r["id"] == pid]
        b = np.array([r["total_blocks"] for r in rs])
        per[pid] = dict(new=pid in new, rule2=written[pid], renderings=len(rs),
                        measured=dict(min=int(b.min()), median=float(np.median(b)), max=int(b.max())),
                        bar_B=bool((b >= BLOCKS_MIN).all()), renderings_two_blocks=int((b >= BLOCKS_MIN).sum()),
                        diff_vs_rule2=dict(min=int((b - written[pid]).min()), max=int((b - written[pid]).max())),
                        by_vib={str(v): int(min(r["total_blocks"] for r in rs if r["vib"] == v)) for v in (0, 1)},
                        found=sum(r["found"] for r in rs), notes=sum(r["notes"] for r in rs))
    rep["per_item"] = per
    rep["cents_range"] = dict(min=min(r["cents_min"] for r in rows), max=max(r["cents_max"] for r in rows))
    rep["summary"] = dict(
        new_bar_B=sum(per[k]["bar_B"] for k in new), new_items=len(new),
        new_measured_min=min(per[k]["measured"]["min"] for k in new),
        slice_bar_B=sorted(k for k in per if not per[k]["new"] and per[k]["bar_B"]),
        slice_rule2_two=sorted(k for k in per if not per[k]["new"] and per[k]["rule2"] >= BLOCKS_MIN),
        slice_any_two=sorted(k for k in per if not per[k]["new"] and per[k]["renderings_two_blocks"] > 0),
        rule2_zero_measured_max=max((per[k]["measured"]["max"] for k in per if per[k]["rule2"] == 0), default=None),
        found_new=[sum(per[k]["found"] for k in new), sum(per[k]["notes"] for k in new)],
        found_slice=[sum(per[k]["found"] for k in per if not per[k]["new"]),
                     sum(per[k]["notes"] for k in per if not per[k]["new"])],
        compute_s=sum(r["seconds"] for r in rows))
    p = rep["summary"]
    rep["predictions"] = dict(
        all_new_pass_B=p["new_bar_B"] == len(new),
        slice_B_is_rule2_two=set(p["slice_bar_B"]) == {"le-pays-des-reves", "abide-with-me"},
        rule2_zero_all_fail_B=all(not per[k]["bar_B"] for k in per if per[k]["rule2"] == 0),
        differs_both_ways=any(v["diff_vs_rule2"]["min"] < 0 for v in per.values()) and
        any(v["diff_vs_rule2"]["max"] > 0 for v in per.values()))
    (RES / "held.json").write_text(json.dumps(rep, indent=1) + "\n")
    print(json.dumps({k: v for k, v in rep.items() if k != "per_item"}, indent=1))
    for k, v in per.items():
        print(f"{k:28s} new={v['new']!s:5s} rule2={v['rule2']} measured={v['measured']} B={v['bar_B']} "
              f"found={v['found']}/{v['notes']}")


if __name__ == "__main__":
    committed_first()
    cmd = sys.argv[1]
    sq = sys.argv[2] if len(sys.argv) > 2 else str(HERE.parents[2] / "squillo")
    if cmd == "write":
        write(sq)
    elif cmd == "sample":
        ctx(); print(json.dumps(check_finder(sq))); sample(sq)
    elif cmd == "run":
        ctx(); check_finder(sq); print("wall", round(run_all(jobs(sq))), "s")
    elif cmd == "analyse":
        analyse(sq)
