"""E-001 round 3 (squillo iteration 66, squillo F-063): is a rung as loud as its take?

Crude experiment code. squillo's `ui` plays the take (UI-013) and each rung (UI-007)
unchanged, so the singer compares them at whatever loudness each has. Fold 1 saw a rung's
peak at 0.718-0.719 from its take's 0.5, a peak and not a loudness. This round measures
loudness.

    uv run python r2_export.py                 # round 1's inputs and requests -> data/cache/r2 (40 s)
    (cd wasm && cargo build --release --bin f1)
    uv run python f1_fold.py gen <squillo>/fixtures   # only if data/cache/f1 is missing
    uv run python r3_loudness.py               # -> results/r3/loudness.json, native.jsonl

Estimate (S19, written before any run): the f1 binary analyses at about 0.09 s per second
of audio and synthesizes each further rung at about 0.03 (round 2, fold 1); round 1's 43
inputs hold about 330 s and fold 1's three takes 95 s, so the WORLD step takes about 1.5
minutes, and the two loudness meters on about 1700 s of audio well under a minute. One
process; no pool.

Inputs (conditions asserted on what is read, S15):
  (a) real: round 1's 19 VocalSet singers (straight-tone scales on /a/, 5.5-18.3 s, 48 kHz),
      as r2_export.py writes them, each with requests `id`, `c100`, `s100` (r2_export.py
      asserts their bounds; here: the files exist, are finite, and the take's samples are
      within [-1, 1]);
  (b) synthetic: round 1's 24 phrases, same requests;
  (c) squillo's `synthesis` fixtures as fold 1 exports them: `voice` with `zero`, `up-50c`,
      `steady`; `long30` and `long60` with `steady`.
  Each rung is made by round 2's crate natively (`wasm/src/bin/f1.rs`, world-rs, WORLD with
  DIO plus StoneMask, CheapTrick, D4C) and rounded to f32, as it crosses squillo's boundary
  (ADR 0006). Browser rungs differ from native ones by at most 4.9e-10 (fold 2), far below
  any loudness resolution here.

Measures, rung minus take, in dB (LU for loudness):
  dL    integrated loudness, ITU-R BS.1770-4: K-weighting (the standard's 48 kHz biquads),
        400 ms blocks with 75 % overlap, absolute gate -70 LKFS, relative gate -10 LU;
        computed twice, by `bs1770()` here and by pyloudnorm 0.2.0 (`pyln`), and both
        reported;
  dRMS  whole-file RMS level;
  dPeak sample peak level;
  block p95: over the 400 ms blocks the take's own gates keep, the 95th percentile of
        |(l_rung - l_take) - dL|, how far a single gain leaves a passage off (recorded,
        a descriptor, not a rule).

The bar, from literature (squillo S11, S12). Jesteadt, Wier and Green (1977), J. Acoust. Soc.
Am. 61(1) 169-177, doi:10.1121/1.381278, abstract read through Crossref: intensity
discrimination for pulsed sinusoids of 200-8000 Hz at 5-80 dB SL is fitted by
dI/I = 0.463 (I/I0)^-0.072, dI the increment for 71 % correct in a two-interval
forced-choice adaptive procedure. As a level difference, dL = 10 log10(1 + dI/I). The bar is
the smallest dL that fit gives inside its measured levels (at 80 dB SL), computed in
`bar()`, floored to 0.01 dB (S11: towards the stricter side). It is a pure-tone figure at
71 % correct; a sung take is a complex tone, and the playback level is unknown, so the
smallest dL in the range is taken. A difference under the bar is smaller than these
listeners could tell apart at their threshold criterion, not one no listener ever hears.

Rule (written and committed before the run):
  R1  If every real rung's |dL| (both meters) is at most the bar, a rung and its take are
      not told apart by loudness at the bar's criterion: no levelling is needed, and F-063
      closes at its fold with this reason. Otherwise levelling is needed: the fold
      specifies a gain that brings each rung's integrated loudness to its take's, and the
      block p95 says what that single gain leaves.
  R2  (recorded) the same outcome stated for the synthetic phrases and for squillo's
      fixtures, which a scenario could use.

Checks of the checks (S15; each must-pass and must-fail differs in the input it reads):
  meter_sine: a 997 Hz sine at full scale, 10 s, mono, reads -3.01 LKFS within 0.05
      (BS.1770-4, Annex 1 note: such a sine in one channel gives -3.01 LKFS), in both
      meters; must fail: the same sine at half amplitude (-9.03).
  meter_gate: 5 s of silence then that sine reads, within 0.05 in both meters, what the
      gating gives by its definition: the 97 blocks wholly in the sine and the 3 that straddle
      the edge (holding 3/4, 1/2 and 1/4 of a block's energy) pass both gates, so
      -3.01 + 10 log10(98.5 / 100) (computed in code); must fail: the ungated mean-square
      level of the same input.
  meters_agree: the two meters' dL agree within 0.05 LU on every rung; must pass: both on a
      take against itself scaled by 0.9; must fail: pyloudnorm on the take against itself
      raised by 0.2 dB, against this meter on the take against itself.

Revision 1, before the full run (S19, a harness fault found by the checks' own first run,
which read no rung): the first meter_gate expected -3.01, but under BS.1770's gating the 3
blocks straddling the silence's edge pass the relative gate and pull the level to -3.076, as
this meter read; and pyloudnorm reads the full-scale sine at -3.052, 0.04 LU from the
standard's -3.01 (its K-weighting is designed from analogue prototypes, not the standard's
48 kHz coefficients), an offset in absolute level that cancels in a difference. So meters_agree
compares the two meters' dL, the measure the rule reads, not their absolute levels, which are
recorded.
  rule: R1's comparison passes a take against itself and fails it against the same take
      raised by 1 dB.
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pyloudnorm as pyln
from scipy.signal import lfilter

HERE = Path(__file__).parent
CACHE = HERE / "data" / "cache"
OUT = HERE / "results" / "r3"
SR = 48_000
F1 = HERE / "wasm" / "target" / "release" / "f1"
MODS = ("id", "c100", "s100")
FOLD1 = {"voice": ("zero", "up-50c", "steady"), "long30": ("steady",), "long60": ("steady",)}
VOCALSET = ("f1", "f2", "f3", "f5", "f6", "f7", "f8", "f9",
            "m1", "m2", "m3", "m4", "m5", "m6", "m7", "m8", "m9", "m10", "m11")

# ITU-R BS.1770-4, Annex 1, Tables 1 and 2: the K-weighting biquads at 48 kHz
K1_B = (1.53512485958697, -2.69169618940638, 1.19839281085285)
K1_A = (1.0, -1.69065929318241, 0.73248077421585)
K2_B = (1.0, -2.0, 1.0)
K2_A = (1.0, -1.99004745483398, 0.99007225036621)
SINE_LKFS = -3.01  # BS.1770-4: a full-scale 997 Hz sine in one channel
TOL_METER = 0.05


def committed_first():
    """squillo L-047 (S15): this script holds the rule and the bar; it refuses to run on an
    uncommitted edit of itself, or before it is committed at all."""
    here = Path(__file__).resolve()
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", here.name], cwd=here.parent,
                             capture_output=True).returncode == 0
    r = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", here.name], cwd=here.parent)
    if not tracked or r.returncode != 0:
        raise SystemExit(f"{here.name} has uncommitted edits: commit its rules first (S15, L-047)")


def bar():
    """Smallest level difference limen of Jesteadt, Wier and Green's (1977) fit over the
    sensation levels they measured (5-80 dB SL), floored to 0.01 dB."""
    sl = np.arange(5.0, 80.0 + 1e-9, 0.1)
    dl = 10 * np.log10(1 + 0.463 * (10 ** (sl / 10)) ** -0.072)
    i = int(np.argmin(dl))
    return dict(sl_at_min=float(sl[i]), dl_min=float(dl[i]), bar=float(np.floor(dl[i] * 100) / 100),
                dl_at_5=float(dl[0]))


def blocks(x):
    """Mean square of the K-weighted signal in 400 ms blocks with 75 % overlap (BS.1770-4)."""
    y = lfilter(K2_B, K2_A, lfilter(K1_B, K1_A, x))
    n, hop = int(0.4 * SR), int(0.1 * SR)
    m = (len(y) - n) // hop + 1
    c = np.concatenate([[0.0], np.cumsum(y * y)])
    s = np.arange(m) * hop
    return (c[s + n] - c[s]) / n


def lk(z):
    return -0.691 + 10 * np.log10(z)


def gates(z):
    """Indices of the blocks both gates keep."""
    with np.errstate(divide="ignore"):
        l = lk(z)
    a = l > -70.0
    rel = lk(z[a].mean()) - 10.0
    return a & (l > rel)


def bs1770(x):
    z = blocks(x)
    return float(lk(z[gates(z)].mean()))


METER = pyln.Meter(SR)


def pyln_l(x):
    return float(METER.integrated_loudness(x))


def db(v):
    return float(20 * np.log10(v))


def compare(x, y):
    zx, zy = blocks(x), blocks(y)
    g = gates(zx)
    lx, ly = bs1770(x), bs1770(y)
    px, py = pyln_l(x), pyln_l(y)
    d = lk(zy[g]) - lk(zx[g]) - (ly - lx)
    return dict(L_take=lx, L_rung=ly, dL=ly - lx, dL_pyln=py - px, meters_take=px - lx, meters_rung=py - ly,
                dRMS=db(np.sqrt(np.mean(y * y)) / np.sqrt(np.mean(x * x))),
                dPeak=db(np.abs(y).max() / np.abs(x).max()),
                block_p95=float(np.percentile(np.abs(d), 95)), blocks=int(g.sum()))


def inaudible(c, b):
    return max(abs(c["dL"]), abs(c["dL_pyln"])) <= b


def check_the_checks(b):
    t = np.arange(10 * SR) / SR
    sine = np.sin(2 * np.pi * 997 * t)
    half = 0.5 * sine
    gated = np.concatenate([np.zeros(5 * SR), sine])
    out = {}
    out["meter_sine_must_pass"] = [bs1770(sine), pyln_l(sine)]
    out["meter_sine_must_fail"] = [bs1770(half), pyln_l(half)]
    assert all(abs(v - SINE_LKFS) <= TOL_METER for v in out["meter_sine_must_pass"]), out
    assert not any(abs(v - SINE_LKFS) <= TOL_METER for v in out["meter_sine_must_fail"]), out
    zg = blocks(gated)
    whole = (10 * SR - int(0.4 * SR)) // int(0.1 * SR) + 1  # blocks wholly in the sine: 97
    gate_expect = SINE_LKFS + 10 * np.log10((whole + 0.75 + 0.5 + 0.25) / (whole + 3))
    out["meter_gate_expect"] = float(gate_expect)
    out["meter_gate_must_pass"] = [bs1770(gated), pyln_l(gated)]
    out["meter_gate_must_fail"] = float(lk(zg.mean()))
    assert all(abs(v - gate_expect) <= TOL_METER for v in out["meter_gate_must_pass"]), out
    assert abs(out["meter_gate_must_fail"] - gate_expect) > TOL_METER, out
    x = np.fromfile(CACHE / "r2" / "m1.x.f64", dtype="<f8")
    out["meters_agree_must_pass"] = (pyln_l(0.9 * x) - pyln_l(x)) - (bs1770(0.9 * x) - bs1770(x))
    out["meters_agree_must_fail"] = (pyln_l(x * 10 ** (0.2 / 20)) - pyln_l(x)) - (bs1770(x) - bs1770(x))
    assert abs(out["meters_agree_must_pass"]) <= TOL_METER, out
    assert abs(out["meters_agree_must_fail"]) > TOL_METER, out
    out["rule_must_pass"] = compare(x, x)["dL"]
    out["rule_must_fail"] = compare(x, x * 10 ** (1 / 20))["dL"]
    assert abs(out["rule_must_pass"]) <= b and abs(out["rule_must_fail"]) > b, out
    assert inaudible(compare(x, x), b) and not inaudible(compare(x, x * 10 ** (1 / 20)), b), out
    return out


def read(p):
    v = np.fromfile(p, dtype="<f8")
    assert len(v) > 0 and np.isfinite(v).all(), p
    return v


def run_world(d, entries):
    """Run the f1 binary on dir d with its own list.txt; returns its JSON lines."""
    (d / "list.txt").write_text("".join(f"{n} {' '.join(r)}\n" for n, r in entries))
    p = subprocess.run([str(F1), str(d)], capture_output=True, text=True, check=True)
    return [json.loads(l) for l in p.stdout.splitlines()]


def main():
    committed_first()
    OUT.mkdir(parents=True, exist_ok=True)
    b = bar()
    report = dict(bar=b, checks=check_the_checks(b["bar"]), items=[])
    assert report["checks"] and b["bar"] > 0
    # (a), (b): round 1's inputs in their own directory, linked from r2's export
    r3 = CACHE / "r3"
    r3.mkdir(exist_ok=True)
    names = [l.split()[0] for l in (CACHE / "r2" / "list.txt").read_text().splitlines()]
    assert set(VOCALSET) <= set(names) and len(names) == 43, names
    for n in names:
        for s in ["x"] + list(MODS):
            link = r3 / f"{n}.{s}.f64"
            if not link.exists():
                link.symlink_to((CACHE / "r2" / f"{n}.{s}.f64").resolve())
    native = run_world(r3, [(n, MODS) for n in names])
    native += run_world(CACHE / "f1", list(FOLD1.items()))
    (OUT / "native.jsonl").write_text("".join(json.dumps(l) + "\n" for l in native))
    sets = [("vocalset" if n in VOCALSET else "synthetic", r3, n, MODS) for n in names]
    sets += [("fixture", CACHE / "f1", n, r) for n, r in FOLD1.items()]
    for kind, d, n, reqs in sets:
        x = read(d / f"{n}.x.f64")
        assert np.abs(x).max() <= 1.0, n
        for q in reqs:
            y = read(d / "out" / f"{n}.{q}.native.f64").astype(np.float32).astype(np.float64)
            assert len(y) == len(x), (n, q)
            c = compare(x, y)
            assert abs(c["dL_pyln"] - c["dL"]) <= TOL_METER, (n, q, c)
            report["items"].append(dict(kind=kind, input=n, request=q, **c,
                                        inaudible=inaudible(c, b["bar"])))
    report["meters_agree_max"] = max(abs(i["dL_pyln"] - i["dL"]) for i in report["items"])
    report["meters_offset_range"] = [min(min(i["meters_take"], i["meters_rung"]) for i in report["items"]),
                                     max(max(i["meters_take"], i["meters_rung"]) for i in report["items"])]
    rng = np.random.default_rng(20261002)
    summ = {}
    for kind in ("vocalset", "synthetic", "fixture"):
        for q in sorted({i["request"] for i in report["items"] if i["kind"] == kind}):
            its = [i for i in report["items"] if i["kind"] == kind and i["request"] == q]
            dl = np.array([i["dL"] for i in its])
            boot = [np.median(rng.choice(dl, len(dl))) for _ in range(2000)] if len(dl) > 2 else [np.nan]
            summ[f"{kind}/{q}"] = dict(
                n=len(its), dL_median=float(np.median(dl)), dL_min=float(dl.min()), dL_max=float(dl.max()),
                dL_median_ci95=[float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
                abs_dL_max=float(max(max(abs(i["dL"]), abs(i["dL_pyln"])) for i in its)),
                dRMS=[float(min(i["dRMS"] for i in its)), float(max(i["dRMS"] for i in its))],
                dPeak=[float(min(i["dPeak"] for i in its)), float(max(i["dPeak"] for i in its))],
                block_p95=[float(min(i["block_p95"] for i in its)), float(max(i["block_p95"] for i in its))],
                inaudible=sum(i["inaudible"] for i in its))
    report["summary"] = summ
    real = [i for i in report["items"] if i["kind"] == "vocalset"]
    assert len(real) == len(VOCALSET) * len(MODS), len(real)
    report["R1"] = dict(inaudible_all=all(i["inaudible"] for i in real),
                        inaudible=sum(i["inaudible"] for i in real), n=len(real),
                        outcome="no levelling" if all(i["inaudible"] for i in real) else "levelling needed")
    for kind in ("synthetic", "fixture"):
        its = [i for i in report["items"] if i["kind"] == kind]
        report[f"R2_{kind}"] = dict(inaudible=sum(i["inaudible"] for i in its), n=len(its))
    (OUT / "loudness.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(dict(bar=b, R1=report["R1"], meters_agree_max=report["meters_agree_max"],
                          summary=summ), indent=1))


if __name__ == "__main__":
    sys.exit(main())
