"""E-004 round 4, post hoc (written after held.json, squillo iteration 68): why a held note is lost.

    uv run --project ../E-002-measurement-reliability python r4_diag.py   # -> results/r4/diag.json

For every rendering of a new item whose measured blocks fall below rule (2)'s count, re-render it exactly
(r4_held.one, same job and seed; the blocks must equal the cached run's, asserted) and, for each written note
of at least 250 frames, read MT-009's steps on that note's written frames: the share of frames accepted
(pitch and a finite MT-003 u), the longest stretch not accepted, and whether fold2.held_notes found a piece
overlapping it. A note is lost by (a) refusal when its accepted share is under 3/4 or a stretch exceeds 12
frames (MT-009's limits), else (b) by the 60-cent cut. For (b), every piece of the take is listed by
`pieces`, a copy of fold2.held_notes's loop (E-002 fold2.py lines 136-170) that keeps the pieces it rejects,
asserted to give exactly fold2.held_notes's held notes on every rendering it reads; the longest piece
overlapping the note is classed by the first MT-009 condition it fails, in fold2's order: shorter than 250
frames, begins on a frame not measured, ends on one, a stretch over 12 frames, over a quarter filled.
Diagnosis only: no rule of round 4 changes. It ran three times uncommitted and unguarded before its guard
was added (squillo L-056); the guarded, committed run's diag.json is byte for byte the last unguarded one's.
Crude, disposable lab code: never product code (squillo PLAN.md rule 11).
"""
import json
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

import subprocess

import r4_held as R

HERE = Path(__file__).parent


def pieces(p, u, fold2):
    """fold2.held_notes (E-002 fold2.py lines 136-170), every piece kept: (first, last, why) per piece,
    frames as indices into p, why None for a held note."""
    acc = ~np.isnan(p) & np.isfinite(u)
    out, n, i = [], len(p), 0
    while i < n:
        if not acc[i]:
            i += 1
            continue
        j, last = i, i
        while j < n and j - last <= fold2.MAX_GAP + 1:
            if acc[j]:
                last = j
            j += 1
        run = np.arange(i, last + 1)
        i = last + 1
        if len(run) < fold2.MIN_LEN:
            continue
        a = acc[run].copy()
        med = np.median(p[run][a])
        a &= np.abs(np.where(a, p[run], med) - med) <= fold2.OCT
        if a.sum() < 2:
            continue
        x = np.arange(len(run))
        lp = fold2.filtfilt(*fold2.B2, np.interp(x, x[a], p[run][a]))
        s0 = 0
        while s0 < len(run):
            ref = np.median(lp[s0:s0 + 31])
            s1 = s0 + 1
            while s1 < len(run) and abs(lp[s1] - ref) <= fold2.SPLIT:
                s1 += 1
            aa = a[s0:s1]
            gaps = np.diff(np.concatenate([[0], (~aa).astype(int), [0]]))
            st, en = np.nonzero(gaps == 1)[0], np.nonzero(gaps == -1)[0]
            why = ("short" if s1 - s0 < fold2.MIN_LEN else "begins-unmeasured" if not aa[0] else
                   "ends-unmeasured" if not aa[-1] else
                   "gap" if len(st) and (en - st).max() > fold2.MAX_GAP else
                   "filled" if (~aa).mean() > fold2.MAX_FILL else None)
            out.append((int(run[s0]), int(run[s1 - 1]), why))
            s0 = s1
    return out


def main(squillo):
    c = R.ctx()
    yin, A, fold2 = c["yin"], c["A"], c["fold2"]
    held = json.load(open(R.RES / "held.json"))["per_item"]
    new = {d["id"] for d in R.ITEMS}
    cap = {}
    orig = R.held_blocks

    def spy(x):
        cap["x"] = x
        return orig(x)
    R.held_blocks = spy
    out = []
    for j in R.jobs(squillo):
        pid, mel = j[0], j[1]
        if pid not in new:
            continue
        cached = json.loads((R.CACHE / f"{j[5]}.json").read_text())
        if cached["total_blocks"] >= held[pid]["rule2"]:
            continue
        r = R.one(j)
        assert r["total_blocks"] == cached["total_blocks"] and r["blocks"] == cached["blocks"], (j, r, cached)
        x = cap["x"]
        idx, f, dip = yin.yin(x)
        f = yin.in_range(f, 3.0)
        u = np.where(np.isnan(f), np.inf, A.u_of(np.nan_to_num(dip, nan=1.0), c["table"]))
        acc = ~np.isnan(f) & np.isfinite(u)
        pc = pieces(fold2.cents(f), u, fold2)
        mine = [(int(idx[a]), int(idx[b])) for a, b, why in pc if why is None]
        assert mine == [tuple(h) for h in r["held"]], (j[:1] + j[2:], mine, r["held"])
        durs = [Fraction(n["quarters"]) * 60 / mel["tempo_qpm"] for n in mel["notes"]]
        starts = np.concatenate([[0.0], np.cumsum([float(d) for d in durs])[:-1]]) + 0.1
        t = c["e5run"].HOP * (idx + 1) / 48000 - c["e5run"].LAG_S   # E-005 run.track's frame time
        notes = []
        for k, d in enumerate(durs):
            if int(d * 125) < 250:
                continue
            m = (t >= starts[k]) & (t < starts[k] + float(d))
            a = acc[m]
            gaps = np.diff(np.concatenate([[0], (~a).astype(int), [0]]))
            st, en = np.nonzero(gaps == 1)[0], np.nonzero(gaps == -1)[0]
            longest = int((en - st).max()) if len(st) else 0
            fr = set(np.nonzero(m)[0].tolist())
            found = [h for h in r["held"] if any(h[0] <= idx[i] <= h[1] for i in fr)]
            cause = ("refusal" if a.mean() < 0.75 or longest > 12 else "cut") if not found else "found"
            nf = np.nonzero(m)[0]
            over = [(b - a + 1, a, b, why) for a, b, why in pc if a <= nf[-1] and b >= nf[0]]
            piece = max(over) if over else None
            notes.append(dict(note=k, frames=int(m.sum()), accepted=round(float(a.mean()), 4),
                              longest_unaccepted=longest, found=found, cause=cause,
                              longest_piece=None if piece is None else dict(frames=piece[0], why=piece[3])))
        out.append(dict(id=pid, voice=j[2], sigma=j[3], vib=j[4], blocks=r["total_blocks"],
                        rule2=held[pid]["rule2"], notes=notes))
    causes, why = {}, {}
    for o in out:
        for n in o["notes"]:
            causes[n["cause"]] = causes.get(n["cause"], 0) + 1
            if n["cause"] != "found":
                w = n["longest_piece"]["why"] if n["longest_piece"] else "no-piece"
                why[w] = why.get(w, 0) + 1
    lost_long = [n["longest_piece"]["frames"] for o in out for n in o["notes"]
                 if n["cause"] != "found" and n["longest_piece"] and n["longest_piece"]["frames"] >= 250]
    # The held notes written (>= 250 frames) in every rendering of the new items, and how many were lost.
    def wilson(k, n, z=1.959963984540054):
        p_ = k / n
        d = 1 + z * z / n
        m = (p_ + z * z / (2 * n)) / d
        h = z * np.sqrt(p_ * (1 - p_) / n + z * z / (4 * n * n)) / d
        return [round(float(m - h), 4), round(float(m + h), 4)]
    written = {d["id"]: sum(int(Fraction(t.split(":")[1]) * 60 / d["tempo"] * 125) >= 250 for t in d["notes"].split())
               for d in R.ITEMS}
    n_held = sum(written[k] * held[k]["renderings"] for k in written)
    n_lost = sum(n["cause"] != "found" for o in out for n in o["notes"])
    one_held = sorted(k for k, v in written.items() if v == 1)
    rend = {k: [held[k]["renderings_two_blocks"], held[k]["renderings"]] for k in written}
    k1 = sum(rend[k][0] for k in one_held), sum(rend[k][1] for k in one_held)
    k2 = sum(rend[k][0] for k in written if k not in one_held), sum(rend[k][1] for k in written if k not in one_held)
    share = dict(held_notes=n_held, lost=n_lost, lost_share=round(n_lost / n_held, 4), lost_wilson95=wilson(n_lost, n_held),
                 one_held_note_items=one_held, two_blocks_one_held=list(k1), two_blocks_one_held_wilson95=wilson(*k1),
                 two_blocks_two_held=list(k2), two_blocks_two_held_wilson95=wilson(*k2),
                 bar_B_one_held=[k for k in one_held if held[k]["bar_B"]],
                 bar_B_two_held=sorted(k for k in written if k not in one_held and held[k]["bar_B"]))
    rep = dict(renderings=len(out), held_note_causes=causes, lost_by=why, share=share,
               lost_piece_frames=dict(min=min(lost_long), max=max(lost_long)) if lost_long else None, rows=out)
    (R.RES / "diag.json").write_text(json.dumps(rep, indent=1) + "\n")
    print(json.dumps({k: v for k, v in rep.items() if k != "rows"}, indent=1))
    for o in out:
        print(o["id"], o["voice"], o["sigma"], o["vib"], o["blocks"], "/", o["rule2"],
              [(n["accepted"], n["longest_unaccepted"], n["cause"], n["longest_piece"]) for n in o["notes"]])


def committed_first():
    """S15: refuse to run on an uncommitted edit of this file or of r4_held.py, whose code it re-runs."""
    for me in (Path(__file__).name, "r4_held.py"):
        a = subprocess.run(["git", "ls-files", "--error-unmatch", me], cwd=HERE, capture_output=True)
        b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", me], cwd=HERE)
        if a.returncode or b.returncode:
            sys.exit(f"{me} is not committed as it stands: commit the rules before running")


if __name__ == "__main__":
    committed_first()
    main(sys.argv[1] if len(sys.argv) > 1 else str(HERE.parents[2] / "squillo"))
