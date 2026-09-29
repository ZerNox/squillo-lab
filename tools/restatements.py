"""Mechanical aids for squillo's S4 and S6 (squillo L-049, R-11, iteration 55).

    python3 tools/restatements.py <squillo> [--at <rev>]   # report; exit 1 if anything is flagged
    python3 tools/restatements.py --self-test

S4: every restatement of an ADR's status in a current-state document (ADRs, `docs/architecture.md`,
`docs/glossary.md`, `docs/later/`, the header block of each question, `STATUS.md` above its ledger)
is compared with that ADR's own `Status:` line. Flagged: a restatement calling a `proposed` ADR
accepted without saying proposed; and one listing the iterations it was revised in whose last is
earlier than the last its header lists.

S6: each question's *Constraint check* table has one row per row of `docs/architecture.md` §2 as it
stood at the question's first commit, and no cell that says "none" with no reason.

Crude lab tooling, stdlib only. It finds the cases it is written for, not every stale sentence: a
flag is a lead to read, and a clean run is not proof (S4 still asks for the search).
"""

import re
import subprocess
import sys
from pathlib import Path

ADR_REF = re.compile(r"ADR (\d{4})")
REVISED = re.compile(r"revised\s+in\s+iterations?\s+((?:\d+)(?:(?:,\s+|\s+and\s+|,\s+and\s+)\d+)*)")


def iters(text):
    """Every iteration a text that says 'revised in iteration(s) …' lists, including a later
    '… and in iteration 53' in the same text."""
    if not REVISED.search(text):
        return []
    out = []
    for m in re.finditer(r"iterations?\s+((?:\d+)(?:(?:,\s+|\s+and\s+|,\s+and\s+)\d+)*)", text):
        out += [int(x) for x in re.findall(r"\d+", m.group(1))]
    return out


def status(adr_text):
    """(current status word, last iteration its Status: line says it was revised in, or None)."""
    m = re.search(r"^- \*\*Status:\*\*(.*?)(?=^- \*\*)", adr_text, re.S | re.M)
    s = " ".join(m.group(1).split()) if m else ""
    word = "proposed" if s.startswith("proposed") else "accepted" if s.startswith("accepted") else s.split(" ")[0]
    r = iters(s)
    return word, (max(r) if r else None)


def window(text, i):
    """The restatement after an ADR mention: its parenthetical, else to the sentence's end."""
    rest = text[i:i + 400]
    m = re.match(r"ADR \d{4}\]?(?:\([^)]*\))?\s*(\()", rest)
    if m:
        depth, j = 0, m.start(1)
        for k in range(j, len(rest)):
            depth += {"(": 1, ")": -1}.get(rest[k], 0)
            if depth == 0:
                return rest[:k + 1]
        return rest
    m = re.search(r"[.;|]\s", rest)
    return rest[:m.start()] if m else rest


def current_state_texts(root):
    """(path, text) for the documents that state what holds now, not what an iteration recorded."""
    root = Path(root)
    for p in sorted((root / "docs/decisions").glob("*.md")):
        yield p, p.read_text()
    for p in [root / "docs/architecture.md", root / "docs/glossary.md", *sorted((root / "docs/later").glob("*.md"))]:
        yield p, p.read_text()
    for p in sorted((root / "docs/questions").glob("Q-*.md")):
        t = p.read_text()
        yield p, t[:t.find("\n## ")] if "\n## " in t else t
    t = (root / "STATUS.md").read_text()
    m = re.search(r"^## .*[Ll]edger", t, re.M)  # squillo's is "## Iteration ledger"
    yield root / "STATUS.md", t[:m.start()] if m else t


def s4(root, adrs):
    flags = []
    for p, text in current_state_texts(root):
        own = re.match(r"(\d{4})-", p.name)
        for m in ADR_REF.finditer(text):
            n = m.group(1)
            if n not in adrs or (own and own.group(1) == n):
                continue
            word, last = adrs[n]
            w = window(text, m.start())
            line = text.count("\n", 0, m.start()) + 1
            if word == "proposed" and re.search(r"\baccepted\b(?! ADR)", w) and "proposed" not in w:
                flags.append((p, line, f"ADR {n} is proposed; this calls it accepted: {w!r}"))
            r = iters(w)
            states = re.search(r"\b(accepted|proposed|back to|so back)\b", w)  # a status restated, not a citation
            if last and r and max(r) < last and states:
                flags.append((p, line, f"ADR {n} was last revised in iteration {last}; this lists {r}: {w!r}"))
    return flags


def table_rows(section):
    rows = [l for l in section.splitlines() if l.startswith("|")]
    return [r for r in rows[2:]]  # header and separator


S6_FROM = 26  # one row per §2 row since L-043 (R-09, iteration 45); Q-026 is the first question after it
NONE_FROM = 32  # "none" with its reason, checked from the first question after R-11 (Q-026 to Q-031 left as decided)


def s6(root, at_rev_of):
    flags = []
    for p in sorted((Path(root) / "docs/questions").glob("Q-*.md")):
        if int(re.search(r"\d+", p.name).group()) < S6_FROM:
            continue
        t = p.read_text()
        for sec in re.split(r"\n(?=## )", t):
            if not sec.startswith("## Constraint check"):
                continue
            rows = table_rows(sec)
            arch = at_rev_of(p)
            if arch is not None:
                a = arch[arch.find("## 2."):arch.find("## 3.")]
                want = len(table_rows(a))
                if len(rows) != want:
                    flags.append((p, 0, f"constraint table has {len(rows)} rows; docs/architecture.md §2 had {want} at its first commit"))
            for r in rows:
                cells = [c.strip() for c in r.strip("|").split("|")]
                if int(re.search(r"\d+", p.name).group()) >= NONE_FROM and len(cells) > 1 and re.fullmatch(r"(?i)none\.?", cells[-1]):
                    flags.append((p, 0, f"'none' with no reason: {cells[0]!r}"))
    return flags


def arch_at_first_commit(root):
    def f(q):
        rel = q.relative_to(root)
        c = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", str(rel)], cwd=root,
                           capture_output=True, text=True).stdout.split()
        if not c:
            return None
        return subprocess.run(["git", "show", f"{c[-1]}:docs/architecture.md"], cwd=root,
                              capture_output=True, text=True).stdout or None
    return f


def run(root):
    root = Path(root).resolve()
    adrs = {re.match(r"(\d{4})", p.name).group(1): status(p.read_text())
            for p in (root / "docs/decisions").glob("[0-9]*.md")}
    flags = s4(root, adrs) + s6(root, arch_at_first_commit(root))
    for p, line, msg in flags:
        print(f"{p.relative_to(root)}:{line}: {msg}")
    print(f"{len(flags)} flagged")
    return flags


def self_test():
    """The checks on a case each must pass and one each must fail, known by construction."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        r = Path(d)
        for sub in ("docs/decisions", "docs/later", "docs/questions"):
            (r / sub).mkdir(parents=True)
        (r / "docs/decisions/0009-x.md").write_text(
            "# 0009\n\n- **Status:** proposed (accepted by Joakim; revised in\n  iterations 48 and 53, so back)\n- **Date:** x\n")
        (r / "docs/architecture.md").write_text("## 2. C\n\n| a | b |\n| :- | :- |\n| r1 | x |\n| r2 | y |\n\n## 3. D\n")
        (r / "docs/glossary.md").write_text(
            "Good: ADR 0009 (proposed: accepted, revised in iterations 48 and 53).\n"
            "Stale list: ADR 0009 (proposed; revised in iteration 48).\n"
            "Stale status: ADR 0009 (accepted).\n"
            "Citation, not status: a term (ADR 0009, revised in iteration 48).\n"
            "Another's status: ADR 0009 (new, amending accepted ADR 0013).\n"
            "Listed in two phrases: ADR 0009 (proposed: revised in iteration 48, and in iteration 53).\n"
            "Across a line: ADR 0009 (proposed: revised in iterations 48 and\n  53).\n")
        (r / "STATUS.md").write_text("# S\n")
        (r / "docs/questions/Q-032.md").write_text(
            "# Q\n\n## Constraint check\n\n| row | options |\n| :- | :- |\n| r1 | none |\n\n## Other\n")
        adrs = {"0009": status((r / "docs/decisions/0009-x.md").read_text())}
        assert adrs["0009"] == ("proposed", 53), adrs
        f4 = s4(r, adrs)
        lines = sorted(l for _, l, _ in f4)
        assert lines == [2, 3], ("S4 must pass line 1 and fail lines 2 and 3", f4)
        f6 = s6(r, lambda q: (r / "docs/architecture.md").read_text())
        assert len(f6) == 2 and "1 rows" in f6[0][2] and "none" in f6[1][2], f6
    print("self-test: S4 passes the good line and the citation and flags both stale ones; S6 flags the short table and the bare 'none'")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        self_test()
    else:
        sys.exit(1 if run(sys.argv[1]) else 0)
