"""The counts under squillo's STATUS.md *Process* against the files they count (squillo L-068, R-20).

    python3 tools/counts.py <squillo> [--at <rev>]   # exit 1 if a count disagrees
    python3 tools/counts.py --self-test

Findings: rows `| F-nnn |` of docs/process/findings.md, open when the last cell starts with "open"
or "needs Joakim", deferred when it starts with "deferred", else closed; compared with STATUS.md's
"— N open, M deferred, K fixed". Lessons: rows `| L-nnn |` of docs/process/lessons.md against
"— N recorded". A cell holding a `|` splits badly; such a row counts as closed, so read any flag.

Crude lab tooling, stdlib only.
"""

import re
import subprocess
import sys


def read(root, path, at):
    if at:
        return subprocess.run(["git", "-C", root, "show", f"{at}:{path}"], check=True,
                              capture_output=True, text=True).stdout
    return open(f"{root}/{path}", encoding="utf-8").read()


def check(findings, lessons, status):
    n_open = n_def = n_closed = 0
    for line in findings.splitlines():
        if not re.match(r"\| F-\d{3} \|", line):
            continue
        st = line.rstrip().rstrip("|").split("|")[-1].strip()
        if st.startswith("open") or st.startswith("needs Joakim"):
            n_open += 1
        elif st.startswith("deferred"):
            n_def += 1
        else:
            n_closed += 1
    n_lessons = sum(1 for line in lessons.splitlines() if re.match(r"\| L-\d{3} \|", line))
    problems = []
    m = re.search(r"findings\.md\)\s+—\s+(\d+) open, (\d+) deferred.*?, (\d+) fixed", status)
    if not m:
        problems.append("STATUS.md: no findings count line")
    else:
        said = tuple(int(x) for x in m.groups())
        if said != (n_open, n_def, n_closed):
            problems.append(f"findings: STATUS.md says {said[0]} open, {said[1]} deferred, {said[2]} fixed; "
                            f"findings.md has {n_open}, {n_def}, {n_closed}")
    m = re.search(r"lessons\.md\)\s+—\s+(\d+) recorded", status)
    if not m:
        problems.append("STATUS.md: no lessons count line")
    elif int(m.group(1)) != n_lessons:
        problems.append(f"lessons: STATUS.md says {m.group(1)} recorded; lessons.md has {n_lessons}")
    return problems


def self_test():
    f = "| F-001 | a | b | fixed in 3 |\n| F-002 | a | b | open |\n| F-003 | a | b | deferred to Stage E by R-1 |\n"
    l = "| L-001 | x |\n| L-002 | y |\n"
    good = "Lessons: [x](docs/process/lessons.md) — 2 recorded\nFindings: [x](docs/process/findings.md) — 1 open, 1 deferred, 1 fixed\n"
    bad = good.replace("1 open, 1 deferred, 1 fixed", "0 open, 1 deferred, 1 fixed")
    assert check(f, l, good) == [], check(f, l, good)
    assert len(check(f, l, bad)) == 1
    assert len(check(f, l, good.replace("2 recorded", "3 recorded"))) == 1
    print("self-test: consistent counts pass; a stale open count and a stale lessons count each flag")


def main(argv):
    if argv == ["--self-test"]:
        self_test()
        return 0
    root, at = argv[0], None
    if len(argv) >= 3 and argv[1] == "--at":
        at = argv[2]
    problems = check(read(root, "docs/process/findings.md", at), read(root, "docs/process/lessons.md", at),
                     read(root, "STATUS.md", at))
    for p in problems:
        print(p)
    print(f"{len(problems)} flagged")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
