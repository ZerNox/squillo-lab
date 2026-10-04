"""Real-singer examples for the session page's listen-first guides.

    python3 session/examples.py

Fetches six VocalSet 1.1 recordings (Wilkins, Seetharaman, Wahl and Pardo
2018, doi:10.5281/zenodo.1442513, CC BY 4.0) by HTTP range requests, only
those members of the 2 GB zip, and cuts one clean take from each into
session/cache/examples/, which git ignores. Every VocalSet singer sings in C:
the men start on C3, the women on C4. The cut times come from a note-by-note
pitch track of each file (2026-09-29): the scale goes up to the ninth, D, and
back; the long tone is the first of three. Stdlib only.
"""

import io
import struct
import sys
import urllib.request
import wave
import zipfile
from pathlib import Path

URL = "https://zenodo.org/api/records/1442513/files/VocalSet11.zip/content"
SIZE = 2077243579
OUT = Path(__file__).resolve().parent / "cache" / "examples"
# page name -> (VocalSet file, start s, end s)
EXAMPLES = {
    "scale-m": ("m8_scales_straight_a.wav", 0.4, 8.2),
    "scale-f": ("f1_scales_straight_a.wav", 0.3, 10.6),
    "row-m": ("m4_row_straight.wav", 0.0, 11.3),
    "row-f": ("f2_row_straight.wav", 0.0, 14.3),
    "hold-m": ("m1_long_straight_a.wav", 0.0, 3.6),
    "hold-f": ("f2_long_straight_a.wav", 0.6, 4.3),
}
FADE = 0.05  # s


class HttpFile(io.RawIOBase):
    def __init__(self):
        self.pos = 0

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = {0: off, 1: self.pos + off, 2: SIZE + off}[whence]
        return self.pos

    def readinto(self, b):
        n = min(len(b), SIZE - self.pos)
        if n <= 0:
            return 0
        req = urllib.request.Request(URL, headers={"Range": f"bytes={self.pos}-{self.pos + n - 1}"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        b[:len(data)] = data
        self.pos += len(data)
        return len(data)


def cut(src, t0, t1, dst):
    with wave.open(io.BytesIO(src)) as w:
        assert w.getsampwidth() == 2 and w.getnchannels() == 1, "VocalSet is 16-bit mono"
        sr = w.getframerate()
        w.setpos(int(t0 * sr))
        n = int((t1 - t0) * sr)
        x = list(struct.unpack(f"<{n}h", w.readframes(n)[:2 * n]))
    n, f = len(x), int(FADE * sr)
    peak = max(1, max(abs(v) for v in x))
    g = 0.5 * 32767 / peak
    for i in range(n):
        ramp = min(1.0, i / f, (n - 1 - i) / f)
        x[i] = int(x[i] * g * ramp)
    with wave.open(str(dst), "wb") as w:
        w.setnchannels(1), w.setsampwidth(2), w.setframerate(sr)
        w.writeframes(struct.pack(f"<{n}h", *x))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    todo = {k: v for k, v in EXAMPLES.items() if not (OUT / f"{k}.wav").exists()}
    if not todo:
        print("all examples present in", OUT)
        return
    z = zipfile.ZipFile(io.BufferedReader(HttpFile(), buffer_size=1 << 20))
    members = {Path(n).name: n for n in z.namelist() if not n.startswith("__MACOSX")}
    for k, (name, t0, t1) in todo.items():
        cut(z.read(members[name]), t0, t1, OUT / f"{k}.wav")
        print(OUT / f"{k}.wav")


if __name__ == "__main__":
    sys.exit(main())
