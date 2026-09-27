"""E-003 round 1: tables from results/runs.json and the readbacks, written
to results/summary.md and results/summary.json."""
import glob
import json
from collections import defaultdict

import numpy as np

runs = json.load(open("results/runs.json"))
versions = json.load(open("results/raw/versions.json"))
L = []
P = L.append


def rng(vals, fmt="{:.2f}"):
    vals = [v for v in vals if v is not None]
    if not vals:
        return "—"
    lo, hi = min(vals), max(vals)
    return fmt.format(lo) if fmt.format(lo) == fmt.format(hi) else f"{fmt.format(lo)} to {fmt.format(hi)}"


P("# E-003 round 1: summary\n")
P(f"Browsers: Chrome {versions.get('chrome')} (Playwright, channel `chrome`), "
  f"Firefox {versions.get('firefox')} (snap; Playwright over WebDriver BiDi, channel `moz-firefox`). "
  "Headless, on Linux (Ubuntu, PipeWire), i7-12700H. Fake capture only: Chrome's "
  "`--use-file-for-fake-audio-capture` with the probe WAV, Firefox's "
  "`media.navigator.streams.fake` (a 1 kHz tone). Ranges are over 3 runs of 12 s per condition.\n")

P("## 1. Readback (S-001)\n")
P("| Browser | Request | `echoCancellation` | `noiseSuppression` | `autoGainControl` | `channelCount` | `sampleRate` | Other |")
P("| :--- | :--- | :--- | :--- | :--- | ---: | ---: | :--- |")
summary = {"readback": {}, "signal": {}, "transport": {}}
for f in sorted(glob.glob("results/raw/*-readback*.json")):
    d = json.load(open(f))
    tag = f"{d['browser']}" + (f" (fake file {d['fakeRate']} Hz)" if d.get("fakeRate") else "")
    for req in ("raw", "default"):
        s = d[req]["settings"]
        other = []
        if req == "raw":
            if "afterExactMono" in d[req]:
                other.append(f"`applyConstraints` exact mono: channelCount {d[req]['afterExactMono'].get('channelCount')}")
            if "exactMonoError" in d[req]:
                other.append(f"`applyConstraints` exact mono: {d[req]['exactMonoError']}")
            if "exactMonoRequest" in d[req]:
                other.append(f"`getUserMedia` exact mono: channelCount {d[req]['exactMonoRequest'].get('channelCount')}")
            if "exactMonoRequestError" in d[req]:
                other.append(f"`getUserMedia` exact mono: {d[req]['exactMonoRequestError']}")
            caps = d[req].get("capabilities") or {}
            other.append("capabilities: " + ", ".join(f"{k} {json.dumps(caps.get(k))}" for k in ("echoCancellation", "autoGainControl", "sampleRate", "channelCount") if k in caps))
        else:
            a = d[req].get("afterApply")
            if a:
                other.append("after `applyConstraints` raw: EC {} NS {} AGC {}".format(a.get("echoCancellation"), a.get("noiseSuppression"), a.get("autoGainControl")))
            if d[req].get("applyError"):
                other.append(f"`applyConstraints`: {d[req]['applyError']}")
        fmt = lambda k: "not reported" if k not in s else f"`{json.dumps(s[k])}`"
        P(f"| {tag} | {'raw (ADR 0002)' if req == 'raw' else 'default (`audio: true`)'} | {fmt('echoCancellation')} | {fmt('noiseSuppression')} | {fmt('autoGainControl')} | {fmt('channelCount')} | {fmt('sampleRate')} | {'; '.join(other)} |")
        summary["readback"][f"{tag}/{req}"] = {"settings": s, "other": other}
P("")

P("## 2. Signal: what arrives at the worker (S-002)\n")
P("Measured against an ideal converter: the source loop itself at the same rate, else its exact "
  "band-limited (FFT) resampling. *Steps*: lag changes over 1 sample between 0.1 s windows, "
  "negative where samples were inserted into the capture, positive where dropped; *drift*: steady rate difference outside steps. "
  "Tone rows: 0.4 s of each of 110, 220, 440, 880 Hz; the worst over tones and runs. "
  "*Ideal SNR*: the window's energy over its residual after least-squares gain and fractional lag.\n")
P("| Browser | Path | Source → context (Hz) | Bit-exact windows | Steps per run (samples) | Drift (ppm) | Tone error (cents) | Tone THD+N (dB) | Ripple 80 Hz–8 kHz (dB) | Ripple 8–20 kHz (dB) | Alias / image (dB) | Ideal SNR, median (dB) | Ideal SNR, sweep < 8 kHz, min (dB) |")
P("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
groups = defaultdict(list)
for r in runs:
    c = r["condition"]
    if c["load"] != 0 and c["path"] == "mic":
        pass
    key = (r["browser"], c["path"], c.get("srcRate") or c.get("fakeRate"), c["ctxRate"])
    groups[key].append(r)
for key in sorted(groups, key=lambda k: (k[0], k[1], str(k[2]), k[3])):
    rs = [r for r in groups[key] if "signal" in r]
    b, pth, src, ctx = key
    if not rs:
        P(f"| {b} | {pth} | {src} → {ctx} | error: {groups[key][0].get('error') or groups[key][0].get('ctxError') or groups[key][0].get('sourceError')} | | | | | | | | | |")
        continue
    sig = [r["signal"] for r in rs]
    pname = {"mic": "fake microphone", "stream": "track from a second context"}[pth]
    if "tone_hz" in sig[0]:
        cents = [1200 * np.log2(s["freq_refined_hz"] / 1000.0) for s in sig]
        P(f"| {b} | {pname} (1 kHz tone) | 48000 (graph) → {ctx} | — | phase deviation max {rng([s['phase_dev_max_samples'] for s in sig])} samples | — | {rng(cents, '{:.3f}')} | {rng([s['tone_thdn_db'] for s in sig], '{:.1f}')} | — | — | — | — | — |")
        summary["signal"][f"{b}/{pth}/{src}->{ctx}"] = {"n_runs": len(sig), "tone_cents": [min(cents), max(cents)],
            "thdn_db": [min(s['tone_thdn_db'] for s in sig), max(s['tone_thdn_db'] for s in sig)],
            "phase_dev_max_samples": max(s['phase_dev_max_samples'] for s in sig)}
        continue
    ex = [s for s in sig if "exact_fraction" in s]
    exact = f"{sum(s['windows_fully_exact'] for s in ex)} of {sum(s['windows_checked_exact'] for s in ex)}" if ex else "— (rates differ)"
    if ex and sum(s['windows_fully_exact'] for s in ex) == 0:
        exact += f" (fraction of exact samples {rng([s['exact_fraction'] for s in ex])})"
    steps = "; ".join(("none" if not s["lag_steps"] else ", ".join(f"{st['samples']:+.0f}" if abs(st['samples']) >= 10 else f"{st['samples']:+.1f}" for st in s["lag_steps"])) for s in sig)
    tc = [t["cents"] for s in sig for t in s["tones"].values()]
    tcmax = max(abs(v) for v in tc) if tc else None
    th = [t["thdn_db"] for s in sig for t in s["tones"].values()]
    al = []
    for s in sig:
        if "alias_21100_db" in s:
            al.append(("alias", s["alias_21100_db"]))
        if "image_23100_db" in s:
            al.append(("image", s["image_23100_db"]))
    alias = "—" if not al else f"{al[0][0]} {rng([v for _, v in al], '{:.1f}')}"
    low = [s["window_snr_sweep_below_8k_db"]["min"] for s in sig if "window_snr_sweep_below_8k_db" in s]
    P(f"| {b} | {pname} | {src} → {ctx} | {exact} | {steps} | {rng([s['drift_ppm'] for s in sig], '{:.1f}')} | max abs {tcmax:.2g} | {rng(th, '{:.1f}')} | {rng([s.get('ripple_80_8k_db') for s in sig], '{:.3f}')} | {rng([s.get('ripple_8k_20k_db') for s in sig], '{:.3f}')} | {alias} | {rng([s['window_snr_db']['median'] for s in sig], '{:.1f}')} | {rng(low, '{:.1f}')} |")
    summary["signal"][f"{b}/{pth}/{src}->{ctx}"] = {
        "n_runs": len(sig), "exact": exact, "steps": [s["lag_steps"] for s in sig],
        "drift_ppm": [s["drift_ppm"] for s in sig], "tone_cents_max_abs": tcmax,
        "thdn_db": [min(th), max(th)] if th else None,
        "ripple_80_8k_db": max(s.get("ripple_80_8k_db", 0) for s in sig),
        "ripple_8k_20k_db": max(s.get("ripple_8k_20k_db", 0) for s in sig),
        "alias_or_image_db": al, "snr_median_db": [s["window_snr_db"]["median"] for s in sig],
        "snr_sweep_below_8k_min_db": low,
        "silence_exact_zero": [s.get("silence_exact_zero_fraction") for s in sig]}
P("")

P("## 3. Transport: worklet to worker, one message per 128-sample block (S-003)\n")
P("*Load*: CPU time the worker burns per block, as a fraction of the block period "
  "(2.667 ms at 48 kHz); *utilisation*: the service time actually measured over the period. "
  "*Arrival lag*: arrival time minus the block's audio time, less the smallest such value in the run. "
  "*Behind at end*: how far the worker's finished work trailed the audio when capture stopped.\n")
P("| Browser | Path | Context (Hz) | Load | Utilisation | Blocks | Lost | Reordered | Quanta skipped | Arrival lag p50 / p99 / max (ms) | Behind at end (ms) | Timer resolution (ms) |")
P("| :--- | :--- | ---: | ---: | :--- | :--- | ---: | ---: | ---: | :--- | :--- | :--- |")
tg = defaultdict(list)
for r in runs:
    if "transport" not in r:
        continue
    c = r["condition"]
    tg[(r["browser"], c["path"], c.get("srcRate") or c.get("fakeRate"), c["ctxRate"], c["load"])].append(r)
for key in sorted(tg, key=lambda k: (k[0], k[1], str(k[2]), k[3], k[4])):
    rs = tg[key]
    t = [r["transport"] for r in rs]
    b, pth, src, ctx, load = key
    P(f"| {b} | {pth} {src or ''} | {ctx} | {load:.2f} | {rng([x['utilisation'] for x in t])} | {rng([x['blocks'] for x in t], '{:.0f}')} | {sum(x['lost'] for x in t)} | {sum(x['reordered'] for x in t)} | {sum(x['quanta_skipped'] for x in t)} | "
      f"{rng([x['arrival_lag_ms']['p50'] for x in t], '{:.1f}')} / {rng([x['arrival_lag_ms']['p99'] for x in t], '{:.1f}')} / {rng([x['arrival_lag_ms']['max'] for x in t], '{:.1f}')} | {rng([x['behind_end_ms'] for x in t], '{:.0f}')} | {rng([x.get('timerRes') for x in t], '{:.3f}')} |")
    summary["transport"][f"{b}/{pth}/{src}/{ctx}/{load}"] = t
P("")
open("results/summary.md", "w").write("\n".join(L))
json.dump(summary, open("results/summary.json", "w"), indent=1, default=float)
print("\n".join(L))
