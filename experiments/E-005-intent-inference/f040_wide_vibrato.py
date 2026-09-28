"""F-040's numbers re-derived into a results file (squillo iteration 43, F-043 m).
Crude experiment code; adds to fold_refusal.py, never replaces it.

    uv run python f040_wide_vibrato.py      # -> results/f040_wide_vibrato.json

Squillo F-040 states that squillo's take-vibrato-in-tune.wav, built at +-50
cents instead of its +-35, gave "98 segments for 14 notes, u 36.6 cents,
state at least" (iteration 38), but no results file held those numbers.
This builds the same take with fold_refusal.py's own generator
(take_sample, note_freq; fold_refusal.py:406-425), changing only VIB_BETA,
and measures it with the same pipeline (track with MT-003's refusal,
measure with the centre over whole vibrato cycles; fold_refusal.py:62-83).

Conditions, written before generating (S15):
- The vibrato is fold_refusal.py's f(t) = f_j (1 + beta sin(2 pi 5.5 t)); a
  take named by A has beta = 2^(A/1200) - 1, so it reaches +A cents and
  -1200 log2(1 - beta) below, both computed from beta and reported.
- A in {30, fixture beta 0.0204, 36 to 45 by 1, 50}; every frequency
  inside E2..C6 at the formula's extremes, asserted as fold_refusal.py does.
- A second model, symmetric in cents, for A = 45 and 50 (the "+-50" of F-040
  may have meant it): f(t) = f_j 2^(A sin(2 pi 5.5 t) / 1200), its phase the
  running sum of f / 48000 from the note's first sample, the note's ramps and
  gaps as take_sample's; its extremes are +-A exactly.
- 14 notes, all in tune (deviation 0), 800 ms each (38 400 samples), as the fixture.
Checks, each checked:
- Must pass: with the fixture's beta the generated take is byte-identical to
  the committed fixture (sha256 in results/fold_refusal_fixtures.json), gives
  14 segments, and its state and s match that file.
- Must fail: the "split" test (segments > 14) is false on the fixture and must
  be true on at least one take above 38.3 cents, where J0(pi A / 50) < 0.

Revised in squillo iteration 47 (F-050 a, S15 as revised by L-041):
- The last must-fail case took its expectation from F-040's own claim (J0
  turns negative above 38.3 cents), so it is kept as a reported result, not
  a check. The split test's must-fail case is now a take whose count is
  known by construction: 15 notes, the 14 of the fixture's melody (its
  pitches, 800 ms, ramps and gaps, no vibrato) and a fifteenth, the last
  note again a whole tone higher. The split test must be true on it; its
  must-pass case is the 14-note take with no vibrato, where it must be false.
- Each take's extremes are asserted on its output: the generator's exact
  phase formula (fold_refusal.py:423-425, or build_cents's) is evaluated on
  the sample grid and must reproduce every generated sample within 1e-9;
  the extremes of its derivative, the instantaneous frequency, are then
  taken over the grid and must be +A (and the model's lower extreme) within
  0.01 cents and inside E2..C6.
- The take's structure is asserted on its output: a leading gap, then 14
  runs of non-zero samples, each at most 38 400 samples and at least
  38 398 (a note's first sample is zero, sin 0, and its last may be), each
  followed by a gap of at least 4 800 zero samples. This assertion is
  checked on two takes it must refuse: the 36-cent take's samples called
  the fixture, and the 15-note take called 14 notes.
"""
import hashlib
import json
import math

import numpy as np
from scipy.special import j0

import fold_refusal as FR
import round2 as R2
import infer

OUT = FR.OUT


def build(beta):
    FR.VIB_BETA = beta  # take_sample reads the module global
    devs, note = [0.0] * 14, 38_400
    fr = [FR.note_freq(j, d) for j, d in enumerate(devs)]
    E2, C6 = 440 * 2 ** (R2.E2_CENTS / 1200), 440 * 2 ** (R2.C6_CENTS / 1200)
    assert E2 <= min(fr) * (1 - beta) and max(fr) * (1 + beta) <= C6, beta
    N = FR.GAP + 14 * (note + FR.GAP)
    xs = [FR.take_sample(n, devs, note, True) for n in range(N)]
    blob = FR.wav(xs)
    return xs, blob


def build_cents(A):
    devs, note = [0.0] * 14, 38_400
    E2, C6 = 440 * 2 ** (R2.E2_CENTS / 1200), 440 * 2 ** (R2.C6_CENTS / 1200)
    fr = [FR.note_freq(j, d) for j, d in enumerate(devs)]
    assert E2 <= min(fr) * 2 ** (-A / 1200) and max(fr) * 2 ** (A / 1200) <= C6, A
    m = np.arange(note)
    g = np.ones(note)
    g[:FR.RAMP] = 0.5 - 0.5 * np.cos(np.pi * m[:FR.RAMP] / FR.RAMP)
    tail = m >= note - FR.RAMP
    g[tail] = 0.5 - 0.5 * np.cos(np.pi * (note - m[tail]) / FR.RAMP)
    xs = [0.0] * FR.GAP
    for j in range(14):
        f = fr[j] * 2 ** (A * np.sin(2 * np.pi * FR.VIB_RATE * m / 48000) / 1200)
        ph = 2 * np.pi * np.concatenate([[0.0], np.cumsum(f[:-1])]) / 48000
        xs += list(0.5 * g * np.sin(ph)) + [0.0] * FR.GAP
    assert len(xs) == FR.GAP + 14 * (note + FR.GAP)
    return xs, FR.wav(xs)


def model(kind, par, freqs=None, vib=True):
    """The exact samples and instantaneous frequency (Hz) per note of a take, on
    the sample grid, from the generator's formula (take_sample, fold_refusal.py:
    409-426; build_cents above)."""
    note = 38_400
    fr = freqs if freqs is not None else [FR.note_freq(j, 0.0) for j in range(14)]
    m = np.arange(note)
    g = np.ones(note)
    g[:FR.RAMP] = 0.5 - 0.5 * np.cos(np.pi * m[:FR.RAMP] / FR.RAMP)
    tail = m >= note - FR.RAMP
    g[tail] = 0.5 - 0.5 * np.cos(np.pi * (note - m[tail]) / FR.RAMP)
    xs, inst = [np.zeros(FR.GAP)], []
    for f in fr:
        if not vib:
            ph, fi = 2 * np.pi * f * m / 48000, np.full(note, f)
        elif kind == "beta":
            ph = 2 * np.pi * f * m / 48000 + f * par / FR.VIB_RATE * (1 - np.cos(2 * np.pi * FR.VIB_RATE * m / 48000))
            fi = f * (1 + par * np.sin(2 * np.pi * FR.VIB_RATE * m / 48000))
        else:
            fi = f * 2 ** (par * np.sin(2 * np.pi * FR.VIB_RATE * m / 48000) / 1200)
            ph = 2 * np.pi * np.concatenate([[0.0], np.cumsum(fi[:-1])]) / 48000
        xs += [0.5 * g * np.sin(ph), np.zeros(FR.GAP)]
        inst.append(fi)
    return np.concatenate(xs), fr, inst


def assert_take(xs, kind, par, up, down, n_notes=14, freqs=None, vib=True):
    """S15 on the output: the samples are the formula's, the extremes are the
    take's name, every frequency inside E2..C6, and the structure is n notes."""
    x = np.asarray(xs, float)
    ref, fr, inst = model(kind, par, freqs, vib)
    assert len(x) == len(ref) == FR.GAP + n_notes * (38_400 + FR.GAP), len(x)
    err = float(np.abs(x - ref).max())
    assert err < 1e-9, err
    E2, C6 = 440 * 2 ** (R2.E2_CENTS / 1200), 440 * 2 ** (R2.C6_CENTS / 1200)
    hi = max(float(1200 * np.log2(fi.max() / f)) for f, fi in zip(fr, inst))
    lo = max(float(-1200 * np.log2(fi.min() / f)) for f, fi in zip(fr, inst))
    assert abs(hi - up) < 0.01 and abs(lo - down) < 0.01, (hi, lo, up, down)
    fmin, fmax = min(float(fi.min()) for fi in inst), max(float(fi.max()) for fi in inst)
    assert E2 <= fmin and fmax <= C6, (fmin, fmax)
    nz = np.flatnonzero(x != 0)
    runs = np.split(nz, np.flatnonzero(np.diff(nz) > 1) + 1)
    lens = [int(r[-1] - r[0] + 1) for r in runs]
    gaps = [int(runs[i + 1][0] - runs[i][-1] - 1) for i in range(len(runs) - 1)]
    assert len(runs) == n_notes and all(38_398 <= L <= 38_400 for L in lens), (len(runs), lens)
    assert runs[0][0] >= FR.GAP and all(gp >= FR.GAP for gp in gaps), gaps
    assert len(x) - 1 - runs[-1][-1] >= FR.GAP
    return dict(err_vs_formula=err, grid_cents_up=round(hi, 4), grid_cents_down=round(lo, 4),
                f_min_hz=round(fmin, 3), f_max_hz=round(fmax, 3), notes_found=len(runs),
                note_len_min=min(lens), note_len_max=max(lens), gap_min=min(gaps))


def build_plain(freqs):
    """No vibrato, any list of notes, fold_refusal's ramps and gaps: the split
    test's must-pass (14 notes) and must-fail (15 notes) inputs."""
    x, _, _ = model("beta", 0.0, freqs, vib=False)
    return list(x), FR.wav(list(x))


def measure_blob(blob, path="/tmp/e005-f040.wav"):
    import soundfile as sf
    open(path, "wb").write(blob)
    x, sr = sf.read(path, dtype="float32")
    assert sr == FR.SR
    t, c, dmin, n_ref = FR.track(x)
    segs = R2.est_segments(c)
    ok = c[~np.isnan(c)]
    r0 = float(infer.circ_mean(ok, np.ones(len(ok))))
    sp = FR.measure(c, t)[0]
    fin = np.isfinite(sp["s"])
    return dict(segments=len(segs), refused=n_ref, provisional_tuning_cents=round(r0, 3),
                state=FR.state(sp), s=round(float(sp["s"]), 3) if fin else None,
                uB=round(float(sp["uB"]), 3) if fin and np.isfinite(sp["uB"]) else None)


def main():
    fx = json.loads((OUT / "fold_refusal_fixtures.json").read_text())["fixtures"]["take-vibrato-in-tune.wav"]
    fixture_beta = 0.0204
    # the split test checked first, on inputs whose note count is known by construction
    f14 = [FR.note_freq(j, 0.0) for j in range(14)]
    f15 = f14 + [f14[-1] * 2 ** (200 / 1200)]
    xs14, b14 = build_plain(f14)
    xs15, b15 = build_plain(f15)
    a14 = assert_take(xs14, "beta", 0.0, 0.0, 0.0, 14, f14, vib=False)
    a15 = assert_take(xs15, "beta", 0.0, 0.0, 0.0, 15, f15, vib=False)
    m14, m15 = measure_blob(b14), measure_blob(b15)
    split_check = dict(
        must_pass_14_plain=dict(asserted=a14, segments=m14["segments"], splits=m14["segments"] > 14),
        must_fail_15_plain=dict(asserted=a15, segments=m15["segments"], splits=m15["segments"] > 14),
        inputs_differ=b14 != b15)
    print("split test checked:", {k: v["segments"] if isinstance(v, dict) else v for k, v in split_check.items()}, flush=True)
    assert split_check["inputs_differ"]
    assert not split_check["must_pass_14_plain"]["splits"], "split test must be false on 14 plain notes"
    assert split_check["must_fail_15_plain"]["splits"], "split test must be true on 15 plain notes"
    # assert_take checked too: it must raise on a take that is not what it is
    # called (the 36-cent take called the fixture; the 15 notes called 14)
    fails = {}
    for name, args in (("36_called_fixture", (build(2 ** (36 / 1200) - 1)[0], "beta", fixture_beta,
                                                1200 * math.log2(1 + fixture_beta), -1200 * math.log2(1 - fixture_beta))),
                       ("15_called_14", (xs15, "beta", 0.0, 0.0, 0.0, 14, f14, False))):
        try:
            assert_take(*args)
            fails[name] = False
        except AssertionError:
            fails[name] = True
    split_check["assert_take_must_fail"] = fails
    print("assert_take must-fail:", fails, flush=True)
    assert all(fails.values()), fails
    rows = {}
    for label, beta in [("30", 2 ** (30 / 1200) - 1), ("fixture", fixture_beta)] + \
            [(str(a), 2 ** (a / 1200) - 1) for a in (36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 50)]:
        xs, blob = build(beta)
        up, down = 1200 * math.log2(1 + beta), -1200 * math.log2(1 - beta)
        chk = assert_take(xs, "beta", beta, up, down)
        r = dict(beta=beta, cents_up=round(up, 3), cents_down=round(down, 3), asserted=chk,
                 j0_at_mean_extent=round(float(j0(math.pi * (up + down) / 2 / 50)), 4),
                 sha256=hashlib.sha256(blob).hexdigest()) | measure_blob(blob)
        r["splits"] = r["segments"] > 14
        rows[label] = r
        print(label, {k: r[k] for k in ("cents_up", "cents_down", "segments", "provisional_tuning_cents", "state", "s", "uB")}, flush=True)
    for A in (45, 50):
        xs, blob = build_cents(A)
        chk = assert_take(xs, "cents", A, A, A)
        r = dict(model="cents", cents_up=float(A), cents_down=float(A), asserted=chk,
                 j0_at_mean_extent=round(float(j0(math.pi * A / 50)), 4),
                 sha256=hashlib.sha256(blob).hexdigest()) | measure_blob(blob)
        r["splits"] = r["segments"] > 14
        rows[f"cents {A}"] = r
        print(f"cents {A}", {k: r[k] for k in ("segments", "provisional_tuning_cents", "state", "s", "uB")}, flush=True)
    f = rows["fixture"]
    checks = dict(
        fixture_byte_identical=f["sha256"] == fx["sha256"],
        fixture_14_segments=f["segments"] == 14,
        fixture_state_and_s_match=f["state"] == fx["state"] and f["s"] == fx["s"],
        split_test_false_on_fixture=not f["splits"],
        split_test_false_on_14_plain=not split_check["must_pass_14_plain"]["splits"],
        split_test_true_on_15_plain=split_check["must_fail_15_plain"]["splits"],
        assert_take_fails_when_it_must=all(fails.values()))
    # F-040's own claim, reported as a result, not a check (F-050 a)
    claim = dict(splits_above_38_3=any(r["splits"] for r in rows.values() if r["cents_up"] > 38.3),
                 first_splitting_up_cents=min((r["cents_up"] for r in rows.values() if r["splits"]), default=None),
                 last_whole_up_cents=max((r["cents_up"] for r in rows.values() if not r["splits"]), default=None))
    res = dict(rows=rows, checks=checks, split_check=split_check, f040_claim_result=claim, fixture_committed=dict(sha256=fx["sha256"], state=fx["state"], s=fx["s"]))
    (OUT / "f040_wide_vibrato.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(checks, indent=1))
    assert all(checks.values()), checks


if __name__ == "__main__":
    main()
