"""S4's hit list, made from the search's own output (squillo L-065, R-18, iteration 90).

    python3 tools/s4hits.py <base-rev> <term>... [--repo <path>]... [--to <rev>]
    python3 tools/s4hits.py --self-test

For each repo (default: squillo, then squillo-lab, as siblings of this tool's repo), every line
holding any term (fixed string) in the tree at --to (default: the working tree) is printed as
`IN DIFF` when that line was added or changed since <base-rev> in that repo, and as `NOT IN DIFF`
otherwise. Every `NOT IN DIFF` hit goes into the commit message's list with why it stays (S4), or
is fixed first. Lines under `STATUS.md`'s *Iteration ledger*, and files under `docs/reviews/`,
`docs/process/ledger-1-60.md` and `openspec/changes/archive/`, are records and are printed as
`RECORD` so they can be listed once by kind.

Crude lab tooling, stdlib only. It matches strings, not meaning: a term too short matches noise,
and a stale sentence with none of the terms is not found (S4 still asks for the phrases).
"""

import re
import subprocess
import sys
from pathlib import Path

RECORD_PATHS = ("docs/reviews/", "docs/process/ledger-1-60.md", "openspec/changes/archive/")


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True).stdout


def changed_lines(repo, base, to):
    """{path: set of line numbers in the new version that the diff base..to adds or changes}."""
    args = ["diff", "-U0", "--no-color", base] + ([to] if to else [])
    out, path, lines = {}, None, None
    for l in git(repo, *args).splitlines():
        if l.startswith("+++ "):
            path = l[6:] if l.startswith("+++ b/") else None
            lines = out.setdefault(path, set()) if path else None
        elif l.startswith("@@") and lines is not None:
            m = re.match(r"@@ -\S+ \+(\d+)(?:,(\d+))? @@", l)
            start, n = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1)
            lines.update(range(start, start + n))
    return out


def ledger_start(repo, to):
    t = git(repo, "show", f"{to}:STATUS.md") if to else (Path(repo) / "STATUS.md").read_text() \
        if (Path(repo) / "STATUS.md").exists() else ""
    for i, l in enumerate(t.splitlines(), 1):
        if re.match(r"^## .*[Ll]edger", l):
            return i
    return None


def hits(repo, base, terms, to=None):
    """[(kind, path, line, text)] for every line holding a term."""
    args = ["grep", "-n", "-I", "-F"] + sum((["-e", t] for t in terms), []) + ([to] if to else [])
    diff = changed_lines(repo, base, to)
    ledger = ledger_start(repo, to)
    out = []
    for l in git(repo, *args).splitlines():
        if to:
            l = l.split(":", 1)[1]
        path, line, text = l.split(":", 2)
        line = int(line)
        if path.startswith(RECORD_PATHS) or (path == "STATUS.md" and ledger and line > ledger):
            kind = "RECORD"
        elif line in diff.get(path, ()):
            kind = "IN DIFF"
        else:
            kind = "NOT IN DIFF"
        out.append((kind, path, line, text))
    return out


def main(argv):
    repos, to, rest = [], None, []
    i = 0
    while i < len(argv):
        if argv[i] == "--repo":
            repos.append(argv[i + 1]); i += 2
        elif argv[i] == "--to":
            to = argv[i + 1]; i += 2
        else:
            rest.append(argv[i]); i += 1
    base, terms = rest[0], rest[1:]
    if not repos:
        lab = Path(__file__).resolve().parent.parent
        repos = [str(lab.parent / "squillo"), str(lab)]
    open_hits = 0
    for repo in repos:
        b = base if git(repo, "rev-parse", "-q", "--verify", base + "^{commit}").strip() else None
        if b is None:
            print(f"# {repo}: {base} is not a revision here; every hit is NOT IN DIFF")
            b = git(repo, "rev-parse", "HEAD").strip()
        for kind, path, line, text in hits(repo, b, terms, to):
            open_hits += kind == "NOT IN DIFF"
            print(f"{kind:12} {Path(repo).name}/{path}:{line}: {text.strip()[:160]}")
    print(f"{open_hits} not in diff: each is listed in the commit message with why, or fixed")
    return open_hits


def self_test():
    """A must-pass and a must-fail case, known by construction."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        r = Path(d)
        git(r, "init", "-q")
        git(r, "config", "user.email", "t@t"); git(r, "config", "user.name", "t")
        (r / "STATUS.md").write_text("# S\n\nF-9 open.\n\nF-9 blocks.\n\n## Iteration ledger\n\n| 1 | F-9 |\n")
        (r / "docs/reviews").mkdir(parents=True)
        (r / "docs/reviews/R-1.md").write_text("F-9\n")
        git(r, "add", "-A"); git(r, "commit", "-qm", "a")
        base = git(r, "rev-parse", "HEAD").strip()
        (r / "STATUS.md").write_text("# S\n\nF-9 fixed.\n\nF-9 blocks.\n\n## Iteration ledger\n\n| 1 | F-9 |\n| 2 | F-9 fixed |\n")
        h = {(p, l): k for k, p, l, _ in hits(str(r), base, ["F-9"])}
        assert h[("STATUS.md", 3)] == "IN DIFF", h                     # must pass: the line changed
        assert h[("STATUS.md", 5)] == "NOT IN DIFF", h                 # must fail: the stale line
        assert h[("STATUS.md", 9)] == h[("STATUS.md", 10)] == "RECORD", h
        assert h[("docs/reviews/R-1.md", 1)] == "RECORD", h
    print("self-test: a changed line IN DIFF, the stale line NOT IN DIFF, ledger rows and reviews RECORD")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        self_test()
    else:
        sys.exit(1 if main(sys.argv[1:]) else 0)
