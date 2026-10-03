"""Mechanical aid for squillo's S15 (squillo L-051, R-12, iteration 60).

    python3 tools/checkkeys.py <script.py> <results.json> [...]   # report; exit 1 if anything is flagged
    python3 tools/checkkeys.py --self-test

For one experiment script and the results files it writes:

1. The script refuses to run uncommitted: it calls a function that runs both
   `git ls-files --error-unmatch` and `git diff --quiet` on itself.
2. Every results key that names a check (`check`, `must`, in any case) is asserted in the
   script: its name appears on a line that also holds `assert`, or in a tuple or list of names
   that a loop asserts (`for k in (...): assert report[k]`), or the experiment's README says
   "recorded, not asserted" in a line that names the key.
3. Keys named `pass`/`passes`/`ok` are listed, not flagged: they may be a check or a bar's
   outcome, which is the result itself; the README says which.
4. Every `json.dump`/`json.dumps` call names a `default=`, so a numpy scalar among the results
   cannot stop the write after the run has passed its checks (squillo L-066: E-002 rounds 6
   and 7 each needed a second run for a numpy bool).

Crude lab tooling, stdlib only. A clean run means the names are there, not that each assert
asserts the right thing: it is a lead, never a substitute for reading the check (S15). It reads
names, not data flow: a key asserted through another key (`check_fails_when_it_must`) or by the
expression it records (`assert not any(x["agrees"] for x in k4)`) is flagged, and is read by hand.
"""

import json
import re
import sys
from pathlib import Path

CHECK = re.compile(r"check|must", re.I)
OUTCOME = re.compile(r"^(pass|passes|ok)$", re.I)


def keys(o, out=None):
    out = set() if out is None else out
    if isinstance(o, dict):
        for k, v in o.items():
            out.add(str(k))
            keys(v, out)
    elif isinstance(o, list):
        for v in o:
            keys(v, out)
    return out


def asserted_names(src):
    """Names on assert lines, and names in a literal tuple/list that a following loop asserts."""
    names = set()
    lines = src.splitlines()
    for i, line in enumerate(lines):
        if "assert" in line:
            names |= set(re.findall(r"[\"']([A-Za-z0-9_]+)[\"']|\b([A-Za-z_][A-Za-z0-9_]*)\b", line) and
                         [a or b for a, b in re.findall(r"[\"']([A-Za-z0-9_]+)[\"']|\b([A-Za-z_][A-Za-z0-9_]*)\b", line)])
    # for k in ("a", "b", ...): ... assert report[k]
    for m in re.finditer(r"for\s+(\w+)\s+in\s+[\(\[]((?:\s*[\"'][\w]+[\"']\s*,?)+)\s*[\)\]]\s*:\s*\n?(.*)", src):
        var, body, after = m.group(1), m.group(2), src[m.end(2):m.end(2) + 300]
        if re.search(r"assert\b[^\n]*\[\s*" + re.escape(var) + r"\s*\]", after):
            names |= set(re.findall(r"[\"']([\w]+)[\"']", body))
    # out["c5"] = dict(a=..., must_fail_x=..., passes=...) followed by assert out["c5"][...]: the dict's
    # keys are its parts, asserted through it
    for m in re.finditer(r"(\w+)\[[\"'](\w+)[\"']\]\s*=\s*dict\(", src):
        var, name, i, depth = m.group(1), m.group(2), m.end(), 1
        while depth and i < len(src):
            depth += {"(": 1, ")": -1}.get(src[i], 0)
            i += 1
        if re.search(r"assert\s+" + re.escape(var) + r"\[[\"']" + re.escape(name) + r"[\"']\]", src):
            names |= set(re.findall(r"(\w+)\s*=", src[m.end():i]))
    return names


def readme_recorded(script):
    rd = Path(script).parent / "README.md"
    if not rd.exists():
        return ""
    return "\n".join(l for l in rd.read_text(encoding="utf-8").splitlines()
                     if re.search(r"recorded,? not asserted", l, re.I))


def bare_json_dumps(src):
    """Each json.dump(s) call whose parentheses hold no `default=`, by line number."""
    out = []
    for m in re.finditer(r"json\.dumps?\(", src):
        i, depth = m.end(), 1
        while depth and i < len(src):
            depth += {"(": 1, ")": -1}.get(src[i], 0)
            i += 1
        if "default=" not in src[m.end():i]:
            out.append(src.count("\n", 0, m.start()) + 1)
    return out


def audit(script, results, src=None, readme=None):
    src = Path(script).read_text(encoding="utf-8") if src is None else src
    readme = readme_recorded(script) if readme is None else readme
    flags, info = [], []
    if not ("ls-files" in src and "--error-unmatch" in src and "diff" in src and "--quiet" in src):
        flags.append("no committed-first guard (git ls-files --error-unmatch and git diff --quiet)")
    for ln in bare_json_dumps(src):
        flags.append(f"json.dump without default= at line {ln}: a numpy scalar stops the write (L-066)")
    names = asserted_names(src)
    for r in results:
        for k in sorted(keys(r)):
            if CHECK.search(k) and k not in names and k not in readme:
                flags.append(f"check key not asserted and not listed as recorded: {k}")
            elif OUTCOME.match(k):
                info.append(k)
    return flags, sorted(set(info))


def self_test():
    good = '''
def committed_first():
    subprocess.run(["git", "ls-files", "--error-unmatch", me]); subprocess.run(["git", "diff", "--quiet", "HEAD"])
assert report["x_check"]["ok"]
for k in ("a_must_fail", "b_must_fail"):
    assert report[k] is True, k
'''
    res = {"x_check": {"ok": True}, "a_must_fail": True, "b_must_fail": True, "passes": True}
    f, info = audit("x.py", [res], good, "")
    assert not f and info == ["ok", "passes"], (f, info)
    # must fail: no guard
    f, _ = audit("x.py", [res], good.replace("--error-unmatch", ""), "")
    assert any("guard" in x for x in f), f
    # must fail: a must key never asserted
    f, _ = audit("x.py", [dict(res, c_must_fail=True)], good, "")
    assert f == ["check key not asserted and not listed as recorded: c_must_fail"], f
    # must pass: the same key listed in the README as recorded, not asserted
    f, _ = audit("x.py", [dict(res, c_must_fail=True)], good, "c_must_fail: recorded, not asserted, because ...")
    assert not f, f
    # must fail: a loop over names whose body does not assert
    f, _ = audit("x.py", [res], good.replace("assert report[k] is True, k", "print(report[k])"), "")
    assert any("a_must_fail" in x for x in f), f
    # must pass: keys inside a dict asserted through it; must fail: the same dict never asserted
    sub = good + 'out["c5"] = dict(n=1, must_pass_harm=0,\n    passes=True)\nassert out["c5"]["passes"]\n'
    r5 = dict(res, c5={"n": 1, "must_pass_harm": 0, "passes": True})
    f, _ = audit("x.py", [r5], sub, "")
    assert not f, f
    f, _ = audit("x.py", [r5], sub.replace('assert out["c5"]["passes"]', 'print(out)'), "")
    assert f == ["check key not asserted and not listed as recorded: must_pass_harm"], f
    # must pass: a json.dumps naming default=; must fail: the same call without it
    js = good + 'out.write_text(json.dumps(res, indent=1, default=lambda o: o.item()))\n'
    f, _ = audit("x.py", [res], js, "")
    assert not f, f
    f, _ = audit("x.py", [res], js.replace(", default=lambda o: o.item()", ""), "")
    assert len(f) == 1 and "json.dump without default=" in f[0], f
    print("self-test: 9 of 9 cases as expected")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        self_test()
        sys.exit(0)
    script, files = sys.argv[1], sys.argv[2:]
    flags, info = audit(script, [json.load(open(f)) for f in files])
    for x in flags:
        print("FLAG", x)
    if info:
        print("outcome keys, not flagged (the README says which are checks):", ", ".join(info))
    print(f"{len(flags)} flagged")
    sys.exit(1 if flags else 0)
