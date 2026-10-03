"""E-002 round 6 (squillo iteration 88, F-075): a fixture that tells MT-009's trimmed pieces from the
untrimmed ones. Crude experiment code.

    uv run python r6_fixture.py <squillo>      # -> results/r6/two-notes-gap.wav, results/r6_fixture.json

Question (squillo F-075). Since squillo iteration 79, MT-009 trims each piece the 60-cent cut forms to its
first and last measured cells. Round 5's T3 found that no squillo fixture gives different held notes under
the trimmed rule and the old (untrimmed) one, so an implementer who keeps the old rule passes every MT-009
scenario. Is there a short generated audio fixture, round 5's constructed case P made into samples, on
which the trimmed rule gives two held notes and the untrimmed rule fewer, with the outcome robust to the
tracker's arithmetic?

The fixture, written before any run (C1). Mono, 48 kHz, IEEE float 32-bit, by fold2.wav (the writer of
squillo's other metrics fixtures):
    x[n] = 0.5 sin(2 pi 220 n / 48000)                    for 0 <= n < NA
    x[n] = 0                                              for NA <= n < NA + G
    x[n] = 0.5 sin(2 pi FB (n - NA - G) / 48000)          for NA + G <= n < NA + G + NB
  with NA = NB = 124 800 samples (2.6 s), FB = 220 * 2^(2/12) Hz (B3, 200 cents above A3) and G = 384 m
  samples of silence, m chosen by the selection rule below. Why these: two steady tones a whole tone
  apart are round 5's case P (0 and +200 cents); silence is the simplest input `signal` gives no pitch
  (SG-006), so no cell across the step is measured; 2.6 s puts each tone's held note (2 s at least, 250
  frames) at about 320 frames, which gives one block (MT-009: less 62 frames at each end, blocks of 125)
  with more than 50 frames' margin either way (a held note gives one block from 249 to 373 frames), so
  that a take of two held notes has the two blocks MT-010 needs, and a take of one has one.

Conditions, asserted on the file as written and read back (C1, C3):
  K1 Both tones inside E2..C6 (yin.E2, yin.C6, squillo ADR 0007), peak at most 1 (computed from x).
  K2 Every frame from 3 whose pitch window (yin.frame_windows: the 1536 samples ending with the frame)
     holds samples of one tone only is measured (finite u under squillo's MT-003 table, fold2.json
     measures.spec.table, as fold3_ladder.fixture_row reads a fixture).
  K3 The frames not measured from 3 on form exactly one stretch, of at most 12 frames (MT-009: a run
     continues across at most 12 cells not measured; fold2.MAX_GAP), so the take is one run.
  K4 Across the step, the cut that begins the piece holding the second tone (the last cut) falls on a
     frame not measured, and so do the frames either side of it (a margin of a frame each way), read
     with r5_trim.cuts, whose rule round 5 asserted (revision 1).
  Selection rule: m is the least of 1 .. 16 for which K1 to K4 hold on the float64 tracking; none means
  the round's answer is no, and the script stops saying so.

Expected outcome, the round's hypothesis H (a prediction, checked, not a selection): under the trimmed
finder (r5_trim.finder trim=True, MT-009 as squillo states it) the fixture gives exactly two held notes,
one on each tone, each giving exactly one block, so `steadiness` (MT-010: two blocks at least) is
measured; under the untrimmed finder (fold2.held_notes, trim=False) exactly one, on the first tone, one
block, so `steadiness` is unmeasurable. K4 is why the second tone is lost untrimmed: its piece begins on
a cell not measured. Recorded: every held note's frames, every block's frames (fold2.blocks' b0, b1),
the take values and u for steadiness, vibrato extent and rate under each finder (fold3_ladder.measure),
the cells not measured, and the 2 Hz contour's least distance from the 60-cent threshold over the cuts'
frames (how far an arithmetic difference must move the contour to move a cut).

Robustness, ADR 0007's numeric epsilon (an implementation's arithmetic): R1 the tracking redone in
float32 (yin.yin dtype=np.float32) gives every cell the same state and both finders the same held notes
(first and last frames, measured cells) and blocks as float64.

Checks of the checks (C10, C11): each check is run on the fixture (must pass) and on an input that differs
in what the check reads (must fail), all before H's outcome is computed:
  K3: must fail on the same formula with m = 20 (a stretch of more than 12; the term moved is G, which
      sets the stretch's length).
  K4 and the finders' difference: must fail on Q, the same tones with the same G of silence moved from
     the step to 100 frames (38 400 samples) inside the second tone, the step itself clean (round 5's Q:
     the cut falls on a measured frame, so trimming recovers nothing).
  R1: must fail when the float32 states of Q are compared with the float64 states of the fixture (the
      input differs).
  The finder identities round 5 asserted (trim=False equals fold2.held_notes; every untrimmed held note
  is a trimmed one) are asserted again here on each input, by r5_trim.both.

Revision 1, before the second run: the first stopped writing results/r6_fixture.json on a numpy bool,
after every assertion had passed and before anything was printed; `plain` serialises numpy scalars. No
rule changed.

Crude, disposable lab code: never product code (squillo PLAN.md rule 11).
"""
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
GUARDED = ("r6_fixture.py", "r5_trim.py", "fold2.py", "fold3_ladder.py", "r2_analyse.py", "yin.py")


def committed_first():
    """S15 (C15): refuse to run on an uncommitted edit of this file or of the modules whose rules it runs."""
    for me in GUARDED:
        a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
        b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", me], cwd=HERE)
        if a.returncode or b.returncode:
            sys.exit(f"{me} is not committed as it stands: commit the rules before running")


if __name__ == "__main__":
    committed_first()
    SQ = Path(sys.argv[1])
    sys.argv = sys.argv[:1] + [str(SQ)]   # fold3_ladder reads sys.argv[1] at import as squillo's path

import r5_trim as T          # noqa: E402
import yin                   # noqa: E402

F2, L = T.F2, T.L
SR, HOP, WIN = yin.SR, yin.HOP, yin.WIN
NA = NB = 124_800
FA = 220.0
FB = 220.0 * 2 ** (2 / 12)
AMP = 0.5
M_RANGE = range(1, 17)
M_FAIL = 20
Q_INTO = 100 * HOP   # Q: the silence moved 100 frames into the second tone
OUT_WAV = HERE / "results" / "r6" / "two-notes-gap.wav"
OUT = HERE / "results" / "r6_fixture.json"


def samples(m, where="step"):
    G = HOP * m
    a = AMP * np.sin(2 * np.pi * FA * np.arange(NA) / SR)
    b = AMP * np.sin(2 * np.pi * FB * np.arange(NB) / SR)
    if where == "step":
        return np.concatenate([a, np.zeros(G), b]), (NA, NA + G)
    # Q: the step clean, the same silence inside the second tone, which resumes in phase after it
    k = Q_INTO
    b2 = AMP * np.sin(2 * np.pi * FB * np.arange(k + G, NB + G) / SR)
    return np.concatenate([a, b[:k], np.zeros(G), b2]), (NA + k, NA + k + G)


def as_file(x):
    """Write by fold2.wav and read back as the file holds it (float32)."""
    raw = F2.wav([float(v) for v in x])
    k = raw.index(b"data") + 8
    return raw, np.frombuffer(raw[k:], "<f4").astype(np.float64)


def track(x, dtype=np.float64):
    """fold3_ladder.fixture_row, with the tracker's dtype as a parameter (R1)."""
    idx, f, dip = yin.yin(x, dtype=dtype)
    f = yin.in_range(f, 3.0)
    u = np.where(np.isnan(f), np.inf, T.A.u_of(np.nan_to_num(dip, nan=1.0), T.TABLE))
    return idx, F2.cents(f), u


def frames_of_one_tone(idx, gap, n):
    """Frames whose pitch window holds no sample of the silence and lies inside the signal."""
    st = HOP * (idx - 3)
    return (st + WIN <= gap[0]) | (st >= gap[1]) & (st + WIN <= n)


def stretches(bad):
    d = np.diff(np.concatenate([[0], bad.astype(int), [0]]))
    return list(zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]))


def k_checks(x, gap, idx, p, u):
    """K1 to K4 on one input; frame numbers are squillo's (idx: 3, 4, ...), arrays from frame 3."""
    A_ok = yin.E2 <= FA <= yin.C6 and yin.E2 <= FB <= yin.C6 and float(np.max(np.abs(x))) <= 1.0
    meas = np.isfinite(u)
    one = frames_of_one_tone(idx, gap, len(x))
    K2 = bool(np.all(meas[one]))
    st = stretches(~meas)
    K3 = len(st) == 1 and st[0][1] - st[0][0] <= F2.MAX_GAP
    c = T.cuts(p, u)
    K4 = bool(len(c) and 0 < c[-1] < len(u) - 1 and not meas[c[-1] - 1:c[-1] + 2].any())
    return dict(K1=A_ok, K2=K2, K3=K3, K4=K4, unmeasured=[[int(idx[a]), int(idx[b - 1])] for a, b in st],
                cuts=[int(idx[k]) for k in c])


def notes_of(p, u, idx, trim):
    F2.held_notes = T.trimmed if trim else T.CURRENT
    try:
        notes, bl, tk = L.measure(p, u)
        out = []
        for fr, con, acc in notes:
            out.append(dict(frames=[int(idx[fr[0]]), int(idx[fr[-1]])],
                            blocks=[[int(idx[fr[b["b0"]]]), int(idx[fr[b["b0"] + F2.BLOCK - 1]])] for b in T.A.block_measures(con)]))
        allb = []
        for fr, con, acc in notes:
            allb += F2.blocks(con, u[fr], acc, L.C, True)
        takes = {m: F2.take(allb, m, L.KAPPA[m]) for m in ("S", "E", "R")}
    finally:
        F2.held_notes = T.CURRENT
    return out, {m: (None if v is None else [float(v[0]), float(v[1]), int(v[2])]) for m, v in takes.items()}


def margin(p, u):
    """The 2 Hz contour's least distance, in cents, from the 60-cent threshold over each piece's frames
    up to and including the frame where it is cut."""
    a = ~np.isnan(p) & np.isfinite(u)
    x = np.arange(len(p))
    lp = F2.filtfilt(*F2.B2, np.interp(x, x[a], p[a]))
    best, s0 = np.inf, 0
    while s0 < len(p):
        ref = np.median(lp[s0:s0 + 31])
        s1 = s0 + 1
        while s1 < len(p) and abs(lp[s1] - ref) <= F2.SPLIT:
            s1 += 1
        seg = lp[s0:min(s1 + 1, len(p))]
        best = min(best, float(np.min(np.abs(np.abs(seg - ref) - F2.SPLIT))))
        s0 = s1
    return best


def same(a, b):
    return T.same_notes(a, b)


def keys(notes):
    """A finder's held notes by their frames and accepted masks only (R1 compares two trackings, whose
    contour values differ in the last bits)."""
    return [(int(f[0]), int(f[-1]), tuple(map(bool, acc))) for f, _, acc in notes]


def plain(o):
    """Revision 1: numpy scalars to JSON (the first run stopped writing the results, every assertion passed,
    no outcome printed)."""
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    raise TypeError(type(o))


def main():
    rep = dict(rules="see the docstring", fixture=dict(NA=NA, NB=NB, FA=FA, FB=FB, amp=AMP, sr=SR))
    # selection: the least m for which K1..K4 hold on float64
    tried, chosen = {}, None
    for m in M_RANGE:
        x0, gap = samples(m)
        raw, x = as_file(x0)
        idx, p, u = track(x)
        k = k_checks(x, gap, idx, p, u)
        tried[m] = {kk: k[kk] for kk in ("K1", "K2", "K3", "K4")}
        if all(tried[m].values()):
            chosen = m
            break
    rep["selection"] = dict(tried=tried, m=chosen)
    if chosen is None:
        OUT.write_text(json.dumps(rep, indent=1, default=plain) + "\n")
        sys.exit("no m in 1..16 meets K1 to K4: the round's answer is no")
    m = chosen
    x0, gap = samples(m)
    raw, x = as_file(x0)
    idx, p, u = track(x)
    K = k_checks(x, gap, idx, p, u)
    assert K["K1"] and K["K2"] and K["K3"] and K["K4"]
    # checks of the checks, before H's outcome
    xf, gf = samples(M_FAIL)
    _, xf = as_file(xf)
    i_f, p_f, u_f = track(xf)
    Kf = k_checks(xf, gf, i_f, p_f, u_f)
    xq, gq = samples(m, "Q")
    _, xq = as_file(xq)
    i_q, p_q, u_q = track(xq)
    Kq = k_checks(xq, gq, i_q, p_q, u_q)
    cur, tr = T.both(p, u)
    cq, tq = T.both(p_q, u_q)
    T.both(p_f, u_f)
    _, p32, u32 = track(x, np.float32)
    _, pq32, uq32 = track(xq, np.float32)
    c32, t32 = T.both(p32, u32)
    chk = dict(
        K3_must_pass=K["K3"], K3_must_fail_m20=Kf["K3"],
        K4_must_pass=K["K4"], K4_must_fail_Q=Kq["K4"],
        differ_must_pass=not same(cur, tr), differ_must_fail_Q=not same(cq, tq),
        R1_must_pass=bool(np.array_equal(np.isfinite(u), np.isfinite(u32)) and keys(cur) == keys(c32) and keys(tr) == keys(t32)),
        R1_must_fail_Q=bool(np.array_equal(np.isfinite(u), np.isfinite(uq32))),
    )
    assert chk["K3_must_pass"] and not chk["K3_must_fail_m20"]
    assert chk["K4_must_pass"] and not chk["K4_must_fail_Q"]
    assert chk["differ_must_pass"] and not chk["differ_must_fail_Q"]
    assert chk["R1_must_pass"] and not chk["R1_must_fail_Q"]
    rep["checks"] = chk
    rep["K"] = K
    rep["K_m20"] = Kf
    rep["K_Q"] = Kq
    # the outcome
    n_tr, t_tr = notes_of(p, u, idx, True)
    n_cu, t_cu = notes_of(p, u, idx, False)
    n_q_tr, _ = notes_of(p_q, u_q, i_q, True)
    n_q_cu, _ = notes_of(p_q, u_q, i_q, False)
    H = dict(trimmed_two_notes=len(n_tr) == 2 and all(len(n["blocks"]) == 1 for n in n_tr),
             untrimmed_one_note=len(n_cu) == 1 and len(n_cu[0]["blocks"]) == 1 and n_cu[0]["frames"][1] < K["unmeasured"][0][0],
             steadiness_measured_trimmed=t_tr["S"] is not None, steadiness_unmeasurable_untrimmed=t_cu["S"] is None)
    H["holds"] = all(H.values())
    rep["H"] = H
    rep["trimmed"] = dict(held=n_tr, take=t_tr)
    rep["untrimmed"] = dict(held=n_cu, take=t_cu)
    rep["Q"] = dict(trimmed=n_q_tr, untrimmed=n_q_cu)
    rep["margin_cents"] = margin(p, u)
    rep["frames"] = dict(first=int(idx[0]), last=int(idx[-1]))
    OUT_WAV.parent.mkdir(parents=True, exist_ok=True)
    OUT_WAV.write_bytes(raw)
    rep["wav"] = dict(path=str(OUT_WAV.relative_to(HERE)), sha256=hashlib.sha256(raw).hexdigest(), samples=len(x),
                      seconds=len(x) / SR, gap_samples=gap[1] - gap[0], gap_at=list(gap))
    OUT.write_text(json.dumps(rep, indent=1, default=plain) + "\n")
    print(json.dumps(rep, indent=1, default=plain))


if __name__ == "__main__":
    main()
