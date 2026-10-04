"""E-005 round 1: run intent inference on synthetic and VocalSet takes.

    uv run python run.py synth    # 600 synthetic phrases -> data/cache/synth.pkl
    uv run python run.py real     # VocalSet takes         -> data/cache/real.pkl
    E005_LOWPASS=4000 uv run python run.py real   # S15 check -> real_lp.pkl
    uv run python report.py       # -> results/summary.json
    uv run python run.py own a.wav b.wav   # needs-human: -> results/own.json

Crude experiment code. Pitch: E-002's YIN (squillo-lab E-002 @ afff13f,
yin.py) at squillo's frame axis (ADR 0007), threshold 0.1, E2-C6 widened by
3 cents; a frame's instant is 20 ms before its end, YIN's lag centre
(E-002 result 5: 17.9 ms at E2 to 23.5 ms at C6).
"""

import itertools
import os
import pickle
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, resample_poly, sosfiltfilt

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "E-002-measurement-reliability"))
import yin  # noqa: E402
import infer  # noqa: E402

CACHE = HERE / "data" / "cache"
LOWPASS = float(os.environ.get("E005_LOWPASS", 0))  # Hz; 0 = off
SR = 48_000
HOP = 384
LAG_S = 0.020
REFS = ("fixed", "global", "local")
SNAPS = ("chromatic", "key", "hybrid")
VOICES = ("bass", "baritone", "tenor", "mezzo", "soprano", "soprano_high")
SCALE_NAMES = ("major", "minor", "harmonic_minor", "pentatonic", "blue")
SIGMAS = (0, 10, 20, 30, 40)

# VocalSet scores (DataSetVocalises.pdf in the VocalSet zip), semitones re the
# first note. Scales: C major up to the ninth and down. The score goes on in
# F major, but every take holds the C-major bar only (5.9-12.9 s).
# Row: the traditional round "Row, row, row your boat" (19th century, public
# domain), notes only.
# the round's words per merged note of SCORES["row"] (repeats merged, as one_real does)
ROW_WORDS = ["Row, row, row", "your", "boat, gent-", "-ly", "down", "the", "stream",
             "merrily (high)", "merrily", "merrily", "merrily (low)", "life", "is", "but", "a", "dream"]
SCORES = {
    "scales": [0, 2, 4, 5, 7, 9, 11, 12, 14, 12, 11, 9, 7, 5, 4, 2, 0],
    "row": [0, 0, 0, 2, 4, 4, 2, 4, 5, 7, 12, 12, 12, 7, 7, 7, 4, 4, 4, 0, 0, 0,
            7, 5, 4, 2, 0],
}


def track(x):
    idx, f0, dmin = yin.yin(x)
    f0 = yin.in_range(f0, 3.0)
    cents = 1200 * np.log2(f0 / 440.0)
    t = HOP * (idx + 1) / SR - LAG_S
    return t, cents, dmin


def evaluate(t, cents, note_of_frame, mid_frame, oracle_segs):
    """Run every method with estimated and oracle segmentation.

    note_of_frame: true note index per frame (-1 outside notes).
    mid_frame: bool, frame lies in its note's settle window (by truth).
    Returns {(seg, ref, snap): dict(frame_target, seg_of_frame, out)}.
    """
    res = {}
    est = infer.segment(cents)
    for segname, segs in (("est", est), ("oracle", oracle_segs)):
        segs = [s for s in segs if np.sum(~np.isnan(cents[s[0]:s[1]])) > 0]
        seg_of_frame = np.full(len(cents), -1)
        for k, (a, b) in enumerate(segs):
            seg_of_frame[a:b] = k
        for ref, snap in itertools.product(REFS, SNAPS):
            out = infer.infer(cents, segs, ref, snap)
            res[(segname, ref, snap)] = dict(seg_of_frame=seg_of_frame, out=out)
    return res


def note_frames(t, starts, durs):
    nof = np.full(len(t), -1)
    mid = np.zeros(len(t), bool)
    for k, (s, d) in enumerate(zip(starts, durs)):
        m = (t >= s) & (t < s + d)
        nof[m] = k
        mid |= (t >= s + 0.3 * d) & (t < s + 0.9 * d)
    return nof, mid


def oracle_from(nof):
    segs, i, n = [], 0, len(nof)
    while i < n:
        if nof[i] < 0:
            i += 1
            continue
        j = i
        while j < n and nof[j] == nof[i]:
            j += 1
        segs.append((i, j))
        i = j
    return segs


def one_synth(args):
    import synth
    voice, scale, sigma, drift, vib, seed = args
    x, truth = synth.phrase(voice, scale, sigma, drift, vib, seed)
    t, cents, dmin = track(x)
    nof, mid = note_frames(t, truth["starts"], truth["durs"])
    res = evaluate(t, cents, nof, mid, oracle_from(nof))
    # true drift at each note's settle-window centre
    tc = truth["starts"] + 0.6 * truth["durs"]
    D = truth["drift"] * (tc / truth["T"] - 0.5)
    return dict(cond=dict(voice=voice, scale=scale, sigma=sigma, drift=drift, vib=vib, seed=seed),
                truth=truth, D=D, nof=nof, mid=mid, t=t, voiced=float(np.mean(~np.isnan(cents))),
                dmin=dmin, res=res)


def run_synth():
    jobs = []
    seed = 20260926
    for scale, sigma, drift, vib in itertools.product(SCALE_NAMES, SIGMAS, (0, 60), (0, 1)):
        for v in VOICES:
            seed += 1
            jobs.append((v, scale, sigma, drift, vib, seed))
    with Pool(18) as p:
        out = p.map(one_synth, jobs, chunksize=4)
    pickle.dump(out, open(CACHE / "synth.pkl", "wb"))
    print(len(out), "phrases")


def dtw(x, p):
    """Monotone alignment of voiced frames x to score states p (both cents)."""
    J = len(p)
    best = None
    for T in np.arange(-3600, 1801, 25.0):
        c = np.minimum(np.abs(x[:, None] - p[None, :] - T), 300.0)
        D = np.full(J, np.inf)
        D[0] = c[0, 0]
        for i in range(1, len(x)):
            stay = D
            move = np.concatenate([[np.inf], D[:-1]])
            D = c[i] + np.minimum(stay, move)
        if best is None or D[-1] < best[0]:
            best = (D[-1], T)
    T = best[1]
    c = np.minimum(np.abs(x[:, None] - p[None, :] - T), 300.0)
    D = np.full((len(x), J), np.inf)
    D[0, 0] = c[0, 0]
    back = np.zeros((len(x), J), np.int8)
    for i in range(1, len(x)):
        move = np.concatenate([[np.inf], D[i - 1, :-1]])
        back[i] = move < D[i - 1]
        D[i] = c[i] + np.minimum(D[i - 1], move)
    path = np.zeros(len(x), int)
    j = J - 1
    for i in range(len(x) - 1, -1, -1):
        path[i] = j
        if i > 0 and back[i, j]:
            j -= 1
    return path, T, float(np.mean(c[np.arange(len(x)), path] > 100))


def one_real(path):
    name = path.stem
    kind = "scales" if "_scales_" in name else "row"
    style = "vibrato" if "vibrato" in name else "straight"
    x, sr = sf.read(path, dtype="float64")
    if x.ndim > 1:
        x = x.mean(axis=1)
    if sr != SR:
        g = np.gcd(SR, sr)
        x = resample_poly(x, SR // g, sr // g)
    if LOWPASS:
        # S15 check: remove the band where synthetic and real spectra differ
        x = sosfiltfilt(butter(8, LOWPASS, fs=SR, output="sos"), x)
    t, cents, dmin = track(x.astype(np.float32))
    score = np.array(SCORES[kind])
    # merge repeated notes: a repeat has the same target, and DTW cannot place
    # the boundary between them
    keep = np.concatenate([[True], np.diff(score) != 0])
    states = score[keep]
    v = np.flatnonzero(~np.isnan(cents))
    # ignore short voiced islands before the first and after the last note
    # align a 200 ms running median: vibrato of +-100 cents would otherwise
    # read as misalignment
    pth, T, bad = dtw(infer.running_median(cents[v], 25), 100.0 * states)
    nof = np.full(len(cents), -1)
    nof[v] = pth
    # fill unvoiced frames inside a state's run
    mid = np.zeros(len(cents), bool)
    for j in range(len(states)):
        fr = v[pth == j]
        if len(fr) == 0:
            continue
        a, b = fr.min(), fr.max() + 1
        nof[a:b][nof[a:b] < 0] = j
        L = b - a
        mid[a + int(0.25 * L):a + int(0.75 * L)] = True
    mid &= nof >= 0
    res = evaluate(t, cents, nof, mid, oracle_from(nof))
    return dict(name=name, kind=kind, style=style, states=states, T=T, dtw_bad=bad,
                nof=nof, mid=mid, t=t, voiced=float(np.mean(~np.isnan(cents))),
                dmin=dmin, res=res)


def run_real():
    files = sorted(CACHE.glob("*.wav"))
    with Pool(18) as p:
        out = p.map(one_real, files)
    pickle.dump(out, open(CACHE / ("real_lp.pkl" if LOWPASS else "real.pkl"), "wb"))
    print(len(out), "takes")


def run_own(paths):
    """needs-human step: the singer's own takes of the traditional round
    (score SCORES['row']). Writes numbers only, never audio."""
    import importlib.util
    import json
    spec = importlib.util.spec_from_file_location("e005_report", HERE / "report.py")
    report = importlib.util.module_from_spec(spec)  # not E-002's report.py
    spec.loader.exec_module(report)
    items = [one_real(Path(p)) for p in paths]
    out = {}
    for it in items:
        key = ("est", "global", "chromatic")
        calls, ok, modal = report.attribution(it, key, it["states"])
        o = it["res"][key]["out"]
        keep = o["dur"] >= report.TRANS_S
        sh = infer.circ_sigma(o["dev"][keep], o["dur"][keep])
        pp = infer.p_attrib(o["dev"], sh)
        flagged = [bool(pp[c[1]] < 0.95) for c in calls if c[1] is not None]
        # per sung word, for the ear check: its span in the take (to play it), and
        # whether intent inference marks it: a different note than the round's,
        # attribution below 95 % (flagged), or no note found
        words = []
        for j, (c, right) in enumerate(zip(calls, ok)):
            fr = np.flatnonzero(it["nof"] == j)
            w = dict(words=ROW_WORDS[j], start_s=round(float(it["t"][fr[0]]), 2) if len(fr) else None,
                     end_s=round(float(it["t"][fr[-1]]), 2) if len(fr) else None)
            if c[1] is None:
                w.update(measured="no note found", marked=True)
            else:
                dev = float(o["dev"][c[1]])
                w.update(dev_cents=round(dev, 1), attributed_right=bool(right), flagged=bool(pp[c[1]] < 0.95),
                         measured="a different note" if not right else
                         "unsure which note" if pp[c[1]] < 0.95 else "fine")
                w["marked"] = not right or w["flagged"]
            words.append(w)
        out[Path(it["name"]).name] = dict(per_word=words,
            notes=len(ok), attributed_right=int(ok.sum()), circ_sigma=None if not np.isfinite(sh) else round(float(sh), 1),
            flagged=int(sum(flagged)), dtw_bad_pct=round(100 * it["dtw_bad"], 1),
            abs_dev_median=round(float(np.median(np.abs(o["dev"][keep]))), 1) if keep.any() else None)
    json.dump(out, open(HERE / "results" / "own.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    if sys.argv[1] == "own":
        run_own(sys.argv[2:])
    else:
        {"synth": run_synth, "real": run_real}[sys.argv[1]]()
