"""Fetch a few VocalSet 1.1 files (CC BY 4.0) by HTTP range requests.

Wilkins, Seetharaman, Wahl and Pardo (2018), VocalSet, doi:10.5281/zenodo.1442513.
Only the listed members are read from the 2 GB zip; they go to data/cache/,
which is not committed. Crude experiment code.
"""

import io
import sys
import urllib.request
import zipfile
from pathlib import Path

URL = "https://zenodo.org/api/records/1442513/files/VocalSet11.zip/content"
SIZE = 2077243579
CACHE = Path(__file__).parent / "data" / "cache"


class HttpFile(io.RawIOBase):
    def __init__(self, url, size):
        self.url, self.size, self.pos = url, size, 0

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = {0: off, 1: self.pos + off, 2: self.size + off}[whence]
        return self.pos

    def readinto(self, b):
        n = min(len(b), self.size - self.pos)
        if n <= 0:
            return 0
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{self.pos + n - 1}"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        b[:len(data)] = data
        self.pos += len(data)
        return len(data)


def open_zip():
    return zipfile.ZipFile(io.BufferedReader(HttpFile(URL, SIZE), buffer_size=1 << 20))


if __name__ == "__main__":
    z = open_zip()
    if sys.argv[1:] == ["list"]:
        for i in z.infolist():
            print(i.filename, i.file_size)
        sys.exit()
    CACHE.mkdir(parents=True, exist_ok=True)
    for name in sys.argv[1:]:
        out = CACHE / Path(name).name
        if not out.exists():
            out.write_bytes(z.read(name))
        print(out)
