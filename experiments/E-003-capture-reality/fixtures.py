"""Capture-trace fixtures for squillo's `capture` spec (squillo iteration 32, F-027;
iteration 43, F-039: events-start-after-load.json, and the model opening only at
the singer's start and releasing at the run's end, CA-010; iteration 46, F-049:
events-start-processed.json, and the model's notices, CA-005 and CA-009).

Crude and disposable, like everything here. Writes JSON capture traces:
readbacks taken from round 1's recorded runs (identifiers removed) and small
constructed block and event traces. Asserts every condition each fixture
must meet (squillo S15), runs a toy model of the `capture` requirements on
every fixture, and checks each check on a must-pass and a must-fail case.

    uv run python fixtures.py <out-dir>      # e.g. ../../../squillo/fixtures/capture
"""
import copy
import hashlib
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).parent
RUNS = json.loads((HERE / "results/runs.json").read_text())
READBACKS = HERE / "results/raw"
IDENTIFIERS = ("deviceId", "groupId")          # never in a fixture (RU-007, ADR 0014)
FLAGS = ("echoCancellation", "noiseSuppression", "autoGainControl")
OTHER_PROCESSING = ("voiceIsolation",)          # reported by Chrome 154; off unless reported on
Q = 128                                         # render quantum (ADR 0002)
RATE = 48000


def run(name):
    [r] = [x for x in RUNS if x["name"] == name]  # S16: named in advance, exactly one
    return r


def strip(settings):
    return {k: v for k, v in settings.items() if k not in IDENTIFIERS}


def f32_exact(x):
    return struct.unpack("<f", struct.pack("<f", x))[0] == x


# ---------------------------------------------------------------- the fixtures
def readback_fixture(source, browser, version, settings, ctx):
    return {"trace_version": 1, "source": source, "browser": browser, "version": version,
            "settings": strip(settings), "context_sample_rate": ctx, "events": []}


def block(frame, channels):
    return {"type": "block", "frame": frame, "channels": channels}


def ramp(k0):
    # exact binary fractions, in f32 and in decimal: 3 * (k - 64) / 128 for k = 0..127
    return [3 * ((k0 + k) % Q - 64) / 128 for k in range(Q)]


def make():
    fx = {}
    c = run("chrome-mic-fake44100-ctx48000-load0-r0")
    fx["readback-chrome-raw.json"] = readback_fixture(
        f"squillo-lab E-003 results/runs.json, run {c['name']}", "chrome", c["version"],
        c["settings"], c["ctxRate"])
    f = run("firefox-mic-fake-ctx48000-load0-r0")
    fx["readback-firefox-raw.json"] = readback_fixture(
        f"squillo-lab E-003 results/runs.json, run {f['name']}", "firefox", f["version"],
        f["settings"], f["ctxRate"])
    s = run("firefox-stream-fake-src44100-ctx48000-load0-r0")
    fx["readback-flags-unreported.json"] = readback_fixture(
        f"squillo-lab E-003 results/runs.json, run {s['name']} (a stream track, no microphone)",
        "firefox", s["version"], s["settings"], s["ctxRate"])
    d = json.loads((READBACKS / "chrome-readback-44100.json").read_text())
    fx["readback-chrome-processed.json"] = readback_fixture(
        "squillo-lab E-003 results/raw/chrome-readback-44100.json, member default.settings "
        "(the microphone opened with no processing constraints); context_sample_rate 48000 "
        "written for this fixture", "chrome", d["version"], d["default"]["settings"], RATE)
    m = run("chrome-mic-fake44100-ctx44100-load0-r0")
    fx["context-rate-44100.json"] = readback_fixture(
        f"squillo-lab E-003 results/runs.json, run {m['name']}", "chrome", m["version"],
        m["settings"], m["ctxRate"])

    # constructed traces, all on the Chrome raw readback
    base = fx["readback-chrome-raw.json"]
    ch0 = [ramp(0), ramp(32), ramp(64)]
    two = copy.deepcopy(base)
    two["source"] = "constructed; readback as readback-chrome-raw.json"
    two["events"] = [block(i * Q, [ch0[i], [-x for x in ch0[i]]]) for i in range(3)] + \
        [{"type": "singer-stop"}]
    fx["blocks-two-channels.json"] = two

    def events(tail, frames=(0, 128, 256, 384, 512), after=()):
        t = copy.deepcopy(base)
        t["source"] = "constructed; readback as readback-chrome-raw.json"
        ev = [block(fr, [ramp(i), ramp(i)]) for i, fr in enumerate(frames)]
        t["events"] = ev + list(tail) + [block(fr, [ramp(9), ramp(9)]) for fr in after]
        return t

    fx["events-singer-stop.json"] = events([{"type": "singer-stop"}])
    fx["events-track-ended.json"] = events([{"type": "track-ended"}], after=(640, 768))
    fx["events-track-muted.json"] = events([{"type": "track-muted"}], after=(640, 768))
    fx["events-context-suspended.json"] = events(
        [{"type": "context-state", "state": "suspended"}], after=(640, 768))
    fx["events-quantum-skipped.json"] = events([{"type": "singer-stop"}],
                                               frames=(0, 128, 256, 512, 640))
    eng = copy.deepcopy(base)
    eng["source"] = "constructed; readback as readback-chrome-raw.json"
    eng["events"] = [{"type": "engine-failed"}]
    fx["events-engine-failed.json"] = eng
    # iteration 43 (CA-010): the singer-stop trace, preceded by the page's load and the singer's start
    sal = events([{"type": "singer-stop"}])
    sal["source"] = ("constructed; readback as readback-chrome-raw.json; as events-singer-stop.json, "
                     "preceded by page-loaded and singer-start")
    sal["events"] = [{"type": "page-loaded"}, {"type": "singer-start"}] + sal["events"]
    fx["events-start-after-load.json"] = sal
    # iteration 46 (F-049): the same start trace under the processed readback
    sp = copy.deepcopy(sal)
    pr = fx["readback-chrome-processed.json"]
    sp["source"] = ("constructed; readback as readback-chrome-processed.json; events as "
                    "events-start-after-load.json")
    sp["settings"], sp["context_sample_rate"] = copy.deepcopy(pr["settings"]), pr["context_sample_rate"]
    fx["events-start-processed.json"] = sp
    return fx


# ------------------------------------------------ a toy model of the `capture` spec
def tier(settings):
    """CA-003: raw only when every one of the three flags is reported false and no
    other processing setting is reported true. The channel count and rates play no part."""
    if any(settings.get(k) is not False for k in FLAGS):
        return "not-raw"
    if any(settings.get(k) is True for k in OTHER_PROCESSING):
        return "not-raw"
    return "raw"


def model(t):
    """What capture does with a trace: start or refuse, the tier, the blocks it
    delivers (first channel), and whether and after which block it reports the input ended."""
    if any(e["type"] == "engine-failed" for e in t["events"]):
        return {"started": False, "why": "engine"}
    if t["context_sample_rate"] != RATE:
        return {"started": False, "why": "rate"}
    out = {"started": True, "tier": tier(t["settings"]),
           "track_rate": t["settings"].get("sampleRate", "not reported"),
           "delivered": [], "ended": None, "released": False}
    # CA-010: a trace with the singer's start opens nothing before it; one without
    # starts at the singer's start implicitly, as every iteration-32 trace
    gated = any(e["type"] == "singer-start" for e in t["events"])
    out["opened_on"] = "singer-start" if gated else "trace-start"
    opened = not gated
    # F-049: the capture condition needs no readback, so it is told at the page's load,
    # nothing opened; the processing notice needs the readback, so it is told in the
    # singer's start, once the microphone is open and before any block is delivered.
    # [notice, when]: when is page-loaded, trace-start, or the blocks delivered so far
    out["notices"] = []

    def opening():
        if not out["notices"]:
            out["notices"].append(["capture-condition", "trace-start"])
        if out["tier"] == "not-raw":
            out["notices"].append(["processing", len(out["delivered"])])

    if not gated:
        opening()
    last = None
    for e in t["events"]:
        if e["type"] == "page-loaded":
            out["notices"].append(["capture-condition", "page-loaded"])
            continue
        if e["type"] == "singer-start":
            opened = True
            opening()
            continue
        if not opened:
            out["opened_before_start"] = e["type"]
            break
        if e["type"] == "block":
            if last is not None and e["frame"] != last + Q:
                out["ended"] = ("quantum-skipped", len(out["delivered"]))
                break
            out["delivered"].append(list(e["channels"][0]))
            last = e["frame"]
        elif e["type"] == "singer-stop":
            out["released"] = True
            break
        else:  # track-ended, track-muted, a context state other than running
            out["ended"] = (e["type"], len(out["delivered"]))
            out["released"] = True
            break
    if out["ended"] and out["ended"][0] == "quantum-skipped":
        out["released"] = True
    return out


# ----------------------------------------------------------- conditions (S15)
def conditions(fx):
    rows = []

    def check(name, ok, what):
        rows.append({"fixture": name, "check": what, "ok": bool(ok)})
        assert ok, f"{name}: {what}"

    for name, t in fx.items():
        check(name, not any(k in t["settings"] for k in IDENTIFIERS), "no device identifier")
        for e in t["events"]:
            if e["type"] == "block":
                check(name, all(len(ch) == Q for ch in e["channels"]), "every channel 128 samples")
                check(name, all(f32_exact(x) for ch in e["channels"] for x in ch),
                      "every sample exact in f32")
    # each derived readback equals its recorded source, identifiers aside
    for name, src in (("readback-chrome-raw.json", "chrome-mic-fake44100-ctx48000-load0-r0"),
                      ("readback-firefox-raw.json", "firefox-mic-fake-ctx48000-load0-r0"),
                      ("readback-flags-unreported.json", "firefox-stream-fake-src44100-ctx48000-load0-r0"),
                      ("context-rate-44100.json", "chrome-mic-fake44100-ctx44100-load0-r0")):
        check(name, fx[name]["settings"] == strip(run(src)["settings"]), "settings as recorded")
        check(name, fx[name]["context_sample_rate"] == run(src)["ctxRate"], "context rate as recorded")
    t = fx["readback-chrome-raw.json"]["settings"]
    check("readback-chrome-raw.json", all(t[k] is False for k in FLAGS) and t["channelCount"] == 2
          and t["sampleRate"] != RATE, "flags off, 2 channels, track rate not 48000")
    t = fx["readback-firefox-raw.json"]["settings"]
    check("readback-firefox-raw.json", all(t[k] is False for k in FLAGS) and "sampleRate" not in t,
          "flags off, no track rate reported")
    check("readback-flags-unreported.json",
          not any(k in fx["readback-flags-unreported.json"]["settings"] for k in FLAGS),
          "no flag reported")
    t = fx["readback-chrome-processed.json"]["settings"]
    check("readback-chrome-processed.json", all(t[k] is True for k in FLAGS), "all three flags on")
    two = [e for e in fx["blocks-two-channels.json"]["events"] if e["type"] == "block"]
    check("blocks-two-channels.json", all(e["channels"][0] != e["channels"][1] for e in two),
          "the two channels differ in every block")
    xs = [x for e in two for x in e["channels"][0]]
    check("blocks-two-channels.json", max(xs) > 1 and min(xs) < -1, "first channel beyond [-1, 1] both ways")
    frames = [e["frame"] for e in fx["events-quantum-skipped.json"]["events"] if e["type"] == "block"]
    steps = [b - a for a, b in zip(frames, frames[1:])]
    check("events-quantum-skipped.json", steps.count(Q) == len(steps) - 1 and steps.count(2 * Q) == 1,
          "exactly one quantum skipped")
    sal, stop = fx["events-start-after-load.json"]["events"], fx["events-singer-stop.json"]["events"]
    check("events-start-after-load.json", [e["type"] for e in sal[:2]] == ["page-loaded", "singer-start"]
          and sal[2:] == stop, "page-loaded, singer-start, then events-singer-stop.json's events unchanged")
    # iteration 46 (F-049): the processed start trace is events-start-after-load.json's events
    # under readback-chrome-processed.json's settings and context rate
    sp = fx["events-start-processed.json"]
    check("events-start-processed.json", sp["events"] == sal
          and sp["settings"] == fx["readback-chrome-processed.json"]["settings"]
          and sp["context_sample_rate"] == fx["readback-chrome-processed.json"]["context_sample_rate"],
          "events-start-after-load.json's events under readback-chrome-processed.json's readback")
    check("events-start-processed.json", tier(sp["settings"]) == "not-raw"
          and all(sp["settings"][k] is True for k in FLAGS), "all three flags on")
    for name in ("events-singer-stop.json", "events-track-ended.json", "events-track-muted.json",
                 "events-context-suspended.json", "blocks-two-channels.json", "events-start-after-load.json",
                 "events-start-processed.json"):
        fr = [e["frame"] for e in fx[name]["events"] if e["type"] == "block"]
        check(name, all(b - a == Q for a, b in zip(fr, fr[1:])), "every quantum consecutive")
    return rows


EXPECTED = {  # written from the spec's scenarios before the model ran
    "readback-chrome-raw.json": {"started": True, "tier": "raw", "track_rate": 44100},
    "readback-firefox-raw.json": {"started": True, "tier": "raw", "track_rate": "not reported"},
    "readback-flags-unreported.json": {"started": True, "tier": "not-raw"},
    "readback-chrome-processed.json": {"started": True, "tier": "not-raw"},
    "context-rate-44100.json": {"started": False, "why": "rate"},
    "blocks-two-channels.json": {"started": True, "tier": "raw", "ended": None, "n": 3},
    "events-singer-stop.json": {"started": True, "ended": None, "n": 5},
    "events-track-ended.json": {"started": True, "ended": ("track-ended", 5), "n": 5, "released": True},
    "events-track-muted.json": {"started": True, "ended": ("track-muted", 5), "n": 5},
    "events-context-suspended.json": {"started": True, "ended": ("context-state", 5), "n": 5},
    "events-quantum-skipped.json": {"started": True, "ended": ("quantum-skipped", 3), "n": 3},
    "events-engine-failed.json": {"started": False, "why": "engine"},
    # iteration 43, CA-010's scenarios, written before the model ran
    "events-start-after-load.json": {"started": True, "ended": None, "n": 5, "opened_on": "singer-start",
                                     "opened_before_start": None, "released": True,
                                     "notices": [["capture-condition", "page-loaded"]]},
    # iteration 46 (F-049), CA-005's and CA-009's scenarios, written and committed before the model ran:
    # the capture condition told at the page's load, with nothing opened; the processing
    # notice told in the singer's start, after the readback and before the first block
    "events-start-processed.json": {"started": True, "tier": "not-raw", "ended": None, "n": 5,
                                    "opened_on": "singer-start", "opened_before_start": None,
                                    "released": True,
                                    "notices": [["capture-condition", "page-loaded"], ["processing", 0]]},
    "readback-chrome-raw.json#notices": [["capture-condition", "trace-start"]],
    "readback-chrome-processed.json#notices": [["capture-condition", "trace-start"], ["processing", 0]],
}


def outcomes(fx):
    rows = []
    for name, t in fx.items():
        got = model(t)
        exp = EXPECTED[name]
        ok = all((len(got["delivered"]) if k == "n" else got.get(k)) == v for k, v in exp.items())
        if name + "#notices" in EXPECTED:
            exp = exp | {"notices": EXPECTED[name + "#notices"]}
            ok = ok and got.get("notices") == exp["notices"]
        if name == "blocks-two-channels.json":
            first = [e["channels"][0] for e in t["events"] if e["type"] == "block"]
            ok = ok and got["delivered"] == first
        rows.append({"fixture": name, "expected": {k: v for k, v in exp.items()},
                     "model": {k: v for k, v in got.items() if k != "delivered"} |
                     {"blocks_delivered": len(got.get("delivered", []))}, "ok": ok})
        assert ok, (name, got, exp)
    return rows


def check_the_checks():
    """S15: each check once on a case it must pass and once on one it must fail,
    each known independently of the check."""
    rows = []
    # tier: E-003's Chrome default readback has all three on (must be not raw);
    # its raw readback has all three off (must be raw)
    d = json.loads((READBACKS / "chrome-readback-44100.json").read_text())
    rows.append(("tier raw on Chrome's raw readback", tier(d["raw"]["settings"]) == "raw"))
    rows.append(("tier not raw on Chrome's default readback", tier(d["default"]["settings"]) == "not-raw"))
    one_missing = {k: False for k in FLAGS}
    del one_missing["autoGainControl"]
    rows.append(("tier not raw with one flag unreported", tier(one_missing) == "not-raw"))
    rows.append(("tier not raw with voice isolation on", tier({**{k: False for k in FLAGS}, "voiceIsolation": True}) == "not-raw"))
    # gap detection: consecutive must pass, a skipped quantum must be caught
    base = {"context_sample_rate": RATE, "settings": {}, "events": []}
    ok = dict(base, events=[block(i * Q, [[0.0] * Q]) for i in range(3)])
    bad = dict(base, events=[block(f, [[0.0] * Q]) for f in (0, 128, 384)])
    rows.append(("no gap reported on consecutive quanta", model(ok)["ended"] is None))
    rows.append(("gap reported on a skipped quantum", model(bad)["ended"] == ("quantum-skipped", 2)))
    # CA-010: a block before the singer's start must be caught; one after must not
    st = [{"type": "page-loaded"}, {"type": "singer-start"}] + [block(i * Q, [[0.0] * Q]) for i in range(2)]
    early = [{"type": "page-loaded"}, block(0, [[0.0] * Q]), {"type": "singer-start"}, block(Q, [[0.0] * Q])]
    rows.append(("nothing opened before the start when blocks follow it", model(dict(base, events=st)).get("opened_before_start") is None))
    rows.append(("a block before the start is caught", model(dict(base, events=early)).get("opened_before_start") == "block"))
    rows.append(("released at the singer's stop", model(dict(base, events=st + [{"type": "singer-stop"}]))["released"]))
    rows.append(("not released while the run goes on", not model(dict(base, events=st))["released"]))
    # F-049: the processing notice before the first block, on a processed readback;
    # none on a raw one (a must-fail case differing in its input, L-041); and a notice
    # told only after a block is caught as such
    proc = {"context_sample_rate": RATE, "settings": d["default"]["settings"], "events": st}
    raw = {"context_sample_rate": RATE, "settings": d["raw"]["settings"], "events": st}
    rows.append(("processing notice before the first block on a processed readback",
                 ["processing", 0] in model(proc)["notices"]))
    rows.append(("no processing notice on a raw readback",
                 not any(n[0] == "processing" for n in model(raw)["notices"])))
    rows.append(("capture condition at the page's load, before the start",
                 model(proc)["notices"][0] == ["capture-condition", "page-loaded"]))
    rows.append(("capture condition not at the load on a trace with no load",
                 model(dict(proc, events=st[1:]))["notices"][0] == ["capture-condition", "trace-start"]))
    # f32 exactness: 0.75 is exact, 0.1 is not
    rows.append(("f32_exact(0.75)", f32_exact(0.75)))
    rows.append(("not f32_exact(0.1)", not f32_exact(0.1)))
    for what, good in rows:
        assert good, what
    return [{"check": w, "ok": g} for w, g in rows]


def dump(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    checks = check_the_checks()
    fx = make()
    cond = conditions(fx)
    res = outcomes(fx)
    hashes = {}
    for name, t in fx.items():
        b = dump(t).encode()
        (out / name).write_bytes(b)
        hashes[name] = hashlib.sha256(b).hexdigest()
    report = {"checks_of_checks": checks, "conditions": cond, "outcomes": res, "sha256": hashes}
    (HERE / "results/fixtures.json").write_text(dump(report))
    print(f"{len(checks)} checks of checks, {len(cond)} conditions, "
          f"{sum(r['ok'] for r in res)} of {len(res)} outcomes as the scenarios state")
    for n, h in hashes.items():
        print(h, n)


if __name__ == "__main__":
    main(sys.argv[1])
