"""The needs-human session: one local page that walks Joakim through every
`needs-human` step (E-001, E-002 round 4, E-003, E-004, E-005).

    python3 session/serve.py            # then open http://localhost:8010/
    python3 session/serve.py --phone    # also serve tone440.wav read-only on the LAN, port 8011
    python3 session/examples.py         # once: the real-singer examples the guides play

The page records takes in the browser and posts them here; they are written to
each experiment's data/cache/human/, which git ignores. It runs only the fixed
commands below, writes only the files named below, and commits only each
experiment's protocol files, when Joakim presses Commit. Nothing is uploaded
anywhere else. Crude lab tooling, stdlib only.
"""

import json
import shutil
import socket
import subprocess
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

LAB = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
RUNNER_LAB = Path.home() / ".local/state/squillo/work/squillo-lab"  # the runner's worktree, for caches
PORT, PHONE_PORT = 8010, 8011

EXP = {
    "E-001": LAB / "experiments/E-001-voice-resynthesis",
    "E-002": LAB / "experiments/E-002-measurement-reliability",
    "E-003": LAB / "experiments/E-003-capture-reality",
    "E-004": LAB / "experiments/E-004-phrase-library",
    "E-005": LAB / "experiments/E-005-intent-inference",
}
HUMAN = "data/cache/human"
# recordings the page may save, per experiment
RECORDINGS = {
    "E-001": {"take1.wav", "take2.wav", "take3.wav"},
    "E-002": {"same1.wav", "same2.wav", "ring1.wav", "ring2.wav"},
    "E-003": {"e003-human-chrome.json", "e003-human-chrome.f32",
              "e003-human-firefox.json", "e003-human-firefox.f32"},
    "E-005": {"row1.wav", "row2.wav"},
}
# text files the page may write
WRITABLE = {
    "E-001": {"data/cache/listening/ratings.csv"},
    "E-002": {"results/own_r4.md"},
    "E-004": {"results/listen.csv"},
    "E-005": {"results/own.md"},
}
# files the page may read
READABLE_PREFIXES = ("data/cache/listening/", "data/listen/", "results/", HUMAN + "/", "data/cache/tone440.wav")
# what each protocol commits, never audio
COMMIT = {
    "E-001": ["results/human/ratings.csv", "results/human/key.json"],
    "E-002": ["results/own_r4.json", "results/own_r4.md"],
    "E-003": ["results/human-chrome.json", "results/human-firefox.json"],
    "E-004": ["results/listen.csv"],
    "E-005": ["results/own.json", "results/own.md"],
}


def h(exp, name):
    return str(EXP[exp] / HUMAN / name)


def e003_inputs():
    return [h("E-003", f"e003-human-{b}.json") for b in ("chrome", "firefox")
            if (EXP["E-003"] / HUMAN / f"e003-human-{b}.json").exists()]


def e002_prep():
    """r4_ring.py run builds data/cache/r4_occ.pkl from VocalSet; reuse the runner's if it has one."""
    rel = "data/cache/r4_occ.pkl"
    ours, theirs = EXP["E-002"] / rel, RUNNER_LAB / "experiments/E-002-measurement-reliability" / rel
    if ours.exists():
        return ["true"]
    if theirs.exists():
        ours.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(theirs, ours)
        return ["echo", f"copied {rel} from the runner's worktree"]
    return ["uv", "run", "python", "r4_ring.py", "run"]


UV = ["uv", "run", "python"]
TASKS = {  # name -> (experiment, argv factory)
    "e001-build": ("E-001", lambda: UV + ["listen.py"] + [h("E-001", f"take{i}.wav") for i in (1, 2, 3)]),
    "e002-prep": ("E-002", e002_prep),
    "e002-run": ("E-002", lambda: UV + ["r4_own.py"] + [h("E-002", n) for n in ("same1.wav", "same2.wav", "ring1.wav", "ring2.wav")]),
    "e003-gen": ("E-003", lambda: UV + ["gen.py"]),
    "e003-analyse": ("E-003", lambda: UV + ["human.py"] + e003_inputs()),
    "e004-build": ("E-004", lambda: UV + ["listen.py"]),
    "e005-run": ("E-005", lambda: UV + ["run.py", "own", h("E-005", "row1.wav"), h("E-005", "row2.wav")]),
}
JOBS = {}


def run_job(jid, exp, argv):
    j = JOBS[jid]
    try:
        p = subprocess.Popen(argv, cwd=EXP[exp], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in p.stdout:
            j["log"] += line
        j["rc"] = p.wait()
    except Exception as e:  # noqa: BLE001 - reported to the page
        j["log"] += f"\n{e}"
        j["rc"] = -1
    j["done"] = True


def git(*args):
    return subprocess.run(["git", "-C", str(LAB), *args], capture_output=True, text=True)


def state():
    s = {}
    for exp, d in EXP.items():
        files = {}
        extra = ["data/cache/tone440.wav"] if exp == "E-003" else []
        for rel in extra + [f"{HUMAN}/{n}" for n in RECORDINGS.get(exp, ())] + COMMIT[exp] + sorted(WRITABLE.get(exp, ())):
            files[rel] = (d / rel).exists()
        paths = [str((d / c).relative_to(LAB)) for c in COMMIT[exp]]
        st = git("status", "--porcelain", "--", *paths).stdout.strip()
        s[exp] = {"files": files, "pending": st.splitlines() if st else [],
                  "occ": (d / "data/cache/r4_occ.pkl").exists() if exp == "E-002" else None,
                  "clips": sorted(p.name for p in (d / "data/cache/listening").glob("clip*.wav")) if exp == "E-001" else None}
    return s


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body=b"", ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("content-type", ctype)
        self.send_header("cache-control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def body(self):
        return self.rfile.read(int(self.headers.get("content-length", 0)))

    def file(self, p, ctype=None):
        if not p.is_file():
            return self.send(404, {"error": "not found"})
        types = {".html": "text/html", ".js": "text/javascript", ".wav": "audio/wav", ".json": "application/json",
                 ".csv": "text/csv", ".md": "text/markdown", ".f32": "application/octet-stream"}
        self.send(200, p.read_bytes(), ctype or types.get(p.suffix, "application/octet-stream"))

    def do_GET(self):
        u = unquote(urlparse(self.path).path)
        if u == "/":
            return self.file(HERE / "index.html")
        if u.startswith("/page/"):  # E-003's probe, worklet and engine, as its own serve.mjs maps them
            return self.file(EXP["E-003"] / "page" / Path(u[6:]).name)
        if u.startswith("/examples/"):  # real-singer guides, cut by session/examples.py
            return self.file(HERE / "cache/examples" / Path(u[10:]).name)
        if u.startswith("/data/"):
            return self.file(EXP["E-003"] / "data/cache" / Path(u[6:]).name)
        if u == "/api/state":
            return self.send(200, state())
        if u.startswith("/api/job/"):
            j = JOBS.get(u[9:])
            return self.send(200, j) if j else self.send(404, {"error": "no job"})
        if u.startswith("/api/file/"):
            exp, _, rel = u[10:].partition("/")
            if exp in EXP and ".." not in rel and rel.startswith(READABLE_PREFIXES):
                return self.file(EXP[exp] / rel)
        return self.send(404, {"error": "not found"})

    def same_origin(self):
        """Refuse requests another web page makes: a cross-origin POST carries its Origin,
        and a rebound DNS name its Host (R-11, squillo iteration 55)."""
        own = {f"localhost:{PORT}", f"127.0.0.1:{PORT}"}
        origin = self.headers.get("origin")
        return self.headers.get("host") in own and (origin is None or origin in {"http://" + o for o in own})

    def do_POST(self):
        if not self.same_origin():
            return self.send(403, {"error": "not from this page"})
        u = unquote(urlparse(self.path).path)
        if u.startswith("/api/rec/"):
            exp, _, name = u[9:].partition("/")
            if name not in RECORDINGS.get(exp, ()):
                return self.send(403, {"error": "not a recording this page saves"})
            p = EXP[exp] / HUMAN / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(self.body())
            return self.send(200, {"saved": str(p.relative_to(LAB)), "bytes": p.stat().st_size})
        if u.startswith("/api/write/"):
            exp, _, rel = u[11:].partition("/")
            if rel not in WRITABLE.get(exp, ()):
                return self.send(403, {"error": "not writable"})
            p = EXP[exp] / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(self.body())
            return self.send(200, {"saved": str(p.relative_to(LAB))})
        if u.startswith("/api/run/"):
            name = u[9:]
            if name not in TASKS:
                return self.send(403, {"error": "unknown task"})
            exp, argv = TASKS[name]
            argv = argv()
            jid = uuid.uuid4().hex[:8]
            JOBS[jid] = {"task": name, "argv": argv, "log": "$ " + " ".join(argv) + "\n", "done": False, "rc": None}
            threading.Thread(target=run_job, args=(jid, exp, argv), daemon=True).start()
            return self.send(200, {"job": jid})
        if u == "/api/e001-finish":  # ratings.csv and key.json into results/human/, for the commit
            d = EXP["E-001"]
            (d / "results/human").mkdir(parents=True, exist_ok=True)
            for n in ("ratings.csv", "key.json"):
                shutil.copy2(d / "data/cache/listening" / n, d / "results/human" / n)
            return self.send(200, {"ok": True})
        if u.startswith("/api/commit/"):
            exp = u[12:]
            if exp not in EXP:
                return self.send(403, {"error": "unknown experiment"})
            paths = [str((EXP[exp] / c).relative_to(LAB)) for c in COMMIT[exp] if (EXP[exp] / c).exists()]
            if not paths:
                return self.send(400, {"error": "nothing to commit"})
            out = []
            for args in (["add", "--", *paths],
                         ["commit", "-m", f"{exp}: Joakim's needs-human step, via session/ (numbers and notes, no audio)", "--", *paths],
                         ["pull", "--rebase", "--autostash", "-q"],
                         ["push", "-q", "origin", "HEAD:main"]):
                r = git(*args)
                out.append(f"$ git {' '.join(args)}\n{r.stdout}{r.stderr}")
                if r.returncode:
                    return self.send(500, {"log": "\n".join(out)})
            return self.send(200, {"log": "\n".join(out), "commit": git("rev-parse", "--short", "HEAD").stdout.strip()})
        return self.send(404, {"error": "not found"})


def phone_server():
    tone = EXP["E-003"] / "data/cache/tone440.wav"

    class P(SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            if self.path != "/tone440.wav" or not tone.exists():
                self.send_error(404)
                return
            b = tone.read_bytes()
            self.send_response(200)
            self.send_header("content-type", "audio/wav")
            self.send_header("content-length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("192.0.2.1", 9))
        ip = s.getsockname()[0]
    except OSError:
        ip = "<this laptop's LAN address>"
    finally:
        s.close()
    print(f"phone: open http://{ip}:{PHONE_PORT}/tone440.wav (read-only; only that file)")
    ThreadingHTTPServer(("0.0.0.0", PHONE_PORT), P).serve_forever()


if __name__ == "__main__":
    if "--phone" in sys.argv:
        threading.Thread(target=phone_server, daemon=True).start()
    print(f"open http://localhost:{PORT}/  (Ctrl-C to stop)")
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
