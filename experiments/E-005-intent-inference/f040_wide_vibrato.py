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
    rows = {}
    for label, beta in [("30", 2 ** (30 / 1200) - 1), ("fixture", fixture_beta)] + \
            [(str(a), 2 ** (a / 1200) - 1) for a in (36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 50)]:
        _, blob = build(beta)
        up, down = 1200 * math.log2(1 + beta), -1200 * math.log2(1 - beta)
        r = dict(beta=beta, cents_up=round(up, 3), cents_down=round(down, 3),
                 j0_at_mean_extent=round(float(j0(math.pi * (up + down) / 2 / 50)), 4),
                 sha256=hashlib.sha256(blob).hexdigest()) | measure_blob(blob)
        r["splits"] = r["segments"] > 14
        rows[label] = r
        print(label, {k: r[k] for k in ("cents_up", "cents_down", "segments", "provisional_tuning_cents", "state", "s", "uB")}, flush=True)
    for A in (45, 50):
        _, blob = build_cents(A)
        r = dict(model="cents", cents_up=float(A), cents_down=float(A),
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
        split_test_true_above_38_3=any(r["splits"] for r in rows.values() if r["cents_up"] > 38.3))
    res = dict(rows=rows, checks=checks, fixture_committed=dict(sha256=fx["sha256"], state=fx["state"], s=fx["s"]))
    (OUT / "f040_wide_vibrato.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(checks, indent=1))
    assert all(checks.values()), checks


if __name__ == "__main__":
    main()
