"""E-004 needs-human: render the phrases whose melody no independent
transcription confirmed, and the originals, for a listener to check.

    uv run python listen.py      # -> data/listen/NN-<id>.wav and results/listen.csv (to fill in)

Each file is a one-bar click count-in, then the phrase as a plain
harmonic tone at its tempo. Nothing is recorded; the WAVs are not committed.
Crude experiment code.
"""

import csv
import json
from pathlib import Path

import numpy as np
import soundfile as sf

import library as L
from run import parse

HERE = Path(__file__).parent
SR = 48_000


def tone(midi_note, seconds):
    t = np.arange(int(seconds * SR)) / SR
    f = 440.0 * 2 ** ((midi_note - 69) / 12)
    x = sum(np.sin(2 * np.pi * k * f * t) / k ** 1.5 for k in range(1, 7))
    env = np.minimum(1, np.minimum(t / 0.02, (seconds - t) / 0.05))
    return 0.2 * x * np.clip(env, 0, 1)


def main():
    summary = json.load(open(HERE / "results" / "summary.json"))
    st = summary["survive"]["per_phrase"]
    items = {c["id"]: c for c in L.CANDIDATES + L.ORIGINALS}
    todo = [i for i in items if st[i] in ("melody-unchecked", "melody-mismatch", "rhythm-differs", "verified-original")]
    out = HERE / "data" / "listen"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for n, i in enumerate(todo, 1):
        c = items[i]
        beat = 60.0 / c["tempo"]
        click = np.concatenate([np.pad(0.3 * np.sin(2 * np.pi * 1500 * np.arange(int(0.03 * SR)) / SR),
                                       (0, int(beat * SR) - int(0.03 * SR)))] * 4)
        x = np.concatenate([click] + [tone(p, b * beat) for p, b in parse(c["melody"])] + [np.zeros(SR // 2)])
        sf.write(out / f"{n:02d}-{i}.wav", x.astype(np.float32), SR)
        rows.append(dict(n=n, id=i, title=c["title"], kind="original" if i in {o["id"] for o in L.ORIGINALS} else "public-domain",
                         words=c["text"], verdict="", first_wrong_note="", reminds_me_of=""))
    with open(HERE / "results" / "listen.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "files in", out)


if __name__ == "__main__":
    main()
