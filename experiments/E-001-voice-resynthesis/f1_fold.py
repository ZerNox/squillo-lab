"""E-001 fold 1: squillo's `synthesis` fixtures and scenarios (squillo
iteration 37, F-021, F-035). Crude experiment code.

    uv run python f1_fold.py gen <squillo>/fixtures     # fixtures, and data/cache/f1 for the builds
    ./wasm/target/release/f1 data/cache/f1 > results/f1/native.jsonl
    node f1_run.mjs                                      # Chrome and Firefox: results/f1/<browser>.json
    uv run python f1_fold.py check <squillo>/fixtures   # results/f1/fold.json

What it answers for squillo's first `synthesis` spec:

1. Squillo's fixtures: one voice-like take, its requests (the change in
   cents per frame), a take longer than the longest squillo accepts.
2. The delivered-change rule, as written in squillo's SY-003 before this
   runs: on at least 95 % of the frames whose pitch `metrics` measures in
   the take (MT-002, MT-003), the rung's frame is measured too and differs
   from the take's by the change within 2 sqrt(u_take^2 + u_rung^2) (MT-005's
   coverage factor 2; MT-008's bound for two measured values). Checked on
   round 2's WORLD pipeline (DIO plus StoneMask, world-rs 0.1.0) for three
   requests, and, as the check of the check (S15, L-036): first on an ideal
   render of each request by the fixture's own formula (must pass), then on
   an output made for another request (must fail).
3. The same output in both browsers, twice each (f1_run.mjs), and against
   native; the time and memory of 30 s and 60 s takes (squillo Q-020).

Conditions, written before generating (S15), each asserted on the output:
- The voice take: 5 s, 240 000 samples, 625 frames (squillo SG-002). Its
  frequency 220 (1 + 0.012 sin(2 pi 0.5 t)) Hz, the wobble of squillo's
  fixtures/metrics/held-wobble.wav (E-002 fold2.py:350 at 51f3964, FIX), inside
  E2..C6 (yin.E2, yin.C6) at every sample, from the exact formula, and
  still inside after a +50-cent change. Harmonics k = 1..K with K * 220 *
  1.012 below 20 kHz, amplitude envelope(k * 220) / k of voice.py's male
  /a/ (voice.py:18-29 FORMANTS and the higher-pole correction, :41-50
  envelope, :114 the 1/k), scaled to a peak of 0.5 on a float64 draft;
  asserted: peak at most 1 on the file. No aspiration noise, so the file is
  a formula. It is a test input for synthesis, not a stand-in for voices:
  what WORLD does to real voices is rounds 1 and 2's, on VocalSet.
- Every frame 3..624 of the take measured by `metrics` (YIN in range,
  aperiodicity below MT-003's refusal), so a request names each of them.
- Requests: a number of cents for each measured frame, null for every
  other; |change| <= 50 cents on the accepted ones (squillo SY-002, from
  round 1's requests, run.py:89-91 and r2_export.py's assertion). The
  refused ones break exactly one rule each: 624 entries; one entry 50.5;
  a number on frame 0, which is not measured.
- The long take: 1 440 384 samples, one frame (384 samples) more than the
  30 s squillo SY-006 accepts, all zero.
"""
import ast
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "E-002-measurement-reliability"))
import yin  # noqa: E402
import voice  # noqa: E402

SR = 48_000
CACHE = HERE / "data" / "cache" / "f1"
OUT = HERE / "results" / "f1"
E002 = HERE.parent / "E-002-measurement-reliability"
N5, NFR = 240_000, 625
F0, WOB, WRATE = 220.0, 0.012, 0.5
K = int(20_000 // (F0 * (1 + WOB)))
LONGEST = 30 * SR
MAXC = 50.0
pi = math.pi


def check(ok, what):
    if not ok:
        sys.exit(f"S15 condition failed: {what}")


# ---------------------------------------------------------------- MT-003, read from its sources
def mt003():
    """The table as E-002 fold2 wrote it (results/fold2.json, measures/spec/table) and its bins as
    r2_analyse.py defines them (BINS), read from the files, never retyped."""
    table = json.loads((E002 / "results" / "fold2.json").read_text())["measures"]["spec"]["table"]
    src = (E002 / "r2_analyse.py").read_text()
    bins = next(ast.literal_eval(n.value) for n in ast.parse(src).body
                if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "BINS")
    return np.array([np.inf if v is None else v for v in table]), np.array(bins)


TABLE, BINS = mt003()


def measure(x):
    """metrics' pitch cells: cents re A4 and u, NaN where not measured (MT-002, MT-003), frames 0..n-1."""
    idx, f, dip = yin.yin(x)
    f = yin.in_range(f, 3.0)
    k = np.clip(np.searchsorted(BINS, np.nan_to_num(dip, nan=1.0), side="right") - 1, 0, len(TABLE) - 1)
    u = np.where(np.isnan(f), np.inf, TABLE[k])
    n = len(x) // 384
    c = np.full(n, np.nan)
    uu = np.full(n, np.nan)
    ok = np.isfinite(u)
    c[idx[ok]] = 1200 * np.log2(f[ok] / 440.0)
    uu[idx[ok]] = u[ok]
    P = np.full(n, np.nan)
    P[idx[ok]] = 48_000 / f[ok]
    return c, uu, P, idx


# ---------------------------------------------------------------- 1. fixtures
def amplitudes():
    k = np.arange(1, K + 1)
    return voice.envelope("male", k * F0) / k


def phase(n):
    return 2 * pi * F0 * n / 48000 + F0 * WOB / WRATE * (1 - math.cos(2 * pi * WRATE * n / 48000))


def wav(samples):
    data = struct.pack(f"<{len(samples)}f", *samples)
    fmt = struct.pack("<HHIIHHH", 3, 1, SR, SR * 4, 4, 32, 0)
    body = (b"WAVE" + b"fmt " + struct.pack("<I", 18) + fmt
            + b"fact" + struct.pack("<I", 4) + struct.pack("<I", len(samples))
            + b"data" + struct.pack("<I", len(data)) + data)
    return b"RIFF" + struct.pack("<I", len(body)) + body


def read_wav(p):
    raw = Path(p).read_bytes()
    k = raw.index(b"data") + 8
    return np.frombuffer(raw[k:], "<f4").astype(np.float64)


def voice_take():
    a = amplitudes()
    # the scale: peak 0.5 on a float64 draft of the same sum
    n = np.arange(N5)
    ph = 2 * pi * F0 * n / 48000 + F0 * WOB / WRATE * (1 - np.cos(2 * pi * WRATE * n / 48000))
    draft = sum(a[k - 1] * np.sin(k * ph) for k in range(1, K + 1))
    scale = 0.5 / np.abs(draft).max()
    coef = [float(scale * v) for v in a]
    s = []
    for i in range(N5):
        p = phase(i)
        acc = 0.0
        for k in range(1, K + 1):
            acc += coef[k - 1] * math.sin(k * p)
        s.append(acc)
    return coef, s


def request_json(changes):
    return (json.dumps({"change_cents": changes}, indent=2) + "\n").encode()


def gen(fixdir):
    fixdir = Path(fixdir) / "synthesis"
    fixdir.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    R = {"K": K, "table": [None if not np.isfinite(v) else float(v) for v in TABLE], "bins": BINS.tolist()}
    t = np.arange(N5) / SR
    f = F0 * (1 + WOB * np.sin(2 * pi * WRATE * t))
    check(f.min() >= yin.E2 and f.max() * 2 ** (MAXC / 1200) <= yin.C6, "voice take inside E2..C6, also +50 cents")
    check(K * F0 * (1 + WOB) < 20_000 and (K + 1) * F0 * (1 + WOB) >= 20_000, "K the last harmonic below 20 kHz")
    coef, s = voice_take()
    blob = wav(s)
    x = read_wav_bytes(blob)
    check(len(x) == N5 and np.isfinite(x).all() and np.abs(x).max() <= 1.0, "voice take: 240000 finite samples, peak <= 1")
    (fixdir / "voice-220hz-wobble.wav").write_bytes(blob)
    c, u, P, _ = measure(x)
    meas = np.isfinite(c)
    check(len(c) == NFR and not meas[:3].any() and meas[3:].all(), "every frame 3..624 of the voice take measured")
    R["voice"] = dict(coef=coef, peak=float(np.abs(x).max()), sha256=hashlib.sha256(blob).hexdigest(), bytes=len(blob),
                      measured=int(meas.sum()), u_values={str(round(float(v), 6)): int(n) for v, n in zip(*np.unique(u[meas], return_counts=True))},
                      f_min=float(f.min()), f_max=float(f.max()), h1_minus_h2_db=float(20 * np.log10(coef[0] / coef[1])))
    # requests
    i = np.arange(NFR)
    tinst = (384 * i - 766 + (48000 / F0) / 2) / SR
    steady = [None if not meas[j] else round(float(-1200 * np.log2(1 + WOB * np.sin(2 * pi * WRATE * tinst[j]))), 4) for j in i]
    reqs = {
        "request-zero.json": [None if not m else 0.0 for m in meas],
        "request-up-50c.json": [None if not m else 50.0 for m in meas],
        "request-steady.json": steady,
    }
    over = list(reqs["request-up-50c.json"]); over[312] = 50.5
    on0 = list(reqs["request-up-50c.json"]); on0[0] = 50.0
    reqs["request-over-50c.json"] = over
    reqs["request-short.json"] = reqs["request-up-50c.json"][:NFR - 1]
    reqs["request-on-unmeasured.json"] = on0
    for name, ch in reqs.items():
        acc = [v for v in ch if v is not None]
        b = request_json(ch)
        (fixdir / name).write_bytes(b)
        R[name] = dict(sha256=hashlib.sha256(b).hexdigest(), entries=len(ch), numbers=len(acc),
                       max_abs=max(abs(v) for v in acc), first_number=ch.index(acc[0]))
    for name in ("request-zero.json", "request-up-50c.json", "request-steady.json"):
        check(R[name]["max_abs"] <= MAXC and R[name]["entries"] == NFR and R[name]["numbers"] == int(meas.sum()),
              f"{name}: within 50 cents, a number on every measured frame and only there")
    check(R["request-over-50c.json"]["max_abs"] == 50.5 and R["request-short.json"]["entries"] == NFR - 1
          and R["request-on-unmeasured.json"]["first_number"] == 0, "each refused request breaks its one rule")
    # the long take
    nl = LONGEST + 384
    blob = wav([0.0] * nl)
    (fixdir / "silence-30s-plus.wav").write_bytes(blob)
    zl = [None] * (nl // 384)
    b = request_json(zl)
    (fixdir / "request-silence-30s-plus.json").write_bytes(b)
    check(len(read_wav_bytes(blob)) == nl and nl // 384 == 3751, "long take: 1 440 384 samples, 3751 frames")
    R["silence-30s-plus.wav"] = dict(sha256=hashlib.sha256(blob).hexdigest(), bytes=len(blob), samples=nl)
    R["request-silence-30s-plus.json"] = dict(sha256=hashlib.sha256(b).hexdigest(), entries=len(zl))
    # exports for the builds: the take, and each accepted request at WORLD's 5 ms frame times
    x.astype("<f8").tofile(CACHE / "voice.x.f64")
    lines = ["voice"]
    for name in ("request-zero.json", "request-up-50c.json", "request-steady.json"):
        key = name[len("request-"):-len(".json")]
        world_request(reqs[name], P, N5).astype("<f8").tofile(CACHE / f"voice.{key}.f64")
        lines[0] += " " + key
    # 30 s and 60 s takes for time and memory (squillo Q-020): the same formula, float64, not fixtures
    for secs in (30, 60):
        n = np.arange(secs * SR)
        ph = 2 * pi * F0 * n / 48000 + F0 * WOB / WRATE * (1 - np.cos(2 * pi * WRATE * n / 48000))
        xl = sum(coef[k - 1] * np.sin(k * ph) for k in range(1, K + 1))
        check(len(xl) == secs * SR and np.abs(xl).max() <= 1.0, f"{secs} s take")
        xl.astype("<f8").tofile(CACHE / f"long{secs}.x.f64")
        cl, _, Pl, _ = measure(xl)
        chl = [None if not np.isfinite(v) else float(-1200 * np.log2(1 + WOB * np.sin(2 * pi * WRATE * ((384 * j - 766 + 48000 / F0 / 2) / SR))))
               for j, v in enumerate(cl)]
        world_request(chl, Pl, len(xl)).astype("<f8").tofile(CACHE / f"long{secs}.steady.f64")
        lines.append(f"long{secs} steady")
    (CACHE / "list.txt").write_text("\n".join(lines) + "\n")
    (OUT / "gen.json").write_text(json.dumps(R, indent=1))
    print(json.dumps({k: (v if k != "voice" else {kk: vv for kk, vv in v.items() if kk != "coef"}) for k, v in R.items()}, indent=1))


def read_wav_bytes(blob):
    k = blob.index(b"data") + 8
    return np.frombuffer(blob[k:], "<f4").astype(np.float64)


def world_request(changes, P, n):
    """The change placed at each measured frame's instant (squillo SG-007: 384 i - 766 + P/2, P the frame's
    measured period), linear between, held at the ends, sampled at WORLD's frame times k * 5 ms."""
    ch = np.array([np.nan if v is None else v for v in changes], dtype=float)
    m = np.isfinite(ch)
    tw = np.arange(n // 240 + 1) * 0.005
    if not m.any():
        return np.zeros(len(tw))
    i = np.arange(len(ch))
    t = (384 * i[m] - 766 + P[m] / 2) / SR
    check(np.all(np.diff(t) > 0), "frame instants increase")
    return np.interp(tw, t, ch[m])


# ---------------------------------------------------------------- 2. the delivered-change rule
def delivered(c_in, u_in, c_out, u_out, change):
    """SY-003 as written: the share of the take's measured frames whose rung frame is measured and within
    2 sqrt(u_in^2 + u_out^2) of the take's value plus the change."""
    m = np.isfinite(c_in)
    ch = np.array([np.nan if v is None else v for v in change], dtype=float)
    assert np.all(np.isfinite(ch[m])) and not np.isfinite(ch[~m]).any()
    ok = m & np.isfinite(c_out)
    err = np.abs(c_out - c_in - ch)
    bound = 2 * np.sqrt(u_in ** 2 + u_out ** 2)
    good = ok & (err <= bound)
    e = err[ok]
    octave = int((ok & (np.abs(c_out - c_in - ch) > 600)).sum())
    return dict(share=float(good.sum() / m.sum()), frames=int(m.sum()), rung_measured=int(ok.sum()),
                within=int(good.sum()), err_median=float(np.median(e)), err_p95=float(np.percentile(e, 95)),
                err_max=float(e.max()), bound_min=float(bound[ok].min()), octave_frames=octave,
                passes=bool(good.sum() >= 0.95 * m.sum()))


def ideal(coef, key):
    """The fixture's own formula along the requested contour (must pass): +50 cents scales the phase;
    steadying removes the wobble, leaving 220 Hz; zero is the take."""
    n = np.arange(N5)
    ph = 2 * pi * F0 * n / 48000 + F0 * WOB / WRATE * (1 - np.cos(2 * pi * WRATE * n / 48000))
    if key == "up-50c":
        ph = ph * 2 ** (50 / 1200)
    elif key == "steady":
        ph = 2 * pi * F0 * n / 48000
    return sum(coef[k - 1] * np.sin(k * ph) for k in range(1, K + 1))


def check_all(fixdir):
    fixdir = Path(fixdir) / "synthesis"
    G = json.loads((OUT / "gen.json").read_text())
    coef = G["voice"]["coef"]
    x = read_wav(fixdir / "voice-220hz-wobble.wav")
    check(hashlib.sha256((fixdir / "voice-220hz-wobble.wav").read_bytes()).hexdigest() == G["voice"]["sha256"], "fixture unchanged since gen")
    c_in, u_in, _, _ = measure(x)
    R = {"rule": {}, "ideal": {}, "must_fail": {}}
    req = {k: json.loads((fixdir / f"request-{k}.json").read_text())["change_cents"] for k in ("zero", "up-50c", "steady")}
    outs = {}
    for k in req:
        y = np.fromfile(CACHE / "out" / f"voice.{k}.native.f64", "<f8")
        check(len(y) == N5 and np.isfinite(y).all(), f"{k}: output length and finite")
        outs[k] = y
        yf = y.astype(np.float32).astype(np.float64)  # as the rung crosses the boundary (ADR 0006: f32)
        c_o, u_o, _, _ = measure(yf)
        R["rule"][k] = delivered(c_in, u_in, c_o, u_o, req[k]) | dict(peak=float(np.abs(y).max()))
        c_i, u_i, _, _ = measure(ideal(coef, k).astype(np.float32).astype(np.float64))
        R["ideal"][k] = delivered(c_in, u_in, c_i, u_i, req[k])
    # must fail: the zero request's output judged against +50 and against steadying; the +50 output against zero
    for out_k, req_k in (("zero", "up-50c"), ("zero", "steady"), ("up-50c", "zero")):
        c_o, u_o, _, _ = measure(outs[out_k].astype(np.float32).astype(np.float64))
        R["must_fail"][f"{out_k} output, {req_k} request"] = delivered(c_in, u_in, c_o, u_o, req[req_k])
    ok_ideal = all(v["passes"] for v in R["ideal"].values())
    ok_fail = not any(v["passes"] for v in R["must_fail"].values())
    R["check_of_check"] = dict(ideal_all_pass=ok_ideal, must_fail_all_fail=ok_fail)
    check(ok_ideal, "the rule passes the ideal renders")
    check(ok_fail, "the rule fails every must-fail case")
    # the builds: native, and both browsers twice each
    R["native"] = [json.loads(line) for line in (OUT / "native.jsonl").read_text().splitlines()]
    R["browsers"] = {}
    for b in ("chrome", "firefox"):
        p = OUT / f"{b}.json"
        if p.exists():
            R["browsers"][b] = json.loads(p.read_text())
    hashes = {}
    for b, d in R["browsers"].items():
        for row in d["rows"]:
            hashes.setdefault((row["input"], row["request"]), set()).update(row["f64_hashes"])
    R["same_everywhere"] = {f"{i} {q}": len(h) == 1 for (i, q), h in hashes.items()}
    f32 = {}
    for b, d in R["browsers"].items():
        for row in d["rows"]:
            f32.setdefault((row["input"], row["request"]), set()).update(row["f32_hashes"])
    R["same_everywhere_f32"] = {f"{i} {q}": len(h) == 1 for (i, q), h in f32.items()}
    # time and memory per browser and input: the faster of two passes, seconds per second of audio
    R["summary"] = {}
    for b, d in R["browsers"].items():
        for row in d["rows"]:
            e = R["summary"].setdefault(f"{b} {row['input']}", dict(seconds=row["seconds"], analysis_s=min(row["analysis_s"]),
                                        analysis_bytes=row["analysis_bytes"], wasm_memory_bytes=row["wasm_memory_bytes"],
                                        synth_s={}, vs_native_max_abs_diff={}))
            e["synth_s"][row["request"]] = min(row["synth_s"])
            e["vs_native_max_abs_diff"][row["request"]] = row["vs_native"]["max_abs_diff"]
    for e in R["summary"].values():
        e["analysis_s_per_s"] = e["analysis_s"] / e["seconds"]
        e["first_rung_s_per_s"] = (e["analysis_s"] + max(e["synth_s"].values())) / e["seconds"]
        e["further_rung_s_per_s"] = max(e["synth_s"].values()) / e["seconds"]
        e["analysis_mb_per_s"] = e["analysis_bytes"] / 1e6 / e["seconds"]
        e["wasm_memory_mb"] = e["wasm_memory_bytes"] / 1e6
    (OUT / "fold.json").write_text(json.dumps(R, indent=1))
    print(json.dumps({k: v for k, v in R.items() if k not in ("native", "browsers", "rule", "ideal", "must_fail")}, indent=1))


if __name__ == "__main__":
    {"gen": gen, "check": check_all}[sys.argv[1]](sys.argv[2])
