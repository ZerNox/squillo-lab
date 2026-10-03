"""A mechanical aid for squillo's S18 (squillo L-063, R-17, iteration 85).

    python3 tools/numbers.py <text-file or -> <results.json> [<results.json> ...]
    python3 tools/numbers.py --self-test

Every decimal number in the text (a README result row, a ledger row, a spec reason) is looked
for among the values the results files hold: as written, as a percentage of a fraction the file
holds, or as a fraction of a percentage, rounded, rounded up or rounded down to the decimals the
text gives. A number found in none is flagged: S18 says a number no results file holds is not
cited. Integers are not read (counts are often sums of entries, and years, sample rates and IDs
are integers), so a flag-free run says nothing about them.

Crude lab tooling, stdlib only. A flag is a lead to read, and a clean run is not proof: a number
can match a value of another quantity by chance. A number the text derives by a formula it
states (an interval from counts a file holds, say) is flagged too; S18 wants it written to a
results file by a committed script, or not cited.
"""

import json
import math
import re
import sys

NUM = re.compile(r"(?<![\w.])(\d+\.\d+)(?!\d|\.\d)")


def values(obj, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            values(k, out)
            values(v, out)
    elif isinstance(obj, list):
        for v in obj:
            values(v, out)
    elif isinstance(obj, bool):
        pass
    elif isinstance(obj, (int, float)):
        if math.isfinite(obj):
            out.append(float(obj))
    elif isinstance(obj, str):
        for m in re.findall(r"-?\d+(?:\.\d+)?(?:[eE]-?\d+)?", obj):
            try:
                if math.isfinite(float(m)):
                    out.append(float(m))
            except ValueError:
                pass
    return out


def held(x, d, vals):
    """Is x, written with d decimals, any held value (or its percentage or fraction) to d decimals?"""
    q = 10 ** d
    for v in vals:
        for c in (abs(v), abs(v) * 100, abs(v) / 100):
            for r in (round(c * q), math.floor(c * q + 1e-9), math.ceil(c * q - 1e-9)):
                if r == round(x * q):
                    return True
    return False


def flags(text, vals):
    out = []
    for m in NUM.finditer(text):
        s = m.group(1)
        if not held(float(s), len(s.split(".")[1]), vals):
            line = text.count("\n", 0, m.start()) + 1
            out.append((line, s, text[max(0, m.start() - 50):m.end() + 20].replace("\n", " ")))
    return out


def self_test():
    vals = values({"worst": {"excl": 9, "n": 40, "pct": 22.5}, "u": 2.1106, "share": 0.075}, [])
    good = flags("9 of 40 (22.5 %), median u 2.11, 2.12 rounded up, 7.5 % of takes", vals)
    assert good == [], ("must pass: values held, rounded, rounded up, as a percentage", good)
    bad = flags("9 of 40 (22.5 %, Wilson 95 % 12.3-37.5)", vals)
    assert [s for _, s, _ in bad] == ["12.3", "37.5"], ("must fail: an interval no file holds", bad)
    assert flags("openspec 1.13.1, BS.1770-4", vals) == [], "version strings and names are not numbers"
    print("self-test: held values pass (rounded, up, as %); the unheld interval's two ends are flagged; versions skipped")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        self_test()
        sys.exit(0)
    src = sys.argv[1]
    text = sys.stdin.read() if src == "-" else open(src).read()
    vals = []
    for p in sys.argv[2:]:
        values(json.load(open(p)), vals)
    fl = flags(text, vals)
    for line, s, ctx in fl:
        print(f"{line}: {s} held by no results file given: ...{ctx}...")
    print(f"{len(fl)} flagged")
    sys.exit(1 if fl else 0)
